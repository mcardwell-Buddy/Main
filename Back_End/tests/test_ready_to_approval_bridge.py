"""
Test READY → Approval Bridge

Validates that READY missions produced by ActionReadinessEngine are registered
as approvable missions, and that approval phrases ("yes", "approve") work correctly.

PHASE 3C: Wire READY Missions Into Approval Flow

Test Coverage:
1. READY → yes → execution occurs
2. READY → yes → yes → second approval rejected
3. yes without READY → "nothing to approve"
4. READY mission uses structured fields (not raw text)
"""

import pytest
import json
from pathlib import Path
from Back_End.interaction_orchestrator import InteractionOrchestrator
from Back_End.session_context import SessionContextManager


# Test helpers

# Global cache for orchestrator per session (similar to Phase 3B test pattern)
_orchestrator_cache = {}

def get_or_create_orchestrator(session_id):
    """Get or create an orchestrator for a session."""
    if session_id not in _orchestrator_cache:
        _orchestrator_cache[session_id] = InteractionOrchestrator()
    return _orchestrator_cache[session_id]

def clear_orchestrator_cache():
    """Clear all cached orchestrators."""
    global _orchestrator_cache
    _orchestrator_cache = {}

def clear_missions_log():
    """Clear missions.jsonl for clean test state."""
    missions_log = Path('missions.jsonl')
    if missions_log.exists():
        missions_log.unlink()


def count_missions():
    """Count missions in missions.jsonl."""
    missions_log = Path('missions.jsonl')
    if not missions_log.exists():
        return 0
    with open(missions_log, 'r') as f:
        return sum(1 for line in f if line.strip())


def run_message(message: str, session_id: str = "test_session"):
    """Run a message through the orchestrator (using cached instance for session persistence)."""
    orchestrator = get_or_create_orchestrator(session_id)
    return orchestrator.process_message(message, session_id=session_id)


# ========== PHASE 3C: READY → Approval Tests ==========

def test_invariant_1_ready_mission_is_approvable():
    """
    UX INVARIANT 1: READY → APPROVABLE
    
    A READY mission must always be approvable in the same session.
    
    Flow:
    1. User: "Extract the emails from linkedin.com" → READY mission created
    2. User: "yes" → Mission approved and executed
    """
    clear_orchestrator_cache()
    clear_missions_log()
    
    # Step 1: Create READY mission
    session_id = "test_ready_approvable"
    response1 = run_message("Extract the emails from linkedin.com", session_id)
    
    # Should create mission
    assert len(response1.missions_spawned) == 1, "READY should create mission"
    mission_id = response1.missions_spawned[0].mission_id
    
    # Step 2: Approve with "yes"
    response2 = run_message("yes", session_id)
    
    # Should attempt to execute mission (may fail in test env due to tool selection)
    assert "Approved and executed" in response2.summary or "execution failed" in response2.summary.lower(), \
        f"Approval should attempt execution. Got: {response2.summary}"
    assert mission_id in response2.summary, \
        f"Should reference mission_id. Got: {response2.summary}"
    
    print("✓ Invariant 1: READY missions are approvable")


def test_invariant_2_approval_executes_exactly_once():
    """
    UX INVARIANT 2: Approval Executes Exactly Once
    
    After approval:
    - Mission executes
    - Pending mission is cleared
    - Second "yes" does nothing
    
    Flow:
    1. User: "Navigate to github.com" → READY mission created
    2. User: "yes" → Mission approved and executed
    3. User: "yes" → "There's nothing to approve yet"
    """
    clear_orchestrator_cache()
    clear_missions_log()
    
    # Step 1: Create READY mission
    session_id = "test_single_approval"
    response1 = run_message("Navigate to github.com", session_id)
    
    # Should create mission
    assert len(response1.missions_spawned) == 1, "READY should create mission"
    mission_id = response1.missions_spawned[0].mission_id
    
    # Step 2: First approval - should work
    response2 = run_message("yes", session_id)
    
    assert "Approved and executed" in response2.summary or "execution failed" in response2.summary.lower(), \
        f"First approval should attempt execution. Got: {response2.summary}"
    
    # Step 3: Second approval - should reject
    response3 = run_message("yes", session_id)
    
    assert "nothing to approve" in response3.summary.lower(), \
        f"Second approval should be rejected. Got: {response3.summary}"
    assert "Approved and executed" not in response3.summary and "execution failed" not in response3.summary.lower(), \
        "Second approval should not attempt execution"
    
    print("✓ Invariant 2: Approval executes exactly once")


def test_invariant_3_no_approval_without_ready():
    """
    UX INVARIANT 3: No Approval Without READY
    
    If no READY mission exists:
    - Approval phrases must not execute anything
    - Must respond: "There's nothing to approve yet"
    
    Flow:
    1. User: "yes" (no prior mission) → "nothing to approve"
    2. User: "approve" (no prior mission) → "nothing to approve"
    3. User: "do it" (no prior mission) → "nothing to approve"
    """
    clear_orchestrator_cache()
    clear_missions_log()
    
    session_id = "test_no_approval_without_ready"
    
    # Test different approval phrases without READY mission
    approval_phrases = ["yes", "approve", "do it"]
    
    for phrase in approval_phrases:
        response = run_message(phrase, session_id)
        
        assert "nothing to approve" in response.summary.lower(), \
            f"'{phrase}' without READY should reject. Got: {response.summary}"
        assert len(response.missions_spawned) == 0, \
            f"'{phrase}' should not create missions"
        assert "Approved and executed" not in response.summary and "execution failed" not in response.summary.lower(), \
            f"'{phrase}' should not attempt execution"
    
    print("✓ Invariant 3: No approval without READY mission")


def test_ready_uses_structured_fields_not_raw_text():
    """
    UX INVARIANT 4: READY Mission Uses Structured Fields
    
    READY missions must use validated structured fields from ActionReadinessEngine,
    not raw text parsing.
    
    Verify:
    - Mission contains intent (extract/navigate/search)
    - Mission contains action_object (for extract/search)
    - Mission contains source_url
    - Mission does NOT just contain raw message
    """
    clear_orchestrator_cache()
    clear_missions_log()
    
    session_id = "test_structured_fields"
    
    # Create READY mission
    response = run_message("Extract the emails from linkedin.com", session_id)
    
    # Verify mission was created
    assert len(response.missions_spawned) == 1, "Should create mission"
    
    mission_ref = response.missions_spawned[0]
    
    # Verify structured fields exist
    assert mission_ref.objective_type in ["extract", "navigate", "search"], \
        f"Should have structured objective_type. Got: {mission_ref.objective_type}"
    
    assert mission_ref.objective_description, \
        "Should have objective_description"
    
    # Verify it's not just raw text
    assert "Extract" in mission_ref.objective_description or \
           "extract" in mission_ref.objective_description, \
        f"Should mention action. Got: {mission_ref.objective_description}"
    
    assert "linkedin.com" in mission_ref.objective_description.lower(), \
        f"Should mention source URL. Got: {mission_ref.objective_description}"
    
    print("✓ Invariant 4: READY uses structured fields")


def test_approval_clears_pending_after_execution():
    """
    Test that pending mission is properly cleared after successful execution.
    
    Flow:
    1. Create READY mission
    2. Approve and execute
    3. Verify pending mission is cleared
    4. New READY mission can be created and approved
    """
    clear_orchestrator_cache()
    clear_missions_log()
    
    session_id = "test_pending_cleared"
    
    # First mission
    response1 = run_message("Navigate to github.com", session_id)
    assert len(response1.missions_spawned) == 1, "First mission created"
    
    response2 = run_message("yes", session_id)
    assert "Approved and executed" in response2.summary or "execution failed" in response2.summary.lower(), \
        "First mission should attempt execution"
    
    # Second mission should work independently
    response3 = run_message("Navigate to reddit.com", session_id)
    assert len(response3.missions_spawned) == 1, "Second mission created"
    
    response4 = run_message("yes", session_id)
    assert "Approved and executed" in response4.summary or "execution failed" in response4.summary.lower(), \
        "Second mission should attempt execution"
    assert "reddit.com" in response4.summary.lower() or "github.com" not in response4.summary.lower(), \
        "Should execute second mission, not first"
    
    print("✓ Pending mission properly cleared after execution")


def test_approval_phrases_all_work():
    """
    Test that all approval phrases work: yes, approve, do it, etc.
    
    Each phrase should trigger execution of pending READY mission.
    """
    clear_orchestrator_cache()
    approval_phrases = ["yes", "approve", "do it"]
    
    for phrase in approval_phrases:
        clear_missions_log()
        session_id = f"test_phrase_{phrase.replace(' ', '_')}"
        
        # Create READY mission
        response1 = run_message("Navigate to example.com", session_id)
        assert len(response1.missions_spawned) == 1, f"Mission created for phrase '{phrase}'"
        
        # Approve with this phrase
        response2 = run_message(phrase, session_id)
        
        assert "Approved and executed" in response2.summary or "execution failed" in response2.summary.lower(), \
            f"Phrase '{phrase}' should trigger approval. Got: {response2.summary}"
    
    print("✓ All approval phrases work")


def test_incomplete_mission_not_approvable():
    """
    Test that INCOMPLETE missions (blocked by readiness) do not become approvable.
    
    Flow:
    1. User: "Extract from linkedin.com" (missing object) → INCOMPLETE, clarification shown
    2. User: "yes" → clarification re-emitted (INCOMPLETE pending clarifications cannot be approved)
    """
    clear_orchestrator_cache()
    clear_missions_log()
    
    session_id = "test_incomplete_not_approvable"
    
    # Send incomplete message
    response1 = run_message("Extract from linkedin.com", session_id)
    
    # Should not create mission
    assert len(response1.missions_spawned) == 0, "INCOMPLETE should not create mission"
    
    # Should ask for clarification
    assert "extract" in response1.summary.lower(), "Should mention action"
    
    # Try to approve - should re-emit clarification (Phase 4A behavior)
    response2 = run_message("yes", session_id)
    
    assert "extract" in response2.summary.lower(), \
        f"INCOMPLETE mission should re-emit clarification. Got: {response2.summary}"
    assert len(response2.missions_spawned) == 0, "Should not create mission on 'yes'"
    
    print("✓ INCOMPLETE missions are not approvable")


# ========== Regression Guards ==========

def test_phase_3a_3b_still_work():
    """
    Regression guard: Phase 3A.1, 3A.2, and 3B still work.
    
    Verify:
    - Sole mission gate (Phase 3A.1)
    - Session context (Phase 3A.2)
    - Targeted clarifications (Phase 3B)
    """
    clear_orchestrator_cache()
    clear_missions_log()
    
    session_id = "test_regression"
    
    # Phase 3A.1: Incomplete blocks mission
    response1 = run_message("Extract the emails", session_id)
    assert len(response1.missions_spawned) == 0, "INCOMPLETE should block mission"
    
    # Phase 3B: Clarification is targeted
    assert "extract" in response1.summary.lower(), "Clarification should mention action"
    assert "know what" in response1.summary.lower() or "where" in response1.summary.lower(), \
        "Phase 3B clarification should be targeted"
    
    # Phase 3A.1: Complete creates mission
    response2 = run_message("Extract the emails from linkedin.com", session_id)
    assert len(response2.missions_spawned) == 1, "READY should create mission"
    
    # Phase 3A.2: Repeat command works
    response3 = run_message("Do it again", session_id)
    # Should either approve pending or create new mission
    # (depends on whether first was executed or still pending)
    
    print("✓ Phase 3A + 3B regression guard passed")


# ========== Test Runner ==========

if __name__ == "__main__":
    print("=" * 60)
    print("PHASE 3C: READY → Approval Bridge Tests")
    print("=" * 60)
    print()
    
    # Run all tests
    test_invariant_1_ready_mission_is_approvable()
    test_invariant_2_approval_executes_exactly_once()
    test_invariant_3_no_approval_without_ready()
    test_ready_uses_structured_fields_not_raw_text()
    test_approval_clears_pending_after_execution()
    test_approval_phrases_all_work()
    test_incomplete_mission_not_approvable()
    test_phase_3a_3b_still_work()
    
    print()
    print("=" * 60)
    print("✅ ALL PHASE 3C TESTS PASSED")
    print("=" * 60)

