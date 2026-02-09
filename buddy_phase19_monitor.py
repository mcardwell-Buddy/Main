"""
Phase 19: Optimization & Adaptive Scheduling - Monitor

Monitors optimization and scheduling performance with real-time metrics
and anomaly detection.
"""

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any


@dataclass
class OptimizationMetric:
    """Real-time optimization metric"""
    metric_name: str
    value: float
    unit: str
    target_value: Optional[float]
    threshold_min: Optional[float]
    threshold_max: Optional[float]
    status: str  # "normal", "warning", "critical"
    timestamp: str


@dataclass
class SchedulingAnomaly:
    """Detected anomaly in scheduling"""
    anomaly_id: str
    anomaly_type: str  # "prediction_error", "schedule_drift", "performance_degradation"
    severity: str  # "low", "medium", "high"
    description: str
    affected_waves: List[int]
    affected_agents: List[str]
    recommendation: str
    timestamp: str


class OptimizationMonitor:
    """
    Real-time monitoring for optimization and scheduling performance.
    
    Responsibilities:
    - Track optimization KPIs
    - Monitor schedule execution
    - Detect scheduling anomalies
    - Calculate system health
    - Generate operational alerts
    """
    
    def __init__(self, phase19_output_dir: Path, monitor_output_dir: Path):
        """
        Initialize optimization monitor.
        
        Args:
            phase19_output_dir: Directory with Phase 19 outputs
            monitor_output_dir: Directory for monitoring outputs
        """
        self.phase19_output_dir = Path(phase19_output_dir)
        self.monitor_output_dir = Path(monitor_output_dir)
        self.monitor_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Monitoring state
        self.metrics: List[OptimizationMetric] = []
        self.anomalies: List[SchedulingAnomaly] = []
        
        # Health tracking
        self.system_health_score: float = 0.0

    def _utc_now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _read_jsonl(self, path: Path) -> List[Dict[str, Any]]:
        if not path.exists():
            return []
        items: List[Dict[str, Any]] = []
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))
        return items
    
    def calculate_metrics(self) -> List[OptimizationMetric]:
        """
        Calculate real-time optimization metrics.
        
        Returns:
            List of OptimizationMetric objects
        
        Metrics tracked:
        - schedule_accuracy: Predicted vs actual success rate
        - throughput_efficiency: Actual vs planned throughput
        - agent_utilization: Average agent utilization
        - confidence_trajectory: Confidence improvement rate
        - schedule_adherence: Schedule execution accuracy
        """
        comparisons = self._read_jsonl(self.phase19_output_dir / "schedule_comparisons.jsonl")
        if comparisons:
            schedule_accuracy = sum(c.get("accuracy_score", 0.0) for c in comparisons) / len(comparisons)
            throughput_efficiency = sum(
                (c.get("actual_throughput", 0.0) / max(c.get("planned_throughput", 1e-6), 1e-6))
                for c in comparisons
            ) / len(comparisons)
            confidence_trajectory = sum(
                (c.get("actual_confidence_delta", 0.0) / max(c.get("planned_confidence_delta", 1e-6), 1e-6))
                for c in comparisons
            ) / len(comparisons)
        else:
            schedule_accuracy = 0.0
            throughput_efficiency = 0.0
            confidence_trajectory = 0.0

        agent_util = self.monitor_agent_utilization()
        agent_utilization = sum(agent_util.values()) / max(len(agent_util), 1)

        schedule_adherence = 0.0
        adherence_file = self.phase19_output_dir / "schedule_adherence.json"
        if adherence_file.exists():
            schedule_adherence = json.loads(adherence_file.read_text()).get("schedule_adherence", 0.0)

        metrics = [
            OptimizationMetric(
                metric_name="schedule_accuracy",
                value=schedule_accuracy,
                unit="ratio",
                target_value=0.9,
                threshold_min=0.85,
                threshold_max=1.0,
                status="normal" if schedule_accuracy >= 0.9 else "warning" if schedule_accuracy >= 0.8 else "critical",
                timestamp=self._utc_now(),
            ),
            OptimizationMetric(
                metric_name="throughput_efficiency",
                value=throughput_efficiency,
                unit="ratio",
                target_value=0.95,
                threshold_min=0.85,
                threshold_max=1.0,
                status="normal" if throughput_efficiency >= 0.95 else "warning" if throughput_efficiency >= 0.85 else "critical",
                timestamp=self._utc_now(),
            ),
            OptimizationMetric(
                metric_name="agent_utilization",
                value=agent_utilization,
                unit="ratio",
                target_value=0.8,
                threshold_min=0.6,
                threshold_max=1.0,
                status="normal" if agent_utilization >= 0.8 else "warning" if agent_utilization >= 0.6 else "critical",
                timestamp=self._utc_now(),
            ),
            OptimizationMetric(
                metric_name="confidence_trajectory",
                value=confidence_trajectory,
                unit="ratio",
                target_value=1.0,
                threshold_min=0.9,
                threshold_max=1.1,
                status="normal" if confidence_trajectory >= 0.9 else "warning" if confidence_trajectory >= 0.8 else "critical",
                timestamp=self._utc_now(),
            ),
            OptimizationMetric(
                metric_name="schedule_adherence",
                value=schedule_adherence,
                unit="ratio",
                target_value=0.9,
                threshold_min=0.85,
                threshold_max=1.0,
                status="normal" if schedule_adherence >= 0.9 else "warning" if schedule_adherence >= 0.85 else "critical",
                timestamp=self._utc_now(),
            ),
        ]
        self.metrics = metrics
        return metrics
    
    def detect_anomalies(self) -> List[SchedulingAnomaly]:
        """
        Detect anomalies in optimization and scheduling.
        
        Returns:
            List of SchedulingAnomaly objects
        
        Anomaly types:
        - prediction_error: Large gap between predicted and actual
        - schedule_drift: Tasks not completing on schedule
        - performance_degradation: Success rate declining over waves
        - optimization_failure: Strategy not achieving goals
        """
        anomalies: List[SchedulingAnomaly] = []
        metric_map = {m.metric_name: m for m in self.metrics}

        if metric_map.get("schedule_accuracy") and metric_map["schedule_accuracy"].value < 0.85:
            anomalies.append(SchedulingAnomaly(
                anomaly_id="AN_PREDICTION_ERROR",
                anomaly_type="prediction_error",
                severity="high" if metric_map["schedule_accuracy"].value < 0.75 else "medium",
                description="Optimizer predictions deviate from actual outcomes",
                affected_waves=[],
                affected_agents=[],
                recommendation="Refine prediction model and adjust strategy weights",
                timestamp=self._utc_now(),
            ))

        if metric_map.get("schedule_adherence") and metric_map["schedule_adherence"].value < 0.85:
            anomalies.append(SchedulingAnomaly(
                anomaly_id="AN_SCHEDULE_DRIFT",
                anomaly_type="schedule_drift",
                severity="medium",
                description="Schedule adherence below threshold",
                affected_waves=[],
                affected_agents=[],
                recommendation="Increase scheduling buffers and load balancing",
                timestamp=self._utc_now(),
            ))

        if metric_map.get("throughput_efficiency") and metric_map["throughput_efficiency"].value < 0.85:
            anomalies.append(SchedulingAnomaly(
                anomaly_id="AN_PERFORMANCE_DEGRADATION",
                anomaly_type="performance_degradation",
                severity="medium",
                description="Throughput efficiency declining",
                affected_waves=[],
                affected_agents=[],
                recommendation="Rebalance task distribution to improve throughput",
                timestamp=self._utc_now(),
            ))

        if metric_map.get("schedule_accuracy") and metric_map.get("confidence_trajectory"):
            if metric_map["schedule_accuracy"].value < 0.8 and metric_map["confidence_trajectory"].value < 0.8:
                anomalies.append(SchedulingAnomaly(
                    anomaly_id="AN_OPTIMIZATION_FAILURE",
                    anomaly_type="optimization_failure",
                    severity="high",
                    description="Optimization strategy failing to improve metrics",
                    affected_waves=[],
                    affected_agents=[],
                    recommendation="Switch optimization strategy and recalibrate heuristics",
                    timestamp=self._utc_now(),
                ))

        self.anomalies = anomalies
        return anomalies
    
    def generate_system_health(self) -> Dict[str, Any]:
        """
        Calculate overall optimization system health (0-100).
        
        Returns:
            Dictionary with:
            - overall_health_score: 0-100 score
            - health_status: EXCELLENT/GOOD/FAIR/POOR
            - component_scores: Per-component scores
            - optimization_metrics: Key metrics
        """
        metric_map = {m.metric_name: m for m in self.metrics}
        accuracy_score = metric_map.get("schedule_accuracy").value * 100 if metric_map.get("schedule_accuracy") else 0.0
        adherence_score = metric_map.get("schedule_adherence").value * 100 if metric_map.get("schedule_adherence") else 0.0
        throughput_score = metric_map.get("throughput_efficiency").value * 100 if metric_map.get("throughput_efficiency") else 0.0
        stability_score = max(0.0, 100.0 - (len(self.anomalies) * 10.0))

        overall = (
            accuracy_score * 0.4
            + adherence_score * 0.3
            + throughput_score * 0.2
            + stability_score * 0.1
        )
        health_status = "EXCELLENT" if overall >= 85 else "GOOD" if overall >= 70 else "FAIR" if overall >= 55 else "POOR"
        self.system_health_score = overall

        return {
            "overall_health_score": round(overall, 2),
            "health_status": health_status,
            "component_scores": {
                "optimization_accuracy": round(accuracy_score, 2),
                "schedule_adherence": round(adherence_score, 2),
                "throughput_efficiency": round(throughput_score, 2),
                "system_stability": round(stability_score, 2),
            },
            "optimization_metrics": [
                {
                    "metric_name": m.metric_name,
                    "value": m.value,
                    "status": m.status,
                }
                for m in self.metrics
            ],
            "detected_anomalies": len(self.anomalies),
            "timestamp": self._utc_now(),
        }
    
    def monitor_agent_utilization(self) -> Dict[str, float]:
        """
        Monitor agent utilization across waves.
        
        Returns:
            Dictionary mapping agent_id to utilization percentage
        """
        durations: Dict[str, float] = {}
        for path in self.phase19_output_dir.glob("wave_*/agent_*/scheduled_tasks.jsonl"):
            for line in path.read_text().splitlines():
                if not line.strip():
                    continue
                data = json.loads(line)
                agent_id = data.get("agent_id")
                start = float(data.get("scheduled_start_time", 0.0))
                end = float(data.get("scheduled_end_time", 0.0))
                durations.setdefault(agent_id, 0.0)
                durations[agent_id] += max(0.0, end - start)

        if not durations:
            return {}

        max_duration = max(durations.values()) or 1.0
        return {agent_id: duration / max_duration for agent_id, duration in durations.items()}
    
    def detect_prediction_errors(self) -> Optional[SchedulingAnomaly]:
        """
        Detect systematic prediction errors in optimizer.
        
        Returns:
            SchedulingAnomaly if errors detected, None otherwise
        """
        metric_map = {m.metric_name: m for m in self.metrics}
        metric = metric_map.get("schedule_accuracy")
        if metric and metric.value < 0.85:
            return SchedulingAnomaly(
                anomaly_id="AN_PREDICTION_ERROR",
                anomaly_type="prediction_error",
                severity="medium" if metric.value >= 0.75 else "high",
                description="Prediction accuracy below threshold",
                affected_waves=[],
                affected_agents=[],
                recommendation="Refine optimizer prediction model",
                timestamp=self._utc_now(),
            )
        return None
    
    def detect_schedule_drift(self) -> Optional[SchedulingAnomaly]:
        """
        Detect when schedule execution drifts from plan.
        
        Returns:
            SchedulingAnomaly if drift detected, None otherwise
        """
        metric_map = {m.metric_name: m for m in self.metrics}
        metric = metric_map.get("schedule_adherence")
        if metric and metric.value < 0.85:
            return SchedulingAnomaly(
                anomaly_id="AN_SCHEDULE_DRIFT",
                anomaly_type="schedule_drift",
                severity="medium",
                description="Schedule adherence below threshold",
                affected_waves=[],
                affected_agents=[],
                recommendation="Increase scheduling buffers and rebalance load",
                timestamp=self._utc_now(),
            )
        return None
    
    def monitor_optimization_convergence(self) -> Dict[str, Any]:
        """
        Monitor if optimization is converging to better solutions.
        
        Returns:
            Dictionary with convergence metrics
        """
        comparisons = self._read_jsonl(self.phase19_output_dir / "schedule_comparisons.jsonl")
        comparisons = sorted(comparisons, key=lambda c: c.get("wave", 0))
        scores = [c.get("accuracy_score", 0.0) for c in comparisons]
        trend = "stable"
        if len(scores) >= 2:
            trend = "improving" if scores[-1] > scores[0] else "degrading" if scores[-1] < scores[0] else "stable"
        return {
            "accuracy_scores": scores,
            "trend": trend,
            "wave_count": len(scores),
        }
    
    def generate_alerts(self) -> List[Dict[str, str]]:
        """
        Generate operational alerts for critical issues.
        
        Returns:
            List of alert dictionaries
        """
        alerts: List[Dict[str, str]] = []
        for anomaly in self.anomalies:
            if anomaly.severity == "high":
                alerts.append({
                    "severity": "high",
                    "message": anomaly.description,
                    "recommendation": anomaly.recommendation,
                })
        if self.system_health_score and self.system_health_score < 70:
            alerts.append({
                "severity": "medium",
                "message": "System health below 70",
                "recommendation": "Review optimization strategy and scheduling",
            })
        return alerts
    
    def write_monitoring_outputs(self):
        """
        Write monitoring outputs to files.
        """
        metrics_path = self.phase19_output_dir / "metrics.jsonl"
        metrics_path.write_text("\n".join(
            json.dumps({
                "metric_name": m.metric_name,
                "value": m.value,
                "unit": m.unit,
                "target_value": m.target_value,
                "threshold_min": m.threshold_min,
                "threshold_max": m.threshold_max,
                "status": m.status,
                "timestamp": m.timestamp,
            })
            for m in self.metrics
        ))

        anomalies_path = self.phase19_output_dir / "anomalies.jsonl"
        anomalies_path.write_text("\n".join(
            json.dumps({
                "anomaly_id": a.anomaly_id,
                "anomaly_type": a.anomaly_type,
                "severity": a.severity,
                "description": a.description,
                "affected_waves": a.affected_waves,
                "affected_agents": a.affected_agents,
                "recommendation": a.recommendation,
                "timestamp": a.timestamp,
            })
            for a in self.anomalies
        ))

        health = self.generate_system_health()
        (self.phase19_output_dir / "system_health.json").write_text(json.dumps(health, indent=2))

        alerts = self.generate_alerts()
        (self.phase19_output_dir / "alerts.json").write_text(json.dumps(alerts, indent=2))


def main():
    """
    Main execution function for testing monitor.
    """
    # TODO: Initialize monitor
    # TODO: Calculate metrics
    # TODO: Detect anomalies
    # TODO: Generate health score
    # TODO: Write outputs
    pass


if __name__ == "__main__":
    main()
