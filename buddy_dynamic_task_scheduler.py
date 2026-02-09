"""
BUDDY DYNAMIC TASK SCHEDULER - PHASE 6
======================================

Purpose: Dynamic, prioritized task queue with workflow orchestration
Phase: 6 - Dynamic Task Scheduling & Conditional Workflows
Status: ACTIVE

Architecture:
- Priority queue with dependency resolution
- Risk-based task evaluation
- Conditional branching support
- Retry and defer logic
- Thread-safe concurrent execution
- Integration with Phase 5 Web Tools
- Zero modifications to Phase 1-4 code

Author: Buddy Phase 6 Architecture Team
Date: February 5, 2026
"""

import json
import threading
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any, Set
from queue import PriorityQueue
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    DEFERRED = "deferred"
    SKIPPED = "skipped"


class TaskPriority(Enum):
    """Task priority levels"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    BACKGROUND = 5


class RiskLevel(Enum):
    """Task risk classification (aligned with Phase 5)"""
    LOW = "low"          # Read-only operations
    MEDIUM = "medium"    # Reversible actions
    HIGH = "high"        # Permanent actions


@dataclass
class TaskDependency:
    """Dependency specification for a task"""
    task_id: str
    required_status: TaskStatus = TaskStatus.COMPLETED
    timeout_seconds: Optional[int] = None


@dataclass
class ConditionalBranch:
    """Conditional branching based on task outcome"""
    condition_type: str  # "success", "failure", "result_equals", "result_contains"
    condition_value: Optional[Any] = None
    next_task_id: Optional[str] = None
    next_task_template: Optional[Dict[str, Any]] = None


@dataclass
class Task:
    """
    Dynamic task with dependencies, priority, and conditional execution
    
    Fields:
    - id: Unique task identifier
    - description: Human-readable task description
    - action: Callable function to execute
    - action_params: Parameters to pass to action
    - priority: Task priority (CRITICAL to BACKGROUND)
    - risk_level: Risk classification (LOW, MEDIUM, HIGH)
    - confidence_score: Predicted success probability (0.0-1.0)
    - dependencies: List of task IDs that must complete first
    - conditional_branches: Outcome-based next tasks
    - status: Current execution status
    - max_attempts: Maximum retry attempts
    - attempt_count: Current attempt number
    - created_at: Task creation timestamp
    - started_at: Execution start timestamp
    - completed_at: Execution completion timestamp
    - result: Task execution result
    - error: Error details if failed
    - metadata: Additional task metadata
    """
    id: str
    description: str
    action: Optional[Callable] = None
    action_params: Dict[str, Any] = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.MEDIUM
    risk_level: RiskLevel = RiskLevel.LOW
    confidence_score: float = 0.5
    dependencies: List[TaskDependency] = field(default_factory=list)
    conditional_branches: List[ConditionalBranch] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    max_attempts: int = 3
    attempt_count: int = 0
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __lt__(self, other):
        """Priority queue comparison (lower priority value = higher priority)"""
        return self.priority.value < other.priority.value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict"""
        data = asdict(self)
        # Remove non-serializable action callable
        data['action'] = str(data['action']) if data['action'] else None
        data['priority'] = self.priority.name
        data['risk_level'] = self.risk_level.name
        data['status'] = self.status.name
        data['dependencies'] = [
            {
                'task_id': dep.task_id,
                'required_status': dep.required_status.name,
                'timeout_seconds': dep.timeout_seconds
            }
            for dep in self.dependencies
        ]
        return data


class TaskScheduler:
    """
    Dynamic task scheduler with priority queue, dependency resolution,
    and conditional workflow execution.
    
    Features:
    - Thread-safe task queue management
    - Priority-based task selection
    - Dependency resolution and blocking
    - Risk-aware execution (respects dry-run mode)
    - Retry logic with exponential backoff
    - Conditional branching based on outcomes
    - Metrics capture and persistence
    - Queue state recovery from disk
    """
    
    def __init__(
        self,
        max_concurrent_tasks: int = 1,
        enable_dry_run: bool = False,
        metrics_dir: str = "outputs/task_scheduler_metrics",
        queue_state_file: str = "outputs/task_scheduler_metrics/queue_state.json"
    ):
        """
        Initialize task scheduler
        
        Args:
            max_concurrent_tasks: Maximum parallel task execution
            enable_dry_run: Enable dry-run mode for high-risk tasks
            metrics_dir: Directory for metrics and logs
            queue_state_file: File path for queue state persistence
        """
        self.max_concurrent_tasks = max_concurrent_tasks
        self.enable_dry_run = enable_dry_run
        self.metrics_dir = Path(metrics_dir)
        self.queue_state_file = Path(queue_state_file)
        
        # Create metrics directory
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        
        # Task storage
        self.tasks: Dict[str, Task] = {}
        self.task_queue: PriorityQueue = PriorityQueue()
        self.active_tasks: Set[str] = set()
        
        # Thread safety
        self.lock = threading.RLock()
        self.condition = threading.Condition(self.lock)
        
        # Execution control
        self.running = False
        self.executor_thread: Optional[threading.Thread] = None
        
        # Metrics
        self.total_tasks_executed = 0
        self.total_tasks_succeeded = 0
        self.total_tasks_failed = 0
        self.total_tasks_deferred = 0
        
        # Action registry (populated externally)
        self.action_registry: Dict[str, Callable] = {}
        
        logger.info(f"TaskScheduler initialized: dry_run={enable_dry_run}, "
                   f"max_concurrent={max_concurrent_tasks}")
    
    def register_action(self, name: str, action: Callable):
        """Register an action callable"""
        with self.lock:
            self.action_registry[name] = action
            logger.info(f"Registered action: {name}")
    
    def add_task(
        self,
        description: str,
        action: Optional[Callable] = None,
        action_name: Optional[str] = None,
        action_params: Optional[Dict[str, Any]] = None,
        priority: TaskPriority = TaskPriority.MEDIUM,
        risk_level: RiskLevel = RiskLevel.LOW,
        confidence_score: float = 0.5,
        dependencies: Optional[List[str]] = None,
        conditional_branches: Optional[List[ConditionalBranch]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        task_id: Optional[str] = None
    ) -> str:
        """
        Add a task to the scheduler
        
        Args:
            description: Task description
            action: Callable to execute (or use action_name)
            action_name: Name of registered action
            action_params: Parameters for action
            priority: Task priority
            risk_level: Risk classification
            confidence_score: Predicted success probability
            dependencies: List of task IDs to wait for
            conditional_branches: Outcome-based branching
            metadata: Additional metadata
            task_id: Custom task ID (generated if not provided)
        
        Returns:
            Task ID
        """
        with self.lock:
            # Generate task ID
            if task_id is None:
                task_id = f"task_{uuid.uuid4().hex[:8]}"
            
            # Resolve action
            if action is None and action_name:
                action = self.action_registry.get(action_name)
                if action is None:
                    raise ValueError(f"Action not registered: {action_name}")
            
            # Create task dependencies
            task_dependencies = []
            if dependencies:
                for dep_id in dependencies:
                    task_dependencies.append(
                        TaskDependency(task_id=dep_id)
                    )
            
            # Create task
            task = Task(
                id=task_id,
                description=description,
                action=action,
                action_params=action_params or {},
                priority=priority,
                risk_level=risk_level,
                confidence_score=confidence_score,
                dependencies=task_dependencies,
                conditional_branches=conditional_branches or [],
                metadata=metadata or {}
            )
            
            # Store task
            self.tasks[task_id] = task
            
            # Add to queue
            self.task_queue.put((task.priority.value, time.time(), task_id))
            
            logger.info(f"Added task: {task_id} - {description} "
                       f"(priority={priority.name}, risk={risk_level.name})")
            
            # Notify executor
            self.condition.notify()
            
            return task_id
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID"""
        with self.lock:
            return self.tasks.get(task_id)
    
    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Get task status"""
        task = self.get_task(task_id)
        return task.status if task else None
    
    def _check_dependencies(self, task: Task) -> bool:
        """
        Check if task dependencies are satisfied
        
        Returns:
            True if all dependencies met, False otherwise
        """
        for dep in task.dependencies:
            dep_task = self.tasks.get(dep.task_id)
            if not dep_task:
                logger.warning(f"Dependency not found: {dep.task_id} for task {task.id}")
                return False
            
            if dep_task.status != dep.required_status:
                logger.debug(f"Dependency not met: {dep.task_id} "
                           f"(status={dep_task.status.name}, "
                           f"required={dep.required_status.name})")
                return False
        
        return True
    
    def _should_execute_task(self, task: Task) -> bool:
        """
        Evaluate if task should be executed now
        
        Considers:
        - Dependencies
        - Risk tolerance
        - Confidence score
        - Max attempts
        """
        # Check dependencies
        if not self._check_dependencies(task):
            return False
        
        # Check max attempts
        if task.attempt_count >= task.max_attempts:
            logger.warning(f"Task {task.id} exceeded max attempts ({task.max_attempts})")
            task.status = TaskStatus.FAILED
            task.error = f"Exceeded max attempts ({task.max_attempts})"
            self._log_task_metrics(task)
            return False
        
        # Check confidence for high-risk tasks
        if task.risk_level == RiskLevel.HIGH and task.confidence_score < 0.7:
            logger.warning(f"Task {task.id} deferred: high-risk with low confidence "
                         f"({task.confidence_score:.2f})")
            task.status = TaskStatus.DEFERRED
            self.total_tasks_deferred += 1
            self._log_task_metrics(task)
            return False
        
        return True
    
    def _execute_task(self, task: Task) -> bool:
        """
        Execute a single task
        
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Executing task {task.id}: {task.description}")
        
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.utcnow().isoformat()
        task.attempt_count += 1
        start_time = time.time()
        
        try:
            # Check dry-run mode for high-risk tasks
            if self.enable_dry_run and task.risk_level == RiskLevel.HIGH:
                logger.info(f"DRY-RUN: Task {task.id} (risk={task.risk_level.name})")
                task.result = {
                    'dry_run': True,
                    'message': f"Dry-run mode: {task.description} not executed"
                }
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.utcnow().isoformat()
                execution_time_ms = (time.time() - start_time) * 1000
                task.metadata['execution_time_ms'] = execution_time_ms
                self.total_tasks_succeeded += 1
                self._log_task_metrics(task, actual_success=True)
                return True
            
            # Execute action
            if task.action:
                result = task.action(**task.action_params)
                execution_time_ms = (time.time() - start_time) * 1000
                
                task.result = result
                task.metadata['execution_time_ms'] = execution_time_ms
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.utcnow().isoformat()
                
                logger.info(f"Task {task.id} completed in {execution_time_ms:.2f}ms")
                self.total_tasks_succeeded += 1
                self._log_task_metrics(task, actual_success=True)
                
                # Process conditional branches
                self._process_conditional_branches(task)
                
                return True
            else:
                # No action - mark as skipped
                task.status = TaskStatus.SKIPPED
                task.completed_at = datetime.utcnow().isoformat()
                task.result = {'message': 'No action defined'}
                execution_time_ms = (time.time() - start_time) * 1000
                task.metadata['execution_time_ms'] = execution_time_ms
                logger.warning(f"Task {task.id} skipped: no action defined")
                self._log_task_metrics(task, actual_success=False)
                return False
        
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            logger.error(f"Task {task.id} failed: {error_msg}", exc_info=True)
            
            execution_time_ms = (time.time() - start_time) * 1000
            task.error = error_msg
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.utcnow().isoformat()
            task.metadata['execution_time_ms'] = execution_time_ms
            
            self.total_tasks_failed += 1
            self._log_task_metrics(task, actual_success=False)
            
            # Retry logic
            if task.attempt_count < task.max_attempts:
                logger.info(f"Retrying task {task.id} (attempt {task.attempt_count + 1}/{task.max_attempts})")
                # Re-queue with exponential backoff
                backoff_seconds = 2 ** task.attempt_count
                time.sleep(backoff_seconds)
                task.status = TaskStatus.PENDING
                self.task_queue.put((task.priority.value, time.time(), task.id))
                return False
            
            return False
    
    def _process_conditional_branches(self, task: Task):
        """Process conditional branches based on task outcome"""
        if not task.conditional_branches:
            return
        
        for branch in task.conditional_branches:
            should_branch = False
            
            if branch.condition_type == "success":
                should_branch = (task.status == TaskStatus.COMPLETED)
            elif branch.condition_type == "failure":
                should_branch = (task.status == TaskStatus.FAILED)
            elif branch.condition_type == "result_equals":
                should_branch = (task.result == branch.condition_value)
            elif branch.condition_type == "result_contains":
                should_branch = (
                    isinstance(task.result, dict) and
                    branch.condition_value in task.result
                )
            
            if should_branch:
                logger.info(f"Conditional branch triggered: {branch.condition_type} "
                          f"for task {task.id}")
                
                # Add next task
                if branch.next_task_id:
                    # Reference existing task
                    next_task = self.tasks.get(branch.next_task_id)
                    if next_task:
                        self.task_queue.put((next_task.priority.value, time.time(), branch.next_task_id))
                        logger.info(f"Queued conditional task: {branch.next_task_id}")
                
                elif branch.next_task_template:
                    # Create new task from template
                    template = branch.next_task_template
                    self.add_task(
                        description=template.get('description', 'Conditional task'),
                        action_name=template.get('action_name'),
                        action_params=template.get('action_params', {}),
                        priority=TaskPriority[template.get('priority', 'MEDIUM')],
                        risk_level=RiskLevel[template.get('risk_level', 'LOW')],
                        confidence_score=template.get('confidence_score', 0.5),
                        dependencies=template.get('dependencies', [])
                    )
    
    def _log_task_metrics(self, task: Task, actual_success: bool = None):
        """
        Log task metrics to JSONL file with confidence calibration support
        
        Args:
            task: Task to log
            actual_success: Actual execution result (for calibration)
        """
        log_file = self.metrics_dir / f"buddy_task_queue_logs_{datetime.utcnow().strftime('%Y%m%d')}.jsonl"
        
        # Determine actual success (for calibration)
        if actual_success is None:
            actual_success = task.status == TaskStatus.COMPLETED
        
        try:
            with open(log_file, 'a') as f:
                log_entry = {
                    'timestamp': datetime.utcnow().isoformat(),
                    'task_id': task.id,
                    'description': task.description,
                    'status': task.status.name,
                    'priority': task.priority.name,
                    'risk_level': task.risk_level.name,
                    'confidence_score': task.confidence_score,
                    'attempt_count': task.attempt_count,
                    'execution_time_ms': task.metadata.get('execution_time_ms'),
                    'error': task.error,
                    'created_at': task.created_at,
                    'started_at': task.started_at,
                    'completed_at': task.completed_at,
                    # Confidence calibration fields
                    'actual_success': actual_success,
                    'predicted_success': 1.0 if task.confidence_score >= 0.7 else 0.0,
                    'calibration_bucket': self._get_confidence_bucket(task.confidence_score)
                }
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            logger.error(f"Failed to log task metrics: {e}")
    
    @staticmethod
    def _get_confidence_bucket(confidence_score: float) -> str:
        """Get calibration bucket for confidence score"""
        if confidence_score < 0.1:
            return "0.0-0.1"
        elif confidence_score < 0.2:
            return "0.1-0.2"
        elif confidence_score < 0.3:
            return "0.2-0.3"
        elif confidence_score < 0.4:
            return "0.3-0.4"
        elif confidence_score < 0.5:
            return "0.4-0.5"
        elif confidence_score < 0.6:
            return "0.5-0.6"
        elif confidence_score < 0.7:
            return "0.6-0.7"
        elif confidence_score < 0.8:
            return "0.7-0.8"
        elif confidence_score < 0.9:
            return "0.8-0.9"
        else:
            return "0.9-1.0"
    
    def _executor_loop(self):
        """Main executor loop - runs in separate thread"""
        logger.info("Task executor started")
        
        while self.running:
            task_to_execute = None
            
            with self.condition:
                # Wait until we have tasks and can execute
                while self.running:
                    # Check if we can accept a task
                    if len(self.active_tasks) >= self.max_concurrent_tasks:
                        # Wait for task completion
                        self.condition.wait(timeout=0.5)
                        continue
                    
                    # Try to find next executable task (highest priority)
                    found_task = False
                    best_task = None
                    best_priority = TaskPriority.BACKGROUND  # Lowest priority (highest value)
                    
                    # Find pending task with highest priority (lowest priority value)
                    for task_id, task in self.tasks.items():
                        if task.status == TaskStatus.PENDING and task_id not in self.active_tasks:
                            if self._check_dependencies(task):
                                # Task is ready to execute
                                # Compare priorities (lower value = higher priority)
                                if task.priority.value < best_priority.value:
                                    best_task = task
                                    best_priority = task.priority
                                    found_task = True
                    
                    if found_task and best_task:
                        task_to_execute = best_task
                        break
                    
                    # No executable tasks - wait for notification
                    self.condition.wait(timeout=1.0)
                
                if not self.running:
                    break
                
                if task_to_execute:
                    self.active_tasks.add(task_to_execute.id)
            
            # Execute task (outside lock for parallelism)
            if task_to_execute:
                try:
                    self._execute_task(task_to_execute)
                finally:
                    with self.lock:
                        self.active_tasks.discard(task_to_execute.id)
                        self.total_tasks_executed += 1
                        self.condition.notify_all()
        
        logger.info("Task executor stopped")
    
    def start(self):
        """Start the task scheduler"""
        with self.lock:
            if self.running:
                logger.warning("Scheduler already running")
                return
            
            self.running = True
            self.executor_thread = threading.Thread(target=self._executor_loop, daemon=True)
            self.executor_thread.start()
            logger.info("Task scheduler started")
    
    def stop(self, wait_for_completion: bool = True):
        """Stop the task scheduler"""
        with self.lock:
            if not self.running:
                logger.warning("Scheduler not running")
                return
            
            logger.info("Stopping task scheduler...")
            self.running = False
            self.condition.notify_all()
        
        if wait_for_completion and self.executor_thread:
            self.executor_thread.join(timeout=10.0)
        
        logger.info("Task scheduler stopped")
    
    def wait_for_completion(self, timeout: Optional[float] = None) -> bool:
        """
        Wait for all tasks to complete
        
        Returns:
            True if all completed, False if timeout
        """
        start_time = time.time()
        last_completion_time = time.time()
        stable_threshold = 0.5  # If no new tasks added for 0.5s, we're done
        
        while True:
            with self.lock:
                # Count task statuses
                completed_count = sum(
                    1 for t in self.tasks.values() 
                    if t.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.SKIPPED]
                )
                total_tasks = len(self.tasks)
                
                # Check if all tasks have terminal status
                if completed_count == total_tasks and total_tasks > 0:
                    # Wait a bit more to see if new tasks are added by conditional branches
                    # If nothing added for stable_threshold seconds, consider truly done
                    if (time.time() - last_completion_time) > stable_threshold:
                        logger.info(f"All tasks completed: {completed_count}/{total_tasks}")
                        return True
                else:
                    # Tasks still pending/in progress - reset stable time
                    last_completion_time = time.time()
                
                # Check timeout
                if timeout and (time.time() - start_time) > timeout:
                    completed_count = sum(
                        1 for t in self.tasks.values() 
                        if t.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.SKIPPED]
                    )
                    logger.warning(f"Wait for completion timed out after {timeout}s ({completed_count}/{total_tasks} completed)")
                    return False
            
            time.sleep(0.1)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get scheduler metrics"""
        with self.lock:
            return {
                'total_tasks': len(self.tasks),
                'total_executed': self.total_tasks_executed,
                'total_succeeded': self.total_tasks_succeeded,
                'total_failed': self.total_tasks_failed,
                'total_deferred': self.total_tasks_deferred,
                'success_rate': (
                    self.total_tasks_succeeded / self.total_tasks_executed
                    if self.total_tasks_executed > 0 else 0.0
                ),
                'active_tasks': len(self.active_tasks),
                'pending_tasks': sum(
                    1 for t in self.tasks.values()
                    if t.status == TaskStatus.PENDING
                ),
                'completed_tasks': sum(
                    1 for t in self.tasks.values()
                    if t.status == TaskStatus.COMPLETED
                ),
                'failed_tasks': sum(
                    1 for t in self.tasks.values()
                    if t.status == TaskStatus.FAILED
                )
            }
    
    def save_queue_state(self):
        """Save queue state to disk for recovery"""
        with self.lock:
            state = {
                'timestamp': datetime.utcnow().isoformat(),
                'version': '1.0',
                'metrics': self.get_metrics(),
                'tasks': [task.to_dict() for task in self.tasks.values()]
            }
            
            try:
                with open(self.queue_state_file, 'w') as f:
                    json.dump(state, f, indent=2)
                logger.info(f"Queue state saved to {self.queue_state_file}")
            except Exception as e:
                logger.error(f"Failed to save queue state: {e}")
    
    def load_queue_state(self) -> Dict[str, Any]:
        """
        Load queue state from disk (for recovery)
        
        Returns:
            Loaded state dict or empty dict if not available
        """
        if not self.queue_state_file.exists():
            logger.info("No queue state file found")
            return {}
        
        try:
            with open(self.queue_state_file, 'r') as f:
                state = json.load(f)
            
            logger.info(f"Loaded queue state from {self.queue_state_file}")
            logger.info(f"State timestamp: {state.get('timestamp')}")
            logger.info(f"Tasks in state: {len(state.get('tasks', []))}")
            
            # Restore pending and deferred tasks
            task_count = 0
            for task_data in state.get('tasks', []):
                task_status = task_data.get('status')
                if task_status in ['pending', 'deferred', 'blocked']:
                    # Restore task to pending state (action must be re-registered)
                    task_id = task_data.get('id')
                    task_count += 1
                    logger.info(f"Task {task_id} marked for recovery (was {task_status})")
            
            logger.info(f"Recovery: {task_count} tasks ready for restoration")
            return state
        
        except Exception as e:
            logger.error(f"Failed to load queue state: {e}")
            return {}


def create_scheduler(
    enable_dry_run: bool = False,
    max_concurrent_tasks: int = 1
) -> TaskScheduler:
    """
    Factory function to create a task scheduler
    
    Args:
        enable_dry_run: Enable dry-run mode for high-risk tasks
        max_concurrent_tasks: Maximum parallel task execution
    
    Returns:
        Configured TaskScheduler instance
    """
    return TaskScheduler(
        enable_dry_run=enable_dry_run,
        max_concurrent_tasks=max_concurrent_tasks
    )


if __name__ == "__main__":
    # Example usage
    print("Buddy Dynamic Task Scheduler - Phase 6")
    print("=" * 50)
    
    # Create scheduler
    scheduler = create_scheduler(enable_dry_run=True)
    
    # Register example actions
    def example_action(message: str) -> Dict[str, Any]:
        print(f"Executing: {message}")
        time.sleep(0.5)
        return {'status': 'success', 'message': message}
    
    scheduler.register_action('example_action', example_action)
    
    # Add example tasks
    task1_id = scheduler.add_task(
        description="Task 1: Low priority background task",
        action_name='example_action',
        action_params={'message': 'Background task executed'},
        priority=TaskPriority.BACKGROUND,
        risk_level=RiskLevel.LOW,
        confidence_score=0.9
    )
    
    task2_id = scheduler.add_task(
        description="Task 2: High priority critical task",
        action_name='example_action',
        action_params={'message': 'Critical task executed'},
        priority=TaskPriority.CRITICAL,
        risk_level=RiskLevel.LOW,
        confidence_score=0.95
    )
    
    task3_id = scheduler.add_task(
        description="Task 3: Depends on task 2",
        action_name='example_action',
        action_params={'message': 'Dependent task executed'},
        priority=TaskPriority.HIGH,
        risk_level=RiskLevel.MEDIUM,
        confidence_score=0.8,
        dependencies=[task2_id]
    )
    
    # Start scheduler
    scheduler.start()
    
    # Wait for completion
    print("\nWaiting for tasks to complete...")
    scheduler.wait_for_completion(timeout=10.0)
    
    # Stop scheduler
    scheduler.stop()
    
    # Print metrics
    print("\nScheduler Metrics:")
    metrics = scheduler.get_metrics()
    for key, value in metrics.items():
        print(f"  {key}: {value}")
    
    # Save state
    scheduler.save_queue_state()
    
    print("\nDone!")
