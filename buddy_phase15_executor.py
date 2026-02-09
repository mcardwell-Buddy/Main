"""
Phase 15: Autonomous Task Executor

Executes tasks with real-time safety gate enforcement, confidence recalibration,
and complete observability. Integrates Phase 13 safety gates and Phase 14 heuristics.
"""

import json
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Tuple
from pathlib import Path
from enum import Enum
import random
import time


class ExecutionStatus(Enum):
    """Task execution status."""
    COMPLETED = "completed"
    FAILED = "failed"
    DEFERRED = "deferred"
    ROLLED_BACK = "rolled_back"


@dataclass
class TaskOutcome:
    """Outcome of task execution."""
    task_id: str
    wave: int
    status: ExecutionStatus
    risk_level: str
    confidence_before: float
    confidence_after: float
    confidence_delta: float
    safety_gate_status: str  # APPROVED, DEFERRED, REJECTED
    execution_time_ms: float
    error: str = None
    rollback_triggered: bool = False
    retries: int = 0


@dataclass
class ConfidenceUpdate:
    """Confidence before/after for a task."""
    task_id: str
    wave: int
    confidence_before: float
    confidence_after: float
    delta: float
    reason: str
    timestamp: str


class AutonomousExecutor:
    """Executes tasks autonomously with safety gates and observability."""

    def __init__(
        self,
        safety_gate,
        policy: Dict[str, Any],
        output_dir: str = "outputs/phase15",
        dry_run: bool = False,
    ):
        self.safety_gate = safety_gate
        self.policy = policy
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.dry_run = dry_run

        self.outcomes: List[TaskOutcome] = []
        self.confidence_updates: List[ConfidenceUpdate] = []
        self.wave_summary: Dict[str, Any] = {}

    def execute_wave(self, wave: int, tasks: List[Dict[str, Any]]) -> Tuple[List[TaskOutcome], Dict[str, Any]]:
        """Execute a complete wave of tasks."""
        self.outcomes = []
        self.confidence_updates = []

        completed = 0
        failed = 0
        deferred = 0
        rolled_back = 0

        for task in tasks:
            outcome = self._execute_task(wave, task)
            self.outcomes.append(outcome)

            if outcome.status == ExecutionStatus.COMPLETED:
                completed += 1
            elif outcome.status == ExecutionStatus.FAILED:
                failed += 1
            elif outcome.status == ExecutionStatus.DEFERRED:
                deferred += 1
            elif outcome.status == ExecutionStatus.ROLLED_BACK:
                rolled_back += 1

        # Build wave summary
        self.wave_summary = {
            "wave": wave,
            "total_tasks": len(tasks),
            "completed": completed,
            "failed": failed,
            "deferred": deferred,
            "rolled_back": rolled_back,
            "success_rate": completed / len(tasks) if tasks else 0.0,
            "avg_confidence_delta": sum(
                o.confidence_delta for o in self.outcomes
            ) / len(self.outcomes) if self.outcomes else 0.0,
        }

        return self.outcomes, self.wave_summary

    def _execute_task(self, wave: int, task: Dict[str, Any]) -> TaskOutcome:
        """Execute a single task with safety gate enforcement."""
        task_id = task.get("task_id", f"task_wave{wave}")
        risk_level = task.get("risk_level", "MEDIUM")
        confidence_before = task.get("confidence", 0.7)

        start_time = time.time()

        # Step 1: Evaluate safety gate
        safety_status, safety_reason = self.safety_gate.evaluate(
            task_id, risk_level, confidence_before, self.dry_run
        )

        if safety_status == "DEFERRED":
            execution_time = (time.time() - start_time) * 1000
            outcome = TaskOutcome(
                task_id=task_id,
                wave=wave,
                status=ExecutionStatus.DEFERRED,
                risk_level=risk_level,
                confidence_before=confidence_before,
                confidence_after=confidence_before,
                confidence_delta=-0.02,
                safety_gate_status="DEFERRED",
                execution_time_ms=execution_time,
                error=f"Deferred by safety gate: {safety_reason}",
            )
            self._record_confidence_update(
                task_id, wave, confidence_before, confidence_before, -0.02, f"Deferred: {safety_reason}"
            )
            return outcome

        elif safety_status == "REJECTED":
            execution_time = (time.time() - start_time) * 1000
            confidence_after = max(confidence_before - 0.15, 0.3)
            outcome = TaskOutcome(
                task_id=task_id,
                wave=wave,
                status=ExecutionStatus.FAILED,
                risk_level=risk_level,
                confidence_before=confidence_before,
                confidence_after=confidence_after,
                confidence_delta=-0.15,
                safety_gate_status="REJECTED",
                execution_time_ms=execution_time,
                error=f"Rejected by safety gate: {safety_reason}",
                rollback_triggered=True,
            )
            self._record_confidence_update(
                task_id, wave, confidence_before, confidence_after, -0.15, f"Rejected: {safety_reason}"
            )
            return outcome

        # Step 2: Execute task (approved)
        success = self._simulate_execution(task_id, risk_level, confidence_before)

        execution_time = (time.time() - start_time) * 1000

        if success:
            # Task completed successfully
            confidence_delta = 0.05 + (random.uniform(0, 0.03))
            confidence_after = min(confidence_before + confidence_delta, 0.99)

            outcome = TaskOutcome(
                task_id=task_id,
                wave=wave,
                status=ExecutionStatus.COMPLETED,
                risk_level=risk_level,
                confidence_before=confidence_before,
                confidence_after=confidence_after,
                confidence_delta=confidence_delta,
                safety_gate_status="APPROVED",
                execution_time_ms=execution_time,
                retries=0,
            )
            self._record_confidence_update(
                task_id, wave, confidence_before, confidence_after, confidence_delta, "Task completed successfully"
            )

        else:
            # Task failed
            rollback_prob = 0.8 if risk_level == "HIGH" else 0.5
            rollback_triggered = random.random() < rollback_prob

            confidence_delta = -0.1 if rollback_triggered else -0.05
            confidence_after = max(confidence_before + confidence_delta, 0.3)

            outcome = TaskOutcome(
                task_id=task_id,
                wave=wave,
                status=ExecutionStatus.ROLLED_BACK if rollback_triggered else ExecutionStatus.FAILED,
                risk_level=risk_level,
                confidence_before=confidence_before,
                confidence_after=confidence_after,
                confidence_delta=confidence_delta,
                safety_gate_status="APPROVED",
                execution_time_ms=execution_time,
                error="Task execution failed",
                rollback_triggered=rollback_triggered,
            )
            self._record_confidence_update(
                task_id,
                wave,
                confidence_before,
                confidence_after,
                confidence_delta,
                "Task failed" + (" with rollback" if rollback_triggered else ""),
            )

        return outcome

    def _simulate_execution(self, task_id: str, risk_level: str, confidence: float) -> bool:
        """Simulate task execution."""
        if self.dry_run:
            return True

        # Success probability based on risk and confidence
        success_rates = {"LOW": 0.92, "MEDIUM": 0.78, "HIGH": 0.62, "UNKNOWN": 0.70}
        base_rate = success_rates.get(risk_level, 0.70)
        adjusted_rate = base_rate * (0.5 + confidence)

        return random.random() < min(adjusted_rate, 0.99)

    def _record_confidence_update(
        self, task_id: str, wave: int, before: float, after: float, delta: float, reason: str
    ) -> None:
        """Record confidence update."""
        update = ConfidenceUpdate(
            task_id=task_id,
            wave=wave,
            confidence_before=before,
            confidence_after=after,
            delta=delta,
            reason=reason,
            timestamp=time.time(),
        )
        self.confidence_updates.append(update)

    def write_wave_outputs(self, wave: int) -> None:
        """Write wave execution outputs."""
        wave_dir = self.output_dir / f"wave_{wave}"
        wave_dir.mkdir(exist_ok=True)

        # Write outcomes
        with open(wave_dir / "task_outcomes.jsonl", "w") as f:
            for outcome in self.outcomes:
                outcome_dict = asdict(outcome)
                outcome_dict["status"] = outcome.status.value
                f.write(json.dumps(outcome_dict) + "\n")

        # Write confidence updates
        with open(wave_dir / "confidence_updates.jsonl", "w") as f:
            for update in self.confidence_updates:
                f.write(json.dumps(asdict(update)) + "\n")

        # Write wave summary
        with open(wave_dir / "wave_summary.json", "w") as f:
            json.dump(self.wave_summary, f, indent=2)

    def get_outcomes(self) -> List[TaskOutcome]:
        """Return all outcomes."""
        return self.outcomes

    def get_confidence_updates(self) -> List[ConfidenceUpdate]:
        """Return all confidence updates."""
        return self.confidence_updates

    def get_summary(self) -> Dict[str, Any]:
        """Return wave summary."""
        return self.wave_summary
