"""
Phase 19: Optimization & Adaptive Scheduling - Feedback Loop

Compares planned vs. executed schedules and generates learning signals
to refine optimization strategies and heuristics.
"""

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any


@dataclass
class ScheduleComparison:
    """Comparison between planned and actual schedule"""
    wave: int
    planned_success_rate: float
    actual_success_rate: float
    planned_throughput: float
    actual_throughput: float
    planned_confidence_delta: float
    actual_confidence_delta: float
    accuracy_score: float


@dataclass
class OptimizationFeedback:
    """Feedback signal for optimization improvement"""
    feedback_id: str
    feedback_type: str  # "strategy_validation", "heuristic_update", "schedule_adjustment"
    confidence: float
    description: str
    recommendation: str
    supporting_evidence: List[str]
    timestamp: str


class OptimizationFeedbackLoop:
    """
    Analyzes schedule execution and generates feedback for continuous improvement.
    
    Responsibilities:
    - Compare planned vs. actual schedule outcomes
    - Evaluate optimization strategy effectiveness
    - Generate learning signals for Phase 16/18 heuristics
    - Update optimization weights and parameters
    """
    
    def __init__(self, phase19_output_dir: Path, feedback_output_dir: Path):
        """
        Initialize optimization feedback loop.
        
        Args:
            phase19_output_dir: Directory with Phase 19 outputs
            feedback_output_dir: Directory for feedback outputs
        """
        self.phase19_output_dir = Path(phase19_output_dir)
        self.feedback_output_dir = Path(feedback_output_dir)
        self.feedback_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Feedback data
        self.schedule_comparisons: List[ScheduleComparison] = []
        self.optimization_feedback: List[OptimizationFeedback] = []
        
        # Performance tracking
        self.strategy_effectiveness: Dict[str, float] = {}
        self.heuristic_weights: Dict[str, float] = {}

    def _utc_now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _write_jsonl(self, path: Path, items: List[Dict[str, Any]]):
        path.write_text("\n".join(json.dumps(item) for item in items))
    
    def evaluate_schedule_outcome(
        self,
        wave: int,
        planned_metrics: Dict[str, float],
        actual_metrics: Dict[str, float]
    ) -> ScheduleComparison:
        """
        Compare planned vs. actual schedule outcomes.
        
        Args:
            wave: Wave number
            planned_metrics: Expected metrics from optimizer
            actual_metrics: Actual execution metrics
        
        Returns:
            ScheduleComparison with accuracy analysis
        """
        planned_success = float(planned_metrics.get("success_rate", 0.0))
        actual_success = float(actual_metrics.get("success_rate", 0.0))
        planned_throughput = float(planned_metrics.get("throughput", 0.0))
        actual_throughput = float(actual_metrics.get("throughput", 0.0))
        planned_conf_delta = float(planned_metrics.get("confidence_delta", 0.0))
        actual_conf_delta = float(actual_metrics.get("confidence_delta", 0.0))

        def accuracy(p: float, a: float) -> float:
            if p == 0.0:
                return 1.0 if a == 0.0 else 0.0
            return max(0.0, 1.0 - abs(p - a) / max(p, 1e-6))

        accuracy_score = (
            accuracy(planned_success, actual_success)
            + accuracy(planned_throughput, actual_throughput)
            + accuracy(planned_conf_delta, actual_conf_delta)
        ) / 3.0

        comparison = ScheduleComparison(
            wave=wave,
            planned_success_rate=planned_success,
            actual_success_rate=actual_success,
            planned_throughput=planned_throughput,
            actual_throughput=actual_throughput,
            planned_confidence_delta=planned_conf_delta,
            actual_confidence_delta=actual_conf_delta,
            accuracy_score=accuracy_score,
        )
        self.schedule_comparisons.append(comparison)
        return comparison
    
    def generate_feedback_events(self) -> int:
        """
        Generate feedback events from schedule analysis.
        
        Returns:
            Number of feedback events generated
        """
        events: List[Dict[str, Any]] = []
        for comparison in self.schedule_comparisons:
            if comparison.accuracy_score < 0.9:
                events.append({
                    "wave": comparison.wave,
                    "type": "prediction_error",
                    "severity": "medium" if comparison.accuracy_score > 0.8 else "high",
                    "accuracy_score": comparison.accuracy_score,
                    "timestamp": self._utc_now(),
                })
        self._write_jsonl(self.feedback_output_dir / "feedback_events.jsonl", events)
        return len(events)
    
    def generate_learning_signals(self) -> List[OptimizationFeedback]:
        """
        Generate learning signals for optimization improvement.
        
        Returns:
            List of OptimizationFeedback objects
        """
        signals: List[OptimizationFeedback] = []
        avg_accuracy = (
            sum(c.accuracy_score for c in self.schedule_comparisons) / max(len(self.schedule_comparisons), 1)
        )
        signals.append(
            OptimizationFeedback(
                feedback_id="P19_LS_STRATEGY_VALIDATION",
                feedback_type="strategy_validation",
                confidence=min(0.99, max(0.1, avg_accuracy)),
                description="Optimization strategy validation",
                recommendation="Continue current strategy" if avg_accuracy >= 0.9 else "Adjust strategy weights",
                supporting_evidence=[f"Average accuracy: {avg_accuracy:.3f}"],
                timestamp=self._utc_now(),
            )
        )

        if self.heuristic_weights:
            signals.append(
                OptimizationFeedback(
                    feedback_id="P19_LS_HEURISTIC_UPDATE",
                    feedback_type="heuristic_update",
                    confidence=0.88,
                    description="Heuristic weight update recommended",
                    recommendation="Apply updated heuristic weights",
                    supporting_evidence=["Performance-driven adjustments"],
                    timestamp=self._utc_now(),
                )
            )

        low_accuracy = [c for c in self.schedule_comparisons if c.accuracy_score < 0.85]
        if low_accuracy:
            signals.append(
                OptimizationFeedback(
                    feedback_id="P19_LS_PREDICTION_ERROR",
                    feedback_type="schedule_adjustment",
                    confidence=0.75,
                    description="Prediction errors detected",
                    recommendation="Increase conservative buffers and refine prediction model",
                    supporting_evidence=[f"Low-accuracy waves: {len(low_accuracy)}"],
                    timestamp=self._utc_now(),
                )
            )

        self.optimization_feedback.extend(signals)
        return signals
    
    def update_heuristic_weights(
        self,
        heuristic_performance: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Update heuristic weights based on performance.
        
        Args:
            heuristic_performance: Performance scores by heuristic
        
        Returns:
            Updated heuristic weights
        """
        updated: Dict[str, float] = {}
        for heuristic, score in heuristic_performance.items():
            base = float(self.heuristic_weights.get(heuristic, 1.0))
            if score >= 0.8:
                base += 0.05
            elif score <= 0.6:
                base -= 0.05
            updated[heuristic] = min(1.5, max(0.5, base))
        self.heuristic_weights = updated
        return updated
    
    def evaluate_strategy_effectiveness(
        self,
        strategy: str
    ) -> float:
        """
        Evaluate effectiveness of optimization strategy.
        
        Args:
            strategy: Strategy name
        
        Returns:
            Effectiveness score (0.0-1.0)
        """
        if not self.schedule_comparisons:
            return 0.0
        effectiveness = sum(c.accuracy_score for c in self.schedule_comparisons) / len(self.schedule_comparisons)
        self.strategy_effectiveness[strategy] = effectiveness
        return effectiveness
    
    def identify_optimization_failures(self) -> List[Dict[str, Any]]:
        """
        Identify cases where optimization predictions were significantly wrong.
        
        Returns:
            List of failure cases with analysis
        """
        failures = []
        for comparison in self.schedule_comparisons:
            if comparison.accuracy_score < 0.8:
                failures.append({
                    "wave": comparison.wave,
                    "accuracy_score": comparison.accuracy_score,
                    "issue": "Prediction error exceeds threshold",
                })
        return failures
    
    def recommend_strategy_adjustments(self) -> List[str]:
        """
        Recommend adjustments to optimization strategies.
        
        Returns:
            List of recommendations
        """
        recommendations = []
        avg_accuracy = sum(c.accuracy_score for c in self.schedule_comparisons) / max(len(self.schedule_comparisons), 1)
        if avg_accuracy < 0.9:
            recommendations.append("Increase success-rate weighting in optimization")
        if avg_accuracy < 0.8:
            recommendations.append("Enable conservative scheduling buffers")
        return recommendations
    
    def update_phase16_heuristics(self):
        """
        Send feedback to Phase 16 to update meta-learning heuristics.
        """
        output_path = Path("outputs/phase16")
        output_path.mkdir(parents=True, exist_ok=True)
        payloads = [
            {
                "type": "phase19_heuristic_update",
                "heuristic_weights": self.heuristic_weights,
                "timestamp": self._utc_now(),
            }
        ]
        self._write_jsonl(output_path / "phase19_feedback.jsonl", payloads)
    
    def update_phase18_coordination(self):
        """
        Send feedback to Phase 18 to improve multi-agent coordination.
        """
        output_path = Path("outputs/phase18")
        output_path.mkdir(parents=True, exist_ok=True)
        payloads = [
            {
                "type": "phase19_coordination_feedback",
                "strategy_effectiveness": self.strategy_effectiveness,
                "timestamp": self._utc_now(),
            }
        ]
        self._write_jsonl(output_path / "phase19_feedback.jsonl", payloads)
    
    def write_feedback_outputs(self):
        """
        Write feedback loop outputs to files.
        """
        comparisons_payload = [
            {
                "wave": c.wave,
                "planned_success_rate": c.planned_success_rate,
                "actual_success_rate": c.actual_success_rate,
                "planned_throughput": c.planned_throughput,
                "actual_throughput": c.actual_throughput,
                "planned_confidence_delta": c.planned_confidence_delta,
                "actual_confidence_delta": c.actual_confidence_delta,
                "accuracy_score": c.accuracy_score,
            }
            for c in self.schedule_comparisons
        ]
        self._write_jsonl(self.feedback_output_dir / "schedule_comparisons.jsonl", comparisons_payload)

        feedback_payload = [
            {
                "feedback_id": f.feedback_id,
                "feedback_type": f.feedback_type,
                "confidence": f.confidence,
                "description": f.description,
                "recommendation": f.recommendation,
                "supporting_evidence": f.supporting_evidence,
                "timestamp": f.timestamp,
            }
            for f in self.optimization_feedback
        ]
        self._write_jsonl(self.feedback_output_dir / "optimization_feedback.jsonl", feedback_payload)
        (self.feedback_output_dir / "heuristic_weights.json").write_text(json.dumps(self.heuristic_weights, indent=2))
        (self.feedback_output_dir / "strategy_effectiveness.json").write_text(json.dumps(self.strategy_effectiveness, indent=2))


def main():
    """
    Main execution function for testing feedback loop.
    """
    # TODO: Initialize feedback loop
    # TODO: Load schedule outcomes
    # TODO: Evaluate outcomes
    # TODO: Generate feedback
    # TODO: Write outputs
    pass


if __name__ == "__main__":
    main()
