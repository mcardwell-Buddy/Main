#!/usr/bin/env python
"""
APPROVAL INVARIANT TEST

Tests the approval gate mechanism:

1. Create mission via chat → status should be "proposed"
2. Approve mission via API → status should be "approved"
3. Verify invariant: exactly 2 records (1 proposed + 1 approved)
4. Verify no execution occurred

Approval Invariant:
missions.jsonl should contain:
  - 1 record with event_type missing (mission creation)
  - 1 record with event_type="mission_status_update" and status="approved"
  - Total = 2 records per mission_id
"""

import requests
import json
import time
from pathlib import Path

def run_approval_test():
    print("\n" + "="*80)
    print("APPROVAL GATE INVARIANT TEST")
    print("="*80)
    
    # Step 1: Create mission via chat
    print("\n[STEP 1] Creating mission via chat...")
    url = 'http://127.0.0.1:8000/chat/integrated'
    payload = {
        'text': 'Extract data from approval-test.com',
        'session_id': 'approval_test_session',
        'external_user_id': 'test_user',
        'source': 'chat'
    }
    
    try:
        response = requests.post(url, json=payload, timeout=5)
        print(f"✓ HTTP {response.status_code}")
        
        if response.status_code != 200:
            print(f"✗ Expected 200, got {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        data = response.json()
        missions = data.get('envelope', {}).get('missions_spawned', [])
        if not missions:
            print("✗ No missions returned")
            return False
        
        mission_id = missions[0].get('mission_id')
        status = missions[0].get('status')
        print(f"✓ Mission ID: {mission_id}")
        print(f"✓ Returned Status: {status}")
        
        if status != 'proposed':
            print(f"✗ Expected status 'proposed', got '{status}'")
            return False
    
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    
    # Step 2: Wait a moment
    print("\n[STEP 2] Waiting for mission to be persisted...")
    time.sleep(1)
    
    # Step 3: Check missions.jsonl before approval
    print("\n[STEP 3] Checking missions.jsonl before approval...")
    missions_file = Path('outputs/phase25/missions.jsonl')
    
    before_records = []
    with open(missions_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and mission_id in line:
                try:
                    before_records.append(json.loads(line))
                except:
                    pass
    
    print(f"Records before approval: {len(before_records)}")
    for i, record in enumerate(before_records):
        print(f"  Record {i+1}: event_type={record.get('event_type', 'N/A')}, status={record.get('status', 'N/A')}")
    
    if len(before_records) != 1:
        print(f"✗ Expected 1 record before approval, found {len(before_records)}")
        return False
    
    if before_records[0].get('status') != 'proposed':
        print(f"✗ Expected status 'proposed', found '{before_records[0].get('status')}'")
        return False
    
    print("✓ Correct: 1 proposed record")
    
    # Step 4: Approve mission via API
    print("\n[STEP 4] Approving mission via API...")
    approve_url = f'http://127.0.0.1:8000/api/missions/{mission_id}/approve'
    
    try:
        response = requests.post(approve_url, timeout=5)
        print(f"✓ HTTP {response.status_code}")
        
        if response.status_code != 200:
            print(f"✗ Expected 200, got {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        result = response.json()
        print(f"✓ Result: {result.get('message')}")
        
        if result.get('current_status') != 'approved':
            print(f"✗ Expected status 'approved', got '{result.get('current_status')}'")
            return False
    
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    
    # Step 5: Wait a moment
    print("\n[STEP 5] Waiting for approval to be persisted...")
    time.sleep(1)
    
    # Step 6: Check missions.jsonl after approval
    print("\n[STEP 6] Checking missions.jsonl after approval...")
    
    after_records = []
    with open(missions_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and mission_id in line:
                try:
                    after_records.append(json.loads(line))
                except:
                    pass
    
    print(f"Records after approval: {len(after_records)}")
    for i, record in enumerate(after_records):
        print(f"  Record {i+1}: event_type={record.get('event_type', 'N/A')}, status={record.get('status', 'N/A')}")
    
    # Step 7: Verify approval invariant
    print("\n[STEP 7] Verifying approval invariant...")
    print("-" * 80)
    
    success = True
    
    # Check total record count
    if len(after_records) != 2:
        print(f"✗ Invariant FAILED: Expected 2 records, found {len(after_records)}")
        success = False
    else:
        print(f"✓ Invariant PASSED: Exactly 2 records per mission_id")
    
    # Check first record is proposed
    if after_records[0].get('status') != 'proposed':
        print(f"✗ Invariant FAILED: First record should be 'proposed', is '{after_records[0].get('status')}'")
        success = False
    else:
        print(f"✓ Invariant PASSED: First record is 'proposed'")
    
    # Check second record is approved
    if len(after_records) > 1 and after_records[1].get('status') != 'approved':
        print(f"✗ Invariant FAILED: Second record should be 'approved', is '{after_records[1].get('status')}'")
        success = False
    elif len(after_records) > 1:
        print(f"✓ Invariant PASSED: Second record is 'approved'")
    
    # Check no active/failed/executed records
    bad_statuses = ['active', 'failed']
    for i, record in enumerate(after_records):
        if record.get('status') in bad_statuses:
            print(f"✗ Invariant FAILED: Found unexpected status '{record.get('status')}' in record {i+1}")
            success = False
    
    if success:
        print(f"✓ Invariant PASSED: No execution occurred (no active/failed records)")
    
    # Step 8: Verify no execution
    print("\n[STEP 8] Verifying execution did NOT occur...")
    
    execution_records = [r for r in after_records if r.get('status') in ['active', 'failed']]
    if execution_records:
        print(f"✗ Execution verification FAILED: Found {len(execution_records)} execution records")
        success = False
    else:
        print(f"✓ Execution verification PASSED: No execution occurred")
    
    return success

if __name__ == '__main__':
    try:
        success = run_approval_test()
        print("\n" + "="*80)
        if success:
            print("✓ APPROVAL INVARIANT TEST PASSED")
            print("="*80 + "\n")
            exit(0)
        else:
            print("✗ APPROVAL INVARIANT TEST FAILED")
            print("="*80 + "\n")
            exit(1)
    except Exception as e:
        print(f"\n✗ Test error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
