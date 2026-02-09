"""
Phase 4x Temporal Aggregation Validation

Validates that temporal signal aggregation works correctly:
1. Runs aggregation on existing signals
2. Confirms signals were written
3. Prints summary counts
"""

import json
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.learning.temporal_signal_aggregator import aggregate_temporal_signals, LEARNING_SIGNALS_FILE


def count_temporal_signals(signals_file: Path) -> int:
    """Count temporal_trend_detected signals in file."""
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
                if signal.get("signal_type") == "temporal_trend_detected":
                    count += 1
            except json.JSONDecodeError:
                continue
    
    return count


def validate_temporal_aggregation():
    """Run validation checks."""
    print("Phase 4x Step 1: Temporal Signal Aggregation Validation")
    print("=" * 60)
    print()
    
    # Count existing temporal signals before aggregation
    before_count = count_temporal_signals(LEARNING_SIGNALS_FILE)
    print(f"Temporal signals before aggregation: {before_count}")
    print()
    
    # Run aggregation
    print("Running temporal aggregation...")
    summary = aggregate_temporal_signals()
    print()
    
    # Display summary
    print("Aggregation Summary")
    print("-" * 60)
    print(f"Total signals loaded: {summary['total_signals_loaded']}")
    print()
    
    print("Signals by layer:")
    for layer, count in summary['signals_by_layer'].items():
        print(f"  {layer:15s}: {count:4d} signals")
    print()
    
    print(f"Trends detected: {summary['trends_detected']}")
    print(f"Trends emitted:  {summary['trends_emitted']}")
    print()
    
    print("Trends by target layer:")
    for layer, count in summary['trends_by_layer'].items():
        print(f"  {layer:15s}: {count:2d} trends")
    print()
    
    # Count temporal signals after aggregation
    after_count = count_temporal_signals(LEARNING_SIGNALS_FILE)
    new_signals = after_count - before_count
    
    print(f"Temporal signals after aggregation: {after_count}")
    print(f"New temporal signals written: {new_signals}")
    print()
    
    # Validation checks
    print("Validation Checks")
    print("-" * 60)
    
    checks_passed = 0
    checks_total = 0
    
    # Check 1: Signals were loaded
    checks_total += 1
    if summary['total_signals_loaded'] > 0:
        print("✓ Signals loaded successfully")
        checks_passed += 1
    else:
        print("✗ No signals loaded")
    
    # Check 2: Trends were detected
    checks_total += 1
    if summary['trends_detected'] > 0:
        print("✓ Trends detected")
        checks_passed += 1
    else:
        print("✗ No trends detected")
    
    # Check 3: Trends were emitted
    checks_total += 1
    if summary['trends_emitted'] > 0:
        print("✓ Trends emitted to signals file")
        checks_passed += 1
    else:
        print("✗ No trends emitted")
    
    # Check 4: New signals written
    checks_total += 1
    if new_signals == summary['trends_emitted']:
        print("✓ Signal count matches emitted count")
        checks_passed += 1
    else:
        print(f"✗ Signal count mismatch (expected {summary['trends_emitted']}, got {new_signals})")
    
    # Check 5: Multiple layers processed
    checks_total += 1
    if len(summary['signals_by_layer']) > 0:
        print(f"✓ Processed {len(summary['signals_by_layer'])} signal layers")
        checks_passed += 1
    else:
        print("✗ No signal layers processed")
    
    print()
    print(f"Validation Result: {checks_passed}/{checks_total} checks passed")
    print()
    
    if checks_passed == checks_total:
        print("✓ Phase 4x Step 1 validation PASSED")
        return 0
    else:
        print("✗ Phase 4x Step 1 validation FAILED")
        return 1


if __name__ == "__main__":
    exit_code = validate_temporal_aggregation()
    sys.exit(exit_code)
