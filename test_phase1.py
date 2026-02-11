"""
Phase 1 Tests - Local Agent Foundation
"""

import unittest
import sys
import os
import tempfile
from pathlib import Path
from datetime import datetime

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Back_End'))

from buddy_local_agent import BuddyLocalAgent
from config_manager import ConfigManager, get_config


class TestPhase1Foundation(unittest.TestCase):
    """Test Phase 1 foundation functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.agent = BuddyLocalAgent()
    
    def test_agent_initialization(self):
        """Test agent can be created."""
        self.assertIsNotNone(self.agent)
        self.assertIsNotNone(self.agent.agent_id)
        self.assertIn('local-', self.agent.agent_id)
    
    def test_agent_id_persistence(self):
        """Test agent ID is consistent."""
        agent_id_1 = self.agent.agent_id
        agent2 = BuddyLocalAgent()
        agent_id_2 = agent2.agent_id
        
        self.assertEqual(agent_id_1, agent_id_2)
    
    def test_database_initialization(self):
        """Test database can be initialized."""
        result = self.agent.initialize()
        # Will pass if no database errors
        self.agent.stop()
    
    def test_config_manager(self):
        """Test configuration manager."""
        ConfigManager().reload()
        
        # Get some config values
        max_browsers = get_config('max_browsers')
        self.assertIsNotNone(max_browsers)
        self.assertIsInstance(max_browsers, int)
        
        log_level = get_config('log_level')
        self.assertIsNotNone(log_level)
    
    def test_success_rate_calculation(self):
        """Test success rate calculation."""
        self.agent.tasks_processed = 95
        self.agent.tasks_failed = 5
        
        rate = self.agent._calculate_success_rate()
        self.assertAlmostEqual(rate, 95.0, places=1)
    
    def test_success_rate_zero_tasks(self):
        """Test success rate with no tasks."""
        self.agent.tasks_processed = 0
        self.agent.tasks_failed = 0
        
        rate = self.agent._calculate_success_rate()
        self.assertEqual(rate, 100.0)
    
    def test_status_dict(self):
        """Test status dictionary."""
        # Set some values
        self.agent.start_time = datetime.now()
        self.agent.running = True
        self.agent.tasks_processed = 10
        
        status = self.agent.get_status()
        
        self.assertIn('agent_id', status)
        self.assertIn('status', status)
        self.assertIn('uptime', status)
        self.assertIn('tasks_processed', status)
        self.assertEqual(status['status'], 'ONLINE')
        self.assertEqual(status['tasks_processed'], 10)


class TestPhase1Integration(unittest.TestCase):
    """Integration tests for Phase 1."""
    
    def test_agent_lifecycle(self):
        """Test full agent lifecycle (without actually running)."""
        agent = BuddyLocalAgent()
        
        # Check initial state
        self.assertFalse(agent.running)
        self.assertIsNone(agent.start_time)
        
        # Simulate initialization (actual initialization would require Firebase)
        # agent.initialize()
        # agent.running = True
        # agent.start_time = datetime.now()
        
        # Check status
        status = agent.get_status()
        self.assertIsNotNone(status)


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
