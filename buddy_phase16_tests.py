"""
Phase 16: Comprehensive Unit Tests

Tests for meta-learning analyzer, adaptive planner, and harness.
"""

import unittest
from pathlib import Path
from unittest.mock import Mock
import json
import tempfile
from dataclasses import asdict

from buddy_phase16_meta_learning import (
    MetaLearningAnalyzer,
    MetaInsight,
    AdaptiveHeuristic,
)
from buddy_phase16_adaptive_planner import AdaptiveWavePlanner, PlannedTask
from buddy_phase16_harness import AdaptiveMetaLearningHarness


class TestMetaLearningAnalyzer(unittest.TestCase):
    """Test meta-learning analysis."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.phase15_dir = Path(self.temp_dir) / "phase15"
        self.phase15_dir.mkdir(exist_ok=True)

        # Create minimal Phase 15 outputs
        with open(self.phase15_dir / "task_outcomes.jsonl", "w") as f:
            f.write(
                json.dumps(
                    {
                        "task_id": "wave1_task1",
                        "wave": 1,
                        "status": "completed",
                        "risk_level": "LOW",
                        "confidence_before": 0.85,
                        "confidence_after": 0.91,
                    }
                )
                + "\n"
            )

        with open(self.phase15_dir / "confidence_updates.jsonl", "w") as f:
            f.write(
                json.dumps(
                    {
                        "task_id": "wave1_task1",
                        "wave": 1,
                        "confidence_before": 0.85,
                        "confidence_after": 0.91,
                        "delta": 0.06,
                    }
                )
                + "\n"
            )

        with open(self.phase15_dir / "safety_gate_decisions.jsonl", "w") as f:
            f.write(
                json.dumps(
                    {
                        "task_id": "wave1_task1",
                        "risk_level": "LOW",
                        "confidence": 0.85,
                        "approval": "APPROVED",
                    }
                )
                + "\n"
            )

        with open(self.phase15_dir / "policy_updates.jsonl", "w") as f:
            pass  # Empty

        ui_state = {"policy_summary": {"current_policy": {}}}
        with open(self.phase15_dir / "phase15_ui_state.json", "w") as f:
            json.dump(ui_state, f)

    def test_analyzer_initialization(self):
        """Test analyzer initializes correctly."""
        analyzer = MetaLearningAnalyzer(phase15_dir=str(self.phase15_dir))
        self.assertIsNotNone(analyzer)

    def test_load_phase15_outputs(self):
        """Test loading Phase 15 outputs."""
        analyzer = MetaLearningAnalyzer(phase15_dir=str(self.phase15_dir))
        result = analyzer.load_phase15_outputs()

        self.assertTrue(result)
        self.assertGreater(len(analyzer.task_outcomes), 0)
        self.assertGreater(len(analyzer.confidence_updates), 0)

    def test_analyze_execution_patterns(self):
        """Test execution pattern analysis."""
        analyzer = MetaLearningAnalyzer(phase15_dir=str(self.phase15_dir))
        analyzer.load_phase15_outputs()
        analyzer.analyze_execution_patterns()

        self.assertGreater(len(analyzer.insights), 0)

    def test_analyze_confidence_trajectories(self):
        """Test confidence trajectory analysis."""
        analyzer = MetaLearningAnalyzer(phase15_dir=str(self.phase15_dir))
        analyzer.load_phase15_outputs()
        analyzer.analyze_confidence_trajectories()

        self.assertGreater(len(analyzer.insights), 0)

    def test_analyze_safety_gate_effectiveness(self):
        """Test safety gate effectiveness analysis."""
        analyzer = MetaLearningAnalyzer(phase15_dir=str(self.phase15_dir))
        analyzer.load_phase15_outputs()
        analyzer.analyze_safety_gate_effectiveness()

        self.assertGreater(len(analyzer.insights), 0)

    def test_derive_adaptive_heuristics(self):
        """Test heuristic derivation."""
        analyzer = MetaLearningAnalyzer(phase15_dir=str(self.phase15_dir))
        analyzer.load_phase15_outputs()
        analyzer.derive_adaptive_heuristics()

        self.assertGreater(len(analyzer.heuristics), 0)
        self.assertTrue(
            any(h.category == "task_prioritization" for h in analyzer.heuristics)
        )

    def test_recommend_policy_adaptations(self):
        """Test policy adaptation recommendations."""
        analyzer = MetaLearningAnalyzer(phase15_dir=str(self.phase15_dir))
        analyzer.load_phase15_outputs()
        analyzer.recommend_policy_adaptations()

        self.assertGreater(len(analyzer.recommendations), 0)

    def test_analyzer_summary(self):
        """Test analyzer summary generation."""
        analyzer = MetaLearningAnalyzer(phase15_dir=str(self.phase15_dir))
        analyzer.load_phase15_outputs()
        analyzer.analyze_execution_patterns()

        summary = analyzer.get_summary()

        self.assertIn("insights_generated", summary)
        self.assertIn("tasks_analyzed", summary)


class TestAdaptiveWavePlanner(unittest.TestCase):
    """Test adaptive wave planner."""

    def setUp(self):
        self.insights = [
            {
                "insight_type": "success_pattern",
                "description": "HIGH success rate",
                "confidence": 0.95,
            }
        ]
        self.heuristics = [
            {"heuristic_id": "H16_001", "category": "task_prioritization"}
        ]
        self.policy = {
            "high_risk_threshold": 0.80,
            "retry_multiplier": 1.0,
            "priority_bias": 1.0,
        }

    def test_planner_initialization(self):
        """Test planner initializes correctly."""
        planner = AdaptiveWavePlanner(self.insights, self.heuristics, self.policy)
        self.assertIsNotNone(planner)

    def test_plan_single_wave(self):
        """Test planning single wave."""
        planner = AdaptiveWavePlanner(self.insights, self.heuristics, self.policy)
        planner._plan_wave(1, 4)

        self.assertEqual(len(planner.planned_tasks), 4)

    def test_plan_multiple_waves(self):
        """Test planning multiple waves."""
        planner = AdaptiveWavePlanner(self.insights, self.heuristics, self.policy)
        planner.plan_waves(num_waves=3, tasks_per_wave=4)

        self.assertEqual(len(planner.planned_tasks), 12)
        self.assertEqual(len(planner.simulated_outcomes), 3)

    def test_generated_tasks_have_ids(self):
        """Test generated tasks have proper IDs."""
        planner = AdaptiveWavePlanner(self.insights, self.heuristics, self.policy)
        planner._plan_wave(1, 4)

        task_ids = [t.task_id for t in planner.planned_tasks]
        self.assertEqual(len(set(task_ids)), 4)  # All unique
        self.assertTrue(all("wave1" in tid for tid in task_ids))

    def test_safety_gate_compliance(self):
        """Test safety gate compliance for planned tasks."""
        planner = AdaptiveWavePlanner(self.insights, self.heuristics, self.policy)
        planner.plan_waves(num_waves=1, tasks_per_wave=4)

        # All tasks should have approval status
        for task in planner.planned_tasks:
            self.assertIn(
                task.approval_status, ["APPROVED", "DEFERRED", "NEEDS_REVIEW"]
            )

    def test_confidence_predictions(self):
        """Test confidence delta predictions."""
        planner = AdaptiveWavePlanner(self.insights, self.heuristics, self.policy)
        planner.plan_waves(num_waves=1, tasks_per_wave=4)

        for task in planner.planned_tasks:
            self.assertIsNotNone(task.predicted_confidence_delta)
            self.assertLess(task.predicted_confidence_delta, 0.5)

    def test_planner_summary(self):
        """Test planner summary."""
        planner = AdaptiveWavePlanner(self.insights, self.heuristics, self.policy)
        planner.plan_waves(num_waves=2, tasks_per_wave=4)

        summary = planner.get_summary()

        self.assertEqual(summary["total_waves_planned"], 2)
        self.assertEqual(summary["total_tasks_planned"], 8)
        self.assertGreater(summary["avg_predicted_success_rate"], 0)


class TestPhase16Harness(unittest.TestCase):
    """Test Phase 16 harness."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.phase15_dir = Path(self.temp_dir) / "phase15"
        self.phase15_dir.mkdir(exist_ok=True)
        self.output_dir = Path(self.temp_dir) / "phase16"

        # Create minimal Phase 15 outputs
        with open(self.phase15_dir / "task_outcomes.jsonl", "w") as f:
            for i in range(3):
                f.write(
                    json.dumps(
                        {
                            "task_id": f"task{i}",
                            "wave": 1,
                            "status": "completed",
                            "risk_level": "LOW",
                            "confidence_before": 0.85,
                            "confidence_after": 0.91,
                        }
                    )
                    + "\n"
                )

        with open(self.phase15_dir / "confidence_updates.jsonl", "w") as f:
            f.write(json.dumps({"task_id": "task0", "delta": 0.06}) + "\n")

        with open(self.phase15_dir / "safety_gate_decisions.jsonl", "w") as f:
            f.write(
                json.dumps(
                    {
                        "task_id": "task0",
                        "risk_level": "LOW",
                        "approval": "APPROVED",
                    }
                )
                + "\n"
            )

        with open(self.phase15_dir / "policy_updates.jsonl", "w") as f:
            pass

        ui_state = {"policy_summary": {"current_policy": {}}}
        with open(self.phase15_dir / "phase15_ui_state.json", "w") as f:
            json.dump(ui_state, f)

    def test_harness_initialization(self):
        """Test harness initializes correctly."""
        harness = AdaptiveMetaLearningHarness(
            phase15_dir=str(self.phase15_dir),
            output_dir=str(self.output_dir),
        )
        self.assertIsNotNone(harness)

    def test_harness_run(self):
        """Test harness execution."""
        harness = AdaptiveMetaLearningHarness(
            phase15_dir=str(self.phase15_dir),
            output_dir=str(self.output_dir),
            num_future_waves=2,
        )

        result = harness.run()

        self.assertEqual(result["status"], "complete")
        self.assertGreater(result["insights_generated"], 0)
        self.assertGreater(result["heuristics_derived"], 0)
        self.assertGreater(result["planned_tasks"], 0)

    def test_outputs_created(self):
        """Test all outputs are created."""
        harness = AdaptiveMetaLearningHarness(
            phase15_dir=str(self.phase15_dir),
            output_dir=str(self.output_dir),
            num_future_waves=1,
        )

        harness.run()

        # Check files exist
        self.assertTrue((self.output_dir / "meta_insights.jsonl").exists())
        self.assertTrue((self.output_dir / "heuristics.jsonl").exists())
        self.assertTrue((self.output_dir / "planned_tasks.jsonl").exists())
        self.assertTrue((self.output_dir / "simulated_outcomes.jsonl").exists())
        self.assertTrue((self.output_dir / "phase16_ui_state.json").exists())
        self.assertTrue(
            (self.output_dir / "PHASE_16_ADAPTIVE_PLAN.md").exists()
        )

    def test_ui_state_structure(self):
        """Test UI state structure."""
        harness = AdaptiveMetaLearningHarness(
            phase15_dir=str(self.phase15_dir),
            output_dir=str(self.output_dir),
        )

        harness.run()

        with open(self.output_dir / "phase16_ui_state.json", "r") as f:
            ui_state = json.load(f)

        self.assertIn("generated_at", ui_state)
        self.assertIn("phase", ui_state)
        self.assertEqual(ui_state["phase"], 16)
        self.assertIn("insights", ui_state)
        self.assertIn("heuristics", ui_state)


class TestIntegration(unittest.TestCase):
    """Integration tests for Phase 16."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.phase15_dir = Path(self.temp_dir) / "phase15"
        self.phase15_dir.mkdir(exist_ok=True)
        self.output_dir = Path(self.temp_dir) / "phase16"

        # Create complete Phase 15 outputs
        with open(self.phase15_dir / "task_outcomes.jsonl", "w") as f:
            for wave in range(1, 3):
                for task in range(1, 5):
                    f.write(
                        json.dumps(
                            {
                                "task_id": f"wave{wave}_task{task}",
                                "wave": wave,
                                "status": "completed",
                                "risk_level": "LOW" if task <= 2 else "MEDIUM",
                                "confidence_before": 0.85,
                                "confidence_after": 0.91,
                                "confidence_delta": 0.06,
                            }
                        )
                        + "\n"
                    )

        with open(self.phase15_dir / "confidence_updates.jsonl", "w") as f:
            for i in range(8):
                f.write(
                    json.dumps(
                        {"task_id": f"task{i}", "wave": 1, "delta": 0.06}
                    )
                    + "\n"
                )

        with open(self.phase15_dir / "safety_gate_decisions.jsonl", "w") as f:
            for i in range(8):
                f.write(
                    json.dumps(
                        {
                            "task_id": f"task{i}",
                            "risk_level": "LOW",
                            "approval": "APPROVED",
                        }
                    )
                    + "\n"
                )

        with open(self.phase15_dir / "policy_updates.jsonl", "w") as f:
            pass

        ui_state = {"policy_summary": {"current_policy": {}}}
        with open(self.phase15_dir / "phase15_ui_state.json", "w") as f:
            json.dump(ui_state, f)

    def test_full_meta_learning_workflow(self):
        """Test complete meta-learning workflow."""
        harness = AdaptiveMetaLearningHarness(
            phase15_dir=str(self.phase15_dir),
            output_dir=str(self.output_dir),
            num_future_waves=3,
        )

        result = harness.run()

        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["waves_planned"], 3)


def run_tests():
    """Run all tests."""
    suite = unittest.TestLoader().loadTestsFromModule(__import__(__name__))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)

