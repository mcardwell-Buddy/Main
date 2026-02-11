"""
Buddy Local Agent - Main Daemon
Phase 1: Foundation

The core local agent that:
- Runs as a daemon
- Connects to Firebase
- Polls for tasks
- Updates heartbeat
- Manages graceful shutdown
"""

import os
import sys
import time
import json
import signal
import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Import Firebase
import firebase_admin
from firebase_admin import credentials, firestore

# Import resource monitor (Phase 2)
from resource_monitor import ResourceMonitor

# Import browser pool manager (Phase 3)
from browser_pool_manager import BrowserPoolManager

# Import task queue processor (Phase 4)
from task_queue_processor import TaskQueueProcessor, init_queue_tables

# Import task scheduler and workflow orchestrator (Phase 5)
from task_scheduler import TaskScheduler, WorkflowOrchestrator, init_phase5_tables

# Import multi-agent coordinator (Phase 6)
from multi_agent_coordinator import (
    AgentCoordinator, AgentCapability, AgentStatus, CoordinationStrategy,
    init_phase6_tables
)

# Import analytics engine (Phase 7)
sys.path.insert(0, str(PROJECT_DIR))
from analytics_engine import AnalyticsEngine

# Setup paths
BASE_DIR = Path(__file__).parent
PROJECT_DIR = BASE_DIR.parent
sys.path.insert(0, str(BASE_DIR))

# Load environment
load_dotenv(PROJECT_DIR / '.env')

# Configure logging
LOG_DIR = PROJECT_DIR / 'logs'
LOG_DIR.mkdir(exist_ok=True)

log_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# File handler
file_handler = logging.FileHandler(LOG_DIR / 'buddy_local.log')
file_handler.setFormatter(log_formatter)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)

logger = logging.getLogger('BuddyLocalAgent')
logger.setLevel(logging.DEBUG)
logger.addHandler(file_handler)
logger.addHandler(console_handler)


class BuddyLocalAgent:
    """Main local agent daemon."""
    
    def __init__(self):
        """Initialize local agent."""
        self.agent_id = self._get_agent_id()
        self.db = None
        self.firestore = None
        self.running = False
        self.start_time = None
        self.tasks_processed = 0
        self.tasks_failed = 0
        
        # Phase 2: Resource monitoring
        self.resource_monitor = ResourceMonitor()
        
        # Phase 3: Browser pool management
        self.browser_pool = None
        
        # Phase 4: Task queue processing
        self.task_queue = None
        
        # Phase 5: Task scheduling and workflows
        self.task_scheduler = None
        self.workflow_orchestrator = None
        
        # Phase 6: Multi-agent coordination
        self.agent_coordinator = None
        self.registered_agent_id = None
        
        # Phase 7: Advanced analytics
        self.analytics_engine = None
        
        logger.info(f"Initializing Buddy Local Agent (ID: {self.agent_id})")
    
    def _get_agent_id(self) -> str:
        """Get or create agent ID."""
        agent_id_file = PROJECT_DIR / 'config' / 'agent_id.txt'
        agent_id_file.parent.mkdir(exist_ok=True)
        
        if agent_id_file.exists():
            return agent_id_file.read_text().strip()
        
        # Generate new agent ID
        import uuid
        import socket
        hostname = socket.gethostname()
        agent_id = f"local-{hostname.lower()}-{str(uuid.uuid4())[:8]}"
        
        agent_id_file.write_text(agent_id)
        return agent_id
    
    def initialize(self) -> bool:
        """Initialize all connections and database."""
        try:
            # Initialize Firebase
            if not firebase_admin._apps:
                logger.info("Initializing Firebase...")
                service_account = os.getenv('FIREBASE_SERVICE_ACCOUNT')
                
                if service_account and os.path.exists(service_account):
                    cred = credentials.Certificate(service_account)
                    firebase_admin.initialize_app(cred)
                else:
                    # Use application default credentials
                    cred = credentials.ApplicationDefault()
                    firebase_admin.initialize_app(cred)
                
                logger.info("✅ Firebase initialized")
            
            self.firestore = firestore.client()
            
            # Initialize SQLite
            logger.info("Initializing SQLite database...")
            self._init_database()
            logger.info("✅ SQLite initialized")
            
            # Initialize browser pool (Phase 3)
            logger.info("Initializing browser pool...")
            self.browser_pool = BrowserPoolManager(self.resource_monitor)
            logger.info("✅ Browser pool initialized")
            
            # Initialize task queue processor (Phase 4)
            logger.info("Initializing task queue processor...")
            from config_manager import ConfigManager
            config = ConfigManager()
            init_queue_tables(str(PROJECT_DIR / 'local_data' / 'buddy_local.db'))
            self.task_queue = TaskQueueProcessor(
                agent_id=self.agent_id,
                db_path=str(PROJECT_DIR / 'local_data' / 'buddy_local.db'),
                config=config,
                browser_pool=self.browser_pool,
                resource_monitor=self.resource_monitor
            )
            logger.info("✅ Task queue processor initialized")
            
            # Initialize task scheduler (Phase 5)
            logger.info("Initializing task scheduler...")
            init_phase5_tables(str(PROJECT_DIR / 'local_data' / 'buddy_local.db'))
            self.task_scheduler = TaskScheduler(str(PROJECT_DIR / 'local_data' / 'buddy_local.db'))
            logger.info("✅ Task scheduler initialized")
            
            # Initialize workflow orchestrator (Phase 5)
            logger.info("Initializing workflow orchestrator...")
            self.workflow_orchestrator = WorkflowOrchestrator(str(PROJECT_DIR / 'local_data' / 'buddy_local.db'))
            logger.info("✅ Workflow orchestrator initialized")
            
            # Initialize agent coordinator (Phase 6)
            logger.info("Initializing agent coordinator...")
            init_phase6_tables({
                'coordinator': str(PROJECT_DIR / 'local_data' / 'buddy_coordinator.db')
            })
            self.agent_coordinator = AgentCoordinator(
                db_path=str(PROJECT_DIR / 'local_data' / 'buddy_coordinator.db')
            )
            
            # Register this agent with coordinator
            capabilities = {
                'navigate': AgentCapability('navigate'),
                'screenshot': AgentCapability('screenshot'),
                'click': AgentCapability('click'),
                'get_text': AgentCapability('get_text'),
                'execute_js': AgentCapability('execute_js'),
            }
            
            resource_capacity = {
                'cpu': os.cpu_count() or 4,
                'memory': int(self.resource_monitor.get_system_status()['memory_available']),
                'browsers': self.browser_pool.max_size if self.browser_pool else 20
            }
            
            self.registered_agent_id = self.agent_coordinator.register_agent(
                hostname=os.getenv('AGENT_HOSTNAME', 'localhost'),
                port=int(os.getenv('AGENT_PORT', '5000')),
                resource_capacity=resource_capacity,
                capabilities=capabilities
            )
            
            # Start agent coordinator
            self.agent_coordinator.start()
            logger.info(f"✅ Agent coordinator initialized (Agent ID: {self.registered_agent_id})")
            
            # Initialize analytics engine (Phase 7)
            logger.info("Initializing analytics engine...")
            analytics_db = str(PROJECT_DIR / 'local_data' / 'analytics.db')
            self.analytics_engine = AnalyticsEngine()
            self.analytics_engine.metrics_collector.db_path = analytics_db
            self.analytics_engine.storage_manager.db_path = analytics_db
            logger.info("✅ Analytics engine initialized")
            
            # Test Firebase connection
            logger.info("Testing Firebase connection...")
            test_doc = self.firestore.collection('configuration').document('status').get()
            logger.info("✅ Firebase connection verified")
            
            return True
        
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            return False
    
    def _init_database(self):
        """Initialize SQLite database."""
        db_dir = PROJECT_DIR / 'local_data'
        db_dir.mkdir(exist_ok=True)
        
        db_path = db_dir / 'buddy_local.db'
        self.db = sqlite3.connect(str(db_path), check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        
        # Enable WAL mode
        self.db.execute('PRAGMA journal_mode=WAL')
        
        # Create tables if they don't exist
        cursor = self.db.cursor()
        
        # Schema version table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                description TEXT
            )
        ''')
        
        # Tasks queue table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks_queue (
                task_id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                params TEXT NOT NULL,
                priority TEXT DEFAULT 'NORMAL',
                status TEXT DEFAULT 'pending',
                retries INTEGER DEFAULT 0,
                max_retries INTEGER DEFAULT 3,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                error TEXT,
                assigned_browser INTEGER
            )
        ''')
        
        # Results buffer table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS results_buffer (
                result_id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                success BOOLEAN NOT NULL,
                data TEXT,
                error TEXT,
                execution_time_ms INTEGER,
                screenshot_path TEXT,
                log_path TEXT,
                synced BOOLEAN DEFAULT 0,
                sync_attempts INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                synced_at TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES tasks_queue(task_id)
            )
        ''')
        
        # Agent metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agent_metrics (
                metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tasks_completed INTEGER DEFAULT 0,
                tasks_failed INTEGER DEFAULT 0,
                average_execution_time_ms INTEGER,
                browsers_active INTEGER,
                ram_used_gb REAL,
                ram_percent REAL,
                cpu_percent REAL
            )
        ''')
        
        # Check schema version
        cursor.execute('SELECT COUNT(*) as count FROM schema_version')
        if cursor.fetchone()['count'] == 0:
            cursor.execute('''
                INSERT INTO schema_version (version, description)
                VALUES (1, 'Initial schema - Phase 1')
            ''')
            logger.info("Schema version 1 created")
        
        self.db.commit()
    
    def start(self):
        """Start the agent daemon."""
        if self.running:
            logger.warning("Agent already running")
            return
        
        logger.info("=" * 70)
        logger.info("🚀 STARTING BUDDY LOCAL AGENT")
        logger.info("=" * 70)
        
        # Initialize
        if not self.initialize():
            logger.error("Failed to initialize. Exiting.")
            return
        
        self.running = True
        self.start_time = datetime.now()
        
        logger.info(f"Agent ID: {self.agent_id}")
        logger.info(f"Start time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Version: 1.0.0")
        logger.info("Status: READY")
        logger.info("")
        
        # Start browser pool (Phase 3)
        if self.browser_pool:
            self.browser_pool.start()
        
        # Start task queue processor (Phase 4)
        if self.task_queue:
            self.task_queue.start()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Main polling loop
        try:
            self._main_loop()
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
        finally:
            self.stop()
    
    def _main_loop(self):
        """Main polling loop."""
        poll_interval = int(os.getenv('AGENT_POLL_INTERVAL', '5'))
        heartbeat_interval = int(os.getenv('AGENT_HEARTBEAT_INTERVAL', '30'))
        
        next_heartbeat = datetime.now()
        
        logger.info(f"Starting main loop...")
        logger.info(f"  Poll interval: {poll_interval}s")
        logger.info(f"  Heartbeat interval: {heartbeat_interval}s")
        logger.info("")
        
        while self.running:
            try:
                # Phase 2: Update resource metrics
                resource_status = self.resource_monitor.update_metrics(self.db)
                
                # Phase 3: Update browser pool
                if self.browser_pool:
                    self.browser_pool.update()
                
                # Phase 4: Update task queue processor
                if self.task_queue:
                    self.task_queue.update()
                
                # Phase 5: Check for scheduled tasks to queue
                if self.task_scheduler:
                    due_tasks = self.task_scheduler.get_due_tasks()
                    for task in due_tasks:
                        # Queue the scheduled task
                        try:
                            conn = sqlite3.connect(str(PROJECT_DIR / 'local_data' / 'buddy_local.db'))
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
                        except Exception as e:
                            logger.debug(f"Could not queue scheduled task: {e}")
                
                # Check if we need to throttle or pause
                if self.resource_monitor.should_pause_tasks():
                    logger.warning(f"🔴 Tasks paused - RAM at {resource_status['ram_percent']:.1f}%")
                    time.sleep(10)  # Wait longer when paused
                    continue
                
                if self.resource_monitor.should_throttle():
                    logger.info(f"🟡 Throttling - RAM at {resource_status['ram_percent']:.1f}%")
                    time.sleep(poll_interval * 2)  # Sleep longer when throttling
                    continue
                
                # Update heartbeat if needed
                if datetime.now() >= next_heartbeat:
                    self._update_heartbeat()
                    next_heartbeat = datetime.now() + timedelta(seconds=heartbeat_interval)
                
                # Poll for tasks (will implement in Phase 2)
                self._poll_tasks()
                
                # Sleep before next poll
                time.sleep(poll_interval)
            
            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                time.sleep(5)  # Wait before retry
    
    def _update_heartbeat(self):
        """Update agent heartbeat in Firebase."""
        try:
            uptime = datetime.now() - self.start_time
            uptime_seconds = int(uptime.total_seconds())
            
            heartbeat_data = {
                'agent_id': self.agent_id,
                'agent_type': 'local',
                'status': 'ONLINE',
                'last_heartbeat': firestore.SERVER_TIMESTAMP,
                'uptime_seconds': uptime_seconds,
                'tasks_processed': self.tasks_processed,
                'tasks_failed': self.tasks_failed,
                'success_rate': self._calculate_success_rate(),
                'version': '1.0.0',
                'hostname': os.getenv('COMPUTERNAME', 'unknown'),
                'updated_at': firestore.SERVER_TIMESTAMP,
                'created_at': firestore.SERVER_TIMESTAMP
            }
            
            # Write to Firebase
            self.firestore.collection('agents').document(self.agent_id).collection('heartbeat').document('current').set(
                heartbeat_data,
                merge=True
            )
            
            logger.debug(f"✅ Heartbeat updated (uptime: {uptime_seconds}s, processed: {self.tasks_processed})")
        
        except Exception as e:
            logger.warning(f"Failed to update heartbeat: {e}")
    
    def _poll_tasks(self):
        """Poll for tasks from Firebase."""
        try:
            # Query pending tasks (Phase 2 implementation)
            # For now, just a placeholder
            pass
        
        except Exception as e:
            logger.error(f"Error polling tasks: {e}")
    
    def _calculate_success_rate(self) -> float:
        """Calculate task success rate."""
        total = self.tasks_processed + self.tasks_failed
        if total == 0:
            return 100.0
        return (self.tasks_processed / total) * 100
    
    def record_task_execution(self, task_id: str, tool_name: str, duration_seconds: float,
                             success: bool, cost_actual: float = 0.0, tokens_used: int = 0,
                             human_effort_level: str = "MEDIUM", browser_used: bool = False):
        """Record a task execution to the analytics engine (Phase 7)."""
        try:
            if self.analytics_engine:
                self.analytics_engine.record_execution(
                    task_id=task_id,
                    agent_id=self.agent_id,
                    tool_name=tool_name,
                    duration_seconds=duration_seconds,
                    success=success,
                    cost_actual=cost_actual,
                    tokens_used=tokens_used,
                    human_effort_level=human_effort_level,
                    browser_used=browser_used
                )
                logger.debug(f"Recorded execution: {tool_name} (task: {task_id}, success: {success})")
        except Exception as e:
            logger.warning(f"Failed to record task execution to analytics: {e}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"\n\n📍 Signal received ({signum}). Initiating graceful shutdown...")
        self.running = False
    
    def stop(self):
        """Stop the agent daemon."""
        if not self.running and self.start_time is None:
            return
        
        logger.info("")
        logger.info("=" * 70)
        logger.info("🛑 STOPPING BUDDY LOCAL AGENT")
        logger.info("=" * 70)
        
        # Get final resource status (Phase 2)
        final_status = self.resource_monitor.get_system_status()
        logger.info(f"Final resource status:")
        logger.info(f"  RAM: {final_status['ram_used_gb']:.1f}GB / {final_status['ram_total_gb']:.1f}GB ({final_status['ram_percent']:.1f}%)")
        logger.info(f"  CPU: {final_status['cpu_percent']:.1f}% ({final_status['cpu_count']} cores)")
        logger.info(f"  Mode: {final_status['mode']}")
        
        # Stop browser pool (Phase 3)
        if self.browser_pool:
            try:
                self.browser_pool.stop()
                logger.info("✅ Browser pool stopped")
            except Exception as e:
                logger.error(f"Error stopping browser pool: {e}")
        
        # Stop task queue processor (Phase 4)
        if self.task_queue:
            try:
                self.task_queue.stop()
                logger.info("✅ Task queue processor stopped")
            except Exception as e:
                logger.error(f"Error stopping task queue processor: {e}")
        
        # Stop agent coordinator (Phase 6)
        if self.agent_coordinator:
            try:
                self.agent_coordinator.stop()
                logger.info("✅ Agent coordinator stopped")
            except Exception as e:
                logger.error(f"Error stopping agent coordinator: {e}")
        
        # Cleanup
        if self.db:
            try:
                self.db.close()
                logger.info("✅ Database closed")
            except Exception as e:
                logger.error(f"Error closing database: {e}")
        
        # Calculate uptime
        if self.start_time:
            uptime = datetime.now() - self.start_time
            logger.info(f"Uptime: {uptime}")
        
        # Summary
        logger.info(f"Tasks processed: {self.tasks_processed}")
        logger.info(f"Tasks failed: {self.tasks_failed}")
        logger.info(f"Success rate: {self._calculate_success_rate():.1f}%")
        logger.info(f"Status: OFFLINE")
        logger.info("=" * 70)
        logger.info("")
        
        self.running = False
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status."""
        uptime = None
        if self.start_time:
            uptime = datetime.now() - self.start_time
        
        # Get resource status (Phase 2)
        resource_status = self.resource_monitor.get_system_status()
        
        # Get browser pool status (Phase 3)
        browser_status = {'total': 0, 'healthy': 0}
        if self.browser_pool and self.browser_pool.running:
            browser_counts = self.browser_pool.get_browser_count()
            browser_status = {
                'total': browser_counts['total'],
                'healthy': browser_counts['healthy']
            }
        
        # Get task queue status (Phase 4)
        queue_status = {'active_tasks': 0, 'tasks_processed': 0}
        if self.task_queue:
            queue_status = self.task_queue.get_status()
        
        # Get scheduler status (Phase 5)
        scheduler_status = {'scheduled_tasks': 0}
        if self.task_scheduler:
            scheduler_status = self.task_scheduler.get_status()
        
        # Get workflow status (Phase 5)
        workflow_status = {'workflows': 0, 'instances': 0}
        if self.workflow_orchestrator:
            workflow_status = self.workflow_orchestrator.get_status()
        
        return {
            'agent_id': self.agent_id,
            'status': 'ONLINE' if self.running else 'OFFLINE',
            'uptime': str(uptime) if uptime else None,
            'tasks_processed': self.tasks_processed,
            'tasks_failed': self.tasks_failed,
            'success_rate': self._calculate_success_rate(),
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'current_time': datetime.now().isoformat(),
            # Phase 2 resource info
            'resource_mode': resource_status['mode'],
            'ram_percent': resource_status['ram_percent'],
            'cpu_percent': resource_status['cpu_percent'],
            'ram_used_gb': resource_status['ram_used_gb'],
            'browser_count_safe': resource_status['browser_count_safe'],
            'health': 'healthy' if resource_status['healthy'] else 'warning',
            # Phase 3 browser pool info
            'browsers_active': browser_status['total'],
            'browsers_healthy': browser_status['healthy'],
            # Phase 4 task queue info
            'active_tasks': queue_status.get('active_tasks', 0),
            'queue_tasks_processed': queue_status.get('tasks_processed', 0),
            # Phase 5 scheduling info
            'scheduled_tasks': scheduler_status.get('scheduled_tasks', 0),
            'workflows_registered': workflow_status.get('registered_workflows', 0),
            'workflow_instances': workflow_status.get('running_instances', 0),
            # Phase 6 multi-agent coordination info
            'registered_agent_id': self.registered_agent_id,
            'coordinator_active': self.agent_coordinator is not None,
        }


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Buddy Local Agent')
    parser.add_argument('--start', action='store_true', help='Start the agent')
    parser.add_argument('--stop', action='store_true', help='Stop the agent')
    parser.add_argument('--status', action='store_true', help='Show agent status')
    parser.add_argument('--debug', action='store_true', help='Debug mode')
    
    args = parser.parse_args()
    
    agent = BuddyLocalAgent()
    
    if args.start:
        agent.start()
    
    elif args.status:
        status = agent.get_status()
        print("\n" + "=" * 70)
        print("📊 BUDDY LOCAL AGENT STATUS")
        print("=" * 70)
        for key, value in status.items():
            print(f"{key:20} : {value}")
        print("=" * 70 + "\n")
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
