#!/usr/bin/env python3
"""
TEST 3: Extract Mission Flow
Goal: Trace where extract intent error occurs
Tests the full flow from intent classification to mission building.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.interaction_orchestrator import _shared_orchestrator

def test_extract_mission_flow():
    """Test extract intent flow to find where error occurs"""
    print("=" * 70)
    print("TEST 3: EXTRACT MISSION FLOW TRACE")
    print("=" * 70)
    
    # Test data
    user_message = "Extract the main headline from example.com"
    context = {"session_id": "test_session", "user_id": "test_user"}
    
    print(f"\n1. Input message: '{user_message}'")
    print(f"2. Context: {context}")
    
    print(f"\n3. Calling orchestrator.process_message()...")
    
    try:
        result = _shared_orchestrator.process_message(
            message=user_message,
            session_id=context["session_id"],
            user_id=context["user_id"],
            context={},
            trace_id="test_trace"
        )
        
        print(f"\n✅ Extract mission executed WITHOUT error!")
        print(f"\nResult:")
        print(f"  - Response type: {type(result).__name__}")
        
        # Handle ResponseEnvelope object
        if hasattr(result, '__dict__'):
            print(f"  - Response data: {result.__dict__}")
        else:
            print(f"  - Response: {result}")
        
        return True
        
    except AssertionError as e:
        error_msg = str(e)
        if "action_object" in error_msg.lower():
            print(f"\n❌ EXTRACT MISSION FAILED with action_object assertion!")
            print(f"   Error: {error_msg}")
            print(f"\n   Location: interaction_orchestrator.py (assertion on action_object)")
            print(f"   Cause: LLM classified as 'extract' but didn't provide action_object")
            return False
        else:
            print(f"\n❌ EXTRACT MISSION FAILED with unexpected assertion:")
            print(f"   Error: {error_msg}")
            return False
    
    except Exception as e:
        print(f"\n❌ EXTRACT MISSION FAILED with unexpected error:")
        print(f"   Error type: {type(e).__name__}")
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    try:
        result = test_extract_mission_flow()
        if result:
            print("\n✅ Test PASSED: Extract mission works")
            sys.exit(0)
        else:
            print("\n❌ Test FAILED: Extract mission has issues")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
