"""
Phase 5: Task Scheduling and Workflow Tests
Comprehensive test suite for scheduling, dependencies, and workflows.

Test Coverage:
- Task scheduling (one-time, recurring, on-event)
- Task dependencies and conditions
- Workflow definition and orchestration
- Batch task processing
- Integration with Phase 4
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

from task_scheduler import (
    ScheduleType, DependencyType, TaskDependency, ScheduledTask,
    WorkflowDefinition, TaskScheduler, WorkflowOrchestrator,
    BatchTaskProcessor, init_phase5_tables
)
from task_queue_processor import Task, TaskStatus, TaskPriority


class TestTaskDependency(unittest.TestCase):
    """Test task dependency model and logic"""
    
    def test_requires_success_satisfied(self):
        """Test REQUIRES_SUCCESS dependency when succeeded"""
        dep = TaskDependency(
            dependent_task_id="task_b",
            upstream_task_id="task_a",
            dependency_type=DependencyType.REQUIRES_SUCCESS
        )
        
        upstream = Task(task_id="task_a", action="navigate", url="https://example.com")
        upstream.status = TaskStatus.COMPLETED
        
        self.assertTrue(dep.is_satisfied(upstream))
    
    def test_requires_success_not_satisfied(self):
        """Test REQUIRES_SUCCESS dependency when not succeeded"""
        dep = TaskDependency(
            dependent_task_id="task_b",
            upstream_task_id="task_a",
            dependency_type=DependencyType.REQUIRES_SUCCESS
        )
        
        upstream = Task(task_id="task_a", action="navigate", url="https://example.com")
        upstream.status = TaskStatus.FAILED
        
        self.assertFalse(dep.is_satisfied(upstream))
    
    def test_requires_completion_any_status(self):
        """Test REQUIRES_COMPLETION accepts any terminal status"""
        dep = TaskDependency(
            dependent_task_id="task_b",
            upstream_task_id="task_a",
            dependency_type=DependencyType.REQUIRES_COMPLETION
        )
        
        # Test COMPLETED
        upstream = Task(task_id="task_a", action="navigate", url="https://example.com")
        upstream.status = TaskStatus.COMPLETED
        self.assertTrue(dep.is_satisfied(upstream))
        
        # Test FAILED
        upstream.status = TaskStatus.FAILED
        self.assertTrue(dep.is_satisfied(upstream))
        
        # Test CANCELLED
        upstream.status = TaskStatus.CANCELLED
        self.assertTrue(dep.is_satisfied(upstream))
        
        # Test PENDING (should fail)
        upstream.status = TaskStatus.PENDING
        self.assertFalse(dep.is_satisfied(upstream))
    
    def test_after_time_dependency(self):
        """Test AFTER_TIME dependency"""
        future_time = datetime.now() + timedelta(seconds=10)
        
        dep = TaskDependency(
            dependent_task_id="task_b",
            dependency_type=DependencyType.AFTER_TIME,
            check_timestamp=future_time
        )
        
        # Should not be satisfied yet
        self.assertFalse(dep.is_satisfied(None))
    
    def test_after_delay_dependency(self):
        """Test AFTER_DELAY dependency"""
        dep = TaskDependency(
            dependent_task_id="task_b",
            upstream_task_id="task_a",
            dependency_type=DependencyType.AFTER_DELAY,
            delay_seconds=5
        )
        
        upstream = Task(task_id="task_a", action="navigate", url="https://example.com")
        upstream.completed_at = datetime.now() - timedelta(seconds=10)
        
        # Should be satisfied (10 seconds have passed)
        self.assertTrue(dep.is_satisfied(upstream))
    
    def test_dependency_serialization(self):
        """Test dependency serialization to dict"""
        dep = TaskDependency(
            dependent_task_id="task_b",
            upstream_task_id="task_a",
            dependency_type=DependencyType.REQUIRES_SUCCESS
        )
        
        dep_dict = dep.to_dict()
        self.assertEqual(dep_dict['dependent_task_id'], "task_b")
        self.assertEqual(dep_dict['upstream_task_id'], "task_a")
        self.assertEqual(dep_dict['dependency_type'], DependencyType.REQUIRES_SUCCESS.value)


class TestScheduledTask(unittest.TestCase):
    """Test scheduled task model"""
    
    def test_one_time_scheduling(self):
        """Test one-time task scheduling"""
        task = Task(task_id="sched_001", action="navigate", url="https://example.com")
        scheduled = ScheduledTask(
            task_template=task,
            schedule_type=ScheduleType.ONE_TIME,
            next_execution=datetime.now() - timedelta(seconds=1)
        )
        
        self.assertTrue(scheduled.should_execute())
    
    def test_recurring_scheduling(self):
        """Test recurring task scheduling"""
        task = Task(task_id="sched_002", action="navigate", url="https://example.com")
        scheduled = ScheduledTask(
            task_template=task,
            schedule_type=ScheduleType.RECURRING,
            cron_expression="0 * * * *",  # Every hour
            next_execution=datetime.now() - timedelta(seconds=1)
        )
        
        self.assertTrue(scheduled.should_execute())
    
    def test_max_executions_limit(self):
        """Test max executions limit"""
        task = Task(task_id="sched_003", action="navigate", url="https://example.com")
        scheduled = ScheduledTask(
            task_template=task,
            schedule_type=ScheduleType.RECURRING,
            cron_expression="0 * * * *",
            max_executions=5,
            execution_count=5
        )
        
        # Should not execute (reached max)
        self.assertFalse(scheduled.should_execute())
    
    def test_disabled_task(self):
        """Test disabled tasks don't execute"""
        task = Task(task_id="sched_004", action="navigate", url="https://example.com")
        scheduled = ScheduledTask(
            task_template=task,
            schedule_type=ScheduleType.ONE_TIME,
            next_execution=datetime.now() - timedelta(seconds=1),
            enabled=False
        )
        
        self.assertFalse(scheduled.should_execute())
    
    def test_scheduled_task_serialization(self):
        """Test scheduled task serialization"""
        task = Task(task_id="sched_005", action="navigate", url="https://example.com")
        scheduled = ScheduledTask(
            task_template=task,
            schedule_type=ScheduleType.ONE_TIME
        )
        
        scheduled_dict = scheduled.to_dict()
        self.assertEqual(scheduled_dict['schedule_type'], ScheduleType.ONE_TIME.value)
        self.assertIn('task_template', scheduled_dict)


class TestWorkflowDefinition(unittest.TestCase):
    """Test workflow definition and execution planning"""
    
    def test_workflow_creation(self):
        """Test creating a workflow"""
        tasks = [
            Task(task_id="t1", action="navigate", url="https://example.com"),
            Task(task_id="t2", action="execute_js", javascript="return 1;"),
            Task(task_id="t3", action="screenshot"),
        ]
        
        workflow = WorkflowDefinition(
            workflow_id="wf_001",
            name="Example Workflow",
            description="Test workflow",
            tasks=tasks,
            dependencies=[]
        )
        
        self.assertEqual(workflow.workflow_id, "wf_001")
        self.assertEqual(len(workflow.tasks), 3)
    
    def test_sequential_execution_plan(self):
        """Test sequential execution plan (no parallelization)"""
        tasks = [
            Task(task_id="t1", action="navigate", url="https://example.com"),
            Task(task_id="t2", action="execute_js", javascript="return 1;"),
        ]
        
        workflow = WorkflowDefinition(
            workflow_id="wf_002",
            name="Sequential",
            description="Sequential workflow",
            tasks=tasks,
            dependencies=[],
            parallel_allowed=False
        )
        
        plan = workflow.get_execution_plan()
        # Each task in its own stage
        self.assertEqual(len(plan), 2)
        self.assertEqual(plan[0], ["t1"])
        self.assertEqual(plan[1], ["t2"])
    
    def test_parallel_execution_plan(self):
        """Test parallel execution plan with dependencies"""
        tasks = [
            Task(task_id="t1", action="navigate", url="https://example.com"),
            Task(task_id="t2", action="navigate", url="https://example.com"),
            Task(task_id="t3", action="screenshot"),
        ]
        
        # t3 depends on t1 and t2
        deps = [
            TaskDependency("t3", "t1", DependencyType.REQUIRES_SUCCESS),
            TaskDependency("t3", "t2", DependencyType.REQUIRES_SUCCESS),
        ]
        
        workflow = WorkflowDefinition(
            workflow_id="wf_003",
            name="Parallel",
            description="Parallel workflow",
            tasks=tasks,
            dependencies=deps,
            parallel_allowed=True
        )
        
        plan = workflow.get_execution_plan()
        # t1 and t2 can run in parallel, then t3
        self.assertEqual(len(plan), 2)
        self.assertIn("t1", plan[0])
        self.assertIn("t2", plan[0])
        self.assertEqual(plan[1], ["t3"])
    
    def test_workflow_serialization(self):
        """Test workflow serialization"""
        tasks = [Task(task_id="t1", action="navigate", url="https://example.com")]
        workflow = WorkflowDefinition(
            workflow_id="wf_004",
            name="Test",
            description="Test workflow",
            tasks=tasks,
            dependencies=[]
        )
        
        wf_dict = workflow.to_dict()
        self.assertEqual(wf_dict['workflow_id'], "wf_004")
        self.assertEqual(len(wf_dict['tasks']), 1)


class TestTaskScheduler(unittest.TestCase):
    """Test task scheduler"""
    
    def setUp(self):
        """Setup test fixtures"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db_path = self.temp_db.name
        self.temp_db.close()
        init_phase5_tables(self.db_path)
        self.scheduler = TaskScheduler(self.db_path)
    
    def tearDown(self):
        """Cleanup"""
        import os
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def test_schedule_task(self):
        """Test scheduling a task"""
        task = Task(task_id="sch_001", action="navigate", url="https://example.com")
        scheduled = ScheduledTask(
            task_template=task,
            schedule_type=ScheduleType.ONE_TIME
        )
        
        task_id = self.scheduler.schedule_task(scheduled)
        self.assertEqual(task_id, "sch_001")
        self.assertIn("sch_001", self.scheduler.scheduled_tasks)
    
    def test_get_due_tasks(self):
        """Test getting tasks due for execution"""
        task = Task(task_id="sch_002", action="navigate", url="https://example.com")
        scheduled = ScheduledTask(
            task_template=task,
            schedule_type=ScheduleType.ONE_TIME,
            next_execution=datetime.now() - timedelta(seconds=1)
        )
        
        self.scheduler.schedule_task(scheduled)
        due_tasks = self.scheduler.get_due_tasks()
        
        self.assertEqual(len(due_tasks), 1)
        self.assertEqual(due_tasks[0].action, "navigate")
    
    def test_unschedule_task(self):
        """Test unscheduling a task"""
        task = Task(task_id="sch_003", action="navigate", url="https://example.com")
        scheduled = ScheduledTask(
            task_template=task,
            schedule_type=ScheduleType.ONE_TIME
        )
        
        self.scheduler.schedule_task(scheduled)
        self.assertIn("sch_003", self.scheduler.scheduled_tasks)
        
        result = self.scheduler.unschedule_task("sch_003")
        self.assertTrue(result)
        self.assertNotIn("sch_003", self.scheduler.scheduled_tasks)
    
    def test_scheduler_status(self):
        """Test scheduler status reporting"""
        task = Task(task_id="sch_004", action="navigate", url="https://example.com")
        scheduled = ScheduledTask(
            task_template=task,
            schedule_type=ScheduleType.ONE_TIME,
            enabled=True
        )
        
        self.scheduler.schedule_task(scheduled)
        status = self.scheduler.get_status()
        
        self.assertEqual(status['scheduled_tasks'], 1)
        self.assertEqual(status['enabled_tasks'], 1)


class TestWorkflowOrchestrator(unittest.TestCase):
    """Test workflow orchestration"""
    
    def setUp(self):
        """Setup test fixtures"""  
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db_path = self.temp_db.name
        self.temp_db.close()
        init_phase5_tables(self.db_path)
        self.orchestrator = WorkflowOrchestrator(self.db_path)
    
    def tearDown(self):
        """Cleanup"""
        import os
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def test_register_workflow(self):
        """Test registering a workflow"""
        tasks = [Task(task_id="t1", action="navigate", url="https://example.com")]
        workflow = WorkflowDefinition(
            workflow_id="wf_005",
            name="Test",
            description="Test",
            tasks=tasks,
            dependencies=[]
        )
        
        wf_id = self.orchestrator.register_workflow(workflow)
        self.assertEqual(wf_id, "wf_005")
        self.assertIn("wf_005", self.orchestrator.workflows)
    
    def test_start_workflow(self):
        """Test starting a workflow"""
        tasks = [Task(task_id="t1", action="navigate", url="https://example.com")]
        workflow = WorkflowDefinition(
            workflow_id="wf_006",
            name="Test",
            description="Test",
            tasks=tasks,
            dependencies=[]
        )
        
        self.orchestrator.register_workflow(workflow)
        instance_id = self.orchestrator.start_workflow("wf_006")
        
        self.assertIsNotNone(instance_id)
        self.assertIn(instance_id, self.orchestrator.workflow_instances)
    
    def test_workflow_task_result_recording(self):
        """Test recording workflow task results"""
        tasks = [Task(task_id="t1", action="navigate", url="https://example.com")]
        workflow = WorkflowDefinition(
            workflow_id="wf_007",
            name="Test",
            description="Test",
            tasks=tasks,
            dependencies=[]
        )
        
        self.orchestrator.register_workflow(workflow)
        instance_id = self.orchestrator.start_workflow("wf_007")
        
        result = {'status': 'success', 'output': 'test'}
        self.orchestrator.record_workflow_task_result(instance_id, "t1", result)
        
        instance = self.orchestrator.workflow_instances[instance_id]
        self.assertEqual(instance['task_results']['t1'], result)
    
    def test_workflow_completion_check(self):
        """Test checking workflow completion"""
        tasks = [
            Task(task_id="t1", action="navigate", url="https://example.com"),
            Task(task_id="t2", action="screenshot"),
        ]
        workflow = WorkflowDefinition(
            workflow_id="wf_008",
            name="Test",
            description="Test",
            tasks=tasks,
            dependencies=[]
        )
        
        self.orchestrator.register_workflow(workflow)
        instance_id = self.orchestrator.start_workflow("wf_008")
        
        # Not complete yet
        self.assertFalse(self.orchestrator.check_workflow_complete(instance_id))
        
        # Record results
        self.orchestrator.record_workflow_task_result(instance_id, "t1", {'status': 'success'})
        self.assertFalse(self.orchestrator.check_workflow_complete(instance_id))
        
        self.orchestrator.record_workflow_task_result(instance_id, "t2", {'status': 'success'})
        self.assertTrue(self.orchestrator.check_workflow_complete(instance_id))


class TestBatchTaskProcessor(unittest.TestCase):
    """Test batch task processing"""
    
    def test_create_batch(self):
        """Test creating a batch of tasks"""
        base_task = Task(task_id="base", action="navigate")
        urls = ["https://example1.com", "https://example2.com", "https://example3.com"]
        
        batch = BatchTaskProcessor.create_batch("batch_001", base_task, urls)
        
        self.assertEqual(len(batch), 3)
        self.assertEqual(batch[0].url, "https://example1.com")
        self.assertEqual(batch[1].url, "https://example2.com")
        self.assertEqual(batch[2].url, "https://example3.com")
    
    def test_aggregate_results(self):
        """Test aggregating batch results"""
        tasks = []
        for i in range(10):
            task = Task(task_id=f"t_{i:02d}", action="navigate", url=f"https://example{i}.com")
            if i < 8:
                task.status = TaskStatus.COMPLETED
                task.result = {'status': 'success', 'data': f'result_{i}'}
            else:
                task.status = TaskStatus.FAILED
                task.error = f'Error {i}'
            tasks.append(task)
        
        agg = BatchTaskProcessor.aggregate_results(tasks)
        
        self.assertEqual(agg['total_tasks'], 10)
        self.assertEqual(agg['successful'], 8)
        self.assertEqual(agg['failed'], 2)
        self.assertEqual(agg['success_rate'], 80.0)


if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING)
    unittest.main(verbosity=2)
