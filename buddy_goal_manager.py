"""Buddy Phase 10 Goal Manager.

Generates high-level goals and task candidates, optionally seeded from
Phase 8 authoring snapshots. This module is additive and sandboxed.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class TaskSpec:
    task_id: str
    title: str
    tool: str
    priority: str
    risk: str
    confidence: float
    dependencies: List[str]
    branches: List[Dict[str, Any]]
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Goal:
    goal_id: str
    description: str
    tasks: List[TaskSpec]


class GoalManager:
    def __init__(self, seed: int = 42):
        self.random = random.Random(seed)

    def load_phase8_snapshot_tasks(self) -> List[TaskSpec]:
        snapshot_path = Path("frontend/public/workflow_snapshots.json")
        if not snapshot_path.exists():
            return []
        try:
            data = json.loads(snapshot_path.read_text(encoding="utf-8"))
            snapshots = data.get("snapshots", [])
            if not snapshots:
                return []
            nodes = snapshots[0].get("workflow", {}).get("nodes", [])
            tasks: List[TaskSpec] = []
            for node in nodes:
                tasks.append(
                    TaskSpec(
                        task_id=node.get("id", f"node_{len(tasks)}"),
                        title=node.get("title", node.get("id", "Task")),
                        tool=node.get("tool", "web_inspect"),
                        priority=str(node.get("priority", "MEDIUM")),
                        risk=str(node.get("risk", "LOW")),
                        confidence=float(node.get("confidence", 0.7)),
                        dependencies=list(node.get("dependencies", [])),
                        branches=list(node.get("branches", [])),
                        metadata={"source": "phase8"}
                    )
                )
            return tasks
        except Exception:
            return []

    def generate_goals(self, wave: int = 1) -> List[Goal]:
        tasks = self.load_phase8_snapshot_tasks()
        if tasks:
            tasks = self._expand_tasks_for_wave(tasks, wave)
            return [Goal(goal_id=f"goal_wave_{wave}", description="Snapshot-based goal", tasks=tasks)]

        # Fallback synthetic goals
        base_tasks = self._fallback_tasks()
        base_tasks = self._expand_tasks_for_wave(base_tasks, wave)
        return [Goal(goal_id=f"goal_wave_{wave}", description="Synthetic goal", tasks=base_tasks)]

    def _fallback_tasks(self) -> List[TaskSpec]:
        return [
            TaskSpec(
                task_id="seed_a",
                title="Inspect",
                tool="web_inspect",
                priority="HIGH",
                risk="LOW",
                confidence=0.85,
                dependencies=[],
                branches=[],
                metadata={"source": "phase10"}
            ),
            TaskSpec(
                task_id="seed_b",
                title="Extract",
                tool="web_extract",
                priority="MEDIUM",
                risk="LOW",
                confidence=0.72,
                dependencies=["seed_a"],
                branches=[{
                    "condition_type": "success",
                    "next_task_template": {
                        "task_id": "branch_high",
                        "title": "High risk submit",
                        "tool": "high_risk_submit",
                        "priority": "HIGH",
                        "risk": "HIGH",
                        "confidence": 0.62,
                        "dependencies": ["seed_b"],
                        "branches": []
                    }
                }],
                metadata={"source": "phase10"}
            )
        ]

    def _expand_tasks_for_wave(self, tasks: List[TaskSpec], wave: int) -> List[TaskSpec]:
        expanded = list(tasks)
        last_id = expanded[-1].task_id if expanded else "seed_a"

        if wave >= 2:
            expanded.append(
                TaskSpec(
                    task_id=f"wave{wave}_fill",
                    title="Fill signup form",
                    tool="web_fill",
                    priority="MEDIUM",
                    risk="MEDIUM",
                    confidence=0.65,
                    dependencies=[last_id],
                    branches=[],
                    metadata={"wave": wave}
                )
            )

        if wave >= 3:
            expanded.append(
                TaskSpec(
                    task_id=f"wave{wave}_click",
                    title="Click plan",
                    tool="web_click",
                    priority="MEDIUM",
                    risk="MEDIUM",
                    confidence=0.68,
                    dependencies=[last_id],
                    branches=[],
                    metadata={"wave": wave}
                )
            )

        if wave >= 4:
            expanded.append(
                TaskSpec(
                    task_id=f"wave{wave}_high",
                    title="High risk checkout",
                    tool="high_risk_submit",
                    priority="CRITICAL",
                    risk="HIGH",
                    confidence=0.62,
                    dependencies=[last_id],
                    branches=[],
                    metadata={"wave": wave}
                )
            )

        return expanded
