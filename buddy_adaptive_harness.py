"""Buddy Phase 10 Adaptive Harness.

Wave-mode autonomous simulation using Phase 6 scheduler, Phase 8 snapshots,
and Phase 9 learning artifacts. Fully sandboxed and additive.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from buddy_goal_manager import GoalManager
from buddy_policy_updater import PolicyUpdater, PolicyState
from buddy_simulated_executor import SimulatedExecutor


class AdaptiveHarness:
    def __init__(self, output_dir: str = "outputs/phase10", seed: int = 1337):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.self_questions_file = self.output_dir / "self_questions.jsonl"
        self.task_outcomes_file = self.output_dir / "task_outcomes.jsonl"
        self.confidence_updates_file = self.output_dir / "confidence_updates.jsonl"
        self.policy_updates_file = self.output_dir / "policy_updates.jsonl"

        for filepath in [
            self.self_questions_file,
            self.task_outcomes_file,
            self.confidence_updates_file,
            self.policy_updates_file
        ]:
            if filepath.exists():
                filepath.unlink()

        for wave_dir in self.output_dir.glob("wave_*"):
            if wave_dir.is_dir():
                for child in wave_dir.glob("*"):
                    if child.is_file():
                        child.unlink()

        self.goal_manager = GoalManager(seed=seed)
        self.policy_updater = PolicyUpdater(initial_policy=PolicyState())
        self.executor = SimulatedExecutor(output_dir=self.output_dir)
        self.wave_stats: List[Dict[str, Any]] = []

    def _load_phase9_outcomes(self) -> List[Dict[str, Any]]:
        phase9_path = Path("outputs/phase9/task_outcomes.jsonl")
        if not phase9_path.exists():
            return []
        lines = phase9_path.read_text(encoding="utf-8").splitlines()
        return [json.loads(line) for line in lines if line.strip()]

    def _write_jsonl(self, path: Path, payload: List[Dict[str, Any]]):
        with path.open("a", encoding="utf-8") as f:
            for item in payload:
                f.write(json.dumps(item) + "\n")

    def run(self, waves: int = 3):
        phase9_outcomes = self._load_phase9_outcomes()
        if phase9_outcomes:
            self.policy_updater.update_from_outcomes(phase9_outcomes)

        for wave in range(1, waves + 1):
            wave_dir = self.output_dir / f"wave_{wave}"
            wave_dir.mkdir(parents=True, exist_ok=True)

            goals = self.goal_manager.generate_goals(wave=wave)
            tasks = [task for goal in goals for task in goal.tasks]

            result = self.executor.execute_wave(
                tasks=tasks,
                wave=wave,
                policy=self.policy_updater.policy.to_dict(),
                output_dir=wave_dir,
                workflow_id=f"phase10_wave_{wave}"
            )

            outcomes = [asdict(o) for o in result["outcomes"]]
            questions = [asdict(q) for q in result["questions"]]
            confidence_updates = [asdict(c) for c in result["confidence_updates"]]

            self._write_jsonl(self.task_outcomes_file, outcomes)
            self._write_jsonl(self.self_questions_file, questions)
            self._write_jsonl(self.confidence_updates_file, confidence_updates)

            policy_update = self.policy_updater.update_from_outcomes(outcomes)
            policy_update["wave"] = wave
            policy_update["timestamp"] = datetime.utcnow().isoformat()
            self._write_jsonl(self.policy_updates_file, [policy_update])

            wave_stats = {
                "wave": wave,
                "total_tasks": len(outcomes),
                "completed": sum(1 for o in outcomes if o.get("status") == "completed"),
                "failed": sum(1 for o in outcomes if o.get("status") == "failed"),
                "deferred": sum(1 for o in outcomes if o.get("status") == "deferred"),
                "success_rate": (
                    sum(1 for o in outcomes if o.get("status") == "completed") / len(outcomes)
                    if outcomes else 0.0
                )
            }
            (wave_dir / "wave_metrics.json").write_text(json.dumps(wave_stats, indent=2), encoding="utf-8")
            self.wave_stats.append(wave_stats)

        self._write_ui_state()
        self._write_report()

    def _write_report(self):
        report_path = self.output_dir / "PHASE_10_READINESS_REPORT.md"
        lines = [
            "# Phase 10 Readiness Report — Autonomous Adaptation",
            "",
            f"Generated: {datetime.utcnow().isoformat()}",
            "",
            "## Wave Statistics",
        ]
        for wave in self.wave_stats:
            lines.append(
                f"- Wave {wave['wave']}: total={wave['total_tasks']}, completed={wave['completed']}, "
                f"failed={wave['failed']}, deferred={wave['deferred']}"
            )

        lines.extend([
            "",
            "## Safety & Adaptation",
            "- High-risk tasks remain deferred unless confidence >= 0.8",
            "- All executions remain dry-run",
            "- Policy updates logged per wave",
            "",
            "## Outputs",
            "- self_questions.jsonl",
            "- task_outcomes.jsonl",
            "- confidence_updates.jsonl",
            "- policy_updates.jsonl",
        ])

        report_path.write_text("\n".join(lines), encoding="utf-8")

    def _write_ui_state(self):
        ui_state = {
            "generated_at": datetime.utcnow().isoformat(),
            "wave_stats": self.wave_stats,
            "policy": self.policy_updater.policy.to_dict()
        }
        (self.output_dir / "phase10_ui_state.json").write_text(
            json.dumps(ui_state, indent=2),
            encoding="utf-8"
        )


def _parse_args():
    parser = argparse.ArgumentParser(description="Buddy Phase 10 Adaptive Harness")
    parser.add_argument("--waves", type=int, default=3, help="Number of waves to execute")
    parser.add_argument("--output-dir", default="outputs/phase10", help="Output directory")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    harness = AdaptiveHarness(output_dir=args.output_dir)
    harness.run(waves=args.waves)
    print(f"Phase 10 complete. Logs saved to {harness.output_dir}")
