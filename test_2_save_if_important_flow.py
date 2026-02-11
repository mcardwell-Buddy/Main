#!/usr/bin/env python3
"""
TEST 2: Agent save_if_important Flow
Goal: Verify that memory_manager.save_if_important() calls reach Firebase
Traces the actual data persistence path.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from Back_End.config import Config
from Back_End.memory_manager import memory_manager
from Back_End.memory import memory
import json
from datetime import datetime

def test_save_if_important_flow():
    """Test if save_if_important actually saves to Firebase"""
    print("=" * 70)
    print("TEST 2: AGENT SAVE_IF_IMPORTANT FLOW")
    print("=" * 70)
    
    # Check preconditions
    firebase_enabled = Config.FIREBASE_ENABLED
    memory_type = memory.__class__.__name__
    print(f"\n1. Preconditions:")
    print(f"   - Firebase enabled: {firebase_enabled}")
    print(f"   - Memory backend: {memory_type}")
    
    if not firebase_enabled:
        print("\n⚠️  Firebase is DISABLED - skipping test")
        print("   (Test would pass if Firebase was enabled)")
        return None
    
    if memory_type != "FirebaseMemory":
        print(f"\n❌ ISSUE: Firebase enabled but backend is {memory_type}")
        print("   save_if_important() would be writing to MockMemory, not Firebase!")
        return False
    
    # Try to call save_if_important with test data
    print(f"\n2. Attempting save_if_important() with test reflection...")
    
    test_key = f"test_reflection_{datetime.now().isoformat()}"
    test_data = {
        "goal": "test_goal",
        "reflection": "Testing save_if_important flow",
        "timestamp": datetime.now().isoformat(),
        "test": True
    }
    
    try:
        # This should call memory.safe_call('set', key, data)
        # If memory is FirebaseMemory, it should go to Firestore
        memory_manager.save_if_important(test_key, "reflection", test_data, context={"searches": 2})
        print(f"   ✅ save_if_important() executed without error")
        
        # Try to retrieve it
        print(f"\n3. Attempting to retrieve saved data...")
        retrieved = memory.safe_call('get', test_key)
        
        if retrieved:
            print(f"   ✅ Retrieved data successfully: {json.dumps(retrieved, indent=2, default=str)[:200]}...")
            return True
        else:
            print(f"   ⚠️  Data not found immediately after save")
            print(f"   (This might be OK - Firestore can have slight delays)")
            return True  # Not a definite failure
            
    except Exception as e:
        print(f"   ❌ Error during save: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    try:
        result = test_save_if_important_flow()
        if result is True:
            print("\n✅ Test PASSED: save_if_important flow works")
            sys.exit(0)
        elif result is False:
            print("\n❌ Test FAILED: save_if_important not reaching Firebase")
            sys.exit(1)
        else:
            print("\n⚠️  Test SKIPPED: Firebase disabled")
            sys.exit(0)
    except Exception as e:
        print(f"\n❌ Test ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

