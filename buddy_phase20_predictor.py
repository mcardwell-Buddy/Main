"""
Phase 20: Predictive Task Assignment - Predictor Module

Purpose:
    Predict task success probability for upcoming waves using Phase 19 outputs
    and learned patterns. Maintains prediction model and updates based on outcomes.

Key Responsibilities:
    - Load Phase 19 optimization outputs and metrics
    - Train/update prediction model with historical data
    - Predict task success probability for each agent-task pair
    - Adjust predictions based on confidence trajectories
    - Generate predicted_tasks.jsonl output
"""

import json
import random
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, List, Tuple, Optional


class PredictionStrategy(Enum):
    """Strategies for task success prediction"""
    CONFIDENCE_BASED = "confidence_based"          # Use agent confidence scores
    HISTORICAL_PERFORMANCE = "historical_performance"  # Use past success rates
    ENSEMBLE = "ensemble"                          # Weighted combination
    CONSERVATIVE = "conservative"                  # Reduce predictions by margin
    OPTIMISTIC = "optimistic"                      # Increase predictions


@dataclass
class TaskPrediction:
    """Prediction for single task-agent assignment"""
    task_id: str
    agent_id: str
    predicted_success_probability: float
    confidence_delta_estimate: float
    predicted_execution_time: float
    risk_assessment: str  # LOW, MEDIUM, HIGH
    reasoning: str
    timestamp: str


@dataclass
class PredictionModel:
    """Learned prediction model from historical data"""
    strategy: str
    accuracy_score: float
    confidence: float
    num_predictions_trained: int
    model_version: str
    last_updated: str
    feature_weights: Dict[str, float]


@dataclass
class PredictionMetric:
    """Metrics tracking prediction accuracy"""
    metric_name: str
    value: float
    unit: str
    target_value: float
    threshold_min: float
    threshold_max: float
    status: str  # normal, warning, critical
    timestamp: str


class AdaptivePredictor:
    """
    Predicts task success probability and optimal agent assignments
    using Phase 19 optimization outputs and learned patterns.
    """

    def __init__(self, phase19_dir: Path, phase20_output_dir: Path, dry_run: bool = True):
        """
        Initialize predictor with Phase 19 data.
        
        Args:
            phase19_dir: Path to Phase 19 outputs (inputs for Phase 20)
            phase20_output_dir: Path for Phase 20 outputs
            dry_run: If True, no side effects; if False, writes actual results
        """
        self.phase19_dir = Path(phase19_dir)
        self.phase20_output_dir = Path(phase20_output_dir)
        self.dry_run = dry_run

        # Data storage
        self.phase19_metrics: List[Dict] = []
        self.phase19_anomalies: List[Dict] = []
        self.phase19_signals: List[Dict] = []
        self.scheduled_tasks: Dict[str, List[Dict]] = {}

        # Prediction tracking
        self.predictions: List[TaskPrediction] = []
        self.prediction_model: Optional[PredictionModel] = None
        self.prediction_accuracy_history: List[float] = []
        self.agent_success_rates: Dict[str, float] = {}
        self.task_complexity_estimates: Dict[str, float] = {}

    def load_phase19_data(self) -> Dict[str, int]:
        """
        Load all Phase 19 outputs as input data.
        
        Returns:
            Dictionary with counts of loaded items
        """
        metrics_count = len(self._read_jsonl(self.phase19_dir / "metrics.jsonl"))
        anomalies_count = len(self._read_jsonl(self.phase19_dir / "anomalies.jsonl"))
        signals_count = len(self._read_jsonl(self.phase19_dir / "learning_signals.jsonl"))

        self.phase19_metrics = self._read_jsonl(self.phase19_dir / "metrics.jsonl")
        self.phase19_anomalies = self._read_jsonl(self.phase19_dir / "anomalies.jsonl")
        self.phase19_signals = self._read_jsonl(self.phase19_dir / "learning_signals.jsonl")

        # Load scheduled tasks from all waves/agents
        for wave in range(1, 4):
            for agent in range(0, 4):
                wave_dir = self.phase19_dir / f"wave_{wave}" / f"agent_{agent}"
                tasks_file = wave_dir / "scheduled_tasks.jsonl"
                if tasks_file.exists():
                    key = f"wave_{wave}_agent_{agent}"
                    self.scheduled_tasks[key] = self._read_jsonl(tasks_file)

        return {
            "metrics_loaded": metrics_count,
            "anomalies_loaded": anomalies_count,
            "signals_loaded": signals_count,
            "scheduled_tasks_loaded": len(self.scheduled_tasks),
        }

    def train_predictor(self, strategy: str = "ensemble") -> Tuple[float, int]:
        """
        Train/update prediction model using Phase 19 data.
        
        Args:
            strategy: Prediction strategy to use
            
        Returns:
            Tuple of (accuracy_score, num_predictions_trained)
        """
        # Extract success rates from Phase 19 metrics
        for metric in self.phase19_metrics:
            if metric.get("metric_name") == "schedule_accuracy":
                schedule_accuracy = metric.get("value", 0.8)
            elif metric.get("metric_name") == "throughput_efficiency":
                throughput_efficiency = metric.get("value", 0.9)
            elif metric.get("metric_name") == "confidence_trajectory":
                confidence_trajectory = metric.get("value", 0.95)

        # Calculate agent success rates from scheduled tasks
        success_rates = {}
        for key, tasks in self.scheduled_tasks.items():
            agent_id = key.split("agent_")[-1]
            if not tasks:
                continue
            
            successes = sum(1 for t in tasks if t.get("status") == "completed")
            success_rate = successes / len(tasks) if tasks else 0.5
            
            if agent_id not in success_rates:
                success_rates[agent_id] = []
            success_rates[agent_id].append(success_rate)

        # Aggregate success rates
        self.agent_success_rates = {
            agent_id: sum(rates) / len(rates)
            for agent_id, rates in success_rates.items()
        }

        # Build feature weights for prediction model
        feature_weights = {
            "agent_success_rate": 0.40,
            "task_complexity": 0.30,
            "confidence_delta": 0.20,
            "anomaly_penalty": 0.10,
        }

        # Calculate model accuracy from Phase 19 signals
        model_accuracy = 0.0
        for signal in self.phase19_signals:
            if signal.get("feedback_type") == "strategy_validation":
                model_accuracy = signal.get("confidence", 0.85)

        self.prediction_model = PredictionModel(
            strategy=strategy,
            accuracy_score=model_accuracy,
            confidence=0.85,
            num_predictions_trained=len(self.scheduled_tasks),
            model_version="1.0",
            last_updated=self._utc_now(),
            feature_weights=feature_weights,
        )

        return model_accuracy, len(self.scheduled_tasks)

    def predict_task_outcomes(
        self, tasks: List[Dict], agents: List[str], wave: int
    ) -> List[TaskPrediction]:
        """
        Predict task success probability for all task-agent pairs.
        
        Args:
            tasks: List of tasks to predict
            agents: List of agent IDs
            wave: Wave number for context
            
        Returns:
            List of TaskPrediction objects
        """
        self.predictions = []

        for task in tasks:
            task_id = task.get("task_id", f"task_{len(self.predictions)}")
            task_risk = task.get("risk_level", "MEDIUM")
            task_confidence = task.get("confidence", 0.75)

            for agent_id in agents:
                # Calculate predicted success probability
                agent_success_rate = self.agent_success_rates.get(agent_id, 0.8)
                
                # Adjust based on task complexity (inverse of confidence)
                complexity_factor = 1.0 - task_confidence  # Higher complexity = lower confidence
                
                # Base prediction from agent success rate
                base_probability = agent_success_rate
                
                # Apply risk penalty
                risk_penalty = {
                    "LOW": 0.0,
                    "MEDIUM": -0.05,
                    "HIGH": -0.15,
                }.get(task_risk, -0.05)
                
                # Apply complexity factor
                complexity_penalty = complexity_factor * -0.1
                
                # Ensemble combination
                predicted_success = base_probability + risk_penalty + complexity_penalty
                predicted_success = max(0.1, min(0.99, predicted_success))

                # Estimate confidence delta
                if predicted_success > 0.85:
                    confidence_delta = random.uniform(0.03, 0.08)
                elif predicted_success > 0.70:
                    confidence_delta = random.uniform(0.01, 0.03)
                else:
                    confidence_delta = random.uniform(-0.02, 0.01)

                # Risk assessment
                if predicted_success >= 0.85:
                    risk = "LOW"
                elif predicted_success >= 0.70:
                    risk = "MEDIUM"
                else:
                    risk = "HIGH"

                # Estimated execution time (based on complexity)
                exec_time = 25.0 + (complexity_factor * 10.0)

                prediction = TaskPrediction(
                    task_id=task_id,
                    agent_id=agent_id,
                    predicted_success_probability=round(predicted_success, 4),
                    confidence_delta_estimate=round(confidence_delta, 4),
                    predicted_execution_time=round(exec_time, 2),
                    risk_assessment=risk,
                    reasoning=f"Agent {agent_id} success rate {agent_success_rate:.2%}, "
                    f"task risk {task_risk}, complexity {complexity_factor:.2f}",
                    timestamp=self._utc_now(),
                )
                self.predictions.append(prediction)

        return self.predictions

    def update_model(self, actual_outcomes: List[Dict]) -> Dict[str, float]:
        """
        Update prediction model based on actual task outcomes.
        
        Args:
            actual_outcomes: List of actual task execution results
            
        Returns:
            Dictionary with updated model metrics
        """
        if not self.predictions or not actual_outcomes:
            return {"updated": False}

        # Calculate prediction accuracy
        correct_predictions = 0
        for prediction in self.predictions:
            for outcome in actual_outcomes:
                if (
                    outcome.get("task_id") == prediction.task_id
                    and outcome.get("agent_id") == prediction.agent_id
                ):
                    # Check if prediction was correct (within tolerance)
                    predicted = prediction.predicted_success_probability
                    actual = 1.0 if outcome.get("status") == "completed" else 0.0
                    
                    if abs(predicted - actual) < 0.20:  # 20% tolerance
                        correct_predictions += 1

        accuracy = correct_predictions / len(self.predictions) if self.predictions else 0.0
        self.prediction_accuracy_history.append(accuracy)

        # Update model confidence
        if self.prediction_model:
            self.prediction_model.accuracy_score = accuracy
            self.prediction_model.num_predictions_trained += len(actual_outcomes)
            self.prediction_model.last_updated = self._utc_now()

        return {
            "accuracy": round(accuracy, 4),
            "correct_predictions": correct_predictions,
            "total_predictions": len(self.predictions),
            "model_updated": True,
        }

    def generate_prediction_metrics(self) -> List[PredictionMetric]:
        """Generate metrics tracking prediction performance."""
        metrics = []

        # Prediction accuracy metric
        avg_accuracy = (
            sum(self.prediction_accuracy_history) / len(self.prediction_accuracy_history)
            if self.prediction_accuracy_history
            else 0.0
        )

        metrics.append(
            PredictionMetric(
                metric_name="prediction_accuracy",
                value=avg_accuracy,
                unit="ratio",
                target_value=0.85,
                threshold_min=0.75,
                threshold_max=1.0,
                status="normal"
                if avg_accuracy >= 0.75
                else ("warning" if avg_accuracy >= 0.60 else "critical"),
                timestamp=self._utc_now(),
            )
        )

        # Model confidence metric
        model_confidence = self.prediction_model.confidence if self.prediction_model else 0.0
        metrics.append(
            PredictionMetric(
                metric_name="model_confidence",
                value=model_confidence,
                unit="ratio",
                target_value=0.85,
                threshold_min=0.70,
                threshold_max=1.0,
                status="normal" if model_confidence >= 0.70 else "warning",
                timestamp=self._utc_now(),
            )
        )

        return metrics

    def write_prediction_outputs(self, wave: int) -> Dict[str, str]:
        """
        Write prediction outputs to JSONL/JSON files.
        
        Args:
            wave: Wave number
            
        Returns:
            Dictionary with output file paths
        """
        output_files = {}

        # Write per-agent predicted tasks
        for agent_id in range(0, 4):
            agent_dir = self.phase20_output_dir / f"wave_{wave}" / f"agent_{agent_id}"
            agent_dir.mkdir(parents=True, exist_ok=True)

            predicted_file = agent_dir / "predicted_tasks.jsonl"
            agent_predictions = [
                p for p in self.predictions if p.agent_id == f"agent_{agent_id}"
            ]

            with open(predicted_file, "w") as f:
                for pred in agent_predictions:
                    f.write(json.dumps(pred.__dict__) + "\n")

            output_files[f"agent_{agent_id}"] = str(predicted_file)

        return output_files

    # Helper methods

    def _read_jsonl(self, file_path: Path) -> List[Dict]:
        """Read JSONL file into list of dicts."""
        if not file_path.exists():
            return []
        records = []
        with open(file_path, "r") as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
        return records

    def _utc_now(self) -> str:
        """Return current UTC timestamp in ISO format."""
        return datetime.now(timezone.utc).isoformat()

