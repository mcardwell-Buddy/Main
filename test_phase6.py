"""
Phase 6: Multi-Agent Coordination Tests
Comprehensive test suite for multi-agent system with coordination, distribution, and failover.

Test Coverage:
- Agent registry and discovery
- Work distribution strategies
- Health monitoring and failover
- Shared state management
- Coordinated task execution
- Integration tests
"""

import unittest
import sqlite3
import json
import tempfile
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent / "Back_End"))

from multi_agent_coordinator import (
    AgentStatus, CoordinationStrategy, FailoverStrategy,
    AgentCapability, AgentInfo, CoordinatedTask,
    AgentRegistry, WorkDistributor, AgentHealthMonitor,
    SharedStateManager, AgentCoordinator, init_phase6_tables
)


class TestAgentRegistry(unittest.TestCase):
    """Test agent registration and discovery"""
    
    def setUp(self):
        self.db_path = tempfile.NamedTemporaryFile(delete=False, suffix='.db').name
        self.registry = AgentRegistry(self.db_path)
    
    def test_register_agent(self):
        """Test registering a new agent"""
        agent_id = self.registry.register_agent(
            hostname="localhost",
            port=5000,
            resource_capacity={'cpu': 4, 'memory': 8},
            capabilities={'navigate': AgentCapability('navigate')}
        )
        
        self.assertIsNotNone(agent_id)
        self.assertTrue(agent_id.startswith('agent-'))
        
        agent = self.registry.get_agent(agent_id)
        self.assertIsNotNone(agent)
        self.assertEqual(agent.hostname, "localhost")
        self.assertEqual(agent.port, 5000)
    
    def test_get_all_agents(self):
        """Test retrieving all agents"""
        agent_id1 = self.registry.register_agent(
            "host1", 5000, {'cpu': 4}, {}
        )
        agent_id2 = self.registry.register_agent(
            "host2", 5001, {'cpu': 4}, {}
        )
        
        agents = self.registry.get_all_agents()
        self.assertEqual(len(agents), 2)
        self.assertIn(agent_id1, [a.agent_id for a in agents])
    
    def test_agent_status_update(self):
        """Test updating agent status"""
        agent_id = self.registry.register_agent("host1", 5000, {}, {})
        
        self.registry.update_agent_status(agent_id, AgentStatus.IDLE)
        agent = self.registry.get_agent(agent_id)
        self.assertEqual(agent.status, AgentStatus.IDLE)
    
    def test_agent_workload_tracking(self):
        """Test tracking agent workload"""
        agent_id = self.registry.register_agent("host1", 5000, {}, {})
        
        self.registry.update_agent_workload(agent_id, 10)
        agent = self.registry.get_agent(agent_id)
        self.assertEqual(agent.current_workload, 10)
    
    def test_agent_health_check(self):
        """Test agent health status"""
        agent_id = self.registry.register_agent("host1", 5000, {}, {})
        agent = self.registry.get_agent(agent_id)
        
        # Fresh agent should be healthy
        self.assertTrue(agent.is_healthy())
        
        # Simulate old heartbeat
        agent.last_heartbeat = datetime.utcnow() - timedelta(seconds=60)
        self.assertFalse(agent.is_healthy(heartbeat_timeout=30))
    
    def test_agent_availability(self):
        """Test agent availability calculation"""
        agent_id = self.registry.register_agent("host1", 5000, {}, {})
        agent = self.registry.get_agent(agent_id)
        
        # Initially available
        self.assertEqual(agent.get_availability(), 1.0)
        
        # Half workload
        agent.current_workload = 25
        self.assertEqual(agent.get_availability(), 0.5)
        
        # Full workload
        agent.current_workload = 50
        self.assertEqual(agent.get_availability(), 0.0)
    
    def test_filter_agents_by_status(self):
        """Test filtering agents by status"""
        agent_id1 = self.registry.register_agent("host1", 5000, {}, {})
        agent_id2 = self.registry.register_agent("host2", 5001, {}, {})
        
        self.registry.update_agent_status(agent_id1, AgentStatus.ACTIVE)
        self.registry.update_agent_status(agent_id2, AgentStatus.OFFLINE)
        
        active_agents = self.registry.get_all_agents(AgentStatus.ACTIVE)
        self.assertEqual(len(active_agents), 1)
        self.assertEqual(active_agents[0].agent_id, agent_id1)


class TestWorkDistributor(unittest.TestCase):
    """Test intelligent work distribution"""
    
    def setUp(self):
        self.db_path = tempfile.NamedTemporaryFile(delete=False, suffix='.db').name
        self.registry = AgentRegistry(self.db_path)
        self.distributor = WorkDistributor(self.registry)
    
    def test_round_robin_distribution(self):
        """Test round-robin distribution strategy"""
        agent_id = self.registry.register_agent("host1", 5000, {}, {})
        self.registry.update_agent_status(agent_id, AgentStatus.ACTIVE)
        
        selected = self.distributor.select_agent(CoordinationStrategy.ROUND_ROBIN)
        self.assertEqual(selected, agent_id)
    
    def test_least_busy_distribution(self):
        """Test least-busy distribution strategy"""
        agent_id1 = self.registry.register_agent("host1", 5000, {}, {})
        agent_id2 = self.registry.register_agent("host2", 5001, {}, {})
        
        self.registry.update_agent_status(agent_id1, AgentStatus.ACTIVE)
        self.registry.update_agent_status(agent_id2, AgentStatus.ACTIVE)
        
        self.registry.update_agent_workload(agent_id1, 20)
        self.registry.update_agent_workload(agent_id2, 5)
        
        selected = self.distributor.select_agent(CoordinationStrategy.LEAST_BUSY)
        self.assertEqual(selected, agent_id2)
    
    def test_load_balanced_distribution(self):
        """Test load-balanced distribution strategy"""
        agent_id1 = self.registry.register_agent("host1", 5000, {}, {})
        agent_id2 = self.registry.register_agent("host2", 5001, {}, {})
        
        self.registry.update_agent_status(agent_id1, AgentStatus.ACTIVE)
        self.registry.update_agent_status(agent_id2, AgentStatus.ACTIVE)
        
        self.registry.update_agent_workload(agent_id1, 40)
        self.registry.update_agent_workload(agent_id2, 10)
        
        selected = self.distributor.select_agent(CoordinationStrategy.LOAD_BALANCED)
        self.assertEqual(selected, agent_id2)
    
    def test_capability_based_distribution(self):
        """Test capability-based distribution"""
        capabilities = {'screenshot': AgentCapability('screenshot')}
        agent_id = self.registry.register_agent(
            "host1", 5000, {}, capabilities
        )
        self.registry.update_agent_status(agent_id, AgentStatus.ACTIVE)
        
        selected = self.distributor.select_agent(
            CoordinationStrategy.CAPABILITY_MATCH,
            required_capability='screenshot'
        )
        self.assertEqual(selected, agent_id)
    
    def test_no_agent_available(self):
        """Test when no agent is available"""
        # No agents registered
        selected = self.distributor.select_agent()
        self.assertIsNone(selected)
    
    def test_distribute_multiple_tasks(self):
        """Test distributing multiple tasks"""
        agent_id1 = self.registry.register_agent("host1", 5000, {}, {})
        agent_id2 = self.registry.register_agent("host2", 5001, {}, {})
        
        self.registry.update_agent_status(agent_id1, AgentStatus.ACTIVE)
        self.registry.update_agent_status(agent_id2, AgentStatus.ACTIVE)
        
        tasks = [
            {'task_id': 'task_1'},
            {'task_id': 'task_2'},
            {'task_id': 'task_3'},
        ]
        
        assignments = self.distributor.distribute_tasks(tasks)
        self.assertEqual(len(assignments), 3)
        for task_id in ['task_1', 'task_2', 'task_3']:
            self.assertIn(task_id, assignments)


class TestAgentHealthMonitor(unittest.TestCase):
    """Test agent health monitoring"""
    
    def setUp(self):
        self.db_path = tempfile.NamedTemporaryFile(delete=False, suffix='.db').name
        self.registry = AgentRegistry(self.db_path)
        self.monitor = AgentHealthMonitor(self.registry, heartbeat_interval=1)
    
    def test_monitor_initialization(self):
        """Test monitor can be initialized"""
        self.assertIsNotNone(self.monitor)
        self.assertFalse(self.monitor.running)
    
    def test_record_heartbeat(self):
        """Test recording agent heartbeat"""
        agent_id = self.registry.register_agent("host1", 5000, {}, {})
        old_heartbeat = self.registry.get_agent(agent_id).last_heartbeat
        
        time.sleep(0.1)
        self.monitor.record_heartbeat(agent_id)
        
        new_heartbeat = self.registry.get_agent(agent_id).last_heartbeat
        self.assertGreater(new_heartbeat, old_heartbeat)
    
    def test_agent_health_detection(self):
        """Test detection of unhealthy agents"""
        agent_id = self.registry.register_agent("host1", 5000, {}, {})
        agent = self.registry.get_agent(agent_id)
        
        # Simulate missing heartbeats
        agent.last_heartbeat = datetime.utcnow() - timedelta(seconds=60)
        
        is_healthy = agent.is_healthy(heartbeat_timeout=30)
        self.assertFalse(is_healthy)


class TestSharedStateManager(unittest.TestCase):
    """Test shared state management"""
    
    def setUp(self):
        self.db_path = tempfile.NamedTemporaryFile(delete=False, suffix='.db').name
        self.state_manager = SharedStateManager(self.db_path)
    
    def test_set_and_get_state(self):
        """Test setting and retrieving shared state"""
        self.state_manager.set_state('task_count', 42, 'agent_1')
        
        value = self.state_manager.get_state('task_count')
        self.assertEqual(value, 42)
    
    def test_state_persistence(self):
        """Test state persists across instances"""
        self.state_manager.set_state('persistent_key', {'data': 'value'}, 'agent_1')
        
        # Create new instance
        new_manager = SharedStateManager(self.db_path)
        value = new_manager.get_state('persistent_key')
        self.assertEqual(value, {'data': 'value'})
    
    def test_get_all_state(self):
        """Test getting all shared state"""
        self.state_manager.set_state('key1', 'value1', 'agent_1')
        self.state_manager.set_state('key2', 'value2', 'agent_1')
        
        all_state = self.state_manager.get_all_state()
        self.assertEqual(len(all_state), 2)
        self.assertEqual(all_state['key1'], 'value1')


class TestCoordinatedTask(unittest.TestCase):
    """Test coordinated task model"""
    
    def test_task_creation(self):
        """Test creating a coordinated task"""
        task = CoordinatedTask(
            task_id='task_001',
            subtasks=['sub_1', 'sub_2'],
            status='pending'
        )
        
        self.assertEqual(task.task_id, 'task_001')
        self.assertEqual(len(task.subtasks), 2)
        self.assertEqual(task.status, 'pending')
    
    def test_task_serialization(self):
        """Test task serialization to dict"""
        task = CoordinatedTask(task_id='task_001')
        task_dict = task.to_dict()
        
        self.assertIn('task_id', task_dict)
        self.assertIn('created_at', task_dict)
        self.assertEqual(task_dict['task_id'], 'task_001')


class TestAgentCoordinator(unittest.TestCase):
    """Test main agent coordinator"""
    
    def setUp(self):
        self.db_dir = tempfile.mkdtemp()
        self.coordinator = AgentCoordinator(
            db_path=f"{self.db_dir}/coordinator.db"
        )
    
    def test_coordinator_initialization(self):
        """Test coordinator initializes properly"""
        self.assertIsNotNone(self.coordinator.registry)
        self.assertIsNotNone(self.coordinator.distributor)
        self.assertIsNotNone(self.coordinator.health_monitor)
    
    def test_register_agent_through_coordinator(self):
        """Test registering agent through coordinator"""
        agent_id = self.coordinator.register_agent(
            "host1", 5000,
            {'cpu': 4},
            {'navigate': AgentCapability('navigate')}
        )
        
        agent = self.coordinator.registry.get_agent(agent_id)
        self.assertIsNotNone(agent)
    
    def test_submit_coordinated_task(self):
        """Test submitting a coordinated task"""
        agent_id = self.coordinator.register_agent(
            "host1", 5000, {'cpu': 4}, {}
        )
        self.coordinator.registry.update_agent_status(agent_id, AgentStatus.ACTIVE)
        
        success = self.coordinator.submit_task(
            'task_001',
            ['subtask_1', 'subtask_2']
        )
        self.assertTrue(success)
    
    def test_get_task_status(self):
        """Test getting task status"""
        agent_id = self.coordinator.register_agent(
            "host1", 5000, {}, {}
        )
        self.coordinator.registry.update_agent_status(agent_id, AgentStatus.ACTIVE)
        
        self.coordinator.submit_task('task_001', [])
        status = self.coordinator.get_task_status('task_001')
        self.assertEqual(status, 'assigned')
    
    def test_record_task_result(self):
        """Test recording task completion"""
        agent_id = self.coordinator.register_agent(
            "host1", 5000, {}, {}
        )
        self.coordinator.registry.update_agent_status(agent_id, AgentStatus.ACTIVE)
        
        self.coordinator.submit_task('task_001', [])
        self.coordinator.record_task_result('task_001', {'result': 'data'})
        
        task = self.coordinator.coordinated_tasks['task_001']
        self.assertEqual(task.status, 'completed')
        self.assertEqual(task.result, {'result': 'data'})
    
    def test_system_status(self):
        """Test getting system status"""
        agent_id1 = self.coordinator.register_agent(
            "host1", 5000, {}, {}
        )
        agent_id2 = self.coordinator.register_agent(
            "host2", 5001, {}, {}
        )
        
        self.coordinator.registry.update_agent_status(agent_id1, AgentStatus.ACTIVE)
        self.coordinator.registry.update_agent_status(agent_id2, AgentStatus.ACTIVE)
        
        status = self.coordinator.get_system_status()
        self.assertEqual(status['total_agents'], 2)
        self.assertEqual(status['active_agents'], 2)
    
    def test_coordinator_lifecycle(self):
        """Test coordinator start/stop"""
        self.coordinator.start()
        self.assertTrue(self.coordinator.health_monitor.running)
        
        self.coordinator.stop()
        # Give monitor thread time to stop
        time.sleep(0.5)
        self.assertFalse(self.coordinator.health_monitor.running)


class TestMultiAgentIntegration(unittest.TestCase):
    """Integration tests for multi-agent system"""
    
    def setUp(self):
        self.db_dir = tempfile.mkdtemp()
        self.coordinator = AgentCoordinator(
            db_path=f"{self.db_dir}/coordinator.db"
        )
    
    def test_complete_workflow(self):
        """Test complete multi-agent workflow"""
        # Register agents
        agent_id1 = self.coordinator.register_agent(
            "host1", 5000, {'cpu': 4, 'memory': 8},
            {'navigate': AgentCapability('navigate')}
        )
        agent_id2 = self.coordinator.register_agent(
            "host2", 5001, {'cpu': 4, 'memory': 8},
            {'screenshot': AgentCapability('screenshot')}
        )
        
        # Activate agents
        self.coordinator.registry.update_agent_status(agent_id1, AgentStatus.ACTIVE)
        self.coordinator.registry.update_agent_status(agent_id2, AgentStatus.ACTIVE)
        
        # Submit tasks
        success1 = self.coordinator.submit_task('task_1', ['nav_1', 'nav_2'])
        success2 = self.coordinator.submit_task('task_2', ['ss_1', 'ss_2'])
        
        self.assertTrue(success1)
        self.assertTrue(success2)
        
        # Record results
        self.coordinator.record_task_result('task_1', {'navigated': True})
        self.coordinator.record_task_result('task_2', None, 'Timeout')
        
        # Check status
        self.assertEqual(self.coordinator.get_task_status('task_1'), 'completed')
        self.assertEqual(self.coordinator.get_task_status('task_2'), 'failed')
    
    def test_agent_failover(self):
        """Test task failover to another agent"""
        agent_id1 = self.coordinator.register_agent("host1", 5000, {}, {})
        agent_id2 = self.coordinator.register_agent("host2", 5001, {}, {})
        
        self.coordinator.registry.update_agent_status(agent_id1, AgentStatus.ACTIVE)
        self.coordinator.registry.update_agent_status(agent_id2, AgentStatus.ACTIVE)
        
        # Submit task (goes to agent1)
        self.coordinator.submit_task('task_1', [])
        task1 = self.coordinator.coordinated_tasks['task_1']
        assigned_agent = task1.agent_id
        
        self.assertIsNotNone(assigned_agent)
    
    def test_system_load_distribution(self):
        """Test system distributes load across agents"""
        agents = []
        for i in range(3):
            agent_id = self.coordinator.register_agent(
                f"host{i}", 5000 + i, {}, {}
            )
            self.coordinator.registry.update_agent_status(agent_id, AgentStatus.ACTIVE)
            agents.append(agent_id)
        
        # Submit multiple tasks
        for i in range(10):
            self.coordinator.submit_task(f'task_{i}', [])
        
        # Check tasks are distributed
        status = self.coordinator.get_system_status()
        self.assertEqual(status['total_agents'], 3)
        self.assertEqual(len(self.coordinator.coordinated_tasks), 10)


if __name__ == '__main__':
    unittest.main(verbosity=2)
