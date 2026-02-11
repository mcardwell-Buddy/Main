"""
Unit tests for Phase 13 Controlled Live Environment
"""

import unittest
import json
import tempfile
from pathlib import Path

from buddy_safety_gate import SafetyGate, ApprovalStatus
from buddy_controlled_live_executor import ControlledLiveExecutor
from buddy_controlled_live_harness import ControlledLiveHarness


class TestSafetyGate(unittest.TestCase):
    """Test safety gate enforcement."""
    
    def setUp(self):
        self.gate = SafetyGate(require_approval=False)
    
    def test_low_risk_approved(self):
        """LOW risk tasks approved if confidence >= 0.5"""
        approval, reason = self.gate.evaluate("task1", "LOW", 0.75)
        self.assertEqual(approval, ApprovalStatus.APPROVED)
        self.assertIn("approved", reason.lower())
    
    def test_low_risk_deferred(self):
        """LOW risk tasks deferred if confidence < 0.5"""
        approval, reason = self.gate.evaluate("task2", "LOW", 0.4)
        self.assertEqual(approval, ApprovalStatus.DEFERRED)
        self.assertIn("deferred", reason.lower())
    
    def test_medium_risk_approved(self):
        """MEDIUM risk tasks approved if confidence >= 0.75"""
        approval, reason = self.gate.evaluate("task3", "MEDIUM", 0.8)
        self.assertEqual(approval, ApprovalStatus.APPROVED)
    
    def test_medium_risk_deferred(self):
        """MEDIUM risk tasks deferred if confidence < 0.75"""
        approval, reason = self.gate.evaluate("task4", "MEDIUM", 0.7)
        self.assertEqual(approval, ApprovalStatus.DEFERRED)
    
    def test_high_risk_requires_approval(self):
        """HIGH risk tasks require explicit approval even with high confidence"""
        self.gate.require_approval = True
        approval, reason = self.gate.evaluate("task5", "HIGH", 0.95)
        self.assertEqual(approval, ApprovalStatus.DEFERRED)
        
        # Approve the task
        self.gate.approve_task("task5")
        approval, reason = self.gate.evaluate("task5", "HIGH", 0.95)
        self.assertEqual(approval, ApprovalStatus.APPROVED)
    
    def test_dry_run_always_approved(self):
        """Dry-run tasks always approved regardless of risk/confidence"""
        approval, reason = self.gate.evaluate("task6", "HIGH", 0.3, is_dry_run=True)
        self.assertEqual(approval, ApprovalStatus.APPROVED)
        self.assertIn("dry-run", reason.lower())
    
    def test_decision_logging(self):
        """Safety gate logs all decisions"""
        self.gate.evaluate("task7", "LOW", 0.8)
        self.gate.evaluate("task8", "MEDIUM", 0.6)
        
        decisions = self.gate.get_decisions()
        self.assertEqual(len(decisions), 2)
        self.assertEqual(decisions[0]["task_id"], "task7")


class TestControlledLiveExecutor(unittest.TestCase):
    """Test controlled live executor."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.executor = ControlledLiveExecutor(
            Path(self.temp_dir),
            wave=1,
            require_approval=False,
            allow_live=True
        )
    
    def test_task_approval(self):
        """Test explicit task approval"""
        self.executor.approve_task("task1")
        self.assertIn("task1", self.executor.safety_gate.approved_task_ids)
    
    def test_wave_execution(self):
        """Test wave execution with mixed tasks"""
        tasks = [
            {
                "task_id": "low_task",
                "title": "Low risk",
                "tool": "web_inspect",
                "action_params": {},
                "priority": "MEDIUM",
                "risk_level": "LOW",
                "confidence_score": 0.85,
                "dependencies": []
            },
            {
                "task_id": "medium_task",
                "title": "Medium risk",
                "tool": "web_click",
                "action_params": {},
                "priority": "MEDIUM",
                "risk_level": "MEDIUM",
                "confidence_score": 0.6,
                "dependencies": []
            }
        ]
        
        outcomes, questions, updates = self.executor.execute_wave(
            tasks,
            "test_workflow"
        )
        
        self.assertEqual(len(outcomes), 2)
        self.assertGreater(len(questions), 0)
        self.assertEqual(len(updates), 2)
    
    def test_dry_run_toggle(self):
        """Test dry-run toggle"""
        tasks = [
            {
                "task_id": "task1",
                "title": "Test",
                "tool": "web_inspect",
                "action_params": {},
                "priority": "MEDIUM",
                "risk_level": "LOW",
                "confidence_score": 0.8,
                "dependencies": []
            }
        ]
        
        # Enforce dry-run
        outcomes, _, _ = self.executor.execute_wave(
            tasks,
            "test_workflow",
            enforce_dry_run=True
        )
        
        self.assertGreater(len(outcomes), 0)
        # In dry-run, execution_type should reflect that
    
    def test_wave_summary(self):
        """Test wave execution summary"""
        tasks = [
            {
                "task_id": "task1",
                "title": "Test",
                "tool": "web_inspect",
                "action_params": {},
                "priority": "MEDIUM",
                "risk_level": "LOW",
                "confidence_score": 0.8,
                "dependencies": []
            }
        ]
        
        self.executor.execute_wave(tasks, "test_workflow")
        summary = self.executor.get_summary()
        
        self.assertEqual(summary["total"], 1)
        self.assertIn("completed", summary)
        self.assertIn("deferred", summary)


class TestControlledLiveHarness(unittest.TestCase):
    """Test harness orchestration."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.phase12_dir = Path(self.temp_dir) / "phase12"
        self.phase12_dir.mkdir(parents=True, exist_ok=True)
        
        # Create mock Phase 12 artifacts
        ui_state = {
            "policy": {
                "high_risk_threshold": 0.8,
                "retry_multiplier": 1.0,
                "priority_bias": 1.5
            }
        }
        with open(self.phase12_dir / "phase12_ui_state.json", "w") as f:
            json.dump(ui_state, f)
        
        strategic_decisions = [
            {
                "task_id": "task1",
                "decision_type": "pattern_boost",
                "confidence_before": 0.7,
                "confidence_after": 0.75
            }
        ]
        with open(self.phase12_dir / "strategic_decisions.jsonl", "w") as f:
            for d in strategic_decisions:
                f.write(json.dumps(d) + "\n")
    
    def test_harness_initialization(self):
        """Test harness loads Phase 12 policy"""
        output_dir = Path(self.temp_dir) / "phase13"
        harness = ControlledLiveHarness(
            self.phase12_dir,
            output_dir
        )
        
        self.assertEqual(harness.policy.high_risk_threshold, 0.8)
        self.assertEqual(harness.policy.priority_bias, 1.5)
    
    def test_harness_execution(self):
        """Test harness can execute waves"""
        output_dir = Path(self.temp_dir) / "phase13"
        harness = ControlledLiveHarness(
            self.phase12_dir,
            output_dir
        )
        
        # Should complete without error
        harness.run(waves=1, enforce_dry_run=True)
        
        # Check outputs exist
        self.assertTrue((output_dir / "self_questions.jsonl").exists())
        self.assertTrue((output_dir / "task_outcomes.jsonl").exists())
        self.assertTrue((output_dir / "phase13_ui_state.json").exists())
    
    def test_wave_task_generation(self):
        """Test wave task generation"""
        output_dir = Path(self.temp_dir) / "phase13"
        harness = ControlledLiveHarness(
            self.phase12_dir,
            output_dir
        )
        
        tasks = harness._generate_wave_tasks(1)
        self.assertGreater(len(tasks), 0)
        self.assertIn("risk_level", tasks[0])
        self.assertIn("confidence_score", tasks[0])


if __name__ == "__main__":
    unittest.main()

