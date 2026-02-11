"""Buddy Phase 10 Simulated Executor.

Executes tasks in dry-run mode using Phase 6 scheduler and safe actions.
Generates self-questions, confidence updates, and task outcomes.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from buddy_dynamic_task_scheduler import (
    create_scheduler,
    TaskPriority,
    RiskLevel,
    ConditionalBranch,
    TaskStatus
)
from phase2_confidence import GradedConfidenceCalculator, ConfidenceFactors
from buddy_goal_manager import TaskSpec


@dataclass
class SelfQuestion:
    task_id: str
    wave: int
    question: str
    answer: str
    confidence: float
    timestamp: str


@dataclass
class TaskOutcome:
    task_id: str
    wave: int
    workflow_id: str
    status: str
    risk_level: str
    confidence_score: float
    retries: int
    execution_time_ms: float
    dry_run: bool
    error: Optional[str]
    observability: Dict[str, Any]
    timestamp: str


@dataclass
class ConfidenceUpdate:
    task_id: str
    wave: int
    previous_confidence: float
    updated_confidence: float
    delta: float
    reason: str
    timestamp: str


class SimulatedExecutor:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.confidence_calc = GradedConfidenceCalculator()
        self.scheduler = create_scheduler(enable_dry_run=True, max_concurrent_tasks=1)
        self._register_safe_actions()

    def _register_safe_actions(self):
        def safe_action(name: str, risk: RiskLevel):
            def _action(**params):
                start = time.time()
                time.sleep(0.02)
                return {
                    "success": True,
                    "dry_run": True,
                    "action": name,
                    "risk": risk.name,
                    "params": params,
                    "execution_time_ms": (time.time() - start) * 1000
                }
            return _action

        self.scheduler.register_action("web_inspect", safe_action("web_inspect", RiskLevel.LOW))
        self.scheduler.register_action("web_extract", safe_action("web_extract", RiskLevel.LOW))
        self.scheduler.register_action("web_click", safe_action("web_click", RiskLevel.MEDIUM))
        self.scheduler.register_action("web_fill", safe_action("web_fill", RiskLevel.MEDIUM))
        self.scheduler.register_action("high_risk_submit", safe_action("high_risk_submit", RiskLevel.HIGH))

    def _collect_observability_snapshot(self) -> Dict[str, Any]:
        queue_state_path = Path("outputs/task_scheduler_metrics/queue_state.json")
        timeline_path = Path("outputs/task_scheduler_metrics/task_execution_log.jsonl")
        snapshot = {
            "queue_state_found": queue_state_path.exists(),
            "timeline_found": timeline_path.exists(),
            "active_tasks": len(self.scheduler.active_tasks),
            "pending_tasks": sum(1 for t in self.scheduler.tasks.values() if t.status == TaskStatus.PENDING),
            "completed_tasks": sum(1 for t in self.scheduler.tasks.values() if t.status == TaskStatus.COMPLETED),
            "failed_tasks": sum(1 for t in self.scheduler.tasks.values() if t.status == TaskStatus.FAILED),
            "deferred_tasks": sum(1 for t in self.scheduler.tasks.values() if t.status == TaskStatus.DEFERRED),
        }
        if queue_state_path.exists():
            try:
                snapshot["queue_state"] = json.loads(queue_state_path.read_text(encoding="utf-8"))
            except Exception:
                snapshot["queue_state"] = {"error": "unreadable"}
        if timeline_path.exists():
            try:
                lines = timeline_path.read_text(encoding="utf-8").strip().splitlines()
                snapshot["timeline_tail"] = lines[-3:] if lines else []
            except Exception:
                snapshot["timeline_tail"] = ["error: unreadable"]
        return snapshot

    def _generate_self_questions(self) -> List[str]:
        return [
            "Did the task complete successfully?",
            "Were dependencies satisfied before execution?",
            "Was the risk level respected?",
            "Is confidence aligned with outcome?",
        ]

    def _answer_questions(self, task, wave: int) -> List[SelfQuestion]:
        answers = []
        for q in self._generate_self_questions():
            if "complete" in q.lower():
                answer = "yes" if task.status == TaskStatus.COMPLETED else "no"
            elif "dependencies" in q.lower():
                answer = "yes" if all(
                    self.scheduler.tasks.get(dep.task_id)
                    and self.scheduler.tasks[dep.task_id].status == dep.required_status
                    for dep in task.dependencies
                ) else "no"
            elif "risk" in q.lower():
                answer = "yes" if task.risk_level != RiskLevel.HIGH or task.confidence_score >= 0.8 else "no"
            else:
                answer = "aligned" if task.status == TaskStatus.COMPLETED and task.confidence_score >= 0.7 else "misaligned"

            confidence = 0.9 if answer in ["yes", "aligned"] else 0.6
            answers.append(SelfQuestion(
                task_id=task.id,
                wave=wave,
                question=q,
                answer=answer,
                confidence=confidence,
                timestamp=datetime.utcnow().isoformat()
            ))
        return answers

    def _update_confidence(self, task, wave: int) -> ConfidenceUpdate:
        previous = task.confidence_score
        success = task.status == TaskStatus.COMPLETED

        factors = ConfidenceFactors(
            goal_understanding=0.8,
            tool_availability=1.0,
            context_richness=0.7,
            tool_confidence=0.9 if success else 0.4
        )
        recalculated = self.confidence_calc.calculate(factors)
        if not success:
            recalculated = max(0.1, recalculated - 0.2)

        task.confidence_score = recalculated

        return ConfidenceUpdate(
            task_id=task.id,
            wave=wave,
            previous_confidence=previous,
            updated_confidence=recalculated,
            delta=recalculated - previous,
            reason="success" if success else "failure",
            timestamp=datetime.utcnow().isoformat()
        )

    def execute_wave(
        self,
        tasks: List[TaskSpec],
        wave: int,
        policy: Dict[str, Any],
        output_dir: Path,
        workflow_id: str = "phase10_workflow"
    ) -> Dict[str, Any]:
        self.scheduler.tasks.clear()
        self.scheduler.active_tasks.clear()

        deferred_specs: List[TaskSpec] = []
        deferred_ids: set[str] = set()
        deferred_reasons: Dict[str, str] = {}
        task_ids = {spec.task_id for spec in tasks}

        for spec in tasks:
            risk = RiskLevel[str(spec.risk).upper()]
            if risk == RiskLevel.HIGH and spec.confidence < policy.get("high_risk_threshold", 0.8):
                deferred_specs.append(spec)
                deferred_ids.add(spec.task_id)
                deferred_reasons[spec.task_id] = "Deferred: confidence below high-risk threshold"
                continue

        # Defer tasks whose dependencies are missing or deferred
        for spec in tasks:
            if spec.task_id in deferred_ids:
                continue
            missing_deps = [dep for dep in spec.dependencies if dep not in task_ids]
            blocked_deps = [dep for dep in spec.dependencies if dep in deferred_ids]
            if missing_deps or blocked_deps:
                deferred_specs.append(spec)
                deferred_ids.add(spec.task_id)
                reason = "Deferred: dependency missing" if missing_deps else "Deferred: dependency deferred"
                deferred_reasons[spec.task_id] = reason

        for spec in tasks:
            if spec.task_id in deferred_ids:
                continue
            risk = RiskLevel[str(spec.risk).upper()]
            priority = TaskPriority[str(spec.priority).upper()]
            self.scheduler.add_task(
                description=spec.title,
                action_name=spec.tool,
                action_params={},
                priority=priority,
                risk_level=risk,
                confidence_score=spec.confidence,
                dependencies=spec.dependencies,
                conditional_branches=[
                    ConditionalBranch(
                        condition_type=branch.get("condition_type", "success"),
                        next_task_id=branch.get("next_task_id"),
                        next_task_template=branch.get("next_task_template")
                    ) for branch in spec.branches
                ],
                metadata={"workflow_id": workflow_id, **spec.metadata},
                task_id=spec.task_id
            )

        self.scheduler.start()
        processed = set()

        outcomes: List[TaskOutcome] = []
        questions: List[SelfQuestion] = []
        confidence_updates: List[ConfidenceUpdate] = []

        # Log deferred specs immediately
        for spec in deferred_specs:
            outcome = TaskOutcome(
                task_id=spec.task_id,
                wave=wave,
                workflow_id=workflow_id,
                status="deferred",
                risk_level=str(spec.risk).upper(),
                confidence_score=spec.confidence,
                retries=0,
                execution_time_ms=0.0,
                dry_run=True,
                error=deferred_reasons.get(spec.task_id, "Deferred"),
                observability=self._collect_observability_snapshot(),
                timestamp=datetime.utcnow().isoformat()
            )
            outcomes.append(outcome)

        while True:
            for task in list(self.scheduler.tasks.values()):
                if task.id in processed:
                    continue
                if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.DEFERRED]:
                    processed.add(task.id)
                    answers = self._answer_questions(task, wave)
                    questions.extend(answers)
                    outcome = TaskOutcome(
                        task_id=task.id,
                        wave=wave,
                        workflow_id=task.metadata.get("workflow_id", workflow_id),
                        status=task.status.name.lower(),
                        risk_level=task.risk_level.name,
                        confidence_score=task.confidence_score,
                        retries=task.attempt_count,
                        execution_time_ms=task.metadata.get("execution_time_ms", 0.0),
                        dry_run=True,
                        error=task.error,
                        observability=self._collect_observability_snapshot(),
                        timestamp=datetime.utcnow().isoformat()
                    )
                    outcomes.append(outcome)

                    update = self._update_confidence(task, wave)
                    confidence_updates.append(update)

            pending = [task for task in self.scheduler.tasks.values() if task.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS]]
            if not pending and len(processed) == len(self.scheduler.tasks):
                break
            time.sleep(0.05)

        self.scheduler.stop()

        self._write_jsonl(output_dir / "self_questions.jsonl", [asdict(q) for q in questions])
        self._write_jsonl(output_dir / "task_outcomes.jsonl", [asdict(o) for o in outcomes])
        self._write_jsonl(output_dir / "confidence_updates.jsonl", [asdict(c) for c in confidence_updates])

        return {
            "questions": questions,
            "outcomes": outcomes,
            "confidence_updates": confidence_updates
        }

    def _write_jsonl(self, path: Path, payload: List[Dict[str, Any]]):
        with path.open("w", encoding="utf-8") as f:
            for item in payload:
                f.write(json.dumps(item) + "\n")

