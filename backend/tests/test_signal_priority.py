"""
Phase 4 Step 4: Signal Prioritization - Validation Tests
"""

import json
from pathlib import Path

from backend.learning.signal_priority import apply_signal_priority
from backend.phase25_dashboard_aggregator import Phase25DashboardAggregator


def test_apply_signal_priority_defaults():
    signal = {"signal_type": "drift_warning"}
    updated = apply_signal_priority(signal)
    assert updated["signal_priority"] == "CRITICAL"

    signal2 = {"signal_type": "selector_outcome"}
    updated2 = apply_signal_priority(signal2)
    assert updated2["signal_priority"] == "INFO"


def test_dashboard_learning_signals_no_loss(tmp_path):
    data_dir = tmp_path / "phase25"
    data_dir.mkdir(parents=True, exist_ok=True)
    signals_file = data_dir / "learning_signals.jsonl"

    # Write a low-confidence signal without priority
    with open(signals_file, "w", encoding="utf-8") as f:
        f.write(json.dumps({
            "signal_type": "selector_outcome",
            "confidence": 0.1,
            "timestamp": "2026-02-07T12:00:00Z"
        }) + "\n")

    aggregator = Phase25DashboardAggregator(data_dir=str(data_dir))
    signals = aggregator._get_learning_signals(limit=10)

    assert len(signals) == 1
    assert signals[0]["signal_type"] == "selector_outcome"
    assert signals[0]["signal_priority"] == "INFO"
