"""
End-to-End Validation: Chat → Execution → Whiteboard

Tests the full pipeline:
1. Send a message through /chat/integrated
2. Observe mission execution
3. Verify whiteboard shows results
"""

import sys
import json
import asyncio
import time
from pathlib import Path

sys.path.insert(0, 'C:/Users/micha/Buddy')

from backend.interaction_orchestrator import InteractionOrchestrator
from backend.execution import execution_queue, executor
from backend.whiteboard.mission_whiteboard import get_mission_whiteboard
from backend.mission_execution_runner import run_executor_with_timeout


async def main():
    print("=" * 70)
    print("END-TO-END VALIDATION: Chat => Execution => Whiteboard")
    print("=" * 70)

    # STEP 1: Create mission via orchestrator
    print("\n[STEP 1] Creating mission via /chat/integrated")
    orchestrator = InteractionOrchestrator()
    test_message = "Get product names and prices from example.com"
    
    response = orchestrator.process_message(
        message=test_message,
        session_id="validation_e2e_001"
    )
    
    if not response.missions_spawned:
        print("  [FAIL] No mission spawned")
        return False
    
    mission_id = response.missions_spawned[0].mission_id
    print(f"  [OK] Mission created: {mission_id}")
    print(f"  [OK] Queue size: {execution_queue.size()}")
    
    if execution_queue.size() != 1:
        print("  [FAIL] Mission not queued")
        return False

    # STEP 2: Execute the mission
    print(f"\n[STEP 2] Executing mission (5 second timeout)")
    try:
        await run_executor_with_timeout(duration_seconds=5)
        print(f"  [OK] Executor completed")
    except Exception as e:
        print(f"  [FAIL] Executor error: {e}")
        return False
    
    # Verify mission was dequeued
    if execution_queue.size() != 0:
        print(f"  [WARN] Queue not empty after execution: {execution_queue.size()}")

    # STEP 3: Check mission records
    print(f"\n[STEP 3] Checking mission records in JSONL")
    output_dir = Path('C:/Users/micha/Buddy/outputs/phase25')
    mission_file = output_dir / 'missions.jsonl'
    
    if not mission_file.exists():
        print(f"  [FAIL] {mission_file} not found")
        return False
    
    with open(mission_file, 'r') as f:
        lines = f.readlines()
    
    # Find all records for this mission
    mission_records = []
    for line in lines:
        try:
            record = json.loads(line)
            if record.get('mission_id') == mission_id:
                mission_records.append(record)
        except:
            pass
    
    print(f"  [OK] Found {len(mission_records)} records for mission")
    
    if len(mission_records) < 3:
        print(f"  [FAIL] Expected at least 3 records (proposed, active, completed)")
        for i, rec in enumerate(mission_records):
            print(f"    [{i}] {rec.get('status', 'unknown')}")
        return False
    
    # Check status progression
    statuses = [rec.get('status') for rec in mission_records]
    print(f"  [OK] Status progression: {' => '.join(statuses)}")
    
    final_status = statuses[-1]
    if final_status not in ['completed', 'failed']:
        print(f"  [FAIL] Final status should be completed/failed, got: {final_status}")
        return False

    # STEP 4: Verify whiteboard can reconstruct mission
    print(f"\n[STEP 4] Reconstructing mission in whiteboard")
    try:
        whiteboard = get_mission_whiteboard(mission_id)
        print(f"  [OK] Whiteboard retrieved")
        print(f"    Status: {whiteboard.get('status')}")
        print(f"    Start time: {whiteboard.get('start_time')}")
        print(f"    End time: {whiteboard.get('end_time')}")
        
        if whiteboard.get('status') not in ['completed', 'failed']:
            print(f"  [WARN] Whiteboard status doesn't match: {whiteboard.get('status')}")
    except Exception as e:
        print(f"  [FAIL] Whiteboard reconstruction failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # FINAL STATUS
    print("\n" + "=" * 70)
    print("ALL TESTS PASSED")
    print("=" * 70)
    print("\nPipeline validated:")
    print("  1. Chat message -> Mission created [OK]")
    print("  2. Mission queued [OK]")
    print("  3. Executor processed mission [OK]")
    print("  4. Status updates written to JSONL [OK]")
    print("  5. Whiteboard can reconstruct mission [OK]")
    return True


if __name__ == '__main__':
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
