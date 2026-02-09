"""
Validation script for Phase 4 Step 7: Confidence Timelines

Validates that confidence timelines are built correctly from signals.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.learning.confidence_timeline_builder import (
    ConfidenceTimelineBuilder,
    render_confidence_timelines
)


def validate_timeline_ordering():
    """Validate that timeline points are ordered by timestamp."""
    print("Checking timeline point ordering...")
    
    builder = ConfidenceTimelineBuilder()
    timelines = builder.build_all_timelines()
    
    for timeline_type, timeline_list in timelines.items():
        for timeline in timeline_list:
            if not timeline.points:
                continue
            
            timestamps = [p.timestamp for p in timeline.points]
            sorted_timestamps = sorted(timestamps)
            
            if timestamps != sorted_timestamps:
                print(f"  ✗ {timeline_type} timeline {timeline.entity_id} not ordered")
                return False
    
    print("  ✓ All timeline points correctly ordered by timestamp")
    return True


def validate_delta_computation():
    """Validate that deltas are computed correctly between consecutive points."""
    print("Checking delta computation...")
    
    builder = ConfidenceTimelineBuilder()
    timelines = builder.build_all_timelines()
    
    errors = 0
    
    for timeline_type, timeline_list in timelines.items():
        for timeline in timeline_list:
            if len(timeline.points) < 2:
                continue
            
            for i in range(1, len(timeline.points)):
                expected_delta = timeline.points[i].confidence - timeline.points[i-1].confidence
                actual_delta = timeline.points[i].delta
                
                if actual_delta is not None:
                    # Allow small floating point errors
                    if abs(expected_delta - actual_delta) > 0.0001:
                        print(f"  ✗ Delta mismatch in {timeline_type} {timeline.entity_id} point {i}")
                        print(f"    Expected: {expected_delta:.4f}, Got: {actual_delta:.4f}")
                        errors += 1
    
    if errors > 0:
        print(f"  ✗ {errors} delta computation errors found")
        return False
    
    print("  ✓ All deltas computed correctly")
    return True


def validate_rolling_average():
    """Validate that rolling averages are computed correctly."""
    print("Checking rolling average computation...")
    
    builder = ConfidenceTimelineBuilder()
    timelines = builder.build_all_timelines()
    
    errors = 0
    
    for timeline_type, timeline_list in timelines.items():
        for timeline in timeline_list:
            if len(timeline.points) < 3:
                continue
            
            for i in range(2, len(timeline.points)):
                # Rolling average of last 3 points (including current)
                expected_avg = sum(p.confidence for p in timeline.points[i-2:i+1]) / 3
                actual_avg = timeline.points[i].rolling_avg
                
                if actual_avg is not None:
                    # Allow small floating point errors
                    if abs(expected_avg - actual_avg) > 0.0001:
                        print(f"  ✗ Rolling avg mismatch in {timeline_type} {timeline.entity_id} point {i}")
                        print(f"    Expected: {expected_avg:.4f}, Got: {actual_avg:.4f}")
                        errors += 1
    
    if errors > 0:
        print(f"  ✗ {errors} rolling average computation errors found")
        return False
    
    print("  ✓ All rolling averages computed correctly")
    return True


def validate_timeline_types():
    """Validate that all expected timeline types are generated."""
    print("Checking timeline type coverage...")
    
    builder = ConfidenceTimelineBuilder()
    timelines = builder.build_all_timelines()
    
    expected_types = {"selector", "intent", "opportunity", "forecast"}
    actual_types = set(timelines.keys())
    
    if expected_types != actual_types:
        print(f"  ✗ Timeline types mismatch")
        print(f"    Expected: {expected_types}")
        print(f"    Got: {actual_types}")
        return False
    
    print(f"  ✓ All {len(expected_types)} timeline types present")
    return True


def validate_entity_grouping():
    """Validate that signals are correctly grouped by entity."""
    print("Checking entity grouping...")
    
    builder = ConfidenceTimelineBuilder()
    builder.load_signals()
    
    # Check selector grouping
    selector_timelines = builder.build_selector_timelines()
    selector_entities = {t.entity_id for t in selector_timelines}
    
    # Count expected selector entities from signals
    expected_selector_entities = set()
    for signal in builder.signals:
        if signal.get("signal_type") == "selector_outcome":
            selector = signal.get("selector", "")
            selector_type = signal.get("selector_type", "")
            entity_id = f"{selector}|{selector_type}"
            expected_selector_entities.add(entity_id)
    
    if selector_entities != expected_selector_entities:
        print(f"  ✗ Selector entity grouping mismatch")
        print(f"    Expected {len(expected_selector_entities)} entities, got {len(selector_entities)}")
        return False
    
    print(f"  ✓ Entities correctly grouped (e.g., {len(selector_entities)} selector entities)")
    return True


def validate_sparkline_rendering():
    """Validate that sparklines render without errors."""
    print("Checking sparkline rendering...")
    
    builder = ConfidenceTimelineBuilder()
    timelines = builder.build_all_timelines()
    
    for timeline_type, timeline_list in timelines.items():
        for timeline in timeline_list:
            try:
                sparkline = builder.render_sparkline(timeline)
                if not sparkline:
                    print(f"  ✗ Empty sparkline for {timeline_type} {timeline.entity_id}")
                    return False
            except Exception as e:
                print(f"  ✗ Sparkline rendering error: {e}")
                return False
    
    print("  ✓ All sparklines render successfully")
    return True


def validate_whiteboard_rendering():
    """Validate that whiteboard section renders without errors."""
    print("Checking whiteboard rendering...")
    
    try:
        output = render_confidence_timelines()
        
        if not output:
            print("  ✗ Empty whiteboard output")
            return False
        
        # Check for required elements
        required_elements = [
            "CONFIDENCE TIMELINES",
            "Read-Only",
            "No Actions",
            "OBSERVATIONAL ONLY"
        ]
        
        for element in required_elements:
            if element not in output:
                print(f"  ✗ Missing required element: {element}")
                return False
        
        print("  ✓ Whiteboard section renders correctly")
        return True
        
    except Exception as e:
        print(f"  ✗ Whiteboard rendering error: {e}")
        return False


def validate_no_action_elements():
    """Validate that output contains no action-triggering elements."""
    print("Checking for action elements...")
    
    output = render_confidence_timelines()
    
    forbidden_terms = [
        "click", "execute", "trigger", "activate", 
        "run", "invoke", "start", "launch",
        "[Action]", "[Button]", "[Execute]"
    ]
    
    output_lower = output.lower()
    found_forbidden = []
    
    for term in forbidden_terms:
        if term.lower() in output_lower:
            found_forbidden.append(term)
    
    if found_forbidden:
        print(f"  ✗ Found forbidden action terms: {found_forbidden}")
        return False
    
    print("  ✓ No action elements detected")
    return True


def validate_timeline_count():
    """Validate that timelines are actually generated from signals."""
    print("Checking timeline count...")
    
    builder = ConfidenceTimelineBuilder()
    timelines = builder.build_all_timelines()
    
    total_timelines = sum(len(timeline_list) for timeline_list in timelines.values())
    
    if total_timelines == 0:
        print("  ✗ No timelines generated")
        return False
    
    print(f"  ✓ Generated {total_timelines} timelines:")
    for timeline_type, timeline_list in timelines.items():
        if timeline_list:
            print(f"    - {timeline_type}: {len(timeline_list)} timelines")
    
    return True


def main():
    """Run all validation checks."""
    print("=" * 80)
    print("Phase 4 Step 7: Confidence Timeline Validation")
    print("=" * 80)
    print()
    
    checks = [
        ("Timeline type coverage", validate_timeline_types),
        ("Timeline count", validate_timeline_count),
        ("Timeline ordering", validate_timeline_ordering),
        ("Delta computation", validate_delta_computation),
        ("Rolling average computation", validate_rolling_average),
        ("Entity grouping", validate_entity_grouping),
        ("Sparkline rendering", validate_sparkline_rendering),
        ("Whiteboard rendering", validate_whiteboard_rendering),
        ("No action elements", validate_no_action_elements),
    ]
    
    results = []
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"  ✗ Error running check: {e}")
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
        
        # Show sample output
        print("\n" + "=" * 80)
        print("SAMPLE WHITEBOARD OUTPUT")
        print("=" * 80)
        print()
        print(render_confidence_timelines())
        
        return 0
    else:
        print(f"\n✗ {total - passed} validation checks failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
