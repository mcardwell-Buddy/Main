"""
Phase 5: Task Scheduling Engine
Handles task scheduling, dependencies, and workflow orchestration.

Architecture:
- TaskScheduler: Main scheduler for recurring and one-time tasks
- TaskDependency: Manages task dependencies and conditions
- WorkflowOrchestrator: Manages multi-task workflows
- Batch processor: Executes groups of tasks with shared config
"""

import sqlite3
import json
import logging
import threading
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Dict, Any, List, Callable
from pathlib import Path
import croniter

from task_queue_processor import Task, TaskStatus, TaskPriority

logger = logging.getLogger(__name__)


class ScheduleType(Enum):
    """Schedule type options"""
    ONE_TIME = "one_time"          # Execute once at specified time
    RECURRING = "recurring"        # Execute on cron schedule
    ON_EVENT = "on_event"          # Execute when event occurs
    ON_DEMAND = "on_demand"        # Execute when requested


class DependencyType(Enum):
    """Dependency relationship types"""
    REQUIRES_SUCCESS = "requires_success"        # Previous task must succeed
    REQUIRES_COMPLETION = "requires_completion"  # Previous task must complete (any status)
    AFTER_TIME = "after_time"                    # Wait until timestamp
    AFTER_DELAY = "after_delay"                  # Wait N seconds after previous task


@dataclass
class TaskDependency:
    """Represents a dependency relationship between tasks"""
    dependent_task_id: str          # Task that depends
    upstream_task_id: Optional[str] = None  # Task it depends on
    dependency_type: DependencyType = DependencyType.REQUIRES_SUCCESS
    check_timestamp: Optional[datetime] = None  # For AFTER_TIME
    delay_seconds: Optional[int] = None  # For AFTER_DELAY
    condition: Optional[Callable] = None  # Custom condition function
    
    def is_satisfied(self, upstream_task: Optional[Task]) -> bool:
        """Check if dependency is satisfied
        
        Args:
            upstream_task: The upstream/previous task
            
        Returns:
            True if dependency is met
        """
        if self.dependency_type == DependencyType.REQUIRES_SUCCESS:
            return upstream_task and upstream_task.status == TaskStatus.COMPLETED
        
        elif self.dependency_type == DependencyType.REQUIRES_COMPLETION:
            return upstream_task and upstream_task.status in [
                TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED
            ]
        
        elif self.dependency_type == DependencyType.AFTER_TIME:
            if not self.check_timestamp:
                return False
            return datetime.now() >= self.check_timestamp
        
        elif self.dependency_type == DependencyType.AFTER_DELAY:
            if not upstream_task or not upstream_task.completed_at:
                return False
            if self.delay_seconds is None:
                return False
            required_time = upstream_task.completed_at + timedelta(seconds=self.delay_seconds)
            return datetime.now() >= required_time
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            'dependent_task_id': self.dependent_task_id,
            'upstream_task_id': self.upstream_task_id,
            'dependency_type': self.dependency_type.value,
            'check_timestamp': self.check_timestamp.isoformat() if self.check_timestamp else None,
            'delay_seconds': self.delay_seconds,
        }


@dataclass
class ScheduledTask:
    """Represents a scheduled task with recurrence"""
    task_template: Task
    schedule_type: ScheduleType
    cron_expression: Optional[str] = None  # For RECURRING
    next_execution: datetime = None
    last_execution: Optional[datetime] = None
    last_result: Optional[Dict[str, Any]] = None
    enabled: bool = True
    max_executions: Optional[int] = None
    execution_count: int = 0
    
    def __post_init__(self):
        if self.next_execution is None:
            self.next_execution = datetime.now()
    
    def should_execute(self) -> bool:
        """Check if task should execute now
        
        Returns:
            True if execution time has arrived
        """
        if not self.enabled:
            return False
        
        if self.max_executions and self.execution_count >= self.max_executions:
            return False
        
        if self.schedule_type == ScheduleType.ONE_TIME:
            return datetime.now() >= self.next_execution
        
        elif self.schedule_type == ScheduleType.RECURRING:
            return datetime.now() >= self.next_execution
        
        return False
    
    def calculate_next_execution(self):
        """Calculate when this task should next execute"""
        if self.schedule_type == ScheduleType.ONE_TIME:
            # One-time tasks don't reschedule
            self.enabled = False
        
        elif self.schedule_type == ScheduleType.RECURRING and self.cron_expression:
            try:
                cron = croniter(self.cron_expression, self.last_execution or datetime.now())
                self.next_execution = cron.get_next(datetime)
            except Exception as e:
                logger.error(f"Error calculating next execution: {e}")
                self.enabled = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            'task_template': self.task_template.to_dict(),
            'schedule_type': self.schedule_type.value,
            'cron_expression': self.cron_expression,
            'next_execution': self.next_execution.isoformat(),
            'last_execution': self.last_execution.isoformat() if self.last_execution else None,
            'enabled': self.enabled,
            'max_executions': self.max_executions,
            'execution_count': self.execution_count,
        }


@dataclass
class WorkflowDefinition:
    """Defines a workflow: ordered sequence of tasks with dependencies"""
    workflow_id: str
    name: str
    description: str
    tasks: List[Task]
    dependencies: List[TaskDependency]
    parallel_allowed: bool = False  # Can non-dependent tasks run in parallel?
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def get_execution_plan(self) -> List[List[str]]:
        """Get tasks grouped by execution stage
        
        Returns:
            List of task ID lists. Each list is a stage that can execute in parallel.
        """
        if not self.parallel_allowed:
            # Sequential: each task in its own stage
            return [[task.task_id] for task in self.tasks]
        
        # Build dependency graph
        graph: Dict[str, List[str]] = {task.task_id: [] for task in self.tasks}
        
        for dep in self.dependencies:
            if dep.upstream_task_id and dep.dependent_task_id:
                if dep.upstream_task_id in graph:
                    graph[dep.upstream_task_id].append(dep.dependent_task_id)
        
        # Topological sort to find stages
        stages = []
        processed = set()
        
        while len(processed) < len(graph):
            # Find all tasks with no unprocessed dependencies
            current_stage = []
            for task_id, dependents in graph.items():
                if task_id not in processed:
                    # Check if all its upstream tasks are processed
                    has_unprocessed_upstream = False
                    for dep in self.dependencies:
                        if dep.dependent_task_id == task_id and dep.upstream_task_id:
                            if dep.upstream_task_id not in processed:
                                has_unprocessed_upstream = True
                                break
                    
                    if not has_unprocessed_upstream:
                        current_stage.append(task_id)
            
            if not current_stage:
                # Circular dependency detected
                logger.error("Circular dependency detected in workflow")
                return [[task.task_id] for task in self.tasks]
            
            stages.append(current_stage)
            processed.update(current_stage)
        
        return stages
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            'workflow_id': self.workflow_id,
            'name': self.name,
            'description': self.description,
            'tasks': [task.to_dict() for task in self.tasks],
            'dependencies': [dep.to_dict() for dep in self.dependencies],
            'parallel_allowed': self.parallel_allowed,
            'created_at': self.created_at.isoformat(),
        }


class TaskScheduler:
    """Manages task scheduling and recurring execution"""
    
    def __init__(self, db_path: str):
        """Initialize scheduler
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.scheduled_tasks: Dict[str, ScheduledTask] = {}
        self.running = False
        self.lock = threading.Lock()
        
        logger.info("TaskScheduler initialized")
    
    def schedule_task(self, scheduled_task: ScheduledTask) -> str:
        """Add a task to the schedule
        
        Args:
            scheduled_task: ScheduledTask to schedule
            
        Returns:
            Task ID
        """
        with self.lock:
            task_id = scheduled_task.task_template.task_id
            self.scheduled_tasks[task_id] = scheduled_task
            self._persist_schedule(scheduled_task)
            logger.info(f"Task {task_id} scheduled ({scheduled_task.schedule_type.value})")
            return task_id
    
    def get_due_tasks(self) -> List[Task]:
        """Get tasks that are due to execute
        
        Returns:
            List of Task objects ready to be queued
        """
        due_tasks = []
        
        with self.lock:
            for task_id, scheduled in self.scheduled_tasks.items():
                if scheduled.should_execute():
                    # Create a copy of the task for execution
                    exec_task = Task(
                        task_id=f"{task_id}_{int(time.time())}",
                        action=scheduled.task_template.action,
                        url=scheduled.task_template.url,
                        javascript=scheduled.task_template.javascript,
                        parameters=scheduled.task_template.parameters,
                        priority=scheduled.task_template.priority,
                        timeout=scheduled.task_template.timeout,
                        max_retries=scheduled.task_template.max_retries,
                    )
                    due_tasks.append(exec_task)
                    
                    # Update scheduling info
                    scheduled.last_execution = datetime.now()
                    scheduled.execution_count += 1
                    scheduled.calculate_next_execution()
                    
                    logger.info(f"Task {task_id} is due for execution")
        
        return due_tasks
    
    def unschedule_task(self, task_id: str) -> bool:
        """Remove a scheduled task
        
        Args:
            task_id: Task ID to remove
            
        Returns:
            True if removed, False if not found
        """
        with self.lock:
            if task_id in self.scheduled_tasks:
                del self.scheduled_tasks[task_id]
                self._remove_schedule(task_id)
                logger.info(f"Task {task_id} unscheduled")
                return True
        
        return False
    
    def _persist_schedule(self, scheduled_task: ScheduledTask):
        """Save schedule to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO scheduled_tasks
                (task_id, schedule_data, created_at)
                VALUES (?, ?, ?)
            """, (
                scheduled_task.task_template.task_id,
                json.dumps(scheduled_task.to_dict()),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
        
        except Exception as e:
            logger.error(f"Error persisting schedule: {e}")
    
    def _remove_schedule(self, task_id: str):
        """Remove schedule from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM scheduled_tasks WHERE task_id = ?", (task_id,))
            conn.commit()
            conn.close()
        
        except Exception as e:
            logger.error(f"Error removing schedule: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get scheduler status"""
        return {
            'scheduled_tasks': len(self.scheduled_tasks),
            'enabled_tasks': sum(1 for st in self.scheduled_tasks.values() if st.enabled),
            'status': 'running' if self.running else 'stopped'
        }


class WorkflowOrchestrator:
    """Orchestrates multi-task workflows"""
    
    def __init__(self, db_path: str):
        """Initialize orchestrator
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.workflows: Dict[str, WorkflowDefinition] = {}
        self.workflow_instances: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()
        
        logger.info("WorkflowOrchestrator initialized")
    
    def register_workflow(self, workflow: WorkflowDefinition) -> str:
        """Register a workflow definition
        
        Args:
            workflow: WorkflowDefinition to register
            
        Returns:
            Workflow ID
        """
        with self.lock:
            self.workflows[workflow.workflow_id] = workflow
            self._persist_workflow(workflow)
            logger.info(f"Workflow {workflow.workflow_id} registered with {len(workflow.tasks)} tasks")
            return workflow.workflow_id
    
    def start_workflow(self, workflow_id: str) -> Optional[str]:
        """Start executing a workflow
        
        Args:
            workflow_id: ID of workflow to execute
            
        Returns:
            Workflow instance ID, or None if workflow not found
        """
        with self.lock:
            if workflow_id not in self.workflows:
                logger.warning(f"Workflow {workflow_id} not found")
                return None
            
            workflow = self.workflows[workflow_id]
            instance_id = f"{workflow_id}_{int(time.time())}"
            
            # Create workflow instance
            instance = {
                'instance_id': instance_id,
                'workflow_id': workflow_id,
                'status': 'running',
                'started_at': datetime.now(),
                'completed_at': None,
                'task_results': {},
                'failed_tasks': [],
            }
            
            self.workflow_instances[instance_id] = instance
            logger.info(f"Workflow instance {instance_id} started")
            
            return instance_id
    
    def get_workflow_tasks_to_queue(self, instance_id: str) -> List[Task]:
        """Get tasks ready to queue for a workflow instance
        
        Args:
            instance_id: Workflow instance ID
            
        Returns:
            List of Task objects ready to execute
        """
        with self.lock:
            if instance_id not in self.workflow_instances:
                return []
            
            instance = self.workflow_instances[instance_id]
            workflow_id = instance['workflow_id']
            
            if workflow_id not in self.workflows:
                return []
            
            workflow = self.workflows[workflow_id]
            ready_tasks = []
            
            for task in workflow.tasks:
                # Skip if already processed
                if task.task_id in instance['task_results']:
                    continue
                
                # Check dependencies
                all_deps_satisfied = True
                for dep in workflow.dependencies:
                    if dep.dependent_task_id == task.task_id:
                        if dep.upstream_task_id:
                            upstream_result = instance['task_results'].get(dep.upstream_task_id)
                            if not upstream_result:
                                all_deps_satisfied = False
                                break
                
                if all_deps_satisfied:
                    ready_tasks.append(task)
            
            return ready_tasks
    
    def record_workflow_task_result(self, instance_id: str, task_id: str, result: Dict[str, Any]):
        """Record result of a workflow task
        
        Args:
            instance_id: Workflow instance ID
            task_id: Task that completed
            result: Result dictionary
        """
        with self.lock:
            if instance_id not in self.workflow_instances:
                return
            
            instance = self.workflow_instances[instance_id]
            instance['task_results'][task_id] = result
            
            if result.get('status') != 'success':
                instance['failed_tasks'].append(task_id)
                logger.warning(f"Task {task_id} failed in workflow {instance_id}")
    
    def check_workflow_complete(self, instance_id: str) -> bool:
        """Check if workflow has completed
        
        Args:
            instance_id: Workflow instance ID
            
        Returns:
            True if all tasks completed
        """
        with self.lock:
            if instance_id not in self.workflow_instances:
                return False
            
            instance = self.workflow_instances[instance_id]
            workflow_id = instance['workflow_id']
            
            if workflow_id not in self.workflows:
                return False
            
            workflow = self.workflows[workflow_id]
            expected_tasks = len(workflow.tasks)
            completed_tasks = len(instance['task_results'])
            
            if completed_tasks >= expected_tasks:
                instance['status'] = 'completed'
                instance['completed_at'] = datetime.now()
                logger.info(f"Workflow instance {instance_id} completed")
                return True
            
            return False
    
    def _persist_workflow(self, workflow: WorkflowDefinition):
        """Save workflow definition to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO workflows
                (workflow_id, workflow_data, created_at)
                VALUES (?, ?, ?)
            """, (
                workflow.workflow_id,
                json.dumps(workflow.to_dict()),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
        
        except Exception as e:
            logger.error(f"Error persisting workflow: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get orchestrator status"""
        return {
            'registered_workflows': len(self.workflows),
            'running_instances': sum(1 for inst in self.workflow_instances.values() 
                                     if inst['status'] == 'running'),
            'total_instances': len(self.workflow_instances),
        }


class BatchTaskProcessor:
    """Processes groups of tasks with shared configuration"""
    
    @staticmethod
    def create_batch(batch_id: str, base_task: Task, urls: List[str], 
                     priority: TaskPriority = TaskPriority.NORMAL) -> List[Task]:
        """Create batch of tasks from template
        
        Args:
            batch_id: Batch identifier
            base_task: Template task (will be copied for each URL)
            urls: List of URLs to process
            priority: Priority for all tasks
            
        Returns:
            List of Task objects
        """
        batch_tasks = []
        
        for i, url in enumerate(urls):
            task = Task(
                task_id=f"{batch_id}_{i:04d}",
                action=base_task.action,
                url=url,
                javascript=base_task.javascript,
                parameters=base_task.parameters,
                priority=priority,
                timeout=base_task.timeout,
                max_retries=base_task.max_retries,
            )
            batch_tasks.append(task)
        
        logger.info(f"Created batch {batch_id} with {len(batch_tasks)} tasks")
        return batch_tasks
    
    @staticmethod
    def aggregate_results(tasks: List[Task]) -> Dict[str, Any]:
        """Aggregate results from batch of tasks
        
        Args:
            tasks: Completed tasks with results
            
        Returns:
            Aggregated results dictionary
        """
        successful = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in tasks if t.status == TaskStatus.FAILED)
        results = [t.result for t in tasks if t.result]
        errors = [t.error for t in tasks if t.error]
        
        return {
            'total_tasks': len(tasks),
            'successful': successful,
            'failed': failed,
            'success_rate': (successful / len(tasks) * 100) if tasks else 0,
            'results': results,
            'errors': errors,
            'aggregated_at': datetime.now().isoformat(),
        }


def init_phase5_tables(db_path: str):
    """Initialize Phase 5 database tables
    
    Args:
        db_path: Path to SQLite database
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Scheduled tasks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scheduled_tasks (
                task_id TEXT PRIMARY KEY,
                schedule_data TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Workflows table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflows (
                workflow_id TEXT PRIMARY KEY,
                workflow_data TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Workflow instances table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflow_instances (
                instance_id TEXT PRIMARY KEY,
                workflow_id TEXT NOT NULL,
                instance_data TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (workflow_id) REFERENCES workflows(workflow_id)
            )
        """)
        
        conn.commit()
        conn.close()
        
        logger.info("✅ Phase 5 tables initialized")
    
    except Exception as e:
        logger.error(f"❌ Error initializing Phase 5 tables: {e}")
