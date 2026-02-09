"""
Phase 22: Meta-Optimization Engine

Purpose:
    Central meta-optimization module that selects strategies to improve
    multi-agent performance using reinforcement signals from Phase 20/21
    and feedback from Phase 16/18.

Core Strategies:
    - MAXIMIZE_SUCCESS
    - MAXIMIZE_THROUGHPUT
    - BALANCE_LOAD
    - MINIMIZE_RETRIES
    - MAXIMIZE_CONFIDENCE
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional
import json


class OptimizationStrategy(str, Enum):
    """Available meta-optimization strategies."""

    MAXIMIZE_SUCCESS = "maximize_success"
    MAXIMIZE_THROUGHPUT = "maximize_throughput"
    BALANCE_LOAD = "balance_load"
    MINIMIZE_RETRIES = "minimize_retries"
    MAXIMIZE_CONFIDENCE = "maximize_confidence"


@dataclass
class MetaOptimizationRecommendation:
    """Recommendation produced by the meta-optimizer."""

    wave: int
    strategy: OptimizationStrategy
    adjustments: Dict[str, float]
    expected_impact: Dict[str, float]
    confidence: float
    rationale: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class Phase22MetaOptimizer:
    """
    Central meta-optimization engine for Phase 22.
    """

    def __init__(self, phase22_output_dir: Path, dry_run: bool = True):
        """
        Initialize the meta-optimizer.

        Args:
            phase22_output_dir: Base output directory for Phase 22
            dry_run: If True, no side effects
        """
        self.phase22_output_dir = Path(phase22_output_dir)
        self.dry_run = dry_run
        self.recommendations: List[MetaOptimizationRecommendation] = []

    def apply_reinforcement_signals(
        self, phase20_metrics: Dict, phase21_metrics: Dict
    ) -> Dict[str, float]:
        """
        Combine Phase 20 and Phase 21 reinforcement signals into weights.

        Args:
            phase20_metrics: Metrics from Phase 20 outputs
            phase21_metrics: Metrics from Phase 21 outputs

        Returns:
            Dict of reinforcement weights per strategy
        """
        success_weight = max(0.0, 1.0 - phase21_metrics.get("failure_rate", 0.0))
        throughput_weight = min(1.0, phase21_metrics.get("throughput", 0.0) / 35.0)
        load_weight = max(0.0, 1.0 - phase21_metrics.get("load_imbalance", 0.0))
        retry_weight = max(0.0, 1.0 - phase21_metrics.get("retry_rate", 0.0))
        confidence_weight = max(0.0, phase20_metrics.get("confidence", 0.95))

        return {
            OptimizationStrategy.MAXIMIZE_SUCCESS.value: success_weight,
            OptimizationStrategy.MAXIMIZE_THROUGHPUT.value: throughput_weight,
            OptimizationStrategy.BALANCE_LOAD.value: load_weight,
            OptimizationStrategy.MINIMIZE_RETRIES.value: retry_weight,
            OptimizationStrategy.MAXIMIZE_CONFIDENCE.value: confidence_weight,
        }

    def optimize_wave(
        self,
        wave: int,
        metrics: Dict[str, float],
        anomalies: Optional[List[Dict]] = None,
    ) -> MetaOptimizationRecommendation:
        """
        Produce a meta-optimization recommendation for a wave.

        Args:
            wave: Wave number
            metrics: Dictionary of computed metrics
            anomalies: Optional list of anomaly dicts

        Returns:
            MetaOptimizationRecommendation
        """
        anomalies = anomalies or []
        strategy = self._select_strategy(metrics, anomalies)
        adjustments = self._compute_adjustments(strategy, metrics)
        expected_impact = self._estimate_impact(strategy, metrics)
        confidence = self._estimate_confidence(metrics, anomalies)

        recommendation = MetaOptimizationRecommendation(
            wave=wave,
            strategy=strategy,
            adjustments=adjustments,
            expected_impact=expected_impact,
            confidence=confidence,
            rationale=self._build_rationale(strategy, metrics, anomalies),
        )
        self.recommendations.append(recommendation)
        return recommendation

    def suggest_phase16_adjustments(
        self, recommendation: MetaOptimizationRecommendation
    ) -> List[Dict]:
        """
        Suggest heuristic adjustments for Phase 16.

        Args:
            recommendation: Meta-optimization recommendation

        Returns:
            List of heuristic adjustment dictionaries
        """
        adjustments = []
        for key, value in recommendation.adjustments.items():
            adjustments.append(
                {
                    "heuristic": key,
                    "delta": value,
                    "confidence": recommendation.confidence,
                    "strategy": recommendation.strategy.value,
                    "rationale": recommendation.rationale,
                }
            )
        return adjustments

    def write_recommendations(self) -> Optional[Path]:
        """
        Write meta-optimization recommendations to JSONL.

        Returns:
            Path to output file or None in dry-run mode
        """
        output_path = self.phase22_output_dir / "meta_optimization_recommendations.jsonl"
        self.phase22_output_dir.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as handle:
            for item in self.recommendations:
                handle.write(json.dumps(item.__dict__) + "\n")
        return output_path

    def _select_strategy(
        self, metrics: Dict[str, float], anomalies: List[Dict]
    ) -> OptimizationStrategy:
        if metrics.get("success_rate", 1.0) < 0.90:
            return OptimizationStrategy.MAXIMIZE_SUCCESS
        if metrics.get("throughput", 0.0) < 35.0:
            return OptimizationStrategy.MAXIMIZE_THROUGHPUT
        if metrics.get("load_balance", 1.0) < 0.85:
            return OptimizationStrategy.BALANCE_LOAD
        if metrics.get("retry_rate", 0.0) > 0.10:
            return OptimizationStrategy.MINIMIZE_RETRIES
        if metrics.get("confidence_trajectory", 1.0) < 0.95:
            return OptimizationStrategy.MAXIMIZE_CONFIDENCE

        for anomaly in anomalies:
            if anomaly.get("anomaly_type") == "optimization_failure":
                return OptimizationStrategy.MAXIMIZE_SUCCESS

        return OptimizationStrategy.BALANCE_LOAD

    def _compute_adjustments(
        self, strategy: OptimizationStrategy, metrics: Dict[str, float]
    ) -> Dict[str, float]:
        if strategy == OptimizationStrategy.MAXIMIZE_SUCCESS:
            return {"retry_threshold": 1.0, "confidence_weight": 0.05}
        if strategy == OptimizationStrategy.MAXIMIZE_THROUGHPUT:
            return {"speed_multiplier": 0.05, "max_parallel_tasks": 1.0}
        if strategy == OptimizationStrategy.BALANCE_LOAD:
            return {"load_balance_bias": 0.10, "rebalance_threshold": -0.05}
        if strategy == OptimizationStrategy.MINIMIZE_RETRIES:
            return {"retry_threshold": -1.0, "safety_gate_strictness": 0.05}
        if strategy == OptimizationStrategy.MAXIMIZE_CONFIDENCE:
            return {"confidence_weight": 0.08, "prediction_bias": 0.02}
        return {}

    def _estimate_impact(
        self, strategy: OptimizationStrategy, metrics: Dict[str, float]
    ) -> Dict[str, float]:
        if strategy == OptimizationStrategy.MAXIMIZE_SUCCESS:
            return {"success_rate": 0.03, "system_health": 0.02}
        if strategy == OptimizationStrategy.MAXIMIZE_THROUGHPUT:
            return {"throughput": 5.0, "utilization": 0.01}
        if strategy == OptimizationStrategy.BALANCE_LOAD:
            return {"load_balance": 0.05, "utilization": 0.02}
        if strategy == OptimizationStrategy.MINIMIZE_RETRIES:
            return {"retry_rate": -0.05, "success_rate": 0.01}
        if strategy == OptimizationStrategy.MAXIMIZE_CONFIDENCE:
            return {"confidence_trajectory": 0.03, "accuracy": 0.01}
        return {}

    def _estimate_confidence(
        self, metrics: Dict[str, float], anomalies: List[Dict]
    ) -> float:
        base = metrics.get("system_health", 0.9)
        penalty = min(0.15, 0.03 * len(anomalies))
        return max(0.70, min(0.98, base - penalty))

    def _build_rationale(
        self,
        strategy: OptimizationStrategy,
        metrics: Dict[str, float],
        anomalies: List[Dict],
    ) -> str:
        issue_summary = []
        if metrics.get("success_rate", 1.0) < 0.90:
            issue_summary.append("success_rate below target")
        if metrics.get("throughput", 0.0) < 35.0:
            issue_summary.append("throughput below target")
        if metrics.get("load_balance", 1.0) < 0.85:
            issue_summary.append("load balance drift")
        if metrics.get("retry_rate", 0.0) > 0.10:
            issue_summary.append("retry rate elevated")
        if metrics.get("confidence_trajectory", 1.0) < 0.95:
            issue_summary.append("confidence trajectory low")
        if anomalies:
            issue_summary.append(f"{len(anomalies)} anomalies detected")

        summary = ", ".join(issue_summary) if issue_summary else "metrics within target range"
        return f"Selected {strategy.value} because {summary}."
