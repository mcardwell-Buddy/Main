#!/usr/bin/env python3
"""
TEST 4: Action Readiness Engine Integration
Goal: Verify if ActionReadinessEngine._extract_action_object is being called
in the main flow or only in shadow/observation mode.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from Back_End.action_readiness_engine import ActionReadinessEngine
import logging

# Set up logging to see if ActionReadinessEngine is called
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("test_action_readiness")

engine = ActionReadinessEngine()

def test_action_readiness_integration():
    """Test if ActionReadinessEngine methods are called"""
    print("=" * 70)
    print("TEST 4: ACTION READINESS ENGINE INTEGRATION")
    print("=" * 70)
    
    print("\n1. Testing ActionReadinessEngine._extract_action_object() directly...")
    
    try:
        # Test data that would fail LLM extraction
        test_message = "Extract information from example.com"
        test_intent = "extract"
        
        # Call the method directly
        action_obj = engine._extract_action_object(test_message.lower(), test_intent)
        
        print(f"   ✅ _extract_action_object() returned: '{action_obj}'")
        
        if action_obj in ["information", "description"]:
            print(f"   ✅ Fallback extraction works - returns '{action_obj}'")
            result1 = True
        else:
            print(f"   ⚠️  Fallback returned: '{action_obj}'")
            result1 = None
            
    except Exception as e:
        print(f"   ❌ Error calling _extract_action_object(): {e}")
        result1 = False
    
    print("\n2. Checking if ActionReadinessEngine is called in main flow...")
    print("   (If it's only in shadow mode, this would NOT help fix extract intent error)")
    
    # Check the code to see if it's called
    try:
        with open("backend/interaction_orchestrator.py", "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        
        # Look for calls to action_readiness_engine or ActionReadinessEngine
        if "action_readiness_engine." in content or "ActionReadinessEngine" in content:
            if "shadow" in content or "observation" in content:
                print("   ⚠️  ActionReadinessEngine found but appears to be in shadow/observation mode")
                print("   (Main flow doesn't use it)")
                result2 = False
            else:
                print("   ✅ ActionReadinessEngine appears to be used in main flow")
                result2 = True
        else:
            print("   ❌ ActionReadinessEngine NOT called in interaction_orchestrator.py")
            result2 = False
            
    except Exception as e:
        print(f"   ❌ Error checking code: {e}")
        result2 = False
    
    print("\n3. Summary:")
    if result1:
        print("   ✅ ActionReadinessEngine._extract_action_object() works")
    if result2:
        print("   ✅ ActionReadinessEngine is called in main flow")
    else:
        print("   ❌ ActionReadinessEngine is NOT called in main flow (shadow mode only)")
        print("      This means our fallback code WON'T help fix the extract intent error!")
    
    print("\n" + "=" * 70)
    
    return result2

if __name__ == "__main__":
    try:
        result = test_action_readiness_integration()
        if result:
            print("\n✅ Test PASSED: ActionReadinessEngine is used in main flow")
            sys.exit(0)
        else:
            print("\n❌ Test FAILED: ActionReadinessEngine not in main flow")
            print("   (This is expected - it's in shadow mode only)")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

