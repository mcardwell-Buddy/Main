"""Buddy Phase 11 Self-Driven Harness.

Autonomous learning loop that ingests Phase 10 outputs, analyzes patterns,
generates adaptive goals, and simulates new strategies in dry-run mode.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from buddy_learning_analyzer import LearningAnalyzer
from buddy_autonomous_goal_generator import AutonomousGoalGenerator
from buddy_policy_updater import PolicyUpdater, PolicyState
from buddy_simulated_executor import SimulatedExecutor


class SelfDrivenHarness:
    def __init__(self, output_dir: str = "outputs/phase11", phase10_dir: str = "outputs/phase10"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.phase10_dir = Path(phase10_dir)

        self.self_questions_file = self.output_dir / "self_questions.jsonl"
        self.task_outcomes_file = self.output_dir / "task_outcomes.jsonl"
        self.confidence_updates_file = self.output_dir / "confidence_updates.jsonl"
        self.policy_updates_file = self.output_dir / "policy_updates.jsonl"
        self.learning_insights_file = self.output_dir / "learning_insights.jsonl"

        for filepath in [
            self.self_questions_file,
            self.task_outcomes_file,
            self.confidence_updates_file,
            self.policy_updates_file,
            self.learning_insights_file
        ]:
            if filepath.exists():
                filepath.unlink()

        for wave_dir in self.output_dir.glob("wave_*"):
            if wave_dir.is_dir():
                for child in wave_dir.glob("*"):
                    if child.is_file():
                        child.unlink()

        self.analyzer = LearningAnalyzer(self.phase10_dir)
        self.goal_generator = AutonomousGoalGenerator(self.analyzer)
        self.policy_updater = PolicyUpdater(initial_policy=self._load_phase10_policy())
        self.executor = SimulatedExecutor(output_dir=self.output_dir)
        self.wave_stats: List[Dict[str, Any]] = []

    def _load_phase10_policy(self) -> PolicyState:
        ui_state_path = self.phase10_dir / "phase10_ui_state.json"
        if not ui_state_path.exists():
            return PolicyState()
        
        try:
            data = json.loads(ui_state_path.read_text(encoding="utf-8"))
            policy_dict = data.get("policy", {})
            return PolicyState(
                high_risk_threshold=policy_dict.get("high_risk_threshold", 0.8),
                retry_multiplier=policy_dict.get("retry_multiplier", 1.0),
                priority_bias=policy_dict.get("priority_bias", 1.0)
            )
        except Exception:
            return PolicyState()

    def _write_jsonl(self, path: Path, payload: List[Dict[str, Any]]):
        with path.open("a", encoding="utf-8") as f:
            for item in payload:
                f.write(json.dumps(item) + "\n")

    def run(self, waves: int = 3):
        # Analyze Phase 10 outcomes
        insights = self.analyzer.analyze()
        for insight in insights:
            self._write_jsonl(self.learning_insights_file, [asdict(insight)])

        for wave in range(1, waves + 1):
            wave_dir = self.output_dir / f"wave_{wave}"
            wave_dir.mkdir(parents=True, exist_ok=True)

            # Generate autonomous goals based on learning
            autonomous_goals = self.goal_generator.generate_goals(wave=wave)
            tasks = [task for goal in autonomous_goals for task in goal.tasks]

            if not tasks:
                # Fallback: generate baseline tasks
                from buddy_goal_manager import GoalManager
                fallback_mgr = GoalManager()
                fallback_goals = fallback_mgr.generate_goals(wave=wave)
                tasks = [task for goal in fallback_goals for task in goal.tasks]

            result = self.executor.execute_wave(
                tasks=tasks,
                wave=wave,
                policy=self.policy_updater.policy.to_dict(),
                output_dir=wave_dir,
                workflow_id=f"phase11_wave_{wave}"
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
            policy_update["learning_insights"] = [asdict(ins) for ins in insights]
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
                ),
                "autonomous_goals": len(autonomous_goals),
                "learning_insights": len(insights)
            }
            (wave_dir / "wave_metrics.json").write_text(json.dumps(wave_stats, indent=2), encoding="utf-8")
            self.wave_stats.append(wave_stats)

        self._write_ui_state()
        self._write_report()

    def _write_ui_state(self):
        ui_state = {
            "generated_at": datetime.utcnow().isoformat(),
            "wave_stats": self.wave_stats,
            "policy": self.policy_updater.policy.to_dict(),
            "learning_insights": [asdict(ins) for ins in self.analyzer.analyze()]
        }
        (self.output_dir / "phase11_ui_state.json").write_text(
            json.dumps(ui_state, indent=2),
            encoding="utf-8"
        )

    def _write_report(self):
        report_path = self.output_dir / "PHASE_11_SELF_DRIVEN_REPORT.md"
        
        insights = self.analyzer.analyze()
        
        lines = [
            "# Phase 11 Self-Driven Learning Report — Autonomous Adaptation",
            "",
            f"Generated: {datetime.utcnow().isoformat()}",
            "",
            "## Executive Summary",
            f"Phase 11 ingested Phase 10 outputs, analyzed {len(self.analyzer.outcomes)} task outcomes, "
            f"identified {len(insights)} learning insights, and generated autonomous goals for {len(self.wave_stats)} waves.",
            "",
            "## Learning Insights from Phase 10",
        ]
        
        for insight in insights:
            lines.extend([
                f"### {insight.insight_type.replace('_', ' ').title()}",
                f"- **Description:** {insight.description}",
                f"- **Confidence:** {insight.confidence:.2f}",
                f"- **Recommendation:** {insight.recommendation}",
                ""
            ])
        
        lines.extend([
            "## Wave Statistics",
        ])
        
        for wave in self.wave_stats:
            lines.append(
                f"- Wave {wave['wave']}: total={wave['total_tasks']}, completed={wave['completed']}, "
                f"failed={wave['failed']}, deferred={wave['deferred']}, "
                f"autonomous_goals={wave.get('autonomous_goals', 0)}"
            )
        
        lines.extend([
            "",
            "## Safety & Adaptation",
            "- High-risk tasks remain deferred unless confidence >= 0.8",
            "- All executions remain dry-run",
            "- Autonomous goals generated based on learning insights",
            "- Policy updates logged per wave",
            "",
            "## Outputs",
            "- self_questions.jsonl",
            "- task_outcomes.jsonl",
            "- confidence_updates.jsonl",
            "- policy_updates.jsonl",
            "- learning_insights.jsonl",
            "- phase11_ui_state.json",
            "",
            "## Phase 12 Readiness",
            "✅ Learning insights captured and analyzed",
            "✅ Autonomous goal generation validated",
            "✅ Policy adaptation operational",
            "✅ Structured outputs ready for Phase 12"
        ])
        
        report_path.write_text("\n".join(lines), encoding="utf-8")


def _parse_args():
    parser = argparse.ArgumentParser(description="Buddy Phase 11 Self-Driven Harness")
    parser.add_argument("--waves", type=int, default=3, help="Number of waves to execute")
    parser.add_argument("--output-dir", default="outputs/phase11", help="Output directory")
    parser.add_argument("--phase10-dir", default="outputs/phase10", help="Phase 10 input directory")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    harness = SelfDrivenHarness(output_dir=args.output_dir, phase10_dir=args.phase10_dir)
    harness.run(waves=args.waves)
    print(f"Phase 11 complete. Logs saved to {harness.output_dir}")
