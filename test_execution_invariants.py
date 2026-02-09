#!/usr/bin/env python3
"""
EXECUTION INVARIANT TESTS

Verify that:
1. Proposed missions do NOT execute
2. Approved missions execute exactly once
3. Execution does NOT re-run for the same mission_id
"""

import requests
import json
import time
from pathlib import Path
from collections import defaultdict

BASE_URL = "http://127.0.0.1:8000"
MISSIONS_FILE = Path("outputs/phase25/missions.jsonl")


def get_mission_records(mission_id: str) -> list:
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


def create_mission(text: str) -> str:
    """Create a mission via chat, return mission_id"""
    payload = {
        'text': text,
        'source': 'chat'
    }
    
    response = requests.post(f"{BASE_URL}/chat/integrated", json=payload, timeout=10)
    if response.status_code != 200:
        raise Exception(f"Chat failed: {response.status_code}")
    
    data = response.json()
    missions = data.get('envelope', {}).get('missions_spawned', [])
    if not missions:
        raise Exception("No mission returned")
    
    return missions[0]['mission_id']


def approve_mission(mission_id: str) -> bool:
    """Approve a mission, return True if successful"""
    response = requests.post(f"{BASE_URL}/api/missions/{mission_id}/approve", timeout=10)
    return response.status_code == 200


def execute_mission(mission_id: str) -> bool:
    """Execute a mission, return True if successful"""
    response = requests.post(f"{BASE_URL}/api/missions/{mission_id}/execute", timeout=10)
    return response.status_code == 200


def print_header(text):
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)


def print_test(name: str, result: bool):
    status = "[PASS]" if result else "[FAIL]"
    print(f"{status} {name}")
    return result


# ============================================================================
# INVARIANT 1: Proposed Missions Do Not Execute
# ============================================================================

def test_proposed_no_execution():
    """
    Create mission via chat.
    DO NOT approve.
    Verify no execution occurs.
    """
    print_header("INVARIANT 1: Proposed Missions Do Not Execute")
    
    # Create mission
    print("\n[Step 1] Creating mission (proposed state)...")
    mission_id = create_mission("Calculate the sum of 100 and 50")
    print(f"  Mission ID: {mission_id}")
    
    # Get records before attempted execution
    print("\n[Step 2] Checking records (before any execution attempt)...")
    records_before = get_mission_records(mission_id)
    print(f"  Records: {len(records_before)}")
    for i, rec in enumerate(records_before):
        print(f"    Record {i+1}: event_type={rec.get('event_type')}, status={rec.get('status')}")
    
    # Try to execute without approval (this should fail)
    print("\n[Step 3] Attempting to execute (without approval - should fail)...")
    response = requests.post(f"{BASE_URL}/api/missions/{mission_id}/execute", timeout=10)
    print(f"  HTTP Status: {response.status_code}")
    if response.status_code == 200:
        print(f"  ERROR: Execution succeeded when it should have failed!")
        return False
    else:
        print(f"  Expected: Execution rejected")
        error_msg = response.json().get('message', '')
        print(f"  Reason: {error_msg}")
    
    # Get records after
    print("\n[Step 4] Checking records (after rejection)...")
    records_after = get_mission_records(mission_id)
    print(f"  Records: {len(records_after)}")
    
    # Verify invariant
    print("\n[Invariant Check]")
    checks = []
    
    # Check 1: No execution record
    has_executed_record = any(r.get('event_type') == 'mission_executed' for r in records_after)
    check1 = not has_executed_record
    checks.append(print_test("No execution record written", check1))
    
    # Check 2: Status is still proposed
    statuses = [r.get('status') for r in records_after]
    check2 = 'proposed' in statuses and 'completed' not in statuses and 'failed' not in statuses
    checks.append(print_test("Status is still 'proposed'", check2))
    
    # Check 3: Same number of records
    check3 = len(records_before) == len(records_after)
    checks.append(print_test("No new records written", check3))
    
    return all(checks)


# ============================================================================
# INVARIANT 2: Approved Missions Execute Exactly Once
# ============================================================================

def test_approved_single_execution():
    """
    Create mission via chat.
    Approve mission.
    Execute mission.
    Verify exactly ONE execution record is written.
    """
    print_header("INVARIANT 2: Approved Missions Execute Exactly Once")
    
    # Create mission
    print("\n[Step 1] Creating mission...")
    mission_id = create_mission("Extract customer information from linkedin.com")
    print(f"  Mission ID: {mission_id}")
    
    # Get records after creation
    print("\n[Step 2] Records after creation...")
    records_created = get_mission_records(mission_id)
    print(f"  Records: {len(records_created)}")
    for i, rec in enumerate(records_created):
        print(f"    Record {i+1}: event_type={rec.get('event_type')}, status={rec.get('status')}")
    
    # Approve
    print("\n[Step 3] Approving mission...")
    approve_result = approve_mission(mission_id)
    print(f"  Approval succeeded: {approve_result}")
    
    # Get records after approval
    print("\n[Step 4] Records after approval...")
    records_approved = get_mission_records(mission_id)
    print(f"  Records: {len(records_approved)}")
    for i, rec in enumerate(records_approved):
        print(f"    Record {i+1}: event_type={rec.get('event_type')}, status={rec.get('status')}")
    
    # Execute
    print("\n[Step 5] Executing mission...")
    exec_result = execute_mission(mission_id)
    print(f"  Execution succeeded: {exec_result}")
    
    # Get records after execution
    print("\n[Step 6] Records after execution...")
    records_executed = get_mission_records(mission_id)
    print(f"  Records: {len(records_executed)}")
    for i, rec in enumerate(records_executed):
        event = rec.get('event_type', 'N/A')
        status = rec.get('status', 'N/A')
        tool = rec.get('tool_used', '')
        print(f"    Record {i+1}: event_type={event}, status={status}, tool={tool}")
    
    # Verify invariant
    print("\n[Invariant Check]")
    checks = []
    
    # Check 1: Execution record exists
    executed_records = [r for r in records_executed if r.get('event_type') == 'mission_executed']
    check1 = len(executed_records) == 1
    checks.append(print_test("Exactly ONE execution record", check1))
    
    # Check 2: Status is completed or failed
    if executed_records:
        exec_status = executed_records[0].get('status')
        check2 = exec_status in ['completed', 'failed']
        checks.append(print_test(f"Execution status is '{exec_status}'", check2))
    else:
        checks.append(print_test("Execution status is valid", False))
    
    # Check 3: Tool was selected
    if executed_records:
        tool_used = executed_records[0].get('tool_used')
        check3 = tool_used is not None and tool_used != ''
        checks.append(print_test(f"Tool was selected: {tool_used}", check3))
    else:
        checks.append(print_test("Tool was selected", False))
    
    # Check 4: Approval record exists
    approval_records = [r for r in records_executed if r.get('event_type') == 'mission_status_update' and r.get('status') == 'approved']
    check4 = len(approval_records) >= 1
    checks.append(print_test("Approval record exists", check4))
    
    return all(checks)


# ============================================================================
# INVARIANT 3: Execution Does Not Re-Run
# ============================================================================

def test_no_reexecution():
    """
    Create and approve mission.
    Execute once.
    Attempt to execute again.
    Verify NO new execution record is written.
    """
    print_header("INVARIANT 3: Execution Does Not Re-Run")
    
    # Create and approve
    print("\n[Step 1] Creating and approving mission...")
    mission_id = create_mission("What is 42 * 2?")
    print(f"  Mission ID: {mission_id}")
    approve_mission(mission_id)
    print(f"  Mission approved")
    
    # Execute first time
    print("\n[Step 2] First execution...")
    result1 = execute_mission(mission_id)
    print(f"  Execution 1 succeeded: {result1}")
    
    # Get records after first execution
    records_after_1 = get_mission_records(mission_id)
    executed_count_1 = len([r for r in records_after_1 if r.get('event_type') == 'mission_executed'])
    print(f"  Execution records after run 1: {executed_count_1}")
    
    # Wait a moment
    time.sleep(1)
    
    # Attempt second execution
    print("\n[Step 3] Attempting second execution...")
    response = requests.post(f"{BASE_URL}/api/missions/{mission_id}/execute", timeout=10)
    result2 = response.status_code == 200
    print(f"  Execution 2 returned HTTP {response.status_code}")
    
    # Get records after second attempt
    records_after_2 = get_mission_records(mission_id)
    executed_count_2 = len([r for r in records_after_2 if r.get('event_type') == 'mission_executed'])
    print(f"  Execution records after run 2 attempt: {executed_count_2}")
    
    # Verify invariant
    print("\n[Invariant Check]")
    checks = []
    
    # Check 1: Only one execution record total
    check1 = executed_count_2 == 1
    checks.append(print_test("Only ONE execution record (not two)", check1))
    
    # Check 2: Second execution was rejected
    check2 = response.status_code != 200
    checks.append(print_test("Second execution was rejected (HTTP != 200)", check2))
    
    # Check 3: No new records written
    check3 = executed_count_1 == executed_count_2
    checks.append(print_test("No new records written on second attempt", check3))
    
    return all(checks)


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def main():
    print("\n" + "=" * 80)
    print("  EXECUTION INVARIANT TEST SUITE")
    print("=" * 80)
    print("Verifying approval-gated execution with zero side effects\n")
    
    # Wait for backend
    print("Waiting for backend to be ready...")
    time.sleep(2)
    
    all_passed = True
    
    # Test 1
    try:
        result1 = test_proposed_no_execution()
        all_passed = all_passed and result1
    except Exception as e:
        print(f"\n[ERROR] Invariant 1 test crashed: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False
    
    # Test 2
    try:
        result2 = test_approved_single_execution()
        all_passed = all_passed and result2
    except Exception as e:
        print(f"\n[ERROR] Invariant 2 test crashed: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False
    
    # Test 3
    try:
        result3 = test_no_reexecution()
        all_passed = all_passed and result3
    except Exception as e:
        print(f"\n[ERROR] Invariant 3 test crashed: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False
    
    # Summary
    print_header("TEST SUITE SUMMARY")
    print(f"\nInvariant 1 (Proposed → No Execution): {'PASS' if result1 else 'FAIL'}")
    print(f"Invariant 2 (Approved → Single Execution): {'PASS' if result2 else 'FAIL'}")
    print(f"Invariant 3 (No Re-Execution): {'PASS' if result3 else 'FAIL'}")
    print()
    
    if all_passed:
        print("=" * 80)
        print("  [SUCCESS] ALL EXECUTION INVARIANTS PASSED")
        print("=" * 80)
        return 0
    else:
        print("=" * 80)
        print("  [FAILURE] SOME INVARIANTS FAILED")
        print("=" * 80)
        return 1


if __name__ == '__main__':
    exit_code = main()
    exit(exit_code)
