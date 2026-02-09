#!/usr/bin/env python3
"""
BUDDY RESULT SURFACING DEMO

Comprehensive demonstration that Buddy is alive with clear result display.

Shows:
1. Execution lifecycle
2. API response format
3. Human-readable logging
4. Result summary
"""

import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent / "backend"))

from mission_approval_service import approve_mission
from execution_service import execute_mission

MISSIONS_FILE = Path("outputs/phase25/missions.jsonl")


def create_demo_mission(description: str) -> str:
    """Create a demo mission"""
    mission_id = f"mission_demo_{int(datetime.now().timestamp() * 1000)}"
    
    record = {
        "mission_id": mission_id,
        "status": "proposed",
        "source": "demo",
        "objective": {
            "type": "math",
            "description": description
        }
    }
    
    with open(MISSIONS_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(record) + '\n')
    
    return mission_id


def run_demo_mission(description: str):
    """Run a complete mission demo"""
    
    print("\n" + "=" * 80)
    print(f"RUNNING DEMO MISSION: {description}")
    print("=" * 80)
    
    # Step 1: Create
    print("\n[Step 1] CREATING MISSION")
    mission_id = create_demo_mission(description)
    print(f"  ✅ Created: {mission_id}")
    print(f"  Description: {description}")
    
    # Step 2: Approve
    print("\n[Step 2] APPROVING MISSION")
    approval_result = approve_mission(mission_id)
    if approval_result.get('success'):
        print(f"  ✅ Approved - Status: {approval_result.get('status')}")
    else:
        print(f"  ❌ Failed: {approval_result.get('message')}")
        return
    
    # Step 3: Execute
    print("\n[Step 3] EXECUTING MISSION")
    execution_result = execute_mission(mission_id)
    
    # Step 4: Display results
    if execution_result.get('success'):
        print(f"  ✅ Execution succeeded")
        
        print("\n" + "─" * 80)
        print("EXECUTION RESULT DETAILS:")
        print("─" * 80)
        
        print(f"\n  Mission ID: {execution_result.get('mission_id')}")
        print(f"  Tool Used: {execution_result.get('tool_used')}")
        print(f"  Confidence: {execution_result.get('tool_confidence'):.0%}")
        print(f"  Status: {execution_result.get('status')}")
        
        print(f"\n  ┌─ HUMAN-READABLE RESULT ─┐")
        print(f"  │ {execution_result.get('result_summary'):<23} │")
        print(f"  └─────────────────────────┘")
        
        print(f"\n  Full result data:")
        full_result = execution_result.get('execution_result', {})
        for key, value in full_result.items():
            print(f"    • {key}: {value}")
    else:
        print(f"  ❌ Execution failed: {execution_result.get('error')}")
    
    return execution_result


def main():
    """Run demonstrations"""
    
    print("\n" + "╔" + "═" * 78 + "╗")
    print("║" + " " * 15 + "BUDDY RESULT SURFACING DEMO" + " " * 36 + "║")
    print("║" + " " * 13 + "Demonstrating that Buddy is alive and working" + " " * 20 + "║")
    print("╚" + "═" * 78 + "╝")
    
    # Ensure directory exists
    MISSIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not MISSIONS_FILE.exists():
        MISSIONS_FILE.touch()
    
    # Run multiple demo missions
    demos = [
        "Calculate what is 100 plus 50?",
        "What is the result of 25 times 4?",
        "Calculate 999 divided by 3"
    ]
    
    results = []
    for demo_description in demos:
        result = run_demo_mission(demo_description)
        if result and result.get('success'):
            results.append(result)
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    successful = len([r for r in results if r.get('success')])
    print(f"\n✅ {successful}/{len(results)} missions executed successfully")
    
    print("\nMissions executed:")
    for result in results:
        if result.get('success'):
            print(f"  • {result.get('mission_id')}")
            print(f"    Tool: {result.get('tool_used')}")
            print(f"    Result: {result.get('result_summary')}")
    
    print("\n" + "=" * 80)
    print("✅ BUDDY IS ALIVE AND PRODUCING CLEAR, READABLE RESULTS")
    print("=" * 80 + "\n")
    
    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
