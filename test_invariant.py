#!/usr/bin/env python
"""
INVARIANT TEST: Verify that auto-execution has been stopped.

Expected behavior:
- Send one chat message
- Check missions.jsonl
- Each mission_id should appear EXACTLY once
- Status should be "proposed"
- No "active" or "failed" transitions should occur
"""

import requests
import json
import time
from pathlib import Path

def test_invariant():
    print("=" * 70)
    print("MISSION WRITE INVARIANT TEST")
    print("=" * 70)
    
    # Wait for backend
    time.sleep(2)
    
    # Step 1: Send chat message
    print("\n[STEP 1] Sending chat message...")
    url = 'http://127.0.0.1:8000/chat/integrated'
    payload = {
        'text': 'Extract data from example.com',
        'session_id': 'invariant_test_001',
        'external_user_id': 'test_user',
        'source': 'chat'
    }
    
    try:
        response = requests.post(url, json=payload, timeout=5)
        print(f"✓ HTTP {response.status_code}")
        
        if response.status_code != 200:
            print(f"✗ Expected 200, got {response.status_code}")
            return False
        
        data = response.json()
        missions = data.get('envelope', {}).get('missions_spawned', [])
        if not missions:
            print("✗ No missions returned")
            return False
        
        mission_id = missions[0].get('mission_id')
        print(f"✓ Mission ID: {mission_id}")
        print(f"✓ Returned Status: {missions[0].get('status')}")
        
    except Exception as e:
        print(f"✗ Error sending message: {e}")
        return False
    
    # Step 2: Check missions.jsonl
    print("\n[STEP 2] Checking missions.jsonl...")
    missions_file = Path('outputs/phase25/missions.jsonl')
    
    if not missions_file.exists():
        print(f"✗ File not found: {missions_file}")
        return False
    
    records = []
    with open(missions_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except:
                continue
    
    print(f"✓ Total records in missions.jsonl: {len(records)}")
    
    # Step 3: Verify invariant
    print("\n[STEP 3] Verifying invariant...")
    
    # Count records per mission_id
    from collections import defaultdict
    counts = defaultdict(int)
    statuses = defaultdict(list)
    
    for record in records:
        mid = record.get('mission_id')
        if mid == mission_id:
            counts[mid] += 1
            status = record.get('status')
            event_type = record.get('event_type')
            statuses[mid].append({
                'event_type': event_type,
                'status': status
            })
    
    print(f"\nMission: {mission_id}")
    print(f"  Record count: {counts[mission_id]}")
    print(f"  Events:")
    for event in statuses[mission_id]:
        print(f"    - {event['event_type']}: status={event['status']}")
    
    # Verify invariant
    print("\n[VERIFICATION]")
    success = True
    
    if counts[mission_id] != 1:
        print(f"✗ INVARIANT FAILED: Expected 1 record, found {counts[mission_id]}")
        success = False
    else:
        print(f"✓ INVARIANT PASSED: Exactly 1 record per mission_id")
    
    # Check status is proposed
    if statuses[mission_id]:
        final_status = statuses[mission_id][0].get('status')
        if final_status == 'proposed':
            print(f"✓ INVARIANT PASSED: Status is 'proposed'")
        else:
            print(f"✗ INVARIANT FAILED: Status is '{final_status}', expected 'proposed'")
            success = False
    
    # Check no auto-execution
    if len(statuses[mission_id]) > 1:
        print(f"✗ INVARIANT FAILED: Multiple status transitions found (auto-execution detected)")
        success = False
    else:
        print(f"✓ INVARIANT PASSED: No auto-execution (no status transitions)")
    
    return success

if __name__ == '__main__':
    success = test_invariant()
    print("\n" + "=" * 70)
    if success:
        print("✓ INVARIANT TEST PASSED")
        print("=" * 70)
        exit(0)
    else:
        print("✗ INVARIANT TEST FAILED")
        print("=" * 70)
        exit(1)

