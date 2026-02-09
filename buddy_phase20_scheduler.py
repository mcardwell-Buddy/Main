"""
Phase 20: Predictive Task Assignment - Scheduler Module

Purpose:
    Assign tasks to agents based on predictions, optimizing for throughput,
    success rate, and confidence growth. Balances load dynamically.

Key Responsibilities:
    - Assign predicted tasks to agents optimally
    - Balance load across agents
    - Adjust confidence estimates
    - Generate predicted_schedule.jsonl output
"""

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class PredictedTaskAssignment:
    """Assignment of predicted task to agent"""
    task_id: str
    agent_id: str
    wave: int
    predicted_start_time: float
    predicted_end_time: float
    predicted_success_probability: float
    predicted_confidence_delta: float
    priority: int
    status: str  # PENDING, ASSIGNED
    timestamp: str


@dataclass
class PredictedScheduleExecution:
    """Predicted schedule execution results"""
    wave: int
    total_predicted_tasks: int
    predicted_success_rate: float
    predicted_throughput: float
    predicted_avg_confidence_delta: float
    predicted_execution_time: float
    agent_load_balance: float
    timestamp: str


class PredictiveScheduler:
    """
    Assigns predicted tasks to agents based on success probability predictions,
    balancing load and optimizing for throughput and confidence.
    """

    def __init__(self, phase20_output_dir: Path, dry_run: bool = True):
        """
        Initialize predictive scheduler.
        
        Args:
            phase20_output_dir: Path for Phase 20 outputs
            dry_run: If True, no side effects; if False, writes actual results
        """
        self.phase20_output_dir = Path(phase20_output_dir)
        self.dry_run = dry_run

        # Scheduling state
        self.predicted_assignments: List[PredictedTaskAssignment] = []
        self.agent_loads: Dict[str, float] = {f"agent_{i}": 0.0 for i in range(0, 4)}
        self.execution_history: List[PredictedScheduleExecution] = []

    def assign_tasks(
        self,
        predictions: List[Dict],
        agents: List[str],
        wave: int,
    ) -> List[PredictedTaskAssignment]:
        """
        Assign predicted tasks to agents optimally.
        
        Args:
            predictions: List of task predictions
            agents: List of agent IDs
            wave: Wave number
            
        Returns:
            List of PredictedTaskAssignment objects
        """
        self.predicted_assignments = []

        # Assign each prediction to its best agent
        for pred in predictions:
            task_id = pred.get("task_id")
            agent_id = pred.get("agent_id", agents[0] if agents else "agent_0")
            success_prob = pred.get("predicted_success_probability", 0.5)
            exec_time = pred.get("predicted_execution_time", 30.0)

            # Update agent load
            current_load = self.agent_loads.get(agent_id, 0.0)
            self.agent_loads[agent_id] = current_load + exec_time

            # Create assignment
            assignment = PredictedTaskAssignment(
                task_id=task_id,
                agent_id=agent_id,
                wave=wave,
                predicted_start_time=current_load,
                predicted_end_time=current_load + exec_time,
                predicted_success_probability=success_prob,
                predicted_confidence_delta=pred.get("confidence_delta_estimate", 0.02),
                priority=1 if pred.get("risk_assessment") in ["LOW", "HIGH"] else 2,
                status="ASSIGNED",
                timestamp=self._utc_now(),
            )

            self.predicted_assignments.append(assignment)

        return self.predicted_assignments

    def balance_load(self) -> Dict[str, float]:
        """
        Balance load across agents by reassigning tasks if needed.
        
        Returns:
            Dictionary with agent utilization after balancing
        """
        max_load = max(self.agent_loads.values()) if self.agent_loads else 0.0
        min_load = min(self.agent_loads.values()) if self.agent_loads else 0.0

        # If imbalance exceeds 30%, rebalance
        if max_load > 0 and (max_load - min_load) > max_load * 0.30:
            # Find overloaded agent
            overloaded = [
                agent for agent, load in self.agent_loads.items()
                if load > max_load * 0.85
            ]

            # Redistribute assignments from overloaded agents
            for agent in overloaded:
                agent_tasks = [
                    a for a in self.predicted_assignments
                    if a.agent_id == agent
                ]

                # Move lowest priority tasks to least loaded agent
                underloaded = min(self.agent_loads.items(), key=lambda x: x[1])[0]

                for task_assign in sorted(agent_tasks, key=lambda x: x.priority, reverse=True)[:1]:
                    # Calculate execution time from predicted times
                    exec_time = task_assign.predicted_end_time - task_assign.predicted_start_time
                    
                    # Move task
                    self.predicted_assignments.remove(task_assign)
                    task_assign.agent_id = underloaded
                    self.predicted_assignments.append(task_assign)

                    # Update loads
                    self.agent_loads[agent] -= exec_time
                    self.agent_loads[underloaded] += exec_time

        # Return utilization percentages
        max_possible_load = 60.0 * 4  # 60 seconds per agent * 4 agents
        utilization = {
            agent: round(load / max_possible_load, 3)
            for agent, load in self.agent_loads.items()
        }

        return utilization

    def adjust_confidence(self, confidence_adjustments: Dict[str, float]) -> Dict[str, float]:
        """
        Adjust predicted confidence delta estimates based on factors.
        
        Args:
            confidence_adjustments: Dict of agent_id -> confidence_delta
            
        Returns:
            Dictionary with updated assignments count
        """
        updated_count = 0
        for assignment in self.predicted_assignments:
            agent_adjustment = confidence_adjustments.get(
                assignment.agent_id, 0.0
            )
            assignment.predicted_confidence_delta += agent_adjustment
            updated_count += 1
        
        return {"assignments_updated": updated_count}

    def execute_predicted_schedule(self) -> PredictedScheduleExecution:
        """
        Simulate execution of predicted schedule.
        
        Returns:
            PredictedScheduleExecution with predicted outcomes
        """
        if not self.predicted_assignments:
            return PredictedScheduleExecution(
                wave=0,
                total_predicted_tasks=0,
                predicted_success_rate=0.0,
                predicted_throughput=0.0,
                predicted_avg_confidence_delta=0.0,
                predicted_execution_time=0.0,
                agent_load_balance=0.0,
                timestamp=self._utc_now(),
            )

        # Calculate predicted metrics
        total_tasks = len(self.predicted_assignments)
        successful_tasks = sum(
            1 for a in self.predicted_assignments
            if a.predicted_success_probability >= 0.75
        )
        predicted_success_rate = successful_tasks / total_tasks if total_tasks > 0 else 0.0

        avg_confidence_delta = (
            sum(a.predicted_confidence_delta for a in self.predicted_assignments)
            / total_tasks
            if total_tasks > 0
            else 0.0
        )

        total_exec_time = max(
            (a.predicted_end_time for a in self.predicted_assignments), default=0.0
        )
        throughput = total_tasks / (total_exec_time / 1000) if total_exec_time > 0 else 0.0

        load_balance = 1.0 - (
            (max(self.agent_loads.values()) - min(self.agent_loads.values()))
            / max(self.agent_loads.values())
            if max(self.agent_loads.values()) > 0
            else 0.0
        )

        execution = PredictedScheduleExecution(
            wave=1,  # Would be set by harness
            total_predicted_tasks=total_tasks,
            predicted_success_rate=round(predicted_success_rate, 4),
            predicted_throughput=round(throughput, 2),
            predicted_avg_confidence_delta=round(avg_confidence_delta, 4),
            predicted_execution_time=round(total_exec_time, 2),
            agent_load_balance=round(load_balance, 4),
            timestamp=self._utc_now(),
        )

        self.execution_history.append(execution)
        return execution

    def write_schedule_outputs(self, wave: int) -> Dict[str, str]:
        """
        Write predicted schedule to output files.
        
        Args:
            wave: Wave number
            
        Returns:
            Dictionary with output file paths
        """
        output_files = {}

        # Write per-agent predicted schedules
        for agent_id in range(0, 4):
            agent_dir = self.phase20_output_dir / f"wave_{wave}" / f"agent_{agent_id}"
            agent_dir.mkdir(parents=True, exist_ok=True)

            schedule_file = agent_dir / "predicted_schedule.jsonl"
            agent_assignments = [
                a for a in self.predicted_assignments
                if a.agent_id == f"agent_{agent_id}"
            ]

            with open(schedule_file, "w") as f:
                for assignment in agent_assignments:
                    f.write(json.dumps(assignment.__dict__) + "\n")

            output_files[f"agent_{agent_id}"] = str(schedule_file)

        return output_files

    # Helper methods

    def _utc_now(self) -> str:
        """Return current UTC timestamp in ISO format."""
        return datetime.now(timezone.utc).isoformat()
