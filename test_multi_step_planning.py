"""
Test Multi-Step Mission Planning

Validates the new multi-step planner integration:
- MultiStepMissionPlanner creates TaskBreakdown
- Per-step tool selection works
- UnifiedProposal generated correctly
- Single cohesive message format

Author: Buddy Multi-Step Architecture Team
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


def test_multi_step_planner():
    """Test MultiStepMissionPlanner end-to-end"""
    from Back_End.multi_step_mission_planner import multi_step_planner
    from Back_End.action_readiness_engine import ReadinessResult, ReadinessDecision
    
    print("\n" + "="*80)
    print("TEST: Multi-Step Mission Planning")
    print("="*80 + "\n")
    
    # Create a mock ReadinessResult
    class MockReadinessResult:
        def __init__(self):
            self.decision = ReadinessDecision.READY
            self.intent = 'research'
            self.action_object = 'Find contact information for tech companies in California'
            self.action_target = 10
            self.source_url = None
            self.constraints = {'target_count': 10}
            self.intent_candidates = []
            self.clarification_question = None
    
    readiness = MockReadinessResult()
    raw_message = "Find contact information for 10 tech companies in California"
    
    try:
        # Plan mission
        print("🚀 Planning multi-step mission...")
        proposal = multi_step_planner.plan_mission(
            readiness_result=readiness,
            raw_chat_message=raw_message,
            user_id="test_user"
        )
        
        # Validate proposal
        print(f"\n✅ Mission Planned: {proposal.mission_id}")
        print(f"   Title: {proposal.mission_title}")
        print(f"   Objective: {proposal.objective}")
        print(f"\n📊 Metrics:")
        print(f"   Total Steps: {proposal.total_steps}")
        print(f"   Buddy Steps: {proposal.buddy_steps}")
        print(f"   Human Steps: {proposal.human_steps}")
        print(f"   Hybrid Steps: {proposal.hybrid_steps}")
        print(f"\n💰 Cost:")
        print(f"   Total: ${proposal.total_cost_usd:.4f}")
        print(f"\n⏱️  Time:")
        print(f"   Buddy: {proposal.estimated_buddy_time_seconds:.1f}s")
        print(f"   Human: {proposal.estimated_human_time_minutes}min")
        print(f"   Total: {proposal.estimated_total_time_minutes}min")
        print(f"\n👤 Human Involvement:")
        print(f"   Requires Approval: {proposal.requires_approval}")
        print(f"   Has Blocking Steps: {proposal.has_blocking_steps}")
        print(f"   Actions Required: {len(proposal.human_actions_required)}")
        
        # Show executive summary
        print(f"\n📝 Executive Summary:")
        print(f"   {proposal.executive_summary}")
        
        # Show step breakdown
        print(f"\n📋 Task Breakdown:")
        for step in proposal.task_breakdown.steps[:3]:  # First 3 steps
            print(f"   Step {step.step_number}: {step.description[:60]}...")
            print(f"      Type: {step.step_type.value}")
            print(f"      Tools: {', '.join(step.tools_used) if step.tools_used else 'None'}")
            if step.estimated_cost:
                print(f"      Cost: ${step.estimated_cost.total_usd:.4f}")
            if step.estimated_buddy_time:
                print(f"      Duration: {step.estimated_buddy_time:.1f}s")
        
        if len(proposal.task_breakdown.steps) > 3:
            print(f"   ... and {len(proposal.task_breakdown.steps) - 3} more steps")
        
        # Validate structure
        assert proposal.mission_id, "Mission ID missing"
        assert proposal.total_steps > 0, "No steps generated"
        assert proposal.executive_summary, "Executive summary missing"
        assert proposal.approval_options, "Approval options missing"
        
        print(f"\n✅ All validations passed!")
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


def test_unified_proposal_response():
    """Test that UnifiedProposal converts to ResponseEnvelope correctly"""
    from Back_End.multi_step_mission_planner import multi_step_planner
    from Back_End.action_readiness_engine import ReadinessResult, ReadinessDecision
    from Back_End.response_envelope import unified_proposal_response
    
    print("\n" + "="*80)
    print("TEST: Unified Proposal Response Format")
    print("="*80 + "\n")
    
    # Create a mock ReadinessResult
    class MockReadinessResult:
        def __init__(self):
            self.decision = ReadinessDecision.READY
            self.intent = 'search'
            self.action_object = 'Latest Python tutorials'
            self.action_target = 5
            self.source_url = None
            self.constraints = {'target_count': 5}
            self.intent_candidates = []
            self.clarification_question = None
    
    readiness = MockReadinessResult()
    
    try:
        # Plan mission
        print("🚀 Planning mission...")
        proposal = multi_step_planner.plan_mission(
            readiness_result=readiness,
            raw_chat_message="Find latest Python tutorials",
            user_id="test_user"
        )
        
        # Convert to response envelope
        print("📦 Creating response envelope...")
        response_envelope = unified_proposal_response(proposal.to_dict())
        
        # Validate response
        print(f"\n✅ Response Envelope Created")
        print(f"   Type: {response_envelope.response_type.value}")
        print(f"   Summary: {response_envelope.summary[:100]}...")
        print(f"   Artifacts: {len(response_envelope.artifacts)}")
        
        if response_envelope.artifacts:
            artifact = response_envelope.artifacts[0]
            print(f"\n📄 First Artifact:")
            print(f"   Type: {artifact.artifact_type.value}")
            print(f"   Title: {artifact.title}")
            print(f"   Has Content: {artifact.content is not None}")
        
        # Validate structure
        assert response_envelope.summary, "Summary missing"
        assert len(response_envelope.artifacts) > 0, "No artifacts"
        assert response_envelope.response_type.value == "artifact_bundle", "Wrong response type"
        
        print(f"\n✅ All validations passed!")
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
    print("\n🧪 Multi-Step Mission Planning Test Suite\n")
    
    results = []
    
    # Run tests
    results.append(("Multi-Step Planner", test_multi_step_planner()))
    results.append(("Unified Proposal Response", test_unified_proposal_response()))
    
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
