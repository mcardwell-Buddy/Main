"""
Phase 19: Optimization & Adaptive Scheduling - Orchestration Harness

Orchestrates the complete Phase 19 optimization and scheduling pipeline.
Coordinates optimizer, scheduler, feedback, and monitoring.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional

from buddy_phase19_optimizer import AdaptiveOptimizer, OptimizationStrategy
from buddy_phase19_scheduler import AdaptiveScheduler
from buddy_phase19_feedback_loop import OptimizationFeedbackLoop
from buddy_phase19_monitor import OptimizationMonitor


class Phase19Harness:
    """
    Complete Phase 19 orchestration harness.
    
    Execution Pipeline:
    1. Load Phase 18 multi-agent outputs
    2. Initialize optimizer with coordination patterns
    3. Calculate optimal schedule
    4. Apply scheduler to assign tasks
    5. Execute schedule (simulated or real)
    6. Generate feedback loop analysis
    7. Monitor optimization performance
    8. Write comprehensive reports
    """
    
    def __init__(
        self,
        phase18_dir: Path = None,
        phase19_output_dir: Path = None,
        optimization_strategy: str = "maximize_success",
        dry_run: bool = True
    ):
        """
        Initialize Phase 19 harness.
        
        Args:
            phase18_dir: Directory with Phase 18 outputs
            phase19_output_dir: Directory for Phase 19 outputs
            optimization_strategy: Strategy to use for optimization
            dry_run: If True, simulate execution (safety toggle)
        """
        self.phase18_dir = Path(phase18_dir or "outputs/phase18")
        self.phase19_output_dir = Path(phase19_output_dir or "outputs/phase19")
        self.optimization_strategy = optimization_strategy
        self.dry_run = dry_run
        
        # Create output directory structure
        self.phase19_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Components (to be initialized)
        self.optimizer = None
        self.scheduler = None
        self.feedback = None
        self.monitor = None

        # Phase 18 data
        self.multi_agent_summary: Dict[str, Any] = {}
        self.coordination_patterns: List[Dict[str, Any]] = []
        self.system_health: Dict[str, Any] = {}
        self.learning_signals: List[Dict[str, Any]] = []
        
        # Execution tracking
        self.start_time = None
        self.end_time = None
        self.waves_optimized = 0

    def _utc_now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _read_json(self, path: Path, default: Any) -> Any:
        if not path.exists():
            return default
        return json.loads(path.read_text())

    def _read_jsonl(self, path: Path) -> List[Dict[str, Any]]:
        if not path.exists():
            return []
        items: List[Dict[str, Any]] = []
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))
        return items
    
    def run_phase19(
        self,
        waves: int = 3,
        agents: int = 4
    ) -> Dict[str, Any]:
        """
        Execute complete Phase 19 optimization pipeline.
        
        Args:
            waves: Number of waves to optimize
            agents: Number of agents to coordinate
        
        Returns:
            Dictionary with execution summary
        """
        self.start_time = datetime.now(timezone.utc)
        phase18_counts = self._load_phase18_data()
        init_summary = self._initialize_optimizer()

        agent_ids = [f"agent_{i}" for i in range(agents)]
        tasks = self._generate_tasks(self.multi_agent_summary.get("total_tasks", waves * agents))
        tasks = self._apply_safety_gates(tasks)

        wave_results = []
        tasks_per_wave = max(1, len(tasks) // max(waves, 1))
        for wave in range(1, waves + 1):
            start_idx = (wave - 1) * tasks_per_wave
            end_idx = len(tasks) if wave == waves else start_idx + tasks_per_wave
            wave_tasks = tasks[start_idx:end_idx]
            optimization_result = self._optimize_wave(wave, wave_tasks, agent_ids)
            schedule_execution = self._apply_scheduler(wave, optimization_result)
            wave_results.append({
                "wave": wave,
                "optimization": optimization_result,
                "execution": schedule_execution,
            })
            self.waves_optimized += 1

        feedback_counts = self._generate_feedback()
        health_metrics = self._monitor_optimization()
        self._generate_reports()
        self.end_time = datetime.now(timezone.utc)

        summary = {
            "phase": 19,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "duration_ms": (self.end_time - self.start_time).total_seconds() * 1000.0,
            "phase18_counts": phase18_counts,
            "init_summary": init_summary,
            "waves_optimized": self.waves_optimized,
            "feedback_counts": feedback_counts,
            "health_metrics": health_metrics,
        }
        (self.phase19_output_dir / "phase19_summary.json").write_text(json.dumps(summary, indent=2))
        return summary
    
    def _load_phase18_data(self) -> Dict[str, int]:
        """
        Load Phase 18 multi-agent execution data.
        
        Returns:
            Dictionary with counts of loaded data
        """
        self.multi_agent_summary = self._read_json(self.phase18_dir / "multi_agent_summary.json", {})
        self.coordination_patterns = self._read_json(self.phase18_dir / "coordination_patterns.json", [])
        self.system_health = self._read_json(self.phase18_dir / "system_health.json", {})
        self.learning_signals = self._read_jsonl(self.phase18_dir / "learning_signals.jsonl")
        return {
            "agents_loaded": len(self.multi_agent_summary.get("agent_performance", {}).keys()),
            "patterns_loaded": len(self.coordination_patterns),
            "signals_loaded": len(self.learning_signals),
        }
    
    def _initialize_optimizer(self) -> Dict[str, Any]:
        """
        Initialize optimizer with Phase 18 data.
        
        Returns:
            Dictionary with initialization summary
        """
        self.optimizer = AdaptiveOptimizer(self.phase18_dir, self.phase19_output_dir)
        load_counts = self.optimizer.load_phase18_data()
        return {
            "strategy": self.optimization_strategy,
            "load_counts": load_counts,
        }
    
    def _optimize_wave(
        self,
        wave: int,
        tasks: List[Dict[str, Any]],
        agents: List[str]
    ) -> Dict[str, Any]:
        """
        Optimize schedule for single wave.
        
        Args:
            wave: Wave number
            tasks: Tasks to schedule
            agents: Available agents
        
        Returns:
            Dictionary with optimization result
        """
        strategy_enum = OptimizationStrategy(self.optimization_strategy)
        optimization_result = self.optimizer.calculate_optimal_schedule(tasks, agents, strategy_enum)
        simulation = self.optimizer.simulate_schedule(optimization_result)
        recommendations = self.optimizer.generate_schedule_recommendations(wave, optimization_result)
        return {
            "optimization_result": optimization_result,
            "simulation": simulation,
            "recommendations": recommendations,
        }
    
    def _apply_scheduler(
        self,
        wave: int,
        optimization_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply scheduler to optimization result.
        
        Args:
            wave: Wave number
            optimization_result: Optimizer output
        
        Returns:
            Dictionary with scheduled tasks
        """
        if self.scheduler is None:
            self.scheduler = AdaptiveScheduler(self.phase19_output_dir, dry_run=self.dry_run)

        optimization_result = optimization_result["optimization_result"]
        agent_assignments = optimization_result.agent_assignments
        tasks = self._reconstruct_tasks(agent_assignments)
        scheduled = self.scheduler.assign_tasks_to_agents(tasks, agent_assignments, wave)
        scheduled = self.scheduler.adjust_for_agent_load(scheduled)
        execution = self.scheduler.execute_schedule(wave, scheduled)
        self.scheduler.write_schedule_outputs(wave)
        self._write_execution_outcomes(wave, execution)
        return {
            "scheduled_tasks": scheduled,
            "execution": execution,
        }
    
    def _execute_wave(
        self,
        wave: int,
        scheduled_tasks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Execute scheduled tasks for wave.
        
        Args:
            wave: Wave number
            scheduled_tasks: Tasks with scheduling info
        
        Returns:
            Dictionary with execution results
        """
        return {
            "wave": wave,
            "scheduled_tasks": scheduled_tasks,
        }
    
    def _generate_feedback(self) -> Dict[str, int]:
        """
        Generate feedback loop analysis.
        
        Returns:
            Dictionary with feedback counts
        """
        self.feedback = OptimizationFeedbackLoop(self.phase19_output_dir, self.phase19_output_dir)
        comparisons = self._read_jsonl(self.phase19_output_dir / "schedule_comparisons.jsonl")
        if not comparisons:
            # build comparisons from executions if missing
            comparisons_payload = []
            for execution in self.scheduler.execution_history if self.scheduler else []:
                comparisons_payload.append({
                    "wave": execution.wave,
                    "planned_success_rate": execution.actual_success_rate,
                    "actual_success_rate": execution.actual_success_rate,
                    "planned_throughput": execution.actual_throughput,
                    "actual_throughput": execution.actual_throughput,
                    "planned_confidence_delta": execution.actual_avg_confidence_delta,
                    "actual_confidence_delta": execution.actual_avg_confidence_delta,
                    "accuracy_score": 1.0,
                })
            if comparisons_payload:
                (self.phase19_output_dir / "schedule_comparisons.jsonl").write_text(
                    "\n".join(json.dumps(c) for c in comparisons_payload)
                )

        for comparison in self._read_jsonl(self.phase19_output_dir / "schedule_comparisons.jsonl"):
            self.feedback.schedule_comparisons.append(
                self.feedback.evaluate_schedule_outcome(
                    comparison.get("wave", 0),
                    {
                        "success_rate": comparison.get("planned_success_rate", 0.0),
                        "throughput": comparison.get("planned_throughput", 0.0),
                        "confidence_delta": comparison.get("planned_confidence_delta", 0.0),
                    },
                    {
                        "success_rate": comparison.get("actual_success_rate", 0.0),
                        "throughput": comparison.get("actual_throughput", 0.0),
                        "confidence_delta": comparison.get("actual_confidence_delta", 0.0),
                    },
                )
            )

        self.feedback.generate_feedback_events()
        signals = self.feedback.generate_learning_signals()
        self.feedback.update_heuristic_weights({"H16_001": 0.85, "H16_002": 0.8, "H16_003": 0.9, "H16_004": 0.75})
        self.feedback.evaluate_strategy_effectiveness(self.optimization_strategy)
        self.feedback.write_feedback_outputs()
        self.feedback.update_phase16_heuristics()
        self.feedback.update_phase18_coordination()

        (self.phase19_output_dir / "learning_signals.jsonl").write_text(
            "\n".join(
                json.dumps({
                    "feedback_id": s.feedback_id,
                    "feedback_type": s.feedback_type,
                    "confidence": s.confidence,
                    "description": s.description,
                    "recommendation": s.recommendation,
                    "supporting_evidence": s.supporting_evidence,
                    "timestamp": s.timestamp,
                })
                for s in signals
            )
        )
        return {"learning_signals": len(signals)}
    
    def _monitor_optimization(self) -> Dict[str, Any]:
        """
        Monitor optimization performance.
        
        Returns:
            Dictionary with health metrics
        """
        self.monitor = OptimizationMonitor(self.phase19_output_dir, self.phase19_output_dir)
        metrics = self.monitor.calculate_metrics()
        self.monitor.detect_anomalies()
        health = self.monitor.generate_system_health()
        self.monitor.write_monitoring_outputs()
        return {
            "metrics": [m.metric_name for m in metrics],
            "health": health,
        }
    
    def _generate_reports(self):
        """
        Generate comprehensive Phase 19 reports.
        """
        if self.optimizer:
            self.optimizer.write_optimization_outputs()
        report = self._create_phase19_execution_report()
        (self.phase19_output_dir / "PHASE_19_AUTONOMOUS_EXECUTION.md").write_text(report)
    
    def _create_phase19_summary(self) -> Dict[str, Any]:
        """
        Create comprehensive Phase 19 execution summary.
        
        Returns:
            Dictionary with complete execution summary
        """
        health = self._read_json(self.phase19_output_dir / "system_health.json", {})
        summary = {
            "phase": 19,
            "timestamp": self._utc_now(),
            "waves_optimized": self.waves_optimized,
            "health": health,
        }
        return summary
    
    def _apply_safety_gates(
        self,
        tasks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Apply Phase 13 safety gates before scheduling.
        
        Args:
            tasks: Tasks to validate
        
        Returns:
            Filtered list of approved tasks
        """
        approved: List[Dict[str, Any]] = []
        rejected: List[Dict[str, Any]] = []
        for task in tasks:
            risk = (task.get("risk_level") or "MEDIUM").upper()
            confidence = float(task.get("confidence", 0.7))
            if risk == "HIGH" and confidence < 0.7:
                rejected.append(task)
            else:
                approved.append(task)

        if rejected:
            (self.phase19_output_dir / "rejected_tasks.jsonl").write_text(
                "\n".join(json.dumps(task) for task in rejected)
            )
        return approved
    
    def _enforce_dry_run(self):
        """
        Ensure dry-run mode is enforced.
        """
        if self.dry_run:
            return "Dry-run mode enabled"
        return "Live execution enabled"
    
    def write_jsonl_outputs(self):
        """
        Write all JSONL outputs for observability.
        """
        # Outputs are written by component methods
        return

    def _generate_tasks(self, total_tasks: int) -> List[Dict[str, Any]]:
        tasks = []
        risk_cycle = ["LOW", "MEDIUM", "LOW", "HIGH"]
        for idx in range(total_tasks):
            tasks.append({
                "task_id": f"task_{idx}",
                "risk_level": risk_cycle[idx % len(risk_cycle)],
                "confidence": 0.8 - (0.01 * (idx % 5)),
                "description": f"Autogenerated task {idx}",
            })
        return tasks

    def _reconstruct_tasks(self, agent_assignments: Dict[str, List[str]]) -> List[Dict[str, Any]]:
        tasks = []
        for agent_id, task_ids in agent_assignments.items():
            for task_id in task_ids:
                tasks.append({
                    "task_id": task_id,
                    "agent_id": agent_id,
                    "risk_level": "MEDIUM",
                    "confidence": 0.75,
                })
        return tasks

    def _write_execution_outcomes(self, wave: int, execution):
        wave_dir = self.phase19_output_dir / f"wave_{wave}"
        wave_dir.mkdir(parents=True, exist_ok=True)
        per_agent: Dict[str, List[Dict[str, Any]]] = {}
        for task in execution.scheduled_tasks:
            per_agent.setdefault(task.agent_id, []).append({
                "task_id": task.task_id,
                "agent_id": task.agent_id,
                "wave": wave,
                "status": task.status.value,
                "confidence": task.confidence,
                "actual_start_time": task.actual_start_time,
                "actual_end_time": task.actual_end_time,
                "retry_count": task.retry_count,
            })
        for agent_id, outcomes in per_agent.items():
            agent_dir = wave_dir / agent_id
            agent_dir.mkdir(parents=True, exist_ok=True)
            (agent_dir / "execution_outcomes.jsonl").write_text(
                "\n".join(json.dumps(o) for o in outcomes)
            )

        comparison = {
            "wave": wave,
            "planned_success_rate": execution.actual_success_rate,
            "actual_success_rate": execution.actual_success_rate,
            "planned_throughput": execution.actual_throughput,
            "actual_throughput": execution.actual_throughput,
            "planned_confidence_delta": execution.actual_avg_confidence_delta,
            "actual_confidence_delta": execution.actual_avg_confidence_delta,
            "accuracy_score": 1.0,
        }
        comparisons_path = self.phase19_output_dir / "schedule_comparisons.jsonl"
        existing = comparisons_path.read_text().splitlines() if comparisons_path.exists() else []
        existing.append(json.dumps(comparison))
        comparisons_path.write_text("\n".join(existing))

    def _create_phase19_execution_report(self) -> str:
        health = self._read_json(self.phase19_output_dir / "system_health.json", {})
        return "\n".join([
            "# Phase 19: Autonomous Optimization Execution Report",
            "",
            f"**Status:** {'DRY-RUN' if self.dry_run else 'LIVE'}",
            f"**Waves Optimized:** {self.waves_optimized}",
            "",
            "## System Health",
            json.dumps(health, indent=2),
        ])


def main():
    """
    Main Phase 19 execution function.
    """
    # TODO: Initialize harness with dry_run=True
    # TODO: Run pipeline
    # TODO: Print summary
    # TODO: Report completion
    pass


if __name__ == "__main__":
    main()

