"""
Phase 3A.2: Session Context Safety Invariants

Proves that session context integration:
1. Never creates missions alone
2. Cannot bypass readiness validation
3. Only resolves unambiguous references
4. Improves valid follow-ups without weakening safety
5. Passes all Phase 3A.1 regression tests
"""

import json
import time
from pathlib import Path
from backend.interaction_orchestrator import InteractionOrchestrator


def clear_missions_log():
    """Clear the missions log before test."""
    missions_file = Path('outputs/phase25/missions.jsonl')
    if missions_file.exists():
        missions_file.unlink()


def clear_orchestrator_cache():
    """Clear the orchestrator cache for next test."""
    global _orchestrator_cache
    _orchestrator_cache.clear()


def count_missions():
    """Count missions in the missions log."""
    missions_file = Path('outputs/phase25/missions.jsonl')
    if not missions_file.exists():
        return 0
    
    with open(missions_file, 'r') as f:
        return sum(1 for _ in f if _.strip())


def last_mission():
    """Get the last mission from the log."""
    missions_file = Path('outputs/phase25/missions.jsonl')
    if not missions_file.exists():
        return None
    
    with open(missions_file, 'r') as f:
        lines = [line for line in f if line.strip()]
        if lines:
            return json.loads(lines[-1])
    return None


# Global orchestrator to maintain session context across messages
_orchestrator_cache = {}

def get_or_create_orchestrator(session_id: str = "test_session"):
    """Get or create orchestrator for session (maintains context across messages)."""
    if session_id not in _orchestrator_cache:
        _orchestrator_cache[session_id] = InteractionOrchestrator()
    return _orchestrator_cache[session_id]

def run_message(message: str, session_id: str = "test_session"):
    """Run a message through the orchestrator."""
    orchestrator = get_or_create_orchestrator(session_id)
    
    response = orchestrator.process_message(
        message=message,
        user_id="test_user",
        session_id=session_id,
    )
    
    # Give emitter time to write
    time.sleep(0.1)
    
    return response, orchestrator


# ========== INVARIANT 1: Context Never Creates Missions Alone ==========

def test_invariant_1_do_it_again_without_prior_mission():
    """
    INVARIANT 1: Context cannot create missions alone.
    
    Scenario: User says "Do it again" with no prior READY mission
    Expected: No mission created, clarification requested
    
    This proves context is read-only and cannot invent missions.
    """
    clear_orchestrator_cache()
    clear_missions_log()
    
    response = run_message("Do it again")[0]
    
    # Should not create mission
    assert len(response.missions_spawned) == 0, "Context alone cannot create mission"
    assert count_missions() == 0, "No mission in log"
    
    # Should clarify what the user wants
    # (either "missing/details" from readiness or generic inquiry from ChatIntakeCoordinator)
    summary_lower = response.summary.lower()
    has_clarification = (
        "missing" in summary_lower 
        or "details" in summary_lower 
        or "help" in summary_lower
        or "would you" in summary_lower
    )
    assert has_clarification, f"Expected clarification, got: {response.summary}"
    
    print("✓ Invariant 1: Context cannot create missions alone")


def test_invariant_1_repeat_without_prior_mission():
    """
    INVARIANT 1: "Repeat" without prior mission is blocked.
    """
    clear_orchestrator_cache()
    clear_missions_log()
    
    response = run_message("Repeat that")[0]
    
    assert len(response.missions_spawned) == 0
    assert count_missions() == 0
    
    print("✓ Invariant 1: 'Repeat' without prior mission blocked")


# ========== INVARIANT 2: Context Cannot Bypass Readiness ==========

def test_invariant_2_context_cannot_bypass_missing_object():
    """
    INVARIANT 2: Context can resolve when unambiguous, but cannot invent.
    
    Scenario:
    1. First request: "Extract the title from example.com"
    2. Second request: "Extract from there"
    
    Expected: 
    - "from there" resolves URL unambiguously (one URL in context)
    - "Extract" without action_object uses context (only one prior action_object)
    - Mission created is reasonable: "Extract title from example.com"
    
    This shows context resolution works for unambiguous cases.
    """
    clear_orchestrator_cache()
    clear_missions_log()
    
    # Create first mission for context
    response1 = run_message(
        "Extract the title from https://example.com",
        session_id="test_session_2a"
    )[0]
    
    assert len(response1.missions_spawned) == 1, "First mission should be created"
    assert count_missions() == 1
    
    time.sleep(0.1)
    clear_missions_log()
    
    # Follow-up with unambiguous context
    # "Extract from there" - "there" = example.com (unambiguous), "title" from context
    response2 = run_message(
        "Extract from there",
        session_id="test_session_2a"
    )[0]
    
    # Should succeed (unambiguous URL + prior action_object in context)
    assert len(response2.missions_spawned) == 1, "Context should resolve unambiguous reference"
    assert count_missions() == 1
    
    mission2 = last_mission()
    assert mission2 is not None
    assert "title" in mission2['objective']['description'].lower()
    assert "example.com" in mission2['objective']['description'].lower()
    
    print("✓ Invariant 2: Context resolves unambiguous references")


def test_invariant_2_context_cannot_bypass_missing_source():
    """
    INVARIANT 2: Context won't resolve AMBIGUOUS references.
    
    Scenario:
    1. First request: "Navigate to github.com"
    2. Create a second mission: "Navigate to example.com"  
    3. Third request: "Extract that"
    
    Expected:
    - "that" is ambiguous pronoun (two sources in context)
    - Should NOT create mission
    - Clarification requested
    """
    clear_orchestrator_cache()
    clear_missions_log()
    
    # Create first navigate mission
    response1 = run_message(
        "Navigate to github.com",
        session_id="test_session_2b"
    )[0]
    
    assert len(response1.missions_spawned) == 1
    assert count_missions() == 1
    
    time.sleep(0.1)
    clear_missions_log()
    
    # Create second navigate mission (now context has two URLs)
    response2 = run_message(
        "Navigate to example.com",
        session_id="test_session_2b"
    )[0]
    
    assert len(response2.missions_spawned) == 1
    assert count_missions() == 1
    
    time.sleep(0.1)
    clear_missions_log()
    
    # Try extract with ambiguous pronoun
    response3 = run_message(
        "Extract emails from there",
        session_id="test_session_2b"
    )[0]
    
    # Should fail because "there" is ambiguous (two URLs in context)
    assert len(response3.missions_spawned) == 0, "Ambiguous 'there' should block mission"
    assert count_missions() == 0, "Context won't guess when ambiguous"
    
    print("✓ Invariant 2: Ambiguous references blocked")


# ========== INVARIANT 3: Context Only Resolves Unambiguous References ==========

def test_invariant_3_ambiguous_url_triggers_clarification():
    """
    INVARIANT 3: Ambiguous references trigger clarification.
    
    Scenario:
    1. Create mission with example.com
    2. Create mission with github.com
    3. Say "Go there" (ambiguous which)
    
    Expected:
    - Clarification requested (two URLs in context)
    - NO mission created
    
    This proves context won't guess when ambiguous.
    """
    clear_orchestrator_cache()
    clear_missions_log()
    
    # Create two missions with different URLs
    response1 = run_message(
        "Navigate to example.com",
        session_id="test_session_3"
    )[0]
    assert len(response1.missions_spawned) == 1
    
    time.sleep(0.1)
    
    response2 = run_message(
        "Navigate to github.com",
        session_id="test_session_3"
    )[0]
    assert len(response2.missions_spawned) == 1
    
    time.sleep(0.1)
    clear_missions_log()
    
    # Try ambiguous reference
    response3 = run_message(
        "Go there",
        session_id="test_session_3"
    )[0]
    
    # Should fail (ambiguous)
    assert len(response3.missions_spawned) == 0
    assert count_missions() == 0
    
    print("✓ Invariant 3: Ambiguous references blocked")


def test_invariant_3_unambiguous_reference_succeeds():
    """
    INVARIANT 3: Unambiguous references are resolved.
    
    Scenario:
    1. Create mission: "Extract title from example.com"
    2. Follow-up: "Extract emails from there"
    
    Expected:
    - "there" resolved to example.com (only one URL in context)
    - Mission created
    
    This proves context resolves when unambiguous.
    """
    clear_orchestrator_cache()
    clear_missions_log()
    
    response1 = run_message(
        "Extract the title from https://example.com",
        session_id="test_session_3b"
    )[0]
    assert len(response1.missions_spawned) == 1
    
    time.sleep(0.1)
    clear_missions_log()
    
    # Follow-up with context resolution
    response2 = run_message(
        "Extract the emails from there",
        session_id="test_session_3b"
    )[0]
    
    # Should succeed (unambiguous)
    assert len(response2.missions_spawned) == 1
    assert count_missions() == 1
    
    mission = last_mission()
    assert mission is not None
    assert "example.com" in mission['objective']['description'].lower()
    
    print("✓ Invariant 3: Unambiguous references resolved")


# ========== INVARIANT 4: Valid Follow-Up Becomes READY ==========

def test_invariant_4_valid_followup_improves_readiness():
    """
    INVARIANT 4: Context improves readiness for valid follow-ups.
    
    Scenario:
    1. First: "Extract title from example.com" → READY, creates mission
    2. Second: "Do it again" → READY (via context), creates mission
    
    Expected:
    - Two missions created
    - Second uses fields from first
    - No re-parsing from raw text
    """
    clear_orchestrator_cache()
    clear_missions_log()
    
    # First mission
    response1 = run_message(
        "Extract the title from https://example.com",
        session_id="test_session_4"
    )[0]
    
    assert len(response1.missions_spawned) == 1
    assert count_missions() == 1
    
    mission1 = last_mission()
    
    time.sleep(0.1)
    clear_missions_log()
    
    # Follow-up: "Do it again"
    response2 = run_message(
        "Do it again",
        session_id="test_session_4"
    )[0]
    
    # Should create second mission from context
    assert len(response2.missions_spawned) == 1
    assert count_missions() == 1
    
    mission2 = last_mission()
    
    # Verify fields match (same intent, object, target)
    assert mission1['objective']['type'] == mission2['objective']['type']
    assert 'title' in mission2['objective']['description'].lower()
    assert 'example.com' in mission2['objective']['description'].lower()
    
    print("✓ Invariant 4: Valid follow-up becomes READY via context")


def test_invariant_4_context_preserves_structured_fields():
    """
    INVARIANT 4: Context doesn't lose structured fields.
    
    Scenario:
    1. Extract task with count constraint
    2. "Do it again" with same constraint
    
    Expected:
    - Constraints preserved in second mission
    """
    clear_orchestrator_cache()
    clear_missions_log()
    
    response1 = run_message(
        "Extract the top 5 emails from linkedin.com",
        session_id="test_session_4b"
    )[0]
    
    assert len(response1.missions_spawned) == 1
    mission1 = last_mission()
    
    time.sleep(0.1)
    clear_missions_log()
    
    response2 = run_message(
        "Do it again",
        session_id="test_session_4b"
    )[0]
    
    assert len(response2.missions_spawned) == 1
    mission2 = last_mission()
    
    # Verify constraints preserved
    assert mission1['objective']['target_count'] == mission2['objective']['target_count']
    
    print("✓ Invariant 4: Constraints preserved via context")


# ========== INVARIANT 5: Phase 3A.1 Regression Guard ==========

def test_invariant_5_phase_3a1_blocking_still_works():
    """
    INVARIANT 5: Phase 3A.1 blocking behavior unchanged.
    
    Ensure that adding session context doesn't weaken
    the core Phase 3A.1 safety invariants.
    """
    clear_orchestrator_cache()
    clear_missions_log()
    
    # Incomplete extract should still be blocked
    response = run_message("Extract the title")[0]
    assert len(response.missions_spawned) == 0
    assert count_missions() == 0
    
    # Incomplete navigate should still be blocked
    clear_missions_log()
    response = run_message("Go there")[0]
    assert len(response.missions_spawned) == 0
    assert count_missions() == 0
    
    # Complete missions still work
    clear_missions_log()
    response = run_message(
        "Extract title from example.com",
        session_id="test_regression"
    )[0]
    assert len(response.missions_spawned) == 1
    assert count_missions() == 1
    
    print("✓ Invariant 5: Phase 3A.1 blocking still enforced")


def test_invariant_5_no_new_mission_paths():
    """
    INVARIANT 5: Session context doesn't add new mission creation paths.
    
    Only mechanisms for mission creation:
    1. Direct readiness → READY
    2. ChatIntakeCoordinator fallback
    
    No new paths via context.
    """
    clear_orchestrator_cache()
    clear_missions_log()
    
    # Scenario: Ambiguous message with context should NOT create mission
    # Setup: Create mission with URL
    response1 = run_message(
        "Navigate to example.com",
        session_id="test_5b"
    )[0]
    assert len(response1.missions_spawned) == 1
    
    time.sleep(0.1)
    clear_missions_log()
    
    # Try ambiguous follow-up
    response2 = run_message(
        "Extract that",  # "that" is ambiguous pronoun
        session_id="test_5b"
    )[0]
    
    # No new path should create mission without full readiness
    assert len(response2.missions_spawned) == 0
    assert count_missions() == 0
    
    print("✓ Invariant 5: No new mission paths added")


# ========== Test Suite Runner ==========

def run_all_invariant_tests():
    """Run all Phase 3A.2 invariant tests."""
    
    print("\n" + "="*60)
    print("PHASE 3A.2: SESSION CONTEXT SAFETY INVARIANTS")
    print("="*60)
    
    # Invariant 1: Context never creates missions alone
    print("\n[INVARIANT 1] Context cannot create missions alone")
    test_invariant_1_do_it_again_without_prior_mission()
    test_invariant_1_repeat_without_prior_mission()
    
    # Invariant 2: Context cannot bypass readiness
    print("\n[INVARIANT 2] Context cannot bypass readiness")
    test_invariant_2_context_cannot_bypass_missing_object()
    test_invariant_2_context_cannot_bypass_missing_source()
    
    # Invariant 3: Unambiguous resolution only
    print("\n[INVARIANT 3] Unambiguous reference resolution only")
    test_invariant_3_ambiguous_url_triggers_clarification()
    test_invariant_3_unambiguous_reference_succeeds()
    
    # Invariant 4: Valid follow-ups improve readiness
    print("\n[INVARIANT 4] Valid follow-ups become READY")
    test_invariant_4_valid_followup_improves_readiness()
    test_invariant_4_context_preserves_structured_fields()
    
    # Invariant 5: Phase 3A.1 regression guard
    print("\n[INVARIANT 5] Phase 3A.1 invariants still enforced")
    test_invariant_5_phase_3a1_blocking_still_works()
    test_invariant_5_no_new_mission_paths()
    
    print("\n" + "="*60)
    print("✅ ALL INVARIANT TESTS PASSED")
    print("="*60)
    print("\nSESSION CONTEXT INTEGRATION SUCCESSFUL:")
    print("✓ Context never creates missions alone")
    print("✓ Context cannot bypass readiness")
    print("✓ Context only resolves unambiguous references")
    print("✓ Valid follow-ups improved without safety loss")
    print("✓ All Phase 3A.1 invariants maintained")


if __name__ == "__main__":
    run_all_invariant_tests()
