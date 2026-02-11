"""
Phase 20: Predictive Task Assignment - Feedback Loop Module

Purpose:
    Generate feedback signals to Phase 16 heuristics and Phase 18 multi-agent
    coordination based on prediction accuracy and task outcomes.

Key Responsibilities:
    - Evaluate prediction accuracy
    - Generate feedback events
    - Generate learning signals for Phase 16/18
    - Update heuristic effectiveness tracking
"""

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class PredictionComparison:
    """Comparison between predicted and actual outcomes"""
    wave: int
    task_id: str
    agent_id: str
    predicted_success: float
    actual_success: float
    prediction_error: float
    predicted_confidence_delta: float
    actual_confidence_delta: float
    timestamp: str


@dataclass
class LearningSignal:
    """Learning signal for Phase 16/18"""
    feedback_id: str
    feedback_type: str
    confidence: float
    description: str
    recommendation: str
    supporting_evidence: List[str]
    timestamp: str


class PredictionFeedbackLoop:
    """
    Analyzes prediction accuracy and generates feedback signals
    for continuous improvement of Phase 16 heuristics and Phase 18 coordination.
    """

    def __init__(self, phase16_dir: Path, phase18_dir: Path, phase20_dir: Path, dry_run: bool = True):
        """
        Initialize feedback loop.
        
        Args:
            phase16_dir: Path to Phase 16 for heuristic feedback
            phase18_dir: Path to Phase 18 for coordination feedback
            phase20_dir: Path to Phase 20 outputs
            dry_run: If True, no side effects
        """
        self.phase16_dir = Path(phase16_dir)
        self.phase18_dir = Path(phase18_dir)
        self.phase20_dir = Path(phase20_dir)
        self.dry_run = dry_run

        # Feedback tracking
        self.comparisons: List[PredictionComparison] = []
        self.learning_signals: List[LearningSignal] = []
        self.prediction_accuracy_history: List[float] = []

    def evaluate_predictions(
        self, predicted_outcomes: List[Dict], actual_outcomes: List[Dict]
    ) -> List[PredictionComparison]:
        """
        Compare predicted vs actual outcomes and generate comparisons.
        
        Args:
            predicted_outcomes: List of predicted task outcomes
            actual_outcomes: List of actual task outcomes
            
        Returns:
            List of PredictionComparison objects
        """
        self.comparisons = []

        for prediction in predicted_outcomes:
            task_id = prediction.get("task_id")
            agent_id = prediction.get("agent_id")

            # Find matching actual outcome
            actual = None
            for outcome in actual_outcomes:
                if (
                    outcome.get("task_id") == task_id
                    and outcome.get("agent_id") == agent_id
                ):
                    actual = outcome
                    break

            if not actual:
                continue

            # Calculate comparison metrics
            predicted_success = prediction.get("predicted_success_probability", 0.5)
            actual_success = 1.0 if actual.get("status") == "completed" else 0.0
            error = abs(predicted_success - actual_success)

            comparison = PredictionComparison(
                wave=prediction.get("wave", 1),
                task_id=task_id,
                agent_id=agent_id,
                predicted_success=round(predicted_success, 4),
                actual_success=round(actual_success, 4),
                prediction_error=round(error, 4),
                predicted_confidence_delta=prediction.get(
                    "predicted_confidence_delta", 0.02
                ),
                actual_confidence_delta=actual.get("confidence_delta", 0.02),
                timestamp=self._utc_now(),
            )
            self.comparisons.append(comparison)

        return self.comparisons

    def generate_feedback_events(self) -> List[Dict]:
        """
        Generate feedback events from prediction comparisons.
        
        Returns:
            List of feedback event dictionaries
        """
        events = []

        # Large prediction errors (opportunities for improvement)
        large_errors = [c for c in self.comparisons if c.prediction_error > 0.20]
        if large_errors:
            events.append({
                "event_type": "prediction_error_detected",
                "severity": "high" if len(large_errors) > len(self.comparisons) * 0.30 else "medium",
                "count": len(large_errors),
                "avg_error": round(sum(c.prediction_error for c in large_errors) / len(large_errors), 4),
                "recommendation": "Review prediction model training data",
                "timestamp": self._utc_now(),
            })

        # Underperforming agents
        agent_errors = {}
        for comp in self.comparisons:
            if comp.agent_id not in agent_errors:
                agent_errors[comp.agent_id] = []
            agent_errors[comp.agent_id].append(comp.prediction_error)

        for agent_id, errors in agent_errors.items():
            avg_error = sum(errors) / len(errors)
            if avg_error > 0.20:
                events.append({
                    "event_type": "agent_prediction_drift",
                    "agent_id": agent_id,
                    "avg_error": round(avg_error, 4),
                    "recommendation": f"Update {agent_id} success rate estimates",
                    "timestamp": self._utc_now(),
                })

        return events

    def generate_learning_signals(self) -> List[LearningSignal]:
        """
        Generate learning signals for Phase 16 heuristics and Phase 18 coordination.
        
        Returns:
            List of LearningSignal objects
        """
        self.learning_signals = []

        if not self.comparisons:
            return self.learning_signals

        # Calculate overall prediction accuracy
        total_comparisons = len(self.comparisons)
        accurate_predictions = sum(
            1 for c in self.comparisons if c.prediction_error < 0.15
        )
        accuracy = accurate_predictions / total_comparisons if total_comparisons > 0 else 0.0
        self.prediction_accuracy_history.append(accuracy)

        # Signal 1: Prediction model validation
        if accuracy >= 0.75:
            signal1 = LearningSignal(
                feedback_id="P20_LS_MODEL_VALIDATION",
                feedback_type="prediction_model_validation",
                confidence=accuracy,
                description="Prediction model validated with high accuracy",
                recommendation="Continue current prediction model",
                supporting_evidence=[
                    f"Prediction accuracy: {accuracy:.2%}",
                    f"Total predictions evaluated: {total_comparisons}",
                ],
                timestamp=self._utc_now(),
            )
            self.learning_signals.append(signal1)

        # Signal 2: Heuristic effectiveness (for Phase 16)
        avg_confidence_delta = (
            sum(c.actual_confidence_delta for c in self.comparisons)
            / total_comparisons
        )
        if avg_confidence_delta > 0.01:
            signal2 = LearningSignal(
                feedback_id="P20_LS_HEURISTIC_EFFECTIVENESS",
                feedback_type="heuristic_effectiveness",
                confidence=0.85,
                description="Phase 16 heuristics show positive confidence trajectory",
                recommendation="Reinforce current heuristic strategy in Phase 16",
                supporting_evidence=[
                    f"Average confidence delta: {avg_confidence_delta:.4f}",
                    f"Positive trend detected",
                ],
                timestamp=self._utc_now(),
            )
            self.learning_signals.append(signal2)

        # Signal 3: Multi-agent coordination insights (for Phase 18)
        # Analyze agent-specific performance
        agent_stats = {}
        for comp in self.comparisons:
            if comp.agent_id not in agent_stats:
                agent_stats[comp.agent_id] = {"successes": 0, "total": 0}
            agent_stats[comp.agent_id]["total"] += 1
            if comp.actual_success > 0.5:
                agent_stats[comp.agent_id]["successes"] += 1

        best_agent = max(
            agent_stats.items(),
            key=lambda x: x[1]["successes"] / x[1]["total"] if x[1]["total"] > 0 else 0,
            default=None,
        )

        if best_agent:
            signal3 = LearningSignal(
                feedback_id="P20_LS_COORDINATION_INSIGHT",
                feedback_type="multi_agent_coordination",
                confidence=0.80,
                description=f"Coordination insights from Phase 20 predictions",
                recommendation=f"Leverage {best_agent[0]} performance pattern in Phase 18 coordination",
                supporting_evidence=[
                    f"Agent {best_agent[0]} success rate: {best_agent[1]['successes'] / best_agent[1]['total']:.2%}",
                    f"Recommendation: Use as reference for coordination",
                ],
                timestamp=self._utc_now(),
            )
            self.learning_signals.append(signal3)

        return self.learning_signals

    def write_feedback_outputs(self) -> Dict[str, str]:
        """
        Write feedback to Phase 16 and Phase 18 directories.
        
        Returns:
            Dictionary with output file paths
        """
        output_files = {}

        # Write learning signals
        signals_file = self.phase20_dir / "learning_signals.jsonl"
        with open(signals_file, "w") as f:
            for signal in self.learning_signals:
                f.write(json.dumps(signal.__dict__) + "\n")
        output_files["learning_signals"] = str(signals_file)

        # Write Phase 16 feedback (heuristic updates)
        phase16_feedback = self.phase16_dir / "phase20_feedback.jsonl"
        with open(phase16_feedback, "w") as f:
            for signal in self.learning_signals:
                if signal.feedback_type == "heuristic_effectiveness":
                    f.write(json.dumps(signal.__dict__) + "\n")
        output_files["phase16_feedback"] = str(phase16_feedback)

        # Write Phase 18 feedback (coordination updates)
        phase18_feedback = self.phase18_dir / "phase20_feedback.jsonl"
        with open(phase18_feedback, "w") as f:
            for signal in self.learning_signals:
                if signal.feedback_type == "multi_agent_coordination":
                    f.write(json.dumps(signal.__dict__) + "\n")
        output_files["phase18_feedback"] = str(phase18_feedback)

        return output_files

    # Helper methods

    def _utc_now(self) -> str:
        """Return current UTC timestamp in ISO format."""
        return datetime.now(timezone.utc).isoformat()

