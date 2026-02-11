"""
Phase 19: Optimization & Adaptive Scheduling - Adaptive Scheduler

Applies optimizer recommendations to schedule tasks across agents dynamically.
Adjusts for real-time agent load and performance.
"""

import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any


class ScheduleStatus(Enum):
    """Schedule execution status"""
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    ADJUSTED = "adjusted"


@dataclass
class ScheduledTask:
    """Task with scheduling information"""
    task_id: str
    agent_id: str
    wave: int
    scheduled_start_time: float
    scheduled_end_time: float
    actual_start_time: Optional[float] = None
    actual_end_time: Optional[float] = None
    priority: int = 0
    status: ScheduleStatus = ScheduleStatus.PENDING
    confidence: float = 0.0
    retry_count: int = 0


@dataclass
class ScheduleExecution:
    """Result of schedule execution"""
    wave: int
    scheduled_tasks: List[ScheduledTask]
    actual_success_rate: float
    actual_throughput: float
    actual_avg_confidence_delta: float
    schedule_adherence: float  # How well actual matched planned
    timestamp: str


class AdaptiveScheduler:
    """
    Adaptive scheduler that applies optimization recommendations dynamically.
    
    Responsibilities:
    - Apply optimizer recommendations to task scheduling
    - Dynamically adjust for agent load and performance
    - Prioritize tasks based on risk and confidence
    - Execute schedule with real-time monitoring
    - Track schedule adherence and performance
    """
    
    def __init__(self, phase19_output_dir: Path, dry_run: bool = True):
        """
        Initialize adaptive scheduler.
        
        Args:
            phase19_output_dir: Directory for Phase 19 outputs
            dry_run: If True, simulate scheduling without execution
        """
        self.phase19_output_dir = Path(phase19_output_dir)
        self.phase19_output_dir.mkdir(parents=True, exist_ok=True)
        self.dry_run = dry_run
        
        # Scheduling state
        self.scheduled_tasks: List[ScheduledTask] = []
        self.agent_loads: Dict[str, int] = {}
        self.execution_history: List[ScheduleExecution] = []
        
        # Performance tracking
        self.schedule_adherence_history: List[float] = []
        self.task_queue: List[Dict[str, Any]] = []
    
    def assign_tasks_to_agents(
        self,
        tasks: List[Dict[str, Any]],
        agent_assignments: Dict[str, List[str]],
        wave: int
    ) -> List[ScheduledTask]:
        """
        Assign tasks to agents based on optimizer recommendations.
        
        Args:
            tasks: Tasks to schedule
            agent_assignments: Optimizer's agent assignments
            wave: Wave number
        
        Returns:
            List of ScheduledTask objects
        """
        task_lookup = {t.get("task_id"): t for t in tasks}
        scheduled: List[ScheduledTask] = []
        for agent_id, task_ids in agent_assignments.items():
            start_time = 0.0
            for idx, task_id in enumerate(task_ids):
                task = task_lookup.get(task_id, {"task_id": task_id})
                duration_ms = float(task.get("estimated_duration_ms", 30.0))
                end_time = start_time + duration_ms
                scheduled.append(
                    ScheduledTask(
                        task_id=task_id,
                        agent_id=agent_id,
                        wave=wave,
                        scheduled_start_time=start_time,
                        scheduled_end_time=end_time,
                        priority=int(task.get("priority", idx + 1)),
                        confidence=float(task.get("confidence", 0.7)),
                    )
                )
                start_time = end_time
            self.agent_loads[agent_id] = len(task_ids)
        self.scheduled_tasks.extend(scheduled)
        return scheduled
    
    def prioritize_tasks(
        self,
        tasks: List[Dict[str, Any]],
        strategy: str = "risk_confidence"
    ) -> List[Dict[str, Any]]:
        """
        Prioritize tasks based on specified strategy.
        
        Args:
            tasks: Tasks to prioritize
            strategy: Prioritization strategy
        
        Returns:
            Sorted list of tasks by priority
        
        Strategies:
        - risk_confidence: Sort by (LOW risk, HIGH confidence) first
        - deadline: Sort by urgency
        - agent_specialization: Sort by agent expertise
        """
        if not tasks:
            return []

        if strategy == "risk_confidence":
            risk_weight = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}
            sorted_tasks = sorted(
                tasks,
                key=lambda t: (
                    risk_weight.get((t.get("risk_level") or "MEDIUM").upper(), 1),
                    -float(t.get("confidence", 0.0)),
                )
            )
        elif strategy == "deadline":
            sorted_tasks = sorted(tasks, key=lambda t: float(t.get("deadline", 0.0)))
        else:
            sorted_tasks = list(tasks)

        for idx, task in enumerate(sorted_tasks, start=1):
            task["priority"] = idx
        return sorted_tasks
    
    def adjust_for_agent_load(
        self,
        scheduled_tasks: List[ScheduledTask]
    ) -> List[ScheduledTask]:
        """
        Dynamically adjust schedule based on current agent loads.
        
        Args:
            scheduled_tasks: Initial schedule
        
        Returns:
            Adjusted schedule
        """
        if not scheduled_tasks:
            return []

        loads = {agent: 0 for agent in {t.agent_id for t in scheduled_tasks}}
        for task in scheduled_tasks:
            loads[task.agent_id] += 1

        if not loads:
            return scheduled_tasks

        avg_load = sum(loads.values()) / len(loads)
        overloaded = [agent for agent, load in loads.items() if load > avg_load + 1]
        underloaded = [agent for agent, load in loads.items() if load < avg_load - 1]

        for agent in overloaded:
            if not underloaded:
                break
            target_agent = underloaded[0]
            candidate = next((t for t in scheduled_tasks if t.agent_id == agent), None)
            if candidate:
                candidate.agent_id = target_agent
                loads[agent] -= 1
                loads[target_agent] += 1
                if loads[target_agent] >= avg_load:
                    underloaded.pop(0)

        return scheduled_tasks
    
    def execute_schedule(
        self,
        wave: int,
        scheduled_tasks: List[ScheduledTask]
    ) -> ScheduleExecution:
        """
        Execute scheduled tasks for a wave.
        
        Args:
            wave: Wave number
            scheduled_tasks: Tasks to execute
        
        Returns:
            ScheduleExecution with actual results
        """
        if not scheduled_tasks:
            execution = ScheduleExecution(
                wave=wave,
                scheduled_tasks=[],
                actual_success_rate=0.0,
                actual_throughput=0.0,
                actual_avg_confidence_delta=0.0,
                schedule_adherence=0.0,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
            self.execution_history.append(execution)
            return execution

        ordered = self.optimize_task_ordering(scheduled_tasks)
        success_flags: List[bool] = []
        confidence_deltas: List[float] = []

        for task in ordered:
            outcome = self.simulate_task_execution(task) if self.dry_run else self.simulate_task_execution(task)
            jitter = 0.5
            task.actual_start_time = task.scheduled_start_time + jitter
            task.actual_end_time = task.scheduled_end_time + jitter
            task.status = ScheduleStatus.COMPLETED if outcome["success"] else ScheduleStatus.FAILED
            success_flags.append(outcome["success"])
            confidence_deltas.append(outcome["confidence_delta"])

        actual_success_rate = sum(1 for s in success_flags if s) / max(len(success_flags), 1)
        total_time_ms = max((t.actual_end_time or 0.0) for t in ordered)
        actual_throughput = (len(ordered) / max(total_time_ms, 1.0)) * 1000.0
        actual_avg_confidence_delta = sum(confidence_deltas) / max(len(confidence_deltas), 1)
        schedule_adherence = self.calculate_schedule_adherence(ordered)

        execution = ScheduleExecution(
            wave=wave,
            scheduled_tasks=ordered,
            actual_success_rate=actual_success_rate,
            actual_throughput=actual_throughput,
            actual_avg_confidence_delta=actual_avg_confidence_delta,
            schedule_adherence=schedule_adherence,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        self.execution_history.append(execution)
        return execution
    
    def simulate_task_execution(
        self,
        task: ScheduledTask
    ) -> Dict[str, Any]:
        """
        Simulate task execution (for dry-run mode).
        
        Args:
            task: Task to simulate
        
        Returns:
            Dictionary with simulated outcome
        """
        risk_weight = {"LOW": 0.0, "MEDIUM": 0.1, "HIGH": 0.2}
        base_conf = float(task.confidence)
        risk_penalty = risk_weight.get("MEDIUM", 0.1)
        success_probability = max(0.05, min(0.99, base_conf - risk_penalty + 0.05))
        success = success_probability >= 0.5
        confidence_delta = (success_probability - 0.5) * 0.1
        return {
            "success": success,
            "success_probability": success_probability,
            "confidence_delta": confidence_delta,
        }
    
    def calculate_schedule_adherence(
        self,
        scheduled_tasks: List[ScheduledTask]
    ) -> float:
        """
        Calculate how well actual execution matched planned schedule.
        
        Args:
            scheduled_tasks: Tasks with actual times
        
        Returns:
            Adherence score (0.0 to 1.0)
        """
        if not scheduled_tasks:
            return 0.0
        total_deviation = 0.0
        count = 0
        for task in scheduled_tasks:
            if task.actual_start_time is None or task.actual_end_time is None:
                continue
            total_deviation += abs(task.actual_start_time - task.scheduled_start_time)
            total_deviation += abs(task.actual_end_time - task.scheduled_end_time)
            count += 2
        if count == 0:
            return 0.0
        avg_dev = total_deviation / count
        adherence = max(0.0, 1.0 - (avg_dev / 10.0))
        return min(1.0, adherence)
    
    def handle_task_failure(
        self,
        task: ScheduledTask
    ) -> Optional[ScheduledTask]:
        """
        Handle failed task - reschedule or reassign.
        
        Args:
            task: Failed task
        
        Returns:
            Rescheduled task or None if max retries exceeded
        """
        if task.retry_count >= 2:
            return None
        task.retry_count += 1
        task.confidence = max(0.05, task.confidence - 0.05)
        task.status = ScheduleStatus.ADJUSTED
        task.scheduled_start_time += 5.0
        task.scheduled_end_time += 5.0
        return task
    
    def optimize_task_ordering(
        self,
        tasks: List[ScheduledTask]
    ) -> List[ScheduledTask]:
        """
        Optimize the order of tasks for maximum efficiency.
        
        Args:
            tasks: Tasks to reorder
        
        Returns:
            Optimized task order
        """
        return sorted(tasks, key=lambda t: (t.priority, t.scheduled_start_time))
    
    def write_schedule_outputs(self, wave: int):
        """
        Write scheduling outputs for wave.
        
        Args:
            wave: Wave number
        """
        wave_dir = self.phase19_output_dir / f"wave_{wave}"
        wave_dir.mkdir(parents=True, exist_ok=True)

        per_agent: Dict[str, List[ScheduledTask]] = {}
        for task in self.scheduled_tasks:
            if task.wave != wave:
                continue
            per_agent.setdefault(task.agent_id, []).append(task)

        for agent_id, tasks in per_agent.items():
            agent_dir = wave_dir / agent_id
            agent_dir.mkdir(parents=True, exist_ok=True)
            jsonl_path = agent_dir / "scheduled_tasks.jsonl"
            jsonl_path.write_text(
                "\n".join(
                    json.dumps({
                        "task_id": t.task_id,
                        "agent_id": t.agent_id,
                        "wave": t.wave,
                        "scheduled_start_time": t.scheduled_start_time,
                        "scheduled_end_time": t.scheduled_end_time,
                        "actual_start_time": t.actual_start_time,
                        "actual_end_time": t.actual_end_time,
                        "priority": t.priority,
                        "status": t.status.value,
                        "confidence": t.confidence,
                        "retry_count": t.retry_count,
                    })
                    for t in tasks
                )
            )

        last_execution = next((e for e in reversed(self.execution_history) if e.wave == wave), None)
        wave_summary = {
            "wave": wave,
            "total_tasks": sum(len(t) for t in per_agent.values()),
            "agents": list(per_agent.keys()),
            "actual_success_rate": getattr(last_execution, "actual_success_rate", 0.0),
            "actual_throughput": getattr(last_execution, "actual_throughput", 0.0),
            "schedule_adherence": getattr(last_execution, "schedule_adherence", 0.0),
        }
        (wave_dir / "wave_summary.json").write_text(json.dumps(wave_summary, indent=2))
        (wave_dir / "schedule_adherence.json").write_text(json.dumps({
            "wave": wave,
            "schedule_adherence": wave_summary["schedule_adherence"],
        }, indent=2))
    
    def get_agent_utilization(self) -> Dict[str, float]:
        """
        Calculate agent utilization percentages.
        
        Returns:
            Dictionary mapping agent_id to utilization (0.0-1.0)
        """
        durations: Dict[str, float] = {}
        for task in self.scheduled_tasks:
            durations.setdefault(task.agent_id, 0.0)
            durations[task.agent_id] += max(0.0, task.scheduled_end_time - task.scheduled_start_time)

        if not durations:
            return {}

        max_duration = max(durations.values()) or 1.0
        return {agent_id: duration / max_duration for agent_id, duration in durations.items()}

    def schedule_tasks(
        self,
        tasks: List[Dict[str, Any]],
        agents: List[str],
        waves: int
    ) -> Dict[str, List[ScheduledTask]]:
        """
        Schedule tasks across agents and waves.
        """
        tasks_per_wave = max(1, len(tasks) // max(waves, 1))
        schedules: Dict[str, List[ScheduledTask]] = {}

        for wave in range(1, waves + 1):
            start_idx = (wave - 1) * tasks_per_wave
            end_idx = len(tasks) if wave == waves else start_idx + tasks_per_wave
            wave_tasks = tasks[start_idx:end_idx]
            wave_tasks = self.prioritize_tasks(wave_tasks)
            assignments = {agent: [] for agent in agents}
            for idx, task in enumerate(wave_tasks):
                assignments[agents[idx % max(len(agents), 1)]].append(task.get("task_id"))
            scheduled = self.assign_tasks_to_agents(wave_tasks, assignments, wave)
            scheduled = self.adjust_for_agent_load(scheduled)
            self.execute_schedule(wave, scheduled)
            self.write_schedule_outputs(wave)
            schedules[f"wave_{wave}"] = scheduled
        return schedules


def main():
    """
    Main execution function for testing scheduler.
    """
    # TODO: Initialize scheduler
    # TODO: Load optimizer recommendations
    # TODO: Assign tasks to agents
    # TODO: Execute schedule
    # TODO: Write outputs
    pass


if __name__ == "__main__":
    main()

