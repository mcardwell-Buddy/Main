"""
BUDDY PHASE 9 - SELF-REFLECTIVE HARNESS
======================================

Purpose:
- автономously run safe, dry-run workflow tests
- generate self-questions, answers, and confidence updates
- log observations without modifying Phase 1–8 code

Safety:
- No real tool execution
- Dry-run only
- High-risk steps require confidence >= 0.8 (simulated only)
"""

import argparse
import json
import random
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from buddy_dynamic_task_scheduler import (
    create_scheduler,
    TaskPriority,
    RiskLevel,
    ConditionalBranch,
    TaskStatus
)
from phase2_confidence import GradedConfidenceCalculator, ConfidenceFactors


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


class SelfReflectiveHarness:
    def __init__(self, output_dir: str = "outputs/phase9", seed: int = 7):
        self.root_output_dir = Path(output_dir)
        self.root_output_dir.mkdir(parents=True, exist_ok=True)

        self.self_questions_file = self.root_output_dir / "self_questions.jsonl"
        self.task_outcomes_file = self.root_output_dir / "task_outcomes.jsonl"
        self.confidence_updates_file = self.root_output_dir / "confidence_updates.jsonl"

        for filepath in [self.self_questions_file, self.task_outcomes_file, self.confidence_updates_file]:
            if filepath.exists():
                filepath.unlink()

        for wave_dir in self.root_output_dir.glob("wave_*"):
            if wave_dir.is_dir():
                for child in wave_dir.glob("*"):
                    if child.is_file():
                        child.unlink()

        self.random = random.Random(seed)
        self.confidence_calc = GradedConfidenceCalculator()

        self.scheduler = None
        self._reset_scheduler()

        self.processed_tasks = set()
        self.stats = {
            "total_tasks": 0,
            "completed": 0,
            "failed": 0,
            "deferred": 0,
            "flagged_for_review": 0
        }
        self.wave_stats: List[Dict[str, Any]] = []
        self.current_wave_dir: Optional[Path] = None

    def _reset_scheduler(self):
        self.scheduler = create_scheduler(enable_dry_run=True, max_concurrent_tasks=1)
        self._register_safe_actions()

    # ------------------------------------------------------------
    # Safe actions (no real web execution)
    # ------------------------------------------------------------
    def _register_safe_actions(self):
        def safe_action(name: str, risk: RiskLevel):
            def _action(**params):
                start = time.time()
                # Simulated latency
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

        def failing_action(**params):
            raise Exception("Simulated failure for Phase 9 testing")

        self.scheduler.register_action("web_inspect", safe_action("web_inspect", RiskLevel.LOW))
        self.scheduler.register_action("web_extract", safe_action("web_extract", RiskLevel.LOW))
        self.scheduler.register_action("web_click", safe_action("web_click", RiskLevel.MEDIUM))
        self.scheduler.register_action("web_fill", safe_action("web_fill", RiskLevel.MEDIUM))
        self.scheduler.register_action("high_risk_submit", safe_action("high_risk_submit", RiskLevel.HIGH))
        self.scheduler.register_action("failing_action", failing_action)

    # ------------------------------------------------------------
    # Workflow setup
    # ------------------------------------------------------------
    def _load_authoring_snapshot(self) -> Optional[List[Dict[str, Any]]]:
        snapshot_path = Path("frontend/public/workflow_snapshots.json")
        if not snapshot_path.exists():
            return None
        try:
            data = json.loads(snapshot_path.read_text(encoding="utf-8"))
            snapshots = data.get("snapshots", [])
            if not snapshots:
                return None
            return snapshots[0].get("workflow", {}).get("nodes", [])
        except Exception:
            return None

    def _seed_workflow(self, wave: int = 1):
        nodes = self._load_authoring_snapshot()
        workflow_id = "phase9_workflow"

        if nodes:
            def _normalize_enum(value: Optional[str], fallback: str):
                if not value:
                    return fallback
                return value.upper()

            def _safe_action_name(name: Optional[str]) -> str:
                if not name:
                    return "web_inspect"
                return name if name in self.scheduler.action_registry else "web_inspect"

            last_node_id = None
            for node in nodes:
                normalized_risk = RiskLevel[_normalize_enum(node.get("risk"), "LOW")]
                confidence_score = node.get("confidence", 0.7)
                if normalized_risk == RiskLevel.HIGH and confidence_score < 0.8:
                    confidence_score = min(confidence_score, 0.69)
                self.scheduler.add_task(
                    description=node.get("title", node.get("id")),
                    action_name=_safe_action_name(node.get("tool")),
                    action_params={},
                    priority=TaskPriority[_normalize_enum(node.get("priority"), "MEDIUM")],
                    risk_level=normalized_risk,
                    confidence_score=confidence_score,
                    dependencies=node.get("dependencies", []),
                    conditional_branches=[
                        ConditionalBranch(
                            condition_type="success",
                            next_task_id=branch.get("nextTaskId")
                        ) for branch in node.get("branches", [])
                    ],
                    metadata={"workflow_id": workflow_id, "source": "phase8"},
                    task_id=node.get("id")
                )
                last_node_id = node.get("id")

            base_dependency = [last_node_id] if last_node_id else []
            if wave >= 2:
                self.scheduler.add_task(
                    description="Snapshot follow-up extract",
                    action_name="web_extract",
                    action_params={"selector": ".details"},
                    priority=TaskPriority.MEDIUM,
                    risk_level=RiskLevel.LOW,
                    confidence_score=0.72,
                    dependencies=base_dependency,
                    metadata={"workflow_id": workflow_id, "wave": wave}
                )

            if wave >= 3:
                self.scheduler.add_task(
                    description="Snapshot follow-up click",
                    action_name="web_click",
                    action_params={"selector_or_text": "Learn more"},
                    priority=TaskPriority.MEDIUM,
                    risk_level=RiskLevel.MEDIUM,
                    confidence_score=0.66,
                    dependencies=base_dependency,
                    metadata={"workflow_id": workflow_id, "wave": wave}
                )

            if wave >= 4:
                self.scheduler.add_task(
                    description="Snapshot high risk submit",
                    action_name="high_risk_submit",
                    action_params={},
                    priority=TaskPriority.CRITICAL,
                    risk_level=RiskLevel.HIGH,
                    confidence_score=0.62,
                    dependencies=base_dependency,
                    metadata={"workflow_id": workflow_id, "wave": wave}
                )
            return

        # Fallback workflow
        task_a = self.scheduler.add_task(
            description="Inspect site",
            action_name="web_inspect",
            action_params={"url": "https://example.com"},
            priority=TaskPriority.HIGH,
            risk_level=RiskLevel.LOW,
            confidence_score=0.9,
            metadata={"workflow_id": workflow_id}
        )
        task_b = self.scheduler.add_task(
            description="Extract pricing",
            action_name="web_extract",
            action_params={"selector": ".pricing"},
            priority=TaskPriority.MEDIUM,
            risk_level=RiskLevel.LOW,
            confidence_score=0.75,
            dependencies=[task_a],
            conditional_branches=[
                ConditionalBranch(condition_type="success", next_task_template={
                    "description": "High risk submit",
                    "action_name": "high_risk_submit",
                    "action_params": {},
                    "priority": "HIGH",
                    "risk_level": "HIGH",
                    "confidence_score": 0.69
                })
            ],
            metadata={"workflow_id": workflow_id}
        )
        self.scheduler.add_task(
            description="Click plan",
            action_name="web_click",
            action_params={"selector_or_text": "Plan"},
            priority=TaskPriority.MEDIUM,
            risk_level=RiskLevel.MEDIUM,
            confidence_score=0.7,
            dependencies=[task_b],
            metadata={"workflow_id": workflow_id}
        )
        self.scheduler.add_task(
            description="Failure simulation",
            action_name="failing_action",
            action_params={},
            priority=TaskPriority.LOW,
            risk_level=RiskLevel.MEDIUM,
            confidence_score=0.6,
            dependencies=[task_b],
            metadata={"workflow_id": workflow_id}
        )

        if wave >= 2:
            self.scheduler.add_task(
                description="Fill signup form",
                action_name="web_fill",
                action_params={"selector": "#email", "value": "test@example.com"},
                priority=TaskPriority.MEDIUM,
                risk_level=RiskLevel.MEDIUM,
                confidence_score=0.65,
                dependencies=[task_b],
                metadata={"workflow_id": workflow_id, "wave": wave}
            )

        if wave >= 3:
            self.scheduler.add_task(
                description="Inspect pricing FAQ",
                action_name="web_inspect",
                action_params={"url": "https://example.com/faq"},
                priority=TaskPriority.LOW,
                risk_level=RiskLevel.LOW,
                confidence_score=0.8,
                dependencies=[task_b],
                metadata={"workflow_id": workflow_id, "wave": wave}
            )

        if wave >= 4:
            self.scheduler.add_task(
                description="High risk checkout",
                action_name="high_risk_submit",
                action_params={},
                priority=TaskPriority.CRITICAL,
                risk_level=RiskLevel.HIGH,
                confidence_score=0.62,
                dependencies=[task_b],
                metadata={"workflow_id": workflow_id, "wave": wave}
            )

    def _apply_safety_gates(self):
        for task in self.scheduler.tasks.values():
            if task.risk_level == RiskLevel.HIGH and task.confidence_score < 0.8:
                if task.status == TaskStatus.PENDING:
                    task.status = TaskStatus.DEFERRED
                    task.error = "Deferred: confidence below 0.8 for high-risk task"

    # ------------------------------------------------------------
    # Self-questioning and confidence updates
    # ------------------------------------------------------------
    def _generate_self_questions(self, task) -> List[str]:
        return [
            "Did the task complete successfully?",
            "Were dependencies satisfied before execution?",
            "Was the risk level respected?",
            "Is confidence aligned with outcome?",
        ]

    def _answer_questions(self, task, questions: List[str], wave: int) -> List[SelfQuestion]:
        answers = []
        for q in questions:
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

    # ------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------
    def _write_jsonl(self, path: Path, payload: Dict[str, Any]):
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")

    def _write_wave_jsonl(self, filename: str, payload: Dict[str, Any]):
        if not self.current_wave_dir:
            return
        path = self.current_wave_dir / filename
        self._write_jsonl(path, payload)

    # ------------------------------------------------------------
    # Harness main loop
    # ------------------------------------------------------------
    def run(self, waves: int = 1):
        for wave in range(1, waves + 1):
            self._reset_scheduler()
            self.processed_tasks = set()
            self._seed_workflow(wave=wave)
            self._apply_safety_gates()
            self.scheduler.start()

            self.current_wave_dir = self.root_output_dir / f"wave_{wave}"
            self.current_wave_dir.mkdir(parents=True, exist_ok=True)

            wave_stats = {
                "wave": wave,
                "total_tasks": 0,
                "completed": 0,
                "failed": 0,
                "deferred": 0,
                "success_rate": 0.0
            }

            while True:
                self._apply_safety_gates()
                for task in list(self.scheduler.tasks.values()):
                    if task.id in self.processed_tasks:
                        continue
                    if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.DEFERRED]:
                        self.processed_tasks.add(task.id)
                        self.stats["total_tasks"] += 1
                        wave_stats["total_tasks"] += 1
                        if task.status == TaskStatus.COMPLETED:
                            self.stats["completed"] += 1
                            wave_stats["completed"] += 1
                        elif task.status == TaskStatus.FAILED:
                            self.stats["failed"] += 1
                            wave_stats["failed"] += 1
                        elif task.status == TaskStatus.DEFERRED:
                            self.stats["deferred"] += 1
                            wave_stats["deferred"] += 1

                        # Self-questions
                        questions = self._generate_self_questions(task)
                        answers = self._answer_questions(task, questions, wave)
                        for answer in answers:
                            self._write_jsonl(self.self_questions_file, asdict(answer))
                            self._write_wave_jsonl("self_questions.jsonl", asdict(answer))

                        # Outcome logging
                        outcome = TaskOutcome(
                            task_id=task.id,
                            wave=wave,
                            workflow_id=task.metadata.get("workflow_id", "unknown"),
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
                        self._write_jsonl(self.task_outcomes_file, asdict(outcome))
                        self._write_wave_jsonl("task_outcomes.jsonl", asdict(outcome))

                        # Confidence update
                        update = self._update_confidence(task, wave)
                        self._write_jsonl(self.confidence_updates_file, asdict(update))
                        self._write_wave_jsonl("confidence_updates.jsonl", asdict(update))

                        if update.updated_confidence < 0.55:
                            self.stats["flagged_for_review"] += 1

                pending = [task for task in self.scheduler.tasks.values() if task.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS]]
                if not pending and len(self.processed_tasks) == len(self.scheduler.tasks):
                    break

                time.sleep(0.05)

            self.scheduler.stop()
            if wave_stats["total_tasks"]:
                wave_stats["success_rate"] = wave_stats["completed"] / wave_stats["total_tasks"]
            self.wave_stats.append(wave_stats)
            (self.current_wave_dir / "wave_metrics.json").write_text(
                json.dumps(wave_stats, indent=2),
                encoding="utf-8"
            )
            self.current_wave_dir = None

        self._write_report()

    def _write_report(self):
        report_path = self.root_output_dir / "PHASE_9_SELF_REFLECTIVE_REPORT.md"
        lines = [
            "# Phase 9 Self-Reflective Report",
            "",
            f"Generated: {datetime.utcnow().isoformat()}",
            "",
            f"Total tasks observed: {self.stats['total_tasks']}",
            f"Completed: {self.stats['completed']}",
            f"Failed: {self.stats['failed']}",
            f"Deferred: {self.stats['deferred']}",
            f"Flagged for review: {self.stats['flagged_for_review']}",
            "",
            "## Wave Statistics",
        ]

        for wave in self.wave_stats:
            lines.extend([
                f"- Wave {wave['wave']}: total={wave['total_tasks']}, "
                f"completed={wave['completed']}, failed={wave['failed']}, deferred={wave['deferred']}"
            ])

        lines.extend([
            "Recommendations:",
            "- Reorder low-confidence tasks earlier for validation.",
            "- Increase retries for medium-risk tasks with repeated failures.",
            "- Keep high-risk tasks in dry-run until confidence >= 0.8."
        ])
        report_path.write_text("\n".join(lines), encoding="utf-8")


def _parse_args():
    parser = argparse.ArgumentParser(description="Buddy Phase 9 Self-Reflective Harness")
    parser.add_argument("--wave-mode", action="store_true", help="Enable multi-wave execution")
    parser.add_argument("--waves", type=int, default=4, help="Number of waves to execute")
    parser.add_argument("--dry-run", action="store_true", help="Run in dry-run mode only")
    parser.add_argument("--output-dir", default="outputs/phase9", help="Output directory")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    harness = SelfReflectiveHarness(output_dir=args.output_dir)
    waves = args.waves if args.wave_mode else 1
    harness.run(waves=waves)
    print(f"Phase 9 complete. Logs saved to {harness.root_output_dir}")

