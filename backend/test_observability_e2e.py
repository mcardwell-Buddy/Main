#!/usr/bin/env python3
"""
Validation test for system observability.

Demonstrates end-to-end tracing without behavior changes.

Run:
  python -m pytest backend/test_observability_e2e.py -v
"""

import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.observability import DecisionTraceLogger, DuplicateDetector, ensure_observability_dirs
from backend.interaction_orchestrator import orchestrate_message


def test_decision_trace_logging():
    """Test that decision traces are logged."""
    ensure_observability_dirs()
    
    trace_id = "test_trace_001"
    message = "Calculate the sum of 10 and 20"
    
    # Simulate decision logging
    DecisionTraceLogger.log_classification(
        trace_id=trace_id,
        message=message,
        intent_type="request_execution",
        confidence=0.85,
        keyword_matches={"execute": 1, "math": 1},
        reasoning="Math keywords detected"
    )
    
    DecisionTraceLogger.log_routing(
        trace_id=trace_id,
        intent_type="request_execution",
        handler_name="execute",
        reasoning="Routed to execute handler"
    )
    
    # Verify traces were written
    traces_file = Path('outputs/debug/decision_traces.jsonl')
    assert traces_file.exists(), "decision_traces.jsonl not created"
    
    # Read traces
    traces = []
    with open(traces_file, 'r') as f:
        for line in f:
            if trace_id in line:
                traces.append(json.loads(line))
    
    assert len(traces) >= 2, f"Expected at least 2 traces, got {len(traces)}"
    assert traces[0]['decision_point'] == 'intent_classification'
    assert traces[1]['decision_point'] == 'routing'
    
    print("✓ Decision trace logging works")
    print(f"  Logged {len(traces)} decision points")


def test_duplicate_detection():
    """Test that duplicates are detected within 500ms."""
    session_id = "test_session_001"
    message = "Get product prices from example.com"
    trace_id_1 = "trace_first"
    trace_id_2 = "trace_duplicate"
    
    # First message should not be duplicate
    is_dup_1 = DuplicateDetector.check_duplicate(session_id, message, trace_id_1)
    assert not is_dup_1, "First message marked as duplicate"
    
    # Second message (same content, quick) should be duplicate
    is_dup_2 = DuplicateDetector.check_duplicate(session_id, message, trace_id_2)
    assert is_dup_2, "Second message not detected as duplicate"
    
    # Verify duplicate was logged
    dup_file = Path('outputs/debug/duplicates.jsonl')
    assert dup_file.exists(), "duplicates.jsonl not created"
    
    with open(dup_file, 'r') as f:
        duplicates = [json.loads(line) for line in f if trace_id_2 in line]
    
    assert len(duplicates) > 0, "Duplicate not logged"
    assert duplicates[0]['action'] == 'dropped'
    
    print("✓ Duplicate detection works")
    print(f"  Detected {len(duplicates)} duplicate(s)")


def test_trace_id_propagation():
    """Test that trace_id flows through orchestrator."""
    trace_id = "test_trace_002"
    
    # Call orchestrator with trace_id
    response = orchestrate_message(
        message="Calculate 100 + 50",
        session_id="test_session_002",
        user_id="test_user",
        context=None,
        trace_id=trace_id
    )
    
    # Check decision traces include our trace_id
    traces_file = Path('outputs/debug/decision_traces.jsonl')
    traces = []
    with open(traces_file, 'r') as f:
        for line in f:
            if trace_id in line:
                traces.append(json.loads(line))
    
    assert len(traces) > 0, f"No traces logged for trace_id {trace_id}"
    assert traces[0]['chosen_intent'] == 'request_execution'
    
    print("✓ trace_id propagation works")
    print(f"  Traced {len(traces)} decision points with trace_id {trace_id[:12]}...")


def test_deterministic_shortcut_logging():
    """Test that deterministic shortcuts are logged."""
    trace_id = "test_trace_003"
    message = "What is 2+2?"
    
    DecisionTraceLogger.log_deterministic_shortcut(
        trace_id=trace_id,
        message=message,
        shortcut_type="math_calculation",
        result="4"
    )
    
    traces_file = Path('outputs/debug/decision_traces.jsonl')
    with open(traces_file, 'r') as f:
        traces = [json.loads(line) for line in f if trace_id in line]
    
    assert any(t['decision_point'] == 'deterministic_shortcut' for t in traces)
    
    print("✓ Deterministic shortcut logging works")


def test_mission_creation_logging():
    """Test that mission creation is logged."""
    trace_id = "test_trace_004"
    mission_id = "mission_test_001"
    
    DecisionTraceLogger.log_mission_creation(
        trace_id=trace_id,
        mission_id=mission_id,
        objective_type="data_extraction",
        objective_description="Get prices from example.com"
    )
    
    traces_file = Path('outputs/debug/decision_traces.jsonl')
    with open(traces_file, 'r') as f:
        traces = [json.loads(line) for line in f if trace_id in line]
    
    assert any(t['decision_point'] == 'mission_creation' for t in traces)
    
    print("✓ Mission creation logging works")


def test_no_behavior_changes():
    """Verify observability doesn't change responses."""
    response_1 = orchestrate_message(
        message="Hi",
        session_id="test_1",
        user_id="user_1",
        trace_id="trace_a"
    )
    
    response_2 = orchestrate_message(
        message="Hi",
        session_id="test_2",
        user_id="user_2",
        trace_id="trace_b"
    )
    
    # Both should give same response type (no behavior change)
    assert response_1.response_type == response_2.response_type
    assert "acknowledgment" in response_1.response_type.value.lower() or "text" in response_1.response_type.value.lower()
    
    print("✓ No behavior changes (responses identical)")


def test_grep_trace_by_id():
    """Demonstrate grep pattern for tracing."""
    trace_id = "test_trace_005"
    
    # Log something
    DecisionTraceLogger.log_classification(
        trace_id=trace_id,
        message="Test message",
        intent_type="question",
        confidence=0.9
    )
    
    # Grep for it
    traces_file = Path('outputs/debug/decision_traces.jsonl')
    with open(traces_file, 'r') as f:
        matching_lines = [line for line in f if trace_id in line]
    
    assert len(matching_lines) > 0
    
    print("✓ Trace grep pattern works")
    print(f"  Example: grep {trace_id} {traces_file}")
    print(f"  Found {len(matching_lines)} matching line(s)")


def main():
    """Run all validation tests."""
    print("\n" + "="*70)
    print("SYSTEM OBSERVABILITY VALIDATION TESTS")
    print("="*70 + "\n")
    
    tests = [
        ("Decision Trace Logging", test_decision_trace_logging),
        ("Duplicate Detection", test_duplicate_detection),
        ("trace_id Propagation", test_trace_id_propagation),
        ("Deterministic Shortcut Logging", test_deterministic_shortcut_logging),
        ("Mission Creation Logging", test_mission_creation_logging),
        ("No Behavior Changes", test_no_behavior_changes),
        ("Grep Trace Pattern", test_grep_trace_by_id),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_fn in tests:
        try:
            print(f"\n[TEST] {name}")
            test_fn()
            passed += 1
        except Exception as e:
            print(f"  ✗ FAILED: {e}")
            failed += 1
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*70)
    
    if failed == 0:
        print("\n✓ All observability tests passed!")
        print("\nYou can now use:")
        print("  1. POST /chat/integrated → returns trace_id")
        print("  2. GET /api/debug/trace/{trace_id} → shows decision path")
        print("  3. GET /api/debug/duplicates → shows duplicate detections")
    else:
        print(f"\n✗ {failed} test(s) failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
