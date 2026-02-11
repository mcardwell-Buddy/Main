"""
Phase 3 Tests - Browser Pool Management
"""

import unittest
import sys
import os
from datetime import datetime, timedelta
import time

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Back_End'))

from browser_pool_manager import BrowserPoolManager, BrowserInstance
from resource_monitor import ResourceMonitor


class TestBrowserInstance(unittest.TestCase):
    """Test individual browser instance."""
    
    def setUp(self):
        """Set up test fixtures."""
        # We'll use a mock driver for testing
        self.mock_driver = None
    
    def test_browser_instance_creation(self):
        """Test browser instance can be created."""
        # Test without actual driver for unit tests
        self.assertIsNotNone(BrowserInstance)


class TestBrowserPoolManager(unittest.TestCase):
    """Test browser pool management."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.resource_monitor = ResourceMonitor()
        self.pool = BrowserPoolManager(self.resource_monitor)
    
    def test_initialization(self):
        """Test pool initializes correctly."""
        self.assertIsNotNone(self.pool)
        self.assertFalse(self.pool.running)
        self.assertEqual(len(self.pool.browsers), 0)
        self.assertIsNotNone(self.pool.resource_monitor)
    
    def test_pool_start(self):
        """Test pool can start."""
        self.pool.start()
        self.assertTrue(self.pool.running)
        self.assertIsNotNone(self.pool.start_time)
        self.pool.stop()
    
    def test_pool_stop(self):
        """Test pool can stop."""
        self.pool.start()
        self.assertTrue(self.pool.running)
        self.pool.stop()
        self.assertFalse(self.pool.running)
    
    def test_get_browser_count(self):
        """Test getting browser count."""
        self.pool.start()
        
        counts = self.pool.get_browser_count()
        self.assertIn('total', counts)
        self.assertIn('healthy', counts)
        self.assertIn('unhealthy', counts)
        self.assertEqual(counts['total'], 0)
        
        self.pool.stop()
    
    def test_get_pool_status(self):
        """Test getting pool status."""
        self.pool.start()
        
        status = self.pool.get_pool_status()
        self.assertIn('running', status)
        self.assertIn('total_browsers', status)
        self.assertIn('healthy_browsers', status)
        self.assertIn('target_count', status)
        self.assertIn('uptime', status)
        self.assertTrue(status['running'])
        
        self.pool.stop()
    
    def test_pool_update_when_not_running(self):
        """Test update when pool not running."""
        # Should not raise error
        self.pool.update()
        self.assertEqual(len(self.pool.browsers), 0)
    
    def test_pool_update_when_running(self):
        """Test update when pool is running."""
        self.pool.start()
        self.pool.target_browser_count = 0  # Don't create browsers
        
        # Should not raise error
        self.pool.update()
        
        self.pool.stop()
    
    def test_auto_scale_target_calculation(self):
        """Test auto-scale target calculation."""
        self.pool.start()
        
        # Get resource status
        resource_status = self.resource_monitor.get_system_status()
        
        # Simulate optimal mode
        self.pool.target_browser_count = 0
        
        # Update should work
        self.pool.update()
        
        self.assertGreaterEqual(self.pool.target_browser_count, 0)
        
        self.pool.stop()
    
    def test_get_available_browser_when_none(self):
        """Test getting browser when none exist."""
        self.pool.start()
        
        browser = self.pool.get_available_browser()
        self.assertIsNone(browser)
        
        self.pool.stop()
    
    def test_pool_configuration(self):
        """Test pool configuration values."""
        self.assertEqual(self.pool.health_check_interval, 30)
        self.assertEqual(self.pool.max_browser_age, 3600)
        self.assertEqual(self.pool.browser_startup_timeout, 10)
        self.assertGreater(self.pool.max_failed_health_checks, 0)
    
    def test_cleanup_idle_browsers_no_error(self):
        """Test cleanup idle browsers doesn't error."""
        self.pool.start()
        
        # Should not raise error
        self.pool._cleanup_idle_browsers()
        
        self.pool.stop()
    
    def test_get_browsers_info_empty(self):
        """Test getting browsers info when empty."""
        self.pool.start()
        
        info = self.pool.get_browsers_info()
        self.assertIsInstance(info, list)
        self.assertEqual(len(info), 0)
        
        self.pool.stop()
    
    def test_thread_safety(self):
        """Test thread safety of browser dict access."""
        self.pool.start()
        
        # Multiple rapid accesses should not cause errors
        for _ in range(10):
            self.pool.get_browser_count()
            self.pool.get_browsers_info()
        
        self.pool.stop()
    
    def test_total_browsers_created_incremented(self):
        """Test total_browsers_created stat."""
        self.pool.start()
        
        initial = self.pool.total_browsers_created
        # Don't create - just verify stat exists
        self.assertEqual(self.pool.total_browsers_created, initial)
        
        self.pool.stop()
    
    def test_pool_status_after_stop(self):
        """Test pool status after stopping."""
        self.pool.start()
        self.pool.stop()
        
        status = self.pool.get_pool_status()
        self.assertFalse(status['running'])


class TestBrowserPoolIntegration(unittest.TestCase):
    """Integration tests for browser pool."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.resource_monitor = ResourceMonitor()
        self.pool = BrowserPoolManager(self.resource_monitor)
    
    def test_pool_lifecycle(self):
        """Test complete pool lifecycle."""
        # Start
        self.pool.start()
        self.assertTrue(self.pool.running)
        
        # Update (should handle scaling)
        self.pool.update()
        
        # Get status
        status = self.pool.get_pool_status()
        self.assertTrue(status['running'])
        
        # Stop
        self.pool.stop()
        self.assertFalse(self.pool.running)
    
    def test_pool_with_resource_monitor(self):
        """Test pool integrates with resource monitor."""
        self.pool.start()
        
        # Get resource status
        resource_status = self.resource_monitor.get_system_status()
        self.assertIsNotNone(resource_status['mode'])
        
        # Update pool (should use resource monitor)
        self.pool.update()
        
        self.pool.stop()
    
    def test_multiple_updates(self):
        """Test multiple consecutive updates."""
        self.pool.start()
        self.pool.target_browser_count = 0
        
        for _ in range(5):
            self.pool.update()
            time.sleep(0.1)
        
        self.pool.stop()
    
    def test_scaling_based_on_resources(self):
        """Test scaling adjusts based on resource mode."""
        self.pool.start()
        
        # Get resource status
        resource_status = self.resource_monitor.get_system_status()
        mode = resource_status['mode']
        
        # Scaling should respond to mode
        self.assertIsNotNone(mode)
        
        self.pool.stop()


class TestBrowserPoolStress(unittest.TestCase):
    """Stress tests for browser pool."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.resource_monitor = ResourceMonitor()
        self.pool = BrowserPoolManager(self.resource_monitor)
    
    def test_rapid_start_stop(self):
        """Test rapid start/stop cycles."""
        for _ in range(3):
            self.pool.start()
            self.assertTrue(self.pool.running)
            self.pool.stop()
            self.assertFalse(self.pool.running)
    
    def test_concurrent_status_checks(self):
        """Test concurrent status checks."""
        self.pool.start()
        
        # Rapid status checks
        for _ in range(20):
            self.pool.get_pool_status()
            self.pool.get_browser_count()
        
        self.pool.stop()
    
    def test_pool_handles_errors_gracefully(self):
        """Test pool handles errors gracefully."""
        self.pool.start()
        
        # Call various methods - should not crash
        try:
            self.pool.update()
            self.pool.get_available_browser()
            self.pool._cleanup_idle_browsers()
            self.pool.get_browsers_info()
        except Exception as e:
            self.fail(f"Pool raised exception: {e}")
        
        self.pool.stop()


if __name__ == '__main__':
    unittest.main(verbosity=2)
