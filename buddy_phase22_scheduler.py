"""
Phase 22: Adaptive Scheduling Module

Purpose:
    Dynamically adjusts task assignments in real-time based on
    Phase 22 predictions, metrics, and failover strategies.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
import json


@dataclass
class Phase22TaskAssignment:
    """Task assignment for Phase 22 scheduling."""

    task_id: str
    agent_id: str
    wave: int
    priority: int
    predicted_success: float
    scheduled_time: str


@dataclass
class ScheduleAdjustment:
    """Represents a schedule adjustment or reassignment."""

    task_id: str
    from_agent: str
    to_agent: str
    reason: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class Phase22AdaptiveScheduler:
    """
    Adaptive scheduler supporting dynamic rebalancing and failover.
    """

    def __init__(self, phase22_output_dir: Path, dry_run: bool = True):
        """
        Initialize scheduler.

        Args:
            phase22_output_dir: Base output directory for Phase 22
            dry_run: If True, no side effects
        """
        self.phase22_output_dir = Path(phase22_output_dir)
        self.dry_run = dry_run
        self.adjustments: List[ScheduleAdjustment] = []

    def generate_initial_schedule(
        self, tasks: List[Dict], agents: List[str], wave: int
    ) -> Dict[str, List[Phase22TaskAssignment]]:
        """
        Generate initial schedule using round-robin with priority ordering.

        Args:
            tasks: List of task dictionaries
            agents: List of agent ids
            wave: Wave number

        Returns:
            Dict of agent_id -> list of Phase22TaskAssignment
        """
        assignments: Dict[str, List[Phase22TaskAssignment]] = {agent: [] for agent in agents}
        sorted_tasks = sorted(tasks, key=lambda t: t.get("priority", 1), reverse=True)
        agent_index = 0
        for task in sorted_tasks:
            agent_id = agents[agent_index % len(agents)]
            assignment = Phase22TaskAssignment(
                task_id=task["task_id"],
                agent_id=agent_id,
                wave=wave,
                priority=task.get("priority", 1),
                predicted_success=task.get("predicted_success", 0.9),
                scheduled_time=datetime.now(timezone.utc).isoformat(),
            )
            assignments[agent_id].append(assignment)
            agent_index += 1
        return assignments

    def rebalance_schedule(
        self, assignments: Dict[str, List[Phase22TaskAssignment]], agent_metrics: Dict[str, Dict[str, float]]
    ) -> Dict[str, List[Phase22TaskAssignment]]:
        """
        Rebalance schedule based on agent load and utilization.

        Args:
            assignments: Current assignments
            agent_metrics: Metrics per agent

        Returns:
            Updated assignments
        """
        loads = {agent: len(tasks) for agent, tasks in assignments.items()}
        if not loads:
            return assignments

        max_agent = max(loads, key=loads.get)
        min_agent = min(loads, key=loads.get)

        if loads[max_agent] - loads[min_agent] < 2:
            return assignments

        if assignments[max_agent]:
            task = assignments[max_agent].pop()
            assignments[min_agent].append(task)
            self.adjustments.append(
                ScheduleAdjustment(
                    task_id=task.task_id,
                    from_agent=max_agent,
                    to_agent=min_agent,
                    reason="load_rebalance",
                )
            )
        return assignments

    def apply_failover(
        self,
        failed_tasks: List[Phase22TaskAssignment],
        assignments: Dict[str, List[Phase22TaskAssignment]],
    ) -> Dict[str, List[Phase22TaskAssignment]]:
        """
        Reassign failed tasks to least loaded agent.

        Args:
            failed_tasks: List of failed task assignments
            assignments: Current assignments

        Returns:
            Updated assignments
        """
        if not assignments:
            return assignments

        for task in failed_tasks:
            loads = {agent: len(tasks) for agent, tasks in assignments.items()}
            target_agent = min(loads, key=loads.get)
            assignments[target_agent].append(task)
            self.adjustments.append(
                ScheduleAdjustment(
                    task_id=task.task_id,
                    from_agent=task.agent_id,
                    to_agent=target_agent,
                    reason="failover_reassignment",
                )
            )
        return assignments

    def write_adjusted_schedule(
        self, wave: int, assignments: Dict[str, List[Phase22TaskAssignment]]
    ) -> Dict[str, Optional[str]]:
        """
        Write adjusted schedule per agent.

        Returns:
            Dict of agent_id -> output path
        """
        outputs: Dict[str, Optional[str]] = {}
        for agent_id, tasks in assignments.items():
            agent_dir = self.phase22_output_dir / f"wave_{wave}" / agent_id
            agent_dir.mkdir(parents=True, exist_ok=True)
            schedule_path = agent_dir / "adjusted_schedule.jsonl"
            with open(schedule_path, "w", encoding="utf-8") as handle:
                for task in tasks:
                    payload = task.__dict__.copy()
                    payload["dry_run"] = self.dry_run
                    handle.write(json.dumps(payload) + "\n")
            outputs[agent_id] = str(schedule_path)
        return outputs

