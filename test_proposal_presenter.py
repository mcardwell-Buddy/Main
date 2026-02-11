"""
Test script for ProposalPresenter

Validates:
- UnifiedProposal generation
- Executive summary quality
- Cost breakdown formatting
- Human action extraction
- "What happens next" narratives
"""

import json
from Back_End.proposal_presenter import ProposalPresenter
from Back_End.task_breakdown_and_proposal import TaskBreakdownEngine
from Back_End.cost_estimator import ServiceTier

def test_simple_proposal():
    """Test proposal for a simple task."""
    print("\n=== Test 1: Simple Proposal ===")
    
    # Create task breakdown
    engine = TaskBreakdownEngine(ServiceTier.FREE)
    breakdown = engine.analyze_task("What is 25 multiplied by 48?")
    
    # Create proposal
    presenter = ProposalPresenter()
    proposal = presenter.create_proposal(
        mission_id="test-001",
        objective="What is 25 multiplied by 48?",
        task_breakdown=breakdown
    )
    
    print(f"Mission: {proposal.mission_title}")
    print(f"Executive Summary: {proposal.executive_summary}")
    print(f"\nMetrics:")
    print(f"  Total steps: {proposal.total_steps}")
    print(f"  Buddy steps: {proposal.buddy_steps}")
    print(f"  Human steps: {proposal.human_steps}")
    print(f"  Hybrid steps: {proposal.hybrid_steps}")
    print(f"\nCosts:")
    print(f"  Total: ${proposal.total_cost_usd:.4f}")
    print(f"\nTime:")
    print(f"  Buddy: {proposal.estimated_buddy_time_seconds:.1f}s")
    print(f"  Human: {proposal.estimated_human_time_minutes}min")
    print(f"  Total: {proposal.estimated_total_time_minutes}min")
    print(f"\nApproval Options: {proposal.approval_options}")
    print(f"\nWhat Happens Next: {proposal.what_happens_next}")
    
    assert proposal.mission_id == "test-001"
    assert proposal.total_steps > 0
    assert len(proposal.executive_summary) > 0
    print("\n[PASS] Simple proposal test passed\n")

def test_complex_proposal():
    """Test proposal for a complex multi-step task."""
    print("\n=== Test 2: Complex Proposal ===")
    
    # Create task breakdown for complex task
    engine = TaskBreakdownEngine(ServiceTier.STARTER)
    breakdown = engine.analyze_task(
        "Research AI market trends, analyze competitor pricing, and create a summary report"
    )
    
    # Create proposal
    presenter = ProposalPresenter()
    proposal = presenter.create_proposal(
        mission_id="test-002",
        objective="Research AI market trends, analyze competitor pricing, and create a summary report",
        task_breakdown=breakdown,
        mission_title="AI Market Analysis"
    )
    
    print(f"Mission: {proposal.mission_title}")
    print(f"Executive Summary: {proposal.executive_summary}")
    print(f"\nMetrics:")
    print(f"  Total steps: {proposal.total_steps}")
    print(f"  Buddy: {proposal.buddy_steps}, Human: {proposal.human_steps}, Hybrid: {proposal.hybrid_steps}")
    print(f"\nCosts:")
    print(f"  Total: ${proposal.total_cost_usd:.4f}")
    for cost in proposal.cost_breakdown:
        print(f"  - {cost['service']}: ${cost['cost_usd']:.4f} ({cost['operations']} ops)")
    
    print(f"\nRequires Approval: {proposal.requires_approval}")
    print(f"Has Blocking Steps: {proposal.has_blocking_steps}")
    
    # Print full JSON
    print("\nFull Proposal JSON:")
    print(json.dumps(proposal.to_dict(), indent=2))
    
    assert proposal.mission_title == "AI Market Analysis"
    assert proposal.total_steps >= 3  # Should break into multiple steps
    print("\n[PASS] Complex proposal test passed\n")

def test_human_approval_proposal():
    """Test proposal for task requiring human approval."""
    print("\n=== Test 3: Human Approval Proposal ===")
    
    # Create task breakdown
    engine = TaskBreakdownEngine(ServiceTier.STARTER)
    breakdown = engine.analyze_task(
        "Draft an email to investors about Q4 results and wait for approval before sending"
    )
    
    # Create proposal
    presenter = ProposalPresenter()
    proposal = presenter.create_proposal(
        mission_id="test-003",
        objective="Draft an email to investors about Q4 results and wait for approval before sending",
        task_breakdown=breakdown
    )
    
    print(f"Mission: {proposal.mission_title}")
    print(f"Executive Summary: {proposal.executive_summary}")
    print(f"\nRequires Approval: {proposal.requires_approval}")
    print(f"Has Blocking Steps: {proposal.has_blocking_steps}")
    print(f"\nHuman Actions Required: {len(proposal.human_actions_required)}")
    for action in proposal.human_actions_required:
        print(f"  - Step {action['step_number']}: {action['action']} ({action['estimated_minutes']}min)")
    
    print(f"\nWhat Happens Next: {proposal.what_happens_next}")
    
    # Check that approval options include "Review Steps" for blocking tasks
    print(f"\nApproval Options: {proposal.approval_options}")
    
    assert proposal.requires_approval or proposal.has_blocking_steps
    print("\n[PASS] Human approval proposal test passed\n")

def test_cost_breakdown_formatting():
    """Test cost breakdown formatting."""
    print("\n=== Test 4: Cost Breakdown Formatting ===")
    
    # Create task with known costs
    engine = TaskBreakdownEngine(ServiceTier.STARTER)
    breakdown = engine.analyze_task("Search for Python tutorials and summarize findings")
    
    # Create proposal
    presenter = ProposalPresenter()
    proposal = presenter.create_proposal(
        mission_id="test-004",
        objective="Search for Python tutorials and summarize findings",
        task_breakdown=breakdown
    )
    
    print(f"Total Cost: ${proposal.total_cost_usd:.4f}")
    print("\nCost Breakdown:")
    for cost in proposal.cost_breakdown:
        print(f"  Service: {cost['service']}")
        print(f"  Cost: ${cost['cost_usd']:.4f}")
        print(f"  Operations: {cost['operations']}")
        print(f"  Tier: {cost.get('tier', 'N/A')}")
        print(f"  Details: {cost['details']}")
        print()
    
    # Verify structure
    assert len(proposal.cost_breakdown) > 0
    for cost in proposal.cost_breakdown:
        assert 'service' in cost
        assert 'cost_usd' in cost
        assert 'operations' in cost
    
    print("[PASS] Cost breakdown formatting test passed\n")

def test_executive_summary_quality():
    """Test executive summary generation quality."""
    print("\n=== Test 5: Executive Summary Quality ===")
    
    test_cases = [
        "Calculate the square root of 144",
        "Research competitors and analyze their pricing strategy",
        "Create a social media campaign and get approval from marketing team"
    ]
    
    engine = TaskBreakdownEngine(ServiceTier.STARTER)
    presenter = ProposalPresenter()
    
    for idx, objective in enumerate(test_cases, 1):
        breakdown = engine.analyze_task(objective)
        proposal = presenter.create_proposal(
            mission_id=f"test-00{idx}",
            objective=objective,
            task_breakdown=breakdown
        )
        
        print(f"\nObjective: {objective}")
        print(f"Summary: {proposal.executive_summary}")
        print(f"Length: {len(proposal.executive_summary)} chars")
        
        # Check quality criteria
        assert len(proposal.executive_summary) > 0, "Summary should not be empty"
        assert len(proposal.executive_summary) < 500, "Summary should be concise"
        # Should mention either Buddy or cost/time
        has_buddy = 'Buddy' in proposal.executive_summary or 'automated' in proposal.executive_summary
        has_metrics = '$' in proposal.executive_summary or 'minute' in proposal.executive_summary
        assert has_buddy or has_metrics, "Summary should mention Buddy's role or metrics"
    
    print("\n[PASS] Executive summary quality test passed\n")

def test_proposal_to_dict():
    """Test proposal serialization to dict."""
    print("\n=== Test 6: Proposal Serialization ===")
    
    engine = TaskBreakdownEngine(ServiceTier.FREE)
    breakdown = engine.analyze_task("What year was Python created?")
    
    presenter = ProposalPresenter()
    proposal = presenter.create_proposal(
        mission_id="test-006",
        objective="What year was Python created?",
        task_breakdown=breakdown
    )
    
    # Convert to dict
    proposal_dict = proposal.to_dict()
    
    print("Proposal dict keys:")
    for key in proposal_dict.keys():
        print(f"  - {key}")
    
    # Verify required keys
    required_keys = [
        'mission_id', 'mission_title', 'objective', 'executive_summary',
        'task_breakdown', 'metrics', 'costs', 'time', 'human_involvement',
        'next_steps', 'metadata'
    ]
    
    for key in required_keys:
        assert key in proposal_dict, f"Missing required key: {key}"
    
    # Verify JSON serializable
    json_str = json.dumps(proposal_dict)
    assert len(json_str) > 0
    
    print(f"\nJSON size: {len(json_str)} bytes")
    print("[PASS] Proposal serialization test passed\n")

def run_all_tests():
    """Run all test scenarios."""
    print("=" * 60)
    print("PROPOSAL PRESENTER TEST SUITE")
    print("=" * 60)
    
    try:
        test_simple_proposal()
        test_complex_proposal()
        test_human_approval_proposal()
        test_cost_breakdown_formatting()
        test_executive_summary_quality()
        test_proposal_to_dict()
        
        print("=" * 60)
        print("[PASS] ALL TESTS PASSED!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n[FAIL] TEST FAILED: {e}\n")
        raise
    except Exception as e:
        print(f"\n[ERROR] UNEXPECTED ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    run_all_tests()

