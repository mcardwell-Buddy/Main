"""
Phase 14: Comprehensive Unit Tests

Tests for meta-learning engine, wave simulator, autonomous planner, and harness.
"""

import unittest
from pathlib import Path
from unittest.mock import Mock, patch
import json
import tempfile

from buddy_meta_learning_engine import MetaLearningEngine, MetaInsight, OperationalHeuristic
from buddy_wave_simulator import WaveSimulator, ExecutionStatus
from buddy_autonomous_planner import AutonomousPlanner, PlannedTask, WavePlan
from buddy_phase14_harness import ControlledLiveHarness


class TestMetaLearningEngine(unittest.TestCase):
    """Test meta-learning engine."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.engine = MetaLearningEngine(output_dir=self.temp_dir)

    def test_engine_initialization(self):
        """Test engine initializes correctly."""
        self.assertIsNotNone(self.engine)
        self.assertEqual(len(self.engine.insights), 0)
        self.assertEqual(len(self.engine.heuristics), 0)

    def test_load_jsonl_empty_file(self):
        """Test loading non-existent JSONL file."""
        result = self.engine._load_jsonl(Path(self.temp_dir) / "nonexistent.jsonl")
        self.assertEqual(result, [])

    def test_load_jsonl_with_data(self):
        """Test loading JSONL file with data."""
        jsonl_path = Path(self.temp_dir) / "test.jsonl"
        with open(jsonl_path, "w") as f:
            f.write('{"task_id": "test1", "value": 1}\n')
            f.write('{"task_id": "test2", "value": 2}\n')

        result = self.engine._load_jsonl(jsonl_path)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["task_id"], "test1")

    def test_analyze_task_patterns(self):
        """Test task pattern analysis."""
        outcomes = [
            {"task_id": "low1", "risk_level": "LOW", "status": "completed", "confidence_score": 0.9},
            {"task_id": "low2", "risk_level": "LOW", "status": "completed", "confidence_score": 0.85},
            {
                "task_id": "med1",
                "risk_level": "MEDIUM",
                "status": "completed",
                "confidence_score": 0.75,
            },
            {"task_id": "med2", "risk_level": "MEDIUM", "status": "failed", "confidence_score": 0.6},
        ]

        self.engine._analyze_task_patterns(outcomes)

        self.assertIn("LOW_success_rate", self.engine.patterns)
        self.assertEqual(self.engine.patterns["LOW_success_rate"], 1.0)
        self.assertEqual(self.engine.patterns["MEDIUM_success_rate"], 0.5)

    def test_extract_heuristics(self):
        """Test heuristic extraction."""
        outcomes = [
            {"task_id": f"low{i}", "risk_level": "LOW", "status": "completed", "confidence_score": 0.9}
            for i in range(5)
        ]
        updates = []

        self.engine._extract_operational_heuristics(outcomes, updates)

        self.assertGreater(len(self.engine.heuristics), 0)

    def test_meta_insight_creation(self):
        """Test meta-insight creation."""
        insight = MetaInsight(
            insight_type="success_pattern",
            description="Test pattern",
            confidence=0.85,
            supporting_evidence=["evidence1"],
            recommendation="Test recommendation",
            frequency=10,
            affected_tasks=["task1"],
        )

        self.assertEqual(insight.insight_type, "success_pattern")
        self.assertEqual(insight.confidence, 0.85)

    def test_get_summary(self):
        """Test summary generation."""
        self.engine.insights.append(
            MetaInsight(
                insight_type="success_pattern",
                description="Test",
                confidence=0.8,
                supporting_evidence=[],
                recommendation="Test",
                frequency=1,
                affected_tasks=[],
            )
        )

        summary = self.engine.get_summary()

        self.assertEqual(summary["metrics"]["total_insights"], 1)
        self.assertIn("patterns", summary)


class TestWaveSimulator(unittest.TestCase):
    """Test wave simulator."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.meta_engine = MetaLearningEngine(output_dir=self.temp_dir)
        self.policy = {"high_risk_threshold": 0.8, "retry_multiplier": 1.0}
        self.simulator = WaveSimulator(self.meta_engine, self.policy, output_dir=self.temp_dir)

    def test_simulator_initialization(self):
        """Test simulator initializes correctly."""
        self.assertIsNotNone(self.simulator)
        self.assertEqual(len(self.simulator.simulated_outcomes), 0)

    def test_evaluate_safety_gate_low_approved(self):
        """Test LOW risk task approval."""
        status, reason = self.simulator._evaluate_safety_gate("task1", "LOW", 0.6)
        self.assertEqual(status, "APPROVED")

    def test_evaluate_safety_gate_low_deferred(self):
        """Test LOW risk task deferral."""
        status, reason = self.simulator._evaluate_safety_gate("task1", "LOW", 0.4)
        self.assertEqual(status, "DEFERRED")

    def test_evaluate_safety_gate_medium_approved(self):
        """Test MEDIUM risk task approval."""
        status, reason = self.simulator._evaluate_safety_gate("task1", "MEDIUM", 0.8)
        self.assertEqual(status, "APPROVED")

    def test_evaluate_safety_gate_medium_deferred(self):
        """Test MEDIUM risk task deferral."""
        status, reason = self.simulator._evaluate_safety_gate("task1", "MEDIUM", 0.6)
        self.assertEqual(status, "DEFERRED")

    def test_evaluate_safety_gate_high_approved(self):
        """Test HIGH risk task approval."""
        status, reason = self.simulator._evaluate_safety_gate("task1", "HIGH", 0.95)
        self.assertEqual(status, "APPROVED")

    def test_evaluate_safety_gate_high_deferred(self):
        """Test HIGH risk task deferral."""
        status, reason = self.simulator._evaluate_safety_gate("task1", "HIGH", 0.7)
        self.assertEqual(status, "DEFERRED")

    def test_calculate_success_probability(self):
        """Test success probability calculation."""
        prob_low = self.simulator._calculate_success_probability(0.8, "LOW")
        prob_high = self.simulator._calculate_success_probability(0.8, "HIGH")

        self.assertGreater(prob_low, prob_high)
        self.assertLess(prob_low, 1.0)
        self.assertGreater(prob_low, 0.0)

    def test_estimate_execution_time(self):
        """Test execution time estimation."""
        time_low = self.simulator._estimate_execution_time("LOW")
        time_high = self.simulator._estimate_execution_time("HIGH")

        self.assertLess(time_low, time_high)
        self.assertGreater(time_low, 0)

    def test_apply_heuristics_boost(self):
        """Test heuristics boost application."""
        task = {"risk_level": "LOW", "confidence": 0.7}
        boost = self.simulator._apply_heuristics(task)

        self.assertGreaterEqual(boost, 0)
        self.assertLessEqual(boost, 0.15)

    def test_simulate_wave(self):
        """Test wave simulation."""
        tasks = [
            {"task_id": "task1", "risk_level": "LOW", "confidence": 0.8},
            {"task_id": "task2", "risk_level": "MEDIUM", "confidence": 0.75},
        ]

        outcomes, summary = self.simulator.simulate_wave(1, tasks)

        self.assertEqual(len(outcomes), 2)
        self.assertIn("wave", summary)
        self.assertIn("success_rate", summary)
        self.assertEqual(summary["wave"], 1)
        self.assertEqual(summary["total_tasks"], 2)

    def test_wave_summary_structure(self):
        """Test wave summary has expected structure."""
        tasks = [
            {"task_id": "task1", "risk_level": "LOW", "confidence": 0.8},
        ]

        outcomes, summary = self.simulator.simulate_wave(1, tasks)

        expected_keys = [
            "wave",
            "total_tasks",
            "completed",
            "failed",
            "deferred",
            "rolled_back",
            "success_rate",
        ]
        for key in expected_keys:
            self.assertIn(key, summary)


class TestAutonomousPlanner(unittest.TestCase):
    """Test autonomous planner."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.meta_engine = MetaLearningEngine(output_dir=self.temp_dir)
        self.policy = {"high_risk_threshold": 0.8}
        self.planner = AutonomousPlanner(self.meta_engine, self.policy, output_dir=self.temp_dir)

    def test_planner_initialization(self):
        """Test planner initializes correctly."""
        self.assertIsNotNone(self.planner)
        self.assertEqual(len(self.planner.wave_plans), 0)

    def test_generate_wave_tasks(self):
        """Test wave task generation."""
        tasks = self.planner._generate_wave_tasks(1)

        self.assertGreater(len(tasks), 0)
        for task in tasks:
            self.assertIn("task_id", task)
            self.assertIn("risk_level", task)
            self.assertIn("confidence", task)

    def test_evaluate_task_safety_low_approved(self):
        """Test LOW risk task safety evaluation."""
        task = {"risk_level": "LOW", "confidence": 0.6}
        status, reason = self.planner._evaluate_task_safety(task)
        self.assertEqual(status, "APPROVED")

    def test_evaluate_task_safety_low_deferred(self):
        """Test LOW risk task deferral."""
        task = {"risk_level": "LOW", "confidence": 0.4}
        status, reason = self.planner._evaluate_task_safety(task)
        self.assertEqual(status, "DEFERRED")

    def test_evaluate_task_safety_medium_approved(self):
        """Test MEDIUM risk task safety evaluation."""
        task = {"risk_level": "MEDIUM", "confidence": 0.8}
        status, reason = self.planner._evaluate_task_safety(task)
        self.assertEqual(status, "APPROVED")

    def test_evaluate_task_safety_medium_deferred(self):
        """Test MEDIUM risk task deferral."""
        task = {"risk_level": "MEDIUM", "confidence": 0.6}
        status, reason = self.planner._evaluate_task_safety(task)
        self.assertEqual(status, "DEFERRED")

    def test_evaluate_task_safety_high(self):
        """Test HIGH risk task safety evaluation."""
        task = {"risk_level": "HIGH", "confidence": 0.85}
        status, reason = self.planner._evaluate_task_safety(task)
        self.assertEqual(status, "APPROVED")

    def test_select_heuristics(self):
        """Test heuristics selection."""
        task = {"risk_level": "LOW"}
        heuristics = self.planner._select_heuristics(task)

        # Should work even with no heuristics in engine
        self.assertIsInstance(heuristics, list)

    def test_estimate_wave_success_rate(self):
        """Test wave success rate estimation."""
        tasks = [
            PlannedTask(
                task_id="task1",
                wave=1,
                title="Test",
                tool="web",
                risk_level="LOW",
                confidence=0.85,
                priority=5,
                dependencies=[],
                justification="Test",
                heuristics_applied=[],
                expected_outcome="Success",
            ),
        ]

        success_rate = self.planner._estimate_wave_success_rate(tasks)

        self.assertGreater(success_rate, 0)
        self.assertLess(success_rate, 1.0)

    def test_plan_waves(self):
        """Test multi-wave planning."""
        plans = self.planner.plan_waves(num_waves=2)

        self.assertEqual(len(plans), 2)
        for plan in plans:
            self.assertIsInstance(plan, WavePlan)
            self.assertGreater(plan.total_tasks, 0)

    def test_get_summary(self):
        """Test planning summary."""
        self.planner.plan_waves(num_waves=2)
        summary = self.planner.get_summary()

        self.assertEqual(summary["total_waves"], 2)
        self.assertGreater(summary["total_planned_tasks"], 0)


class TestPhase14Harness(unittest.TestCase):
    """Test Phase 14 harness."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.phase12_dir = Path(self.temp_dir) / "phase12"
        self.phase13_dir = Path(self.temp_dir) / "phase13"
        self.phase12_dir.mkdir(exist_ok=True)
        self.phase13_dir.mkdir(exist_ok=True)

        # Create minimal Phase 12 UI state
        ui_state = {
            "policy": {
                "high_risk_threshold": 0.8,
                "retry_multiplier": 1.0,
                "priority_bias": 1.0,
            }
        }
        with open(self.phase12_dir / "phase12_ui_state.json", "w") as f:
            json.dump(ui_state, f)

    def test_harness_initialization(self):
        """Test harness initializes correctly."""
        harness = ControlledLiveHarness(
            phase12_dir=str(self.phase12_dir),
            phase13_dir=str(self.phase13_dir),
            output_dir=str(Path(self.temp_dir) / "phase14"),
        )

        self.assertIsNotNone(harness)
        self.assertEqual(harness.policy["high_risk_threshold"], 0.8)

    def test_load_policy_default(self):
        """Test policy loading with defaults."""
        empty_dir = Path(self.temp_dir) / "empty"
        empty_dir.mkdir(exist_ok=True)

        harness = ControlledLiveHarness(
            phase12_dir=str(empty_dir),
            phase13_dir=str(self.phase13_dir),
            output_dir=str(Path(self.temp_dir) / "phase14"),
        )

        # Should have default policy
        self.assertIn("high_risk_threshold", harness.policy)

    def test_run_creates_outputs(self):
        """Test harness run creates expected outputs."""
        harness = ControlledLiveHarness(
            phase12_dir=str(self.phase12_dir),
            phase13_dir=str(self.phase13_dir),
            output_dir=str(Path(self.temp_dir) / "phase14"),
        )

        result = harness.run(waves=1)

        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["waves_planned"], 1)

        # Check output files
        output_dir = Path(self.temp_dir) / "phase14"
        self.assertTrue((output_dir / "phase14_ui_state.json").exists())
        self.assertTrue((output_dir / "PHASE_14_AUTONOMOUS_PLAN.md").exists())
        self.assertTrue((output_dir / "planned_tasks.jsonl").exists())
        self.assertTrue((output_dir / "simulated_outcomes.jsonl").exists())

    def test_ui_state_structure(self):
        """Test UI state has expected structure."""
        harness = ControlledLiveHarness(
            phase12_dir=str(self.phase12_dir),
            phase13_dir=str(self.phase13_dir),
            output_dir=str(Path(self.temp_dir) / "phase14"),
        )

        harness.run(waves=1)

        ui_state_path = Path(self.temp_dir) / "phase14" / "phase14_ui_state.json"
        with open(ui_state_path, "r") as f:
            ui_state = json.load(f)

        expected_keys = [
            "generated_at",
            "phase",
            "execution_mode",
            "wave_stats",
            "policy",
            "execution_summary",
        ]
        for key in expected_keys:
            self.assertIn(key, ui_state)


class TestIntegration(unittest.TestCase):
    """Integration tests for full Phase 14 workflow."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.phase12_dir = Path(self.temp_dir) / "phase12"
        self.phase12_dir.mkdir(exist_ok=True)

        # Create minimal Phase 12 outputs
        ui_state = {"policy": {"high_risk_threshold": 0.8, "retry_multiplier": 1.0}}
        with open(self.phase12_dir / "phase12_ui_state.json", "w") as f:
            json.dump(ui_state, f)

        # Create dummy outcomes
        with open(self.phase12_dir / "task_outcomes.jsonl", "w") as f:
            f.write('{"task_id": "test1", "risk_level": "LOW", "status": "completed", "confidence_score": 0.85}\n')

        with open(self.phase12_dir / "confidence_updates.jsonl", "w") as f:
            f.write('{"task_id": "test1", "confidence_delta": 0.05}\n')

        with open(self.phase12_dir / "strategic_decisions.jsonl", "w") as f:
            f.write('{"task_id": "test1", "decision_type": "elevate_confidence"}\n')

        with open(self.phase12_dir / "policy_updates.jsonl", "w") as f:
            f.write('{"wave": 1, "new_policy": {"high_risk_threshold": 0.8}}\n')

    def test_full_phase14_workflow(self):
        """Test complete Phase 14 workflow."""
        harness = ControlledLiveHarness(
            phase12_dir=str(self.phase12_dir),
            phase13_dir=str(Path(self.temp_dir) / "phase13"),
            output_dir=str(Path(self.temp_dir) / "phase14"),
        )

        result = harness.run(waves=2)

        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["waves_planned"], 2)
        self.assertGreater(result["total_planned_tasks"], 0)

        # Verify outputs
        output_dir = Path(self.temp_dir) / "phase14"
        self.assertTrue((output_dir / "PHASE_14_AUTONOMOUS_PLAN.md").exists())


def run_tests():
    """Run all tests."""
    suite = unittest.TestLoader().loadTestsFromModule(__import__(__name__))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
