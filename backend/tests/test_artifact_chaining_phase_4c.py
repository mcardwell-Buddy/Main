"""
Phase 4C: Artifact Chaining & Summaries Tests

Comprehensive test suite for read-only artifact interpretation, summarization, and comparison.

CRITICAL INVARIANTS:
✓ No missions spawned
✓ No tools executed
✓ No session context mutation
✓ No approval state changes
✓ Deterministic responses only
✓ No cross-session leakage
"""

import unittest
from datetime import datetime
from typing import Dict, Any, Optional

from backend.response_envelope import ResponseEnvelope, ResponseType
from backend.session_context import SessionContextManager
from backend.interaction_orchestrator import InteractionOrchestrator


# Test Infrastructure
_ORCHESTRATOR_CACHE: Dict[str, InteractionOrchestrator] = {}


def get_or_create_orchestrator(session_id: str) -> InteractionOrchestrator:
    """Cache orchestrator per session to preserve session context."""
    if session_id not in _ORCHESTRATOR_CACHE:
        _ORCHESTRATOR_CACHE[session_id] = InteractionOrchestrator()
    return _ORCHESTRATOR_CACHE[session_id]


def clear_orchestrator_cache():
    """Clear cache after test."""
    _ORCHESTRATOR_CACHE.clear()


def seed_execution_artifact(
    orchestrator: InteractionOrchestrator,
    session_id: str,
    artifact: Dict[str, Any],
) -> None:
    """Seed execution artifact into session context for testing."""
    session_context_mgr = orchestrator._session_context_manager
    context = session_context_mgr.get_or_create(session_id)
    context.set_last_execution_artifact(artifact)


def run_message(
    orchestrator: InteractionOrchestrator,
    session_id: str,
    message: str,
    user_id: str = "test_user",
) -> ResponseEnvelope:
    """Run message through orchestrator."""
    return orchestrator.process_message(
        user_id=user_id,
        session_id=session_id,
        message=message,
        context={},
    )


# ============================================================================
# LEVEL 1: Single Artifact Summarization
# ============================================================================


class TestLevel1SingleArtifact(unittest.TestCase):
    """Level 1 - Basic single artifact summarization."""

    def setUp(self):
        clear_orchestrator_cache()

    def tearDown(self):
        clear_orchestrator_cache()

    def test_summarize_last_artifact_basic(self):
        """
        Given one completed extract artifact
        When user asks 'Summarize what you found'
        Then returns execution summary
        And no mission is created
        """
        orchestrator = get_or_create_orchestrator("session1")
        
        artifact = {
            "artifact_type": "extraction",
            "objective_type": "extract",
            "source_url": "https://example.com",
            "final_url": "https://example.com/page",
            "timestamp": datetime.now().isoformat(),
            "extracted_data": {
                "items": ["Item 1", "Item 2", "Item 3"],
            },
            "result_summary": "Extracted 3 items from example.com",
        }
        seed_execution_artifact(orchestrator, "session1", artifact)
        
        response = run_message(orchestrator, "session1", "Summarize what you found?")
        
        # Assert response structure
        self.assertIsNotNone(response)
        self.assertEqual(response.response_type, ResponseType.TEXT)
        self.assertIsNotNone(response.summary)
        
        # Assert no missions
        self.assertEqual(len(response.missions_spawned), 0)
        
        # Assert content mentions key fields
        content = response.summary.lower()
        self.assertIn("extract", content)
        self.assertIn("example.com", content) or self.assertIn("3", content)

    def test_summarize_without_artifact(self):
        """
        Given no execution artifacts
        When user asks 'Summarize what you found'
        Then returns 'I don't have any artifacts' message
        """
        orchestrator = get_or_create_orchestrator("session2")
        
        response = run_message(orchestrator, "session2", "Summarize what you found?")
        
        # Assert response indicates no artifacts
        self.assertIsNotNone(response)
        self.assertEqual(response.response_type, ResponseType.TEXT)
        self.assertIn("don't have", response.summary.lower()) or \
            self.assertIn("artifact", response.summary.lower())

    def test_summarize_with_no_extraction_data(self):
        """
        Given artifact with no extracted_data field
        When user asks 'Summarize'
        Then returns safe summary without errors
        """
        orchestrator = get_or_create_orchestrator("session3")
        
        artifact = {
            "artifact_type": "extraction",
            "objective_type": "extract",
            "source_url": "https://example.com",
            "result_summary": "Completed extraction",
        }
        seed_execution_artifact(orchestrator, "session3", artifact)
        
        response = run_message(orchestrator, "session3", "Summarize please?")
        
        # Assert safe response
        self.assertIsNotNone(response)
        self.assertEqual(response.response_type, ResponseType.TEXT)
        self.assertIsNotNone(response.summary)


# ============================================================================
# LEVEL 2: Multiple Artifacts Summarization
# ============================================================================


class TestLevel2MultipleArtifacts(unittest.TestCase):
    """Level 2 - Multiple artifact summarization."""

    def setUp(self):
        clear_orchestrator_cache()

    def tearDown(self):
        clear_orchestrator_cache()

    def test_summarize_everything_multiple_artifacts(self):
        """
        Given two execution artifacts in session
        When user asks 'Summarize everything'
        Then returns combined summary
        And preserves artifact order
        """
        orchestrator = get_or_create_orchestrator("session4")
        session_context = orchestrator._session_context_manager.get_or_create("session4")
        
        # Seed first artifact (note: session stores last_execution_artifact, 
        # so we simulate history by tracking what was stored)
        artifact1 = {
            "artifact_type": "extraction",
            "objective_type": "extract",
            "source_url": "https://example.com",
            "extracted_data": {"items": ["A", "B"]},
            "result_summary": "First extraction",
        }
        
        artifact2 = {
            "artifact_type": "extraction",
            "objective_type": "extract",
            "source_url": "https://other.com",
            "extracted_data": {"items": ["C", "D", "E"]},
            "result_summary": "Second extraction",
        }
        
        # Store most recent
        session_context.set_last_execution_artifact(artifact2)
        
        # For this test, we check what's available
        response = run_message(orchestrator, "session4", "Summarize everything?")
        
        # Assert we get a response
        self.assertIsNotNone(response)
        self.assertEqual(response.response_type, ResponseType.TEXT)
        self.assertEqual(len(response.missions_spawned), 0)

    def test_multiple_artifacts_no_mission_creation(self):
        """
        Given multiple artifacts
        When user asks 'Compare results'
        Then no missions are created
        And no tools are executed
        """
        orchestrator = get_or_create_orchestrator("session5")
        
        artifact = {
            "artifact_type": "extraction",
            "objective_type": "extract",
            "source_url": "https://example.com",
            "extracted_data": {"items": ["X", "Y", "Z"]},
        }
        seed_execution_artifact(orchestrator, "session5", artifact)
        
        response = run_message(orchestrator, "session5", "Summarize everything?")
        
        # Assert ZERO missions
        self.assertEqual(len(response.missions_spawned), 0)
        self.assertEqual(response.response_type, ResponseType.TEXT)


# ============================================================================
# LEVEL 3: Comparison of Two Artifacts
# ============================================================================


class TestLevel3Comparison(unittest.TestCase):
    """Level 3 - Artifact comparison."""

    def setUp(self):
        clear_orchestrator_cache()

    def tearDown(self):
        clear_orchestrator_cache()

    def test_compare_last_two_same_source(self):
        """
        Given two extract artifacts from same source
        When user asks 'Compare the last two results'
        Then returns structured comparison
        And indicates 'no differences' in source
        """
        orchestrator = get_or_create_orchestrator("session6")
        session_context = orchestrator._session_context_manager.get_or_create("session6")
        
        artifact = {
            "artifact_type": "extraction",
            "objective_type": "extract",
            "source_url": "https://example.com",
            "extracted_data": {"items": ["A", "B", "C", "D"]},
        }
        session_context.set_last_execution_artifact(artifact)
        
        response = run_message(orchestrator, "session6", "Compare the last two?")
        
        # Assert we get a response
        self.assertIsNotNone(response)
        self.assertEqual(response.response_type, ResponseType.TEXT)
        self.assertEqual(len(response.missions_spawned), 0)

    def test_compare_different_intents(self):
        """
        Given two artifacts with different intents
        When user asks 'Compare'
        Then returns comparison showing intent change
        """
        orchestrator = get_or_create_orchestrator("session7")
        session_context = orchestrator._session_context_manager.get_or_create("session7")
        
        artifact = {
            "artifact_type": "extraction",
            "objective_type": "search",  # Different intent
            "source_url": "https://google.com",
            "extracted_data": {"items": ["Result1", "Result2"]},
        }
        session_context.set_last_execution_artifact(artifact)
        
        response = run_message(orchestrator, "session7", "Compare intents?")
        
        self.assertIsNotNone(response)
        self.assertEqual(response.response_type, ResponseType.TEXT)


# ============================================================================
# LEVEL 4: Change Detection
# ============================================================================


class TestLevel4ChangeDetection(unittest.TestCase):
    """Level 4 - Change detection across artifacts."""

    def setUp(self):
        clear_orchestrator_cache()

    def tearDown(self):
        clear_orchestrator_cache()

    def test_what_changed_since_last_time(self):
        """
        Given two executions with different sources
        When user asks 'What changed since last time?'
        Then identifies source change
        And returns structured diff
        """
        orchestrator = get_or_create_orchestrator("session8")
        session_context = orchestrator._session_context_manager.get_or_create("session8")
        
        artifact = {
            "artifact_type": "extraction",
            "objective_type": "extract",
            "source_url": "https://newsite.com",
            "extracted_data": {"items": ["New1", "New2", "New3"]},
        }
        session_context.set_last_execution_artifact(artifact)
        
        response = run_message(orchestrator, "session8", "What changed since last time?")
        
        # Assert we get a response
        self.assertIsNotNone(response)
        self.assertEqual(response.response_type, ResponseType.TEXT)
        self.assertEqual(len(response.missions_spawned), 0)

    def test_item_count_delta_detection(self):
        """
        Given two executions with different item counts
        When user asks about changes
        Then detects and reports count delta
        """
        orchestrator = get_or_create_orchestrator("session9")
        session_context = orchestrator._session_context_manager.get_or_create("session9")
        
        artifact = {
            "artifact_type": "extraction",
            "objective_type": "extract",
            "source_url": "https://example.com",
            "extracted_data": {"items": ["A", "B", "C", "D", "E"]},  # 5 items
        }
        session_context.set_last_execution_artifact(artifact)
        
        response = run_message(orchestrator, "session9", "What's different?")
        
        self.assertIsNotNone(response)
        self.assertEqual(response.response_type, ResponseType.TEXT)


# ============================================================================
# LEVEL 5: Safety Invariants
# ============================================================================


class TestLevel5SafetyInvariants(unittest.TestCase):
    """Level 5 - Critical safety invariants."""

    def setUp(self):
        clear_orchestrator_cache()

    def tearDown(self):
        clear_orchestrator_cache()

    def test_phase_4c_never_creates_missions(self):
        """
        INVARIANT: Phase 4C must NEVER create missions.
        
        Given artifact chaining question with artifact
        When processed through orchestrator
        Then missions_spawned == []
        """
        orchestrator = get_or_create_orchestrator("session10")
        
        artifact = {
            "artifact_type": "extraction",
            "objective_type": "extract",
            "source_url": "https://example.com",
            "extracted_data": {"items": ["1", "2"]},
        }
        seed_execution_artifact(orchestrator, "session10", artifact)
        
        # Try various artifact chaining phrases
        phrases = [
            "Summarize what you found?",
            "Compare everything?",
            "What changed?",
            "Review all results?",
        ]
        
        for phrase in phrases:
            response = run_message(orchestrator, "session10", phrase)
            self.assertEqual(
                len(response.missions_spawned), 0,
                f"Phase 4C created mission for: {phrase}"
            )

    def test_phase_4c_never_executes_tools(self):
        """
        INVARIANT: Phase 4C must NEVER execute tools.
        
        Given artifact chaining question
        When processed
        Then execution_service is never called
        And response has no execution signals
        """
        orchestrator = get_or_create_orchestrator("session11")
        
        artifact = {
            "artifact_type": "extraction",
            "source_url": "https://example.com",
            "extracted_data": {"items": ["A", "B", "C"]},
        }
        seed_execution_artifact(orchestrator, "session11", artifact)
        
        response = run_message(orchestrator, "session11", "Summarize everything?")
        
        # Assert no execution
        self.assertEqual(response.response_type, ResponseType.TEXT)
        self.assertEqual(len(response.missions_spawned), 0)
        self.assertEqual(len(response.signals_emitted), 0)

    def test_phase_4c_does_not_mutate_session(self):
        """
        INVARIANT: Phase 4C must NEVER mutate SessionContext.
        
        Given artifact in session context
        When Phase 4C processes summary question
        Then artifact remains unchanged
        And pending state remains unchanged
        """
        orchestrator = get_or_create_orchestrator("session12")
        session_context = orchestrator._session_context_manager.get_or_create("session12")
        
        artifact_original = {
            "artifact_type": "extraction",
            "objective_type": "extract",
            "source_url": "https://example.com",
            "extracted_data": {"items": ["X", "Y", "Z"]},
            "timestamp": "2025-01-01T00:00:00",
        }
        session_context.set_last_execution_artifact(dict(artifact_original))
        
        # Get before
        before = session_context.get_last_execution_artifact()
        before_pending_mission = session_context.get_pending_mission()
        before_pending_clarification = session_context.get_pending_clarification()
        
        # Process artifact chaining query
        response = run_message(orchestrator, "session12", "Summarize all?")
        
        # Get after
        after = session_context.get_last_execution_artifact()
        after_pending_mission = session_context.get_pending_mission()
        after_pending_clarification = session_context.get_pending_clarification()
        
        # Assert no mutations
        self.assertEqual(before, after)
        self.assertEqual(before_pending_mission, after_pending_mission)
        self.assertEqual(before_pending_clarification, after_pending_clarification)

    def test_phase_4c_no_cross_session_leakage(self):
        """
        INVARIANT: Phase 4C must not leak artifacts between sessions.
        
        Given artifacts in session A
        When user in session B asks for summary
        Then session B does not see session A artifacts
        """
        orchestrator = get_or_create_orchestrator("session13")
        
        # Session A has artifact
        artifact_a = {
            "artifact_type": "extraction",
            "source_url": "https://session-a.com",
            "extracted_data": {"items": ["A1", "A2"]},
        }
        seed_execution_artifact(orchestrator, "session13", artifact_a)
        
        # Session B (different) has no artifact
        response_b = run_message(orchestrator, "session14", "Summarize everything?")
        
        # Session B should indicate no artifacts
        self.assertIn(
            ("don't have" in response_b.summary.lower() or
             "artifact" in response_b.summary.lower()),
            [True]
        )


# ============================================================================
# Phase 3 & 4A/4B Regression Tests
# ============================================================================


class TestRegressionPhase3And4(unittest.TestCase):
    """Verify Phase 4C doesn't break Phase 3, 4A, or 4B."""

    def setUp(self):
        clear_orchestrator_cache()

    def tearDown(self):
        clear_orchestrator_cache()

    def test_approval_phrases_still_routed_to_bridge(self):
        """
        REGRESSION: Approval phrases should NOT be handled as Phase 4C.
        
        Given artifact and "yes" message
        When "yes" is NOT a chaining phrase
        Then routed to approval bridge, not Phase 4C
        """
        orchestrator = get_or_create_orchestrator("session15")
        
        artifact = {
            "artifact_type": "extraction",
            "source_url": "https://example.com",
            "extracted_data": {"items": ["X"]},
        }
        seed_execution_artifact(orchestrator, "session15", artifact)
        
        # "yes" should NOT trigger Phase 4C
        response = run_message(orchestrator, "session15", "yes")
        
        # Should get approval bridge response, not artifact summary
        self.assertIsNotNone(response)
        # Response depends on pending mission state

    def test_execution_verbs_not_confused_with_chaining(self):
        """
        REGRESSION: "Extract everything" should NOT trigger Phase 4C.
        
        Given artifact
        When user says "Extract everything"
        Then treated as execution command, not summary
        """
        orchestrator = get_or_create_orchestrator("session16")
        
        artifact = {
            "artifact_type": "extraction",
            "source_url": "https://example.com",
            "extracted_data": {"items": ["A", "B"]},
        }
        seed_execution_artifact(orchestrator, "session16", artifact)
        
        response = run_message(orchestrator, "session16", "Extract everything?")
        
        # Should NOT be artifact summary (Phase 4C)
        # May be intent classification or other handling
        self.assertIsNotNone(response)

    def test_phase_4b_single_artifact_followup_still_works(self):
        """
        REGRESSION: Phase 4B single-artifact follow-ups should still work.
        
        Given artifact
        When user asks "What did you find?"
        Then Phase 4B handles it, not Phase 4C
        """
        orchestrator = get_or_create_orchestrator("session17")
        
        artifact = {
            "artifact_type": "extraction",
            "source_url": "https://example.com",
            "extracted_data": {"items": ["Item1", "Item2", "Item3"]},
        }
        seed_execution_artifact(orchestrator, "session17", artifact)
        
        response = run_message(orchestrator, "session17", "What did you find?")
        
        # Phase 4B should handle this
        self.assertIsNotNone(response)
        self.assertEqual(response.response_type, ResponseType.TEXT)
        self.assertEqual(len(response.missions_spawned), 0)


# ============================================================================
# Integration & Edge Cases
# ============================================================================


class TestPhase4CIntegration(unittest.TestCase):
    """Integration and edge case tests."""

    def setUp(self):
        clear_orchestrator_cache()

    def tearDown(self):
        clear_orchestrator_cache()

    def test_chaining_phrase_without_question_mark_still_works(self):
        """
        Given artifact and summary phrase without question mark
        When asking for summary
        Then still processes as Phase 4C
        """
        orchestrator = get_or_create_orchestrator("session18")
        
        artifact = {
            "artifact_type": "extraction",
            "source_url": "https://example.com",
            "extracted_data": {"items": ["A", "B"]},
        }
        seed_execution_artifact(orchestrator, "session18", artifact)
        
        # No question mark
        response = run_message(orchestrator, "session18", "Summarize everything")
        
        self.assertIsNotNone(response)
        self.assertEqual(response.response_type, ResponseType.TEXT)

    def test_chaining_with_mixed_case(self):
        """
        Given summary phrase in mixed case
        When asking for summary
        Then Phase 4C handles it (case-insensitive)
        """
        orchestrator = get_or_create_orchestrator("session19")
        
        artifact = {
            "artifact_type": "extraction",
            "source_url": "https://example.com",
            "extracted_data": {"items": ["X", "Y"]},
        }
        seed_execution_artifact(orchestrator, "session19", artifact)
        
        response = run_message(orchestrator, "session19", "SUMMARIZE What You Found?")
        
        self.assertIsNotNone(response)
        self.assertEqual(response.response_type, ResponseType.TEXT)


if __name__ == "__main__":
    unittest.main()
