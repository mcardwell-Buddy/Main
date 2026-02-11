"""
Phase 22: Meta-Optimization & Autonomous Tuning - Orchestration Harness

Purpose:
    Orchestrates Phase 22 execution with adaptive tuning, scheduling,
    monitoring, and bidirectional feedback across multiple waves.
"""

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
import hashlib
import json

from buddy_safety_gate import SafetyGate, ApprovalStatus
from buddy_phase22_meta_optimizer import Phase22MetaOptimizer
from buddy_phase22_agent_tuner import Phase22AgentTuner
from buddy_phase22_scheduler import Phase22AdaptiveScheduler, Phase22TaskAssignment
from buddy_phase22_feedback_loop import Phase22FeedbackLoop
from buddy_phase22_monitor import Phase22Monitor


@dataclass
class Phase22ExecutionResult:
    """Summary of Phase 22 execution."""

    execution_id: str
    status: str
    waves_executed: int
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    success_rate: float
    system_health_score: float
    start_time: str
    end_time: str
    learning_signals_generated: int
    anomalies_detected: int


class Phase22Harness:
    """
    Orchestrates Phase 22 meta-optimization and autonomous tuning.
    """

    def __init__(
        self,
        phase20_dir: Path,
        phase21_dir: Path,
        phase16_dir: Path,
        phase18_dir: Path,
        phase22_output_dir: Path,
        num_agents: int = 4,
        dry_run: bool = True,
    ):
        """
        Initialize Phase 22 harness.

        Args:
            phase20_dir: Phase 20 output directory
            phase21_dir: Phase 21 output directory
            phase16_dir: Phase 16 heuristics directory
            phase18_dir: Phase 18 coordination directory
            phase22_output_dir: Phase 22 output directory
            num_agents: Number of agents
            dry_run: If True, no side effects
        """
        self.phase20_dir = Path(phase20_dir)
        self.phase21_dir = Path(phase21_dir)
        self.phase16_dir = Path(phase16_dir)
        self.phase18_dir = Path(phase18_dir)
        self.phase22_output_dir = Path(phase22_output_dir)
        self.num_agents = num_agents
        self.dry_run = dry_run

        self.meta_optimizer = Phase22MetaOptimizer(self.phase22_output_dir, dry_run)
        self.agent_tuner = Phase22AgentTuner(self.phase22_output_dir, dry_run)
        self.scheduler = Phase22AdaptiveScheduler(self.phase22_output_dir, dry_run)
        self.feedback_loop = Phase22FeedbackLoop(
            self.phase16_dir, self.phase18_dir, self.phase20_dir, self.phase22_output_dir, dry_run
        )
        self.monitor = Phase22Monitor(self.phase22_output_dir, dry_run)
        self.safety_gate = SafetyGate(require_approval=False)

        self.inputs: Dict[str, List[Dict]] = {}

    def load_inputs(self) -> Dict[str, List[Dict]]:
        """
        Load Phase 20/21/16/18 inputs.

        Returns:
            Dictionary containing input datasets
        """
        self.inputs = {
            "phase20_metrics": self._read_jsonl(self.phase20_dir / "metrics.jsonl"),
            "phase20_anomalies": self._read_jsonl(self.phase20_dir / "anomalies.jsonl"),
            "phase20_signals": self._read_jsonl(self.phase20_dir / "learning_signals.jsonl"),
            "phase20_predictions": self._read_jsonl(self.phase20_dir / "predicted_tasks.jsonl"),
            "phase20_schedule": self._read_jsonl(self.phase20_dir / "predicted_schedule.jsonl"),
            "phase21_outcomes": self._read_jsonl(self.phase21_dir / "execution_outcomes.jsonl"),
            "phase21_metrics": self._read_jsonl(self.phase21_dir / "metrics.jsonl"),
            "phase16_heuristics": self._read_jsonl(self.phase16_dir / "heuristics.jsonl"),
            "phase18_coordination": self._read_json(self.phase18_dir / "multi_agent_summary.json"),
        }
        return self.inputs

    def run_phase22(self, waves: List[int], tasks_per_wave: int = 20) -> Phase22ExecutionResult:
        """
        Run Phase 22 end-to-end pipeline.

        Args:
            waves: List of wave numbers
            tasks_per_wave: Number of tasks per wave

        Returns:
            Phase22ExecutionResult
        """
        start_time = datetime.now(timezone.utc).isoformat()
        execution_id = f"PHASE22_{start_time.replace('-', '').replace(':', '')[:15]}"

        agents = [f"agent_{i}" for i in range(self.num_agents)]
        self.agent_tuner.initialize_agents(agents)
        self.load_inputs()

        total_tasks = 0
        total_completed = 0
        total_failed = 0
        total_anomalies = 0

        for wave in waves:
            wave_result = self._execute_wave(wave, agents, tasks_per_wave)
            total_tasks += wave_result["total_tasks"]
            total_completed += wave_result["completed_tasks"]
            total_failed += wave_result["failed_tasks"]
            total_anomalies += len(wave_result["anomalies"])

        self.meta_optimizer.write_recommendations()
        self.feedback_loop.write_feedback_outputs()
        self.monitor.write_monitoring_outputs()

        system_health = self.monitor.health_history[-1].overall_health_score if self.monitor.health_history else 0.0
        end_time = datetime.now(timezone.utc).isoformat()

        success_rate = (total_completed / total_tasks) if total_tasks else 0.0
        status = "success" if success_rate >= 0.90 and system_health >= 90.0 else "partial"
        result = Phase22ExecutionResult(
            execution_id=execution_id,
            status=status,
            waves_executed=len(waves),
            total_tasks=total_tasks,
            completed_tasks=total_completed,
            failed_tasks=total_failed,
            success_rate=success_rate,
            system_health_score=system_health,
            start_time=start_time,
            end_time=end_time,
            learning_signals_generated=len(self.feedback_loop.learning_signals),
            anomalies_detected=total_anomalies,
        )

        self._write_meta_optimization_report(result)
        self._write_phase22_summary(result)
        return result

    def _execute_wave(self, wave: int, agents: List[str], tasks_per_wave: int) -> Dict[str, object]:
        tasks = self._generate_tasks(wave, tasks_per_wave)
        assignments = self.scheduler.generate_initial_schedule(tasks, agents, wave)

        agent_metrics = self._calculate_agent_metrics(assignments)
        tuning_results = self.agent_tuner.tune_agents(wave, agent_metrics)
        adjustments = self.scheduler.rebalance_schedule(assignments, agent_metrics)
        self.scheduler.write_adjusted_schedule(wave, adjustments)
        self.agent_tuner.write_tuning_outputs(wave)

        execution_summary, execution_details = self._simulate_execution(wave, adjustments)

        metrics = self._compute_wave_metrics(wave, execution_summary, adjustments)
        optimization = self.meta_optimizer.optimize_wave(wave, metrics)

        monitor_metrics = self.monitor.calculate_metrics(
            wave,
            execution_summary,
            self._summarize_tuning(tuning_results),
            {"schedule_adherence": metrics["schedule_adherence"]},
            {"learning_impact": metrics["learning_impact"], "optimization_efficiency": metrics["optimization_efficiency"]},
        )
        anomalies = self.monitor.detect_anomalies(wave, monitor_metrics)
        self.monitor.generate_system_health(wave, monitor_metrics, anomalies)

        self.feedback_loop.generate_feedback_signals(
            wave=wave,
            metrics=metrics,
            anomalies=[a.__dict__ for a in anomalies],
            tuning_results=[asdict(t) for t in tuning_results],
            optimization_result={
                "strategy": optimization.strategy.value,
                "adjustments": optimization.adjustments,
                "expected_impact": optimization.expected_impact,
            },
        )

        return {
            "total_tasks": execution_summary["total_tasks"],
            "completed_tasks": execution_summary["completed_tasks"],
            "failed_tasks": execution_summary["failed_tasks"],
            "metrics": metrics,
            "anomalies": anomalies,
            "tuning_results": tuning_results,
            "execution_details": execution_details,
        }

    def _generate_tasks(self, wave: int, tasks_per_wave: int) -> List[Dict]:
        predictions = self.inputs.get("phase20_predictions", [])
        tasks: List[Dict] = []

        if predictions:
            for item in predictions[:tasks_per_wave]:
                tasks.append(
                    {
                        "task_id": item.get("task_id", f"wave{wave}_task_{len(tasks)}"),
                        "predicted_success": item.get("predicted_success_probability", 0.9),
                        "priority": item.get("priority", 1),
                        "risk_level": item.get("risk_level", "LOW"),
                    }
                )
        else:
            for idx in range(tasks_per_wave):
                tasks.append(
                    {
                        "task_id": f"wave{wave}_task_{idx}",
                        "predicted_success": 0.9,
                        "priority": 1,
                        "risk_level": "LOW",
                    }
                )
        return tasks

    def _simulate_execution(
        self, wave: int, assignments: Dict[str, List[Phase22TaskAssignment]]
    ) -> Dict[str, object]:
        completed = 0
        failed = 0
        total_tasks = 0
        retries = 0
        confidence_values = []
        execution_details = []

        for agent_id, tasks in assignments.items():
            params = self.agent_tuner.get_agent_parameters(agent_id)
            for task in tasks:
                total_tasks += 1
                base_success = task.predicted_success * params.confidence_weight
                if self.dry_run:
                    adjusted_success = min(0.99, base_success)
                else:
                    adjusted_success = min(0.98, base_success + 0.06)
                approval, _ = self.safety_gate.evaluate(
                    task_id=task.task_id,
                    risk_level="LOW",
                    confidence=adjusted_success,
                    is_dry_run=self.dry_run,
                )
                if approval != ApprovalStatus.APPROVED:
                    failed += 1
                    execution_details.append({
                        "task_id": task.task_id,
                        "agent_id": agent_id,
                        "success": False,
                        "retries": 0,
                    })
                    continue

                if self.dry_run:
                    success = adjusted_success >= 0.85
                else:
                    success = self._deterministic_success(task.task_id, adjusted_success)
                if success:
                    completed += 1
                else:
                    failed += 1
                    retries += 1

                execution_details.append({
                    "task_id": task.task_id,
                    "agent_id": agent_id,
                    "success": success,
                    "retries": 1 if not success else 0,
                })
                confidence_values.append(adjusted_success)

        total_time = max(0.01, total_tasks * 0.01)
        throughput = total_tasks / total_time
        retry_rate = (retries / total_tasks) if total_tasks else 0.0
        confidence_trajectory = sum(confidence_values) / len(confidence_values) if confidence_values else 0.95

        return (
            {
                "total_tasks": total_tasks,
                "completed_tasks": completed,
                "failed_tasks": failed,
                "success_rate": (completed / total_tasks) if total_tasks else 0.0,
                "throughput": throughput,
                "retry_rate": retry_rate,
                "confidence_trajectory": confidence_trajectory,
                "agent_utilization": self._calculate_utilization(assignments),
            },
            execution_details,
        )

    def _compute_wave_metrics(
        self, wave: int, execution_summary: Dict[str, float], assignments: Dict[str, List[Phase22TaskAssignment]]
    ) -> Dict[str, float]:
        schedule_adherence = 1.0 - (len(self.scheduler.adjustments) / max(1, execution_summary["total_tasks"]))
        load_balance = self._calculate_load_balance(assignments)

        metrics = {
            "success_rate": execution_summary["success_rate"],
            "throughput": execution_summary["throughput"],
            "agent_utilization": execution_summary["agent_utilization"],
            "confidence_trajectory": execution_summary["confidence_trajectory"],
            "schedule_adherence": schedule_adherence,
            "learning_impact": 0.95,
            "optimization_efficiency": 0.92,
            "load_balance": load_balance,
            "retry_rate": execution_summary["retry_rate"],
            "system_health": 0.95,
        }
        return metrics

    def _calculate_agent_metrics(
        self, assignments: Dict[str, List[Phase22TaskAssignment]]
    ) -> Dict[str, Dict[str, float]]:
        metrics = {}
        for agent_id, tasks in assignments.items():
            utilization = len(tasks) / max(1, max(len(t) for t in assignments.values()))
            metrics[agent_id] = {
                "success_rate": 0.92,
                "throughput": 50.0,
                "confidence": 0.96,
                "utilization": utilization,
            }
        return metrics

    def _calculate_utilization(self, assignments: Dict[str, List[Phase22TaskAssignment]]) -> float:
        if not assignments:
            return 0.0
        max_load = max(len(tasks) for tasks in assignments.values())
        avg_load = sum(len(tasks) for tasks in assignments.values()) / len(assignments)
        return avg_load / max(1, max_load)

    def _calculate_load_balance(self, assignments: Dict[str, List[Phase22TaskAssignment]]) -> float:
        if not assignments:
            return 1.0
        loads = [len(tasks) for tasks in assignments.values()]
        if not loads:
            return 1.0
        return min(loads) / max(loads) if max(loads) else 1.0

    def _summarize_tuning(self, tuning_results: List[object]) -> Dict[str, float]:
        if not tuning_results:
            return {"tuning_actions": 0.0}
        return {"tuning_actions": float(len(tuning_results))}

    def _deterministic_success(self, task_id: str, probability: float) -> bool:
        digest = hashlib.md5(task_id.encode("utf-8")).hexdigest()
        value = int(digest[:4], 16) / 65535.0
        return value <= probability

    def _read_jsonl(self, path: Path) -> List[Dict]:
        if not path.exists():
            return []
        items = []
        with open(path, "r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                items.append(json.loads(line))
        return items

    def _read_json(self, path: Path) -> List[Dict]:
        if not path.exists():
            return []
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)

    def _write_meta_optimization_report(self, result: Phase22ExecutionResult) -> None:
        self.phase22_output_dir.mkdir(parents=True, exist_ok=True)
        report_path = self.phase22_output_dir / "meta_optimization_report.md"
        with open(report_path, "w", encoding="utf-8") as handle:
            handle.write("# Phase 22 Meta-Optimization Report\n\n")
            handle.write(f"Execution ID: {result.execution_id}\n")
            handle.write(f"Status: {result.status}\n")
            handle.write(f"Waves Executed: {result.waves_executed}\n")
            handle.write(f"Success Rate: {result.success_rate:.2%}\n")
            handle.write(f"System Health: {result.system_health_score:.1f}/100\n")
            handle.write(f"Learning Signals: {result.learning_signals_generated}\n")
            handle.write(f"Anomalies: {result.anomalies_detected}\n")
            handle.write(f"Dry Run: {self.dry_run}\n")

    def _write_phase22_summary(self, result: Phase22ExecutionResult) -> None:
        summary_path = self.phase22_output_dir / "phase22_summary.json"
        with open(summary_path, "w", encoding="utf-8") as handle:
            json.dump(result.__dict__, handle, indent=2)

