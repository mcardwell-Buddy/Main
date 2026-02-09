"""
Phase 4 Step 3: Concept Drift Detection

Read-only monitor to detect gradual performance degradation across missions.
Tracks rolling metrics and emits drift_warning signals when degradation exceeds threshold.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import json

from backend.learning.signal_priority import apply_signal_priority


@dataclass
class MetricSeries:
    metric: str
    values: List[Tuple[str, float, str]]  # (mission_id, value, timestamp)


class DriftMonitor:
    """
    Concept drift monitor for performance metrics.

    Metrics tracked:
    - selector_success_rate (from selector_aggregate.overall_success_rate)
    - intent_confidence (from navigation_intent_ranked.confidence)
    - opportunity_confidence (from opportunity_normalized.avg_confidence)

    Read-only analysis only. No execution changes or remediation.
    """

    def __init__(
        self,
        signals_file: Optional[Path] = None,
        window_size: int = 5,
        threshold: float = 0.15,
        min_baseline_samples: int = 3
    ) -> None:
        if signals_file is None:
            output_dir = Path(__file__).parent.parent.parent / "outputs" / "phase25"
            output_dir.mkdir(parents=True, exist_ok=True)
            signals_file = output_dir / "learning_signals.jsonl"

        self.signals_file = signals_file
        self.window_size = window_size
        self.threshold = threshold
        self.min_baseline_samples = min_baseline_samples

    def evaluate(self) -> List[Dict[str, Any]]:
        """
        Evaluate drift across metrics and emit warnings if degradation detected.

        Returns:
            List of drift_warning signals emitted.
        """
        signals = self._read_signals()
        if not signals:
            return []

        metric_series = self._build_metric_series(signals)
        warnings: List[Dict[str, Any]] = []

        for series in metric_series:
            warning = self._evaluate_series(series, signals)
            if warning:
                self._emit_signal(apply_signal_priority(warning))
                warnings.append(warning)

        return warnings

    def _read_signals(self) -> List[Dict[str, Any]]:
        if not self.signals_file.exists():
            return []
        records: List[Dict[str, Any]] = []
        with open(self.signals_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return records

    def _build_metric_series(self, signals: List[Dict[str, Any]]) -> List[MetricSeries]:
        selector_values: List[Tuple[str, float, str]] = []
        intent_values: List[Tuple[str, float, str]] = []
        opportunity_values: List[Tuple[str, float, str]] = []

        for s in signals:
            signal_type = s.get("signal_type")
            mission_id = s.get("mission_id")
            timestamp = s.get("timestamp")

            if not mission_id or not timestamp:
                continue

            if signal_type == "selector_aggregate":
                value = s.get("overall_success_rate")
                if isinstance(value, (int, float)):
                    selector_values.append((mission_id, float(value), timestamp))

            if signal_type == "navigation_intent_ranked":
                value = s.get("confidence")
                if isinstance(value, (int, float)):
                    intent_values.append((mission_id, float(value), timestamp))

            if signal_type == "opportunity_normalized":
                value = s.get("avg_confidence")
                if isinstance(value, (int, float)):
                    opportunity_values.append((mission_id, float(value), timestamp))

        return [
            MetricSeries("selector_success_rate", selector_values),
            MetricSeries("intent_confidence", intent_values),
            MetricSeries("opportunity_confidence", opportunity_values)
        ]

    def _evaluate_series(
        self,
        series: MetricSeries,
        signals: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        # Sort by timestamp
        values = sorted(series.values, key=lambda v: v[2])
        if len(values) < self.window_size + self.min_baseline_samples:
            return None

        # Current window (last N)
        current_window = values[-self.window_size:]
        baseline_window = values[:-self.window_size]

        if len(baseline_window) < self.min_baseline_samples:
            return None

        baseline_avg = sum(v[1] for v in baseline_window) / len(baseline_window)
        current_avg = sum(v[1] for v in current_window) / len(current_window)
        delta = current_avg - baseline_avg

        if baseline_avg <= 0:
            return None

        # Detect degradation
        if (baseline_avg - current_avg) >= self.threshold:
            latest_mission_id = current_window[-1][0]
            mission_thread_id = self._find_mission_thread_id(latest_mission_id, signals)

            warning = {
                "signal_type": "drift_warning",
                "signal_layer": "analysis",
                "signal_source": "drift_monitor",
                "mission_id": latest_mission_id,
                "metric": series.metric,
                "baseline": round(baseline_avg, 4),
                "current": round(current_avg, 4),
                "delta": round(delta, 4),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            if mission_thread_id:
                warning["mission_thread_id"] = mission_thread_id

            return warning

        return None

    def _find_mission_thread_id(self, mission_id: str, signals: List[Dict[str, Any]]) -> Optional[str]:
        for s in reversed(signals):
            if s.get("mission_id") == mission_id and s.get("mission_thread_id"):
                return s.get("mission_thread_id")
        return None

    def _emit_signal(self, signal: Dict[str, Any]) -> None:
        with open(self.signals_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(signal) + "\n")
