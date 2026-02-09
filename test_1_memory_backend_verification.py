#!/usr/bin/env python3
"""
TEST 1: Memory Backend Verification
Goal: Determine if memory backend is FirebaseMemory or MockMemory
This reveals if agent learning persistence is even possible.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.config import Config
from backend.memory import memory

def test_memory_backend():
    """Check what memory backend is instantiated"""
    print("=" * 70)
    print("TEST 1: MEMORY BACKEND VERIFICATION")
    print("=" * 70)
    
    # Check config
    firebase_enabled = Config.FIREBASE_ENABLED
    print(f"\n1. FIREBASE_ENABLED setting: {firebase_enabled}")
    
    # Check actual memory object
    memory_type = memory.__class__.__name__
    print(f"2. Actual memory backend instantiated: {memory_type}")
    
    # Check if it's what we expect
    if firebase_enabled and memory_type == "MockMemory":
        print("\n❌ ISSUE: Firebase is ENABLED but MockMemory is being used!")
        print("   This means agent learning is NOT persisting to Firebase.")
        return False
    elif firebase_enabled and memory_type == "FirebaseMemory":
        print("\n✅ CORRECT: Firebase ENABLED and FirebaseMemory is active")
        print("   Agent learning SHOULD be persisting to Firebase.")
        return True
    elif not firebase_enabled and memory_type == "MockMemory":
        print("\n⚠️  INFO: Firebase DISABLED and MockMemory is active (expected)")
        print("   Agent learning is NOT persisting (by design).")
        return None
    else:
        print(f"\n⚠️  UNEXPECTED: Firebase={firebase_enabled}, Backend={memory_type}")
        return None
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    try:
        result = test_memory_backend()
        if result is True:
            print("\n✅ Test PASSED: FirebaseMemory is active")
            sys.exit(0)
        elif result is False:
            print("\n❌ Test FAILED: Backend mismatch - needs investigation")
            sys.exit(1)
        else:
            print("\n⚠️  Test INFO: Firebase disabled or unexpected state")
            sys.exit(0)
    except Exception as e:
        print(f"\n❌ Test ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
