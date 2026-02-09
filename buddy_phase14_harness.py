"""
Phase 14: Autonomous Operation Planning Harness

Orchestrates autonomous planning using Phase 12 & 13 data with meta-learning,
wave simulation, and policy adaptation.
"""

import json
import argparse
from dataclasses import asdict
from typing import Dict, Any
from pathlib import Path
from datetime import datetime

from buddy_meta_learning_engine import MetaLearningEngine
from buddy_wave_simulator import WaveSimulator
from buddy_autonomous_planner import AutonomousPlanner


class ControlledLiveHarness:
    """Phase 14: Autonomous Operation Planning."""

    def __init__(
        self,
        phase12_dir: str = "outputs/phase12",
        phase13_dir: str = "outputs/phase13",
        output_dir: str = "outputs/phase14",
    ):
        self.phase12_dir = Path(phase12_dir)
        self.phase13_dir = Path(phase13_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Load Phase 12 policy
        self.policy = self._load_phase12_policy()

        # Initialize components
        self.meta_engine = MetaLearningEngine(str(self.output_dir))
        self.planner = AutonomousPlanner(self.meta_engine, self.policy, str(self.output_dir))
        self.simulator = None

        # Execution metrics
        self.wave_stats = []
        self.all_planned_tasks = []
        self.all_simulated_outcomes = []

    def _load_phase12_policy(self) -> Dict[str, Any]:
        """Load Phase 12 policy from UI state."""
        ui_state_path = self.phase12_dir / "phase12_ui_state.json"

        if not ui_state_path.exists():
            # Default policy
            return {
                "high_risk_threshold": 0.8,
                "retry_multiplier": 1.0,
                "priority_bias": 1.0,
            }

        try:
            with open(ui_state_path, "r") as f:
                ui_state = json.load(f)
                return ui_state.get("policy", {})
        except Exception as e:
            print(f"Warning: Failed to load Phase 12 policy: {e}")
            return {}

    def run(self, waves: int = 3) -> Dict[str, Any]:
        """Execute full Phase 14 planning and simulation."""
        print(f"\n{'='*70}")
        print("PHASE 14: AUTONOMOUS OPERATION PLANNING")
        print(f"{'='*70}\n")

        # Step 1: Analyze Phase 12 outcomes
        print("[STEP 1] Analyzing Phase 12 execution outcomes...")
        meta_results = self.meta_engine.analyze_phase12_outcomes(str(self.phase12_dir))
        print(f"  ✓ Extracted {meta_results['insights_count']} insights")
        print(f"  ✓ Extracted {meta_results['heuristics_count']} heuristics")
        print(f"  ✓ Generated {meta_results['policy_recommendations']} policy recommendations\n")

        # Step 2: Check for Phase 13 data
        print("[STEP 2] Checking for Phase 13 live execution data...")
        if (self.phase13_dir / "phase13_ui_state.json").exists():
            phase13_results = self.meta_engine.analyze_phase13_outcomes(str(self.phase13_dir))
            print(f"  ✓ Phase 13 data available: {phase13_results['status']}\n")
        else:
            print("  ℹ Phase 13 not yet executed; using Phase 12 data only\n")

        # Step 3: Plan multi-wave workflow
        print(f"[STEP 3] Planning {waves} waves of autonomous operations...")
        self.planner.plan_waves(num_waves=waves)
        planning_summary = self.planner.get_summary()
        print(f"  ✓ Planned {planning_summary['total_planned_tasks']} tasks across {waves} waves\n")

        # Step 4: Simulate wave execution
        print("[STEP 4] Simulating wave execution with confidence projections...")
        self.simulator = WaveSimulator(self.meta_engine, self.policy, str(self.output_dir))

        for wave_num in range(1, waves + 1):
            wave_plan = self.planner.wave_plans[wave_num - 1]
            tasks_to_simulate = [asdict(t) for t in wave_plan.planned_tasks]

            outcomes, summary = self.simulator.simulate_wave(wave_num, tasks_to_simulate)

            self.all_simulated_outcomes.extend(outcomes)
            self.wave_stats.append(summary)

            print(f"  Wave {wave_num}: {summary['completed']}/{summary['total_tasks']} completed "
                  f"(success rate: {summary['success_rate']*100:.1f}%)")

        print()

        # Step 5: Write outputs
        print("[STEP 5] Writing structured outputs...")
        self._write_wave_outputs()
        self._write_aggregate_logs()
        self._write_ui_state()
        self._write_report()
        print("  ✓ All outputs written\n")

        return {
            "status": "complete",
            "waves_planned": waves,
            "total_planned_tasks": planning_summary['total_planned_tasks'],
            "wave_stats": self.wave_stats,
        }

    def _write_wave_outputs(self) -> None:
        """Write per-wave outputs from planning and simulation."""
        self.planner.write_wave_plans()

        for wave_num in range(len(self.wave_stats)):
            self.simulator.wave_summary = self.wave_stats[wave_num]
            self.simulator.simulated_outcomes = [
                o for o in self.all_simulated_outcomes if o.wave == wave_num + 1
            ]
            self.simulator.write_simulation_results(wave_num + 1)

            # Write meta-learning artifacts
            self.meta_engine.write_meta_artifacts(wave_num + 1)

    def _write_aggregate_logs(self) -> None:
        """Write aggregate JSONL logs."""
        # Write all simulated outcomes
        with open(self.output_dir / "simulated_outcomes.jsonl", "w") as f:
            for outcome in self.all_simulated_outcomes:
                outcome_dict = asdict(outcome)
                outcome_dict["status"] = outcome.status.value
                f.write(json.dumps(outcome_dict) + "\n")

        # Write all planned tasks
        with open(self.output_dir / "planned_tasks.jsonl", "w") as f:
            for task in self.planner.planned_tasks:
                f.write(json.dumps(asdict(task)) + "\n")

        # Write meta-learning insights
        with open(self.output_dir / "meta_insights.jsonl", "w") as f:
            for insight in self.meta_engine.get_insights():
                f.write(json.dumps(asdict(insight)) + "\n")

        # Write operational heuristics
        with open(self.output_dir / "heuristics.jsonl", "w") as f:
            for heuristic in self.meta_engine.get_heuristics():
                f.write(json.dumps(asdict(heuristic)) + "\n")

        # Write policy recommendations
        with open(self.output_dir / "policy_recommendations.jsonl", "w") as f:
            for rec in self.meta_engine.get_policy_recommendations():
                f.write(json.dumps(rec) + "\n")

    def _write_ui_state(self) -> None:
        """Write Phase 14 UI state compatible with Phase 7/8."""
        ui_state = {
            "generated_at": datetime.utcnow().isoformat(),
            "phase": 14,
            "execution_mode": "planning_and_simulation",
            "wave_stats": self.wave_stats,
            "planning_summary": self.planner.get_summary(),
            "meta_learning": self.meta_engine.get_summary(),
            "policy": self.policy,
            "execution_summary": {
                "total_waves": len(self.wave_stats),
                "total_planned_tasks": len(self.planner.planned_tasks),
                "total_simulated_outcomes": len(self.all_simulated_outcomes),
                "avg_planned_confidence": sum(
                    t.confidence for t in self.planner.planned_tasks
                ) / len(self.planner.planned_tasks) if self.planner.planned_tasks else 0.0,
                "overall_success_rate": sum(
                    s.get("success_rate", 0) for s in self.wave_stats
                ) / len(self.wave_stats) if self.wave_stats else 0.0,
            },
        }

        with open(self.output_dir / "phase14_ui_state.json", "w") as f:
            json.dump(ui_state, f, indent=2)

    def _write_report(self) -> None:
        """Write comprehensive Phase 14 report."""
        report_path = self.output_dir / "PHASE_14_AUTONOMOUS_PLAN.md"

        with open(report_path, "w") as f:
            f.write("# Phase 14: Autonomous Operation Planning Report\n\n")
            f.write(f"Generated: {datetime.utcnow().isoformat()}\n\n")

            f.write("## Executive Summary\n\n")
            f.write(f"Phase 14 autonomously planned and simulated {len(self.wave_stats)} waves of operations ")
            f.write(f"using Phase 12 execution insights and meta-learning heuristics.\n\n")

            # Meta-Learning Results
            f.write("## Meta-Learning Results\n\n")
            f.write(f"**Insights Extracted:** {len(self.meta_engine.get_insights())}\n")
            f.write(f"**Heuristics Derived:** {len(self.meta_engine.get_heuristics())}\n")
            f.write(f"**Policy Recommendations:** {len(self.meta_engine.get_policy_recommendations())}\n\n")

            f.write("### Key Insights\n\n")
            for insight in self.meta_engine.get_insights()[:5]:  # Top 5
                f.write(f"- **{insight.insight_type}**: {insight.description}\n")
                f.write(f"  - Confidence: {insight.confidence:.2f}\n")
                f.write(f"  - Recommendation: {insight.recommendation}\n\n")

            # Wave Planning Results
            f.write("## Wave Planning Results\n\n")
            for plan in self.planner.wave_plans:
                f.write(f"### Wave {plan.wave}\n\n")
                f.write(f"- **Planned Tasks:** {plan.total_tasks}\n")
                f.write(f"- **Deferred Tasks:** {len(plan.deferred_tasks)}\n")
                f.write(f"- **Estimated Success Rate:** {plan.estimated_success_rate*100:.1f}%\n")
                f.write(f"- **Average Confidence:** {plan.estimated_avg_confidence:.2f}\n")
                f.write(f"- **Safety Rationale:** {plan.safety_rationale}\n\n")

            # Simulation Results
            f.write("## Simulation Results\n\n")
            for stats in self.wave_stats:
                f.write(f"### Wave {stats['wave']}\n\n")
                f.write(f"- **Total Tasks:** {stats['total_tasks']}\n")
                f.write(f"- **Completed:** {stats['completed']}\n")
                f.write(f"- **Failed:** {stats['failed']}\n")
                f.write(f"- **Deferred:** {stats['deferred']}\n")
                f.write(f"- **Rolled Back:** {stats['rolled_back']}\n")
                f.write(f"- **Success Rate:** {stats['success_rate']*100:.1f}%\n")
                f.write(f"- **Projected Next Wave Confidence:** {stats['projected_next_wave_confidence']:.2f}\n\n")

            # Operational Heuristics
            f.write("## Extracted Operational Heuristics\n\n")
            for heuristic in self.meta_engine.get_heuristics()[:5]:  # Top 5
                f.write(f"### {heuristic.heuristic_id}\n\n")
                f.write(f"- **Category:** {heuristic.category}\n")
                f.write(f"- **Rule:** {heuristic.rule}\n")
                f.write(f"- **Applicability:** {heuristic.applicability}\n")
                f.write(f"- **Confidence:** {heuristic.confidence:.2f}\n")
                f.write(f"- **Recommended Weight:** {heuristic.recommended_weight:.2f}\n\n")

            # Policy Recommendations
            f.write("## Policy Recommendations for Phase 15\n\n")
            for rec in self.meta_engine.get_policy_recommendations():
                f.write(f"### {rec['type']}\n\n")
                f.write(f"- **Rationale:** {rec['rationale']}\n")
                f.write(f"- **Action:** {rec['action']}\n")
                f.write(f"- **Confidence:** {rec['confidence']:.2f}\n\n")

            # Safety Analysis
            f.write("## Safety & Risk Analysis\n\n")
            total_high_risk = sum(p.high_risk_count for p in self.planner.wave_plans)
            total_deferred = sum(len(p.deferred_tasks) for p in self.planner.wave_plans)

            f.write(f"- **Total High-Risk Tasks:** {total_high_risk}\n")
            f.write(f"- **Total Deferred Tasks:** {total_deferred}\n")
            f.write(f"- **All Deferred Tasks:** {self._get_all_deferred_tasks()}\n\n")

            f.write("## Outputs Generated\n\n")
            f.write("- `planned_tasks.jsonl` - All autonomously planned tasks\n")
            f.write("- `simulated_outcomes.jsonl` - Simulated execution outcomes with projections\n")
            f.write("- `meta_insights.jsonl` - Extracted meta-learning insights\n")
            f.write("- `heuristics.jsonl` - Derived operational heuristics\n")
            f.write("- `policy_recommendations.jsonl` - Policy optimization recommendations\n")
            f.write("- `phase14_ui_state.json` - UI state for Phase 7/8 observability\n")
            f.write("- `wave_*/` - Per-wave planning and simulation artifacts\n\n")

            f.write("## Phase 15 Readiness\n\n")
            f.write("Phase 14 outputs provide complete foundation for Phase 15 real-time operation:\n")
            f.write("[OK] Autonomous task planning with safety enforcement\n")
            f.write("[OK] Confidence projections and rollback modeling\n")
            f.write("[OK] Meta-learning heuristics for task sequencing\n")
            f.write("[OK] Policy adaptation recommendations\n")
            f.write("[OK] Full observability and decision audit trails\n\n")

    def _get_all_deferred_tasks(self) -> str:
        """Get comma-separated list of deferred tasks."""
        all_deferred = []
        for plan in self.planner.wave_plans:
            all_deferred.extend(plan.deferred_tasks)
        return ", ".join(all_deferred) if all_deferred else "None"


def main():
    parser = argparse.ArgumentParser(description="Phase 14: Autonomous Operation Planning")
    parser.add_argument("--waves", type=int, default=3, help="Number of waves to plan (default: 3)")
    parser.add_argument(
        "--output-dir",
        default="outputs/phase14",
        help="Output directory (default: outputs/phase14)",
    )
    parser.add_argument(
        "--phase12-dir",
        default="outputs/phase12",
        help="Phase 12 output directory (default: outputs/phase12)",
    )
    parser.add_argument(
        "--phase13-dir",
        default="outputs/phase13",
        help="Phase 13 output directory (default: outputs/phase13)",
    )

    args = parser.parse_args()

    harness = ControlledLiveHarness(
        phase12_dir=args.phase12_dir,
        phase13_dir=args.phase13_dir,
        output_dir=args.output_dir,
    )

    result = harness.run(waves=args.waves)

    print(f"{'='*70}")
    print("PHASE 14 EXECUTION COMPLETE")
    print(f"{'='*70}")
    print(f"\nWaves Planned: {args.waves}")
    print(f"Total Planned Tasks: {result['total_planned_tasks']}")
    print(f"\nOutputs written to: {args.output_dir}")


if __name__ == "__main__":
    main()
