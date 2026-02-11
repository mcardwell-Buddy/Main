"""
Phase 3B: Clarification UX Invariants

Tests proving that clarifications are:
1. Never vague
2. Always actionable  
3. Never create missions
4. Don't break READY behavior
5. Never auto-resolve ambiguity
"""

import json
import time
from pathlib import Path
from Back_End.interaction_orchestrator import InteractionOrchestrator
from Back_End.action_readiness_engine import ClarificationType


# Global orchestrator cache (like Phase 3A.2 tests)
_orchestrator_cache = {}


def get_or_create_orchestrator(session_id: str = "test_session"):
    """Get or create orchestrator for session (maintains context across messages)."""
    if session_id not in _orchestrator_cache:
        _orchestrator_cache[session_id] = InteractionOrchestrator()
    return _orchestrator_cache[session_id]


def clear_orchestrator_cache():
    """Clear the orchestrator cache for next test."""
    global _orchestrator_cache
    _orchestrator_cache.clear()


def clear_missions_log():
    """Clear the missions log before test."""
    missions_file = Path('outputs/phase25/missions.jsonl')
    if missions_file.exists():
        missions_file.unlink()


def count_missions():
    """Count missions in the missions log."""
    missions_file = Path('outputs/phase25/missions.jsonl')
    if not missions_file.exists():
        return 0
    
    with open(missions_file, 'r') as f:
        return sum(1 for _ in f if _.strip())


def run_message(message: str, session_id: str = "test_session"):
    """Run a message through the orchestrator."""
    orchestrator = get_or_create_orchestrator(session_id)
    response = orchestrator.process_message(
        message=message,
        user_id="test_user",
        session_id=session_id,
    )
    time.sleep(0.1)
    return response


# ========== UX INVARIANT 1: Never Ask a Vague Question ==========

def test_invariant_1_clarification_mentions_missing_field():
    """
    UX INVARIANT 1: Never Ask a Vague Question
    
    Forbidden phrases:
    - "Can you provide more details?"
    - "What would you like me to help with?"
    - "I'm missing some information."
    
    Clarifications MUST mention:
    - What is missing
    - Why it's needed
    - How to fix it
    """
    clear_orchestrator_cache()
    clear_missions_log()
    
    # Incomplete extract (missing object)
    response = run_message("Extract from linkedin.com")
    
    assert len(response.missions_spawned) == 0, "Should not create mission"
    assert "extract" in response.summary.lower(), "Should mention the action"
    assert "what" in response.summary.lower(), "Should ask a specific question"
    
    # Verify NEVER forbidden phrases
    forbidden = [
        "provide more details",
        "what would you like",
        "i'm missing some information",
        "missing some required",
    ]
    summary_lower = response.summary.lower()
    for forbidden_phrase in forbidden:
        assert forbidden_phrase not in summary_lower, f"Forbidden phrase found: '{forbidden_phrase}'"
    
    print("✓ Invariant 1: Clarifications are specific, not vague")


def test_invariant_1_clarification_is_contextual():
    """
    UX INVARIANT 1: Clarifications use context when available
    
    If context has prior URL, clarification should suggest it.
    If no context, clarification should ask directly.
    """
    clear_missions_log()
    
    # First mission to establish context
    response1 = run_message(
        "Extract the emails from linkedin.com",
        session_id="test_inv1"
    )
    assert len(response1.missions_spawned) == 1
    
    time.sleep(0.1)
    clear_missions_log()
    
    # Follow-up missing source - context available
    response2 = run_message(
        "Extract the names",
        session_id="test_inv1"
    )
    
    # Should suggest the context URL
    assert "linkedin.com" in response2.summary.lower(), "Should suggest context URL"
    assert len(response2.missions_spawned) == 0, "Should not create mission"
    
    print("✓ Invariant 1: Clarifications are contextual")


# ========== UX INVARIANT 2: Every Clarification Is Actionable ==========

def test_invariant_2_clarification_has_example():
    """
    UX INVARIANT 2: Every Clarification Is Actionable
    
    Each clarification must include at least one of:
    - Example
    - Suggested option
    - Reference to prior context
    """
    clear_missions_log()
    
    # Incomplete extract (missing object)
    response = run_message("Extract from github.com")
    
    assert len(response.missions_spawned) == 0, "Should not create mission"
    
    # Must have at least one actionable element
    summary_lower = response.summary.lower()
    has_actionable = (
        "•" in response.summary or  # Bullet points
        "example" in summary_lower or  # Examples mentioned
        "for example" in summary_lower or  # Examples shown
        "should i" in summary_lower or  # Suggested options
        "tell me" in summary_lower or  # Direct instruction
        "could you" in summary_lower  # Request with context
    )
    
    assert has_actionable, f"Clarification not actionable: {response.summary}"
    
    print("✓ Invariant 2: Clarifications include examples or options")


def test_invariant_2_clarification_is_direct():
    """
    UX INVARIANT 2: Clarification directly addresses the gap
    
    Example: "Extract from" missing object should ask "what to extract"
    NOT "provide more details"
    """
    clear_missions_log()
    
    # Missing object clarification
    response1 = run_message("Extract from linkedin.com")
    assert "extract" in response1.summary.lower()
    assert "what" in response1.summary.lower()
    
    # Missing source clarification  
    response2 = run_message("Extract the emails")
    assert "extract" in response2.summary.lower()
    assert "where" in response2.summary.lower() or "website" in response2.summary.lower()
    
    print("✓ Invariant 2: Clarifications directly address the gap")


# ========== UX INVARIANT 3: Clarifications Never Create Missions ==========

def test_invariant_3_incomplete_never_creates_mission():
    """
    UX INVARIANT 3: Clarifications Never Create Missions
    
    For all INCOMPLETE responses:
    - missions_spawned == []
    - missions.jsonl unchanged
    """
    clear_missions_log()
    
    # Request clarification for many different incomplete cases
    incomplete_messages = [
        "Extract from linkedin.com",  # Missing object
        "Extract the emails",  # Missing source
        "Do it again",  # No prior mission
        "Navigate somewhere",  # No URL in message
        "Search for stuff",  # Vague + missing source
    ]
    
    for msg in incomplete_messages:
        clear_missions_log()
        response = run_message(msg)
        
        # No missions should be created
        assert len(response.missions_spawned) == 0, f"Created mission for: {msg}"
        assert count_missions() == 0, f"Mission logged for: {msg}"
        
        # Response should be clarification (text), not artifact
        from Back_End.response_envelope import ResponseType
        assert response.response_type in {ResponseType.TEXT, ResponseType.CLARIFICATION_REQUEST}, \
            f"Expected text response, got {response.response_type} for: {msg}"
    
    print("✓ Invariant 3: Clarifications never create missions")


# ========== UX INVARIANT 4: READY Behavior Unchanged ==========

def test_invariant_4_ready_creates_mission():
    """
    UX INVARIANT 4: READY Behavior Unchanged
    
    For complete inputs:
    - No clarification shown
    - Mission created exactly as in Phase 3A.2
    """
    clear_missions_log()
    
    # Complete requests should create missions
    # (These have enough context for Buddy to act)
    complete_messages = [
        "Extract the emails from linkedin.com",
        "Navigate to github.com",
        "Search for python developers on github.com",  # action + object + source
    ]
    
    for msg in complete_messages:
        clear_missions_log()
        response = run_message(msg)
        
        # Mission should be created
        assert len(response.missions_spawned) == 1, f"No mission for: {msg}"
        assert count_missions() == 1, f"Mission not logged for: {msg}"
        
        # Response should be artifact (mission), not text clarification
        from Back_End.response_envelope import ResponseType
        assert response.response_type == ResponseType.ARTIFACT_BUNDLE, \
            f"Expected mission response for: {msg}"
    
    print("✓ Invariant 4: READY creates missions, clarification doesn't")


def test_invariant_4_repeat_still_works():
    """
    UX INVARIANT 4: Repeat command still works without clarification
    
    Complete repeat should create mission, not ask for clarification.
    """
    clear_missions_log()
    
    # First mission
    response1 = run_message(
        "Extract the names from github.com",
        session_id="test_inv4_repeat"
    )
    assert len(response1.missions_spawned) == 1
    
    time.sleep(0.1)
    clear_missions_log()
    
    # Repeat
    response2 = run_message(
        "Do it again",
        session_id="test_inv4_repeat"
    )
    
    # Should create mission, not ask for clarification
    assert len(response2.missions_spawned) == 1, "Repeat should create mission"
    assert count_missions() == 1, "Repeat mission should be logged"
    
    print("✓ Invariant 4: Repeat still creates mission")


# ========== UX INVARIANT 5: Ambiguity Never Auto-Resolves ==========

def test_invariant_5_ambiguous_reference_asks_user():
    """
    UX INVARIANT 5: Ambiguity Never Auto-Resolves
    
    When ambiguity exists (2+ URLs in context):
    - Buddy must ask
    - Never choose silently
    - Never guess
    """
    clear_missions_log()
    
    # Create mission with URL 1
    response1 = run_message(
        "Extract emails from linkedin.com",
        session_id="test_inv5"
    )
    assert len(response1.missions_spawned) == 1
    
    time.sleep(0.1)
    clear_missions_log()
    
    # Create mission with URL 2 (context now has 2 URLs)
    response2 = run_message(
        "Extract names from github.com",
        session_id="test_inv5"
    )
    assert len(response2.missions_spawned) == 1
    
    time.sleep(0.1)
    clear_missions_log()
    
    # Try "extract from there" with ambiguous context
    response3 = run_message(
        "Extract titles from there",
        session_id="test_inv5"
    )
    
    # Should NOT create mission (ambiguous)
    assert len(response3.missions_spawned) == 0, "Should ask for clarification"
    assert count_missions() == 0, "No mission should be created"
    
    # Should ask for clarification
    summary_lower = response3.summary.lower()
    has_clarification = any(
        phrase in summary_lower
        for phrase in ["clarify", "specify", "which", "refer", "mean", "website"]
    )
    assert has_clarification, f"Should ask clarification but got: {response3.summary}"
    
    print("✓ Invariant 5: Ambiguous references trigger clarification")


def test_invariant_5_unambiguous_reference_works():
    """
    UX INVARIANT 5: Unambiguous references resolve without clarification
    
    When only one URL in context:
    - "Extract from there" should work
    - No clarification needed
    - Mission created
    """
    clear_missions_log()
    
    # First mission
    response1 = run_message(
        "Extract emails from linkedin.com",
        session_id="test_inv5_unambig"
    )
    assert len(response1.missions_spawned) == 1
    
    time.sleep(0.1)
    clear_missions_log()
    
    # Follow-up with unambiguous pronoun
    response2 = run_message(
        "Extract names from there",
        session_id="test_inv5_unambig"
    )
    
    # Should create mission (unambiguous)
    assert len(response2.missions_spawned) == 1, "Should resolve unambiguous reference"
    assert count_missions() == 1, "Mission should be created"
    
    # Should NOT ask for clarification
    summary_lower = response2.summary.lower()
    assert "clarify" not in summary_lower, "Should not ask for clarification"
    
    print("✓ Invariant 5: Unambiguous references resolve without clarification")


# ========== PHASE 3A.1 + 3A.2 REGRESSION GUARD ==========

def test_phase_3a1_regression():
    """
    Ensure Phase 3A.1 safety is still maintained.
    
    - No mission created without READY
    - No context bypass
    - All blocking still enforced
    """
    clear_missions_log()
    
    # Incomplete should be blocked
    response1 = run_message("Extract the emails")
    assert len(response1.missions_spawned) == 0
    assert count_missions() == 0
    
    # Complete should create mission
    response2 = run_message("Extract emails from linkedin.com")
    assert len(response2.missions_spawned) == 1
    assert count_missions() == 1
    
    print("✓ Phase 3A.1: Blocking still enforced")


def test_phase_3a2_regression():
    """
    Ensure Phase 3A.2 session context still works.
    
    - Context-aware resolution still works
    - Repeat still works
    - No new bypass paths added
    """
    clear_missions_log()
    
    # Create mission for context
    response1 = run_message(
        "Extract emails from linkedin.com",
        session_id="test_3a2_regress"
    )
    assert len(response1.missions_spawned) == 1
    
    time.sleep(0.1)
    clear_missions_log()
    
    # Repeat should still work
    response2 = run_message(
        "Do it again",
        session_id="test_3a2_regress"
    )
    assert len(response2.missions_spawned) == 1
    
    print("✓ Phase 3A.2: Session context still works")


# ========== RUN ALL INVARIANTS ==========

def run_all_ux_invariants():
    """Run all UX invariant tests."""
    print("\n" + "="*60)
    print("PHASE 3B: UX INVARIANT TESTS")
    print("="*60 + "\n")
    
    # Invariant 1: Never Ask Vague Questions
    print("Testing Invariant 1: Never Ask Vague Questions")
    test_invariant_1_clarification_mentions_missing_field()
    test_invariant_1_clarification_is_contextual()
    
    # Invariant 2: Actionable Clarifications
    print("\nTesting Invariant 2: Actionable Clarifications")
    test_invariant_2_clarification_has_example()
    test_invariant_2_clarification_is_direct()
    
    # Invariant 3: No Mission Creation
    print("\nTesting Invariant 3: No Mission Creation via Clarification")
    test_invariant_3_incomplete_never_creates_mission()
    
    # Invariant 4: READY Unchanged
    print("\nTesting Invariant 4: READY Behavior Unchanged")
    test_invariant_4_ready_creates_mission()
    test_invariant_4_repeat_still_works()
    
    # Invariant 5: No Auto-Resolution
    print("\nTesting Invariant 5: Ambiguity Never Auto-Resolves")
    test_invariant_5_ambiguous_reference_asks_user()
    test_invariant_5_unambiguous_reference_works()
    
    # Regression Guards
    print("\nRegression Guards:")
    test_phase_3a1_regression()
    test_phase_3a2_regression()
    
    print("\n" + "="*60)
    print("✅ ALL INVARIANTS PASSED")
    print("="*60 + "\n")


if __name__ == "__main__":
    run_all_ux_invariants()

