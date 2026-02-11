"""
Phase 4x Step 2: Drift Detection Validation

Validates that drift detection works correctly:
1. Creates test data with simulated drift
2. Runs drift detection
3. Confirms warnings were emitted
4. Validates warning content
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from Back_End.learning.drift_detector import detect_drift, DriftDetector


def create_test_signals_with_drift(test_file: Path) -> None:
    """Create test signals demonstrating various drift patterns."""
    
    # Ensure directory exists
    test_file.parent.mkdir(parents=True, exist_ok=True)
    
    test_signals = []
    
    # Scenario 1: Selector layer with confidence decay
    # Long window: high confidence (0.8)
    test_signals.append({
        "signal_type": "temporal_trend_detected",
        "signal_layer": "temporal",
        "signal_source": "temporal_aggregator",
        "target_layer": "selector",
        "window": "long",
        "trend": "flat",
        "rolling_count": 200,
        "avg_confidence": 0.8,
        "volatility": 0.01,
        "success_rate": 0.9,
        "timestamp": "2026-02-07T10:00:00.000000+00:00"
    })
    
    # Medium window: moderate confidence (0.7)
    test_signals.append({
        "signal_type": "temporal_trend_detected",
        "signal_layer": "temporal",
        "signal_source": "temporal_aggregator",
        "target_layer": "selector",
        "window": "medium",
        "trend": "down",
        "rolling_count": 50,
        "avg_confidence": 0.7,
        "volatility": 0.02,
        "success_rate": 0.85,
        "timestamp": "2026-02-07T10:00:00.000000+00:00"
    })
    
    # Short window: LOW confidence (0.5) - 20% drop from medium, triggers warning
    test_signals.append({
        "signal_type": "temporal_trend_detected",
        "signal_layer": "temporal",
        "signal_source": "temporal_aggregator",
        "target_layer": "selector",
        "window": "short",
        "trend": "down",
        "rolling_count": 10,
        "avg_confidence": 0.5,  # 28.6% drop from medium (0.7)
        "volatility": 0.05,
        "success_rate": 0.6,  # 29.4% drop from medium
        "timestamp": "2026-02-07T10:00:00.000000+00:00"
    })
    
    # Scenario 2: Intent layer with volatility spike
    # Long window: low volatility
    test_signals.append({
        "signal_type": "temporal_trend_detected",
        "signal_layer": "temporal",
        "signal_source": "temporal_aggregator",
        "target_layer": "intent",
        "window": "long",
        "trend": "flat",
        "rolling_count": 200,
        "avg_confidence": 0.6,
        "volatility": 0.01,
        "timestamp": "2026-02-07T10:00:00.000000+00:00"
    })
    
    # Medium window: moderate volatility
    test_signals.append({
        "signal_type": "temporal_trend_detected",
        "signal_layer": "temporal",
        "signal_source": "temporal_aggregator",
        "target_layer": "intent",
        "window": "medium",
        "trend": "flat",
        "rolling_count": 50,
        "avg_confidence": 0.6,
        "volatility": 0.02,
        "timestamp": "2026-02-07T10:00:00.000000+00:00"
    })
    
    # Short window: HIGH volatility - 2.5x spike from medium
    test_signals.append({
        "signal_type": "temporal_trend_detected",
        "signal_layer": "temporal",
        "signal_source": "temporal_aggregator",
        "target_layer": "intent",
        "window": "short",
        "trend": "flat",
        "rolling_count": 10,
        "avg_confidence": 0.6,
        "volatility": 0.05,  # 2.5x spike from medium
        "timestamp": "2026-02-07T10:00:00.000000+00:00"
    })
    
    # Scenario 3: Mission layer with success rate degradation
    # Long window: high success rate
    test_signals.append({
        "signal_type": "temporal_trend_detected",
        "signal_layer": "temporal",
        "signal_source": "temporal_aggregator",
        "target_layer": "mission",
        "window": "long",
        "trend": "flat",
        "rolling_count": 200,
        "avg_confidence": 0.5,
        "volatility": None,
        "success_rate": 0.8,
        "timestamp": "2026-02-07T10:00:00.000000+00:00"
    })
    
    # Medium window: moderate success rate
    test_signals.append({
        "signal_type": "temporal_trend_detected",
        "signal_layer": "temporal",
        "signal_source": "temporal_aggregator",
        "target_layer": "mission",
        "window": "medium",
        "trend": "down",
        "rolling_count": 50,
        "avg_confidence": 0.5,
        "volatility": None,
        "success_rate": 0.75,
        "timestamp": "2026-02-07T10:00:00.000000+00:00"
    })
    
    # Short window: LOW success rate - 26.7% drop from medium
    test_signals.append({
        "signal_type": "temporal_trend_detected",
        "signal_layer": "temporal",
        "signal_source": "temporal_aggregator",
        "target_layer": "mission",
        "window": "short",
        "trend": "down",
        "rolling_count": 10,
        "avg_confidence": 0.5,
        "volatility": None,
        "success_rate": 0.55,  # 26.7% drop from medium
        "timestamp": "2026-02-07T10:00:00.000000+00:00"
    })
    
    # Write test signals
    with open(test_file, 'w', encoding='utf-8') as f:
        for signal in test_signals:
            f.write(json.dumps(signal) + '\n')
    
    print(f"Created {len(test_signals)} test signals with simulated drift")


def count_drift_warnings(signals_file: Path) -> int:
    """Count drift_warning signals in file."""
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
                if signal.get("signal_type") == "drift_warning":
                    count += 1
            except json.JSONDecodeError:
                continue
    
    return count


def get_drift_warnings(signals_file: Path) -> List[Dict]:
    """Get all drift warning signals."""
    warnings = []
    if not signals_file.exists():
        return warnings
    
    with open(signals_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                signal = json.loads(line)
                if signal.get("signal_type") == "drift_warning":
                    warnings.append(signal)
            except json.JSONDecodeError:
                continue
    
    return warnings


def validate_drift_detection():
    """Run validation checks."""
    print("Phase 4x Step 2: Drift Detection Validation")
    print("=" * 60)
    print()
    
    # Create temporary test file
    temp_dir = tempfile.mkdtemp()
    test_file = Path(temp_dir) / "test_signals.jsonl"
    
    try:
        # Create test signals with simulated drift
        print("Creating test signals with simulated drift...")
        create_test_signals_with_drift(test_file)
        print()
        
        # Count warnings before detection
        before_count = count_drift_warnings(test_file)
        print(f"Drift warnings before detection: {before_count}")
        print()
        
        # Run drift detection
        print("Running drift detection...")
        summary = detect_drift(test_file)
        print()
        
        # Display summary
        print("Detection Summary")
        print("-" * 60)
        print(f"Temporal trends loaded: {summary['temporal_trends_loaded']}")
        print()
        
        print("Trends by layer:")
        for layer, count in summary['trends_by_layer'].items():
            print(f"  {layer:15s}: {count} trends")
        print()
        
        print(f"Drift warnings detected: {summary['drift_warnings_detected']}")
        print(f"Drift warnings emitted:  {summary['drift_warnings_emitted']}")
        print()
        
        if summary['warnings_by_layer']:
            print("Warnings by layer:")
            for layer, count in summary['warnings_by_layer'].items():
                print(f"  {layer:15s}: {count} warnings")
            print()
        
        if summary['warnings_by_type']:
            print("Warnings by type:")
            for drift_type, count in summary['warnings_by_type'].items():
                print(f"  {drift_type:30s}: {count} warnings")
            print()
        
        if summary['warnings_by_severity']:
            print("Warnings by severity:")
            for severity, count in summary['warnings_by_severity'].items():
                print(f"  {severity:10s}: {count} warnings")
            print()
        
        # Count warnings after detection
        after_count = count_drift_warnings(test_file)
        new_warnings = after_count - before_count
        
        print(f"Drift warnings after detection: {after_count}")
        print(f"New drift warnings written: {new_warnings}")
        print()
        
        # Get and display actual warnings
        warnings = get_drift_warnings(test_file)
        if warnings:
            print("Drift Warnings Detected:")
            print("-" * 60)
            for i, warning in enumerate(warnings, 1):
                print(f"{i}. {warning['target_layer']} - {warning['drift_type']}")
                print(f"   Severity: {warning['severity']}")
                print(f"   Evidence:")
                for evidence in warning['evidence']:
                    print(f"     - {evidence}")
                print()
        
        # Validation checks
        print("Validation Checks")
        print("-" * 60)
        
        checks_passed = 0
        checks_total = 0
        
        # Check 1: Temporal trends loaded
        checks_total += 1
        if summary['temporal_trends_loaded'] > 0:
            print("✓ Temporal trends loaded successfully")
            checks_passed += 1
        else:
            print("✗ No temporal trends loaded")
        
        # Check 2: Drift warnings detected
        checks_total += 1
        if summary['drift_warnings_detected'] > 0:
            print("✓ Drift warnings detected")
            checks_passed += 1
        else:
            print("✗ No drift warnings detected")
        
        # Check 3: Warnings emitted
        checks_total += 1
        if summary['drift_warnings_emitted'] > 0:
            print("✓ Drift warnings emitted to signals file")
            checks_passed += 1
        else:
            print("✗ No drift warnings emitted")
        
        # Check 4: Confidence decay detected
        checks_total += 1
        if 'confidence_decay' in summary['warnings_by_type']:
            print("✓ Confidence decay detected")
            checks_passed += 1
        else:
            print("✗ Confidence decay not detected")
        
        # Check 5: Success rate degradation detected
        checks_total += 1
        if 'success_rate_degradation' in summary['warnings_by_type']:
            print("✓ Success rate degradation detected")
            checks_passed += 1
        else:
            print("✗ Success rate degradation not detected")
        
        # Check 6: Volatility spike detected
        checks_total += 1
        if 'volatility_spike' in summary['warnings_by_type']:
            print("✓ Volatility spike detected")
            checks_passed += 1
        else:
            print("✗ Volatility spike not detected")
        
        # Check 7: Multiple severity levels
        checks_total += 1
        if len(summary['warnings_by_severity']) > 0:
            print(f"✓ Severity levels assigned ({len(summary['warnings_by_severity'])} types)")
            checks_passed += 1
        else:
            print("✗ No severity levels assigned")
        
        print()
        print(f"Validation Result: {checks_passed}/{checks_total} checks passed")
        print()
        
        if checks_passed == checks_total:
            print("✓ Phase 4x Step 2 validation PASSED")
            return 0
        else:
            print("✗ Phase 4x Step 2 validation FAILED")
            return 1
    
    finally:
        # Cleanup
        if test_file.exists():
            test_file.unlink()
        Path(temp_dir).rmdir()


if __name__ == "__main__":
    exit_code = validate_drift_detection()
    sys.exit(exit_code)

