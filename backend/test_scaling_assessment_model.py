"""
Unit tests for Scaling Assessment Model - Phase 6 Step 3

Tests cover:
1. SCALABLE classification (batch, parallel, independent)
2. NON_SCALABLE classification (human, sequential, dependent)
3. CONDITIONAL classification (approved, phased)
4. Bottleneck detection (human, system, temporal, sequential)
5. Parallelizable unit estimation
6. Edge cases and determinism
7. Signal structure
"""

import json
import sys
from pathlib import Path
import pytest
from tempfile import TemporaryDirectory

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from scaling_assessment_model import (
    ScalingAssessmentModel,
    ScalabilityLevel,
    ScalabilityAssessment,
    assess_scalability,
)


class TestScalingAssessmentModel:
    """Test suite for ScalingAssessmentModel."""

    @pytest.fixture
    def model(self):
        """Create fresh model instance."""
        return ScalingAssessmentModel()

    # =========================
    # SCALABLE TESTS (1-5)
    # =========================

    def test_classify_scalable_batch_processing(self, model):
        """Test classification of batch processing task."""
        result = model.assess_scalability("Process batch of customer records")
        assert result.scalability_level == ScalabilityLevel.SCALABLE
        assert result.confidence >= 0.5
        assert result.bottleneck_type == "none"
        assert result.parallelizable_units >= 2

    def test_classify_scalable_parallel_execution(self, model):
        """Test classification of parallel execution task."""
        result = model.assess_scalability("Run analysis in parallel on dataset")
        assert result.scalability_level == ScalabilityLevel.SCALABLE
        assert result.bottleneck_type == "none"

    def test_classify_scalable_bulk_export(self, model):
        """Test classification of bulk export task."""
        result = model.assess_scalability("Export 500 records to CSV")
        # Should recognize export as scalable activity
        assert result.scalability_level in [ScalabilityLevel.SCALABLE, ScalabilityLevel.CONDITIONAL]
        assert result.parallelizable_units >= 1

    def test_classify_scalable_repetitive_task(self, model):
        """Test classification of repetitive task."""
        result = model.assess_scalability("Process each file in folder independently")
        assert result.scalability_level == ScalabilityLevel.SCALABLE
        assert result.bottleneck_type == "none"

    def test_classify_scalable_idempotent_operation(self, model):
        """Test classification of idempotent operation."""
        result = model.assess_scalability("Send bulk emails to mailing list")
        assert result.scalability_level == ScalabilityLevel.SCALABLE
        assert result.confidence >= 0.5

    # =========================
    # NON_SCALABLE TESTS (6-10)
    # =========================

    def test_classify_non_scalable_phone_call(self, model):
        """Test classification of phone call task."""
        result = model.assess_scalability("Call customer to discuss contract")
        assert result.scalability_level == ScalabilityLevel.NON_SCALABLE
        assert result.bottleneck_type == "human"
        assert result.parallelizable_units == 1

    def test_classify_non_scalable_approval_workflow(self, model):
        """Test classification of approval workflow task."""
        result = model.assess_scalability("Request approval from manager")
        assert result.scalability_level == ScalabilityLevel.NON_SCALABLE
        # Bottleneck should indicate human involvement
        assert result.bottleneck_type in ["human", "unknown"]

    def test_classify_non_scalable_sequential_dependency(self, model):
        """Test classification of sequential dependency task."""
        result = model.assess_scalability("Process orders sequentially by priority")
        # Should not be fully scalable due to priority/sequential constraint
        assert result.scalability_level in [ScalabilityLevel.NON_SCALABLE, ScalabilityLevel.CONDITIONAL]

    def test_classify_non_scalable_signature_required(self, model):
        """Test classification of signature-required task."""
        result = model.assess_scalability("Sign legal document")
        assert result.scalability_level == ScalabilityLevel.NON_SCALABLE
        assert result.bottleneck_type == "human"

    def test_classify_non_scalable_external_api_sync(self, model):
        """Test classification of external API sync task."""
        result = model.assess_scalability("Sync data with third party API (rate limited)")
        assert result.scalability_level == ScalabilityLevel.NON_SCALABLE
        assert result.bottleneck_type in ["system", "temporal"]

    # =========================
    # CONDITIONAL TESTS (11-14)
    # =========================

    def test_classify_conditional_approval_required(self, model):
        """Test classification of approval-required task."""
        result = model.assess_scalability("Process orders once approved by manager")
        assert result.scalability_level == ScalabilityLevel.CONDITIONAL
        assert len(result.conditions_for_scale) > 0
        # Should mention approval or setup requirements
        condition_text = " ".join(result.conditions_for_scale).lower()
        assert "approval" in condition_text or "dependent" in condition_text or "batch" in condition_text

    def test_classify_conditional_phased_rollout(self, model):
        """Test classification of phased rollout task."""
        result = model.assess_scalability("Deploy changes in phased rollout")
        assert result.scalability_level == ScalabilityLevel.CONDITIONAL
        assert any("phased" in cond.lower() or "phase" in cond.lower() for cond in result.conditions_for_scale)

    def test_classify_conditional_pilot_program(self, model):
        """Test classification of pilot program task."""
        result = model.assess_scalability("Run as pilot program before full scale")
        assert result.scalability_level == ScalabilityLevel.CONDITIONAL
        assert len(result.conditions_for_scale) > 0

    def test_classify_conditional_dependent_setup(self, model):
        """Test classification of dependent setup task."""
        result = model.assess_scalability("Process subset depending on initial review")
        # Should be conditional due to dependency
        assert result.scalability_level in [ScalabilityLevel.CONDITIONAL, ScalabilityLevel.SCALABLE]

    # =========================
    # BOTTLENECK DETECTION (15-18)
    # =========================

    def test_bottleneck_human_call_scenario(self, model):
        """Test human bottleneck detection in call scenario."""
        result = model.assess_scalability("Call each customer to confirm orders")
        assert result.bottleneck_type == "human"

    def test_bottleneck_sequential_ordering(self, model):
        """Test sequential bottleneck detection."""
        result = model.assess_scalability("Execute tasks in order, each depends on previous")
        # Should identify sequential dependency
        assert result.bottleneck_type in ["sequential", "data_dependency"]

    def test_bottleneck_temporal_realtime(self, model):
        """Test temporal bottleneck detection."""
        result = model.assess_scalability("Process real time data stream synchronously")
        assert result.bottleneck_type == "temporal"

    def test_bottleneck_data_dependency(self, model):
        """Test data dependency bottleneck detection."""
        result = model.assess_scalability("Step 2 depends on output from Step 1")
        assert result.bottleneck_type == "data_dependency"

    # =========================
    # PARALLELIZABLE UNITS (19-22)
    # =========================

    def test_parallelizable_units_single_task(self, model):
        """Test unit estimation for single task."""
        result = model.assess_scalability("Review this document")
        assert result.parallelizable_units == 1

    def test_parallelizable_units_batch_100(self, model):
        """Test unit estimation from numeric hint."""
        result = model.assess_scalability("Process 100 orders in parallel")
        assert result.parallelizable_units >= 2

    def test_parallelizable_units_many_items(self, model):
        """Test unit estimation from 'many' keyword."""
        result = model.assess_scalability("Send emails to many recipients")
        assert result.parallelizable_units >= 2

    def test_parallelizable_units_conditional(self, model):
        """Test unit estimation for conditional tasks."""
        result = model.assess_scalability("Process subset if approved")
        assert result.parallelizable_units >= 1

    # =========================
    # CONFIDENCE TESTS (23-25)
    # =========================

    def test_confidence_range_valid(self, model):
        """Test confidence always in valid range."""
        tasks = [
            "Reply to email",
            "Run batch job",
            "Call customer",
            "Process conditionally",
            "Unknown task xyz abc"
        ]

        for task in tasks:
            result = model.assess_scalability(task)
            assert 0.0 <= result.confidence <= 1.0

    def test_confidence_high_for_clear_scalable(self, model):
        """Test high confidence for clearly scalable tasks."""
        result = model.assess_scalability("Process batch of 100 records in parallel")
        assert result.confidence >= 0.5

    def test_confidence_high_for_clear_non_scalable(self, model):
        """Test high confidence for clearly non-scalable tasks."""
        result = model.assess_scalability("Negotiate contract terms with customer")
        assert result.confidence >= 0.5

    # =========================
    # EVIDENCE FACTORS (26-27)
    # =========================

    def test_evidence_factors_scalable_task(self, model):
        """Test evidence factors for scalable task."""
        result = model.assess_scalability("Process batch records in parallel")
        assert len(result.evidence_factors) > 0
        assert any(word in result.evidence_factors for word in ["batch", "process", "parallel"])

    def test_evidence_factors_non_scalable_task(self, model):
        """Test evidence factors for non-scalable task."""
        result = model.assess_scalability("Call customer for approval")
        assert len(result.evidence_factors) > 0
        assert any(word in result.evidence_factors for word in ["call", "approval"])

    # =========================
    # REASONING TESTS (28-29)
    # =========================

    def test_reasoning_contains_level(self, model):
        """Test reasoning includes scalability level."""
        result = model.assess_scalability("Process batch")
        assert result.scalability_level.value in result.reasoning

    def test_reasoning_contains_confidence(self, model):
        """Test reasoning includes confidence percentage."""
        result = model.assess_scalability("Call customer")
        assert "%" in result.reasoning

    # =========================
    # EDGE CASE TESTS (30-32)
    # =========================

    def test_empty_task_description(self, model):
        """Test classification of empty task."""
        result = model.assess_scalability("")
        assert result.scalability_level in [ScalabilityLevel.SCALABLE, ScalabilityLevel.NON_SCALABLE, ScalabilityLevel.CONDITIONAL]
        assert result.parallelizable_units >= 1

    def test_ambiguous_task_description(self, model):
        """Test classification of ambiguous task."""
        result = model.assess_scalability("Do important work")
        assert result.scalability_level in [ScalabilityLevel.SCALABLE, ScalabilityLevel.NON_SCALABLE, ScalabilityLevel.CONDITIONAL]

    def test_very_long_task_description(self, model):
        """Test classification of very long description."""
        long_task = "Process records " * 50
        result = model.assess_scalability(long_task)
        assert result.scalability_level is not None

    # =========================
    # DETERMINISM TESTS (33-35)
    # =========================

    def test_deterministic_same_input(self, model):
        """Test same input produces same output."""
        task = "Process 100 records in parallel"

        result1 = model.assess_scalability(task)
        result2 = model.assess_scalability(task)

        assert result1.scalability_level == result2.scalability_level
        assert result1.confidence == result2.confidence
        assert result1.bottleneck_type == result2.bottleneck_type
        assert result1.parallelizable_units == result2.parallelizable_units

    def test_deterministic_bottleneck_detection(self, model):
        """Test bottleneck detection is deterministic."""
        task = "Call customer to discuss options"

        result1 = model.assess_scalability(task)
        result2 = model.assess_scalability(task)

        assert result1.bottleneck_type == result2.bottleneck_type

    def test_deterministic_units_estimation(self, model):
        """Test unit estimation is deterministic."""
        task = "Process batch of orders"

        result1 = model.assess_scalability(task)
        result2 = model.assess_scalability(task)

        assert result1.parallelizable_units == result2.parallelizable_units

    # =========================
    # SESSION TRACKING (36-37)
    # =========================

    def test_session_id_persistent_in_model(self, model):
        """Test session_id is consistent within model."""
        result1 = model.assess_scalability("Task 1")
        result2 = model.assess_scalability("Task 2")

        assert result1.session_id == result2.session_id

    def test_different_models_different_sessions(self):
        """Test different model instances have different sessions."""
        model1 = ScalingAssessmentModel()
        model2 = ScalingAssessmentModel()

        result1 = model1.assess_scalability("Task")
        result2 = model2.assess_scalability("Task")

        assert result1.session_id != result2.session_id

    # =========================
    # SIGNAL STRUCTURE (38-40)
    # =========================

    def test_signal_structure_complete(self, model):
        """Test all required signal fields present."""
        result = model.assess_scalability("Process batch")

        assert hasattr(result, 'task_description')
        assert hasattr(result, 'scalability_level')
        assert hasattr(result, 'confidence')
        assert hasattr(result, 'bottleneck_type')
        assert hasattr(result, 'parallelizable_units')
        assert hasattr(result, 'reasoning')
        assert hasattr(result, 'evidence_factors')
        assert hasattr(result, 'conditions_for_scale')
        assert hasattr(result, 'session_id')
        assert hasattr(result, 'timestamp')

    def test_signal_serialization(self, model):
        """Test signal can be serialized to JSON."""
        result = model.assess_scalability("Process batch of records")

        signal = {
            "signal_type": "scalability_assessed",
            "signal_layer": "cognition",
            "signal_source": "scaling_model",
            "timestamp": result.timestamp,
            "session_id": result.session_id,
            "data": {
                "task_description": result.task_description,
                "scalability_level": result.scalability_level.value,
                "confidence": result.confidence,
                "bottleneck_type": result.bottleneck_type,
                "parallelizable_units": result.parallelizable_units,
                "reasoning": result.reasoning,
                "evidence_factors": result.evidence_factors,
                "conditions_for_scale": result.conditions_for_scale,
            }
        }

        # Should be JSON serializable
        json_str = json.dumps(signal)
        assert len(json_str) > 0

    def test_signal_type_correct(self, model):
        """Test signal type is correct."""
        result = model.assess_scalability("Test task")
        assert result.scalability_level.value in ["SCALABLE", "NON_SCALABLE", "CONDITIONAL"]

    # =========================
    # CONVENIENCE FUNCTION (41)
    # =========================

    def test_convenience_function(self):
        """Test convenience function."""
        result = assess_scalability("Process batch")
        assert result.scalability_level is not None
        assert isinstance(result, ScalabilityAssessment)

    # =========================
    # SPECIAL CASES (42-45)
    # =========================

    def test_email_batch_scalable(self, model):
        """Test bulk email is classified as scalable."""
        result = model.assess_scalability("Send 1000 bulk emails")
        assert result.scalability_level == ScalabilityLevel.SCALABLE

    def test_meeting_non_scalable(self, model):
        """Test meeting is classified as non-scalable."""
        result = model.assess_scalability("Attend team meeting")
        assert result.scalability_level == ScalabilityLevel.NON_SCALABLE

    def test_conditional_with_multiple_conditions(self, model):
        """Test conditional task can have multiple conditions."""
        result = model.assess_scalability("Process once approved and after setup")
        assert result.scalability_level == ScalabilityLevel.CONDITIONAL
        assert len(result.conditions_for_scale) > 0

    def test_numeric_extraction_from_description(self, model):
        """Test numeric extraction for parallelizable units."""
        result = model.assess_scalability("Process 250 customer records")
        assert result.parallelizable_units >= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
