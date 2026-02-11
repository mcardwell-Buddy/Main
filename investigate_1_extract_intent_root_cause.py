#!/usr/bin/env python3
"""
INVESTIGATION 1: Extract Intent Root Cause Analysis
Goal: Understand why extract intent works now - trace the actual fix
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from Back_End.action_readiness_engine import ActionReadinessEngine, IntentCandidate

def investigate_extract_intent_fix():
    """Trace the exact flow for extract intent"""
    print("=" * 70)
    print("INVESTIGATION 1: EXTRACT INTENT ROOT CAUSE")
    print("=" * 70)
    
    # The test message that used to fail
    message = "Extract the main headline from example.com"
    message_lower = message.lower()
    
    print(f"\n1. Test message: '{message}'")
    print(f"2. Creating ActionReadinessEngine and calling validate()...")
    
    engine = ActionReadinessEngine()
    
    # Simulate what orchestrator does
    intent_candidate = IntentCandidate(intent="extract", confidence=0.95)
    
    try:
        readiness = engine.evaluate(
            user_message=message,
            intent_candidates=[intent_candidate]
        )
        
        print(f"\n3. Validation result:")
        print(f"   - Decision: {readiness.decision}")
        print(f"   - Intent: {readiness.intent}")
        print(f"   - action_object: {readiness.action_object}")
        print(f"   - action_target: {readiness.action_target}")
        print(f"   - source_url: {readiness.source_url}")
        print(f"   - missing_fields: {readiness.missing_fields}")
        
        if readiness.decision.value == "READY":
            print(f"\n✅ Readiness says READY - all fields extracted!")
            
            # This is what would be passed to _create_mission_from_readiness
            print(f"\n4. Would be passed to mission builder:")
            print(f"   intent={readiness.intent}")
            print(f"   action_object={readiness.action_object}")
            print(f"   source_url={readiness.source_url}")
            
            if readiness.action_object:
                print(f"\n✅ action_object IS PROVIDED")
                print(f"   This means the assert on line 900 will PASS")
                return True
            else:
                print(f"\n❌ action_object IS NOT PROVIDED")
                print(f"   This means the assert on line 900 will FAIL")
                print(f"   ERROR: Missing action_object for extract")
                return False
                
        else:
            print(f"\n⚠️  Readiness is {readiness.decision.value} (not READY)")
            print(f"   So mission building is blocked before the assert")
            return None
            
    except AssertionError as e:
        print(f"\n❌ AssertionError during evaluation:")
        print(f"   Error: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error:")
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    result = investigate_extract_intent_fix()
    
    if result is True:
        print("\n✅ FINDING: action_object IS being extracted - ready state will succeed")
        sys.exit(0)
    elif result is False:
        print("\n❌ FINDING: action_object NOT being extracted - would fail")
        sys.exit(1)
    else:
        print("\n⚠️  FINDING: Readiness blocked before mission builder")
        sys.exit(0)

