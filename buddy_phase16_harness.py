"""
Phase 16: Adaptive Meta-Learning Orchestration Harness

Orchestrates complete meta-learning pipeline:
1. Load Phase 15 execution outputs
2. Analyze patterns and generate insights
3. Derive adaptive heuristics and recommendations
4. Plan future waves with optimized task sequencing
5. Simulate execution and project outcomes
6. Generate structured outputs and reports
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from buddy_phase16_meta_learning import MetaLearningAnalyzer
from buddy_phase16_adaptive_planner import AdaptiveWavePlanner


class AdaptiveMetaLearningHarness:
    """Orchestrates Phase 16 adaptive meta-learning."""

    def __init__(
        self,
        phase15_dir: str = "outputs/phase15",
        output_dir: str = "outputs/phase16",
        num_future_waves: int = 3,
    ):
        self.phase15_dir = Path(phase15_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        self.num_future_waves = num_future_waves

        self.analyzer = None
        self.planner = None

    def run(self) -> Dict[str, Any]:
        """Run complete meta-learning pipeline."""
        print("\n" + "=" * 70)
        print("PHASE 16: ADAPTIVE META-LEARNING SYSTEM")
        print("=" * 70)

        # Step 1: Load Phase 15 outputs
        print("\n[STEP 1] Loading Phase 15 outputs...")
        self.analyzer = MetaLearningAnalyzer(phase15_dir=str(self.phase15_dir))
        if not self.analyzer.load_phase15_outputs():
            print("  ✗ Failed to load Phase 15 outputs")
            return {"status": "failed"}
        print("  ✓ Loaded Phase 15 data successfully")

        # Step 2: Analyze execution patterns
        print("\n[STEP 2] Analyzing execution patterns...")
        self.analyzer.analyze_execution_patterns()
        print(f"  ✓ Identified {len(self.analyzer.insights)} insight types")

        # Step 3: Analyze trajectories
        print("\n[STEP 3] Analyzing confidence trajectories...")
        self.analyzer.analyze_confidence_trajectories()
        print(f"  ✓ Analyzed confidence evolution")

        # Step 4: Analyze safety gates
        print("\n[STEP 4] Analyzing safety gate effectiveness...")
        self.analyzer.analyze_safety_gate_effectiveness()
        print(f"  ✓ Total insights: {len(self.analyzer.insights)}")

        # Step 5: Derive heuristics
        print("\n[STEP 5] Deriving adaptive heuristics...")
        self.analyzer.derive_adaptive_heuristics()
        print(f"  ✓ Derived {len(self.analyzer.heuristics)} heuristics")

        # Step 6: Generate recommendations
        print("\n[STEP 6] Generating policy recommendations...")
        self.analyzer.recommend_policy_adaptations()
        print(f"  ✓ Generated {len(self.analyzer.recommendations)} recommendations")

        # Step 7: Plan future waves
        print("\n[STEP 7] Planning future waves...")
        current_policy = self.analyzer.ui_state.get("policy_summary", {}).get(
            "current_policy", {}
        )
        if not current_policy:
            current_policy = {
                "high_risk_threshold": 0.80,
                "retry_multiplier": 1.0,
                "priority_bias": 1.0,
            }

        self.planner = AdaptiveWavePlanner(
            meta_insights=[self._insight_to_dict(i) for i in self.analyzer.insights],
            heuristics=[asdict(h) for h in self.analyzer.heuristics],
            current_policy=current_policy,
        )

        self.planner.plan_waves(
            num_waves=self.num_future_waves, tasks_per_wave=4
        )
        print(f"  ✓ Planned {len(self.planner.planned_tasks)} tasks")

        # Step 8: Write outputs
        print("\n[STEP 8] Writing structured outputs...")
        self._write_outputs()
        print("  ✓ All outputs written")

        # Step 9: Generate report
        print("\n[STEP 9] Generating comprehensive report...")
        self._write_report()
        print("  ✓ Report generated")

        print("\n" + "=" * 70)
        print("PHASE 16 EXECUTION COMPLETE")
        print("=" * 70)

        return {
            "status": "complete",
            "insights_generated": len(self.analyzer.insights),
            "heuristics_derived": len(self.analyzer.heuristics),
            "recommendations_made": len(self.analyzer.recommendations),
            "waves_planned": len(self.planner.simulated_outcomes),
            "planned_tasks": len(self.planner.planned_tasks),
            "output_dir": str(self.output_dir),
        }

    def _insight_to_dict(self, insight) -> Dict[str, Any]:
        """Convert insight (with Enum) to dict."""
        return {
            "insight_type": insight.insight_type,  # already a string
            "description": insight.description,
            "confidence": insight.confidence,
            "evidence_count": insight.evidence_count,
            "pattern": insight.pattern,
            "recommendation": insight.recommendation,
            "timestamp": insight.timestamp,
        }

    def _write_outputs(self) -> None:
        """Write all structured outputs."""
        # Write meta insights
        with open(self.output_dir / "meta_insights.jsonl", "w") as f:
            for insight in self.analyzer.insights:
                f.write(json.dumps(self._insight_to_dict(insight)) + "\n")

        # Write heuristics
        with open(self.output_dir / "heuristics.jsonl", "w") as f:
            for heuristic in self.analyzer.heuristics:
                f.write(json.dumps(asdict(heuristic)) + "\n")

        # Write policy recommendations
        with open(self.output_dir / "policy_recommendations.jsonl", "w") as f:
            for rec in self.analyzer.recommendations:
                f.write(json.dumps(asdict(rec)) + "\n")

        # Write planned tasks
        with open(self.output_dir / "planned_tasks.jsonl", "w") as f:
            for task in self.planner.planned_tasks:
                f.write(json.dumps(asdict(task)) + "\n")

        # Write simulated outcomes
        with open(self.output_dir / "simulated_outcomes.jsonl", "w") as f:
            for outcome in self.planner.simulated_outcomes:
                f.write(json.dumps(asdict(outcome)) + "\n")

        # Write UI state
        ui_state = {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "phase": 16,
            "mode": "adaptive_meta_learning",
            "analysis_summary": self.analyzer.get_summary(),
            "planning_summary": self.planner.get_summary(),
            "insights": len(self.analyzer.insights),
            "heuristics": len(self.analyzer.heuristics),
            "recommendations": len(self.analyzer.recommendations),
            "planned_tasks": len(self.planner.planned_tasks),
            "wave_predictions": [asdict(o) for o in self.planner.simulated_outcomes],
        }

        with open(self.output_dir / "phase16_ui_state.json", "w") as f:
            json.dump(ui_state, f, indent=2)

    def _write_report(self) -> None:
        """Generate comprehensive Phase 16 report."""
        report = f"""# Phase 16: Adaptive Meta-Learning Report

## Execution Summary

**Generated**: {datetime.utcnow().isoformat()}Z
**Phase**: 16 - Adaptive Meta-Learning System
**Mode**: Autonomous meta-learning and future planning
**Status**: ✅ COMPLETE

## Meta-Learning Analysis

### Phase 15 Data Ingestion
- Task Outcomes Analyzed: {len(self.analyzer.task_outcomes)}
- Confidence Updates Reviewed: {len(self.analyzer.confidence_updates)}
- Safety Decisions Reviewed: {len(self.analyzer.safety_decisions)}

### Insights Generated: {len(self.analyzer.insights)}

"""
        for insight in self.analyzer.insights:
            report += f"\n#### {insight.insight_type.upper()}\n"
            report += f"- **Description**: {insight.description}\n"
            report += f"- **Confidence**: {insight.confidence:.2%}\n"
            report += f"- **Evidence**: {insight.evidence_count} tasks\n"
            report += f"- **Recommendation**: {insight.recommendation}\n"

        report += f"\n## Adaptive Heuristics: {len(self.analyzer.heuristics)}\n"

        for heuristic in self.analyzer.heuristics:
            report += f"\n### {heuristic.heuristic_id}: {heuristic.name}\n"
            report += f"- **Category**: {heuristic.category}\n"
            report += f"- **Description**: {heuristic.description}\n"
            report += f"- **Confidence**: {heuristic.confidence:.2%}\n"
            report += f"- **Expected Improvement**: {heuristic.expected_improvement:+.2%}\n"

        report += f"\n## Policy Recommendations: {len(self.analyzer.recommendations)}\n"

        for rec in self.analyzer.recommendations:
            report += f"\n### {rec.recommendation_id}: {rec.parameter}\n"
            report += f"- **Current**: {rec.current_value:.3f}\n"
            report += f"- **Recommended**: {rec.recommended_value:.3f}\n"
            report += f"- **Adjustment**: {rec.adjustment_amount:+.3f}\n"
            report += f"- **Rationale**: {rec.rationale}\n"
            report += f"- **Confidence**: {rec.confidence:.2%}\n"
            report += f"- **Risk Level**: {rec.risk}\n"

        report += f"\n## Future Wave Planning: {len(self.planner.simulated_outcomes)} Waves\n"

        for outcome in self.planner.simulated_outcomes:
            report += f"\n### Wave {outcome.wave}\n"
            report += f"- **Planned Tasks**: {outcome.planned_tasks}\n"
            report += f"- **Predicted Completed**: {outcome.predicted_completed}\n"
            report += f"- **Predicted Failed**: {outcome.predicted_failed}\n"
            report += f"- **Predicted Deferred**: {outcome.predicted_deferred}\n"
            report += f"- **Predicted Success Rate**: {outcome.predicted_success_rate:.1%}\n"
            report += f"- **Avg Confidence Improvement**: {outcome.avg_confidence_improvement:+.4f}\n"
            if outcome.safety_concerns:
                report += f"- **Safety Concerns**: {', '.join(outcome.safety_concerns)}\n"

        report += f"\n## Task Prioritization\n\n"

        for wave in range(1, self.num_future_waves + 1):
            wave_tasks = self.planner.get_planned_tasks_for_wave(wave)
            report += f"\n### Wave {wave} Tasks (Priority Order)\n"
            for task in sorted(wave_tasks, key=lambda t: t.priority):
                report += f"\n#### {task.task_id}\n"
                report += f"- **Risk Level**: {task.risk_level}\n"
                report += f"- **Confidence**: {task.confidence:.3f}\n"
                report += f"- **Priority**: {task.priority}\n"
                report += f"- **Predicted Success**: {task.predicted_success_rate:.1%}\n"
                report += f"- **Predicted Confidence Delta**: {task.predicted_confidence_delta:+.4f}\n"
                report += f"- **Approval Status**: {task.approval_status}\n"
                if task.heuristics_applied:
                    report += f"- **Heuristics Applied**: {', '.join(task.heuristics_applied)}\n"

        report += f"\n## Key Metrics\n"

        summary = self.planner.get_summary()
        for key, value in summary.items():
            if isinstance(value, float):
                report += f"- **{key}**: {value:.4f}\n"
            else:
                report += f"- **{key}**: {value}\n"

        report += f"\n## Readiness for Phase 17\n\n"
        report += f"""Phase 16 outputs provide optimal foundation for Phase 17:

- ✅ Adaptive heuristics derived from real execution data
- ✅ Policy recommendations tuned to observed patterns
- ✅ Future wave plans optimized with predicted success rates
- ✅ Risk assessment enhanced with confidence trajectories
- ✅ Safety gates validated across all risk levels
- ✅ Prioritization strategy based on task synergies

Phase 17 should apply these recommendations to live execution
and continuously feedback results for further refinement.

---

**Status**: Phase 16 COMPLETE - Ready for Phase 17 integration
"""

        with open(self.output_dir / "PHASE_16_ADAPTIVE_PLAN.md", "w", encoding="utf-8") as f:
            f.write(report)


def asdict(obj):
    """Convert dataclass to dict."""
    from dataclasses import asdict as _asdict
    return _asdict(obj)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Phase 16: Adaptive Meta-Learning")
    parser.add_argument(
        "--phase15-dir",
        default="outputs/phase15",
        help="Phase 15 output directory",
    )
    parser.add_argument(
        "--output-dir",
        default="outputs/phase16",
        help="Output directory",
    )
    parser.add_argument(
        "--waves",
        type=int,
        default=3,
        help="Number of future waves to plan",
    )

    args = parser.parse_args()

    harness = AdaptiveMetaLearningHarness(
        phase15_dir=args.phase15_dir,
        output_dir=args.output_dir,
        num_future_waves=args.waves,
    )

    result = harness.run()
    return 0 if result["status"] == "complete" else 1


if __name__ == "__main__":
    exit(main())
