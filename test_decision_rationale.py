"""
Deterministic Decision Narratives - Validation Tests
Tests decision rationale emission and signal structure.
"""

from Back_End.explainability.decision_rationale import DecisionRationaleEmitter, DecisionRationale
import json


def test_intent_action_taken_rationale():
    """Test 1: Intent action taken explanation."""
    print("\n" + "="*70)
    print("DECISION RATIONALE VALIDATION TESTS")
    print("="*70 + "\n")
    
    print("🧪 Test 1: Intent Action Taken Rationale")
    print("-" * 70)
    
    emitter = DecisionRationaleEmitter()
    
    action = {
        "text": "Next →",
        "href": "https://example.com/page/2",
        "score": 5,
        "signals": ["text_navigation_keyword", "goal_keyword_match:2"]
    }
    
    rationale = emitter.explain_intent_action_taken(
        action=action,
        goal="Find directory of companies",
        confidence=0.7,
        score=5,
        total_candidates=20,
        confidence_threshold=0.5
    )
    
    print(f"   Decision: {rationale.decision}")
    print(f"   Because:")
    for reason in rationale.because:
        print(f"     • {reason}")
    print()
    
    # Validate structure
    assert rationale.decision == "Navigate to: Next →"
    assert len(rationale.because) > 0, "Should have reasons"
    assert any("Highest ranked" in r for r in rationale.because), "Should mention ranking"
    assert any("exceeds threshold" in r for r in rationale.because), "Should mention confidence"
    assert rationale.action_type == "intent_action_taken"
    
    # Validate signal
    signal = rationale.to_signal("test-mission-001")
    print("   Signal structure:")
    print(json.dumps(signal, indent=4))
    print()
    
    assert signal["signal_type"] == "decision_rationale"
    assert signal["signal_layer"] == "explainability"
    assert signal["signal_source"] == "decision_engine"
    assert "rationale" in signal
    assert signal["rationale"]["decision"] == rationale.decision
    
    print("   ✅ PASSED\n")


def test_intent_action_blocked_rationale():
    """Test 2: Intent action blocked explanation."""
    print("🧪 Test 2: Intent Action Blocked Rationale")
    print("-" * 70)
    
    emitter = DecisionRationaleEmitter()
    
    action = {
        "text": "Login",
        "href": "https://example.com/login",
        "score": 1,
        "signals": []
    }
    
    rationale = emitter.explain_intent_action_blocked(
        action=action,
        goal="Find directory of companies",
        confidence=0.2,
        block_reason="confidence_too_low",
        confidence_threshold=0.5
    )
    
    print(f"   Decision: {rationale.decision}")
    print(f"   Because:")
    for reason in rationale.because:
        print(f"     • {reason}")
    print()
    
    assert "Blocked" in rationale.decision
    assert len(rationale.because) > 0
    assert any("below threshold" in r for r in rationale.because), "Should explain low confidence"
    assert rationale.action_type == "intent_action_blocked"
    
    print("   ✅ PASSED\n")


def test_selector_choice_ranked():
    """Test 3: Ranked selector choice explanation."""
    print("🧪 Test 3: Ranked Selector Choice Rationale")
    print("-" * 70)
    
    emitter = DecisionRationaleEmitter()
    
    rationale = emitter.explain_selector_choice(
        selector="a[rel='next']",
        selector_type="css",
        ranked=True,
        fallback_used=False,
        success_rate=0.85,
        page_number=3
    )
    
    print(f"   Decision: {rationale.decision}")
    print(f"   Because:")
    for reason in rationale.because:
        print(f"     • {reason}")
    print()
    
    assert "Execute selector" in rationale.decision
    assert len(rationale.because) > 0
    assert any("learned selector rankings" in r for r in rationale.because)
    assert any("85.0%" in r for r in rationale.because), "Should show success rate"
    assert any("page 3" in r for r in rationale.because), "Should mention page context"
    assert rationale.action_type == "selector_execution"
    
    print("   ✅ PASSED\n")


def test_selector_choice_fallback():
    """Test 4: Fallback selector choice explanation."""
    print("🧪 Test 4: Fallback Selector Choice Rationale")
    print("-" * 70)
    
    emitter = DecisionRationaleEmitter()
    
    rationale = emitter.explain_selector_choice(
        selector=".next-button",
        selector_type="css",
        ranked=False,
        fallback_used=True,
        page_number=1
    )
    
    print(f"   Decision: {rationale.decision}")
    print(f"   Because:")
    for reason in rationale.because:
        print(f"     • {reason}")
    print()
    
    assert "Execute selector" in rationale.decision
    assert any("fallback" in r for r in rationale.because), "Should mention fallback"
    assert rationale.action_type == "selector_execution"
    
    print("   ✅ PASSED\n")


def test_goal_evaluation_satisfied():
    """Test 5: Goal satisfied explanation."""
    print("🧪 Test 5: Goal Evaluation Satisfied Rationale")
    print("-" * 70)
    
    emitter = DecisionRationaleEmitter()
    
    rationale = emitter.explain_goal_evaluation_decision(
        goal_satisfied=True,
        confidence=0.85,
        items_collected=50,
        target_items=50,
        confidence_threshold=0.6
    )
    
    print(f"   Decision: {rationale.decision}")
    print(f"   Because:")
    for reason in rationale.because:
        print(f"     • {reason}")
    print()
    
    assert "Goal satisfied" in rationale.decision
    assert any("Target reached" in r for r in rationale.because)
    assert any("High confidence" in r for r in rationale.because)
    assert rationale.action_type == "goal_evaluation"
    
    print("   ✅ PASSED\n")


def test_goal_evaluation_not_satisfied():
    """Test 6: Goal not satisfied explanation."""
    print("🧪 Test 6: Goal Evaluation Not Satisfied Rationale")
    print("-" * 70)
    
    emitter = DecisionRationaleEmitter()
    
    rationale = emitter.explain_goal_evaluation_decision(
        goal_satisfied=False,
        confidence=0.3,
        items_collected=0,
        target_items=50,
        confidence_threshold=0.6
    )
    
    print(f"   Decision: {rationale.decision}")
    print(f"   Because:")
    for reason in rationale.because:
        print(f"     • {reason}")
    print()
    
    assert "Goal not satisfied" in rationale.decision
    assert any("Zero items" in r for r in rationale.because)
    assert any("Low confidence" in r for r in rationale.because)
    
    print("   ✅ PASSED\n")


def test_signal_emission_logic():
    """Test 7: Signal emission logic."""
    print("🧪 Test 7: Signal Emission Logic")
    print("-" * 70)
    
    emitter = DecisionRationaleEmitter()
    
    # Create any rationale
    rationale = emitter.explain_selector_choice(
        selector="test",
        selector_type="css",
        ranked=True,
        fallback_used=False
    )
    
    should_emit = emitter.should_emit_signal(rationale)
    print(f"   Should emit signal: {should_emit}")
    
    assert should_emit == True, "Should always emit decision rationales"
    
    print("   ✅ PASSED\n")


def test_signal_structure():
    """Test 8: Complete signal structure validation."""
    print("🧪 Test 8: Complete Signal Structure")
    print("-" * 70)
    
    emitter = DecisionRationaleEmitter()
    
    action = {
        "text": "Companies",
        "href": "https://example.com/companies",
        "score": 8,
        "signals": ["goal_keyword_match:1"]
    }
    
    rationale = emitter.explain_intent_action_taken(
        action=action,
        goal="Find companies directory",
        confidence=0.9,
        score=8,
        total_candidates=10
    )
    
    signal = rationale.to_signal("mission-123")
    
    # Validate all required fields
    required_fields = [
        "signal_type", "signal_layer", "signal_source", "mission_id",
        "action_type", "rationale", "decision_inputs", "thresholds_used",
        "timestamp"
    ]
    
    for field in required_fields:
        assert field in signal, f"Missing required field: {field}"
        print(f"   ✓ {field}: present")
    
    # Validate rationale structure
    assert "decision" in signal["rationale"]
    assert "because" in signal["rationale"]
    assert isinstance(signal["rationale"]["because"], list)
    print(f"   ✓ rationale structure: valid")
    
    # Validate values
    assert signal["signal_type"] == "decision_rationale"
    assert signal["signal_layer"] == "explainability"
    assert signal["signal_source"] == "decision_engine"
    assert signal["mission_id"] == "mission-123"
    
    print()
    print("   Complete signal:")
    print(json.dumps(signal, indent=4))
    print()
    print("   ✅ PASSED\n")


def test_deterministic_output():
    """Test 9: Deterministic output (no randomness)."""
    print("🧪 Test 9: Deterministic Output")
    print("-" * 70)
    
    emitter = DecisionRationaleEmitter()
    
    action = {
        "text": "Next",
        "href": "https://example.com/2",
        "score": 5,
        "signals": ["text_navigation_keyword"]
    }
    
    # Generate same rationale twice
    rationale1 = emitter.explain_intent_action_taken(
        action=action,
        goal="Test goal",
        confidence=0.6,
        score=5,
        total_candidates=10
    )
    
    rationale2 = emitter.explain_intent_action_taken(
        action=action,
        goal="Test goal",
        confidence=0.6,
        score=5,
        total_candidates=10
    )
    
    # Decisions should be identical
    assert rationale1.decision == rationale2.decision, "Decision should be deterministic"
    
    # Reasons should be identical (excluding timestamps)
    assert len(rationale1.because) == len(rationale2.because), "Reason count should match"
    for i, (r1, r2) in enumerate(zip(rationale1.because, rationale2.because)):
        assert r1 == r2, f"Reason {i} should match: {r1} != {r2}"
    
    print(f"   ✓ Decisions match: {rationale1.decision}")
    print(f"   ✓ Reasons match: {len(rationale1.because)} identical")
    print()
    print("   ✅ PASSED - Output is deterministic\n")


def run_all_tests():
    """Run all validation tests."""
    try:
        test_intent_action_taken_rationale()
        test_intent_action_blocked_rationale()
        test_selector_choice_ranked()
        test_selector_choice_fallback()
        test_goal_evaluation_satisfied()
        test_goal_evaluation_not_satisfied()
        test_signal_emission_logic()
        test_signal_structure()
        test_deterministic_output()
        
        print("="*70)
        print("✅ ALL VALIDATION TESTS PASSED")
        print("="*70)
        print()
        print("📊 Summary:")
        print("   ✓ Intent action taken explanations")
        print("   ✓ Intent action blocked explanations")
        print("   ✓ Ranked selector choice explanations")
        print("   ✓ Fallback selector explanations")
        print("   ✓ Goal satisfaction explanations")
        print("   ✓ Signal emission logic")
        print("   ✓ Complete signal structure")
        print("   ✓ Deterministic output (no LLM, no randomness)")
        print()
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        raise
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}\n")
        raise


if __name__ == "__main__":
    run_all_tests()

