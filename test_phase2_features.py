"""
Test Phase 2 Features: Email, Scheduling, Parallelization

Validates:
- Email tool registration and functionality
- Step scheduling (time-based, event-based, cascade)
- Parallelization detection
- Integration with multi-step planner

Author: Buddy Phase 2 Architecture Team  
Date: February 11, 2026
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_email_tool():
    """Test email tool registration"""
    print("\n" + "="*80)
    print("TEST: Email Tool Registration (Work + Buddy)")
    print("="*80 + "\n")
    
    try:
        from Back_End.tool_email import send_work_email, send_buddy_email
        from Back_End.tool_registry import tool_registry
        
        # Check if work email tool is registered
        assert 'email_send_work' in tool_registry.tools, "Work email tool not registered"
        
        tool_info = tool_registry.tools['email_send_work']
        print(f"✅ Work email tool registered: email_send_work")
        print(f"   Description: {tool_info['description'][:100]}...")
        assert tool_info['func'] == send_work_email, "Work tool function mismatch"
        
        # Check if Buddy email tool is registered
        assert 'email_send_buddy' in tool_registry.tools, "Buddy email tool not registered"
        
        tool_info = tool_registry.tools['email_send_buddy']
        print(f"✅ Buddy email tool registered: email_send_buddy")
        print(f"   Description: {tool_info['description'][:100]}...")
        assert tool_info['func'] == send_buddy_email, "Buddy tool function mismatch"
        
        print(f"\n✅ Both email tools validated successfully")
        
        print("\n" + "="*80)
        print("TEST PASSED")
        print("="*80 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        print("\n" + "="*80)
        print("TEST FAILED")
        print("="*80 + "\n")
        return False


def test_step_scheduler():
    """Test step scheduler functionality"""
    print("\n" + "="*80)
    print("TEST: Step Scheduler")
    print("="*80 + "\n")
    
    try:
        from Back_End.step_scheduler import (
            step_scheduler, ScheduleTrigger, RecurrencePattern
        )
        
        # Test immediate schedule
        immediate = step_scheduler.create_immediate_schedule(1)
        print(f"✅ Immediate schedule: {immediate.to_human_readable()}")
        assert immediate.trigger == ScheduleTrigger.IMMEDIATE
        
        # Test time-based schedule
        time_based = step_scheduler.create_time_schedule(
            step_number=2,
            scheduled_time="2026-02-15T09:00:00Z"
        )
        print(f"✅ Time-based schedule: {time_based.to_human_readable()}")
        assert time_based.trigger == ScheduleTrigger.TIME_BASED
        
        # Test event-based schedule
        event_based = step_scheduler.create_event_schedule(
            step_number=3,
            depends_on_step=2,
            event_condition="success"
        )
        print(f"✅ Event-based schedule: {event_based.to_human_readable()}")
        assert event_based.trigger == ScheduleTrigger.EVENT_BASED
        
        # Test cascade schedule
        cascade = step_scheduler.create_cascade_schedule(
            step_number=4,
            depends_on_step=3
        )
        print(f"✅ Cascade schedule: {cascade.to_human_readable()}")
        assert cascade.trigger == ScheduleTrigger.CASCADE
        
        # Test recurring schedule
        recurring = step_scheduler.create_recurring_schedule(
            step_number=5,
            recurrence=RecurrencePattern.DAILY,
            scheduled_time="09:00:00"
        )
        print(f"✅ Recurring schedule: {recurring.to_human_readable()}")
        assert recurring.trigger == ScheduleTrigger.RECURRING
        
        # Test auto-schedule
        schedules = step_scheduler.auto_schedule_steps(3)
        print(f"\n✅ Auto-scheduled 3 steps:")
        for schedule in schedules:
            print(f"   Step {schedule.step_number}: {schedule.to_human_readable()}")
        assert len(schedules) == 3
        
        # Test validation
        issues = step_scheduler.validate_schedules(schedules)
        print(f"\n✅ Validation: {len(issues)} issues found")
        assert len(issues) == 0, f"Unexpected validation issues: {issues}"
        
        print("\n" + "="*80)
        print("TEST PASSED")
        print("="*80 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        print("\n" + "="*80)
        print("TEST FAILED")
        print("="*80 + "\n")
        return False


def test_parallelization_detector():
    """Test parallelization detection"""
    print("\n" + "="*80)
    print("TEST: Parallelization Detector")
    print("="*80 + "\n")
    
    try:
        from Back_End.parallelization_detector import parallelization_detector
        from Back_End.task_breakdown_and_proposal import TaskStep, StepType
        from Back_End.action_readiness_engine import ExecutionClass
        
        # Create mock steps
        steps = [
            TaskStep(
                step_number=1,
                description="Search for Python tutorials",
                step_type=StepType.PURE_BUDDY,
                execution_class=ExecutionClass.AI_EXECUTABLE,
                estimated_buddy_time=5.0,
                tools_used=['web_search']
            ),
            TaskStep(
                step_number=2,
                description="Search for JavaScript tutorials",
                step_type=StepType.PURE_BUDDY,
                execution_class=ExecutionClass.AI_EXECUTABLE,
                estimated_buddy_time=5.0,
                tools_used=['web_search']
            ),
            TaskStep(
                step_number=3,
                description="Search for React tutorials",
                step_type=StepType.PURE_BUDDY,
                execution_class=ExecutionClass.AI_EXECUTABLE,
                estimated_buddy_time=5.0,
                tools_used=['web_search']
            )
        ]
        
        # Analyze parallelization
        opportunities = parallelization_detector.analyze_steps(steps)
        
        print(f"✅ Found {len(opportunities)} parallelization opportunities")
        
        for i, opp in enumerate(opportunities, 1):
            print(f"\n   Opportunity {i}:")
            print(f"   - {opp.to_human_readable()}")
            print(f"   - Sequential: {opp.sequential_time_seconds:.1f}s")
            print(f"   - Parallel: {opp.parallel_time_seconds:.1f}s")
            print(f"   - Savings: {opp.time_savings_seconds:.1f}s")
            print(f"   - Risk: {opp.risk_level}")
        
        print("\n" + "="*80)
        print("TEST PASSED")
        print("="*80 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        print("\n" + "="*80)
        print("TEST FAILED")
        print("="*80 + "\n")
        return False


def test_phase2_integration():
    """Test Phase 2 integration with multi-step planner"""
    print("\n" + "="*80)
    print("TEST: Phase 2 Integration (Scheduling + Parallelization)")
    print("="*80 + "\n")
    
    try:
        from Back_End.multi_step_mission_planner import multi_step_planner
        from Back_End.action_readiness_engine import ReadinessResult, ReadinessDecision
        
        # Create mock ReadinessResult
        class MockReadinessResult:
            def __init__(self):
                self.decision = ReadinessDecision.READY
                self.intent = 'search'
                self.action_object = 'Find tutorials for Python, JavaScript, and React'
                self.action_target = 3
                self.source_url = None
                self.constraints = {'target_count': 3}
                self.intent_candidates = []
                self.clarification_question = None
        
        readiness = MockReadinessResult()
        
        print("🚀 Planning multi-step mission with Phase 2 features...")
        proposal = multi_step_planner.plan_mission(
            readiness_result=readiness,
            raw_chat_message="Find tutorials for Python, JavaScript, and React",
            user_id="test_user"
        )
        
        # Validate scheduling
        print(f"\n✅ Mission Planned: {proposal.mission_id}")
        print(f"\n📅 Step Schedules:")
        for schedule_dict in proposal.step_schedules:
            if schedule_dict:
                print(f"   Step {schedule_dict['step_number']}: {schedule_dict['description']}")
        
        assert len(proposal.step_schedules) > 0, "No schedules generated"
        
        # Validate parallelization
        print(f"\n⚡ Parallelization Opportunities: {len(proposal.parallelization_opportunities)}")
        for opp_dict in proposal.parallelization_opportunities:
            print(f"   - Steps {opp_dict['parallel_steps']}: saves {opp_dict['time_savings_seconds']:.1f}s")
        
        # Validate enhanced proposal structure
        proposal_dict = proposal.to_dict()
        assert 'scheduling' in proposal_dict, "Scheduling section missing"
        assert 'step_schedules' in proposal_dict['scheduling'], "Step schedules missing"
        assert 'parallelization_opportunities' in proposal_dict['scheduling'], "Parallelization missing"
        
        print(f"\n✅ All Phase 2 features integrated successfully")
        
        print("\n" + "="*80)
        print("TEST PASSED")
        print("="*80 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        print("\n" + "="*80)
        print("TEST FAILED")
        print("="*80 + "\n")
        return False


if __name__ == "__main__":
    print("\n🧪 Phase 2 Test Suite: Email, Scheduling, Parallelization\n")
    
    results = []
    
    # Run tests
    results.append(("Email Tool", test_email_tool()))
    results.append(("Step Scheduler", test_step_scheduler()))
    results.append(("Parallelization Detector", test_parallelization_detector()))
    results.append(("Phase 2 Integration", test_phase2_integration()))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print("="*80 + "\n")
    
    sys.exit(0 if passed == total else 1)
