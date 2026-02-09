"""
Phase 22: Meta-Learning Feedback Loop

Purpose:
    Generates bidirectional feedback signals for Phases 16, 18, and 20
    based on optimization outcomes, agent tuning, and system health.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
import json


@dataclass
class Phase22FeedbackEvent:
    """Event captured during Phase 22 feedback generation."""

    event_id: str
    wave: int
    event_type: str
    details: Dict
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class Phase22LearningSignal:
    """Learning signal routed to upstream phases."""

    signal_id: str
    signal_type: str  # heuristic_feedback, coordination_refinement, prediction_tuning
    target_phase: int
    confidence: float
    content: Dict
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class Phase22FeedbackLoop:
    """
    Generates and routes feedback signals for Phase 22.
    """

    def __init__(
        self,
        phase16_dir: Path,
        phase18_dir: Path,
        phase20_dir: Path,
        phase22_output_dir: Path,
        dry_run: bool = True,
    ):
        """
        Initialize feedback loop.

        Args:
            phase16_dir: Phase 16 directory
            phase18_dir: Phase 18 directory
            phase20_dir: Phase 20 directory
            phase22_output_dir: Phase 22 output directory
            dry_run: If True, no side effects
        """
        self.phase16_dir = Path(phase16_dir)
        self.phase18_dir = Path(phase18_dir)
        self.phase20_dir = Path(phase20_dir)
        self.phase22_output_dir = Path(phase22_output_dir)
        self.dry_run = dry_run

        self.feedback_events: List[Phase22FeedbackEvent] = []
        self.learning_signals: List[Phase22LearningSignal] = []

    def generate_feedback_signals(
        self,
        wave: int,
        metrics: Dict[str, float],
        anomalies: List[Dict],
        tuning_results: List[Dict],
        optimization_result: Dict,
    ) -> List[Phase22LearningSignal]:
        """
        Generate learning signals based on Phase 22 outcomes.

        Args:
            wave: Wave number
            metrics: Computed metrics
            anomalies: Detected anomalies
            tuning_results: Per-agent tuning results
            optimization_result: Meta-optimization recommendation

        Returns:
            List of Phase22LearningSignal
        """
        signals: List[Phase22LearningSignal] = []
        confidence = max(0.75, min(0.98, metrics.get("system_health", 0.9)))

        heuristic_signal = Phase22LearningSignal(
            signal_id=f"phase22_heuristic_{wave}",
            signal_type="heuristic_feedback",
            target_phase=16,
            confidence=confidence,
            content={
                "wave": wave,
                "optimization_strategy": optimization_result.get("strategy"),
                "adjustments": optimization_result.get("adjustments", {}),
                "metrics": metrics,
                "anomalies": anomalies,
            },
        )
        signals.append(heuristic_signal)

        coordination_signal = Phase22LearningSignal(
            signal_id=f"phase22_coordination_{wave}",
            signal_type="coordination_refinement",
            target_phase=18,
            confidence=confidence,
            content={
                "wave": wave,
                "load_balance": metrics.get("load_balance", 1.0),
                "utilization": metrics.get("agent_utilization", 1.0),
                "schedule_adherence": metrics.get("schedule_adherence", 1.0),
                "tuning_actions": tuning_results,
            },
        )
        signals.append(coordination_signal)

        prediction_signal = Phase22LearningSignal(
            signal_id=f"phase22_prediction_{wave}",
            signal_type="prediction_tuning",
            target_phase=20,
            confidence=confidence,
            content={
                "wave": wave,
                "confidence_trajectory": metrics.get("confidence_trajectory", 1.0),
                "success_rate": metrics.get("success_rate", 1.0),
                "recommendations": optimization_result.get("adjustments", {}),
            },
        )
        signals.append(prediction_signal)

        self.learning_signals.extend(signals)
        return signals

    def write_feedback_outputs(self) -> Dict[str, Optional[str]]:
        """
        Write feedback outputs to Phase 16, 18, 20 and Phase 22 directories.

        Returns:
            Dict of output paths
        """
        outputs: Dict[str, Optional[str]] = {
            "learning_signals": None,
            "phase16_feedback": None,
            "phase18_feedback": None,
            "phase20_feedback": None,
        }
        self.phase22_output_dir.mkdir(parents=True, exist_ok=True)
        learning_signals_path = self.phase22_output_dir / "learning_signals.jsonl"
        with open(learning_signals_path, "w", encoding="utf-8") as handle:
            for signal in self.learning_signals:
                payload = signal.__dict__.copy()
                payload["dry_run"] = self.dry_run
                handle.write(json.dumps(payload) + "\n")
        outputs["learning_signals"] = str(learning_signals_path)

        if not self.dry_run:
            outputs["phase16_feedback"] = self._write_phase_feedback(
                self.phase16_dir, "phase22_feedback.jsonl", 16
            )
            outputs["phase18_feedback"] = self._write_phase_feedback(
                self.phase18_dir, "phase22_feedback.jsonl", 18
            )
            outputs["phase20_feedback"] = self._write_phase_feedback(
                self.phase20_dir, "phase22_feedback.jsonl", 20
            )

        return outputs

    def _write_phase_feedback(
        self, phase_dir: Path, filename: str, target_phase: int
    ) -> Optional[str]:
        if self.dry_run:
            return None

        phase_dir.mkdir(parents=True, exist_ok=True)
        output_path = phase_dir / filename
        with open(output_path, "w", encoding="utf-8") as handle:
            for signal in self.learning_signals:
                if signal.target_phase == target_phase:
                    handle.write(json.dumps(signal.__dict__) + "\n")
        return str(output_path)
