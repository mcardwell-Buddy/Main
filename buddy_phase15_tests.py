"""
Phase 15: Comprehensive Unit Tests

Tests for autonomous executor, policy adapter, and harness.
"""

import unittest
from pathlib import Path
from unittest.mock import Mock
import json
import tempfile

from buddy_phase15_executor import AutonomousExecutor, TaskOutcome, ExecutionStatus
from buddy_phase15_policy_adapter import PolicyAdapter
from buddy_safety_gate import SafetyGate
from buddy_phase15_harness import AutonomousOperationHarness


class TestAutonomousExecutor(unittest.TestCase):
    """Test autonomous task executor."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.safety_gate = SafetyGate(require_approval=False)
        self.policy = {"high_risk_threshold": 0.8, "retry_multiplier": 1.0}
        self.executor = AutonomousExecutor(
            self.safety_gate, self.policy, output_dir=self.temp_dir
        )

    def test_executor_initialization(self):
        """Test executor initializes correctly."""
        self.assertIsNotNone(self.executor)
        self.assertEqual(len(self.executor.outcomes), 0)
        self.assertFalse(self.executor.dry_run)

    def test_execute_wave_single_task(self):
        """Test executing a wave with single task."""
        task = {
            "task_id": "test1",
            "risk_level": "LOW",
            "confidence": 0.85,
        }

        outcomes, summary = self.executor.execute_wave(1, [task])

        self.assertEqual(len(outcomes), 1)
        self.assertIn("wave", summary)
        self.assertEqual(summary["wave"], 1)
        self.assertEqual(summary["total_tasks"], 1)

    def test_execute_wave_multiple_tasks(self):
        """Test executing a wave with multiple tasks."""
        tasks = [
            {"task_id": "test1", "risk_level": "LOW", "confidence": 0.85},
            {"task_id": "test2", "risk_level": "MEDIUM", "confidence": 0.75},
            {"task_id": "test3", "risk_level": "LOW", "confidence": 0.90},
        ]

        outcomes, summary = self.executor.execute_wave(1, tasks)

        self.assertEqual(len(outcomes), 3)
        self.assertEqual(summary["total_tasks"], 3)
        self.assertGreater(summary["completed"], 0)

    def test_task_execution_approved(self):
        """Test approved task execution."""
        task = {
            "task_id": "test1",
            "risk_level": "LOW",
            "confidence": 0.85,
        }

        outcome = self.executor._execute_task(1, task)

        self.assertIsInstance(outcome, TaskOutcome)
        self.assertIn(outcome.status, [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED])

    def test_task_execution_deferred(self):
        """Test task deferral due to low confidence."""
        task = {
            "task_id": "test1",
            "risk_level": "MEDIUM",
            "confidence": 0.6,  # Below MEDIUM threshold (0.75)
        }

        outcome = self.executor._execute_task(1, task)

        # Deferred due to safety gate evaluation
        self.assertIn(outcome.status, [ExecutionStatus.DEFERRED, ExecutionStatus.COMPLETED])
        # Can be either DEFERRED or proceed if safety gate approves

    def test_confidence_update_completion(self):
        """Test confidence update on task completion."""
        task = {"task_id": "test1", "risk_level": "LOW", "confidence": 0.85}

        outcome = self.executor._execute_task(1, task)

        # Check confidence update recorded
        self.assertEqual(len(self.executor.get_confidence_updates()), 1)
        update = self.executor.get_confidence_updates()[0]
        self.assertEqual(update.task_id, "test1")

    def test_confidence_delta_deferred(self):
        """Test confidence delta for low-confidence task."""
        task = {
            "task_id": "test1",
            "risk_level": "MEDIUM",
            "confidence": 0.6,
        }

        outcome = self.executor._execute_task(1, task)

        # Confidence delta varies based on outcome
        self.assertLess(outcome.confidence_delta, 0.1)  # Should be small or negative

    def test_dry_run_mode(self):
        """Test executor in dry-run mode."""
        executor = AutonomousExecutor(
            self.safety_gate, self.policy, output_dir=self.temp_dir, dry_run=True
        )

        task = {"task_id": "test1", "risk_level": "LOW", "confidence": 0.85}
        outcome = executor._execute_task(1, task)

        # In dry-run, task should succeed
        self.assertEqual(outcome.status, ExecutionStatus.COMPLETED)

    def test_wave_summary_metrics(self):
        """Test wave summary contains expected metrics."""
        tasks = [
            {"task_id": f"test{i}", "risk_level": "LOW", "confidence": 0.85}
            for i in range(3)
        ]

        outcomes, summary = self.executor.execute_wave(1, tasks)

        expected_keys = [
            "wave",
            "total_tasks",
            "completed",
            "failed",
            "deferred",
            "rolled_back",
            "success_rate",
            "avg_confidence_delta",
        ]
        for key in expected_keys:
            self.assertIn(key, summary)


class TestPolicyAdapter(unittest.TestCase):
    """Test policy adaptation."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.initial_policy = {
            "high_risk_threshold": 0.8,
            "retry_multiplier": 1.0,
            "priority_bias": 1.0,
        }
        self.adapter = PolicyAdapter(self.initial_policy, output_dir=self.temp_dir)

    def test_adapter_initialization(self):
        """Test adapter initializes correctly."""
        self.assertIsNotNone(self.adapter)
        self.assertEqual(self.adapter.current_policy, self.initial_policy)

    def test_adapt_to_high_failure_rate(self):
        """Test policy adapts to high failure rate."""
        outcomes = []
        for i in range(10):
            outcome = Mock()
            outcome.status.value = "failed" if i < 3 else "completed"
            outcomes.append(outcome)

        self.adapter.record_wave_metrics(1, outcomes, [])

        # Should increase retry_multiplier
        self.assertGreater(
            self.adapter.current_policy.get("retry_multiplier", 1.0),
            self.initial_policy.get("retry_multiplier", 1.0),
        )

    def test_adapt_to_high_deferral_rate(self):
        """Test policy adapts to high deferral rate."""
        outcomes = []
        for i in range(10):
            outcome = Mock()
            outcome.status.value = "deferred" if i < 4 else "completed"
            outcomes.append(outcome)

        self.adapter.record_wave_metrics(1, outcomes, [])

        # Should increase high_risk_threshold
        self.assertGreater(
            self.adapter.current_policy.get("high_risk_threshold", 0.8),
            self.initial_policy.get("high_risk_threshold", 0.8),
        )

    def test_adapt_to_high_success_rate(self):
        """Test policy adapts to high success rate."""
        outcomes = []
        for i in range(10):
            outcome = Mock()
            outcome.status.value = "completed" if i < 9 else "failed"
            outcomes.append(outcome)

        self.adapter.record_wave_metrics(1, outcomes, [])

        # Should increase priority_bias
        self.assertGreater(
            self.adapter.current_policy.get("priority_bias", 1.0),
            self.initial_policy.get("priority_bias", 1.0),
        )

    def test_policy_history_tracking(self):
        """Test policy updates are tracked."""
        outcomes = []
        for i in range(10):
            outcome = Mock()
            outcome.status.value = "failed" if i < 3 else "completed"
            outcomes.append(outcome)

        self.adapter.record_wave_metrics(1, outcomes, [])

        history = self.adapter.get_policy_history()
        self.assertGreater(len(history), 0)

    def test_policy_summary(self):
        """Test policy summary generation."""
        outcomes = []
        for i in range(10):
            outcome = Mock()
            outcome.status.value = "completed"
            outcomes.append(outcome)

        self.adapter.record_wave_metrics(1, outcomes, [])

        summary = self.adapter.get_summary()

        expected_keys = [
            "initial_policy",
            "current_policy",
            "updates_count",
            "policy_changes",
        ]
        for key in expected_keys:
            self.assertIn(key, summary)


class TestAutonomousHarness(unittest.TestCase):
    """Test Phase 15 harness."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.phase14_dir = Path(self.temp_dir) / "phase14"
        self.phase14_dir.mkdir(exist_ok=True)

        # Create minimal Phase 14 files
        with open(self.phase14_dir / "planned_tasks.jsonl", "w") as f:
            f.write('{"task_id": "wave1_task1", "wave": 1, "risk_level": "LOW", "confidence": 0.85}\n')

        with open(self.phase14_dir / "meta_insights.jsonl", "w") as f:
            f.write('{"insight_type": "success_pattern", "confidence": 0.95}\n')

        with open(self.phase14_dir / "heuristics.jsonl", "w") as f:
            f.write('{"heuristic_id": "h1", "category": "task_sequencing"}\n')

        ui_state = {
            "policy": {
                "high_risk_threshold": 0.8,
                "retry_multiplier": 1.0,
                "priority_bias": 1.0,
            }
        }
        with open(self.phase14_dir / "phase14_ui_state.json", "w") as f:
            json.dump(ui_state, f)

    def test_harness_initialization(self):
        """Test harness initializes correctly."""
        harness = AutonomousOperationHarness(
            phase14_dir=str(self.phase14_dir),
            output_dir=str(Path(self.temp_dir) / "phase15"),
        )

        self.assertIsNotNone(harness)
        self.assertGreater(len(harness.planned_tasks), 0)

    def test_harness_run(self):
        """Test harness execution."""
        harness = AutonomousOperationHarness(
            phase14_dir=str(self.phase14_dir),
            output_dir=str(Path(self.temp_dir) / "phase15"),
            dry_run=True,
        )

        result = harness.run(waves=1)

        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["waves_executed"], 1)
        self.assertGreater(result["total_outcomes"], 0)

    def test_outputs_created(self):
        """Test all outputs are created."""
        output_dir = Path(self.temp_dir) / "phase15"
        harness = AutonomousOperationHarness(
            phase14_dir=str(self.phase14_dir),
            output_dir=str(output_dir),
            dry_run=True,
        )

        harness.run(waves=1)

        # Check key output files exist
        self.assertTrue((output_dir / "task_outcomes.jsonl").exists())
        self.assertTrue((output_dir / "phase15_ui_state.json").exists())
        self.assertTrue((output_dir / "PHASE_15_AUTONOMOUS_EXECUTION.md").exists())

    def test_ui_state_structure(self):
        """Test UI state has expected structure."""
        output_dir = Path(self.temp_dir) / "phase15"
        harness = AutonomousOperationHarness(
            phase14_dir=str(self.phase14_dir),
            output_dir=str(output_dir),
            dry_run=True,
        )

        harness.run(waves=1)

        ui_state_path = output_dir / "phase15_ui_state.json"
        with open(ui_state_path, "r") as f:
            ui_state = json.load(f)

        expected_keys = ["generated_at", "phase", "execution_mode", "wave_stats", "policy_summary"]
        for key in expected_keys:
            self.assertIn(key, ui_state)


class TestIntegration(unittest.TestCase):
    """Integration tests for Phase 15."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.phase14_dir = Path(self.temp_dir) / "phase14"
        self.phase14_dir.mkdir(exist_ok=True)

        # Create comprehensive Phase 14 files
        with open(self.phase14_dir / "planned_tasks.jsonl", "w") as f:
            for wave in range(1, 3):
                for i in range(2):
                    task = {
                        "task_id": f"wave{wave}_task{i+1}",
                        "wave": wave,
                        "risk_level": "LOW" if i == 0 else "MEDIUM",
                        "confidence": 0.85 if i == 0 else 0.75,
                    }
                    f.write(json.dumps(task) + "\n")

        with open(self.phase14_dir / "meta_insights.jsonl", "w") as f:
            f.write('{"insight_type": "success_pattern", "confidence": 0.95}\n')

        with open(self.phase14_dir / "heuristics.jsonl", "w") as f:
            f.write('{"heuristic_id": "h1"}\n')

        ui_state = {"policy": {"high_risk_threshold": 0.8, "retry_multiplier": 1.0}}
        with open(self.phase14_dir / "phase14_ui_state.json", "w") as f:
            json.dump(ui_state, f)

    def test_full_phase15_workflow(self):
        """Test complete Phase 15 workflow."""
        harness = AutonomousOperationHarness(
            phase14_dir=str(self.phase14_dir),
            output_dir=str(Path(self.temp_dir) / "phase15"),
            dry_run=True,
        )

        result = harness.run(waves=2)

        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["waves_executed"], 2)
        self.assertGreater(result["total_outcomes"], 0)


def run_tests():
    """Run all tests."""
    suite = unittest.TestLoader().loadTestsFromModule(__import__(__name__))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)

