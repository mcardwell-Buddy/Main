"""
Phase 22: Monitoring Module

Purpose:
    Tracks metrics, detects anomalies, and generates system health scores
    for meta-optimization cycles across waves and agents.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
import json


@dataclass
class Phase22Metric:
    """Metric for Phase 22 performance tracking."""

    metric_name: str
    wave: int
    value: float
    unit: str
    target_value: float
    status: str  # normal, warning, critical
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class Phase22Anomaly:
    """Detected anomaly for Phase 22 monitoring."""

    anomaly_id: str
    anomaly_type: str  # high_failure, schedule_drift, confidence_drop, excessive_retries, optimization_failure
    severity: str  # low, medium, high
    description: str
    recommendation: str
    wave: int
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class Phase22SystemHealth:
    """System health snapshot for Phase 22."""

    wave: int
    overall_health_score: float
    health_status: str  # EXCELLENT, GOOD, FAIR, POOR
    metrics: Dict[str, float]
    anomaly_count: int
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class Phase22Monitor:
    """
    Monitoring and anomaly detection for Phase 22.
    """

    def __init__(self, phase22_output_dir: Path, dry_run: bool = True):
        """
        Initialize monitor.

        Args:
            phase22_output_dir: Output directory for Phase 22
            dry_run: If True, no side effects
        """
        self.phase22_output_dir = Path(phase22_output_dir)
        self.dry_run = dry_run
        self.metrics: List[Phase22Metric] = []
        self.anomalies: List[Phase22Anomaly] = []
        self.health_history: List[Phase22SystemHealth] = []

    def calculate_metrics(
        self,
        wave: int,
        execution_summary: Dict[str, float],
        tuning_summary: Dict[str, float],
        schedule_summary: Dict[str, float],
        optimization_summary: Dict[str, float],
    ) -> List[Phase22Metric]:
        """
        Calculate core Phase 22 metrics.

        Returns:
            List of Phase22Metric objects
        """
        metric_definitions = {
            "success_rate": (execution_summary.get("success_rate", 1.0), 0.90, "%"),
            "throughput": (execution_summary.get("throughput", 50.0), 35.0, "tasks/sec"),
            "agent_utilization": (execution_summary.get("agent_utilization", 1.0), 0.70, "ratio"),
            "confidence_trajectory": (execution_summary.get("confidence_trajectory", 1.0), 0.95, "ratio"),
            "schedule_adherence": (schedule_summary.get("schedule_adherence", 1.0), 0.95, "ratio"),
            "learning_impact": (optimization_summary.get("learning_impact", 0.95), 0.90, "ratio"),
            "optimization_efficiency": (optimization_summary.get("optimization_efficiency", 0.92), 0.90, "ratio"),
        }

        metrics: List[Phase22Metric] = []
        for name, (value, target, unit) in metric_definitions.items():
            status = "normal" if value >= target else "warning"
            metric = Phase22Metric(
                metric_name=name,
                wave=wave,
                value=value,
                unit=unit,
                target_value=target,
                status=status,
            )
            metrics.append(metric)
        self.metrics.extend(metrics)
        return metrics

    def detect_anomalies(self, wave: int, metrics: List[Phase22Metric]) -> List[Phase22Anomaly]:
        """
        Detect anomalies based on metrics.

        Returns:
            List of Phase22Anomaly objects
        """
        metric_map = {metric.metric_name: metric.value for metric in metrics}
        anomalies: List[Phase22Anomaly] = []

        if metric_map.get("success_rate", 1.0) < 0.90:
            anomalies.append(self._build_anomaly(wave, "high_failure", "Success rate below target", "Increase retries or reassign tasks", "high"))
        if metric_map.get("schedule_adherence", 1.0) < 0.95:
            anomalies.append(self._build_anomaly(wave, "schedule_drift", "Schedule adherence drift", "Rebalance schedule and enforce deadlines", "medium"))
        if metric_map.get("confidence_trajectory", 1.0) < 0.95:
            anomalies.append(self._build_anomaly(wave, "confidence_drop", "Confidence trajectory below target", "Recalibrate confidence weighting", "medium"))
        if metric_map.get("optimization_efficiency", 1.0) < 0.90:
            anomalies.append(self._build_anomaly(wave, "optimization_failure", "Optimization efficiency below target", "Review meta-optimization strategy", "high"))
        if metric_map.get("throughput", 50.0) < 35.0:
            anomalies.append(self._build_anomaly(wave, "excessive_retries", "Throughput degraded", "Reduce retries or increase parallelism", "low"))

        self.anomalies.extend(anomalies)
        return anomalies

    def generate_system_health(
        self, wave: int, metrics: List[Phase22Metric], anomalies: List[Phase22Anomaly]
    ) -> Phase22SystemHealth:
        """
        Generate overall system health score (0-100).
        """
        metric_map = {metric.metric_name: metric.value for metric in metrics}
        weights = {
            "success_rate": 0.30,
            "throughput": 0.15,
            "agent_utilization": 0.15,
            "confidence_trajectory": 0.15,
            "schedule_adherence": 0.10,
            "learning_impact": 0.10,
            "optimization_efficiency": 0.05,
        }
        score = 0.0
        for key, weight in weights.items():
            score += metric_map.get(key, 1.0) * weight
        score = max(0.0, min(1.0, score)) * 100

        if score >= 90:
            status = "EXCELLENT"
        elif score >= 75:
            status = "GOOD"
        elif score >= 60:
            status = "FAIR"
        else:
            status = "POOR"

        health = Phase22SystemHealth(
            wave=wave,
            overall_health_score=score,
            health_status=status,
            metrics=metric_map,
            anomaly_count=len(anomalies),
        )
        self.health_history.append(health)
        return health

    def write_monitoring_outputs(self) -> Dict[str, Optional[str]]:
        """
        Write monitoring outputs to Phase 22 directory.

        Returns:
            Dict with output paths
        """
        outputs = {"metrics": None, "anomalies": None, "system_health": None}
        self.phase22_output_dir.mkdir(parents=True, exist_ok=True)

        metrics_path = self.phase22_output_dir / "metrics.jsonl"
        with open(metrics_path, "w", encoding="utf-8") as handle:
            for metric in self.metrics:
                payload = metric.__dict__.copy()
                payload["dry_run"] = self.dry_run
                handle.write(json.dumps(payload) + "\n")
        outputs["metrics"] = str(metrics_path)

        anomalies_path = self.phase22_output_dir / "anomalies.jsonl"
        with open(anomalies_path, "w", encoding="utf-8") as handle:
            for anomaly in self.anomalies:
                payload = anomaly.__dict__.copy()
                payload["dry_run"] = self.dry_run
                handle.write(json.dumps(payload) + "\n")
        outputs["anomalies"] = str(anomalies_path)

        health_path = self.phase22_output_dir / "system_health.json"
        with open(health_path, "w", encoding="utf-8") as handle:
            json.dump([h.__dict__ for h in self.health_history], handle, indent=2)
        outputs["system_health"] = str(health_path)

        return outputs

    def _build_anomaly(
        self, wave: int, anomaly_type: str, description: str, recommendation: str, severity: str
    ) -> Phase22Anomaly:
        return Phase22Anomaly(
            anomaly_id=f"anomaly_{wave}_{anomaly_type}",
            anomaly_type=anomaly_type,
            severity=severity,
            description=description,
            recommendation=recommendation,
            wave=wave,
        )
