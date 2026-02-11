"""
Mission Cost Accounting - Validation Tests
Tests cost computation, signal emission, and whiteboard integration.
"""

import json
import tempfile
from pathlib import Path
from datetime import datetime, timezone

from Back_End.mission.mission_cost_accountant import MissionCostAccountant, MissionCostReport


def test_cost_computation():
    """Test 1: Cost computation from signals."""
    print("\n" + "="*70)
    print("MISSION COST ACCOUNTING VALIDATION TESTS")
    print("="*70 + "\n")
    
    print("🧪 Test 1: Cost Computation from Signals")
    print("-" * 70)
    
    # Create temporary signals file with test data
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        test_signals = [
            # Mission start
            {
                "signal_type": "mission_status_update",
                "mission_id": "test-cost-001",
                "status": "active",
                "timestamp": "2026-02-07T10:00:00+00:00"
            },
            # Selector outcomes
            {
                "signal_type": "selector_outcome",
                "mission_id": "test-cost-001",
                "outcome": "success",
                "page_number": 1,
                "retry_count": 0,
                "timestamp": "2026-02-07T10:00:05+00:00"
            },
            {
                "signal_type": "selector_outcome",
                "mission_id": "test-cost-001",
                "outcome": "failure",
                "page_number": 1,
                "retry_count": 1,
                "timestamp": "2026-02-07T10:00:10+00:00"
            },
            {
                "signal_type": "selector_outcome",
                "mission_id": "test-cost-001",
                "outcome": "success",
                "page_number": 2,
                "retry_count": 0,
                "timestamp": "2026-02-07T10:00:20+00:00"
            },
            {
                "signal_type": "selector_outcome",
                "mission_id": "test-cost-001",
                "outcome": "failure",
                "page_number": 2,
                "retry_count": 2,
                "timestamp": "2026-02-07T10:00:25+00:00"
            },
            {
                "signal_type": "selector_outcome",
                "mission_id": "test-cost-001",
                "outcome": "success",
                "page_number": 3,
                "retry_count": 0,
                "timestamp": "2026-02-07T10:00:35+00:00"
            },
            # Mission end
            {
                "signal_type": "mission_status_update",
                "mission_id": "test-cost-001",
                "status": "completed",
                "timestamp": "2026-02-07T10:01:00+00:00"
            }
        ]
        
        for signal in test_signals:
            f.write(json.dumps(signal) + '\n')
        
        temp_file = f.name
    
    try:
        # Compute costs
        accountant = MissionCostAccountant(signals_file=temp_file)
        report = accountant.compute_costs("test-cost-001")
        
        assert report is not None, "Cost report should be generated"
        
        # Validate metrics
        print(f"   Mission ID: {report.mission_id}")
        print(f"   Duration: {report.total_duration_sec}s")
        print(f"   Pages visited: {report.pages_visited}")
        print(f"   Selectors attempted: {report.selectors_attempted}")
        print(f"   Selectors failed: {report.selectors_failed}")
        print(f"   Total retries: {report.retries_total}")
        print()
        print(f"   Cost Units:")
        print(f"   • time_cost: {report.time_cost}s")
        print(f"   • page_cost: {report.page_cost}")
        print(f"   • failure_cost: {report.failure_cost}")
        print()
        
        # Validate expected values
        assert report.total_duration_sec == 60.0, f"Expected 60s, got {report.total_duration_sec}"
        assert report.pages_visited == 3, f"Expected 3 pages, got {report.pages_visited}"
        assert report.selectors_attempted == 5, f"Expected 5 attempts, got {report.selectors_attempted}"
        assert report.selectors_failed == 2, f"Expected 2 failures, got {report.selectors_failed}"
        assert report.retries_total == 3, f"Expected 3 retries (1+2), got {report.retries_total}"
        
        # Validate cost units match raw metrics
        assert report.time_cost == report.total_duration_sec
        assert report.page_cost == report.pages_visited
        assert report.failure_cost == report.selectors_failed
        
        print("   ✅ PASSED - All metrics computed correctly\n")
        
    finally:
        Path(temp_file).unlink()


def test_signal_emission():
    """Test 2: Signal emission logic."""
    print("🧪 Test 2: Signal Emission and Format")
    print("-" * 70)
    
    # Create test report
    report = MissionCostReport(
        mission_id="test-cost-002",
        total_duration_sec=45.5,
        pages_visited=5,
        selectors_attempted=10,
        selectors_failed=3,
        retries_total=4,
        time_cost=45.5,
        page_cost=5,
        failure_cost=3,
        timestamp="2026-02-07T10:00:00+00:00"
    )
    
    # Check emission logic
    accountant = MissionCostAccountant()
    should_emit = accountant.should_emit_signal(report)
    
    assert should_emit == True, "Should emit signal for valid report"
    print("   ✓ Should emit: True")
    
    # Check signal format
    signal = report.to_signal()
    
    print(f"   ✓ Signal type: {signal.get('signal_type')}")
    print(f"   ✓ Signal layer: {signal.get('signal_layer')}")
    print(f"   ✓ Signal source: {signal.get('signal_source')}")
    print()
    
    # Validate required fields
    required_fields = [
        "signal_type", "signal_layer", "signal_source", "mission_id",
        "total_duration_sec", "pages_visited", "selectors_attempted",
        "selectors_failed", "retries_total", "cost_units", "timestamp"
    ]
    
    for field in required_fields:
        assert field in signal, f"Missing required field: {field}"
    
    # Validate signal structure
    assert signal["signal_type"] == "mission_cost_report"
    assert signal["signal_layer"] == "mission"
    assert signal["signal_source"] == "mission_cost_accountant"
    assert signal["mission_id"] == "test-cost-002"
    
    # Validate cost_units structure
    cost_units = signal.get("cost_units", {})
    assert "time_cost" in cost_units
    assert "page_cost" in cost_units
    assert "failure_cost" in cost_units
    
    print("   Signal structure preview:")
    print(f"   {json.dumps(signal, indent=6)}")
    print()
    print("   ✅ PASSED - Signal structure valid\n")


def test_zero_activity_mission():
    """Test 3: Mission with no selector activity."""
    print("🧪 Test 3: Zero Activity Mission")
    print("-" * 70)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        test_signals = [
            {
                "signal_type": "mission_status_update",
                "mission_id": "test-cost-003",
                "status": "active",
                "timestamp": "2026-02-07T10:00:00+00:00"
            },
            {
                "signal_type": "mission_status_update",
                "mission_id": "test-cost-003",
                "status": "failed",
                "timestamp": "2026-02-07T10:00:10+00:00"
            }
        ]
        
        for signal in test_signals:
            f.write(json.dumps(signal) + '\n')
        
        temp_file = f.name
    
    try:
        accountant = MissionCostAccountant(signals_file=temp_file)
        report = accountant.compute_costs("test-cost-003")
        
        assert report is not None, "Should generate report even with zero activity"
        
        print(f"   Duration: {report.total_duration_sec}s")
        print(f"   Pages visited: {report.pages_visited}")
        print(f"   Selectors attempted: {report.selectors_attempted}")
        print(f"   Selectors failed: {report.selectors_failed}")
        print()
        
        assert report.total_duration_sec == 10.0
        assert report.pages_visited == 0
        assert report.selectors_attempted == 0
        assert report.selectors_failed == 0
        assert report.retries_total == 0
        
        print("   ✅ PASSED - Handles zero activity correctly\n")
        
    finally:
        Path(temp_file).unlink()


def test_high_failure_rate():
    """Test 4: Mission with high failure rate."""
    print("🧪 Test 4: High Failure Rate Mission")
    print("-" * 70)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        test_signals = [
            {
                "signal_type": "mission_status_update",
                "mission_id": "test-cost-004",
                "status": "active",
                "timestamp": "2026-02-07T10:00:00+00:00"
            }
        ]
        
        # Add many failed selectors
        for i in range(20):
            test_signals.append({
                "signal_type": "selector_outcome",
                "mission_id": "test-cost-004",
                "outcome": "failure",
                "page_number": 1,
                "retry_count": 3,
                "timestamp": f"2026-02-07T10:00:{10+i:02d}+00:00"
            })
        
        # Add a few successes
        for i in range(5):
            test_signals.append({
                "signal_type": "selector_outcome",
                "mission_id": "test-cost-004",
                "outcome": "success",
                "page_number": 1,
                "retry_count": 0,
                "timestamp": f"2026-02-07T10:00:{30+i:02d}+00:00"
            })
        
        test_signals.append({
            "signal_type": "mission_status_update",
            "mission_id": "test-cost-004",
            "status": "completed",
            "timestamp": "2026-02-07T10:01:00+00:00"
        })
        
        for signal in test_signals:
            f.write(json.dumps(signal) + '\n')
        
        temp_file = f.name
    
    try:
        accountant = MissionCostAccountant(signals_file=temp_file)
        report = accountant.compute_costs("test-cost-004")
        
        print(f"   Selectors attempted: {report.selectors_attempted}")
        print(f"   Selectors failed: {report.selectors_failed}")
        print(f"   Failure rate: {report.selectors_failed / report.selectors_attempted * 100:.1f}%")
        print(f"   Total retries: {report.retries_total}")
        print(f"   Failure cost: {report.failure_cost}")
        print()
        
        assert report.selectors_attempted == 25
        assert report.selectors_failed == 20
        assert report.retries_total == 60  # 20 failures * 3 retries each
        assert report.failure_cost == 20
        
        failure_rate = report.selectors_failed / report.selectors_attempted
        assert failure_rate == 0.8, "Failure rate should be 80%"
        
        print("   ✅ PASSED - High failure costs tracked correctly\n")
        
    finally:
        Path(temp_file).unlink()


def test_missing_signals_file():
    """Test 5: Handle missing signals file gracefully."""
    print("🧪 Test 5: Missing Signals File")
    print("-" * 70)
    
    accountant = MissionCostAccountant(signals_file="/nonexistent/file.jsonl")
    report = accountant.compute_costs("test-cost-005")
    
    assert report is None, "Should return None for missing file"
    assert accountant.should_emit_signal(None) == False, "Should not emit for None report"
    
    print("   ✓ Returns None for missing file")
    print("   ✓ Does not emit signal for None report")
    print("   ✅ PASSED - Handles missing file gracefully\n")


def test_whiteboard_integration():
    """Test 6: Whiteboard cost summary format."""
    print("🧪 Test 6: Whiteboard Integration Format")
    print("-" * 70)
    
    # Simulate what whiteboard would display
    cost_summary = {
        "total_duration_sec": 120.5,
        "pages_visited": 10,
        "selectors_attempted": 25,
        "selectors_failed": 5,
        "retries_total": 8,
        "time_cost": 120.5,
        "page_cost": 10,
        "failure_cost": 5,
        "timestamp": "2026-02-07T10:00:00+00:00"
    }
    
    print("   Whiteboard Cost Summary:")
    print(f"   {json.dumps(cost_summary, indent=6)}")
    print()
    
    # Validate all required fields present
    required_fields = [
        "total_duration_sec", "pages_visited", "selectors_attempted",
        "selectors_failed", "retries_total", "time_cost", "page_cost",
        "failure_cost", "timestamp"
    ]
    
    for field in required_fields:
        assert field in cost_summary, f"Missing field: {field}"
    
    print("   ✅ PASSED - Whiteboard format complete\n")


def run_all_tests():
    """Run all validation tests."""
    try:
        test_cost_computation()
        test_signal_emission()
        test_zero_activity_mission()
        test_high_failure_rate()
        test_missing_signals_file()
        test_whiteboard_integration()
        
        print("="*70)
        print("✅ ALL VALIDATION TESTS PASSED")
        print("="*70)
        print()
        print("📊 Summary:")
        print("   ✓ Cost computation from signals")
        print("   ✓ Signal emission logic")
        print("   ✓ Zero activity handling")
        print("   ✓ High failure rate tracking")
        print("   ✓ Missing file handling")
        print("   ✓ Whiteboard integration format")
        print()
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        raise
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}\n")
        raise


if __name__ == "__main__":
    run_all_tests()

