#!/usr/bin/env python3
"""
BUDDY CONFIDENCE MISSION

Execute one end-to-end mission to demonstrate that Buddy is alive:
- Create mission
- Approve mission
- Execute mission
- Display results clearly
"""

import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent / "backend"))

from mission_approval_service import approve_mission
from execution_service import execute_mission

MISSIONS_FILE = Path("outputs/phase25/missions.jsonl")


def create_confidence_mission() -> str:
    """Create a simple math mission (higher confidence than extraction)"""
    mission_id = f"mission_confidence_{int(datetime.now().timestamp() * 1000)}"
    
    record = {
        "mission_id": mission_id,
        "status": "proposed",
        "source": "confidence_test",
        "objective": {
            "type": "math",
            "description": "Calculate what is 250 times 4?"
        },
        "metadata": {
            "created_at": datetime.now().isoformat(),
            "type": "confidence"
        }
    }
    
    with open(MISSIONS_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(record) + '\n')
    
    return mission_id


def main():
    """Run the confidence mission"""
    
    print("\n" + "=" * 70)
    print("BUDDY CONFIDENCE MISSION")
    print("=" * 70)
    
    # Ensure file exists
    MISSIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not MISSIONS_FILE.exists():
        MISSIONS_FILE.touch()
    
    # Step 1: Create mission
    print("\n[Step 1] Creating mission...")
    mission_id = create_confidence_mission()
    print(f"✅ Mission created: {mission_id}")
    print(f"   Objective: Calculate what is 250 times 4?")
    
    # Step 2: Approve mission
    print("\n[Step 2] Approving mission...")
    approval_result = approve_mission(mission_id)
    if approval_result.get('success'):
        print(f"✅ Mission approved")
        print(f"   Status: {approval_result.get('status')}")
    else:
        print(f"❌ Approval failed: {approval_result.get('message')}")
        return False
    
    # Step 3: Execute mission
    print("\n[Step 3] Executing mission...")
    execution_result = execute_mission(mission_id)
    
    # Step 4: Display results
    print("\n" + "=" * 70)
    print("EXECUTION RESULT")
    print("=" * 70)
    
    if execution_result.get('success'):
        print(f"\n✅ EXECUTION SUCCESSFUL")
        print(f"\nMission ID: {execution_result.get('mission_id')}")
        print(f"Tool Used: {execution_result.get('tool_used')}")
        print(f"Confidence: {execution_result.get('tool_confidence', 0):.2%}")
        print(f"Status: {execution_result.get('status')}")
        
        print(f"\n{'─' * 70}")
        print("RESULT SUMMARY:")
        print(f"{'─' * 70}")
        result_summary = execution_result.get('result_summary', 'No summary')
        print(result_summary)
        
        print(f"\n{'─' * 70}")
        print("FULL RESULT DATA:")
        print(f"{'─' * 70}")
        full_result = execution_result.get('execution_result', {})
        print(json.dumps(full_result, indent=2)[:500])
        
        print(f"\n{'=' * 70}")
        print("✅ BUDDY IS ALIVE AND WORKING!")
        print(f"{'=' * 70}\n")
        
        return True
    else:
        print(f"\n❌ EXECUTION FAILED")
        print(f"Error: {execution_result.get('error')}")
        print(f"{'=' * 70}\n")
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

