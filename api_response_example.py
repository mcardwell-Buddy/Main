#!/usr/bin/env python3
"""
API RESPONSE EXAMPLE

Show what the API returns when executing a mission.
This demonstrates the human-readable result surfacing.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "backend"))

from mission_approval_service import approve_mission
from execution_service import execute_mission

MISSIONS_FILE = Path("outputs/phase25/missions.jsonl")
from datetime import datetime


def create_test_mission() -> str:
    """Create a test mission"""
    mission_id = f"mission_api_demo_{int(datetime.now().timestamp() * 1000)}"
    
    record = {
        "mission_id": mission_id,
        "status": "proposed",
        "source": "api_demo",
        "objective": {
            "type": "math",
            "description": "What is 15 plus 27?"
        }
    }
    
    with open(MISSIONS_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(record) + '\n')
    
    return mission_id


def main():
    """Show API response"""
    
    print("\n" + "=" * 75)
    print("API RESPONSE EXAMPLE: Execution Result Surfacing")
    print("=" * 75)
    
    # Setup
    MISSIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not MISSIONS_FILE.exists():
        MISSIONS_FILE.touch()
    
    # Create and approve mission
    mission_id = create_test_mission()
    approve_mission(mission_id)
    
    # Execute mission
    result = execute_mission(mission_id)
    
    # Format as API response (what would be returned by POST /api/missions/{id}/execute)
    api_response = {
        "status": "success",
        "mission_id": result.get('mission_id'),
        "execution_status": result.get('status'),
        "tool_used": result.get('tool_used'),
        "tool_confidence": result.get('tool_confidence'),
        "result_summary": result.get('result_summary'),
        "message": f"Mission executed successfully using {result.get('tool_used')}",
        "result": result.get('execution_result')
    }
    
    print("\n[HTTP 200] POST /api/missions/{mission_id}/execute")
    print("\nRESPONSE BODY:")
    print(json.dumps(api_response, indent=2))
    
    print("\n" + "=" * 75)
    print("KEY FIELDS FOR HUMAN CONSUMPTION:")
    print("=" * 75)
    print(f"  Tool Used: {api_response['tool_used']}")
    print(f"  Confidence: {api_response['tool_confidence']:.0%}")
    print(f"  Result Summary: {api_response['result_summary']}")
    print(f"  Message: {api_response['message']}")
    
    print("\n" + "=" * 75 + "\n")


if __name__ == "__main__":
    main()

