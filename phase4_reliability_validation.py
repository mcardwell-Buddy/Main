"""
Phase 4 Step 5: Meta-Forecasting Confidence Control Validation

Validates forecast reliability tracking:
1. Track reliability for test domains
2. Verify signal emission
3. Check suppression logic
4. Confirm deterministic behavior
"""

import json
import sys
from pathlib import Path
from typing import Dict, List

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from Back_End.learning.forecast_reliability_tracker import (
    ForecastReliabilityTracker,
    ReliabilityMetrics,
    track_forecast_reliability
)


def count_reliability_signals(signals_file: Path) -> int:
    """Count forecast_reliability_update signals."""
    if not signals_file.exists():
        return 0
    
    count = 0
    with open(signals_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                signal = json.loads(line)
                if signal.get("signal_type") == "forecast_reliability_update":
                    count += 1
            except json.JSONDecodeError:
                continue
    
    return count


def count_suppression_signals(signals_file: Path) -> int:
    """Count forecast_suppressed signals."""
    if not signals_file.exists():
        return 0
    
    count = 0
    with open(signals_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                signal = json.loads(line)
                if signal.get("signal_type") == "forecast_suppressed":
                    count += 1
            except json.JSONDecodeError:
                continue
    
    return count


def get_reliability_signals(signals_file: Path) -> List[Dict]:
    """Get all forecast_reliability_update signals."""
    if not signals_file.exists():
        return []
    
    signals = []
    with open(signals_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                signal = json.loads(line)
                if signal.get("signal_type") == "forecast_reliability_update":
                    signals.append(signal)
            except json.JSONDecodeError:
                continue
    
    return signals


def get_suppression_signals(signals_file: Path) -> List[Dict]:
    """Get all forecast_suppressed signals."""
    if not signals_file.exists():
        return []
    
    signals = []
    with open(signals_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                signal = json.loads(line)
                if signal.get("signal_type") == "forecast_suppressed":
                    signals.append(signal)
            except json.JSONDecodeError:
                continue
    
    return signals


def validate_reliability_tracking():
    """Run validation checks."""
    print("Phase 4 Step 5: Meta-Forecasting Confidence Control Validation")
    print("=" * 60)
    print()
    
    # Setup paths
    signals_file = Path(__file__).parent / "outputs" / "phase25" / "learning_signals.jsonl"
    
    if not signals_file.exists():
        print(f"✗ Signals file not found: {signals_file}")
        return 1
    
    print(f"Using signals file: {signals_file}")
    print()
    
    # Count signals before tracking
    before_reliability = count_reliability_signals(signals_file)
    before_suppression = count_suppression_signals(signals_file)
    
    print(f"Signals before tracking:")
    print(f"  Reliability updates: {before_reliability}")
    print(f"  Suppressions: {before_suppression}")
    print()
    
    # Track reliability
    domains = [
        "internal_system_health",
        "business_opportunity",
        "financial_markets",
        "environmental"
    ]
    
    print("Tracking forecast reliability...")
    tracker = ForecastReliabilityTracker(signals_file)
    results = tracker.track_all_domains(domains)
    print()
    
    # Display results
    print("Reliability Metrics")
    print("-" * 60)
    
    for domain, metrics in results.items():
        reliability = tracker.calculate_reliability_score(metrics.avg_error)
        suppressed = tracker.should_suppress_forecast(reliability, metrics.evaluation_count)
        
        print(f"{domain}:")
        print(f"  Forecasts: {metrics.forecast_count}")
        print(f"  Evaluations: {metrics.evaluation_count}")
        print(f"  Avg Error: {metrics.avg_error:.3f}")
        print(f"  Reliability: {reliability:.3f}")
        print(f"  Confidence Adjustment: {metrics.confidence_adjustment_factor:.3f}")
        print(f"  Suppressed: {'Yes' if suppressed else 'No'}")
        print()
    
    # Count signals after tracking
    after_reliability = count_reliability_signals(signals_file)
    after_suppression = count_suppression_signals(signals_file)
    
    new_reliability = after_reliability - before_reliability
    new_suppression = after_suppression - before_suppression
    
    print(f"Signals after tracking:")
    print(f"  Reliability updates: {after_reliability} (+{new_reliability})")
    print(f"  Suppressions: {after_suppression} (+{new_suppression})")
    print()
    
    # Get and display new signals
    reliability_signals = get_reliability_signals(signals_file)[-len(domains):]
    suppression_signals = get_suppression_signals(signals_file)[-new_suppression:] if new_suppression > 0 else []
    
    if reliability_signals:
        print("Reliability Update Signals:")
        print("-" * 60)
        for signal in reliability_signals:
            print(f"{signal['domain']}:")
            print(f"  Reliability: {signal['reliability_score']}")
            print(f"  Confidence Adjustment: {signal['confidence_adjustment']}")
            print(f"  Avg Error: {signal['avg_error']}")
            print()
    
    if suppression_signals:
        print("Suppression Signals:")
        print("-" * 60)
        for signal in suppression_signals:
            print(f"{signal['domain']}:")
            print(f"  Reliability: {signal['reliability_score']}")
            print(f"  Reason: {signal['reason']}")
            print()
    
    # Validation checks
    print("Validation Checks")
    print("-" * 60)
    
    checks_passed = 0
    checks_total = 0
    
    # Check 1: Domains tracked
    checks_total += 1
    if len(results) == len(domains):
        print(f"✓ All {len(domains)} domains tracked")
        checks_passed += 1
    else:
        print(f"✗ Expected {len(domains)} domains, tracked {len(results)}")
    
    # Check 2: Reliability signals emitted
    checks_total += 1
    if new_reliability >= len(domains):
        print(f"✓ Reliability signals emitted ({new_reliability})")
        checks_passed += 1
    else:
        print(f"✗ Expected at least {len(domains)} reliability signals, got {new_reliability}")
    
    # Check 3: Suppression signals emitted (at least 1)
    checks_total += 1
    if new_suppression > 0:
        print(f"✓ Suppression signals emitted ({new_suppression})")
        checks_passed += 1
    else:
        print("✗ No suppression signals emitted")
    
    # Check 4: Metrics have evaluations
    checks_total += 1
    all_have_evaluations = all(m.evaluation_count > 0 for m in results.values())
    if all_have_evaluations:
        print("✓ All domains have evaluation counts")
        checks_passed += 1
    else:
        print("✗ Some domains missing evaluations")
    
    # Check 5: Confidence adjustments calculated
    checks_total += 1
    all_have_adjustments = all(0.0 <= m.confidence_adjustment_factor <= 1.0 for m in results.values())
    if all_have_adjustments:
        print("✓ All confidence adjustments within bounds")
        checks_passed += 1
    else:
        print("✗ Some confidence adjustments out of bounds")
    
    # Check 6: financial_markets suppressed (simulated poor reliability)
    checks_total += 1
    financial_metrics = results.get("financial_markets")
    if financial_metrics:
        reliability = tracker.calculate_reliability_score(financial_metrics.avg_error)
        suppressed = tracker.should_suppress_forecast(reliability, financial_metrics.evaluation_count)
        if suppressed:
            print("✓ financial_markets correctly suppressed (poor reliability)")
            checks_passed += 1
        else:
            print("✗ financial_markets not suppressed despite poor reliability")
    else:
        print("✗ financial_markets not tracked")
    
    # Check 7: internal_system_health NOT suppressed (simulated good reliability)
    checks_total += 1
    internal_metrics = results.get("internal_system_health")
    if internal_metrics:
        reliability = tracker.calculate_reliability_score(internal_metrics.avg_error)
        suppressed = tracker.should_suppress_forecast(reliability, internal_metrics.evaluation_count)
        if not suppressed:
            print("✓ internal_system_health not suppressed (good reliability)")
            checks_passed += 1
        else:
            print("✗ internal_system_health incorrectly suppressed")
    else:
        print("✗ internal_system_health not tracked")
    
    # Check 8: Reliability store created
    checks_total += 1
    reliability_store = signals_file.parent / "forecast_reliability.json"
    if reliability_store.exists():
        print("✓ Reliability store created")
        checks_passed += 1
    else:
        print("✗ Reliability store not created")
    
    print()
    print(f"Validation Result: {checks_passed}/{checks_total} checks passed")
    print()
    
    if checks_passed == checks_total:
        print("✓ Phase 4 Step 5 validation PASSED")
        return 0
    else:
        print("✗ Phase 4 Step 5 validation FAILED")
        return 1


if __name__ == "__main__":
    exit_code = validate_reliability_tracking()
    sys.exit(exit_code)

