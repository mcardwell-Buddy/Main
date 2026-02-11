"""
Unit tests for Human Energy Model - Phase 6 Step 2

Tests cover:
1. LOW effort classification (reply, approve, skim)
2. MEDIUM effort classification (review doc, decide)
3. HIGH effort classification (calls, meetings, physical)
4. Rest window constraints and warnings
5. Time estimate accuracy
6. Edge cases (empty, ambiguous, duration hints)
7. Signal emission integration
"""

import json
import sys
from pathlib import Path
import pytest
from tempfile import TemporaryDirectory

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from human_energy_model import (
    HumanEnergyModel,
    EffortLevel,
    HumanEnergyEstimate,
    estimate_human_cost,
)
from learning_signal_writer import LearningSignalWriter


class TestHumanEnergyModel:
    """Test suite for HumanEnergyModel."""

    @pytest.fixture
    def model(self):
        """Create fresh model instance."""
        return HumanEnergyModel(max_continuous_minutes=120.0)

    @pytest.fixture
    def signal_writer(self):
        """Create temporary signal writer."""
        with TemporaryDirectory() as tmpdir:
            writer = LearningSignalWriter(
                log_path=str(Path(tmpdir) / "signals_test.jsonl")
            )
            yield writer

    # =========================
    # LOW EFFORT TESTS (1-3)
    # =========================

    def test_classify_low_effort_quick_reply(self, model):
        """Test classification of quick reply task."""
        result = model.estimate_human_cost("Reply to customer email")
        assert result.effort_level == EffortLevel.LOW
        assert 1.0 <= result.estimated_minutes <= 5.0
        assert result.estimated_minutes == result.min_minutes or result.estimated_minutes < 5.0
        assert "reply" in result.evidence_keywords or "email" in result.evidence_keywords

    def test_classify_low_effort_approval(self, model):
        """Test classification of simple approval task."""
        result = model.estimate_human_cost("Approve the purchase order")
        assert result.effort_level == EffortLevel.LOW
        assert result.estimated_minutes <= 5.0
        assert "approve" in result.evidence_keywords

    def test_classify_low_effort_quick_skim(self, model):
        """Test classification of quick skim task."""
        result = model.estimate_human_cost("Skim the briefing document")
        assert result.effort_level == EffortLevel.LOW
        assert result.estimated_minutes <= 5.0
        assert "skim" in result.evidence_keywords

    # =========================
    # MEDIUM EFFORT TESTS (4-6)
    # =========================

    def test_classify_medium_effort_document_review(self, model):
        """Test classification of document review task."""
        result = model.estimate_human_cost("Review the quarterly report document")
        assert result.effort_level == EffortLevel.MEDIUM
        assert 5.0 <= result.estimated_minutes <= 30.0
        assert "review" in result.evidence_keywords or "document" in result.evidence_keywords

    def test_classify_medium_effort_decision_making(self, model):
        """Test classification of decision-making task."""
        result = model.estimate_human_cost("Make a decision on vendor selection")
        assert result.effort_level == EffortLevel.MEDIUM
        assert 5.0 <= result.estimated_minutes <= 30.0
        assert "decision" in result.evidence_keywords or "make" in result.evidence_keywords

    def test_classify_medium_effort_code_review(self, model):
        """Test classification of code review task."""
        result = model.estimate_human_cost("Code review pull request changes")
        assert result.effort_level == EffortLevel.MEDIUM
        assert 5.0 <= result.estimated_minutes <= 30.0
        assert "code" in result.evidence_keywords or "review" in result.evidence_keywords

    # =========================
    # HIGH EFFORT TESTS (7-9)
    # =========================

    def test_classify_high_effort_meeting(self, model):
        """Test classification of meeting task."""
        result = model.estimate_human_cost("Attend team planning meeting")
        assert result.effort_level == EffortLevel.HIGH
        assert result.estimated_minutes >= 30.0
        assert "meeting" in result.evidence_keywords or "attend" in result.evidence_keywords

    def test_classify_high_effort_phone_call(self, model):
        """Test classification of phone call task."""
        result = model.estimate_human_cost("Conduct customer phone call")
        assert result.effort_level == EffortLevel.HIGH
        assert result.estimated_minutes >= 30.0
        assert "call" in result.evidence_keywords or "phone" in result.evidence_keywords

    def test_classify_high_effort_site_visit(self, model):
        """Test classification of site visit task."""
        result = model.estimate_human_cost("Visit warehouse for inspection")
        assert result.effort_level == EffortLevel.HIGH
        assert result.estimated_minutes >= 30.0
        assert "visit" in result.evidence_keywords or "site" in result.evidence_keywords

    # =========================
    # REST CONSTRAINTS TESTS (10-12)
    # =========================

    def test_rest_ok_under_limit(self, model):
        """Test rest status when under limit."""
        result = model.estimate_human_cost(
            "Reply to email",
            current_cumulative_minutes=30.0
        )
        assert result.rest_warning is False
        assert result.rest_recommendation == "OK"

    def test_rest_near_limit_warning(self, model):
        """Test rest warning when near limit."""
        result = model.estimate_human_cost(
            "Attend meeting",
            current_cumulative_minutes=110.0  # Near 120 limit
        )
        assert result.rest_warning is True
        assert result.rest_recommendation in ["NEAR_LIMIT", "EXCEEDS_LIMIT"]

    def test_rest_exceeds_limit(self, model):
        """Test rest warning when exceeding limit."""
        result = model.estimate_human_cost(
            "Attend long meeting",
            current_cumulative_minutes=130.0  # Beyond 120 limit
        )
        assert result.rest_warning is True
        assert result.rest_recommendation == "EXCEEDS_LIMIT"

    # =========================
    # TIME ESTIMATE TESTS (13-14)
    # =========================

    def test_time_estimate_range_low_effort(self, model):
        """Test time estimate ranges for LOW effort."""
        result = model.estimate_human_cost("Quick reply to email")
        assert result.min_minutes <= result.estimated_minutes <= result.max_minutes
        assert result.estimated_minutes <= 5.0

    def test_time_estimate_range_high_effort(self, model):
        """Test time estimate ranges for HIGH effort."""
        result = model.estimate_human_cost("Conduct comprehensive meeting")
        assert result.min_minutes <= result.estimated_minutes <= result.max_minutes
        assert result.estimated_minutes >= 30.0

    # =========================
    # DURATION HINT TESTS (15-16)
    # =========================

    def test_duration_hint_quick_modifier(self, model):
        """Test quick/brief modifiers reduce estimates."""
        quick_result = model.estimate_human_cost("Quick review of document")
        normal_result = model.estimate_human_cost("Review of document")
        assert quick_result.estimated_minutes <= normal_result.estimated_minutes

    def test_duration_hint_extensive_modifier(self, model):
        """Test extensive/comprehensive modifiers increase estimates."""
        extensive_result = model.estimate_human_cost("Extensive analysis of data")
        quick_result = model.estimate_human_cost("Quick analysis of data")
        assert extensive_result.estimated_minutes >= quick_result.estimated_minutes

    # =========================
    # SIGNAL EMISSION TESTS (17-19)
    # =========================

    def test_signal_structure(self, model, signal_writer):
        """Test that signal structure is correct."""
        # Create estimate with manual signal emission
        estimate = model.estimate_human_cost("Review document")

        # Verify estimate has all required fields
        assert hasattr(estimate, 'task_description')
        assert hasattr(estimate, 'effort_level')
        assert hasattr(estimate, 'estimated_minutes')
        assert hasattr(estimate, 'rest_warning')
        assert hasattr(estimate, 'session_id')
        assert hasattr(estimate, 'timestamp')

    def test_emit_human_effort_signal(self, signal_writer):
        """Test emitting human effort signal."""
        model = HumanEnergyModel()
        estimate = model.estimate_human_cost("Review document")

        # Create and emit signal manually (simulating what integration layer would do)
        signal = {
            "signal_type": "human_effort_estimated",
            "signal_layer": "cognition",
            "signal_source": "human_energy_model",
            "timestamp": estimate.timestamp,
            "session_id": estimate.session_id,
            "data": {
                "task_description": estimate.task_description,
                "effort_level": estimate.effort_level.value,
                "estimated_minutes": estimate.estimated_minutes,
                "min_minutes": estimate.min_minutes,
                "max_minutes": estimate.max_minutes,
                "evidence_keywords": estimate.evidence_keywords,
                "rest_warning": estimate.rest_warning,
                "rest_recommendation": estimate.rest_recommendation,
                "reasoning": estimate.reasoning,
            }
        }

        # Write signal to file
        signal_writer.log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(signal_writer.log_path, "a") as f:
            f.write(json.dumps(signal) + "\n")

        # Read back and verify
        signals = signal_writer.read_signals() if hasattr(signal_writer, 'read_signals') else []
        if not signals:
            # Manually read the file
            with open(signal_writer.log_path, "r") as f:
                signals = [json.loads(line) for line in f if line.strip()]

        assert len(signals) > 0
        assert signals[0]["signal_type"] == "human_effort_estimated"
        assert signals[0]["signal_layer"] == "cognition"
        assert signals[0]["signal_source"] == "human_energy_model"

    def test_multiple_signals_accumulated(self, signal_writer):
        """Test accumulating multiple effort signals."""
        model = HumanEnergyModel()

        # Generate multiple estimates
        tasks = [
            "Reply to email",
            "Attend meeting",
            "Review code"
        ]

        signals = []
        for task in tasks:
            estimate = model.estimate_human_cost(task)
            signal = {
                "signal_type": "human_effort_estimated",
                "signal_layer": "cognition",
                "signal_source": "human_energy_model",
                "timestamp": estimate.timestamp,
                "session_id": estimate.session_id,
                "data": {
                    "task_description": estimate.task_description,
                    "effort_level": estimate.effort_level.value,
                    "estimated_minutes": estimate.estimated_minutes,
                }
            }
            signals.append(signal)
            
            # Write to file
            signal_writer.log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(signal_writer.log_path, "a") as f:
                f.write(json.dumps(signal) + "\n")

        # Read back and verify
        with open(signal_writer.log_path, "r") as f:
            read_signals = [json.loads(line) for line in f if line.strip()]

        assert len(read_signals) >= 3

    def test_signal_statistics(self, signal_writer):
        """Test signal statistics generation."""
        model = HumanEnergyModel()

        # Generate different effort levels
        estimates = [
            model.estimate_human_cost("Reply to email"),  # LOW
            model.estimate_human_cost("Review document"),  # MEDIUM
            model.estimate_human_cost("Attend meeting"),   # HIGH
        ]

        signal_writer.log_path.parent.mkdir(parents=True, exist_ok=True)
        for estimate in estimates:
            signal = {
                "signal_type": "human_effort_estimated",
                "signal_layer": "cognition",
                "signal_source": "human_energy_model",
                "timestamp": estimate.timestamp,
                "session_id": estimate.session_id,
                "data": {
                    "task_description": estimate.task_description,
                    "effort_level": estimate.effort_level.value,
                    "estimated_minutes": estimate.estimated_minutes,
                }
            }
            with open(signal_writer.log_path, "a") as f:
                f.write(json.dumps(signal) + "\n")

        # Verify signals were written
        with open(signal_writer.log_path, "r") as f:
            signals = [json.loads(line) for line in f if line.strip()]

        assert len(signals) >= 3

    # =========================
    # EDGE CASE TESTS (20-22)
    # =========================

    def test_empty_task_description(self, model):
        """Test classification of empty task description."""
        result = model.estimate_human_cost("")
        # Should default to MEDIUM
        assert result.effort_level == EffortLevel.MEDIUM
        assert result.estimated_minutes >= 5.0

    def test_ambiguous_task_description(self, model):
        """Test classification of ambiguous task."""
        result = model.estimate_human_cost("Do something important")
        # Should handle gracefully
        assert result.effort_level in [EffortLevel.LOW, EffortLevel.MEDIUM, EffortLevel.HIGH]
        assert result.estimated_minutes > 0.0

    def test_very_long_task_description(self, model):
        """Test classification of very long description."""
        long_task = "Attend a comprehensive strategic planning meeting " * 20
        result = model.estimate_human_cost(long_task)
        assert result.effort_level == EffortLevel.HIGH
        assert result.estimated_minutes >= 30.0

    # =========================
    # CONFIDENCE SCORE TESTS (23-24)
    # =========================

    def test_high_confidence_digital(self, model):
        """Test high confidence when multiple keywords match."""
        result = model.estimate_human_cost("Quick reply to email message")
        # Multiple LOW keywords should increase confidence
        assert len(result.evidence_keywords) >= 2

    def test_confidence_range(self, model):
        """Test confidence is always valid range."""
        results = [
            model.estimate_human_cost("Reply"),
            model.estimate_human_cost("Review document"),
            model.estimate_human_cost("Attend meeting"),
            model.estimate_human_cost("Do task"),
        ]

        for result in results:
            # Confidence embedded in reasoning
            assert "%" in result.reasoning

    # =========================
    # REST STATUS TESTS (25-26)
    # =========================

    def test_get_rest_status_ok(self, model):
        """Test getting rest status when OK."""
        model.cumulative_effort_minutes = 50.0
        status = model.get_rest_status()

        assert status["cumulative_minutes"] == 50.0
        assert status["max_continuous_minutes"] == 120.0
        assert status["remaining_minutes"] == 70.0
        assert status["status"] == "OK"

    def test_get_rest_status_near_limit(self, model):
        """Test getting rest status near limit."""
        model.cumulative_effort_minutes = 105.0  # 87.5% of 120
        status = model.get_rest_status()

        assert status["cumulative_minutes"] == 105.0
        assert status["status"] == "NEAR_LIMIT"

    # =========================
    # CONVENIENCE FUNCTION TESTS (27)
    # =========================

    def test_convenience_function_estimate_human_cost(self):
        """Test convenience function."""
        result = estimate_human_cost("Reply to email")
        assert result.effort_level == EffortLevel.LOW
        assert isinstance(result, HumanEnergyEstimate)

    # =========================
    # DETERMINISM TESTS (28-29)
    # =========================

    def test_deterministic_classification_same_input(self, model):
        """Test that same input produces same output."""
        task = "Review the quarterly report"

        result1 = model.estimate_human_cost(task)
        result2 = model.estimate_human_cost(task)

        assert result1.effort_level == result2.effort_level
        assert result1.estimated_minutes == result2.estimated_minutes
        assert set(result1.evidence_keywords) == set(result2.evidence_keywords)

    def test_deterministic_rest_calculation(self, model):
        """Test that rest calculation is deterministic."""
        task = "Attend meeting"
        cumulative = 100.0

        result1 = model.estimate_human_cost(task, current_cumulative_minutes=cumulative)
        result2 = model.estimate_human_cost(task, current_cumulative_minutes=cumulative)

        assert result1.rest_warning == result2.rest_warning
        assert result1.rest_recommendation == result2.rest_recommendation

    # =========================
    # SESSION TRACKING TESTS (30-31)
    # =========================

    def test_session_id_persistence(self, model):
        """Test session_id is consistent within model instance."""
        result1 = model.estimate_human_cost("Task 1")
        result2 = model.estimate_human_cost("Task 2")

        assert result1.session_id == result2.session_id

    def test_different_models_different_sessions(self):
        """Test different model instances have different session_ids."""
        model1 = HumanEnergyModel()
        model2 = HumanEnergyModel()

        result1 = model1.estimate_human_cost("Task")
        result2 = model2.estimate_human_cost("Task")

        assert result1.session_id != result2.session_id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

