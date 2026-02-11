"""
Phase 15: Autonomous Real-Time Operation Harness

Orchestrates autonomous wave execution with real-time policy adaptation,
safety gate enforcement, and complete observability.
"""

import json
import argparse
from dataclasses import asdict
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime

from buddy_phase15_executor import AutonomousExecutor, TaskOutcome
from buddy_phase15_policy_adapter import PolicyAdapter
from buddy_safety_gate import SafetyGate


class AutonomousOperationHarness:
    """Phase 15: Autonomous Real-Time Operation."""

    def __init__(
        self,
        phase14_dir: str = "outputs/phase14",
        output_dir: str = "outputs/phase15",
        dry_run: bool = False,
        require_approval: bool = False,
    ):
        self.phase14_dir = Path(phase14_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.dry_run = dry_run

        # Load Phase 14 data
        self.planned_tasks = self._load_jsonl(self.phase14_dir / "planned_tasks.jsonl")
        self.meta_insights = self._load_jsonl(self.phase14_dir / "meta_insights.jsonl")
        self.heuristics = self._load_jsonl(self.phase14_dir / "heuristics.jsonl")
        self.ui_state = self._load_json(self.phase14_dir / "phase14_ui_state.json")

        # Initialize policy from Phase 14
        self.initial_policy = self.ui_state.get("policy", {
            "high_risk_threshold": 0.8,
            "retry_multiplier": 1.0,
            "priority_bias": 1.0,
        })

        # Initialize components
        self.safety_gate = SafetyGate(require_approval=require_approval)
        self.policy_adapter = PolicyAdapter(self.initial_policy, str(self.output_dir))
        self.executor = AutonomousExecutor(
            self.safety_gate, self.initial_policy, str(self.output_dir), dry_run=dry_run
        )

        # Execution state
        self.all_outcomes: List[TaskOutcome] = []
        self.wave_stats = []
        self.all_confidence_updates = []

    def _load_jsonl(self, path: Path) -> List[Dict[str, Any]]:
        """Load JSONL file."""
        if not path.exists():
            return []
        data = []
        try:
            with open(path, "r") as f:
                for line in f:
                    if line.strip():
                        data.append(json.loads(line))
        except Exception as e:
            print(f"Warning: Failed to load {path}: {e}")
        return data

    def _load_json(self, path: Path) -> Dict[str, Any]:
        """Load JSON file."""
        if not path.exists():
            return {}
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load {path}: {e}")
            return {}

    def run(self, waves: int = 3) -> Dict[str, Any]:
        """Execute autonomous operations."""
        print(f"\n{'='*70}")
        print("PHASE 15: AUTONOMOUS REAL-TIME OPERATION")
        print(f"{'='*70}\n")

        # Step 1: Load and validate Phase 14 plans
        print("[STEP 1] Loading Phase 14 plans and heuristics...")
        print(f"  ✓ Loaded {len(self.planned_tasks)} planned tasks")
        print(f"  ✓ Loaded {len(self.meta_insights)} insights")
        print(f"  ✓ Loaded {len(self.heuristics)} heuristics\n")

        # Step 2: Execute waves
        print(f"[STEP 2] Executing {waves} autonomous waves...")

        for wave in range(1, waves + 1):
            # Get tasks for this wave
            wave_tasks = [t for t in self.planned_tasks if t.get("wave") == wave]

            if not wave_tasks:
                # Generate tasks if not in plan (fallback)
                wave_tasks = self._generate_wave_tasks(wave)

            # Execute wave
            outcomes, summary = self.executor.execute_wave(wave, wave_tasks)

            self.all_outcomes.extend(outcomes)
            self.all_confidence_updates.extend(self.executor.get_confidence_updates())
            self.wave_stats.append(summary)

            # Adapt policy based on outcomes
            self.policy_adapter.record_wave_metrics(wave, outcomes, self.meta_insights)

            print(f"  Wave {wave}: {summary['completed']}/{summary['total_tasks']} completed "
                  f"(success: {summary['success_rate']*100:.1f}%)")

        print()

        # Step 3: Write outputs
        print("[STEP 3] Writing structured outputs...")
        self._write_wave_outputs()
        self._write_aggregate_logs()
        self._write_ui_state()
        self._write_report()
        print("  ✓ All outputs written\n")

        return {
            "status": "complete",
            "waves_executed": waves,
            "total_outcomes": len(self.all_outcomes),
            "wave_stats": self.wave_stats,
        }

    def _generate_wave_tasks(self, wave: int) -> List[Dict[str, Any]]:
        """Generate fallback tasks for wave."""
        return [
            {
                "task_id": f"wave{wave}_task{i+1}",
                "wave": wave,
                "title": f"Execute task {i+1}",
                "tool": "web_action",
                "risk_level": "LOW" if i % 3 == 0 else "MEDIUM",
                "confidence": 0.85 if i % 3 == 0 else 0.75,
                "priority": 10 - i,
            }
            for i in range(3)
        ]

    def _write_wave_outputs(self) -> None:
        """Write per-wave outputs."""
        for wave in range(1, len(self.wave_stats) + 1):
            wave_dir = self.output_dir / f"wave_{wave}"
            wave_dir.mkdir(exist_ok=True)

            wave_outcomes = [o for o in self.all_outcomes if o.wave == wave]

            # Write outcomes
            with open(wave_dir / "task_outcomes.jsonl", "w") as f:
                for outcome in wave_outcomes:
                    outcome_dict = asdict(outcome)
                    outcome_dict["status"] = outcome.status.value
                    f.write(json.dumps(outcome_dict) + "\n")

            # Write confidence updates
            wave_updates = [u for u in self.all_confidence_updates if u.wave == wave]
            with open(wave_dir / "confidence_updates.jsonl", "w") as f:
                for update in wave_updates:
                    f.write(json.dumps(asdict(update)) + "\n")

    def _write_aggregate_logs(self) -> None:
        """Write aggregate JSONL logs."""
        # Task outcomes
        with open(self.output_dir / "task_outcomes.jsonl", "w") as f:
            for outcome in self.all_outcomes:
                outcome_dict = asdict(outcome)
                outcome_dict["status"] = outcome.status.value
                f.write(json.dumps(outcome_dict) + "\n")

        # Confidence updates
        with open(self.output_dir / "confidence_updates.jsonl", "w") as f:
            for update in self.all_confidence_updates:
                f.write(json.dumps(asdict(update)) + "\n")

        # Policy updates
        with open(self.output_dir / "policy_updates.jsonl", "w") as f:
            for update in self.policy_adapter.get_policy_history():
                f.write(json.dumps(asdict(update)) + "\n")

        # Safety gate decisions
        with open(self.output_dir / "safety_gate_decisions.jsonl", "w") as f:
            for decision in self.safety_gate.get_decisions():
                f.write(json.dumps(decision) + "\n")

    def _write_ui_state(self) -> None:
        """Write Phase 15 UI state."""
        ui_state = {
            "generated_at": datetime.utcnow().isoformat(),
            "phase": 15,
            "execution_mode": "autonomous_real_time",
            "dry_run": self.dry_run,
            "wave_stats": self.wave_stats,
            "policy_summary": self.policy_adapter.get_summary(),
            "execution_summary": {
                "total_waves": len(self.wave_stats),
                "total_tasks": len(self.all_outcomes),
                "completed": sum(1 for o in self.all_outcomes if o.status.value == "completed"),
                "failed": sum(1 for o in self.all_outcomes if o.status.value == "failed"),
                "deferred": sum(1 for o in self.all_outcomes if o.status.value == "deferred"),
                "rolled_back": sum(1 for o in self.all_outcomes if o.status.value == "rolled_back"),
                "overall_success_rate": sum(
                    s.get("success_rate", 0) for s in self.wave_stats
                ) / len(self.wave_stats) if self.wave_stats else 0.0,
            },
        }

        with open(self.output_dir / "phase15_ui_state.json", "w") as f:
            json.dump(ui_state, f, indent=2)

    def _write_report(self) -> None:
        """Write comprehensive Phase 15 report."""
        report_path = self.output_dir / "PHASE_15_AUTONOMOUS_EXECUTION.md"

        with open(report_path, "w") as f:
            f.write("# Phase 15: Autonomous Real-Time Operation Report\n\n")
            f.write(f"Generated: {datetime.utcnow().isoformat()}\n\n")

            f.write("## Executive Summary\n\n")
            f.write(f"Phase 15 executed {len(self.wave_stats)} autonomous waves using Phase 14 plans ")
            f.write(f"with real-time policy adaptation and safety gate enforcement.\n\n")

            # Execution metrics
            f.write("## Execution Metrics\n\n")
            total_tasks = len(self.all_outcomes)
            completed = sum(1 for o in self.all_outcomes if o.status.value == "completed")
            failed = sum(1 for o in self.all_outcomes if o.status.value == "failed")
            deferred = sum(1 for o in self.all_outcomes if o.status.value == "deferred")
            rolled_back = sum(1 for o in self.all_outcomes if o.status.value == "rolled_back")

            f.write(f"- **Total Tasks:** {total_tasks}\n")
            f.write(f"- **Completed:** {completed} ({completed/total_tasks*100:.1f}%)\n")
            f.write(f"- **Failed:** {failed}\n")
            f.write(f"- **Deferred:** {deferred}\n")
            f.write(f"- **Rolled Back:** {rolled_back}\n\n")

            # Wave results
            f.write("## Wave-by-Wave Results\n\n")
            for stats in self.wave_stats:
                f.write(f"### Wave {stats['wave']}\n\n")
                f.write(f"- Completed: {stats['completed']}/{stats['total_tasks']}\n")
                f.write(f"- Success Rate: {stats['success_rate']*100:.1f}%\n")
                f.write(f"- Avg Confidence Delta: {stats['avg_confidence_delta']:+.3f}\n\n")

            # Policy adaptation
            f.write("## Policy Adaptation\n\n")
            policy_summary = self.policy_adapter.get_summary()
            f.write(f"- Initial Policy: {policy_summary['initial_policy']}\n")
            f.write(f"- Final Policy: {policy_summary['current_policy']}\n")
            f.write(f"- Policy Updates: {policy_summary['updates_count']}\n\n")

            f.write("## Outputs Generated\n\n")
            f.write("- `task_outcomes.jsonl` - All task execution outcomes\n")
            f.write("- `confidence_updates.jsonl` - Confidence trajectories\n")
            f.write("- `policy_updates.jsonl` - Policy adaptation history\n")
            f.write("- `safety_gate_decisions.jsonl` - Safety gate decisions\n")
            f.write("- `phase15_ui_state.json` - UI state snapshot\n")
            f.write("- `wave_*/` - Per-wave detailed results\n\n")

            f.write("## Phase 16 Readiness\n\n")
            f.write("Phase 15 outputs ready for Phase 16 autonomous refinement:\n")
            f.write("- Task execution history with real-time outcomes\n")
            f.write("- Confidence calibration under live conditions\n")
            f.write("- Policy evolution trajectory\n")
            f.write("- Safety gate performance metrics\n")


def main():
    parser = argparse.ArgumentParser(description="Phase 15: Autonomous Real-Time Operation")
    parser.add_argument("--waves", type=int, default=3, help="Number of waves to execute")
    parser.add_argument("--output-dir", default="outputs/phase15", help="Output directory")
    parser.add_argument("--phase14-dir", default="outputs/phase14", help="Phase 14 directory")
    parser.add_argument("--dry-run", action="store_true", help="Execute in dry-run mode")
    parser.add_argument("--require-approval", action="store_true", help="Require approval for all non-LOW tasks")

    args = parser.parse_args()

    harness = AutonomousOperationHarness(
        phase14_dir=args.phase14_dir,
        output_dir=args.output_dir,
        dry_run=args.dry_run,
        require_approval=args.require_approval,
    )

    result = harness.run(waves=args.waves)

    print(f"{'='*70}")
    print("PHASE 15 EXECUTION COMPLETE")
    print(f"{'='*70}")
    print(f"\nWaves Executed: {args.waves}")
    print(f"Total Tasks: {result['total_outcomes']}")
    print(f"Outputs: {args.output_dir}")


if __name__ == "__main__":
    main()

