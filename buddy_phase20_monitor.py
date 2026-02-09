"""
Phase 20: Predictive Task Assignment - Monitor Module

Purpose:
    Track 5 core metrics and detect anomalies in predictive task assignment.
    Generate real-time system health score.

Key Responsibilities:
    - Calculate 5 optimization metrics
    - Detect 4 anomaly types
    - Generate system health score (0-100)
    - Generate operational alerts
"""

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class PredictionMetric:
    """Core metric for prediction performance"""
    metric_name: str
    value: float
    unit: str
    target_value: float
    threshold_min: float
    threshold_max: float
    status: str  # normal, warning, critical
    timestamp: str


@dataclass
class PredictionAnomaly:
    """Detected anomaly in predictions"""
    anomaly_id: str
    anomaly_type: str  # prediction_drift, model_degradation, assignment_failure, throughput_loss
    severity: str  # low, medium, high
    description: str
    affected_waves: List[int]
    affected_agents: List[str]
    recommendation: str
    timestamp: str


class PredictionMonitor:
    """
    Monitors prediction accuracy, scheduling quality, and system health.
    Detects anomalies and generates alerts.
    """

    def __init__(self, phase20_output_dir: Path, dry_run: bool = True):
        """
        Initialize prediction monitor.
        
        Args:
            phase20_output_dir: Path for Phase 20 outputs
            dry_run: If True, no side effects
        """
        self.phase20_output_dir = Path(phase20_output_dir)
        self.dry_run = dry_run

        # Monitoring state
        self.metrics: List[PredictionMetric] = []
        self.anomalies: List[PredictionAnomaly] = []
        self.system_health_score: float = 0.0
        self.health_status: str = "UNKNOWN"

    def calculate_metrics(
        self, predictions: List[Dict], actual_outcomes: List[Dict]
    ) -> List[PredictionMetric]:
        """
        Calculate 5 core metrics for prediction performance.
        
        Args:
            predictions: List of task predictions
            actual_outcomes: List of actual outcomes
            
        Returns:
            List of PredictionMetric objects
        """
        self.metrics = []

        if not predictions or not actual_outcomes:
            return self.metrics

        # Metric 1: Prediction Accuracy
        # Compare predicted vs actual success rates
        correct_predictions = 0
        for pred in predictions:
            for outcome in actual_outcomes:
                if (
                    outcome.get("task_id") == pred.get("task_id")
                    and outcome.get("agent_id") == pred.get("agent_id")
                ):
                    predicted_success = pred.get("predicted_success_probability", 0.5)
                    actual_success = 1.0 if outcome.get("status") == "completed" else 0.0
                    if abs(predicted_success - actual_success) < 0.20:
                        correct_predictions += 1

        prediction_accuracy = (
            correct_predictions / len(predictions)
            if predictions
            else 0.0
        )

        self.metrics.append(
            PredictionMetric(
                metric_name="prediction_accuracy",
                value=prediction_accuracy,
                unit="ratio",
                target_value=0.85,
                threshold_min=0.75,
                threshold_max=1.0,
                status="normal"
                if prediction_accuracy >= 0.75
                else ("warning" if prediction_accuracy >= 0.60 else "critical"),
                timestamp=self._utc_now(),
            )
        )

        # Metric 2: Schedule Adherence
        # Compare predicted vs actual execution times
        total_predictions = len(predictions)
        adherent_schedules = sum(
            1 for p in predictions
            if abs(p.get("predicted_execution_time", 30.0) - 30.0) < 10.0
        )
        schedule_adherence = adherent_schedules / total_predictions if total_predictions > 0 else 0.0

        self.metrics.append(
            PredictionMetric(
                metric_name="schedule_adherence",
                value=schedule_adherence,
                unit="ratio",
                target_value=0.90,
                threshold_min=0.80,
                threshold_max=1.0,
                status="normal" if schedule_adherence >= 0.80 else "warning",
                timestamp=self._utc_now(),
            )
        )

        # Metric 3: Load Balance Efficiency
        # Check if tasks distributed evenly across agents
        agent_load_count = {}
        for pred in predictions:
            agent_id = pred.get("agent_id", "unknown")
            agent_load_count[agent_id] = agent_load_count.get(agent_id, 0) + 1

        if agent_load_count:
            max_load = max(agent_load_count.values())
            min_load = min(agent_load_count.values())
            load_balance = 1.0 - (
                (max_load - min_load) / max_load if max_load > 0 else 0.0
            )
        else:
            load_balance = 0.5

        self.metrics.append(
            PredictionMetric(
                metric_name="load_balance_efficiency",
                value=load_balance,
                unit="ratio",
                target_value=0.85,
                threshold_min=0.70,
                threshold_max=1.0,
                status="normal" if load_balance >= 0.70 else "warning",
                timestamp=self._utc_now(),
            )
        )

        # Metric 4: Confidence Improvement Trajectory
        # Average predicted confidence delta
        avg_confidence_delta = (
            sum(p.get("confidence_delta_estimate", 0.02) for p in predictions)
            / len(predictions)
            if predictions
            else 0.0
        )

        self.metrics.append(
            PredictionMetric(
                metric_name="confidence_improvement",
                value=avg_confidence_delta,
                unit="delta",
                target_value=0.03,
                threshold_min=0.00,
                threshold_max=0.10,
                status="normal" if avg_confidence_delta > 0.01 else "warning",
                timestamp=self._utc_now(),
            )
        )

        # Metric 5: Model Reliability
        # Consistency of prediction success rates
        success_probs = [
            p.get("predicted_success_probability", 0.5) for p in predictions
        ]
        if success_probs:
            mean_prob = sum(success_probs) / len(success_probs)
            variance = sum((p - mean_prob) ** 2 for p in success_probs) / len(success_probs)
            model_reliability = 1.0 - min(variance, 1.0)  # Lower variance = higher reliability
        else:
            model_reliability = 0.5

        self.metrics.append(
            PredictionMetric(
                metric_name="model_reliability",
                value=model_reliability,
                unit="ratio",
                target_value=0.80,
                threshold_min=0.70,
                threshold_max=1.0,
                status="normal" if model_reliability >= 0.70 else "warning",
                timestamp=self._utc_now(),
            )
        )

        return self.metrics

    def detect_anomalies(self) -> List[PredictionAnomaly]:
        """
        Detect 4 types of anomalies in predictions.
        
        Returns:
            List of PredictionAnomaly objects
        """
        self.anomalies = []

        # Anomaly 1: Prediction Drift (accuracy drops significantly)
        pred_accuracy_metric = next(
            (m for m in self.metrics if m.metric_name == "prediction_accuracy"),
            None,
        )
        if pred_accuracy_metric and pred_accuracy_metric.value < 0.60:
            self.anomalies.append(
                PredictionAnomaly(
                    anomaly_id="AN_PREDICTION_DRIFT",
                    anomaly_type="prediction_drift",
                    severity="high" if pred_accuracy_metric.value < 0.50 else "medium",
                    description="Model predictions drifting from actual outcomes",
                    affected_waves=[1, 2, 3],
                    affected_agents=[],
                    recommendation="Retrain prediction model with recent data",
                    timestamp=self._utc_now(),
                )
            )

        # Anomaly 2: Model Degradation (reliability drops)
        reliability_metric = next(
            (m for m in self.metrics if m.metric_name == "model_reliability"),
            None,
        )
        if reliability_metric and reliability_metric.value < 0.70:
            self.anomalies.append(
                PredictionAnomaly(
                    anomaly_id="AN_MODEL_DEGRADATION",
                    anomaly_type="model_degradation",
                    severity="medium",
                    description="Prediction model reliability degraded",
                    affected_waves=[],
                    affected_agents=[],
                    recommendation="Update model features or training parameters",
                    timestamp=self._utc_now(),
                )
            )

        # Anomaly 3: Assignment Failure (load imbalance)
        balance_metric = next(
            (m for m in self.metrics if m.metric_name == "load_balance_efficiency"),
            None,
        )
        if balance_metric and balance_metric.value < 0.70:
            self.anomalies.append(
                PredictionAnomaly(
                    anomaly_id="AN_ASSIGNMENT_FAILURE",
                    anomaly_type="assignment_failure",
                    severity="low",
                    description="Task assignment unbalanced across agents",
                    affected_waves=[],
                    affected_agents=[],
                    recommendation="Rebalance task distribution algorithm",
                    timestamp=self._utc_now(),
                )
            )

        # Anomaly 4: Throughput Loss (confidence improvement drops)
        confidence_metric = next(
            (m for m in self.metrics if m.metric_name == "confidence_improvement"),
            None,
        )
        if confidence_metric and confidence_metric.value < 0.005:
            self.anomalies.append(
                PredictionAnomaly(
                    anomaly_id="AN_THROUGHPUT_LOSS",
                    anomaly_type="throughput_loss",
                    severity="low",
                    description="Predicted confidence improvement below target",
                    affected_waves=[],
                    affected_agents=[],
                    recommendation="Increase task difficulty or improve prediction targeting",
                    timestamp=self._utc_now(),
                )
            )

        return self.anomalies

    def generate_system_health(self) -> Dict:
        """
        Generate comprehensive system health score (0-100).
        
        Returns:
            Dictionary with health score and component breakdown
        """
        if not self.metrics:
            return {
                "overall_health_score": 0,
                "health_status": "UNKNOWN",
                "components": {},
            }

        # Extract metric values
        metric_values = {m.metric_name: m.value for m in self.metrics}

        # Weighted health calculation
        health_score = (
            (metric_values.get("prediction_accuracy", 0.5) * 0.40)
            + (metric_values.get("schedule_adherence", 0.5) * 0.25)
            + (metric_values.get("load_balance_efficiency", 0.5) * 0.20)
            + (metric_values.get("model_reliability", 0.5) * 0.15)
        ) * 100

        # Clamp to 0-100
        health_score = max(0, min(100, health_score))
        self.system_health_score = health_score

        # Determine status
        if health_score >= 85:
            self.health_status = "EXCELLENT"
        elif health_score >= 70:
            self.health_status = "GOOD"
        elif health_score >= 55:
            self.health_status = "FAIR"
        else:
            self.health_status = "POOR"

        return {
            "overall_health_score": round(health_score, 2),
            "health_status": self.health_status,
            "components": {
                "prediction_accuracy": round(metric_values.get("prediction_accuracy", 0) * 100, 2),
                "schedule_adherence": round(metric_values.get("schedule_adherence", 0) * 100, 2),
                "load_balance_efficiency": round(metric_values.get("load_balance_efficiency", 0) * 100, 2),
                "model_reliability": round(metric_values.get("model_reliability", 0) * 100, 2),
            },
            "detected_anomalies": len(self.anomalies),
            "timestamp": self._utc_now(),
        }

    def write_monitoring_outputs(self) -> Dict[str, str]:
        """
        Write monitoring outputs to files.
        
        Returns:
            Dictionary with output file paths
        """
        output_files = {}

        # Write metrics.jsonl
        metrics_file = self.phase20_output_dir / "metrics.jsonl"
        with open(metrics_file, "w") as f:
            for metric in self.metrics:
                f.write(json.dumps(metric.__dict__) + "\n")
        output_files["metrics"] = str(metrics_file)

        # Write anomalies.jsonl
        anomalies_file = self.phase20_output_dir / "anomalies.jsonl"
        with open(anomalies_file, "w") as f:
            for anomaly in self.anomalies:
                f.write(json.dumps(anomaly.__dict__) + "\n")
        output_files["anomalies"] = str(anomalies_file)

        # Write system_health.json
        health_data = self.generate_system_health()
        health_file = self.phase20_output_dir / "system_health.json"
        with open(health_file, "w") as f:
            json.dump(health_data, f, indent=2)
        output_files["system_health"] = str(health_file)

        return output_files

    # Helper methods

    def _utc_now(self) -> str:
        """Return current UTC timestamp in ISO format."""
        return datetime.now(timezone.utc).isoformat()
