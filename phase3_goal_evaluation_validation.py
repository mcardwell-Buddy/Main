"""
Phase 3 Step 1 Validation: Goal Satisfaction Evaluation
Tests deterministic goal evaluation for satisfied and unsatisfied objectives.
"""

from backend.mission_control.goal_satisfaction_evaluator import GoalSatisfactionEvaluator


def test_quantitative_objective_satisfied():
    """Test: Objective with target count that IS met."""
    print("\n🧪 Test 1: Quantitative Objective SATISFIED")
    print("   Objective: 'Collect at least 5 items'")
    print("   Items: 8 collected")
    
    evaluator = GoalSatisfactionEvaluator()
    
    items = [
        {"title": "Item 1", "content": "Content 1"},
        {"title": "Item 2", "content": "Content 2"},
        {"title": "Item 3", "content": "Content 3"},
        {"title": "Item 4", "content": "Content 4"},
        {"title": "Item 5", "content": "Content 5"},
        {"title": "Item 6", "content": "Content 6"},
        {"title": "Item 7", "content": "Content 7"},
        {"title": "Item 8", "content": "Content 8"},
    ]
    
    evaluation = evaluator.evaluate(
        mission_id="test-satisfied",
        mission_objective="Collect at least 5 items",
        items_collected=items
    )
    
    print(f"   ✓ Goal satisfied: {evaluation.goal_satisfied}")
    print(f"   ✓ Confidence: {evaluation.confidence:.2f}")
    print(f"   ✓ Evidence: {evaluation.evidence}")
    
    assert evaluation.goal_satisfied == True, "Should be satisfied"
    assert evaluation.confidence >= 0.5, "Confidence should be at least 0.5"
    print("   ✅ PASSED\n")


def test_quantitative_objective_unsatisfied():
    """Test: Objective with target count that is NOT met."""
    print("🧪 Test 2: Quantitative Objective NOT SATISFIED")
    print("   Objective: 'Collect 10 items'")
    print("   Items: 3 collected")
    
    evaluator = GoalSatisfactionEvaluator()
    
    items = [
        {"title": "Item 1", "content": "Content 1"},
        {"title": "Item 2", "content": "Content 2"},
        {"title": "Item 3", "content": "Content 3"},
    ]
    
    evaluation = evaluator.evaluate(
        mission_id="test-unsatisfied",
        mission_objective="Collect 10 items",
        items_collected=items
    )
    
    print(f"   ✓ Goal satisfied: {evaluation.goal_satisfied}")
    print(f"   ✓ Confidence: {evaluation.confidence:.2f}")
    print(f"   ✓ Gap reason: {evaluation.gap_reason}")
    print(f"   ✓ Evidence: {evaluation.evidence}")
    
    assert evaluation.goal_satisfied == False, "Should NOT be satisfied"
    assert evaluation.gap_reason is not None, "Should have gap reason"
    print("   ✅ PASSED\n")


def test_qualitative_objective_satisfied():
    """Test: Qualitative objective (keyword-based) that IS satisfied."""
    print("🧪 Test 3: Qualitative Objective SATISFIED")
    print("   Objective: 'Find quotes by famous authors'")
    print("   Items: 4 items with 'quotes' and 'authors' keywords")
    
    evaluator = GoalSatisfactionEvaluator()
    
    items = [
        {"title": "Famous Quote", "content": "A wise quote by renowned authors"},
        {"title": "Author Interview", "content": "Discussion with famous authors"},
        {"title": "Literary Works", "content": "Quotes and writings from authors"},
        {"title": "Author Collection", "content": "Curated quotes from great authors"},
    ]
    
    evaluation = evaluator.evaluate(
        mission_id="test-qualitative-satisfied",
        mission_objective="Find quotes by famous authors",
        items_collected=items
    )
    
    print(f"   ✓ Goal satisfied: {evaluation.goal_satisfied}")
    print(f"   ✓ Confidence: {evaluation.confidence:.2f}")
    print(f"   ✓ Evidence: {evaluation.evidence}")
    
    assert evaluation.goal_satisfied == True, "Should be satisfied"
    print("   ✅ PASSED\n")


def test_qualitative_objective_unsatisfied():
    """Test: Qualitative objective (keyword-based) that is NOT satisfied."""
    print("🧪 Test 4: Qualitative Objective NOT SATISFIED")
    print("   Objective: 'Find technical documentation and API references'")
    print("   Items: 3 items without required keywords")
    
    evaluator = GoalSatisfactionEvaluator()
    
    items = [
        {"title": "Blog Post", "content": "A general blog post about web development"},
        {"title": "News Article", "content": "Technology news from today"},
        {"title": "Tutorial", "content": "How to build websites"},
    ]
    
    evaluation = evaluator.evaluate(
        mission_id="test-qualitative-unsatisfied",
        mission_objective="Find technical documentation and API references",
        items_collected=items
    )
    
    print(f"   ✓ Goal satisfied: {evaluation.goal_satisfied}")
    print(f"   ✓ Confidence: {evaluation.confidence:.2f}")
    print(f"   ✓ Gap reason: {evaluation.gap_reason}")
    print(f"   ✓ Evidence: {evaluation.evidence}")
    
    assert evaluation.goal_satisfied == False, "Should NOT be satisfied"
    print("   ✅ PASSED\n")


def test_zero_items():
    """Test: No items collected."""
    print("🧪 Test 5: Zero Items Collected")
    print("   Objective: 'Collect at least 5 items'")
    print("   Items: 0 collected")
    
    evaluator = GoalSatisfactionEvaluator()
    
    evaluation = evaluator.evaluate(
        mission_id="test-zero-items",
        mission_objective="Collect at least 5 items",
        items_collected=[]
    )
    
    print(f"   ✓ Goal satisfied: {evaluation.goal_satisfied}")
    print(f"   ✓ Confidence: {evaluation.confidence:.2f}")
    print(f"   ✓ Gap reason: {evaluation.gap_reason}")
    
    assert evaluation.goal_satisfied == False, "Should NOT be satisfied"
    assert evaluation.confidence == 0.0, "Confidence should be 0"
    print("   ✅ PASSED\n")


def test_generic_objective():
    """Test: Generic objective (no specific targets)."""
    print("🧪 Test 6: Generic Objective")
    print("   Objective: 'Browse and extract data'")
    print("   Items: 3 items collected")
    
    evaluator = GoalSatisfactionEvaluator()
    
    items = [
        {"title": "Item 1", "content": "Content 1"},
        {"title": "Item 2", "content": "Content 2"},
        {"title": "Item 3", "content": "Content 3"},
    ]
    
    evaluation = evaluator.evaluate(
        mission_id="test-generic",
        mission_objective="Browse and extract data",
        items_collected=items
    )
    
    print(f"   ✓ Goal satisfied: {evaluation.goal_satisfied}")
    print(f"   ✓ Confidence: {evaluation.confidence:.2f}")
    print(f"   ✓ Evidence: {evaluation.evidence}")
    
    assert evaluation.goal_satisfied == True, "Generic objectives satisfied by any items"
    assert evaluation.confidence > 0.0, "Confidence should be > 0"
    print("   ✅ PASSED\n")


def test_signal_generation():
    """Test: Signal generation for persistence."""
    print("🧪 Test 7: Signal Generation")
    
    evaluator = GoalSatisfactionEvaluator()
    
    items = [{"title": "Item 1", "content": "Content"}]
    
    evaluation = evaluator.evaluate(
        mission_id="test-signal",
        mission_objective="Collect items",
        items_collected=items
    )
    
    signal = evaluation.to_signal()
    
    print(f"   ✓ Signal type: {signal['signal_type']}")
    print(f"   ✓ Signal layer: {signal['signal_layer']}")
    print(f"   ✓ Signal source: {signal['signal_source']}")
    print(f"   ✓ Mission ID: {signal['mission_id']}")
    print(f"   ✓ Goal satisfied: {signal['goal_satisfied']}")
    print(f"   ✓ Timestamp: {signal['timestamp'][:10]}...")
    
    assert signal["signal_type"] == "goal_evaluation"
    assert signal["signal_layer"] == "mission"
    assert signal["signal_source"] == "goal_evaluator"
    assert signal["mission_id"] == "test-signal"
    print("   ✅ PASSED\n")


def main():
    """Run all validation tests."""
    print("\n" + "="*60)
    print("PHASE 3 STEP 1: GOAL SATISFACTION EVALUATOR VALIDATION")
    print("="*60)
    
    try:
        test_quantitative_objective_satisfied()
        test_quantitative_objective_unsatisfied()
        test_qualitative_objective_satisfied()
        test_qualitative_objective_unsatisfied()
        test_zero_items()
        test_generic_objective()
        test_signal_generation()
        
        print("="*60)
        print("✅ ALL VALIDATION TESTS PASSED")
        print("="*60)
        print("\n📊 Summary:")
        print("   ✓ Quantitative evaluation works (count-based)")
        print("   ✓ Qualitative evaluation works (keyword-based)")
        print("   ✓ Edge cases handled (zero items, generic)")
        print("   ✓ Signals properly formatted for logging")
        print("   ✓ No execution changes (read-only evaluator)")
        print("   ✓ Deterministic results (no LLM, no randomness)")
        
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
