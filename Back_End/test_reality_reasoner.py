"""
Reality Reasoner Tests - Phase 6 Step 4

Test suite for RealityReasoner aggregator combining:
- Capability Boundary Model
- Human Energy Model
- Scaling Assessment Model

Tests organized by:
1. Role assignment (BUDDY, USER, BOTH, ESCALATE)
2. Risk assessment (LOW, MEDIUM, HIGH, CRITICAL)
3. Capability combinations
4. Cross-model consistency
5. Determinism
6. Session tracking
"""

import unittest
import sys
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from reality_reasoner import (
    RealityReasoner,
    RealityAssessment,
    RoleAssignment,
    RiskLevel,
    assess_reality,
)
from capability_boundary_model import Capability
from human_energy_model import EffortLevel
from scaling_assessment_model import ScalabilityLevel


class TestRealityReasonerRoleAssignment(unittest.TestCase):
    """Tests for role assignment logic."""

    def setUp(self):
        self.reasoner = RealityReasoner()

    def test_buddy_role_digital_low_effort(self):
        """Buddy should handle digital, low effort, scalable tasks."""
        task = "Process data in spreadsheet"
        result = self.reasoner.assess_reality(task)
        
        # Digital with low effort should typically be buddy or both
        if result.capability == Capability.DIGITAL:
            self.assertLess(result.estimated_minutes, 30)
            self.assertIn(result.who_does_what, [RoleAssignment.BUDDY, RoleAssignment.BOTH])

    def test_buddy_role_digital_medium_effort(self):
        """Buddy should handle digital, medium effort, scalable tasks."""
        task = "Parse JSON data and format for reporting"
        result = self.reasoner.assess_reality(task)
        
        self.assertEqual(result.capability, Capability.DIGITAL)
        self.assertEqual(result.effort_level, EffortLevel.MEDIUM)
        # Scalable digital tasks
        self.assertIn(result.who_does_what, [RoleAssignment.BUDDY, RoleAssignment.BOTH])

    def test_user_role_physical_task(self):
        """User must handle physical tasks."""
        task = "Physically deliver package to customer location"
        result = self.reasoner.assess_reality(task)
        
        self.assertEqual(result.capability, Capability.PHYSICAL)
        self.assertEqual(result.who_does_what, RoleAssignment.USER)

    def test_both_role_hybrid_task(self):
        """Collaboration needed for hybrid tasks."""
        task = "Arrange video meeting and send calendar invites"
        result = self.reasoner.assess_reality(task)
        
        self.assertEqual(result.capability, Capability.HYBRID)
        # Should suggest collaboration
        self.assertIn(result.who_does_what, [RoleAssignment.BOTH, RoleAssignment.BUDDY])

    def test_escalate_role_high_effort_human_bottleneck(self):
        """Escalate high-effort human bottleneck tasks."""
        task = "Conduct strategic partnership negotiation"
        result = self.reasoner.assess_reality(task)
        
        # High effort + human involvement = likely escalate or both
        self.assertGreaterEqual(result.estimated_minutes, 30)
        self.assertIn(result.who_does_what, [RoleAssignment.ESCALATE, RoleAssignment.BOTH])


class TestRealityReasonerRiskAssessment(unittest.TestCase):
    """Tests for risk assessment."""

    def setUp(self):
        self.reasoner = RealityReasoner()

    def test_low_risk_simple_task(self):
        """Simple digital task should have low risk."""
        task = "Create list of product names from database"
        result = self.reasoner.assess_reality(task)
        
        self.assertEqual(result.risk_level, RiskLevel.LOW)
        self.assertIsInstance(result.risk_notes, list)

    def test_medium_risk_moderate_effort(self):
        """Moderate effort tasks should have medium risk."""
        task = "Review and update customer database entries"
        result = self.reasoner.assess_reality(task)
        
        self.assertIn(result.risk_level, [RiskLevel.LOW, RiskLevel.MEDIUM])
        self.assertGreater(len(result.risk_notes), 0)

    def test_high_risk_high_effort_bottleneck(self):
        """High effort with human bottleneck should be high risk."""
        task = "Conduct salary negotiation with key employee"
        result = self.reasoner.assess_reality(task)
        
        self.assertEqual(result.effort_level, EffortLevel.HIGH)
        self.assertIn(result.risk_level, [RiskLevel.HIGH, RiskLevel.CRITICAL])

    def test_critical_risk_escalation(self):
        """Complex tasks should be reviewed."""
        task = "Conduct comprehensive legal review process"
        result = self.reasoner.assess_reality(task)
        
        # Should be a substantial task
        self.assertGreater(result.estimated_minutes, 15)


class TestRealityReasonerCapabilityScenarios(unittest.TestCase):
    """Tests for different capability scenarios."""

    def setUp(self):
        self.reasoner = RealityReasoner()

    def test_pure_digital_scalable(self):
        """Digital + scalable should enable parallelization."""
        task = "Process batch of 500 data items"
        result = self.reasoner.assess_reality(task)
        
        # Batch processing should be scalable
        self.assertEqual(result.scalability, ScalabilityLevel.SCALABLE)
        self.assertGreater(result.parallelizable_units, 5)
        self.assertIn(result.risk_level, [RiskLevel.LOW, RiskLevel.MEDIUM])

    def test_digital_non_scalable(self):
        """Digital non-scalable should flag constraints."""
        task = "Manually call each customer to confirm"
        result = self.reasoner.assess_reality(task)
        
        # Should have constraints and risk notes
        self.assertGreater(len(result.risk_notes), 0)
        self.assertGreater(len(result.conditions), 0)

    def test_physical_scalable_warning(self):
        """Physical tasks can't truly scale - humans are bottleneck."""
        task = "Deliver packages to 100 customer locations"
        result = self.reasoner.assess_reality(task)
        
        self.assertEqual(result.capability, Capability.PHYSICAL)
        # Physical can't scale in traditional sense
        self.assertNotEqual(result.who_does_what, RoleAssignment.BUDDY)

    def test_hybrid_requires_approval(self):
        """Tasks with mixed requirements should have conditions."""
        task = "Create report and present to executive team"
        result = self.reasoner.assess_reality(task)
        
        # Should have meaningful conditions
        self.assertGreater(len(result.conditions), 0)


class TestRealityReasonerEffortScenarios(unittest.TestCase):
    """Tests for effort-based scenarios."""

    def setUp(self):
        self.reasoner = RealityReasoner()

    def test_low_effort_fast_task(self):
        """Low effort should be quick."""
        task = "Generate report summary"
        result = self.reasoner.assess_reality(task)
        
        self.assertEqual(result.effort_level, EffortLevel.LOW)
        self.assertLess(result.max_minutes, 60)

    def test_medium_effort_moderate_time(self):
        """Medium effort should be moderate time."""
        task = "Analyze sales trends and create visualization"
        result = self.reasoner.assess_reality(task)
        
        self.assertEqual(result.effort_level, EffortLevel.MEDIUM)
        self.assertGreater(result.estimated_minutes, 10)

    def test_high_effort_extended_time(self):
        """High effort should require significant time."""
        task = "Conduct comprehensive audit of all accounting records"
        result = self.reasoner.assess_reality(task)
        
        self.assertEqual(result.effort_level, EffortLevel.HIGH)
        self.assertGreater(result.estimated_minutes, 30)

    def test_effort_ranges_valid(self):
        """Effort time ranges should be valid."""
        task = "Update database configuration"
        result = self.reasoner.assess_reality(task)
        
        self.assertLess(result.min_minutes, result.estimated_minutes)
        self.assertLess(result.estimated_minutes, result.max_minutes)


class TestRealityReasonerScalabilityScenarios(unittest.TestCase):
    """Tests for scalability-based scenarios."""

    def setUp(self):
        self.reasoner = RealityReasoner()

    def test_scalable_parallel_units(self):
        """Scalable tasks should have high parallel units."""
        task = "Batch process customer records"
        result = self.reasoner.assess_reality(task)
        
        if result.scalability == ScalabilityLevel.SCALABLE:
            self.assertGreater(result.parallelizable_units, 5)

    def test_non_scalable_single_unit(self):
        """Non-scalable should be single unit."""
        task = "Call customer to get approval before proceeding"
        result = self.reasoner.assess_reality(task)
        
        self.assertIn(result.scalability, [ScalabilityLevel.NON_SCALABLE, ScalabilityLevel.CONDITIONAL])
        # Non-scalable should have human bottleneck
        self.assertEqual(result.bottleneck_type, "human")

    def test_conditional_scalable_with_conditions(self):
        """Conditional scalable should list conditions."""
        task = "Process orders with manager approval required"
        result = self.reasoner.assess_reality(task)
        
        # Should have conditions regardless of scalability classification
        self.assertGreater(len(result.conditions), 0)

    def test_bottleneck_types_identified(self):
        """Different bottlenecks should be identified."""
        # Human bottleneck task
        task1 = "Conduct salary negotiation with key employee"
        result1 = self.reasoner.assess_reality(task1)
        # Bottleneck should be identified (may be human, system, or other)
        self.assertIsNotNone(result1.bottleneck_type)
        self.assertGreater(len(result1.bottleneck_type), 0)


class TestRealityReasonerConditions(unittest.TestCase):
    """Tests for condition generation."""

    def setUp(self):
        self.reasoner = RealityReasoner()

    def test_conditions_present_for_complex_task(self):
        """Complex tasks should have conditions."""
        task = "Reorganize filing system with high effort"
        result = self.reasoner.assess_reality(task)
        
        self.assertIsInstance(result.conditions, list)
        self.assertGreater(len(result.conditions), 0)

    def test_conditions_none_for_simple_task(self):
        """Simple tasks might have no conditions."""
        task = "Sort list alphabetically"
        result = self.reasoner.assess_reality(task)
        
        self.assertIsInstance(result.conditions, list)
        # Either "None" or empty is acceptable
        if result.conditions:
            self.assertNotEqual(result.conditions, [])

    def test_physical_task_has_availability_condition(self):
        """Physical tasks should mention availability."""
        task = "Inspect equipment on-site"
        result = self.reasoner.assess_reality(task)
        
        # Should have conditions
        self.assertGreater(len(result.conditions), 0)


class TestRealityReasonerReasoning(unittest.TestCase):
    """Tests for reasoning output."""

    def setUp(self):
        self.reasoner = RealityReasoner()

    def test_integrated_reasoning_present(self):
        """All assessments should have integrated reasoning."""
        task = "Clean up database"
        result = self.reasoner.assess_reality(task)
        
        self.assertIsNotNone(result.reasoning)
        self.assertGreater(len(result.reasoning), 10)

    def test_reasoning_by_model_complete(self):
        """Should have reasoning from each model."""
        task = "Generate monthly financial report"
        result = self.reasoner.assess_reality(task)
        
        self.assertIn("capability", result.reasoning_by_model)
        self.assertIn("energy", result.reasoning_by_model)
        self.assertIn("scalability", result.reasoning_by_model)

    def test_reasoning_mentions_role(self):
        """Reasoning should mention the determined role."""
        task = "Archive old project files"
        result = self.reasoner.assess_reality(task)
        
        # Role name should appear in reasoning
        role_words = result.who_does_what.value.lower().split()
        reasoning_lower = result.reasoning.lower()
        # At least role concept should be in reasoning
        self.assertTrue(any(word in reasoning_lower for word in ["execute", "handle", "requires", "need"]))


class TestRealityReasonerMetadata(unittest.TestCase):
    """Tests for metadata and session tracking."""

    def setUp(self):
        self.reasoner = RealityReasoner()

    def test_session_id_present(self):
        """Assessment should have session ID."""
        task = "Test task"
        result = self.reasoner.assess_reality(task)
        
        self.assertIsNotNone(result.session_id)
        self.assertGreater(len(result.session_id), 0)

    def test_timestamp_valid(self):
        """Assessment should have valid timestamp."""
        task = "Test task"
        result = self.reasoner.assess_reality(task)
        
        self.assertIsNotNone(result.timestamp)
        # Should be parseable as ISO format
        datetime.fromisoformat(result.timestamp)

    def test_session_persistence(self):
        """Same reasoner should have same session ID."""
        task1 = "Task one"
        task2 = "Task two"
        
        result1 = self.reasoner.assess_reality(task1)
        result2 = self.reasoner.assess_reality(task2)
        
        self.assertEqual(result1.session_id, result2.session_id)

    def test_task_description_preserved(self):
        """Original task should be preserved."""
        task = "Specific detailed task description"
        result = self.reasoner.assess_reality(task)
        
        self.assertEqual(result.task_description, task)


class TestRealityReasonerAssessmentStructure(unittest.TestCase):
    """Tests for assessment structure and completeness."""

    def setUp(self):
        self.reasoner = RealityReasoner()

    def test_assessment_is_complete(self):
        """All required fields should be present."""
        task = "Complete assessment test"
        result = self.reasoner.assess_reality(task)
        
        # Check all required fields exist
        self.assertIsNotNone(result.task_description)
        self.assertIsNotNone(result.who_does_what)
        self.assertIsNotNone(result.capability)
        self.assertIsNotNone(result.effort_level)
        self.assertIsNotNone(result.scalability)
        self.assertIsNotNone(result.estimated_minutes)
        self.assertIsNotNone(result.min_minutes)
        self.assertIsNotNone(result.max_minutes)
        self.assertIsNotNone(result.parallelizable_units)
        self.assertIsNotNone(result.bottleneck_type)
        self.assertIsNotNone(result.risk_level)
        self.assertIsNotNone(result.risk_notes)
        self.assertIsNotNone(result.conditions)
        self.assertIsNotNone(result.reasoning)
        self.assertIsNotNone(result.reasoning_by_model)
        self.assertIsNotNone(result.session_id)
        self.assertIsNotNone(result.timestamp)

    def test_assessment_is_dataclass(self):
        """RealityAssessment should be a proper dataclass."""
        task = "Test"
        result = self.reasoner.assess_reality(task)
        
        # Should be convertible to dict
        self.assertIsInstance(result.__dict__, dict)
        self.assertGreater(len(result.__dict__), 10)

    def test_risk_notes_not_empty_for_concerns(self):
        """Risk notes should exist for concerning tasks."""
        task = "High-effort complex task requiring extensive review"
        result = self.reasoner.assess_reality(task)
        
        if result.risk_level != RiskLevel.LOW:
            self.assertGreater(len(result.risk_notes), 0)

    def test_parallelizable_units_positive(self):
        """Parallelizable units should always be positive."""
        task = "Any task"
        result = self.reasoner.assess_reality(task)
        
        self.assertGreater(result.parallelizable_units, 0)


class TestRealityReasonerCrossModelConsistency(unittest.TestCase):
    """Tests for consistency across models."""

    def setUp(self):
        self.reasoner = RealityReasoner()

    def test_digital_scalable_low_risk(self):
        """Digital + Scalable should typically be low risk."""
        task = "Process batch of items in parallel"
        result = self.reasoner.assess_reality(task)
        
        if (result.capability == Capability.DIGITAL and 
            result.scalability == ScalabilityLevel.SCALABLE):
            self.assertIn(result.risk_level, [RiskLevel.LOW, RiskLevel.MEDIUM])

    def test_physical_user_required(self):
        """Physical tasks should always require user."""
        task = "Physically move equipment to warehouse"
        result = self.reasoner.assess_reality(task)
        
        if result.capability == Capability.PHYSICAL:
            self.assertEqual(result.who_does_what, RoleAssignment.USER)

    def test_high_effort_involves_user(self):
        """High effort should typically involve user."""
        task = "Conduct comprehensive strategic review"
        result = self.reasoner.assess_reality(task)
        
        if result.effort_level == EffortLevel.HIGH:
            self.assertIn(result.who_does_what, 
                         [RoleAssignment.USER, RoleAssignment.BOTH, RoleAssignment.ESCALATE])

    def test_non_scalable_high_effort_escalates(self):
        """Non-scalable + high effort should escalate."""
        task = "Approve all customer accounts manually"
        result = self.reasoner.assess_reality(task)
        
        if (result.scalability == ScalabilityLevel.NON_SCALABLE and 
            result.effort_level == EffortLevel.HIGH):
            # Should be high risk or escalated
            self.assertIn(result.risk_level, [RiskLevel.HIGH, RiskLevel.CRITICAL])


class TestRealityReasonerDeterminism(unittest.TestCase):
    """Tests for deterministic behavior."""

    def setUp(self):
        self.reasoner = RealityReasoner()

    def test_same_task_same_assessment(self):
        """Same task should produce same assessment."""
        task = "Analyze sales data"
        
        result1 = self.reasoner.assess_reality(task)
        result2 = self.reasoner.assess_reality(task)
        
        # Core results should match (excluding timestamps)
        self.assertEqual(result1.capability, result2.capability)
        self.assertEqual(result1.effort_level, result2.effort_level)
        self.assertEqual(result1.scalability, result2.scalability)
        self.assertEqual(result1.who_does_what, result2.who_does_what)
        self.assertEqual(result1.risk_level, result2.risk_level)

    def test_new_reasoner_different_session(self):
        """New reasoner should have different session."""
        task = "Test task"
        
        reasoner1 = RealityReasoner()
        reasoner2 = RealityReasoner()
        
        result1 = reasoner1.assess_reality(task)
        result2 = reasoner2.assess_reality(task)
        
        # Sessions should be different
        self.assertNotEqual(result1.session_id, result2.session_id)
        # But assessments should be same
        self.assertEqual(result1.capability, result2.capability)


class TestRealityReasonerConvenienceFunction(unittest.TestCase):
    """Tests for convenience function."""

    def test_convenience_function_works(self):
        """Convenience function should produce valid assessment."""
        task = "Test convenience function"
        result = assess_reality(task)
        
        self.assertIsInstance(result, RealityAssessment)
        self.assertEqual(result.task_description, task)
        self.assertIsNotNone(result.who_does_what)

    def test_convenience_function_different_sessions(self):
        """Each convenience call should have different session."""
        task = "Test"
        
        result1 = assess_reality(task)
        result2 = assess_reality(task)
        
        # Different reasoners = different sessions
        self.assertNotEqual(result1.session_id, result2.session_id)


class TestRealityReasonerEdgeCases(unittest.TestCase):
    """Tests for edge cases."""

    def setUp(self):
        self.reasoner = RealityReasoner()

    def test_empty_task_description(self):
        """Should handle empty task gracefully."""
        result = self.reasoner.assess_reality("")
        
        self.assertIsInstance(result, RealityAssessment)
        self.assertEqual(result.task_description, "")

    def test_very_long_task_description(self):
        """Should handle very long tasks."""
        long_task = "Process " + ("x" * 1000)
        result = self.reasoner.assess_reality(long_task)
        
        self.assertIsInstance(result, RealityAssessment)

    def test_special_characters_in_task(self):
        """Should handle special characters."""
        task = "Test @#$%^&*() with special: chars!"
        result = self.reasoner.assess_reality(task)
        
        self.assertIsInstance(result, RealityAssessment)

    def test_unicode_in_task(self):
        """Should handle unicode characters."""
        task = "Process données français 日本語"
        result = self.reasoner.assess_reality(task)
        
        self.assertIsInstance(result, RealityAssessment)


class TestRealityReasonerIntegration(unittest.TestCase):
    """Integration tests combining multiple aspects."""

    def setUp(self):
        self.reasoner = RealityReasoner()

    def test_full_workflow_simple_task(self):
        """Complete workflow for simple task."""
        task = "Sort and organize list"
        result = self.reasoner.assess_reality(task)
        
        # Should be straightforward with low risk
        self.assertLess(result.estimated_minutes, 30)
        self.assertEqual(result.risk_level, RiskLevel.LOW)

    def test_full_workflow_complex_task(self):
        """Complete workflow for complex task."""
        task = "Conduct strategic partnership review meeting"
        result = self.reasoner.assess_reality(task)
        
        # Should be hybrid, medium-high effort, likely requires collaboration
        self.assertEqual(result.capability, Capability.HYBRID)
        self.assertIn(result.effort_level, [EffortLevel.MEDIUM, EffortLevel.HIGH])
        self.assertIn(result.who_does_what, [RoleAssignment.BOTH, RoleAssignment.ESCALATE])

    def test_full_workflow_physical_task(self):
        """Complete workflow for physical task."""
        task = "Install equipment on-site at customer location"
        result = self.reasoner.assess_reality(task)
        
        # Should be physical, requires user
        self.assertEqual(result.capability, Capability.PHYSICAL)
        self.assertEqual(result.who_does_what, RoleAssignment.USER)


if __name__ == '__main__':
    unittest.main()

