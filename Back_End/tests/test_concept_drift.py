"""
Phase 4 Step 3: Concept Drift Detection - Validation Tests

Tests that DriftMonitor detects degradation and emits drift_warning signals.
"""

import os
import json
import uuid
import pytest
from datetime import datetime, timedelta
from pathlib import Path

from Back_End.evaluation.drift_monitor import DriftMonitor


def _write_signal(path: Path, signal: dict) -> None:
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(signal) + "\n")


def test_drift_warning_emitted_for_selector_success_rate(tmp_path):
    """Inject degraded selector success rate and confirm drift_warning emitted."""
    signals_file = tmp_path / "learning_signals.jsonl"
    base_time = datetime(2026, 2, 7, 12, 0, 0)

    # Baseline missions (5) with high success rates
    baseline_missions = []
    for i in range(5):
        mission_id = str(uuid.uuid4())
        baseline_missions.append(mission_id)
        _write_signal(signals_file, {
            "signal_type": "selector_aggregate",
            "mission_id": mission_id,
            "overall_success_rate": 0.9,
            "timestamp": (base_time + timedelta(minutes=i)).isoformat()
        })

    # Current missions (3) with degraded success rates
    current_missions = []
    for i in range(3):
        mission_id = str(uuid.uuid4())
        current_missions.append(mission_id)
        _write_signal(signals_file, {
            "signal_type": "selector_aggregate",
            "mission_id": mission_id,
            "overall_success_rate": 0.5,
            "timestamp": (base_time + timedelta(minutes=10 + i)).isoformat()
        })

    # Include mission_thread_id for latest mission
    latest_mission_id = current_missions[-1]
    thread_id = str(uuid.uuid4())
    _write_signal(signals_file, {
        "signal_type": "mission_status_update",
        "mission_id": latest_mission_id,
        "mission_thread_id": thread_id,
        "status": "completed",
        "reason": "execution_completed",
        "timestamp": (base_time + timedelta(minutes=20)).isoformat()
    })

    monitor = DriftMonitor(
        signals_file=signals_file,
        window_size=3,
        threshold=0.2,
        min_baseline_samples=3
    )

    warnings = monitor.evaluate()

    assert len(warnings) == 1
    warning = warnings[0]
    assert warning["signal_type"] == "drift_warning"
    assert warning["metric"] == "selector_success_rate"
    assert warning["baseline"] > warning["current"]
    assert warning["delta"] < 0
    assert warning["mission_id"] == latest_mission_id
    assert warning["mission_thread_id"] == thread_id

    # Confirm signal persisted
    with open(signals_file, "r", encoding="utf-8") as f:
        signals = [json.loads(line) for line in f if line.strip()]

    drift_signals = [s for s in signals if s.get("signal_type") == "drift_warning"]
    assert len(drift_signals) == 1
    assert drift_signals[0]["metric"] == "selector_success_rate"


def test_whiteboard_shows_drift_alerts(tmp_path):
    """Confirm whiteboard exposes drift alerts."""
    missions_file = tmp_path / "missions.jsonl"
    signals_file = tmp_path / "learning_signals.jsonl"

    os.environ["MISSIONS_FILE"] = str(missions_file)
    os.environ["LEARNING_SIGNALS_FILE"] = str(signals_file)

    try:
        # Create mission record
        mission_id = str(uuid.uuid4())
        _write_signal(missions_file, {
            "event_type": "mission_created",
            "mission": {
                "mission_id": mission_id,
                "objective": {
                    "type": "data_collection",
                    "description": "Test mission",
                    "target": 10,
                    "required_fields": ["data"]
                },
                "scope": {"allowed_domains": ["example.com"], "max_pages": 10, "max_duration_seconds": 60},
                "authority": {"execution_mode": "supervised", "external_actions_allowed": []},
                "success_conditions": {"min_items_collected": 10},
                "failure_conditions": {"no_progress_pages": 5, "navigation_blocked": False, "required_fields_missing": False},
                "reporting": {"summary_required": True, "confidence_explanation": True},
                "status": "completed",
                "created_at": datetime.now().isoformat(),
                "completed_at": datetime.now().isoformat()
            },
            "timestamp": datetime.now().isoformat()
        })

        # Add drift warning signal
        _write_signal(signals_file, {
            "signal_type": "drift_warning",
            "signal_layer": "analysis",
            "signal_source": "drift_monitor",
            "mission_id": mission_id,
            "metric": "selector_success_rate",
            "baseline": 0.9,
            "current": 0.5,
            "delta": -0.4,
            "timestamp": datetime.now().isoformat()
        })

        import importlib
        import Back_End.whiteboard.mission_whiteboard as wb_module
        importlib.reload(wb_module)
        from Back_End.whiteboard.mission_whiteboard import get_mission_whiteboard

        whiteboard = get_mission_whiteboard(mission_id)

        assert "drift_alerts" in whiteboard
        assert len(whiteboard["drift_alerts"]) == 1
        assert whiteboard["drift_alerts"][0]["metric"] == "selector_success_rate"
        assert whiteboard["mission_drift_warning"] is not None

    finally:
        if "MISSIONS_FILE" in os.environ:
            del os.environ["MISSIONS_FILE"]
        if "LEARNING_SIGNALS_FILE" in os.environ:
            del os.environ["LEARNING_SIGNALS_FILE"]

