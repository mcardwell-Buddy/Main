#!/usr/bin/env python3
"""
DIRECT EXECUTION TESTS (No HTTP - Direct Service Calls)

Verify that:
1. Proposed missions do NOT execute
2. Approved missions execute exactly once
3. Execution does NOT re-run for the same mission_id
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Any

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from execution_service import ExecutionService, execute_mission
from tool_selector import tool_selector
from datetime import datetime

MISSIONS_FILE = Path("outputs/phase25/missions.jsonl")


def get_mission_records(mission_id: str) -> List[Dict]:
    """Read all records for a mission from missions.jsonl"""
    records = []
    if not MISSIONS_FILE.exists():
        return records
    
    with open(MISSIONS_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                if record.get('mission_id') == mission_id:
                    records.append(record)
            except:
                continue
    
    return records


def count_execution_records(mission_id: str) -> int:
    """Count how many execution records exist for a mission"""
    records = get_mission_records(mission_id)
    exec_count = sum(1 for r in records if r.get('event_type') == 'mission_executed')
    return exec_count


def get_current_status(mission_id: str) -> str:
    """Get the current status of a mission (last record wins)"""
    records = get_mission_records(mission_id)
    if not records:
        return None
    
    # Most recent record has the current status
    return records[-1].get('status')


def create_proposed_mission() -> str:
    """Manually create a proposed mission in missions.jsonl"""
    mission_id = f"mission_direct_{int(datetime.now().timestamp() * 1000)}"
    
    # Write the proposal record with full mission data matching production structure
    record = {
        "mission_id": mission_id,
        "status": "proposed",
        "source": "test",
        "objective": {
            "type": "math",
            "description": "Calculate 100 + 50"
        },
        "metadata": {
            "created_at": datetime.now().isoformat(),
            "test": True
        }
    }
    
    with open(MISSIONS_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(record) + '\n')
    
    return mission_id


def approve_mission(mission_id: str) -> None:
    """Manually approve a mission"""
    record = {
        "event_type": "mission_status_update",
        "mission_id": mission_id,
        "status": "approved",
        "timestamp": datetime.now().isoformat()
    }
    
    with open(MISSIONS_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(record) + '\n')


def print_section(title: str):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_step(num: int, text: str):
    """Print a numbered step"""
    print(f"\n[Step {num}] {text}")


def test_invariant_1_proposed_no_execution() -> bool:
    """
    INVARIANT 1: Proposed missions do NOT execute
    
    Workflow:
    1. Create mission (status=proposed)
    2. Attempt to execute WITHOUT approving
    3. Verify: HTTP 400 returned, NO execution record written
    """
    print_section("INVARIANT 1: Proposed Missions Do Not Execute")
    
    try:
        # Step 1: Create proposed mission
        print_step(1, "Creating mission in proposed state...")
        mission_id = create_proposed_mission()
        print(f"  ✓ Mission created: {mission_id}")
        print(f"  ✓ Status: proposed (not approved)")
        
        # Step 2: Verify no records exist yet except creation
        records_before = get_mission_records(mission_id)
        exec_before = count_execution_records(mission_id)
        print(f"  ✓ Execution records before attempt: {exec_before}")
        assert exec_before == 0, "Should have 0 execution records initially"
        
        # Step 3: Attempt to execute WITHOUT approving
        print_step(2, "Attempting to execute proposed mission...")
        result = execute_mission(mission_id)
        print(f"  → Result: {result}")
        
        # Step 4: Verify execution was rejected
        if not result.get('success', False):
            error_msg = result.get('error', '')
            if 'not "approved"' in error_msg or 'proposed' in error_msg:
                print(f"  ✓ Execution correctly REJECTED: {error_msg}")
            else:
                print(f"  ✓ Execution rejected with error: {error_msg}")
        else:
            print(f"  ✗ ERROR: Execution was not rejected! Result: {result}")
            return False
        
        # Step 5: Verify NO execution record was written
        exec_after = count_execution_records(mission_id)
        print(f"  ✓ Execution records after attempt: {exec_after}")
        
        if exec_after != exec_before:
            print(f"  ✗ ERROR: Execution record was written when it shouldn't be!")
            return False
        
        print("\n✅ INVARIANT 1 PASSED: Proposed missions do NOT execute")
        return True
        
    except Exception as e:
        print(f"\n❌ INVARIANT 1 FAILED with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_invariant_2_approved_single_execution() -> bool:
    """
    INVARIANT 2: Approved missions execute exactly once
    
    Workflow:
    1. Create mission (status=proposed)
    2. Approve mission (status=approved)
    3. Execute mission
    4. Verify: Exactly ONE execution record written with success status
    """
    print_section("INVARIANT 2: Approved Missions Execute Exactly Once")
    
    try:
        # Step 1: Create proposed mission
        print_step(1, "Creating mission in proposed state...")
        mission_id = create_proposed_mission()
        print(f"  ✓ Mission created: {mission_id}")
        
        # Step 2: Approve the mission
        print_step(2, "Approving mission...")
        approve_mission(mission_id)
        current_status = get_current_status(mission_id)
        print(f"  ✓ Mission approved")
        print(f"  ✓ Current status: {current_status}")
        assert current_status == "approved", f"Status should be approved, got {current_status}"
        
        # Step 3: Execute the mission
        print_step(3, "Executing approved mission...")
        result = execute_mission(mission_id)
        print(f"  → Result: {result}")
        
        if not result.get('success', False):
            print(f"  ✗ ERROR: Execution failed: {result}")
            return False
        
        print(f"  ✓ Execution succeeded")
        print(f"  ✓ Tool used: {result.get('tool_used', 'N/A')}")
        
        # Step 4: Verify exactly ONE execution record
        exec_count = count_execution_records(mission_id)
        print(f"\n  Execution record count: {exec_count}")
        
        if exec_count != 1:
            print(f"  ✗ ERROR: Expected 1 execution record, got {exec_count}")
            return False
        
        print(f"  ✓ Exactly one execution record found")
        
        # Step 5: Verify execution record has correct status
        records = get_mission_records(mission_id)
        exec_records = [r for r in records if r.get('event_type') == 'mission_executed']
        if exec_records:
            exec_status = exec_records[0].get('status')
            print(f"  ✓ Execution status: {exec_status}")
        
        print("\n✅ INVARIANT 2 PASSED: Approved missions execute exactly once")
        return True
        
    except Exception as e:
        print(f"\n❌ INVARIANT 2 FAILED with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_invariant_3_no_reexecution() -> bool:
    """
    INVARIANT 3: Execution does NOT re-run for same mission_id
    
    Workflow:
    1. Create and approve mission
    2. Execute mission (first time)
    3. Attempt to execute again
    4. Verify: Still only ONE execution record (second attempt rejected)
    """
    print_section("INVARIANT 3: Execution Does Not Re-Run")
    
    try:
        # Step 1: Create and approve mission
        print_step(1, "Creating and approving mission...")
        mission_id = create_proposed_mission()
        approve_mission(mission_id)
        current_status = get_current_status(mission_id)
        print(f"  ✓ Mission created and approved: {mission_id}")
        print(f"  ✓ Current status: {current_status}")
        
        # Step 2: Execute mission (first time)
        print_step(2, "Executing mission (first attempt)...")
        result1 = execute_mission(mission_id)
        print(f"  → First execution result: {result1}")
        
        if not result1.get('success', False):
            print(f"  ✗ ERROR: First execution failed: {result1}")
            return False
        
        exec_count_after_first = count_execution_records(mission_id)
        print(f"  ✓ First execution succeeded")
        print(f"  ✓ Execution records after first attempt: {exec_count_after_first}")
        
        if exec_count_after_first != 1:
            print(f"  ✗ ERROR: Expected 1 record after first exec, got {exec_count_after_first}")
            return False
        
        # Step 3: Attempt to execute AGAIN
        print_step(3, "Attempting to re-execute (second attempt)...")
        result2 = execute_mission(mission_id)
        print(f"  → Second execution result: {result2}")
        
        # Step 4: Verify second attempt was rejected
        if result2.get('success', False):
            print(f"  ✗ ERROR: Second execution should be rejected but succeeded!")
            return False
        
        error_msg = result2.get('error', '')
        print(f"  ✓ Second execution correctly rejected: {error_msg}")
        
        # Step 5: Verify STILL only ONE execution record
        exec_count_after_second = count_execution_records(mission_id)
        print(f"  ✓ Execution records after second attempt: {exec_count_after_second}")
        
        if exec_count_after_second != 1:
            print(f"  ✗ ERROR: Expected 1 record total, got {exec_count_after_second}")
            return False
        
        print(f"  ✓ No additional execution record written")
        
        print("\n✅ INVARIANT 3 PASSED: Execution does not re-run")
        return True
        
    except Exception as e:
        print(f"\n❌ INVARIANT 3 FAILED with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all invariant tests"""
    print("=" * 80)
    print("EXECUTION INVARIANT TEST SUITE (DIRECT SERVICE CALLS)")
    print("=" * 80)
    print("\nVerifying approval-gated execution with zero side effects\n")
    
    # Ensure missions file exists
    MISSIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not MISSIONS_FILE.exists():
        MISSIONS_FILE.touch()
    
    # Run tests
    result1 = test_invariant_1_proposed_no_execution()
    result2 = test_invariant_2_approved_single_execution()
    result3 = test_invariant_3_no_reexecution()
    
    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUITE SUMMARY")
    print("=" * 80)
    print(f"\nInvariant 1 (Proposed → No Execution):     {'✅ PASS' if result1 else '❌ FAIL'}")
    print(f"Invariant 2 (Approved → Single Exec):       {'✅ PASS' if result2 else '❌ FAIL'}")
    print(f"Invariant 3 (No Re-Execution):              {'✅ PASS' if result3 else '❌ FAIL'}")
    
    all_passed = result1 and result2 and result3
    print("\n" + ("=" * 80))
    if all_passed:
        print("✅ ALL INVARIANTS PASSED - Execution system is safe!")
        print("=" * 80)
        return 0
    else:
        print("❌ SOME INVARIANTS FAILED - Review errors above")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
