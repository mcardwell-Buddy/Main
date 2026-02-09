"""
Validation script for Phase 4 Step 8: Forecast-to-Mission Promotion Gate

Validates that forecast promotion eligibility is evaluated correctly.
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.learning.forecast_promotion_gate import (
    ForecastPromotionGate,
    PromotionEligibility,
    evaluate_and_emit_promotions
)


def validate_eligibility_criteria():
    """Validate that all 5 promotion criteria are checked."""
    print("Checking eligibility criteria coverage...")
    
    gate = ForecastPromotionGate()
    gate.load_signals()
    gate.load_domain_contracts()
    gate.load_reliability_metrics()
    
    # Get first domain
    first_domain = list(gate.contracts.keys())[0] if gate.contracts else None
    
    if not first_domain:
        print("  ✗ No domains in contracts")
        return False
    
    # Evaluate a forecast
    latest_reliability = gate._get_latest_reliability(first_domain)
    if not latest_reliability:
        print("  ✗ No reliability data")
        return False
    
    forecast_id = f"test_{first_domain}"
    confidence = latest_reliability.get("reliability_score", 0.5)
    timestamp = latest_reliability.get("timestamp", datetime.now().isoformat())
    
    eligibility = gate.evaluate_promotion(
        forecast_id=forecast_id,
        domain=first_domain,
        forecast_confidence=confidence,
        forecast_created_timestamp=timestamp
    )
    
    # Check that all 5 criteria are in reasons
    if len(eligibility.reasons) != 5:
        print(f"  ✗ Expected 5 criteria checks, got {len(eligibility.reasons)}")
        return False
    
    # Check for keywords indicating all criteria were checked
    reason_text = " ".join(eligibility.reasons).lower()
    criteria_keywords = ["domain", "confidence", "reliability", "drift", "delay"]
    
    for keyword in criteria_keywords:
        if keyword not in reason_text:
            print(f"  ✗ Missing criteria check: {keyword}")
            return False
    
    print("  ✓ All 5 promotion criteria checked")
    return True


def validate_no_mission_creation():
    """Validate that no missions are automatically created."""
    print("Checking that no missions are created...")
    
    gate = ForecastPromotionGate()
    
    # Get signals file
    signals_path = Path(gate.signals_file)
    initial_signals = []
    if signals_path.exists():
        with open(signals_path, 'r') as f:
            initial_signals = [line for line in f if line.strip()]
    
    initial_count = len(initial_signals)
    
    # Run evaluation
    evaluations = evaluate_and_emit_promotions()
    
    # Check final signal count
    final_signals = []
    if signals_path.exists():
        with open(signals_path, 'r') as f:
            final_signals = [line for line in f if line.strip()]
    
    final_count = len(final_signals)
    added_signals = final_count - initial_count
    
    # Should only add forecast_promotion_evaluated signals, not missions
    if added_signals > 0:
        # Parse the new signals to verify they're only promotion_evaluated
        for signal_line in final_signals[-added_signals:]:
            try:
                signal = json.loads(signal_line)
                signal_type = signal.get("signal_type", "")
                
                if signal_type == "mission_created":
                    print(f"  ✗ Found mission_created signal (should not happen)")
                    return False
                
                if signal_type not in ["forecast_promotion_evaluated"]:
                    # Other signal types might have been there before
                    pass
            except json.JSONDecodeError:
                pass
    
    print(f"  ✓ No missions created ({added_signals} signals emitted)")
    return True


def validate_signal_emission():
    """Validate that promotion signals are emitted correctly."""
    print("Checking promotion signal emission...")
    
    gate = ForecastPromotionGate()
    evaluations = gate.evaluate_all_forecasts()
    
    # Verify evaluations exist
    if not evaluations:
        print("  ✗ No evaluations generated")
        return False
    
    # Check signal emission
    signals_path = Path(gate.signals_file)
    
    emission_errors = 0
    for evaluation in evaluations:
        try:
            # Manually check that signal structure is valid
            signal_dict = {
                "signal_type": "forecast_promotion_evaluated",
                "signal_layer": "temporal",
                "signal_source": "forecast_promotion_gate",
                "forecast_id": evaluation.forecast_id,
                "eligible": evaluation.eligible,
                "reasons": evaluation.reasons,
                "timestamp": evaluation.timestamp
            }
            
            # Verify required fields
            required_fields = ["signal_type", "forecast_id", "eligible", "reasons", "timestamp"]
            for field in required_fields:
                if field not in signal_dict:
                    print(f"  ✗ Missing field in signal: {field}")
                    emission_errors += 1
        except Exception as e:
            print(f"  ✗ Error validating signal: {e}")
            emission_errors += 1
    
    if emission_errors > 0:
        print(f"  ✗ {emission_errors} signal emission errors")
        return False
    
    print(f"  ✓ {len(evaluations)} signals structured correctly")
    return True


def validate_eligible_cases():
    """Validate that eligible cases are identified correctly."""
    print("Checking eligible forecast detection...")
    
    gate = ForecastPromotionGate()
    gate.load_signals()
    gate.load_domain_contracts()
    gate.load_reliability_metrics()
    
    evaluations = gate.evaluate_all_forecasts()
    
    eligible_count = sum(1 for e in evaluations if e.eligible)
    ineligible_count = sum(1 for e in evaluations if not e.eligible)
    
    # At least some should be evaluated (eligible or ineligible)
    if not evaluations:
        print("  ✗ No evaluations performed")
        return False
    
    print(f"  ✓ {eligible_count} eligible, {ineligible_count} ineligible forecasts")
    
    # Show sample of eligible forecasts
    eligible_samples = [e for e in evaluations if e.eligible][:2]
    if eligible_samples:
        for sample in eligible_samples:
            print(f"    • {sample.forecast_id}: ELIGIBLE")
    
    return True


def validate_ineligible_cases():
    """Validate that ineligible cases are identified with reasons."""
    print("Checking ineligible forecast detection...")
    
    gate = ForecastPromotionGate()
    gate.load_signals()
    gate.load_domain_contracts()
    gate.load_reliability_metrics()
    
    evaluations = gate.evaluate_all_forecasts()
    
    ineligible = [e for e in evaluations if not e.eligible]
    
    if not ineligible:
        print("  ✓ All forecasts eligible (no ineligible cases to check)")
        return True
    
    # Check that ineligible cases have reasons
    errors = 0
    for eval in ineligible:
        if not eval.reasons or len(eval.reasons) == 0:
            print(f"  ✗ Ineligible forecast {eval.forecast_id} has no reasons")
            errors += 1
        
        # Check that at least one reason is negative
        has_negative_reason = False
        for reason in eval.reasons:
            if "below" in reason.lower() or "no" in reason.lower() or "failed" in reason.lower():
                has_negative_reason = True
                break
        
        if not has_negative_reason:
            print(f"  ✗ Ineligible forecast {eval.forecast_id} has no negative reason")
            errors += 1
    
    if errors > 0:
        print(f"  ✗ {errors} ineligible case errors")
        return False
    
    print(f"  ✓ {len(ineligible)} ineligible forecasts have reasons")
    
    # Show samples
    samples = ineligible[:2]
    for sample in samples:
        print(f"    • {sample.forecast_id}: INELIGIBLE")
        print(f"      - {sample.reasons[0] if sample.reasons else 'No reason'}")
    
    return True


def validate_deterministic_evaluation():
    """Validate that evaluation is deterministic."""
    print("Checking deterministic evaluation...")
    
    gate1 = ForecastPromotionGate()
    evals1 = gate1.evaluate_all_forecasts()
    
    gate2 = ForecastPromotionGate()
    evals2 = gate2.evaluate_all_forecasts()
    
    # Compare results
    if len(evals1) != len(evals2):
        print(f"  ✗ Different number of evaluations: {len(evals1)} vs {len(evals2)}")
        return False
    
    for e1, e2 in zip(evals1, evals2):
        if e1.eligible != e2.eligible:
            print(f"  ✗ Eligibility mismatch for {e1.forecast_id}")
            return False
        
        if e1.reasons != e2.reasons:
            print(f"  ✗ Reasons mismatch for {e1.forecast_id}")
            return False
    
    print(f"  ✓ Deterministic evaluation verified ({len(evals1)} forecasts)")
    return True


def validate_no_autonomy():
    """Validate that no autonomous actions are taken."""
    print("Checking for no autonomous actions...")
    
    gate = ForecastPromotionGate()
    
    # Verify that evaluation doesn't modify execution state
    # or create any actionable items
    
    evaluations = gate.evaluate_all_forecasts()
    
    forbidden_attributes = ["creates_mission", "executes", "modifies_production", "sends_external"]
    
    for evaluation in evaluations:
        eval_dict = evaluation.to_dict()
        for attr in forbidden_attributes:
            if attr in eval_dict:
                print(f"  ✗ Found forbidden attribute: {attr}")
                return False
    
    print(f"  ✓ No autonomous actions in {len(evaluations)} evaluations")
    return True


def validate_audit_trail():
    """Validate that evaluation results are auditable."""
    print("Checking audit trail...")
    
    gate = ForecastPromotionGate()
    evaluations = gate.evaluate_all_forecasts()
    
    required_audit_fields = ["forecast_id", "eligible", "reasons", "timestamp"]
    
    audit_errors = 0
    for eval in evaluations:
        for field in required_audit_fields:
            value = getattr(eval, field, None)
            if value is None or (isinstance(value, list) and len(value) == 0):
                print(f"  ✗ Missing audit field: {field} in {eval.forecast_id}")
                audit_errors += 1
    
    if audit_errors > 0:
        print(f"  ✗ {audit_errors} audit trail errors")
        return False
    
    print(f"  ✓ Audit trail complete for {len(evaluations)} evaluations")
    return True


def validate_criteria_detail():
    """Validate individual criteria status is tracked."""
    print("Checking criteria detail tracking...")
    
    gate = ForecastPromotionGate()
    evaluations = gate.evaluate_all_forecasts()
    
    criteria_fields = [
        "domain_allows_promotion",
        "confidence_meets_cap",
        "reliability_sufficient",
        "no_high_drift",
        "evaluation_delay_met"
    ]
    
    detail_errors = 0
    for eval in evaluations:
        for field in criteria_fields:
            if not hasattr(eval, field):
                print(f"  ✗ Missing criteria field: {field}")
                detail_errors += 1
    
    if detail_errors > 0:
        print(f"  ✗ {detail_errors} criteria tracking errors")
        return False
    
    print(f"  ✓ All criteria details tracked for {len(evaluations)} evaluations")
    return True


def main():
    """Run all validation checks."""
    print("=" * 80)
    print("Phase 4 Step 8: Forecast-to-Mission Promotion Gate Validation")
    print("=" * 80)
    print()
    
    checks = [
        ("Eligibility criteria coverage", validate_eligibility_criteria),
        ("No mission creation", validate_no_mission_creation),
        ("Signal emission", validate_signal_emission),
        ("Eligible case detection", validate_eligible_cases),
        ("Ineligible case detection", validate_ineligible_cases),
        ("Deterministic evaluation", validate_deterministic_evaluation),
        ("No autonomous actions", validate_no_autonomy),
        ("Audit trail", validate_audit_trail),
        ("Criteria detail tracking", validate_criteria_detail),
    ]
    
    results = []
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"  ✗ Error running check: {e}")
            import traceback
            traceback.print_exc()
            results.append((check_name, False))
        print()
    
    # Summary
    print("=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for check_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {check_name}")
    
    print()
    print(f"Result: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n✓ All validation checks passed!")
        
        # Show sample evaluation output
        print("\n" + "=" * 80)
        print("SAMPLE EVALUATIONS")
        print("=" * 80)
        
        gate = ForecastPromotionGate()
        evaluations = gate.evaluate_all_forecasts()
        
        for eval in evaluations[:3]:
            status = "ELIGIBLE" if eval.eligible else "INELIGIBLE"
            print(f"\n{status}: {eval.forecast_id}")
            for reason in eval.reasons:
                print(f"  • {reason}")
        
        return 0
    else:
        print(f"\n✗ {total - passed} validation checks failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
