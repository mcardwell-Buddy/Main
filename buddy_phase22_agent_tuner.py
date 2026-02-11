"""
Phase 22: Agent Tuner Module

Purpose:
    Adaptive per-agent tuning for speed, retries, confidence weighting,
    and parallelism based on multi-wave performance metrics.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
import json


@dataclass
class AgentTuningParameters:
    """Tunable parameters for an agent."""

    speed_multiplier: float = 1.0
    retry_threshold: int = 3
    confidence_weight: float = 1.0
    max_parallel_tasks: int = 2


@dataclass
class AgentTuningResult:
    """Result of tuning an agent for a wave."""

    agent_id: str
    wave: int
    before: AgentTuningParameters
    after: AgentTuningParameters
    expected_impact: Dict[str, float]
    reason: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class Phase22AgentTuner:
    """
    Per-agent adaptive tuning for Phase 22.
    """

    def __init__(self, phase22_output_dir: Path, dry_run: bool = True):
        """
        Initialize agent tuner.

        Args:
            phase22_output_dir: Output base directory for Phase 22
            dry_run: If True, no side effects
        """
        self.phase22_output_dir = Path(phase22_output_dir)
        self.dry_run = dry_run
        self.agent_parameters: Dict[str, AgentTuningParameters] = {}
        self.tuning_results: List[AgentTuningResult] = []

    def initialize_agents(self, agent_ids: List[str]) -> None:
        """
        Initialize agents with default tuning parameters.

        Args:
            agent_ids: List of agent identifiers
        """
        for agent_id in agent_ids:
            if agent_id not in self.agent_parameters:
                self.agent_parameters[agent_id] = AgentTuningParameters()

    def tune_agents(
        self,
        wave: int,
        agent_metrics: Dict[str, Dict[str, float]],
    ) -> List[AgentTuningResult]:
        """
        Tune agents based on performance metrics.

        Args:
            wave: Wave number
            agent_metrics: Metrics per agent

        Returns:
            List of AgentTuningResult
        """
        results: List[AgentTuningResult] = []
        for agent_id, metrics in agent_metrics.items():
            before = self.agent_parameters.get(agent_id, AgentTuningParameters())
            after = AgentTuningParameters(**before.__dict__)

            reason = []
            expected_impact = {"success_rate": 0.0, "throughput": 0.0}

            if metrics.get("success_rate", 1.0) < 0.90:
                after.retry_threshold = min(5, after.retry_threshold + 1)
                expected_impact["success_rate"] += 0.02
                reason.append("increase retry_threshold for reliability")

            if metrics.get("throughput", 50.0) < 35.0:
                after.speed_multiplier = min(1.3, after.speed_multiplier + 0.05)
                expected_impact["throughput"] += 2.0
                reason.append("increase speed_multiplier for throughput")

            if metrics.get("confidence", 1.0) < 0.95:
                after.confidence_weight = min(1.2, after.confidence_weight + 0.05)
                expected_impact["success_rate"] += 0.01
                reason.append("increase confidence_weight for alignment")

            if metrics.get("utilization", 1.0) < 0.7:
                after.max_parallel_tasks = min(4, after.max_parallel_tasks + 1)
                expected_impact["throughput"] += 1.0
                reason.append("increase max_parallel_tasks for utilization")

            if not reason:
                reason.append("metrics within target range")

            result = AgentTuningResult(
                agent_id=agent_id,
                wave=wave,
                before=before,
                after=after,
                expected_impact=expected_impact,
                reason="; ".join(reason),
            )
            self.agent_parameters[agent_id] = after
            results.append(result)

        self.tuning_results.extend(results)
        return results

    def get_agent_parameters(self, agent_id: str) -> AgentTuningParameters:
        """
        Get current tuning parameters for an agent.

        Args:
            agent_id: Agent identifier

        Returns:
            AgentTuningParameters
        """
        return self.agent_parameters.get(agent_id, AgentTuningParameters())

    def write_tuning_outputs(self, wave: int) -> Dict[str, Optional[str]]:
        """
        Write tuning outputs per agent and wave.

        Returns:
            Dict of agent_id -> output path
        """
        outputs: Dict[str, Optional[str]] = {}
        for agent_id, params in self.agent_parameters.items():
            agent_dir = self.phase22_output_dir / f"wave_{wave}" / agent_id
            agent_dir.mkdir(parents=True, exist_ok=True)
            file_path = agent_dir / "tuned_parameters.jsonl"
            with open(file_path, "w", encoding="utf-8") as handle:
                handle.write(json.dumps({
                    "agent_id": agent_id,
                    "wave": wave,
                    "parameters": params.__dict__,
                    "dry_run": self.dry_run,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }) + "\n")
            outputs[agent_id] = str(file_path)
        return outputs

