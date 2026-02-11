"""
Phase 4: Task Queue Processing Tests
Comprehensive test suite for task execution, queue management, and result handling.

Test Coverage:
- Task model and lifecycle
- Task execution with different action types
- Queue processing and task assignment
- Error handling and retries
- Integration with browser pool and resource monitor
"""

import unittest
import sqlite3
import json
import logging
import tempfile
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent))

from task_queue_processor import (
    Task, TaskStatus, TaskPriority, TaskExecutor, TaskQueueProcessor,
    init_queue_tables
)
from config_manager import ConfigManager


class TestTaskModel(unittest.TestCase):
    """Test Task model and serialization"""

    def test_task_creation(self):
        """Test creating a task"""
        task = Task(
            task_id="test_123",
            action="navigate",
            url="https://example.com"
        )
        self.assertEqual(task.task_id, "test_123")
        self.assertEqual(task.action, "navigate")
        self.assertEqual(task.url, "https://example.com")
        self.assertEqual(task.status, TaskStatus.PENDING)
        self.assertIsNotNone(task.created_at)

    def test_task_to_dict(self):
        """Test converting task to dictionary"""
        task = Task(
            task_id="test_123",
            action="execute_js",
            javascript="return document.title;",
            priority=TaskPriority.HIGH
        )
        task_dict = task.to_dict()
        self.assertEqual(task_dict['task_id'], "test_123")
        self.assertEqual(task_dict['action'], "execute_js")
        self.assertEqual(task_dict['priority'], TaskPriority.HIGH.value)
        self.assertEqual(task_dict['status'], TaskStatus.PENDING.value)

    def test_task_from_dict(self):
        """Test creating task from dictionary"""
        task_dict = {
            'task_id': 'test_456',
            'action': 'navigate',
            'url': 'https://example.com',
            'priority': TaskPriority.NORMAL.value,
            'timeout': 30,
            'max_retries': 3,
            'created_at': datetime.now().isoformat(),
            'assigned_at': None,
            'completed_at': None,
            'result': None,
            'error': None,
            'retry_count': 0,
            'status': TaskStatus.PENDING.value,
            'parameters': None,
            'javascript': None
        }
        task = Task.from_dict(task_dict)
        self.assertEqual(task.task_id, 'test_456')
        self.assertEqual(task.status, TaskStatus.PENDING)

    def test_task_status_transitions(self):
        """Test task status transitions"""
        task = Task(task_id="test_789", action="navigate", url="https://example.com")
        
        # Progress through statuses
        task.status = TaskStatus.ASSIGNED
        self.assertEqual(task.status, TaskStatus.ASSIGNED)
        
        task.status = TaskStatus.EXECUTING
        self.assertEqual(task.status, TaskStatus.EXECUTING)
        
        task.status = TaskStatus.COMPLETED
        self.assertEqual(task.status, TaskStatus.COMPLETED)
        self.assertIsNotNone(task.completed_at)


class TestTaskExecutor(unittest.TestCase):
    """Test TaskExecutor class"""

    def setUp(self):
        """Setup test fixtures"""
        self.mock_config = MagicMock()
        self.mock_config.get = MagicMock(side_effect=lambda key, default=None: {
            'task_settings': {'timeout': 30, 'max_retries': 3},
            'browser_settings': {'max_browsers': 25}
        }.get(key, default))
        self.executor = TaskExecutor(self.mock_config)
        self.mock_browser = MagicMock()

    def test_executor_initialization(self):
        """Test TaskExecutor initializes correctly"""
        self.assertIsNotNone(self.executor)
        self.assertEqual(self.executor.config, self.config)

    def test_navigate_action(self):
        """Test navigate action execution"""
        task = Task(
            task_id="nav_001",
            action="navigate",
            url="https://example.com"
        )
        self.mock_browser.get = MagicMock()
        self.mock_browser.current_url = "https://example.com/"

        result = self.executor.execute(task, self.mock_browser)
        
        self.assertEqual(result['status'], 'success')
        self.mock_browser.get.assert_called_once_with("https://example.com")
        self.assertIn('duration', result)

    def test_execute_js_action(self):
        """Test JavaScript execution action"""
        task = Task(
            task_id="js_001",
            action="execute_js",
            javascript="return document.title;"
        )
        self.mock_browser.execute_script = MagicMock(return_value="Test Page")

        result = self.executor.execute(task, self.mock_browser)
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['output'], "Test Page")
        self.mock_browser.execute_script.assert_called_once()

    def test_screenshot_action(self):
        """Test screenshot action"""
        task = Task(
            task_id="ss_001",
            action="screenshot"
        )
        fake_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        self.mock_browser.get_screenshot_as_base64 = MagicMock(return_value=fake_b64)

        result = self.executor.execute(task, self.mock_browser)
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['output'], fake_b64)

    def test_click_action(self):
        """Test click action"""
        task = Task(
            task_id="click_001",
            action="click",
            parameters={"selector": "button.submit"}
        )
        mock_element = MagicMock()
        mock_element.click = MagicMock()
        self.mock_browser.find_element = MagicMock(return_value=mock_element)

        result = self.executor.execute(task, self.mock_browser)
        
        self.assertEqual(result['status'], 'success')
        mock_element.click.assert_called_once()

    def test_get_text_action(self):
        """Test get_text action"""
        task = Task(
            task_id="txt_001",
            action="get_text",
            parameters={"selector": "h1"}
        )
        mock_element = MagicMock()
        mock_element.text = "Welcome to Example"
        self.mock_browser.find_element = MagicMock(return_value=mock_element)

        result = self.executor.execute(task, self.mock_browser)
        
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['output'], "Welcome to Example")

    def test_timeout_handling(self):
        """Test timeout error handling"""
        from selenium.common.exceptions import TimeoutException
        
        task = Task(
            task_id="timeout_001",
            action="navigate",
            url="https://example.com",
            timeout=1
        )
        self.mock_browser.get = MagicMock(side_effect=TimeoutException("Timeout"))

        result = self.executor.execute(task, self.mock_browser)
        
        self.assertEqual(result['status'], 'timeout')
        self.assertIn('timeout', result['error'].lower())

    def test_browser_error_handling(self):
        """Test browser error handling"""
        from selenium.common.exceptions import WebDriverException
        
        task = Task(
            task_id="browser_error_001",
            action="navigate",
            url="https://example.com"
        )
        self.mock_browser.get = MagicMock(side_effect=WebDriverException("Connection refused"))

        result = self.executor.execute(task, self.mock_browser)
        
        self.assertEqual(result['status'], 'browser_error')
        self.assertIsNotNone(result['error'])

    def test_unknown_action_error(self):
        """Test error on unknown action"""
        task = Task(
            task_id="unknown_001",
            action="unknown_action"
        )

        result = self.executor.execute(task, self.mock_browser)
        
        self.assertEqual(result['status'], 'error')
        self.assertIn('unknown', result['error'].lower())


class TestTaskQueueProcessor(unittest.TestCase):
    """Test TaskQueueProcessor class"""

    def setUp(self):
        """Setup test fixtures"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db_path = self.temp_db.name
        self.temp_db.close()

        # Initialize database
        init_queue_tables(self.db_path)

        self.mock_config = MagicMock()
        self.mock_config.get = MagicMock(side_effect=lambda key, default=None: {
            'task_settings': {'timeout': 30, 'max_retries': 3},
            'browser_settings': {'max_browsers': 25}
        }.get(key, default))
        self.mock_pool = MagicMock()
        self.mock_monitor = MagicMock()
        self.mock_monitor.should_pause_tasks = MagicMock(return_value=False)

        self.processor = TaskQueueProcessor(
            agent_id="test_agent_001",
            db_path=self.db_path,
            config=self.mock_config,
            browser_pool=self.mock_pool,
            resource_monitor=self.mock_monitor
        )

    def tearDown(self):
        """Cleanup"""
        import os
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_processor_initialization(self):
        """Test TaskQueueProcessor initializes correctly"""
        self.assertEqual(self.processor.agent_id, "test_agent_001")
        self.assertFalse(self.processor.running)
        self.assertIsNotNone(self.processor.executor)
        self.assertEqual(len(self.processor.active_tasks), 0)

    def test_processor_start_stop(self):
        """Test starting and stopping processor"""
        self.processor.start()
        self.assertTrue(self.processor.running)

        self.processor.stop()
        self.assertFalse(self.processor.running)

    def test_processor_status(self):
        """Test getting processor status"""
        self.processor.start()
        status = self.processor.get_status()

        self.assertIn('active_tasks', status)
        self.assertIn('tasks_processed', status)
        self.assertIn('status', status)
        self.assertEqual(status['status'], 'running')

        self.processor.stop()

    def test_add_task_to_queue(self):
        """Test adding task to queue database"""
        task = Task(
            task_id="queue_001",
            action="navigate",
            url="https://example.com"
        )

        # Store task to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO tasks_queue (task_id, status, task_data, priority, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            task.task_id,
            task.status.value,
            json.dumps(task.to_dict()),
            task.priority.value,
            task.created_at.isoformat(),
            datetime.now().isoformat()
        ))
        conn.commit()
        conn.close()

        # Verify task in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT task_id FROM tasks_queue WHERE task_id = ?", (task.task_id,))
        result = cursor.fetchone()
        conn.close()

        self.assertIsNotNone(result)
        self.assertEqual(result[0], "queue_001")

    def test_metrics_tracking(self):
        """Test metrics are tracked correctly"""
        self.assertEqual(self.processor.metrics['tasks_completed'], 0)
        self.assertEqual(self.processor.metrics['tasks_failed'], 0)

        # Simulate task completion
        self.processor.metrics['tasks_completed'] += 1
        self.processor.metrics['total_execution_time'] += 2.5

        self.assertEqual(self.processor.metrics['tasks_completed'], 1)
        self.assertGreater(self.processor.metrics['total_execution_time'], 0)

    def test_pause_tasks_when_resources_constrained(self):
        """Test task processing is paused when resources are constrained"""
        self.processor.start()
        self.mock_monitor.should_pause_tasks = MagicMock(return_value=True)

        # Call update - should skip processing due to pause
        self.processor.update()

        # Verify get_available_browser was not called (no tasks processed)
        self.mock_pool.get_available_browser.assert_not_called()

        self.processor.stop()

    def test_task_result_storage(self):
        """Test storing task result to database"""
        task = Task(task_id="result_001", action="navigate", url="https://example.com")
        result = {
            'status': 'success',
            'output': 'https://example.com/',
            'error': None,
            'duration': 1.5,
            'timestamp': datetime.now().isoformat()
        }

        self.processor._store_result_to_db(task, result)

        # Verify result in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT task_id FROM results_buffer WHERE task_id = ?", (task.task_id,))
        db_result = cursor.fetchone()
        conn.close()

        self.assertIsNotNone(db_result)
        self.assertEqual(db_result[0], "result_001")

    def test_get_pending_tasks(self):
        """Test retrieving pending tasks from database"""
        # Add test tasks
        for i in range(3):
            task = Task(
                task_id=f"pending_{i:03d}",
                action="navigate",
                url=f"https://example{i}.com"
            )
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tasks_queue (task_id, status, task_data, priority, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                task.task_id,
                TaskStatus.PENDING.value,
                json.dumps(task.to_dict()),
                task.priority.value,
                task.created_at.isoformat(),
                datetime.now().isoformat()
            ))
            conn.commit()
            conn.close()

        pending = self.processor._get_pending_tasks_from_db()
        self.assertEqual(len(pending), 3)

    def test_retry_logic(self):
        """Test retry logic for failed tasks"""
        task = Task(
            task_id="retry_001",
            action="navigate",
            url="https://example.com",
            max_retries=3,
            status=TaskStatus.FAILED
        )
        task.retry_count = 1

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO tasks_queue (task_id, status, task_data, priority, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            task.task_id,
            task.status.value,
            json.dumps(task.to_dict()),
            task.priority.value,
            task.created_at.isoformat(),
            datetime.now().isoformat()
        ))
        conn.commit()
        conn.close()

        # Get failed tasks
        failed = self.processor._get_failed_tasks_from_db()
        self.assertEqual(len(failed), 1)
        self.assertEqual(failed[0]['task_id'], 'retry_001')


class TestQueueIntegration(unittest.TestCase):
    """Integration tests with browser pool and resource monitor"""

    def setUp(self):
        """Setup test fixtures"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db_path = self.temp_db.name
        self.temp_db.close()
        init_queue_tables(self.db_path)

        self.mock_config = MagicMock()
        self.mock_config.get = MagicMock(side_effect=lambda key, default=None: {
            'task_settings': {'timeout': 30, 'max_retries': 3},
            'browser_settings': {'max_browsers': 25}
        }.get(key, default))
        self.mock_pool = MagicMock()
        self.mock_monitor = MagicMock()
        self.mock_monitor.should_pause_tasks = MagicMock(return_value=False)
        self.mock_monitor.should_throttle = MagicMock(return_value=False)

        self.processor = TaskQueueProcessor(
            agent_id="integration_test",
            db_path=self.db_path,
            config=self.mock_config,
            browser_pool=self.mock_pool,
            resource_monitor=self.mock_monitor
        )

    def tearDown(self):
        """Cleanup"""
        import os
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_full_execution_cycle(self):
        """Test complete task execution cycle"""
        self.processor.start()

        # Create and queue a task
        task = Task(
            task_id="cycle_001",
            action="navigate",
            url="https://example.com"
        )

        # Mock browser
        mock_browser = MagicMock()
        mock_browser.current_url = "https://example.com/"
        self.mock_pool.get_available_browser = MagicMock(return_value=mock_browser)

        # Store task to queue
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO tasks_queue (task_id, status, task_data, priority, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            task.task_id,
            task.status.value,
            json.dumps(task.to_dict()),
            task.priority.value,
            task.created_at.isoformat(),
            datetime.now().isoformat()
        ))
        conn.commit()
        conn.close()

        # Process tasks
        self.processor.update()

        # Verify browser was used
        self.mock_pool.get_available_browser.assert_called()

        self.processor.stop()

    def test_multiple_tasks_execution(self):
        """Test executing multiple tasks in sequence"""
        self.processor.start()

        tasks = [
            Task(task_id=f"multi_{i:03d}", action="navigate", url=f"https://example{i}.com")
            for i in range(3)
        ]

        mock_browser = MagicMock()
        mock_browser.current_url = "https://example.com/"
        self.mock_pool.get_available_browser = MagicMock(return_value=mock_browser)

        # Store all tasks
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        for task in tasks:
            cursor.execute("""
                INSERT INTO tasks_queue (task_id, status, task_data, priority, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                task.task_id,
                task.status.value,
                json.dumps(task.to_dict()),
                task.priority.value,
                task.created_at.isoformat(),
                datetime.now().isoformat()
            ))
        conn.commit()
        conn.close()

        # Verify tasks queued
        pending = self.processor._get_pending_tasks_from_db()
        self.assertGreaterEqual(len(pending), 1)

        self.processor.stop()


if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(
        level=logging.WARNING,  # Suppress info/debug during tests
        format='%(name)s - %(levelname)s - %(message)s'
    )
    
    unittest.main(verbosity=2)
