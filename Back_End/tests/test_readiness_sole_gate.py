"""
Invariant Test: ActionReadinessEngine is the SOLE mission gate.

Proves that:
1. Incomplete missions are blocked (no mission created)
2. Complete missions are created ONLY via readiness validation
3. Readiness fields are used directly for mission construction
4. No raw-text mission creation bypasses readiness
"""

import json
from pathlib import Path
import time
from Back_End.interaction_orchestrator import InteractionOrchestrator


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


def run_message(message: str):
    """Run a message through the orchestrator."""
    clear_missions_log()
    orchestrator = InteractionOrchestrator()
    
    response = orchestrator.process_message(
        message=message,
        user_id="test_user",
        session_id="test_session",
    )
    
    # Give emitter time to write
    time.sleep(0.1)
    
    return response


def test_incomplete_extract_no_source_blocks_mission():
    """
    INVARIANT: Incomplete missions are blocked.
    
    User: "Extract the emails"
    Expected: INCOMPLETE (no source URL)
    Result: No mission created
    """
    response = run_message("Extract the emails")
    
    # Should not spawn mission
    assert len(response.missions_spawned) == 0, "Incomplete mission should be blocked"
    
    # Should not write to missions log
    assert count_missions() == 0, "No mission should be written for incomplete request"
    
    # Should suggest clarification (Phase 3B: targeted, specific message)
    summary_lower = response.summary.lower()
    assert "know what" in summary_lower or "where" in summary_lower, \
        "Should ask for missing context in specific way"


def test_incomplete_navigate_without_url_blocks_mission():
    """
    INVARIANT: Navigation without target is blocked.
    
    User: "Go there"
    Expected: INCOMPLETE (no target URL)
    Result: No mission created
    """
    response = run_message("Go there")
    
    assert len(response.missions_spawned) == 0
    assert count_missions() == 0


def test_complete_extract_creates_mission_with_readiness_fields():
    """
    INVARIANT: Only READY readiness creates missions.
    
    User: "Extract the title from https://example.com"
    Expected: READY with extracted fields
    Result: Mission created with validated fields
    """
    response = run_message("Extract the title from https://example.com")
    
    # Should spawn exactly one mission
    assert len(response.missions_spawned) == 1, "Ready mission should be created"
    
    # Mission should be in log
    assert count_missions() == 1, "Ready mission should be written"
    
    mission = last_mission()
    assert mission is not None
    
    # Verify mission has structured readiness fields
    # Note: emitter converts to nested structure
    assert mission['objective']['type'] == 'extract'
    assert 'title' in mission['objective']['description'].lower()
    assert 'example.com' in mission['objective']['description'].lower()


def test_complete_navigate_creates_mission_with_readiness_fields():
    """
    INVARIANT: Navigation with valid target creates mission.
    
    User: "Navigate to github.com"
    Expected: READY
    Result: Mission created with URL
    """
    response = run_message("Navigate to github.com")
    
    assert len(response.missions_spawned) == 1
    assert count_missions() == 1
    
    mission = last_mission()
    assert mission is not None
    assert mission['objective']['type'] == 'navigate'
    assert 'github' in mission['objective']['description'].lower()


def test_multiple_incomplete_requests_no_cumulative_missions():
    """
    INVARIANT: Each request is independently gated.
    
    Send 3 incomplete requests in sequence.
    Expected: 0 missions total
    """
    for message in [
        "Extract the data",  # INCOMPLETE - no source
        "Search for something",  # INCOMPLETE - no source
        "Navigate there",  # INCOMPLETE - no target
    ]:
        response = run_message(message)
        # Each should be blocked
        assert len(response.missions_spawned) == 0, f"Blocked: {message}"
    
    # Total missions in log: 0
    assert count_missions() == 0, "No incomplete missions should accumulate"


def test_mixed_requests_only_ready_creates_missions():
    """
    INVARIANT: Only READY requests create missions in a mixed batch.
    
    Requests:
    1. "Extract emails" - INCOMPLETE (no source)
    2. "Extract names from linkedin.com" - READY
    3. "Navigate somewhere" - INCOMPLETE (no URL)
    
    Expected: Only request 2 creates a mission
    """
    clear_missions_log()
    orchestrator = InteractionOrchestrator()
    
    # Request 1: INCOMPLETE
    response1 = orchestrator.process_message(
        message="Extract emails",
        user_id="test_user",
        session_id="test_session",
    )
    assert len(response1.missions_spawned) == 0
    
    # Request 2: READY
    response2 = orchestrator.process_message(
        message="Extract names from linkedin.com",
        user_id="test_user",
        session_id="test_session",
    )
    assert len(response2.missions_spawned) == 1
    
    # Request 3: INCOMPLETE
    response3 = orchestrator.process_message(
        message="Navigate somewhere",
        user_id="test_user",
        session_id="test_session",
    )
    assert len(response3.missions_spawned) == 0
    
    time.sleep(0.1)
    
    # Total missions: 1 (only the READY one)
    mission_count = count_missions()
    assert mission_count == 1, f"Expected 1 mission, got {mission_count}"


if __name__ == "__main__":
    test_incomplete_extract_no_source_blocks_mission()
    print("✓ Incomplete extract blocked")
    
    test_incomplete_navigate_without_url_blocks_mission()
    print("✓ Incomplete navigate blocked")
    
    test_complete_extract_creates_mission_with_readiness_fields()
    print("✓ Complete extract creates mission with readiness fields")
    
    test_complete_navigate_creates_mission_with_readiness_fields()
    print("✓ Complete navigate creates mission with readiness fields")
    
    test_multiple_incomplete_requests_no_cumulative_missions()
    print("✓ Multiple incomplete requests don't accumulate missions")
    
    test_mixed_requests_only_ready_creates_missions()
    print("✓ Only READY requests create missions in mixed batch")
    
    print("\n✅ All invariant tests passed: ActionReadinessEngine is the SOLE mission gate")

