"""
Intent Routing Diagnostic Test Suite

Tests each layer of the intent routing system to identify wiring issues.

Run: python test_intent_routing_diagnosis.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.interaction_orchestrator import (
    DeterministicIntentClassifier, 
    IntentType,
    RoutingDecision,
    InteractionOrchestrator
)
from backend.action_readiness_engine import ActionReadinessEngine, ReadinessDecision
from backend.llm_client import llm_client

# Test messages that should work
TEST_CASES = [
    {
        "message": "Navigate to https://www.cardwellassociates.com",
        "expected_intent": IntentType.REQUEST_EXECUTION,
        "expected_handler": "execute",
        "expected_readiness": ReadinessDecision.READY
    },
    {
        "message": "Extract the company phone number from https://www.cardwellassociates.com",
        "expected_intent": IntentType.REQUEST_EXECUTION,
        "expected_handler": "execute",
        "expected_readiness": ReadinessDecision.READY
    },
    {
        "message": "Get the contact information from cardwellassociates.com",
        "expected_intent": IntentType.REQUEST_EXECUTION,
        "expected_handler": "execute",
        "expected_readiness": ReadinessDecision.READY
    },
    {
        "message": "Search for python tutorials on google.com",
        "expected_intent": IntentType.REQUEST_EXECUTION,
        "expected_handler": "execute",
        "expected_readiness": ReadinessDecision.READY
    }
]

def test_llm_availability():
    """Test 1: Is LLM properly configured?"""
    print("\n" + "="*70)
    print("TEST 1: LLM Configuration")
    print("="*70)
    
    print(f"LLM Provider: {llm_client.provider}")
    print(f"LLM Enabled: {llm_client.enabled}")
    
    if llm_client.enabled:
        test_prompt = "Classify this intent: Navigate to google.com"
        result = llm_client.complete(test_prompt, max_tokens=50)
        print(f"LLM Test Response: {result}")
        print("✅ LLM is working")
    else:
        print("❌ LLM is NOT enabled")
    
    return llm_client.enabled

def test_intent_classification():
    """Test 2: Intent classification layer"""
    print("\n" + "="*70)
    print("TEST 2: Intent Classification Layer")
    print("="*70)
    
    classifier = DeterministicIntentClassifier()
    results = []
    
    for i, test in enumerate(TEST_CASES, 1):
        message = test["message"]
        expected = test["expected_intent"]
        
        print(f"\nTest {i}: {message}")
        intent = classifier.classify(message)
        
        status = "✅" if intent.intent_type == expected else "❌"
        results.append(intent.intent_type == expected)
        
        print(f"  Expected: {expected.value}")
        print(f"  Got: {intent.intent_type.value}")
        print(f"  Confidence: {intent.confidence:.2f}")
        print(f"  Actionable: {intent.actionable}")
        print(f"  Reasoning: {intent.reasoning}")
        print(f"  {status}")
    
    success_rate = sum(results) / len(results) * 100
    print(f"\n{'='*70}")
    print(f"Intent Classification Success Rate: {success_rate:.0f}%")
    return success_rate == 100

def test_routing_decision():
    """Test 3: Routing decision layer"""
    print("\n" + "="*70)
    print("TEST 3: Routing Decision Layer")
    print("="*70)
    
    classifier = DeterministicIntentClassifier()
    results = []
    
    for i, test in enumerate(TEST_CASES, 1):
        message = test["message"]
        expected_handler = test["expected_handler"]
        
        print(f"\nTest {i}: {message}")
        intent = classifier.classify(message)
        handler, kwargs = RoutingDecision.route(intent, message, context=None)
        
        status = "✅" if handler == expected_handler else "❌"
        results.append(handler == expected_handler)
        
        print(f"  Expected Handler: {expected_handler}")
        print(f"  Got Handler: {handler}")
        print(f"  {status}")
    
    success_rate = sum(results) / len(results) * 100
    print(f"\n{'='*70}")
    print(f"Routing Decision Success Rate: {success_rate:.0f}%")
    return success_rate == 100

def test_readiness_inference():
    """Test 4: Readiness intent inference"""
    print("\n" + "="*70)
    print("TEST 4: Readiness Intent Inference")
    print("="*70)
    
    orchestrator = InteractionOrchestrator()
    results = []
    
    for i, test in enumerate(TEST_CASES, 1):
        message = test["message"]
        
        print(f"\nTest {i}: {message}")
        readiness_intent = orchestrator._infer_readiness_intent(message)
        
        status = "✅" if readiness_intent else "❌"
        results.append(readiness_intent is not None)
        
        print(f"  Readiness Intent: {readiness_intent}")
        print(f"  {status}")
    
    success_rate = sum(results) / len(results) * 100
    print(f"\n{'='*70}")
    print(f"Readiness Inference Success Rate: {success_rate:.0f}%")
    return success_rate == 100

def test_action_readiness_engine():
    """Test 5: ActionReadinessEngine validation"""
    print("\n" + "="*70)
    print("TEST 5: ActionReadinessEngine Validation")
    print("="*70)
    
    engine = ActionReadinessEngine(session_context={})
    results = []
    
    # Test with explicit intent hints
    test_with_intent = [
        ("Navigate to https://www.cardwellassociates.com", "navigate"),
        ("Extract the company phone number from https://www.cardwellassociates.com", "extract"),
        ("Search for python tutorials on google.com", "search"),
    ]
    
    for i, (message, intent_hint) in enumerate(test_with_intent, 1):
        print(f"\nTest {i}: {message}")
        print(f"  Intent Hint: {intent_hint}")
        
        readiness = engine.validate(
            user_message=message,
            session_context={},
            intent=intent_hint,
            context_obj=None
        )
        
        status = "✅" if readiness.decision == ReadinessDecision.READY else "❌"
        results.append(readiness.decision == ReadinessDecision.READY)
        
        print(f"  Decision: {readiness.decision.value}")
        print(f"  Confidence: {readiness.confidence_tier.value}")
        print(f"  Missing Fields: {readiness.missing_fields}")
        if readiness.decision != ReadinessDecision.READY:
            print(f"  Clarification: {readiness.clarification_question}")
        print(f"  {status}")
    
    success_rate = sum(results) / len(results) * 100
    print(f"\n{'='*70}")
    print(f"ActionReadinessEngine Success Rate: {success_rate:.0f}%")
    return success_rate == 100

def test_end_to_end_flow():
    """Test 6: Complete end-to-end flow"""
    print("\n" + "="*70)
    print("TEST 6: End-to-End Message Processing")
    print("="*70)
    
    orchestrator = InteractionOrchestrator()
    results = []
    
    for i, test in enumerate(TEST_CASES, 1):
        message = test["message"]
        
        print(f"\nTest {i}: {message}")
        
        try:
            response = orchestrator.process_message(
                message=message,
                session_id="test_session",
                user_id="test_user",
                context=None
            )
            
            # Check if mission was created
            mission_created = len(response.missions_spawned) > 0
            is_clarification = response.response_type.value == "clarification_request"
            
            if mission_created:
                print(f"  ✅ Mission created: {response.missions_spawned[0].mission_id}")
                results.append(True)
            elif is_clarification:
                print(f"  ❌ Got clarification request instead of mission")
                print(f"  Summary: {response.summary}")
                results.append(False)
            else:
                print(f"  ❌ Unexpected response type: {response.response_type.value}")
                results.append(False)
                
        except Exception as e:
            print(f"  ❌ Exception: {e}")
            results.append(False)
    
    success_rate = sum(results) / len(results) * 100
    print(f"\n{'='*70}")
    print(f"End-to-End Success Rate: {success_rate:.0f}%")
    return success_rate == 100

def main():
    """Run all diagnostic tests"""
    print("\n" + "#"*70)
    print("#" + " "*22 + "INTENT ROUTING DIAGNOSIS" + " "*22 + "#")
    print("#"*70)
    
    test_results = {
        "LLM Configuration": test_llm_availability(),
        "Intent Classification": test_intent_classification(),
        "Routing Decision": test_routing_decision(),
        "Readiness Inference": test_readiness_inference(),
        "ActionReadinessEngine": test_action_readiness_engine(),
        "End-to-End Flow": test_end_to_end_flow()
    }
    
    print("\n" + "#"*70)
    print("DIAGNOSTIC SUMMARY")
    print("#"*70)
    
    for test_name, passed in test_results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:30} {status}")
    
    total_passed = sum(test_results.values())
    total_tests = len(test_results)
    
    print(f"\nTotal: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("\n🎉 All tests passed! Intent routing is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Review the output above to identify issues.")
        print("\nRecommended fixes:")
        
        if not test_results["LLM Configuration"]:
            print("  1. Check LLM_PROVIDER and OPENAI_API_KEY in .env")
        
        if not test_results["Intent Classification"]:
            print("  2. LLM prompt in _classify_with_llm() may need tuning")
        
        if not test_results["Routing Decision"]:
            print("  3. RoutingDecision.route() logic may need adjustment")
        
        if not test_results["Readiness Inference"]:
            print("  4. _infer_readiness_intent() keywords need expansion")
        
        if not test_results["ActionReadinessEngine"]:
            print("  5. ActionReadinessEngine validation logic may be too strict")
        
        if not test_results["End-to-End Flow"]:
            print("  6. Integration between components is broken")

if __name__ == "__main__":
    main()
