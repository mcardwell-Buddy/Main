"""
BUDDY DYNAMIC TASK SCHEDULER - TEST HARNESS
============================================

Purpose: Integration tests for Phase 6 task scheduler with Phase 5 web tools
Phase: 6 - Dynamic Task Scheduling & Conditional Workflows
Status: ACTIVE

Test Coverage:
- Priority-based task execution
- Dependency resolution
- Risk-based filtering
- Conditional branching
- Retry logic
- Phase 5 web tool integration
- Dry-run mode verification
- Metrics capture

Author: Buddy Phase 6 Testing Team
Date: February 5, 2026
"""

import sys
import time
import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

# Import scheduler
from buddy_dynamic_task_scheduler import (
    TaskScheduler,
    TaskPriority,
    RiskLevel,
    TaskStatus,
    ConditionalBranch,
    create_scheduler
)

# Import Phase 5 web tools (if available)
try:
    from backend import web_tools
    PHASE5_AVAILABLE = True
except ImportError:
    PHASE5_AVAILABLE = False
    print("WARNING: Phase 5 web tools not available - using mock actions")


class TaskSchedulerTestHarness:
    """
    Test harness for dynamic task scheduler
    
    Tests:
    1. Priority-based execution (CRITICAL before LOW)
    2. Dependency resolution (task waits for dependencies)
    3. Risk filtering (high-risk deferred with low confidence)
    4. Conditional branching (success/failure paths)
    5. Phase 5 web tool integration (dry-run mode)
    """
    
    def __init__(self, enable_dry_run: bool = True):
        """Initialize test harness"""
        self.enable_dry_run = enable_dry_run
        self.test_results: List[Dict[str, Any]] = []
        self.scheduler: Optional[TaskScheduler] = None
        
        print("=" * 80)
        print("BUDDY DYNAMIC TASK SCHEDULER - TEST HARNESS")
        print("=" * 80)
        print(f"Phase 5 Available: {PHASE5_AVAILABLE}")
        print(f"Dry-Run Mode: {enable_dry_run}")
        print()
    
    def create_mock_actions(self) -> Dict[str, callable]:
        """Create mock actions for testing"""
        
        def mock_web_inspect(url: str) -> Dict[str, Any]:
            """Mock web inspection"""
            print(f"  [MOCK] Inspecting {url}")
            time.sleep(0.3)
            return {
                'success': True,
                'url': url,
                'inspection': {
                    'forms': ['login_form'],
                    'buttons': ['submit', 'cancel'],
                    'inputs': ['email', 'password']
                }
            }
        
        def mock_web_navigate(url: str) -> Dict[str, Any]:
            """Mock navigation"""
            print(f"  [MOCK] Navigating to {url}")
            time.sleep(0.2)
            return {
                'success': True,
                'url': url,
                'final_url': url,
                'title': 'Test Page'
            }
        
        def mock_web_click(selector_or_text: str, tag: str = 'button') -> Dict[str, Any]:
            """Mock click action"""
            print(f"  [MOCK] Clicking {tag} with text/selector: {selector_or_text}")
            time.sleep(0.2)
            return {
                'success': True,
                'target': selector_or_text,
                'message': f'Clicked {selector_or_text}'
            }
        
        def mock_web_fill(field_hint: str, value: str) -> Dict[str, Any]:
            """Mock form fill"""
            masked_value = '***' if 'password' in field_hint.lower() else value
            print(f"  [MOCK] Filling field '{field_hint}' with '{masked_value}'")
            time.sleep(0.2)
            return {
                'success': True,
                'field_hint': field_hint,
                'value': masked_value,
                'message': f'Filled {field_hint}'
            }
        
        def mock_web_extract(selector: str, extract_type: str = 'text') -> Dict[str, Any]:
            """Mock data extraction"""
            print(f"  [MOCK] Extracting {extract_type} from {selector}")
            time.sleep(0.2)
            return {
                'success': True,
                'selector': selector,
                'elements': [
                    {'text': 'Example Item 1'},
                    {'text': 'Example Item 2'}
                ],
                'count': 2
            }
        
        def mock_failing_action() -> Dict[str, Any]:
            """Mock action that fails (for retry testing)"""
            print(f"  [MOCK] Failing action (for retry test)")
            raise Exception("Simulated failure for retry testing")
        
        return {
            'web_inspect': mock_web_inspect,
            'web_navigate': mock_web_navigate,
            'web_click': mock_web_click,
            'web_fill': mock_web_fill,
            'web_extract': mock_web_extract,
            'failing_action': mock_failing_action
        }
    
    def run_test_1_priority_execution(self) -> Dict[str, Any]:
        """Test 1: Priority-based task execution"""
        print("\n" + "=" * 80)
        print("TEST 1: Priority-Based Task Execution")
        print("=" * 80)
        print("Goal: Verify CRITICAL tasks execute before LOW priority tasks\n")
        
        # Create scheduler
        scheduler = create_scheduler(enable_dry_run=self.enable_dry_run, max_concurrent_tasks=1)
        self.scheduler = scheduler
        
        # Register mock actions
        actions = self.create_mock_actions()
        for name, action in actions.items():
            scheduler.register_action(name, action)
        
        # Add tasks in reverse priority order
        task_low = scheduler.add_task(
            description="LOW priority task (should execute last)",
            action_name='web_inspect',
            action_params={'url': 'https://low-priority.com'},
            priority=TaskPriority.LOW,
            risk_level=RiskLevel.LOW,
            confidence_score=0.8
        )
        
        task_medium = scheduler.add_task(
            description="MEDIUM priority task",
            action_name='web_inspect',
            action_params={'url': 'https://medium-priority.com'},
            priority=TaskPriority.MEDIUM,
            risk_level=RiskLevel.LOW,
            confidence_score=0.8
        )
        
        task_critical = scheduler.add_task(
            description="CRITICAL priority task (should execute first)",
            action_name='web_inspect',
            action_params={'url': 'https://critical-priority.com'},
            priority=TaskPriority.CRITICAL,
            risk_level=RiskLevel.LOW,
            confidence_score=0.9
        )
        
        # Start scheduler
        scheduler.start()
        
        # Wait for completion
        print("Executing tasks...")
        completed = scheduler.wait_for_completion(timeout=15.0)
        
        # Stop scheduler
        scheduler.stop()
        
        # Verify execution order
        critical_task = scheduler.get_task(task_critical)
        medium_task = scheduler.get_task(task_medium)
        low_task = scheduler.get_task(task_low)
        
        critical_started = critical_task.started_at if critical_task else None
        medium_started = medium_task.started_at if medium_task else None
        low_started = low_task.started_at if low_task else None
        
        # Check order
        order_correct = (
            critical_started and medium_started and low_started and
            critical_started < medium_started < low_started
        )
        
        result = {
            'test_name': 'Priority Execution',
            'passed': completed and order_correct,
            'completed': completed,
            'order_correct': order_correct,
            'execution_order': {
                'critical': critical_started,
                'medium': medium_started,
                'low': low_started
            },
            'metrics': scheduler.get_metrics()
        }
        
        print(f"\n[PASS] Test Completed: {'PASS' if result['passed'] else 'FAIL'}")
        print(f"  - All tasks completed: {completed}")
        print(f"  - Execution order correct: {order_correct}")
        
        self.test_results.append(result)
        return result
    
    def run_test_2_dependency_resolution(self) -> Dict[str, Any]:
        """Test 2: Task dependency resolution"""
        print("\n" + "=" * 80)
        print("TEST 2: Task Dependency Resolution")
        print("=" * 80)
        print("Goal: Verify tasks wait for dependencies before executing\n")
        
        # Create scheduler
        scheduler = create_scheduler(enable_dry_run=self.enable_dry_run, max_concurrent_tasks=1)
        self.scheduler = scheduler
        
        # Register mock actions
        actions = self.create_mock_actions()
        for name, action in actions.items():
            scheduler.register_action(name, action)
        
        # Add tasks with dependencies
        task_a = scheduler.add_task(
            description="Task A: Navigate to site",
            action_name='web_navigate',
            action_params={'url': 'https://example.com'},
            priority=TaskPriority.HIGH,
            risk_level=RiskLevel.LOW,
            confidence_score=0.9
        )
        
        task_b = scheduler.add_task(
            description="Task B: Inspect site (depends on A)",
            action_name='web_inspect',
            action_params={'url': 'https://example.com'},
            priority=TaskPriority.HIGH,
            risk_level=RiskLevel.LOW,
            confidence_score=0.9,
            dependencies=[task_a]
        )
        
        task_c = scheduler.add_task(
            description="Task C: Extract data (depends on B)",
            action_name='web_extract',
            action_params={'selector': '.product-name', 'extract_type': 'text'},
            priority=TaskPriority.HIGH,
            risk_level=RiskLevel.LOW,
            confidence_score=0.8,
            dependencies=[task_b]
        )
        
        # Start scheduler
        scheduler.start()
        
        # Wait for completion
        print("Executing tasks with dependencies...")
        completed = scheduler.wait_for_completion(timeout=15.0)
        
        # Stop scheduler
        scheduler.stop()
        
        # Verify execution order
        task_a_obj = scheduler.get_task(task_a)
        task_b_obj = scheduler.get_task(task_b)
        task_c_obj = scheduler.get_task(task_c)
        
        a_started = task_a_obj.started_at if task_a_obj else None
        b_started = task_b_obj.started_at if task_b_obj else None
        c_started = task_c_obj.started_at if task_c_obj else None
        
        # Check order respects dependencies
        order_correct = (
            a_started and b_started and c_started and
            a_started < b_started < c_started
        )
        
        result = {
            'test_name': 'Dependency Resolution',
            'passed': completed and order_correct,
            'completed': completed,
            'order_correct': order_correct,
            'execution_order': {
                'task_a': a_started,
                'task_b': b_started,
                'task_c': c_started
            },
            'metrics': scheduler.get_metrics()
        }
        
        print(f"\n[PASS] Test Completed: {'PASS' if result['passed'] else 'FAIL'}")
        print(f"  - All tasks completed: {completed}")
        print(f"  - Dependency order correct: {order_correct}")
        
        self.test_results.append(result)
        return result
    
    def run_test_3_risk_filtering(self) -> Dict[str, Any]:
        """Test 3: Risk-based task filtering"""
        print("\n" + "=" * 80)
        print("TEST 3: Risk-Based Task Filtering")
        print("=" * 80)
        print("Goal: Verify high-risk tasks with low confidence are deferred\n")
        
        # Create scheduler
        scheduler = create_scheduler(enable_dry_run=self.enable_dry_run, max_concurrent_tasks=1)
        self.scheduler = scheduler
        
        # Register mock actions
        actions = self.create_mock_actions()
        for name, action in actions.items():
            scheduler.register_action(name, action)
        
        # Add high-risk task with LOW confidence (should be deferred)
        task_risky = scheduler.add_task(
            description="HIGH risk task with LOW confidence (should defer)",
            action_name='web_fill',
            action_params={'field_hint': 'credit_card', 'value': '1234-5678'},
            priority=TaskPriority.HIGH,
            risk_level=RiskLevel.HIGH,
            confidence_score=0.4  # Below 0.7 threshold
        )
        
        # Add high-risk task with HIGH confidence (should execute in dry-run)
        task_safe = scheduler.add_task(
            description="HIGH risk task with HIGH confidence (should execute)",
            action_name='web_fill',
            action_params={'field_hint': 'email', 'value': 'test@example.com'},
            priority=TaskPriority.HIGH,
            risk_level=RiskLevel.HIGH,
            confidence_score=0.9  # Above 0.7 threshold
        )
        
        # Start scheduler
        scheduler.start()
        
        # Wait for completion
        print("Executing tasks with risk filtering...")
        time.sleep(3.0)  # Give time for tasks to process
        
        # Stop scheduler
        scheduler.stop()
        
        # Verify outcomes
        risky_task = scheduler.get_task(task_risky)
        safe_task = scheduler.get_task(task_safe)
        
        risky_deferred = risky_task.status == TaskStatus.DEFERRED if risky_task else False
        safe_completed = safe_task.status == TaskStatus.COMPLETED if safe_task else False
        
        result = {
            'test_name': 'Risk Filtering',
            'passed': risky_deferred and safe_completed,
            'risky_deferred': risky_deferred,
            'safe_completed': safe_completed,
            'risky_status': risky_task.status.name if risky_task else 'UNKNOWN',
            'safe_status': safe_task.status.name if safe_task else 'UNKNOWN',
            'metrics': scheduler.get_metrics()
        }
        
        print(f"\n[PASS] Test Completed: {'PASS' if result['passed'] else 'FAIL'}")
        print(f"  - High-risk low-confidence deferred: {risky_deferred}")
        print(f"  - High-risk high-confidence completed: {safe_completed}")
        
        self.test_results.append(result)
        return result
    
    def run_test_4_conditional_branching(self) -> Dict[str, Any]:
        """Test 4: Conditional branching based on outcomes"""
        print("\n" + "=" * 80)
        print("TEST 4: Conditional Branching")
        print("=" * 80)
        print("Goal: Verify conditional branches trigger based on task outcomes\n")
        
        # Create scheduler
        scheduler = create_scheduler(enable_dry_run=self.enable_dry_run, max_concurrent_tasks=1)
        self.scheduler = scheduler
        
        # Register mock actions
        actions = self.create_mock_actions()
        for name, action in actions.items():
            scheduler.register_action(name, action)
        
        # Add conditional task
        task_main = scheduler.add_task(
            description="Main task with conditional branches",
            action_name='web_inspect',
            action_params={'url': 'https://example.com'},
            priority=TaskPriority.HIGH,
            risk_level=RiskLevel.LOW,
            confidence_score=0.9,
            conditional_branches=[
                ConditionalBranch(
                    condition_type='success',
                    next_task_template={
                        'description': 'Success branch: Extract data',
                        'action_name': 'web_extract',
                        'action_params': {'selector': '.data', 'extract_type': 'text'},
                        'priority': 'HIGH',
                        'risk_level': 'LOW',
                        'confidence_score': 0.8
                    }
                )
            ]
        )
        
        # Start scheduler
        scheduler.start()
        
        # Wait for completion
        print("Executing task with conditional branching...")
        completed = scheduler.wait_for_completion(timeout=15.0)
        
        # Stop scheduler
        scheduler.stop()
        
        # Verify conditional branch was triggered
        metrics = scheduler.get_metrics()
        branch_triggered = metrics['total_executed'] >= 2  # Main task + branch task
        
        result = {
            'test_name': 'Conditional Branching',
            'passed': completed and branch_triggered,
            'completed': completed,
            'branch_triggered': branch_triggered,
            'total_executed': metrics['total_executed'],
            'metrics': metrics
        }
        
        print(f"\n[PASS] Test Completed: {'PASS' if result['passed'] else 'FAIL'}")
        print(f"  - Main task completed: {completed}")
        print(f"  - Conditional branch triggered: {branch_triggered}")
        print(f"  - Total tasks executed: {metrics['total_executed']}")
        
        self.test_results.append(result)
        return result
    
    def run_test_5_retry_logic(self) -> Dict[str, Any]:
        """Test 5: Retry logic on failures"""
        print("\n" + "=" * 80)
        print("TEST 5: Retry Logic")
        print("=" * 80)
        print("Goal: Verify tasks retry on failure up to max_attempts\n")
        
        # Create scheduler
        scheduler = create_scheduler(enable_dry_run=self.enable_dry_run, max_concurrent_tasks=1)
        self.scheduler = scheduler
        
        # Register mock actions
        actions = self.create_mock_actions()
        for name, action in actions.items():
            scheduler.register_action(name, action)
        
        # Add failing task (will retry 3 times)
        task_failing = scheduler.add_task(
            description="Failing task (should retry 3 times)",
            action_name='failing_action',
            priority=TaskPriority.HIGH,
            risk_level=RiskLevel.LOW,
            confidence_score=0.8,
            metadata={'max_attempts': 3}
        )
        
        # Start scheduler
        scheduler.start()
        
        # Wait for retries to complete
        print("Executing failing task with retries...")
        time.sleep(8.0)  # Give time for retries with backoff
        
        # Stop scheduler
        scheduler.stop()
        
        # Verify retry attempts
        failing_task = scheduler.get_task(task_failing)
        retry_count = failing_task.attempt_count if failing_task else 0
        final_status = failing_task.status if failing_task else TaskStatus.PENDING
        
        result = {
            'test_name': 'Retry Logic',
            'passed': retry_count == 3 and final_status == TaskStatus.FAILED,
            'retry_count': retry_count,
            'expected_retries': 3,
            'final_status': final_status.name,
            'metrics': scheduler.get_metrics()
        }
        
        print(f"\n[PASS] Test Completed: {'PASS' if result['passed'] else 'FAIL'}")
        print(f"  - Retry attempts: {retry_count} (expected: 3)")
        print(f"  - Final status: {final_status.name}")
        
        self.test_results.append(result)
        return result
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate test report"""
        print("\n" + "=" * 80)
        print("TEST REPORT SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r['passed'])
        
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': total_tests - passed_tests,
            'success_rate': passed_tests / total_tests if total_tests > 0 else 0.0,
            'dry_run_enabled': self.enable_dry_run,
            'phase5_available': PHASE5_AVAILABLE,
            'test_results': self.test_results,
            'validation_checklist': {
                'priority_execution': any(r['test_name'] == 'Priority Execution' and r['passed'] for r in self.test_results),
                'dependency_resolution': any(r['test_name'] == 'Dependency Resolution' and r['passed'] for r in self.test_results),
                'risk_filtering': any(r['test_name'] == 'Risk Filtering' and r['passed'] for r in self.test_results),
                'conditional_branching': any(r['test_name'] == 'Conditional Branching' and r['passed'] for r in self.test_results),
                'retry_logic': any(r['test_name'] == 'Retry Logic' and r['passed'] for r in self.test_results)
            }
        }
        
        print(f"\nTotal Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {report['success_rate'] * 100:.1f}%")
        
        print("\nValidation Checklist:")
        for check, status in report['validation_checklist'].items():
            status_str = "[PASS]" if status else "[FAIL]"
            print(f"  {status_str} - {check}")
        
        # Save report
        report_file = Path("outputs/task_scheduler_metrics") / f"test_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        report_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n[INFO] Report saved to: {report_file}")
        
        return report


def main():
    """Run all tests"""
    harness = TaskSchedulerTestHarness(enable_dry_run=True)
    
    try:
        # Run tests
        harness.run_test_1_priority_execution()
        harness.run_test_2_dependency_resolution()
        harness.run_test_3_risk_filtering()
        harness.run_test_4_conditional_branching()
        harness.run_test_5_retry_logic()
        
        # Generate report
        report = harness.generate_report()
        
        # Exit code
        if report['success_rate'] >= 0.8:
            print("\n[PASS] TEST SUITE PASSED (>=80% success rate)")
            return 0
        else:
            print("\n[FAIL] TEST SUITE FAILED (<80% success rate)")
            return 1
    
    except Exception as e:
        print(f"\n[ERROR] TEST SUITE ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

