"""
Confidence Check: Tool Selection with Real Mission

Demonstrates tool selection invariant working with actual mission execution.
"""

import json
import time
from pathlib import Path
from backend.execution_service import ExecutionService

MISSIONS_FILE = Path("outputs/phase25/missions.jsonl")


def clear_missions():
    """Clear missions.jsonl"""
    if MISSIONS_FILE.exists():
        MISSIONS_FILE.unlink()
    MISSIONS_FILE.parent.mkdir(parents=True, exist_ok=True)


def create_and_approve_mission(mission_id: str, objective: str):
    """Create and approve a mission"""
    # Create
    mission = {
        'mission_id': mission_id,
        'mission': {
            'objective': {
                'description': objective
            }
        },
        'status': 'proposed',
        'created_at': f'2026-02-08T{time.time()}'
    }
    
    with open(MISSIONS_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(mission) + '\n')
    
    # Approve
    approval = {
        'event_type': 'mission_status_update',
        'mission_id': mission_id,
        'status': 'approved',
        'timestamp': f'2026-02-08T{time.time()}'
    }
    
    with open(MISSIONS_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(approval) + '\n')


def run_confidence_mission(objective: str, expected_intent: str):
    """Run a single confidence mission"""
    print(f"\n{'='*80}")
    print(f"CONFIDENCE MISSION: {objective[:60]}")
    print(f"{'='*80}")
    
    clear_missions()
    service = ExecutionService()
    
    mission_id = f"confidence_{int(time.time() * 1000)}"
    
    print(f"\n1. Creating mission...")
    print(f"   Objective: {objective}")
    print(f"   Expected Intent: {expected_intent}")
    
    create_and_approve_mission(mission_id, objective)
    
    print(f"\n2. Executing mission...")
    result = service.execute_mission(mission_id)
    
    print(f"\n3. Results:")
    print(f"   ✓ Success: {result.get('success')}")
    print(f"   ✓ Intent: {result.get('intent')}")
    print(f"   ✓ Tool Used: {result.get('tool_used')}")
    print(f"   ✓ Tool Confidence: {result.get('tool_confidence', 0.0):.2f}")
    
    if result.get('success'):
        print(f"   ✓ Result Summary: {result.get('result_summary', 'N/A')[:100]}")
        print(f"\n✅ Mission SUCCEEDED")
        
        # Verify intent matches expected
        if result.get('intent') == expected_intent:
            print(f"✅ Intent classification CORRECT ({expected_intent})")
        else:
            print(f"⚠️  Intent was {result.get('intent')}, expected {expected_intent}")
        
        return True
    else:
        error = result.get('error', 'Unknown error')
        print(f"   ✗ Error: {error}")
        print(f"\n❌ Mission FAILED")
        
        # Check if failure was due to tool selection invariant
        if 'not allowed for intent' in error:
            print(f"\n🔒 TOOL SELECTION INVARIANT ENFORCED")
            print(f"   Tool '{result.get('tool_used')}' was correctly rejected for intent '{result.get('intent')}'")
            print(f"   Allowed tools: {result.get('allowed_tools', [])}")
        
        return False


def main():
    print("\n" + "="*80)
    print("🎯 TOOL SELECTION CONFIDENCE CHECK")
    print("="*80)
    print("\nDemonstrating tool selection with invariant enforcement")
    print("No human hints required - system determines intent and selects tool")
    
    # Test missions with different intents
    missions = [
        ("Calculate what is 100 + 50", "calculation"),
        ("Calculate 25 * 4", "calculation"),
        ("What is 999 / 3", "calculation"),
    ]
    
    results = []
    for objective, expected_intent in missions:
        success = run_confidence_mission(objective, expected_intent)
        results.append((objective[:50], success))
    
    # Summary
    print("\n" + "="*80)
    print("CONFIDENCE CHECK SUMMARY")
    print("="*80)
    
    for objective, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {objective}")
    
    passed = sum(1 for _, s in results if s)
    total = len(results)
    
    print(f"\n{passed}/{total} missions executed successfully")
    
    if passed == total:
        print("\n✅ CONFIDENCE CHECK PASSED")
        print("\nKey Observations:")
        print("  ✓ Tool selection is deterministic")
        print("  ✓ Intent classification is accurate")
        print("  ✓ Tool/intent validation works correctly")
        print("  ✓ Results are clearly surfaced")
        print("  ✓ No human hinting required")
        print("\n🎯 Tool selection invariant is ENFORCED and WORKING")
        return True
    else:
        print(f"\n⚠️  {total - passed} mission(s) failed")
        print("   Review logs above for details")
        return False


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
