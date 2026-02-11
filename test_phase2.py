"""
Phase 2 Tests - Resource Monitoring
"""

import unittest
import sys
import os
from datetime import datetime, timedelta

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Back_End'))

from resource_monitor import ResourceMonitor
import psutil


class TestResourceMonitor(unittest.TestCase):
    """Test resource monitoring functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.monitor = ResourceMonitor()
    
    def test_initialization(self):
        """Test monitor initializes correctly."""
        self.assertIsNotNone(self.monitor)
        self.assertEqual(self.monitor.RAM_PER_BROWSER_MB, 141)
        self.assertIsNotNone(self.monitor.max_browsers_configured)
    
    def test_get_system_status(self):
        """Test getting system status."""
        status = self.monitor.get_system_status()
        
        self.assertIn('timestamp', status)
        self.assertIn('ram_used_gb', status)
        self.assertIn('ram_percent', status)
        self.assertIn('cpu_percent', status)
        self.assertIn('browser_count_safe', status)
        self.assertIn('mode', status)
        self.assertIn('healthy', status)
        
        # Verify values are reasonable
        self.assertGreater(status['ram_total_gb'], 0)
        self.assertGreaterEqual(status['ram_percent'], 0)
        self.assertLessEqual(status['ram_percent'], 100)
        self.assertGreater(status['browser_count_safe'], 0)
    
    def test_safe_browser_count(self):
        """Test browser count calculation."""
        safe = self.monitor.get_safe_browser_count('safe')
        comfortable = self.monitor.get_safe_browser_count('comfortable')
        aggressive = self.monitor.get_safe_browser_count('aggressive')
        
        # Comfortable should be >= safe (may be equal on very large systems)
        self.assertGreaterEqual(comfortable, safe)
        
        # Aggressive should be >= comfortable (may be equal on very large systems)
        self.assertGreaterEqual(aggressive, comfortable)
        
        # All should be positive
        self.assertGreater(safe, 0)
        self.assertGreater(comfortable, 0)
        self.assertGreater(aggressive, 0)
    
    def test_approaching_limit(self):
        """Test approaching limit detection."""
        result = self.monitor.is_approaching_limit()
        # Should return boolean
        self.assertIsInstance(result, bool)
    
    def test_should_throttle(self):
        """Test throttle detection."""
        result = self.monitor.should_throttle()
        self.assertIsInstance(result, bool)
    
    def test_should_pause_tasks(self):
        """Test pause detection."""
        result = self.monitor.should_pause_tasks()
        self.assertIsInstance(result, bool)
    
    def test_get_alerts(self):
        """Test alert system."""
        alerts = self.monitor.get_alerts()
        self.assertIsInstance(alerts, list)
        
        # If alerts exist, they should have proper format
        for alert in alerts:
            self.assertIn('level', alert)
            self.assertIn('message', alert)
    
    def test_update_metrics(self):
        """Test metric update."""
        metrics = self.monitor.update_metrics()
        
        self.assertIsNotNone(metrics)
        self.assertIn('ram_percent', metrics)
        self.assertIn('cpu_percent', metrics)
    
    def test_historical_metrics(self):
        """Test historical metric storage."""
        # Add multiple metrics
        for _ in range(5):
            self.monitor.update_metrics()
        
        history = self.monitor.get_historical_metrics()
        self.assertGreaterEqual(len(history), 5)
    
    def test_health_check(self):
        """Test system health check."""
        healthy = self.monitor.health_check()
        self.assertIsInstance(healthy, bool)
    
    def test_summary_output(self):
        """Test summary generation."""
        summary = self.monitor.get_summary()
        self.assertIsInstance(summary, str)
        self.assertIn('RAM Usage', summary)
        self.assertIn('CPU Usage', summary)
        self.assertIn('Mode', summary)
    
    def test_get_resource_forecast(self):
        """Test resource forecasting."""
        # Add some history
        for _ in range(10):
            self.monitor.update_metrics()
        
        forecast = self.monitor.get_resource_forecast(minutes_ahead=5)
        self.assertIn('ram_percent_forecast', forecast)
        self.assertIn('cpu_percent_forecast', forecast)
    
    def test_current_mode_calculation(self):
        """Test mode calculation."""
        # Test different RAM percentages
        mode_optimal = self.monitor._get_current_mode(50)
        self.assertEqual(mode_optimal, 'optimal')
        
        mode_throttled = self.monitor._get_current_mode(76)
        self.assertEqual(mode_throttled, 'throttled')
        
        mode_paused = self.monitor._get_current_mode(87)
        self.assertEqual(mode_paused, 'paused')
        
        mode_critical = self.monitor._get_current_mode(96)
        self.assertEqual(mode_critical, 'critical')


class TestResourceMonitorIntegration(unittest.TestCase):
    """Integration tests for resource monitoring."""
    
    def test_monitor_lifecycle(self):
        """Test monitor through typical usage."""
        monitor = ResourceMonitor()
        
        # Get initial status
        status1 = monitor.get_system_status()
        self.assertIsNotNone(status1)
        
        # Update metrics
        metrics = monitor.update_metrics()
        self.assertIsNotNone(metrics)
        
        # Get status again
        status2 = monitor.get_system_status()
        self.assertIsNotNone(status2)
        
        # Statuses should have same structure
        self.assertEqual(set(status1.keys()), set(status2.keys()))
    
    def test_throttle_state_consistency(self):
        """Test throttle state is consistent."""
        monitor = ResourceMonitor()
        
        # Call should_throttle multiple times
        result1 = monitor.should_throttle()
        result2 = monitor.should_throttle()
        
        # Same function, same conditions = same result
        self.assertEqual(result1, result2)


if __name__ == '__main__':
    unittest.main(verbosity=2)
