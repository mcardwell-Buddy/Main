#!/usr/bin/env python3
"""
Full approval flow test - verify end-to-end approval workflow
"""
import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def test_full_approval_workflow():
    print("[TEST] Full Approval Workflow")
    print("=" * 80)
    
    # Step 1: Create mission via chat
    print("\n[STEP 1] Creating mission via chat...")
    chat_payload = {
        "text": "Extract financial data from earnings reports",
        "source": "chat"
    }
    
    response = requests.post(f"{BASE_URL}/chat/integrated", json=chat_payload)
    print(f"Status: HTTP {response.status_code}")
    chat_response = response.json()
    
    # Extract mission from envelope
    missions_spawned = chat_response.get("envelope", {}).get("missions_spawned", [])
    mission_id = missions_spawned[0].get("mission_id") if missions_spawned else None
    initial_status = missions_spawned[0].get("status") if missions_spawned else None
    
    print(f"Mission ID: {mission_id}")
    print(f"Initial Status: {initial_status}")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert mission_id, "No mission_id in response"
    assert initial_status == "proposed", f"Expected 'proposed', got '{initial_status}'"
    print("✓ Mission created successfully")
    
    # Step 2: Get mission via whiteboard API (before approval)
    print("\n[STEP 2] Retrieving mission via whiteboard API (before approval)...")
    response = requests.get(f"{BASE_URL}/api/whiteboard/{mission_id}")
    print(f"Status: HTTP {response.status_code}")
    if response.status_code == 200:
        whiteboard_data = response.json().get("state", {})
        status_before = whiteboard_data.get("status")
        print(f"Whiteboard Status (before): {status_before}")
        print(f"Whiteboard Keys: {list(whiteboard_data.keys())}")
    else:
        print(f"Error: {response.text}")
        whiteboard_data = {}
    
    # Step 3: Check missions.jsonl before approval
    print("\n[STEP 3] Checking missions.jsonl before approval...")
    with open("outputs/phase25/missions.jsonl", "r") as f:
        all_records = [json.loads(line) for line in f if line.strip()]
    
    mission_records_before = [r for r in all_records if r.get("mission_id") == mission_id]
    print(f"Records before approval: {len(mission_records_before)}")
    for i, record in enumerate(mission_records_before, 1):
        print(f"  Record {i}: event_type={record.get('event_type')}, status={record.get('status')}")
    
    # Step 4: Approve the mission via API
    print("\n[STEP 4] Approving mission via API...")
    response = requests.post(f"{BASE_URL}/api/missions/{mission_id}/approve")
    print(f"Status: HTTP {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Result: {result.get('status')}")
        print(f"Current Status: {result.get('current_status')}")
        print("✓ Approval successful")
    else:
        print(f"Error: {response.text}")
        print("✗ Approval failed")
        return False
    
    # Step 5: Check missions.jsonl after approval
    print("\n[STEP 5] Checking missions.jsonl after approval...")
    with open("outputs/phase25/missions.jsonl", "r") as f:
        all_records = [json.loads(line) for line in f if line.strip()]
    
    mission_records_after = [r for r in all_records if r.get("mission_id") == mission_id]
    print(f"Records after approval: {len(mission_records_after)}")
    for i, record in enumerate(mission_records_after, 1):
        event_type = record.get('event_type', 'N/A')
        status = record.get('status', 'N/A')
        print(f"  Record {i}: event_type={event_type}, status={status}")
    
    # Step 6: Get mission via whiteboard API (after approval)
    print("\n[STEP 6] Retrieving mission via whiteboard API (after approval)...")
    response = requests.get(f"{BASE_URL}/api/whiteboard/{mission_id}")
    print(f"Status: HTTP {response.status_code}")
    if response.status_code == 200:
        whiteboard_data = response.json().get("state", {})
        status_after = whiteboard_data.get("status")
        print(f"Whiteboard Status (after): {status_after}")
        print(f"Whiteboard Keys: {list(whiteboard_data.keys())}")
        assert status_after == "approved", f"Expected 'approved', got '{status_after}'"
        print("✓ Whiteboard status updated correctly")
    else:
        print(f"Error: {response.text}")
        return False
    
    # Step 7: Verify invariants
    print("\n[STEP 7] Verifying approval invariants...")
    print(f"Invariant 1: Exactly 2 records per mission_id")
    assert len(mission_records_after) == 2, f"Expected 2 records, got {len(mission_records_after)}"
    print("✓ PASSED")
    
    print(f"Invariant 2: First record is 'proposed'")
    assert mission_records_after[0].get('status') == 'proposed', f"Expected 'proposed', got '{mission_records_after[0].get('status')}'"
    print("✓ PASSED")
    
    print(f"Invariant 3: Second record is 'approved'")
    assert mission_records_after[1].get('status') == 'approved', f"Expected 'approved', got '{mission_records_after[1].get('status')}'"
    print("✓ PASSED")
    
    print(f"Invariant 4: No execution occurred (no 'active' or 'failed' records)")
    statuses = [r.get('status') for r in mission_records_after]
    assert 'active' not in statuses, "Found 'active' record - execution occurred!"
    assert 'failed' not in statuses, "Found 'failed' record - execution failed!"
    print("✓ PASSED")
    
    print("\n" + "=" * 80)
    print("✓ FULL APPROVAL WORKFLOW TEST PASSED")
    print("=" * 80)
    return True

if __name__ == "__main__":
    try:
        success = test_full_approval_workflow()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ TEST FAILED WITH ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
