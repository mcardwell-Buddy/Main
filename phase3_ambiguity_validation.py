"""
Ambiguity Evaluator Validation Tests
Tests deterministic ambiguity detection rules.
"""

from backend.mission_control.ambiguity_evaluator import AmbiguityEvaluator


def test_clear_outcome_high_confidence():
    """Test 1: Clear outcome - high confidence, goal satisfied."""
    print("\n🧪 Test 1: Clear Outcome - High Confidence")
    
    evaluator = AmbiguityEvaluator(
        goal_confidence_threshold=0.6,
        opportunity_confidence_threshold=0.65,
        evidence_minimum_items=3
    )
    
    goal_evaluation = {
        "goal_satisfied": True,
        "confidence": 0.95,
        "evidence": ["10 items collected", "All keywords found"],
        "gap_reason": None
    }
    
    opportunity_summary = {
        "opportunities_created": 8,
        "opportunity_types": {"directory": 5, "job": 3},
        "avg_confidence": 0.85
    }
    
    evaluation = evaluator.evaluate(
        mission_id="test-clear-001",
        goal_evaluation=goal_evaluation,
        opportunity_summary=opportunity_summary,
        items_collected=10,
        mission_status="completed"
    )
    
    print(f"   ✓ Ambiguous: {evaluation.ambiguous}")
    print(f"   ✓ Reason: {evaluation.reason}")
    print(f"   ✓ Confidence gap: {evaluation.confidence_gap:.2f}")
    print(f"   ✓ Opportunity weakness: {evaluation.opportunity_weakness:.2f}")
    print(f"   ✓ Evidence sufficiency: {evaluation.evidence_sufficiency:.2f}")
    
    assert evaluation.ambiguous == False, "Should not be ambiguous"
    assert evaluation.reason == "clear_outcome", "Should be clear outcome"
    print("   ✅ PASSED\n")


def test_low_confidence_despite_completion():
    """Test 2: Ambiguous - low confidence despite completion."""
    print("🧪 Test 2: Ambiguous - Low Confidence Despite Completion")
    
    evaluator = AmbiguityEvaluator()
    
    goal_evaluation = {
        "goal_satisfied": False,
        "confidence": 0.45,
        "evidence": ["5 items collected", "Found 2/5 keywords"],
        "gap_reason": "partial_match"
    }
    
    opportunity_summary = {
        "opportunities_created": 5,
        "opportunity_types": {"unknown": 5},
        "avg_confidence": 0.60
    }
    
    evaluation = evaluator.evaluate(
        mission_id="test-ambig-001",
        goal_evaluation=goal_evaluation,
        opportunity_summary=opportunity_summary,
        items_collected=5,
        mission_status="completed"
    )
    
    print(f"   ✓ Ambiguous: {evaluation.ambiguous}")
    print(f"   ✓ Reason: {evaluation.reason}")
    print(f"   ✓ Recommended next: {evaluation.recommended_next_mission}")
    
    assert evaluation.ambiguous == True, "Should be ambiguous"
    assert "low_goal_confidence" in evaluation.reason, "Should mention low confidence"
    assert evaluation.recommended_next_mission is not None, "Should have recommendation"
    print("   ✅ PASSED\n")


def test_weak_opportunities():
    """Test 3: Ambiguous - many weak opportunities."""
    print("🧪 Test 3: Ambiguous - Many Weak Opportunities")
    
    evaluator = AmbiguityEvaluator()
    
    goal_evaluation = {
        "goal_satisfied": True,
        "confidence": 0.75,
        "evidence": ["10 items collected"],
        "gap_reason": None
    }
    
    opportunity_summary = {
        "opportunities_created": 8,
        "opportunity_types": {"unknown": 6, "lead": 2},
        "avg_confidence": 0.55  # Below threshold
    }
    
    evaluation = evaluator.evaluate(
        mission_id="test-ambig-002",
        goal_evaluation=goal_evaluation,
        opportunity_summary=opportunity_summary,
        items_collected=10,
        mission_status="completed"
    )
    
    print(f"   ✓ Ambiguous: {evaluation.ambiguous}")
    print(f"   ✓ Reason: {evaluation.reason}")
    print(f"   ✓ Opportunity weakness: {evaluation.opportunity_weakness:.2f}")
    print(f"   ✓ Recommended next: {evaluation.recommended_next_mission}")
    
    assert evaluation.ambiguous == True, "Should be ambiguous"
    assert "weak_opportunities" in evaluation.reason, "Should mention weak opportunities"
    assert "enrichment_mission" in evaluation.recommended_next_mission, "Should suggest enrichment"
    print("   ✅ PASSED\n")


def test_insufficient_evidence():
    """Test 4: Ambiguous - insufficient evidence collected."""
    print("🧪 Test 4: Ambiguous - Insufficient Evidence")
    
    evaluator = AmbiguityEvaluator(evidence_minimum_items=5)
    
    goal_evaluation = {
        "goal_satisfied": True,
        "confidence": 0.70,
        "evidence": ["2 items collected"],
        "gap_reason": None
    }
    
    opportunity_summary = {
        "opportunities_created": 2,
        "opportunity_types": {"directory": 2},
        "avg_confidence": 0.80
    }
    
    evaluation = evaluator.evaluate(
        mission_id="test-ambig-003",
        goal_evaluation=goal_evaluation,
        opportunity_summary=opportunity_summary,
        items_collected=2,
        mission_status="completed"
    )
    
    print(f"   ✓ Ambiguous: {evaluation.ambiguous}")
    print(f"   ✓ Reason: {evaluation.reason}")
    print(f"   ✓ Evidence sufficiency: {evaluation.evidence_sufficiency:.2f}")
    print(f"   ✓ Recommended next: {evaluation.recommended_next_mission}")
    
    assert evaluation.ambiguous == True, "Should be ambiguous"
    assert "insufficient_evidence" in evaluation.reason, "Should mention insufficient evidence"
    print("   ✅ PASSED\n")


def test_no_evidence_collected():
    """Test 5: Ambiguous - zero items collected."""
    print("🧪 Test 5: Ambiguous - No Evidence Collected")
    
    evaluator = AmbiguityEvaluator()
    
    goal_evaluation = {
        "goal_satisfied": False,
        "confidence": 0.0,
        "evidence": ["No items were collected"],
        "gap_reason": "zero_items_collected"
    }
    
    opportunity_summary = {
        "opportunities_created": 0,
        "opportunity_types": {},
        "avg_confidence": 0.0
    }
    
    evaluation = evaluator.evaluate(
        mission_id="test-ambig-004",
        goal_evaluation=goal_evaluation,
        opportunity_summary=opportunity_summary,
        items_collected=0,
        mission_status="completed"
    )
    
    print(f"   ✓ Ambiguous: {evaluation.ambiguous}")
    print(f"   ✓ Reason: {evaluation.reason}")
    print(f"   ✓ Recommended next: {evaluation.recommended_next_mission}")
    
    assert evaluation.ambiguous == True, "Should be ambiguous"
    assert "no_evidence" in evaluation.reason, "Should mention no evidence"
    assert "retry" in evaluation.recommended_next_mission, "Should suggest retry"
    print("   ✅ PASSED\n")


def test_goal_satisfied_no_opportunities():
    """Test 6: Ambiguous - goal satisfied but no opportunities identified."""
    print("🧪 Test 6: Ambiguous - Goal Satisfied But No Opportunities")
    
    evaluator = AmbiguityEvaluator()
    
    goal_evaluation = {
        "goal_satisfied": True,
        "confidence": 0.80,
        "evidence": ["10 items collected", "All keywords found"],
        "gap_reason": None
    }
    
    opportunity_summary = {
        "opportunities_created": 0,
        "opportunity_types": {},
        "avg_confidence": 0.0
    }
    
    evaluation = evaluator.evaluate(
        mission_id="test-ambig-005",
        goal_evaluation=goal_evaluation,
        opportunity_summary=opportunity_summary,
        items_collected=10,
        mission_status="completed"
    )
    
    print(f"   ✓ Ambiguous: {evaluation.ambiguous}")
    print(f"   ✓ Reason: {evaluation.reason}")
    print(f"   ✓ Recommended next: {evaluation.recommended_next_mission}")
    
    assert evaluation.ambiguous == True, "Should be ambiguous"
    assert "no_opportunities_identified" in evaluation.reason, "Should mention no opportunities"
    print("   ✅ PASSED\n")


def test_mission_failed_but_opportunities_exist():
    """Test 7: Ambiguous - mission failed but found opportunities."""
    print("🧪 Test 7: Ambiguous - Mission Failed But Opportunities Exist")
    
    evaluator = AmbiguityEvaluator()
    
    goal_evaluation = {
        "goal_satisfied": False,
        "confidence": 0.30,
        "evidence": ["3 items collected", "Failed navigation"],
        "gap_reason": "navigation_blocked"
    }
    
    opportunity_summary = {
        "opportunities_created": 3,
        "opportunity_types": {"lead": 2, "job": 1},
        "avg_confidence": 0.75
    }
    
    evaluation = evaluator.evaluate(
        mission_id="test-ambig-006",
        goal_evaluation=goal_evaluation,
        opportunity_summary=opportunity_summary,
        items_collected=3,
        mission_status="failed"
    )
    
    print(f"   ✓ Ambiguous: {evaluation.ambiguous}")
    print(f"   ✓ Reason: {evaluation.reason}")
    print(f"   ✓ Recommended next: {evaluation.recommended_next_mission}")
    
    assert evaluation.ambiguous == True, "Should be ambiguous"
    assert "failed_but_opportunities_exist" in evaluation.reason, "Should mention mixed signals"
    assert "salvage" in evaluation.recommended_next_mission, "Should suggest salvage"
    print("   ✅ PASSED\n")


def test_high_confidence_but_unsatisfied():
    """Test 8: Ambiguous - high confidence but goal unsatisfied."""
    print("🧪 Test 8: Ambiguous - High Confidence But Goal Unsatisfied")
    
    evaluator = AmbiguityEvaluator()
    
    goal_evaluation = {
        "goal_satisfied": False,
        "confidence": 0.85,
        "evidence": ["10 items collected", "Target not met"],
        "gap_reason": "target_not_reached"
    }
    
    opportunity_summary = {
        "opportunities_created": 10,
        "opportunity_types": {"directory": 8, "job": 2},
        "avg_confidence": 0.80
    }
    
    evaluation = evaluator.evaluate(
        mission_id="test-ambig-007",
        goal_evaluation=goal_evaluation,
        opportunity_summary=opportunity_summary,
        items_collected=10,
        mission_status="completed"
    )
    
    print(f"   ✓ Ambiguous: {evaluation.ambiguous}")
    print(f"   ✓ Reason: {evaluation.reason}")
    print(f"   ✓ Recommended next: {evaluation.recommended_next_mission}")
    
    assert evaluation.ambiguous == True, "Should be ambiguous"
    assert "high_confidence_but_goal_unsatisfied" in evaluation.reason, "Should mention contradiction"
    print("   ✅ PASSED\n")


def test_signal_emission():
    """Test 9: Signal emitted only when ambiguous."""
    print("🧪 Test 9: Signal Emission Logic")
    
    evaluator = AmbiguityEvaluator()
    
    # Clear outcome
    clear_eval = AmbiguityEvaluator().evaluate(
        mission_id="test-signal-001",
        goal_evaluation={"goal_satisfied": True, "confidence": 0.95},
        opportunity_summary={"opportunities_created": 5, "avg_confidence": 0.85},
        items_collected=5,
        mission_status="completed"
    )
    
    # Ambiguous outcome
    ambig_eval = AmbiguityEvaluator().evaluate(
        mission_id="test-signal-002",
        goal_evaluation={"goal_satisfied": False, "confidence": 0.40},
        opportunity_summary={"opportunities_created": 0, "avg_confidence": 0.0},
        items_collected=0,
        mission_status="completed"
    )
    
    print(f"   ✓ Clear outcome - emit signal: {evaluator.should_emit_signal(clear_eval)}")
    print(f"   ✓ Ambiguous outcome - emit signal: {evaluator.should_emit_signal(ambig_eval)}")
    
    assert evaluator.should_emit_signal(clear_eval) == False, "Should not emit for clear"
    assert evaluator.should_emit_signal(ambig_eval) == True, "Should emit for ambiguous"
    
    # Verify signal structure
    signal = ambig_eval.to_signal("test-signal-002")
    assert signal["signal_type"] == "mission_ambiguous", "Signal type should be correct"
    assert signal["signal_layer"] == "mission", "Signal layer should be mission"
    assert signal["mission_id"] == "test-signal-002", "Mission ID should be present"
    
    print(f"   ✓ Signal structure valid")
    print("   ✅ PASSED\n")


def main():
    """Run all validation tests."""
    print("\n" + "="*70)
    print("AMBIGUITY EVALUATOR VALIDATION TESTS")
    print("="*70)
    
    try:
        test_clear_outcome_high_confidence()
        test_low_confidence_despite_completion()
        test_weak_opportunities()
        test_insufficient_evidence()
        test_no_evidence_collected()
        test_goal_satisfied_no_opportunities()
        test_mission_failed_but_opportunities_exist()
        test_high_confidence_but_unsatisfied()
        test_signal_emission()
        
        print("="*70)
        print("✅ ALL VALIDATION TESTS PASSED")
        print("="*70)
        print("\n📊 Summary:")
        print("   ✓ Clear outcomes correctly identified")
        print("   ✓ Low confidence ambiguity detected")
        print("   ✓ Weak opportunities flagged")
        print("   ✓ Insufficient evidence detected")
        print("   ✓ Zero evidence handled")
        print("   ✓ Mixed signals (goal satisfied, no opportunities) detected")
        print("   ✓ Failed missions with opportunities flagged")
        print("   ✓ High confidence contradictions detected")
        print("   ✓ Signal emission logic correct")
        
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
