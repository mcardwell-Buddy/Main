"""
Phase 14: Wave Simulator

Simulates execution of planned task waves with confidence projections,
rollback modeling, and safety gate enforcement.
"""

import json
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Tuple
from pathlib import Path
from enum import Enum
import random


class ExecutionStatus(Enum):
    """Simulated execution status."""
    COMPLETED = "completed"
    FAILED = "failed"
    DEFERRED = "deferred"
    ROLLED_BACK = "rolled_back"


@dataclass
class SimulatedTaskOutcome:
    """Outcome of simulated task execution."""
    task_id: str
    wave: int
    planned_confidence: float
    risk_level: str
    status: ExecutionStatus
    projected_confidence: float
    confidence_delta: float
    rollback_probability: float
    rollback_triggered: bool
    predicted_execution_time_ms: float
    safety_gate_status: str  # APPROVED, DEFERRED, REJECTED
    reasoning: str
    meta_hints: List[str]


class WaveSimulator:
    """Simulates wave execution with confidence projections and rollback modeling."""

    def __init__(self, meta_engine, policy: Dict[str, Any], output_dir: str = "outputs/phase14"):
        self.meta_engine = meta_engine
        self.policy = policy
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        self.simulated_outcomes: List[SimulatedTaskOutcome] = []
        self.wave_summary: Dict[str, Any] = {}

    def simulate_wave(self, wave: int, tasks: List[Dict[str, Any]]) -> Tuple[List[SimulatedTaskOutcome], Dict[str, Any]]:
        """Simulate execution of a wave of tasks."""
        self.simulated_outcomes = []
        outcomes = []

        completed = 0
        failed = 0
        deferred = 0
        rolled_back = 0
        total_confidence_delta = 0.0

        for task in tasks:
            outcome = self._simulate_task(wave, task)
            outcomes.append(outcome)

            if outcome.status == ExecutionStatus.COMPLETED:
                completed += 1
            elif outcome.status == ExecutionStatus.FAILED:
                failed += 1
            elif outcome.status == ExecutionStatus.DEFERRED:
                deferred += 1
            elif outcome.status == ExecutionStatus.ROLLED_BACK:
                rolled_back += 1

            total_confidence_delta += outcome.confidence_delta

        self.simulated_outcomes = outcomes

        # Build wave summary
        self.wave_summary = {
            "wave": wave,
            "total_tasks": len(tasks),
            "completed": completed,
            "failed": failed,
            "deferred": deferred,
            "rolled_back": rolled_back,
            "success_rate": completed / len(tasks) if tasks else 0.0,
            "avg_confidence_delta": total_confidence_delta / len(tasks) if tasks else 0.0,
            "projected_next_wave_confidence": self._project_next_wave_confidence(outcomes),
        }

        return outcomes, self.wave_summary

    def _simulate_task(self, wave: int, task: Dict[str, Any]) -> SimulatedTaskOutcome:
        """Simulate a single task execution."""
        task_id = task.get("task_id", f"task_wave{wave}")
        risk_level = task.get("risk_level", "MEDIUM")
        confidence = task.get("confidence", 0.7)

        # Apply meta-learning heuristics
        heuristic_boost = self._apply_heuristics(task)
        adjusted_confidence = min(confidence + heuristic_boost, 0.99)

        # Evaluate safety gate
        safety_status, safety_reason = self._evaluate_safety_gate(task_id, risk_level, adjusted_confidence)

        # Determine execution status
        if safety_status == "DEFERRED":
            outcome = SimulatedTaskOutcome(
                task_id=task_id,
                wave=wave,
                planned_confidence=confidence,
                risk_level=risk_level,
                status=ExecutionStatus.DEFERRED,
                projected_confidence=confidence,
                confidence_delta=-0.02,
                rollback_probability=0.0,
                rollback_triggered=False,
                predicted_execution_time_ms=0.0,
                safety_gate_status="DEFERRED",
                reasoning=f"Safety gate deferral: {safety_reason}",
                meta_hints=[],
            )
        elif safety_status == "REJECTED":
            outcome = SimulatedTaskOutcome(
                task_id=task_id,
                wave=wave,
                planned_confidence=confidence,
                risk_level=risk_level,
                status=ExecutionStatus.FAILED,
                projected_confidence=max(confidence - 0.15, 0.3),
                confidence_delta=-0.15,
                rollback_probability=1.0,
                rollback_triggered=True,
                predicted_execution_time_ms=0.0,
                safety_gate_status="REJECTED",
                reasoning="Safety gate rejection: Insufficient confidence for risk level",
                meta_hints=["High risk without approval", "Consider deferral strategy"],
            )
        else:  # APPROVED
            # Simulate execution outcome
            success_probability = self._calculate_success_probability(adjusted_confidence, risk_level)
            is_success = random.random() < success_probability

            if is_success:
                # Task completed successfully
                confidence_delta = 0.05 + (heuristic_boost * 0.1)
                rollback_prob = 0.0
                execution_time = self._estimate_execution_time(risk_level)

                outcome = SimulatedTaskOutcome(
                    task_id=task_id,
                    wave=wave,
                    planned_confidence=confidence,
                    risk_level=risk_level,
                    status=ExecutionStatus.COMPLETED,
                    projected_confidence=min(adjusted_confidence + confidence_delta, 0.99),
                    confidence_delta=confidence_delta,
                    rollback_probability=rollback_prob,
                    rollback_triggered=False,
                    predicted_execution_time_ms=execution_time,
                    safety_gate_status="APPROVED",
                    reasoning="Task executed successfully within safety constraints",
                    meta_hints=[f"Success rate {success_probability*100:.1f}% for {risk_level} risk"],
                )
            else:
                # Task execution failed
                rollback_prob = 0.8 if risk_level == "HIGH" else 0.5
                rollback_triggered = random.random() < rollback_prob

                confidence_delta = -0.1 if rollback_triggered else -0.05
                new_confidence = max(adjusted_confidence + confidence_delta, 0.3)

                outcome = SimulatedTaskOutcome(
                    task_id=task_id,
                    wave=wave,
                    planned_confidence=confidence,
                    risk_level=risk_level,
                    status=ExecutionStatus.ROLLED_BACK if rollback_triggered else ExecutionStatus.FAILED,
                    projected_confidence=new_confidence,
                    confidence_delta=confidence_delta,
                    rollback_probability=rollback_prob,
                    rollback_triggered=rollback_triggered,
                    predicted_execution_time_ms=self._estimate_execution_time(risk_level),
                    safety_gate_status="APPROVED",
                    reasoning=f"Task failed - {'Rollback triggered' if rollback_triggered else 'Retry deferred'}",
                    meta_hints=[f"Failure rate {(1-success_probability)*100:.1f}% for {risk_level} risk"],
                )

        return outcome

    def _evaluate_safety_gate(self, task_id: str, risk_level: str, confidence: float) -> Tuple[str, str]:
        """Evaluate safety gate approval."""
        high_risk_threshold = self.policy.get("high_risk_threshold", 0.8)

        if risk_level == "LOW":
            if confidence >= 0.5:
                return "APPROVED", "LOW risk with sufficient confidence"
            else:
                return "DEFERRED", "Confidence below LOW risk threshold (0.5)"

        elif risk_level == "MEDIUM":
            if confidence >= 0.75:
                return "APPROVED", "MEDIUM risk with sufficient confidence"
            else:
                return "DEFERRED", "Confidence below MEDIUM risk threshold (0.75)"

        elif risk_level == "HIGH":
            if confidence >= 0.9:
                return "APPROVED", "HIGH risk with very high confidence"
            else:
                return "DEFERRED", f"Confidence below HIGH risk threshold ({high_risk_threshold})"

        else:  # UNKNOWN
            if confidence >= 0.7:
                return "APPROVED", "Confidence sufficient for UNKNOWN risk"
            else:
                return "DEFERRED", "Confidence below UNKNOWN risk threshold (0.7)"

    def _apply_heuristics(self, task: Dict[str, Any]) -> float:
        """Apply meta-learning heuristics to boost confidence."""
        boost = 0.0

        # Heuristic 1: Low-risk tasks get boost
        if task.get("risk_level") == "LOW":
            boost += 0.05

        # Heuristic 2: High-confidence tasks get boost
        if task.get("confidence", 0) >= 0.75:
            boost += 0.03

        # Heuristic 3: Check if task matches success patterns
        for heuristic in self.meta_engine.get_heuristics():
            if heuristic.applicability == "universal" or heuristic.applicability == f"{task.get('risk_level', 'UNKNOWN').lower()}_risk":
                boost += heuristic.recommended_weight * 0.02

        return min(boost, 0.15)  # Cap at 0.15

    def _calculate_success_probability(self, confidence: float, risk_level: str) -> float:
        """Calculate probability of successful execution."""
        base_success_rate = {
            "LOW": 0.9,
            "MEDIUM": 0.75,
            "HIGH": 0.6,
            "UNKNOWN": 0.65,
        }

        base_rate = base_success_rate.get(risk_level, 0.65)

        # Adjust based on confidence
        adjusted_rate = base_rate * (0.5 + confidence)  # Scale by confidence multiplier

        return min(adjusted_rate, 0.99)

    def _estimate_execution_time(self, risk_level: str) -> float:
        """Estimate execution time in milliseconds."""
        base_times = {
            "LOW": 20.0,
            "MEDIUM": 50.0,
            "HIGH": 100.0,
            "UNKNOWN": 75.0,
        }

        base_time = base_times.get(risk_level, 50.0)
        variance = random.uniform(0.8, 1.2)

        return base_time * variance

    def _project_next_wave_confidence(self, outcomes: List[SimulatedTaskOutcome]) -> float:
        """Project average confidence for next wave."""
        if not outcomes:
            return 0.7

        projections = [o.projected_confidence for o in outcomes]
        return sum(projections) / len(projections) if projections else 0.7

    def write_simulation_results(self, wave: int) -> None:
        """Write simulation results for wave."""
        wave_dir = self.output_dir / f"wave_{wave}"
        wave_dir.mkdir(exist_ok=True)

        # Write simulated outcomes
        with open(wave_dir / "simulated_outcomes.jsonl", "w") as f:
            for outcome in self.simulated_outcomes:
                outcome_dict = asdict(outcome)
                outcome_dict["status"] = outcome.status.value
                f.write(json.dumps(outcome_dict) + "\n")

        # Write wave summary
        with open(wave_dir / "wave_summary.json", "w") as f:
            json.dump(self.wave_summary, f, indent=2)

    def get_outcomes(self) -> List[SimulatedTaskOutcome]:
        """Return all simulated outcomes."""
        return self.simulated_outcomes

    def get_summary(self) -> Dict[str, Any]:
        """Return wave summary."""
        return self.wave_summary

