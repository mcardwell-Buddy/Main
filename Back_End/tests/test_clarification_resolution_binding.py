"""
Phase 4A: Clarification Resolution Binding Tests

Deterministic clarification resolution with no safety regressions.
"""

from Back_End.interaction_orchestrator import InteractionOrchestrator


# Global cache for orchestrator per session (Phase 3B pattern)
_orchestrator_cache = {}


def get_or_create_orchestrator(session_id: str) -> InteractionOrchestrator:
    if session_id not in _orchestrator_cache:
        _orchestrator_cache[session_id] = InteractionOrchestrator()
    return _orchestrator_cache[session_id]


def clear_orchestrator_cache():
    global _orchestrator_cache
    _orchestrator_cache = {}


def run_message(message: str, session_id: str):
    orchestrator = get_or_create_orchestrator(session_id)
    return orchestrator.process_message(message, session_id=session_id)


def get_session_context(session_id: str):
    orchestrator = get_or_create_orchestrator(session_id)
    return orchestrator._session_context_manager.get_or_create(session_id)


def test_resolves_missing_source_url():
    clear_orchestrator_cache()
    session_id = "clarify_missing_source"

    response1 = run_message("Extract the title", session_id)
    assert len(response1.missions_spawned) == 0

    context = get_session_context(session_id)
    pending = context.get_pending_clarification()
    assert pending is not None
    assert pending.missing_field == "source_url"

    response2 = run_message("example.com", session_id)
    assert len(response2.missions_spawned) == 1
    assert "Mission ready" in response2.summary


def test_resolves_option_selection():
    clear_orchestrator_cache()
    session_id = "clarify_option_selection"

    # Seed a recent source URL
    response1 = run_message("Navigate to example.com", session_id)
    assert len(response1.missions_spawned) == 1

    # Trigger clarification
    response2 = run_message("Extract emails", session_id)
    assert len(response2.missions_spawned) == 0

    context = get_session_context(session_id)
    pending = context.get_pending_clarification()
    assert pending is not None
    assert pending.missing_field == "source_url"
    assert pending.options and len(pending.options) >= 1

    selected_option = pending.options[0]
    response3 = run_message(selected_option, session_id)
    assert len(response3.missions_spawned) == 1
    assert "Mission ready" in response3.summary


def test_ambiguous_reply_does_not_resolve():
    clear_orchestrator_cache()
    session_id = "clarify_ambiguous_reply"

    # Seed multiple recent URLs
    run_message("Navigate to example.com", session_id)
    run_message("Navigate to example.org", session_id)

    response1 = run_message("Extract titles", session_id)
    assert len(response1.missions_spawned) == 0

    context = get_session_context(session_id)
    pending = context.get_pending_clarification()
    assert pending is not None
    assert pending.missing_field == "source_url"
    assert pending.options and len(pending.options) >= 2

    response2 = run_message("that one", session_id)
    assert len(response2.missions_spawned) == 0

    pending_after = context.get_pending_clarification()
    assert pending_after is not None
    assert pending_after.missing_field == "source_url"


def test_yes_does_not_resolve_clarification():
    clear_orchestrator_cache()
    session_id = "clarify_yes_no_resolve"

    response1 = run_message("Extract the title", session_id)
    assert len(response1.missions_spawned) == 0

    response2 = run_message("yes", session_id)
    assert len(response2.missions_spawned) == 0

    context = get_session_context(session_id)
    pending = context.get_pending_clarification()
    assert pending is not None
    assert pending.missing_field == "source_url"


def test_new_full_command_clears_pending_clarification():
    clear_orchestrator_cache()
    session_id = "clarify_new_command"

    response1 = run_message("Extract the title", session_id)
    assert len(response1.missions_spawned) == 0

    response2 = run_message("Navigate to example.com", session_id)
    assert len(response2.missions_spawned) == 1

    context = get_session_context(session_id)
    assert context.get_pending_clarification() is None


def test_regression_guard_no_mission_without_ready():
    clear_orchestrator_cache()
    session_id = "clarify_regression_no_ready"

    response1 = run_message("Extract from linkedin.com", session_id)
    assert len(response1.missions_spawned) == 0


if __name__ == "__main__":
    test_resolves_missing_source_url()
    test_resolves_option_selection()
    test_ambiguous_reply_does_not_resolve()
    test_yes_does_not_resolve_clarification()
    test_new_full_command_clears_pending_clarification()
    test_regression_guard_no_mission_without_ready()
    print("✅ Phase 4A clarification resolution binding tests passed")

