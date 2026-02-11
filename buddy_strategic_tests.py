"""
Unit tests for Phase 12 Strategic Execution Harness
"""

import unittest
import json
import tempfile
from pathlib import Path

from buddy_dynamic_task_scheduler import TaskScheduler, RiskLevel
from phase2_confidence import GradedConfidenceCalculator
from buddy_strategic_executor import StrategicExecutor, StrategicDecision
from buddy_strategic_harness import StrategicHarness


class TestStrategicExecutor(unittest.TestCase):
    """Test strategic executor with adaptive decision-making."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock learning insights
        self.learning_insights = [
            {
                "insight_type": "deferred_high_risk",
                "description": "2 high-risk tasks deferred (avg conf: 0.62)",
                "confidence": 0.95,
                "recommendation": "Implement confidence-boosting strategies"
            },
            {
                "insight_type": "high_success_risk_level",
                "description": "LOW risk tasks show 100% success rate",
                "confidence": 0.85,
                "recommendation": "Consider increasing complexity"
            }
        ]
    
    def test_confidence_elevation_for_high_risk(self):
        """Test that high-risk tasks get confidence elevation based on insights."""
        executor = StrategicExecutor(
            Path(self.temp_dir),
            self.learning_insights,
            1
        )
        
        # Task with low confidence for high-risk
        original_confidence = 0.65
        adjusted, decision = executor._apply_strategic_adjustments(
            "test_high_risk",
            RiskLevel.HIGH,
            original_confidence
        )
        
        self.assertGreater(adjusted, original_confidence)
        self.assertIsNotNone(decision)
        self.assertEqual(decision.decision_type, "confidence_elevation")
        self.assertIn("Elevated confidence", decision.rationale)
    
    def test_pattern_boost_for_successful_risk_level(self):
        """Test that tasks in proven successful risk categories get boost."""
        executor = StrategicExecutor(
            Path(self.temp_dir),
            self.learning_insights,
            1
        )
        
        original_confidence = 0.70
        adjusted, decision = executor._apply_strategic_adjustments(
            "test_low_risk",
            RiskLevel.LOW,
            original_confidence
        )
        
        self.assertGreater(adjusted, original_confidence)
        self.assertIsNotNone(decision)
        self.assertEqual(decision.decision_type, "pattern_boost")
    
    def test_strategic_decisions_logged(self):
        """Test that strategic decisions are logged to file."""
        executor = StrategicExecutor(
            Path(self.temp_dir),
            self.learning_insights,
            1
        )
        
        tasks = [
            {
                "task_id": "task1",
                "description": "Test task",
                "action": "web_inspect",
                "action_params": {},
                "priority": "MEDIUM",
                "risk_level": "HIGH",
                "confidence_score": 0.65,
                "dependencies": []
            }
        ]
        
        executor.execute_wave(tasks, "test_workflow")
        
        decisions_file = Path(self.temp_dir) / "strategic_decisions_wave_1.jsonl"
        self.assertTrue(decisions_file.exists())
        
        with open(decisions_file) as f:
            decisions = [json.loads(line) for line in f]
        
        self.assertGreater(len(decisions), 0)
        self.assertIn("decision_type", decisions[0])


class TestStrategicHarness(unittest.TestCase):
    """Test strategic harness orchestration."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.phase11_dir = Path(self.temp_dir) / "phase11"
        self.phase11_dir.mkdir(parents=True, exist_ok=True)
        
        # Create mock Phase 11 artifacts
        ui_state = {
            "policy": {
                "high_risk_threshold": 0.8,
                "retry_multiplier": 1.0,
                "priority_bias": 1.35
            }
        }
        with open(self.phase11_dir / "phase11_ui_state.json", "w") as f:
            json.dump(ui_state, f)
        
        learning_insights = [
            {
                "insight_type": "deferred_high_risk",
                "description": "2 high-risk tasks deferred",
                "confidence": 0.95,
                "recommendation": "Boost confidence"
            }
        ]
        with open(self.phase11_dir / "learning_insights.jsonl", "w") as f:
            for insight in learning_insights:
                f.write(json.dumps(insight) + "\n")
        
        # Create mock task outcomes
        with open(self.phase11_dir / "task_outcomes.jsonl", "w") as f:
            f.write(json.dumps({
                "task_id": "wave4_high",
                "status": "deferred",
                "risk_level": "HIGH",
                "confidence_score": 0.62
            }) + "\n")
        
        # Create mock confidence updates
        with open(self.phase11_dir / "confidence_updates.jsonl", "w") as f:
            f.write(json.dumps({
                "task_id": "wave4_high",
                "confidence_before": 0.62,
                "confidence_after": 0.62
            }) + "\n")
    
    def test_phase11_policy_loaded(self):
        """Test that Phase 11 policy is loaded correctly."""
        output_dir = Path(self.temp_dir) / "phase12"
        harness = StrategicHarness(self.phase11_dir, output_dir)
        
        self.assertEqual(harness.policy.high_risk_threshold, 0.8)
        self.assertEqual(harness.policy.priority_bias, 1.35)
    
    def test_learning_insights_loaded(self):
        """Test that learning insights are loaded."""
        output_dir = Path(self.temp_dir) / "phase12"
        harness = StrategicHarness(self.phase11_dir, output_dir)
        
        self.assertGreater(len(harness.learning_insights), 0)
        self.assertEqual(harness.learning_insights[0]["insight_type"], "deferred_high_risk")
    
    def test_strategic_execution_produces_outputs(self):
        """Test that strategic execution produces all required outputs."""
        output_dir = Path(self.temp_dir) / "phase12"
        harness = StrategicHarness(self.phase11_dir, output_dir)
        harness.run(waves=1)
        
        # Check aggregate outputs
        self.assertTrue((output_dir / "self_questions.jsonl").exists())
        self.assertTrue((output_dir / "task_outcomes.jsonl").exists())
        self.assertTrue((output_dir / "confidence_updates.jsonl").exists())
        self.assertTrue((output_dir / "policy_updates.jsonl").exists())
        self.assertTrue((output_dir / "strategic_decisions.jsonl").exists())
        self.assertTrue((output_dir / "phase12_ui_state.json").exists())
        self.assertTrue((output_dir / "PHASE_12_STRATEGIC_REPORT.md").exists())


if __name__ == "__main__":
    unittest.main()

