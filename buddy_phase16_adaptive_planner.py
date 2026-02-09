"""
Phase 16: Adaptive Future Wave Planner

Plans future waves using learned heuristics, predicted confidence,
and optimized task sequences while respecting safety gates.
"""

import json
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional
from pathlib import Path
from enum import Enum
from datetime import datetime
import random


@dataclass
class PlannedTask:
    """Task planned for future execution."""
    task_id: str
    wave: int
    risk_level: str  # LOW, MEDIUM, HIGH
    confidence: float  # Initial confidence for this wave
    priority: int  # Execution priority (1=first)
    heuristics_applied: List[str]  # Which heuristics shaped this task
    predicted_success_rate: float
    predicted_confidence_delta: float
    approval_status: str  # APPROVED, DEFERRED, NEEDS_REVIEW
    reason: str


@dataclass
class SimulatedWaveOutcome:
    """Predicted outcome of a simulated wave."""
    wave: int
    planned_tasks: int
    predicted_completed: int
    predicted_failed: int
    predicted_deferred: int
    predicted_success_rate: float
    avg_confidence_improvement: float
    policy_adjustments: Dict[str, float]
    safety_concerns: List[str]


class AdaptiveWavePlanner:
    """Plans future waves using adaptive heuristics."""

    def __init__(
        self,
        meta_insights: List[Dict[str, Any]],
        heuristics: List[Dict[str, Any]],
        current_policy: Dict[str, float],
    ):
        self.meta_insights = meta_insights
        self.heuristics = heuristics
        self.current_policy = current_policy

        self.planned_tasks: List[PlannedTask] = []
        self.simulated_outcomes: List[SimulatedWaveOutcome] = []

    def plan_waves(self, num_waves: int = 3, tasks_per_wave: int = 4) -> None:
        """Plan multiple future waves."""
        for wave in range(1, num_waves + 1):
            self._plan_wave(wave, tasks_per_wave)

    def _plan_wave(self, wave: int, num_tasks: int) -> None:
        """Plan a single wave."""
        # Generate task specifications using heuristics
        tasks = []

        for task_num in range(1, num_tasks + 1):
            task = self._generate_task(wave, task_num)
            tasks.append(task)

        # Sort by priority
        tasks.sort(key=lambda t: t.priority)

        # Check safety gate compliance
        self._validate_safety_gates(tasks)

        # Simulate wave execution
        self._simulate_wave(wave, tasks)

        self.planned_tasks.extend(tasks)

    def _generate_task(self, wave: int, task_num: int) -> PlannedTask:
        """Generate a task specification."""
        # Use heuristics to determine risk/confidence distribution
        task_id = f"wave{wave}_task{task_num}"

        # Apply prioritization heuristic (H16_001)
        if task_num == 1:
            risk_level = "LOW"
            confidence = 0.88
            priority = 1
        elif task_num == 2:
            risk_level = "LOW"
            confidence = 0.80
            priority = 2
        elif task_num == 3:
            risk_level = "MEDIUM"
            confidence = 0.82
            priority = 3
        else:
            risk_level = "MEDIUM"
            confidence = 0.78
            priority = 4

        # Apply confidence elevation heuristic (H16_002) if applicable
        applied_heuristics = []
        if risk_level == "MEDIUM" and 0.70 <= confidence <= 0.75:
            confidence += 0.05
            applied_heuristics.append("H16_002")

        # Predict success based on risk/confidence
        predicted_success = self._predict_success(risk_level, confidence)
        predicted_delta = self._predict_confidence_delta(risk_level, predicted_success)

        # Determine approval status
        approval_status = self._evaluate_safety_gate(risk_level, confidence)

        task = PlannedTask(
            task_id=task_id,
            wave=wave,
            risk_level=risk_level,
            confidence=confidence,
            priority=priority,
            heuristics_applied=applied_heuristics,
            predicted_success_rate=predicted_success,
            predicted_confidence_delta=predicted_delta,
            approval_status=approval_status,
            reason=f"Task planned for wave {wave}",
        )

        return task

    def _predict_success(self, risk_level: str, confidence: float) -> float:
        """Predict success rate based on risk and confidence."""
        if risk_level == "LOW":
            return min(0.95, 0.70 + (confidence - 0.50) * 0.50)
        elif risk_level == "MEDIUM":
            return min(0.90, 0.60 + (confidence - 0.50) * 0.60)
        else:  # HIGH
            return min(0.85, 0.50 + (confidence - 0.50) * 0.70)

    def _predict_confidence_delta(
        self, risk_level: str, success_rate: float
    ) -> float:
        """Predict confidence delta based on expected outcome."""
        if success_rate >= 0.90:
            return 0.07 + random.uniform(-0.01, 0.02)
        elif success_rate >= 0.75:
            return 0.05 + random.uniform(-0.01, 0.01)
        elif success_rate >= 0.60:
            return 0.02 + random.uniform(-0.02, 0.01)
        else:
            return -0.03 + random.uniform(-0.02, 0.01)

    def _evaluate_safety_gate(self, risk_level: str, confidence: float) -> str:
        """Evaluate safety gate for task."""
        if risk_level == "LOW":
            if confidence >= 0.50:
                return "APPROVED"
            else:
                return "DEFERRED"
        elif risk_level == "MEDIUM":
            if confidence >= 0.75:
                return "APPROVED"
            elif confidence >= 0.50:
                return "DEFERRED"
            else:
                return "NEEDS_REVIEW"
        else:  # HIGH
            if confidence >= 0.90:
                return "APPROVED"
            elif confidence >= 0.75:
                return "DEFERRED"
            else:
                return "NEEDS_REVIEW"

    def _validate_safety_gates(self, tasks: List[PlannedTask]) -> None:
        """Validate all tasks pass safety gates."""
        for task in tasks:
            if task.approval_status == "NEEDS_REVIEW":
                # Flag high-risk recommendations
                task.reason += " [REQUIRES EXPLICIT APPROVAL]"

    def _simulate_wave(self, wave: int, tasks: List[PlannedTask]) -> None:
        """Simulate wave execution outcomes."""
        completed = 0
        failed = 0
        deferred = 0

        confidence_improvements = []

        for task in tasks:
            # Simulate based on predicted success
            if random.random() < task.predicted_success_rate:
                completed += 1
                confidence_improvements.append(task.predicted_confidence_delta)
            elif task.approval_status == "DEFERRED":
                deferred += 1
                confidence_improvements.append(-0.02)
            else:
                failed += 1
                confidence_improvements.append(-0.05)

        avg_improvement = (
            sum(confidence_improvements) / len(confidence_improvements)
            if confidence_improvements
            else 0
        )

        success_rate = completed / len(tasks) if tasks else 0

        # Determine policy adjustments for next wave
        policy_adjustments = self._recommend_policy_adjustments(success_rate)

        # Identify safety concerns
        safety_concerns = []
        if deferred > 1:
            safety_concerns.append(
                f"High deferral rate ({deferred}/{len(tasks)})"
            )
        if failed > 0:
            safety_concerns.append(f"{failed} task(s) predicted to fail")

        outcome = SimulatedWaveOutcome(
            wave=wave,
            planned_tasks=len(tasks),
            predicted_completed=completed,
            predicted_failed=failed,
            predicted_deferred=deferred,
            predicted_success_rate=success_rate,
            avg_confidence_improvement=avg_improvement,
            policy_adjustments=policy_adjustments,
            safety_concerns=safety_concerns,
        )

        self.simulated_outcomes.append(outcome)

    def _recommend_policy_adjustments(
        self, success_rate: float
    ) -> Dict[str, float]:
        """Recommend policy adjustments based on success rate."""
        adjustments = {}

        if success_rate >= 0.95:
            adjustments["priority_bias"] = self.current_policy.get(
                "priority_bias", 1.0
            ) * 1.1
        elif success_rate <= 0.70:
            adjustments["high_risk_threshold"] = min(
                0.95, self.current_policy.get("high_risk_threshold", 0.80) + 0.05
            )

        return adjustments

    def get_planned_tasks_for_wave(self, wave: int) -> List[PlannedTask]:
        """Get all tasks planned for a specific wave."""
        return [t for t in self.planned_tasks if t.wave == wave]

    def get_summary(self) -> Dict[str, Any]:
        """Get planning summary."""
        return {
            "total_waves_planned": len(self.simulated_outcomes),
            "total_tasks_planned": len(self.planned_tasks),
            "total_approved": sum(
                1 for t in self.planned_tasks if t.approval_status == "APPROVED"
            ),
            "total_deferred": sum(
                1 for t in self.planned_tasks if t.approval_status == "DEFERRED"
            ),
            "total_needs_review": sum(
                1
                for t in self.planned_tasks
                if t.approval_status == "NEEDS_REVIEW"
            ),
            "avg_predicted_success_rate": sum(
                o.predicted_success_rate for o in self.simulated_outcomes
            ) / len(self.simulated_outcomes) if self.simulated_outcomes else 0,
            "avg_confidence_improvement": sum(
                o.avg_confidence_improvement for o in self.simulated_outcomes
            ) / len(self.simulated_outcomes) if self.simulated_outcomes else 0,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }


def main():
    """Main planner."""
    # Example usage
    insights = [
        {
            "insight_type": "success_pattern",
            "description": "LOW risk 100% success",
            "confidence": 1.0,
        }
    ]

    heuristics = [
        {
            "heuristic_id": "H16_001",
            "category": "task_prioritization",
        }
    ]

    policy = {
        "high_risk_threshold": 0.80,
        "retry_multiplier": 1.0,
        "priority_bias": 1.0,
    }

    planner = AdaptiveWavePlanner(insights, heuristics, policy)
    planner.plan_waves(num_waves=3, tasks_per_wave=4)

    print("\n" + "=" * 70)
    print("ADAPTIVE WAVE PLANNING")
    print("=" * 70)
    print(f"\nPlanned {len(planner.planned_tasks)} tasks across {len(planner.simulated_outcomes)} waves")

    summary = planner.get_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")

    return planner


if __name__ == "__main__":
    main()
