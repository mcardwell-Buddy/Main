"""
Phase 4: Task Queue Processing Engine
Handles incoming tasks, assigns to browsers, executes, and reports results.

Architecture:
- TaskQueueProcessor: Main orchestrator listening to Firebase
- TaskExecutor: Executes individual tasks in browsers
- Task monitoring with retry logic and error recovery
- Thread-safe queue management with browser assignment
"""

import sqlite3
import json
import logging
import threading
import time
import traceback
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Dict, Any, List
from pathlib import Path

from selenium.common.exceptions import TimeoutException, WebDriverException
import firebase_admin
from firebase_admin import db as firebase_db
from config_manager import ConfigManager
from browser_pool_manager import BrowserPoolManager
from resource_monitor import ResourceMonitor

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task lifecycle states"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 3
    NORMAL = 2
    HIGH = 1
    CRITICAL = 0


@dataclass
class Task:
    """Represents a task to be executed"""
    task_id: str
    action: str  # "navigate", "execute_js", "screenshot", "click", etc.
    url: Optional[str] = None  # For navigation
    javascript: Optional[str] = None  # For JS execution
    parameters: Optional[Dict[str, Any]] = None
    priority: TaskPriority = TaskPriority.NORMAL
    timeout: int = 30  # seconds
    max_retries: int = 3
    created_at: datetime = None
    assigned_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retry_count: int = 0
    status: TaskStatus = TaskStatus.PENDING

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary for storage"""
        d = asdict(self)
        d['status'] = self.status.value
        d['priority'] = self.priority.value
        d['action'] = str(self.action)
        d['created_at'] = self.created_at.isoformat()
        d['assigned_at'] = self.assigned_at.isoformat() if self.assigned_at else None
        d['completed_at'] = self.completed_at.isoformat() if self.completed_at else None
        return d

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Task':
        """Create task from dictionary"""
        data['status'] = TaskStatus(data['status'])
        data['priority'] = TaskPriority(data['priority'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['assigned_at'] = datetime.fromisoformat(data['assigned_at']) if data['assigned_at'] else None
        data['completed_at'] = datetime.fromisoformat(data['completed_at']) if data['completed_at'] else None
        return Task(**data)


class TaskExecutor:
    """Executes tasks in a browser instance"""

    def __init__(self, config: ConfigManager):
        """Initialize task executor
        
        Args:
            config: Configuration manager instance
        """
        self.config = config
        self.task_timeout = config.get('task_settings', {}).get('timeout', 30)
        self.max_retries = config.get('task_settings', {}).get('max_retries', 3)

    def execute(self, task: Task, browser) -> Dict[str, Any]:
        """Execute a task in the provided browser
        
        Args:
            task: Task to execute
            browser: Selenium WebDriver instance
            
        Returns:
            Dictionary with result/status/error
        """
        start_time = time.time()
        result = {
            'task_id': task.task_id,
            'status': 'success',
            'output': None,
            'error': None,
            'duration': 0,
            'timestamp': datetime.now().isoformat()
        }

        try:
            # Set timeout for this task
            browser.set_script_timeout(task.timeout)
            browser.set_page_load_timeout(task.timeout)

            # Route to appropriate action handler
            if task.action == 'navigate':
                output = self._handle_navigate(task, browser)
            elif task.action == 'execute_js':
                output = self._handle_execute_js(task, browser)
            elif task.action == 'screenshot':
                output = self._handle_screenshot(task, browser)
            elif task.action == 'click':
                output = self._handle_click(task, browser)
            elif task.action == 'get_text':
                output = self._handle_get_text(task, browser)
            else:
                raise ValueError(f"Unknown action: {task.action}")

            result['output'] = output
            logger.info(f"✅ Task {task.task_id} ({task.action}) executed successfully")

        except TimeoutException as e:
            result['status'] = 'timeout'
            result['error'] = f"Task timeout after {task.timeout}s: {str(e)}"
            logger.warning(f"⏱️  Task {task.task_id} timed out: {result['error']}")

        except WebDriverException as e:
            result['status'] = 'browser_error'
            result['error'] = f"Browser error: {str(e)}"
            logger.error(f"🔴 Browser error executing task {task.task_id}: {result['error']}")

        except Exception as e:
            result['status'] = 'error'
            result['error'] = f"{type(e).__name__}: {str(e)}"
            logger.error(f"❌ Error executing task {task.task_id}: {result['error']}\n{traceback.format_exc()}")

        finally:
            result['duration'] = time.time() - start_time

        return result

    def _handle_navigate(self, task: Task, browser) -> str:
        """Navigate to URL
        
        Args:
            task: Task with URL
            browser: Selenium WebDriver
            
        Returns:
            URL that was navigated to
        """
        if not task.url:
            raise ValueError("navigate action requires 'url' parameter")

        logger.debug(f"Navigating to {task.url}...")
        browser.get(task.url)
        return browser.current_url

    def _handle_execute_js(self, task: Task, browser) -> Any:
        """Execute JavaScript code
        
        Args:
            task: Task with javascript code
            browser: Selenium WebDriver
            
        Returns:
            Result of JavaScript execution
        """
        if not task.javascript:
            raise ValueError("execute_js action requires 'javascript' parameter")

        logger.debug(f"Executing JavaScript ({len(task.javascript)} chars)...")
        result = browser.execute_script(task.javascript)
        return result

    def _handle_screenshot(self, task: Task, browser) -> str:
        """Take screenshot and return base64
        
        Args:
            task: Task
            browser: Selenium WebDriver
            
        Returns:
            Base64 encoded screenshot
        """
        logger.debug("Taking screenshot...")
        screenshot_b64 = browser.get_screenshot_as_base64()
        return screenshot_b64

    def _handle_click(self, task: Task, browser) -> Dict[str, str]:
        """Click on element specified by selector
        
        Args:
            task: Task with selector parameter
            browser: Selenium WebDriver
            
        Returns:
            Status dict
        """
        if not task.parameters or 'selector' not in task.parameters:
            raise ValueError("click action requires 'selector' in parameters")

        selector = task.parameters['selector']
        logger.debug(f"Clicking element: {selector}")
        element = browser.find_element("css selector", selector)
        element.click()
        return {"selector": selector, "status": "clicked"}

    def _handle_get_text(self, task: Task, browser) -> str:
        """Get text from element specified by selector
        
        Args:
            task: Task with selector parameter
            browser: Selenium WebDriver
            
        Returns:
            Text content of element
        """
        if not task.parameters or 'selector' not in task.parameters:
            raise ValueError("get_text action requires 'selector' in parameters")

        selector = task.parameters['selector']
        logger.debug(f"Getting text from: {selector}")
        element = browser.find_element("css selector", selector)
        return element.text


class TaskQueueProcessor:
    """Main task queue processor - orchestrates execution"""

    def __init__(self, agent_id: str, db_path: str, config: ConfigManager,
                 browser_pool: BrowserPoolManager, resource_monitor: ResourceMonitor):
        """Initialize task queue processor
        
        Args:
            agent_id: Agent identifier
            db_path: SQLite database path
            config: Configuration manager
            browser_pool: Browser pool manager
            resource_monitor: Resource monitor
        """
        self.agent_id = agent_id
        self.db_path = db_path
        self.config = config
        self.browser_pool = browser_pool
        self.resource_monitor = resource_monitor
        self.running = False
        self.lock = threading.Lock()

        # Initialize task executor
        self.executor = TaskExecutor(config)

        # Task tracking
        self.active_tasks: Dict[str, Task] = {}
        self.task_results: Dict[str, Dict[str, Any]] = {}

        # Performance metrics
        self.metrics = {
            'tasks_received': 0,
            'tasks_completed': 0,
            'tasks_failed': 0,
            'tasks_retried': 0,
            'total_execution_time': 0,
            'average_task_time': 0,
        }

        logger.info(f"✅ TaskQueueProcessor initialized for agent {agent_id}")

    def start(self):
        """Start the task queue processor"""
        self.running = True
        logger.info("🟢 Task Queue Processor starting...")
        
        # Initialize Firebase listener if available
        try:
            self._setup_firebase_listener()
            logger.info("✅ Firebase task listener initialized")
        except Exception as e:
            logger.warning(f"⚠️  Firebase listener not available: {e}")

    def stop(self):
        """Stop the task queue processor"""
        self.running = False
        logger.info("🔴 Task Queue Processor stopping...")

    def update(self):
        """Called periodically to process tasks from queue
        
        This is called from the main agent loop every ~5 seconds
        """
        if not self.running:
            return

        try:
            # Check if we should pause due to resources
            if self.resource_monitor.should_pause_tasks():
                logger.debug("⏸️  Task processing paused - resources constrained")
                return

            # Process pending tasks
            self._process_pending_tasks()

            # Monitor active tasks (check for completion, timeouts)
            self._monitor_active_tasks()

            # Handle retries
            self._process_retries()

        except Exception as e:
            logger.error(f"❌ Error in update cycle: {e}\n{traceback.format_exc()}")

    def _process_pending_tasks(self):
        """Get pending tasks from queue and assign to browsers"""
        with self.lock:
            # Get pending tasks from database
            pending_tasks = self._get_pending_tasks_from_db()

            for task_data in pending_tasks:
                task = Task.from_dict(task_data)

                # Only assign if we have available browsers
                available_browser = self.browser_pool.get_available_browser()
                if not available_browser:
                    logger.debug(f"⏳ No available browsers for task {task.task_id}")
                    continue

                # Assign task to browser
                self._assign_task(task, available_browser)

    def _assign_task(self, task: Task, browser):
        """Assign and begin executing a task
        
        Args:
            task: Task to assign
            browser: Browser instance to execute in
        """
        task.status = TaskStatus.ASSIGNED
        task.assigned_at = datetime.now()
        self.active_tasks[task.task_id] = task

        # Execute task
        logger.info(f"🎯 Executing task {task.task_id} ({task.action}) in browser")

        try:
            result = self.executor.execute(task, browser)

            # Update task status
            task.status = TaskStatus.COMPLETED if result['status'] == 'success' else TaskStatus.FAILED
            task.completed_at = datetime.now()
            task.result = result

            # Store result
            self._store_task_result(task, result)

            # Update metrics
            self.metrics['tasks_completed'] += 1
            if result['status'] != 'success':
                self.metrics['tasks_failed'] += 1
            self.metrics['total_execution_time'] += result['duration']

            # Clean up
            del self.active_tasks[task.task_id]

        except Exception as e:
            logger.error(f"❌ Task execution error: {e}")
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.retry_count += 1

    def _process_retries(self):
        """Check failed tasks and retry if within retry limit"""
        with self.lock:
            failed_tasks = self._get_failed_tasks_from_db()

            for task_data in failed_tasks:
                task = Task.from_dict(task_data)

                if task.retry_count < task.max_retries:
                    logger.info(f"🔄 Retrying task {task.task_id} (attempt {task.retry_count + 1}/{task.max_retries})")
                    task.status = TaskStatus.RETRYING
                    task.retry_count += 1
                    self.metrics['tasks_retried'] += 1

                    # Update in database
                    self._update_task_in_db(task)

    def _monitor_active_tasks(self):
        """Monitor active tasks for completion"""
        # This would be used for polling-based task monitoring if needed
        # For now, tasks are executed synchronously in _assign_task
        pass

    def _store_task_result(self, task: Task, result: Dict[str, Any]):
        """Store task result to database and Firebase
        
        Args:
            task: Task that was executed
            result: Result dictionary
        """
        try:
            # Store to SQLite
            self._store_result_to_db(task, result)

            # Store to Firebase if available
            self._store_result_to_firebase(task, result)

        except Exception as e:
            logger.error(f"❌ Error storing task result: {e}")

    def _get_pending_tasks_from_db(self) -> List[Dict[str, Any]]:
        """Get pending tasks from SQLite queue
        
        Returns:
            List of task dictionaries
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT task_data FROM tasks_queue 
                WHERE status = ? 
                ORDER BY priority ASC, created_at ASC 
                LIMIT 5
            """, (TaskStatus.PENDING.value,))

            rows = cursor.fetchall()
            tasks = [json.loads(row['task_data']) for row in rows]
            conn.close()

            return tasks

        except Exception as e:
            logger.error(f"❌ Error getting pending tasks: {e}")
            return []

    def _get_failed_tasks_from_db(self) -> List[Dict[str, Any]]:
        """Get failed tasks that can be retried
        
        Returns:
            List of task dictionaries
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT task_data FROM tasks_queue 
                WHERE status = ? AND retry_count < max_retries
                ORDER BY created_at ASC 
                LIMIT 3
            """, (TaskStatus.FAILED.value,))

            rows = cursor.fetchall()
            tasks = [json.loads(row['task_data']) for row in rows]
            conn.close()

            return tasks

        except Exception as e:
            logger.error(f"❌ Error getting failed tasks: {e}")
            return []

    def _update_task_in_db(self, task: Task):
        """Update task in database
        
        Args:
            task: Task to update
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE tasks_queue 
                SET task_data = ?
                WHERE task_id = ?
            """, (json.dumps(task.to_dict()), task.task_id))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"❌ Error updating task in DB: {e}")

    def _store_result_to_db(self, task: Task, result: Dict[str, Any]):
        """Store result to SQLite results_buffer
        
        Args:
            task: Completed task
            result: Result dictionary
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            result_entry = {
                'task_id': task.task_id,
                'agent_id': self.agent_id,
                'status': result['status'],
                'result': result['output'],
                'error': result['error'],
                'duration': result['duration'],
                'timestamp': result['timestamp'],
                'completed_at': datetime.now().isoformat()
            }

            cursor.execute("""
                INSERT INTO results_buffer 
                (task_id, agent_id, result_data, created_at)
                VALUES (?, ?, ?, ?)
            """, (
                task.task_id,
                self.agent_id,
                json.dumps(result_entry),
                datetime.now().isoformat()
            ))

            conn.commit()
            conn.close()

            logger.debug(f"📝 Result for task {task.task_id} stored to database")

        except Exception as e:
            logger.error(f"❌ Error storing result to DB: {e}")

    def _store_result_to_firebase(self, task: Task, result: Dict[str, Any]):
        """Store result to Firebase
        
        Args:
            task: Completed task
            result: Result dictionary
        """
        try:
            if not firebase_admin._apps:
                logger.warning("Firebase not initialized")
                return

            firebase_db.reference(f"agents/{self.agent_id}/results/{task.task_id}").set({
                'status': result['status'],
                'output': result['output'],
                'error': result['error'],
                'duration': result['duration'],
                'timestamp': result['timestamp'],
                'completed_at': datetime.now().isoformat()
            })

            logger.debug(f"☁️  Result for task {task.task_id} synced to Firebase")

        except Exception as e:
            logger.debug(f"⚠️  Could not sync to Firebase: {e}")

    def _setup_firebase_listener(self):
        """Setup Firebase listener for real-time task updates"""
        if not firebase_admin._apps:
            logger.warning("Firebase not initialized for listener")
            return

        # This would set up a listener on Firebase tasks
        # For now, we poll from SQLite in the update() method
        logger.info("Firebase listener setup ready")

    def get_status(self) -> Dict[str, Any]:
        """Get queue processor status
        
        Returns:
            Status dictionary
        """
        return {
            'active_tasks': len(self.active_tasks),
            'tasks_processed': self.metrics['tasks_completed'],
            'tasks_failed': self.metrics['tasks_failed'],
            'tasks_retried': self.metrics['tasks_retried'],
            'average_task_time': (self.metrics['average_task_time'] / max(1, self.metrics['tasks_completed'])),
            'status': 'running' if self.running else 'stopped'
        }


def init_queue_tables(db_path: str):
    """Initialize/verify task queue database tables
    
    Args:
        db_path: Path to SQLite database
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Verify tasks_queue table exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks_queue (
                task_id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                task_data TEXT NOT NULL,
                priority INTEGER DEFAULT 2,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        # Verify results_buffer table exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS results_buffer (
                result_id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                result_data TEXT NOT NULL,
                synced BOOLEAN DEFAULT 0,
                created_at TEXT NOT NULL
            )
        """)

        conn.commit()
        conn.close()

        logger.info("✅ Queue tables initialized/verified")

    except Exception as e:
        logger.error(f"❌ Error initializing queue tables: {e}")
