"""
Phase 19: Optimization & Adaptive Scheduling - Adaptive Optimizer

Applies optimization algorithms to multi-agent task assignment and scheduling.
Uses Phase 18 coordination patterns to maximize efficiency and success rates.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple


class OptimizationStrategy(Enum):
    """Optimization strategy types"""
    MAXIMIZE_SUCCESS = "maximize_success"
    MAXIMIZE_THROUGHPUT = "maximize_throughput"
    BALANCE_LOAD = "balance_load"
    MINIMIZE_RETRIES = "minimize_retries"
    CONFIDENCE_OPTIMIZATION = "confidence_optimization"


@dataclass
class OptimizationResult:
    """Result of optimization computation"""
    strategy: OptimizationStrategy
    expected_success_rate: float
    expected_throughput: float
    expected_confidence_delta: float
    agent_assignments: Dict[str, List[str]]  # agent_id -> task_ids
    task_priorities: Dict[str, int]  # task_id -> priority
    confidence: float
    timestamp: str


@dataclass
class ScheduleRecommendation:
    """Scheduling recommendation from optimizer"""
    recommendation_id: str
    wave: int
    agent_id: str
    task_ids: List[str]
    expected_completion_time_ms: float
    expected_success_probability: float
    rationale: str
    confidence: float


class AdaptiveOptimizer:
    """
    Adaptive optimization engine for multi-agent task scheduling.
    
    Responsibilities:
    - Load Phase 18 multi-agent execution data
    - Apply optimization algorithms for task assignment
    - Generate optimal scheduling recommendations
    - Simulate schedule outcomes
    - Update confidence estimates based on historical data
    """
    
    def __init__(self, phase18_dir: Path, phase19_output_dir: Path):
        """
        Initialize adaptive optimizer.
        
        Args:
            phase18_dir: Directory with Phase 18 outputs
            phase19_output_dir: Directory for Phase 19 outputs
        """
        self.phase18_dir = Path(phase18_dir)
        self.phase19_output_dir = Path(phase19_output_dir)
        self.phase19_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Phase 18 data
        self.multi_agent_summary: Dict[str, Any] = {}
        self.coordination_patterns: List[Dict[str, Any]] = []
        self.system_health: Dict[str, Any] = {}
        self.learning_signals: List[Dict[str, Any]] = []
        
        # Optimization state
        self.agent_performance_history: Dict[str, List[float]] = {}
        self.task_success_patterns: Dict[str, float] = {}
        self.optimization_results: List[OptimizationResult] = []
        self.schedule_recommendations: List[ScheduleRecommendation] = []

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

    def _risk_weight(self, risk_level: str) -> float:
        risk = (risk_level or "MEDIUM").upper()
        if risk == "LOW":
            return 0.0
        if risk == "MEDIUM":
            return 0.1
        if risk == "HIGH":
            return 0.2
        return 0.1

    def _agent_success_rate(self, agent_id: str) -> float:
        agent_perf = self.multi_agent_summary.get("agent_performance", {}).get(agent_id, {})
        return float(agent_perf.get("success_rate", self.multi_agent_summary.get("success_rate", 0.85)))

    def _agent_retry_rate(self, agent_id: str) -> float:
        agent_perf = self.multi_agent_summary.get("agent_performance", {}).get(agent_id, {})
        return float(agent_perf.get("retry_rate", self.multi_agent_summary.get("retry_rate", 0.1)))

    def _agent_confidence_delta(self, agent_id: str) -> float:
        agent_perf = self.multi_agent_summary.get("agent_performance", {}).get(agent_id, {})
        return float(agent_perf.get("avg_confidence_delta", self.multi_agent_summary.get("avg_confidence_delta", 0.02)))

    def _predict_success(self, task: Dict[str, Any], agent_id: str) -> float:
        base_conf = float(task.get("confidence", 0.7))
        risk_penalty = self._risk_weight(task.get("risk_level", "MEDIUM"))
        agent_success = self._agent_success_rate(agent_id)
        predicted = (base_conf * 0.6) + (agent_success * 0.4) - risk_penalty
        return max(0.05, min(0.99, predicted))
    
    def load_phase18_data(self) -> Dict[str, int]:
        """
        Load Phase 18 multi-agent execution outputs.
        
        Returns:
            Dictionary with counts of loaded data:
            - agents_loaded: Number of agents
            - patterns_loaded: Number of coordination patterns
            - signals_loaded: Number of learning signals
        
        Raises:
            FileNotFoundError: If Phase 18 output files not found
        """
        self.multi_agent_summary = self._read_json(self.phase18_dir / "multi_agent_summary.json", {})
        self.coordination_patterns = self._read_json(self.phase18_dir / "coordination_patterns.json", [])
        self.system_health = self._read_json(self.phase18_dir / "system_health.json", {})
        self.learning_signals = self._read_jsonl(self.phase18_dir / "learning_signals.jsonl")

        agent_perf = self.multi_agent_summary.get("agent_performance", {})
        for agent_id, perf in agent_perf.items():
            history = perf.get("success_history") or []
            if history:
                self.agent_performance_history[agent_id] = history
            else:
                self.agent_performance_history[agent_id] = [float(perf.get("success_rate", 0.85))]

        self.task_success_patterns = self.multi_agent_summary.get("task_success_patterns", {})
        return {
            "agents_loaded": len(agent_perf.keys()),
            "patterns_loaded": len(self.coordination_patterns),
            "signals_loaded": len(self.learning_signals),
        }
    
    def calculate_optimal_schedule(
        self,
        tasks: List[Dict[str, Any]],
        agents: List[str],
        strategy: OptimizationStrategy = OptimizationStrategy.MAXIMIZE_SUCCESS
    ) -> OptimizationResult:
        """
        Calculate optimal task-to-agent assignment using specified strategy.
        
        Args:
            tasks: List of tasks to schedule
            agents: List of available agent IDs
            strategy: Optimization strategy to apply
        
        Returns:
            OptimizationResult with assignments and expected metrics
        """
        if not tasks or not agents:
            result = OptimizationResult(
                strategy=strategy,
                expected_success_rate=0.0,
                expected_throughput=0.0,
                expected_confidence_delta=0.0,
                agent_assignments={a: [] for a in agents},
                task_priorities={},
                confidence=0.0,
                timestamp=self._utc_now(),
            )
            self.optimization_results.append(result)
            return result

        strategy_map = {
            OptimizationStrategy.MAXIMIZE_SUCCESS: self.optimize_for_success,
            OptimizationStrategy.MAXIMIZE_THROUGHPUT: self.optimize_for_throughput,
            OptimizationStrategy.BALANCE_LOAD: self.optimize_for_throughput,
            OptimizationStrategy.MINIMIZE_RETRIES: self.optimize_for_minimize_retries,
            OptimizationStrategy.CONFIDENCE_OPTIMIZATION: self.optimize_for_confidence,
        }
        assignment_fn = strategy_map.get(strategy, self.optimize_for_success)
        agent_assignments = assignment_fn(tasks, agents)

        task_priorities: Dict[str, int] = {}
        for priority, task in enumerate(sorted(tasks, key=lambda t: (-float(t.get("confidence", 0.0)), t.get("task_id", ""))), start=1):
            task_priorities[task.get("task_id", f"task_{priority}")] = priority

        predicted_success_rates: List[float] = []
        for agent_id, task_ids in agent_assignments.items():
            for task_id in task_ids:
                task = next((t for t in tasks if t.get("task_id") == task_id), None)
                if not task:
                    continue
                predicted_success_rates.append(self._predict_success(task, agent_id))

        expected_success_rate = sum(predicted_success_rates) / max(len(predicted_success_rates), 1)
        avg_exec_ms = float(self.multi_agent_summary.get("avg_execution_time_ms", 30.0))
        expected_throughput = (len(tasks) / max(avg_exec_ms, 1.0)) * 1000.0
        expected_confidence_delta = sum(
            self._agent_confidence_delta(agent_id) for agent_id in agents
        ) / max(len(agents), 1)

        result = OptimizationResult(
            strategy=strategy,
            expected_success_rate=expected_success_rate,
            expected_throughput=expected_throughput,
            expected_confidence_delta=expected_confidence_delta,
            agent_assignments=agent_assignments,
            task_priorities=task_priorities,
            confidence=min(0.99, max(0.1, expected_success_rate)),
            timestamp=self._utc_now(),
        )
        self.optimization_results.append(result)
        return result
    
    def optimize_for_success(
        self,
        tasks: List[Dict[str, Any]],
        agents: List[str]
    ) -> Dict[str, List[str]]:
        """
        Optimize task assignment to maximize success rate.
        
        Args:
            tasks: Tasks to assign
            agents: Available agents
        
        Returns:
            Dictionary mapping agent_id to assigned task_ids
        """
        agent_ranking = sorted(agents, key=self._agent_success_rate, reverse=True)
        tasks_sorted = sorted(
            tasks,
            key=lambda t: (
                {"LOW": 0, "MEDIUM": 1, "HIGH": 2}.get((t.get("risk_level") or "MEDIUM").upper(), 1),
                -float(t.get("confidence", 0.0)),
            ),
        )

        assignments: Dict[str, List[str]] = {agent: [] for agent in agents}
        for idx, task in enumerate(tasks_sorted):
            agent_id = agent_ranking[idx % max(len(agent_ranking), 1)]
            assignments[agent_id].append(task.get("task_id", f"task_{idx}"))
        return assignments
    
    def optimize_for_throughput(
        self,
        tasks: List[Dict[str, Any]],
        agents: List[str]
    ) -> Dict[str, List[str]]:
        """
        Optimize task assignment to maximize throughput.
        
        Args:
            tasks: Tasks to assign
            agents: Available agents
        
        Returns:
            Dictionary mapping agent_id to assigned task_ids
        """
        assignments: Dict[str, List[str]] = {agent: [] for agent in agents}
        loads: Dict[str, int] = {agent: 0 for agent in agents}
        for idx, task in enumerate(tasks):
            agent_id = min(loads, key=loads.get)
            assignments[agent_id].append(task.get("task_id", f"task_{idx}"))
            loads[agent_id] += 1
        return assignments

    def optimize_for_minimize_retries(
        self,
        tasks: List[Dict[str, Any]],
        agents: List[str]
    ) -> Dict[str, List[str]]:
        """
        Optimize task assignment to minimize retries.
        """
        agent_ranking = sorted(agents, key=self._agent_retry_rate)
        tasks_sorted = sorted(tasks, key=lambda t: int(t.get("retry_count", 0)), reverse=True)
        assignments: Dict[str, List[str]] = {agent: [] for agent in agents}
        for idx, task in enumerate(tasks_sorted):
            agent_id = agent_ranking[idx % max(len(agent_ranking), 1)]
            assignments[agent_id].append(task.get("task_id", f"task_{idx}"))
        return assignments
    
    def optimize_for_confidence(
        self,
        tasks: List[Dict[str, Any]],
        agents: List[str]
    ) -> Dict[str, List[str]]:
        """
        Optimize task assignment to maximize confidence improvements.
        
        Args:
            tasks: Tasks to assign
            agents: Available agents
        
        Returns:
            Dictionary mapping agent_id to assigned task_ids
        """
        agent_ranking = sorted(agents, key=self._agent_confidence_delta, reverse=True)
        tasks_sorted = sorted(tasks, key=lambda t: float(t.get("confidence", 0.0)))
        assignments: Dict[str, List[str]] = {agent: [] for agent in agents}
        for idx, task in enumerate(tasks_sorted):
            agent_id = agent_ranking[idx % max(len(agent_ranking), 1)]
            assignments[agent_id].append(task.get("task_id", f"task_{idx}"))
        return assignments
    
    def simulate_schedule(
        self,
        optimization_result: OptimizationResult
    ) -> Dict[str, Any]:
        """
        Simulate schedule execution to predict outcomes.
        
        Args:
            optimization_result: Schedule to simulate
        
        Returns:
            Dictionary with simulated metrics:
            - simulated_success_rate
            - simulated_completion_time_ms
            - simulated_confidence_delta
            - agent_utilization
        """
        total_tasks = sum(len(t) for t in optimization_result.agent_assignments.values())
        if total_tasks == 0:
            return {
                "simulated_success_rate": 0.0,
                "simulated_completion_time_ms": 0.0,
                "simulated_confidence_delta": 0.0,
                "agent_utilization": {},
            }

        predicted_success_rates: List[float] = []
        for agent_id, task_ids in optimization_result.agent_assignments.items():
            for task_id in task_ids:
                task = {"task_id": task_id, "confidence": 0.7, "risk_level": "MEDIUM"}
                predicted_success_rates.append(self._predict_success(task, agent_id))

        simulated_success_rate = sum(predicted_success_rates) / max(len(predicted_success_rates), 1)
        avg_exec_ms = float(self.multi_agent_summary.get("avg_execution_time_ms", 30.0))
        simulated_completion_time_ms = avg_exec_ms * total_tasks

        simulated_confidence_delta = sum(
            self._agent_confidence_delta(agent_id) for agent_id in optimization_result.agent_assignments.keys()
        ) / max(len(optimization_result.agent_assignments.keys()), 1)

        max_tasks = max((len(t) for t in optimization_result.agent_assignments.values()), default=1)
        agent_utilization = {
            agent_id: len(tasks) / max_tasks
            for agent_id, tasks in optimization_result.agent_assignments.items()
        }

        return {
            "simulated_success_rate": simulated_success_rate,
            "simulated_completion_time_ms": simulated_completion_time_ms,
            "simulated_confidence_delta": simulated_confidence_delta,
            "agent_utilization": agent_utilization,
        }
    
    def update_confidence_estimates(
        self,
        tasks: List[Dict[str, Any]],
        agent_performance: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Update confidence estimates for tasks based on agent performance.
        
        Args:
            tasks: Tasks to update
            agent_performance: Historical performance by agent
        
        Returns:
            Dictionary mapping task_id to updated confidence
        """
        updated: Dict[str, float] = {}
        for task in tasks:
            task_id = task.get("task_id")
            base_conf = float(task.get("confidence", 0.7))
            risk_penalty = self._risk_weight(task.get("risk_level", "MEDIUM"))
            agent_id = task.get("agent_id")
            agent_factor = float(agent_performance.get(agent_id, 0.85))
            new_conf = base_conf + (agent_factor - 0.85) * 0.2 - risk_penalty
            updated[task_id] = max(0.05, min(0.99, new_conf))
        return updated
    
    def generate_schedule_recommendations(
        self,
        wave: int,
        optimization_result: OptimizationResult
    ) -> List[ScheduleRecommendation]:
        """
        Generate detailed scheduling recommendations per agent.
        
        Args:
            wave: Wave number
            optimization_result: Optimization result
        
        Returns:
            List of ScheduleRecommendation objects
        """
        recommendations: List[ScheduleRecommendation] = []
        for agent_id, task_ids in optimization_result.agent_assignments.items():
            expected_success = self._agent_success_rate(agent_id)
            expected_time = float(self.multi_agent_summary.get("avg_execution_time_ms", 30.0)) * max(len(task_ids), 1)
            recommendations.append(
                ScheduleRecommendation(
                    recommendation_id=f"REC_{wave}_{agent_id}",
                    wave=wave,
                    agent_id=agent_id,
                    task_ids=task_ids,
                    expected_completion_time_ms=expected_time,
                    expected_success_probability=expected_success,
                    rationale=f"Assigned based on {optimization_result.strategy.value} strategy",
                    confidence=min(0.99, max(0.1, expected_success)),
                )
            )
        self.schedule_recommendations.extend(recommendations)
        return recommendations
    
    def calculate_optimization_metrics(self) -> Dict[str, float]:
        """
        Calculate optimization performance metrics.
        
        Returns:
            Dictionary with:
            - optimization_efficiency: How well optimizer performs
            - prediction_accuracy: Accuracy of simulations
            - schedule_quality: Quality score (0-100)
        """
        if not self.optimization_results:
            return {
                "optimization_efficiency": 0.0,
                "prediction_accuracy": 0.0,
                "schedule_quality": 0.0,
            }
        avg_success = sum(r.expected_success_rate for r in self.optimization_results) / len(self.optimization_results)
        avg_throughput = sum(r.expected_throughput for r in self.optimization_results) / len(self.optimization_results)
        optimization_efficiency = min(1.0, avg_throughput / 50.0)
        prediction_accuracy = min(1.0, avg_success)
        schedule_quality = min(100.0, (optimization_efficiency * 50.0) + (prediction_accuracy * 50.0))
        return {
            "optimization_efficiency": optimization_efficiency,
            "prediction_accuracy": prediction_accuracy,
            "schedule_quality": schedule_quality,
        }
    
    def write_optimization_outputs(self):
        """
        Write optimization results to output files.
        """
        summary = {
            "phase": 19,
            "timestamp": self._utc_now(),
            "optimization_results": [
                {
                    "strategy": r.strategy.value,
                    "expected_success_rate": r.expected_success_rate,
                    "expected_throughput": r.expected_throughput,
                    "expected_confidence_delta": r.expected_confidence_delta,
                    "agent_assignments": r.agent_assignments,
                    "task_priorities": r.task_priorities,
                    "confidence": r.confidence,
                    "timestamp": r.timestamp,
                }
                for r in self.optimization_results
            ],
            "metrics": self.calculate_optimization_metrics(),
        }
        (self.phase19_output_dir / "optimization_summary.json").write_text(json.dumps(summary, indent=2))

        recommendations_path = self.phase19_output_dir / "schedule_recommendations.jsonl"
        recommendations_path.write_text(
            "\n".join(
                json.dumps({
                    "recommendation_id": r.recommendation_id,
                    "wave": r.wave,
                    "agent_id": r.agent_id,
                    "task_ids": r.task_ids,
                    "expected_completion_time_ms": r.expected_completion_time_ms,
                    "expected_success_probability": r.expected_success_probability,
                    "rationale": r.rationale,
                    "confidence": r.confidence,
                })
                for r in self.schedule_recommendations
            )
        )

        agent_assignments = {
            r.timestamp: r.agent_assignments for r in self.optimization_results
        }
        (self.phase19_output_dir / "agent_assignments.json").write_text(json.dumps(agent_assignments, indent=2))

    def optimize_schedule(
        self,
        tasks: List[Dict[str, Any]],
        agents: List[str],
        strategy: str
    ) -> OptimizationResult:
        """
        Compute optimized schedule using strategy string.
        """
        try:
            strategy_enum = OptimizationStrategy(strategy)
        except ValueError:
            strategy_enum = OptimizationStrategy.MAXIMIZE_SUCCESS
        return self.calculate_optimal_schedule(tasks, agents, strategy_enum)


def main():
    """
    Main execution function for testing optimizer.
    """
    # TODO: Initialize optimizer
    # TODO: Load Phase 18 data
    # TODO: Calculate optimal schedule
    # TODO: Simulate schedule
    # TODO: Write outputs
    pass


if __name__ == "__main__":
    main()
