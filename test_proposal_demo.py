#!/usr/bin/env python3
"""
Unified Proposal System Demo
Shows what a proposal looks like when presented to the user
"""

import json
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from Back_End.task_breakdown_and_proposal import TaskBreakdownEngine
from Back_End.proposal_presenter import ProposalPresenter
from Back_End.cost_estimator import ServiceTier

def print_section(title, char="="):
    """Print a formatted section header"""
    print(f"\n{char * 80}")
    print(f"  {title}")
    print(f"{char * 80}\n")

def print_proposal(proposal_dict, budget=True):
    """Pretty-print a proposal"""
    
    mission_title = proposal_dict.get('mission_title', 'Mission')
    objective = proposal_dict.get('objective', '')
    executive_summary = proposal_dict.get('executive_summary', '')
    
    metrics = proposal_dict.get('metrics', {})
    costs = proposal_dict.get('costs', {})
    time = proposal_dict.get('time', {})
    task_breakdown = proposal_dict.get('task_breakdown', {})
    human_involvement = proposal_dict.get('human_involvement', {})
    next_steps = proposal_dict.get('next_steps', {})
    
    # Header
    print("┌" + "─" * 78 + "┐")
    print(f"│ {mission_title[:76].ljust(76)} │")
    print("└" + "─" * 78 + "┘")
    print()
    
    # Objective
    print(f"📋 OBJECTIVE")
    print(f"   {objective}")
    print()
    
    # Executive Summary
    print(f"📝 EXECUTIVE SUMMARY")
    print(f"   {executive_summary}")
    print()
    
    # Metrics
    print(f"📊 STEP BREAKDOWN")
    total = metrics.get('total_steps', 0)
    buddy = metrics.get('buddy_steps', 0)
    human = metrics.get('human_steps', 0)
    hybrid = metrics.get('hybrid_steps', 0)
    
    print(f"   Total Steps:    {total}")
    print(f"   Buddy Steps:    {buddy} (I'll handle these automatically) 🤖")
    print(f"   Your Steps:     {human} (These need your input/approval) 👤")
    print(f"   Hybrid Steps:   {hybrid} (I start, you approve) ⚙️")
    print()
    
    # Costs
    print(f"💰 COST BREAKDOWN")
    total_cost = costs.get('total_usd', 0)
    print(f"   TOTAL COST: ${total_cost:.4f}")
    print()
    
    breakdown = costs.get('breakdown', [])
    if breakdown:
        print(f"   Cost by Service:")
        for item in breakdown:
            service = item.get('service', 'Unknown')
            cost = item.get('cost_usd', 0)
            ops = item.get('operations', 0)
            tier = item.get('tier', '')
            print(f"      • {service:<15} ${cost:.4f} ({ops} operations){f' [{tier}]' if tier else ''}")
    print()
    
    # Time
    print(f"⏱️  TIME ESTIMATES")
    buddy_seconds = time.get('buddy_seconds', 0)
    human_minutes = time.get('human_minutes', 0)
    total_minutes = time.get('total_minutes', 0)
    
    print(f"   My Time:        {buddy_seconds:.1f} seconds")
    print(f"   Your Time:      {human_minutes} minutes")
    print(f"   Total Time:     ~{total_minutes} minutes")
    print()
    
    # Human Involvement
    if human_involvement.get('requires_approval'):
        print(f"⚠️  REQUIRES YOUR APPROVAL before starting")
        print()
    
    if human_involvement.get('has_blocking_steps'):
        print(f"⏸️  BLOCKING STEPS: Some steps will pause waiting for your input")
        print()
    
    # What happens next
    print(f"📌 WHAT HAPPENS NEXT")
    print(f"   {next_steps.get('what_happens_next', 'Mission execution will begin.')}")
    print()
    
    # Steps detail
    steps = task_breakdown.get('steps', [])
    if steps:
        print(f"📋 DETAILED STEPS ({len(steps)} total)\n")
        for step in steps:
            step_num = step.get('step_number', '?')
            step_type = step.get('step_type', 'unknown').replace('_', ' ').upper()
            desc = step.get('description', '')
            cost = step.get('estimated_cost', {}).get('total_usd', 0) if step.get('estimated_cost') else 0
            buddy_time = step.get('estimated_buddy_time', 0)
            human_time = step.get('estimated_human_time', 0)
            is_blocking = step.get('is_blocking', False)
            
            blocking_text = " [BLOCKING]" if is_blocking else ""
            
            print(f"   Step {step_num}: {desc}")
            print(f"      Type: {step_type}{blocking_text}")
            if cost > 0:
                print(f"      Cost: ${cost:.4f}")
            if buddy_time > 0:
                print(f"      My Time: {buddy_time:.1f}s")
            if human_time > 0:
                print(f"      Your Time: {human_time}min")
            
            human_actions = step.get('human_actions', [])
            if human_actions:
                print(f"      Required Actions:")
                for action in human_actions:
                    print(f"         • {action.get('action', '?')}: {action.get('description', '')}")
            print()
    
    # Approval options
    print(f"🎯 YOUR OPTIONS:")
    approval_options = next_steps.get('approval_options', ['Approve', 'Reject'])
    for i, option in enumerate(approval_options, 1):
        symbol = "✓" if "Approve" in option else "✗" if "Reject" in option else "⚙"
        print(f"   {symbol} [{i}] {option}")
    print()
    
    print("┌" + "─" * 78 + "┐")
    print("│  What would you like to do? (Approve / Modify / Reject)             │")
    print("└" + "─" * 78 + "┘")


def test_proposal_generation():
    """Generate and display a sample proposal"""
    
    print_section("UNIFIED PROPOSAL SYSTEM - DEMO")
    print("Initializing proposal generation system...\n")
    
    # Initialize components
    try:
        engine = TaskBreakdownEngine(serpapi_tier=ServiceTier.FREE)
        presenter = ProposalPresenter()
        print("✓ TaskBreakdownEngine initialized")
        print("✓ ProposalPresenter initialized")
    except Exception as e:
        print(f"✗ Failed to initialize: {e}")
        return False
    
    # Test objectives
    test_objectives = [
        "Research the latest machine learning trends and create a technical summary document",
        "Find competitive pricing for cloud hosting services and compile a comparison table",
        "Search for React optimization techniques and write a best practices guide"
    ]
    
    for idx, objective in enumerate(test_objectives, 1):
        print_section(f"DEMO {idx}: Mission Proposal", "=")
        
        try:
            print(f"Objective: {objective}\n")
            print("Analyzing task...")
            
            # Analyze task
            task_breakdown = engine.analyze_task(objective)
            print(f"✓ Task analyzed: {len(task_breakdown.steps)} steps identified")
            
            # Create proposal
            print("Generating proposal...")
            proposal = presenter.create_proposal(
                mission_id=f"demo_{idx}",
                objective=objective,
                task_breakdown=task_breakdown,
                mission_title=f"Mission {idx}"
            )
            print("✓ Proposal generated")
            
            # Convert to dict for display
            proposal_dict = proposal.to_dict()
            
            # Display proposal
            print_proposal(proposal_dict)
            
            # Show JSON too
            print_section("RAW PROPOSAL DATA (as sent to frontend)", "-")
            print(json.dumps(proposal_dict, indent=2, default=str))
            
        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()
        
        if idx < len(test_objectives):
            input("\n[Press Enter to see next demo...]")
    
    print_section("Demo Complete", "=")
    print("\nThis is what users will see when they request a mission.")
    print("The system calculates costs, time estimates, and identifies")
    print("what Buddy can do vs what needs human approval.")
    return True

if __name__ == "__main__":
    try:
        success = test_proposal_generation()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

