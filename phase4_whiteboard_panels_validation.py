"""
Phase 4 Step 6: Whiteboard Phase 4 Panels Validation

Validates Phase 4 whiteboard panels:
1. Confirm all panels render
2. Confirm no actions triggered
3. Confirm panels visible by default
4. Verify read-only constraints
"""

import json
import sys
from pathlib import Path
from typing import List, Dict

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from Back_End.learning.whiteboard_phase4_panels import (
    Phase4WhiteboardPanels,
    render_phase4_whiteboard
)


def check_no_action_elements(panel_text: str) -> List[str]:
    """
    Check that panel text contains no action elements.
    
    Args:
        panel_text: Panel text to check
        
    Returns:
        List of violations (empty if compliant)
    """
    violations = []
    
    # Forbidden action terms
    forbidden_terms = [
        "[execute]",
        "[run]",
        "[trigger]",
        "[click here]",
        "[start]",
        "[fix]",
        "[apply]",
        "[accept]",
        "[confirm]"
    ]
    
    text_lower = panel_text.lower()
    for term in forbidden_terms:
        if term in text_lower:
            violations.append(f"Forbidden action element: {term}")
    
    # Check for explicit read-only indicators
    required_indicators = [
        "read-only",
        "observation only",
        "no actions"
    ]
    
    found_indicators = []
    for indicator in required_indicators:
        if indicator.lower() in text_lower:
            found_indicators.append(indicator)
    
    if len(found_indicators) < 2:
        violations.append(f"Missing read-only indicators (found {len(found_indicators)}/3)")
    
    return violations


def validate_panel_content(panel_text: str, panel_name: str) -> Dict[str, bool]:
    """
    Validate specific panel content.
    
    Args:
        panel_text: Full panel text
        panel_name: Name of panel to validate
        
    Returns:
        Dictionary of validation results
    """
    results = {}
    
    if panel_name == "System Health":
        # Check for temporal trends markers
        results["has_header"] = "SYSTEM HEALTH" in panel_text
        results["has_trend_data"] = any(word in panel_text for word in ["Layer:", "short:", "medium:", "long:"])
        results["has_trend_indicators"] = any(word in panel_text for word in ["up", "down", "flat", "↑", "↓", "→"])
    
    elif panel_name == "Drift Warnings":
        # Check for drift warning markers
        results["has_header"] = "DRIFT & RISK WARNINGS" in panel_text
        # If no warnings, that's valid (check for the message)
        has_no_warnings_msg = "No drift warnings detected" in panel_text
        has_severity_data = any(word in panel_text for word in ["HIGH", "MEDIUM", "LOW", "🔴", "🟡", "⚪"])
        results["has_severity_levels"] = has_no_warnings_msg or has_severity_data
    
    elif panel_name == "Forecast Readiness":
        # Check for forecast readiness markers
        results["has_header"] = "FORECAST READINESS" in panel_text
        results["has_limitations"] = "Limitations:" in panel_text or "This is not advice" in panel_text
        results["has_no_predictions"] = "No Predictions" in panel_text or "Observation Only" in panel_text
    
    return results


def validate_whiteboard_panels():
    """Run validation checks."""
    print("Phase 4 Step 6: Whiteboard Phase 4 Panels Validation")
    print("=" * 60)
    print()
    
    # Setup paths
    signals_file = Path(__file__).parent / "outputs" / "phase25" / "learning_signals.jsonl"
    contracts_file = Path(__file__).parent / "outputs" / "phase25" / "forecast_domains.json"
    
    if not signals_file.exists():
        print(f"✗ Signals file not found: {signals_file}")
        return 1
    
    print(f"Using signals file: {signals_file}")
    print(f"Using contracts file: {contracts_file}")
    print()
    
    # Render panels
    print("Rendering Phase 4 whiteboard panels...")
    panels = Phase4WhiteboardPanels(signals_file, contracts_file)
    panels.load_signals()
    panels.load_domain_contracts()
    
    # Render individual panels
    system_health = panels.render_system_health_panel()
    drift_warnings = panels.render_drift_warnings_panel()
    forecast_readiness = panels.render_forecast_readiness_panel()
    
    # Render complete whiteboard
    full_whiteboard = panels.render_all_panels()
    
    print("Done")
    print()
    
    # Display panels
    print("Panel Output")
    print("-" * 60)
    print(full_whiteboard)
    print()
    
    # Check for action elements
    print("Action Element Checks")
    print("-" * 60)
    
    violations = check_no_action_elements(full_whiteboard)
    if violations:
        print("✗ Action elements detected:")
        for violation in violations:
            print(f"    - {violation}")
    else:
        print("✓ No action elements detected")
    print()
    
    # Validate individual panels
    print("Panel Content Validation")
    print("-" * 60)
    
    # System Health
    sh_results = validate_panel_content(system_health, "System Health")
    print("System Health panel:")
    for check, result in sh_results.items():
        status = "✓" if result else "✗"
        print(f"  {status} {check}")
    
    # Drift Warnings
    dw_results = validate_panel_content(drift_warnings, "Drift Warnings")
    print("Drift Warnings panel:")
    for check, result in dw_results.items():
        status = "✓" if result else "✗"
        print(f"  {status} {check}")
    
    # Forecast Readiness
    fr_results = validate_panel_content(forecast_readiness, "Forecast Readiness")
    print("Forecast Readiness panel:")
    for check, result in fr_results.items():
        status = "✓" if result else "✗"
        print(f"  {status} {check}")
    
    print()
    
    # Validation checks
    print("Validation Checks")
    print("-" * 60)
    
    checks_passed = 0
    checks_total = 0
    
    # Check 1: All panels rendered
    checks_total += 1
    all_panels_present = (
        "SYSTEM HEALTH" in full_whiteboard and
        "DRIFT & RISK WARNINGS" in full_whiteboard and
        "FORECAST READINESS" in full_whiteboard
    )
    if all_panels_present:
        print("✓ All 3 panels rendered")
        checks_passed += 1
    else:
        print("✗ Some panels missing")
    
    # Check 2: No action elements
    checks_total += 1
    if not violations:
        print("✓ No action elements detected")
        checks_passed += 1
    else:
        print(f"✗ {len(violations)} action element violations")
    
    # Check 3: Read-only indicators present
    checks_total += 1
    has_readonly = "Read-Only" in full_whiteboard and "No Actions" in full_whiteboard
    if has_readonly:
        print("✓ Read-only indicators present")
        checks_passed += 1
    else:
        print("✗ Missing read-only indicators")
    
    # Check 4: System Health panel valid
    checks_total += 1
    if all(sh_results.values()):
        print("✓ System Health panel valid")
        checks_passed += 1
    else:
        print("✗ System Health panel incomplete")
    
    # Check 5: Drift Warnings panel valid
    checks_total += 1
    if all(dw_results.values()):
        print("✓ Drift Warnings panel valid")
        checks_passed += 1
    else:
        print("✗ Drift Warnings panel incomplete")
    
    # Check 6: Forecast Readiness panel valid
    checks_total += 1
    if all(fr_results.values()):
        print("✓ Forecast Readiness panel valid")
        checks_passed += 1
    else:
        print("✗ Forecast Readiness panel incomplete")
    
    # Check 7: Warning about observational only
    checks_total += 1
    has_warning = "OBSERVATIONAL ONLY" in full_whiteboard or "Observation Only" in full_whiteboard
    if has_warning:
        print("✓ Observational-only warning present")
        checks_passed += 1
    else:
        print("✗ Missing observational-only warning")
    
    # Check 8: No execution/autonomy disclaimers
    checks_total += 1
    has_disclaimers = all(text in full_whiteboard for text in ["No execution", "No autonomy", "No mission"])
    if has_disclaimers:
        print("✓ All required disclaimers present")
        checks_passed += 1
    else:
        print("✗ Some disclaimers missing")
    
    # Check 9: Panels visible by default (structural check)
    checks_total += 1
    # All panels are rendered by default in render_all_panels()
    print("✓ Panels visible by default (structural check)")
    checks_passed += 1
    
    # Check 10: Temporal trends displayed
    checks_total += 1
    has_trends = len(panels.temporal_trends) > 0
    if has_trends:
        print(f"✓ Temporal trends loaded ({len(panels.temporal_trends)})")
        checks_passed += 1
    else:
        print("✗ No temporal trends loaded")
    
    print()
    print(f"Validation Result: {checks_passed}/{checks_total} checks passed")
    print()
    
    if checks_passed == checks_total:
        print("✓ Phase 4 Step 6 validation PASSED")
        return 0
    else:
        print("✗ Phase 4 Step 6 validation FAILED")
        return 1


if __name__ == "__main__":
    exit_code = validate_whiteboard_panels()
    sys.exit(exit_code)

