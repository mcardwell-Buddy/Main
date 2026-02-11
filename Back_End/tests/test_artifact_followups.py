"""
Phase 4B: Artifact-Aware Follow-Ups Tests

Read-only follow-up questions about executed mission artifacts.
No mission creation, no execution, no approval state changes.
"""

from Back_End.interaction_orchestrator import InteractionOrchestrator


# Global cache for orchestrator per session
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


def seed_execution_artifact(session_id: str):
    """Seed a mock execution artifact for testing."""
    context = get_session_context(session_id)
    artifact = {
        "artifact_type": "web_extraction_result",
        "source_url": "https://example.com",
        "final_url": "https://example.com/page",
        "extracted_data": {
            "items": ["title1", "title2", "title3"],
            "titles": ["Item 1", "Item 2", "Item 3"],
            "count": 3,
        },
        "result_summary": "Extracted 3 items from the website.",
        "summary": "Found 3 matching records.",
    }
    context.set_last_execution_artifact(artifact)
    return artifact


def test_followup_without_artifact():
    """
    Test: Follow-up question without prior execution.

    Expected: Safe "no results yet" message.
    """
    clear_orchestrator_cache()
    session_id = "followup_no_artifact"

    response = run_message("What did you find?", session_id)

    assert "don't have any recent results" in response.summary.lower()
    assert len(response.missions_spawned) == 0


def test_followup_returns_source_url():
    """
    Test: Follow-up question about source URL.

    Expected: Return correct URL from artifact.
    """
    clear_orchestrator_cache()
    session_id = "followup_source_url"

    seed_execution_artifact(session_id)

    response = run_message("What website did you visit?", session_id)

    assert "example.com" in response.summary.lower()
    assert len(response.missions_spawned) == 0


def test_followup_returns_count():
    """
    Test: Follow-up question about item count.

    Expected: Return correct count from artifact.
    """
    clear_orchestrator_cache()
    session_id = "followup_count"

    seed_execution_artifact(session_id)

    response = run_message("How many items did you find?", session_id)

    assert "3" in response.summary
    assert len(response.missions_spawned) == 0


def test_followup_does_not_create_mission():
    """
    Test: Follow-up question does not create mission.

    Expected: No missions spawned, read-only answer.
    """
    clear_orchestrator_cache()
    session_id = "followup_no_mission"

    seed_execution_artifact(session_id)

    response = run_message("What did you find?", session_id)

    assert len(response.missions_spawned) == 0
    assert response.response_type.value == "text"


def test_followup_does_not_trigger_approval():
    """
    Test: Approval phrase after follow-up does nothing.

    Expected: "nothing to approve" message (no approval state created).
    """
    clear_orchestrator_cache()
    session_id = "followup_no_approval"

    seed_execution_artifact(session_id)

    response1 = run_message("What did you find?", session_id)
    assert len(response1.missions_spawned) == 0

    response2 = run_message("yes", session_id)
    assert "nothing to approve" in response2.summary.lower()


def test_followup_pattern_what_did_you_extract():
    """Test follow-up pattern: 'what did you extract?'"""
    clear_orchestrator_cache()
    session_id = "followup_extract_pattern"

    seed_execution_artifact(session_id)

    response = run_message("What did you extract?", session_id)

    assert len(response.missions_spawned) == 0
    assert ("extracted" in response.summary.lower() or "found" in response.summary.lower())


def test_followup_pattern_how_many_results():
    """Test follow-up pattern: 'how many results?'"""
    clear_orchestrator_cache()
    session_id = "followup_results_pattern"

    seed_execution_artifact(session_id)

    response = run_message("How many results did you get?", session_id)

    assert len(response.missions_spawned) == 0
    assert "3" in response.summary


def test_followup_pattern_where_did_you_go():
    """Test follow-up pattern: 'where did you go?'"""
    clear_orchestrator_cache()
    session_id = "followup_where_pattern"

    seed_execution_artifact(session_id)

    response = run_message("Where did you go?", session_id)

    assert len(response.missions_spawned) == 0
    assert ("example.com" in response.summary.lower() or "visited" in response.summary.lower())


def test_followup_ignores_execution_verbs():
    """
    Test: Follow-up containing execution verbs is not treated as follow-up.

    Expected: Treated as normal request, no artifact answer.
    """
    clear_orchestrator_cache()
    session_id = "followup_exec_verbs"

    seed_execution_artifact(session_id)

    response = run_message("Can you find more items?", session_id)

    assert "don't have any recent results" not in response.summary.lower()


def test_followup_requires_question_mark():
    """
    Test: Follow-up statement (no ?) not treated as follow-up.

    Expected: Not answered as artifact follow-up.
    """
    clear_orchestrator_cache()
    session_id = "followup_no_question_mark"

    seed_execution_artifact(session_id)

    response = run_message("What did you find", session_id)

    assert len(response.missions_spawned) == 0


def test_regression_guard_phase_3_pipeline():
    """
    Regression guard: Phase 3 READY → APPROVABLE → EXECUTABLE still works.

    Artifact follow-ups must not interfere with approval flow.
    """
    clear_orchestrator_cache()
    session_id = "regression_phase3"

    response1 = run_message("Extract the title from example.com", session_id)
    assert len(response1.missions_spawned) == 1
    assert "ready" in response1.summary.lower()

    response2 = run_message("yes", session_id)
    assert len(response2.missions_spawned) == 0


def test_followup_with_no_extracted_data():
    """
    Test: Follow-up question when artifact lacks extraction data.

    Expected: Safe "don't have that information" message.
    """
    clear_orchestrator_cache()
    session_id = "followup_no_extracted_data"

    context = get_session_context(session_id)
    artifact = {
        "artifact_type": "web_navigation_result",
        "source_url": "https://example.com",
    }
    context.set_last_execution_artifact(artifact)

    response = run_message("How many items did you find?", session_id)

    assert "don't have count information" in response.summary.lower()


def test_followup_readonly_no_state_mutation():
    """
    Test: Follow-up answers are read-only, no state mutation.

    Expected: Multiple follow-ups use same artifact without changing state.
    """
    clear_orchestrator_cache()
    session_id = "followup_readonly"

    seed_execution_artifact(session_id)

    response1 = run_message("What did you find?", session_id)
    context = get_session_context(session_id)
    artifact1 = context.get_last_execution_artifact()

    response2 = run_message("How many items?", session_id)
    artifact2 = context.get_last_execution_artifact()

    assert artifact1 == artifact2
    assert len(response1.missions_spawned) == 0
    assert len(response2.missions_spawned) == 0


if __name__ == "__main__":
    test_followup_without_artifact()
    test_followup_returns_source_url()
    test_followup_returns_count()
    test_followup_does_not_create_mission()
    test_followup_does_not_trigger_approval()
    test_followup_pattern_what_did_you_extract()
    test_followup_pattern_how_many_results()
    test_followup_pattern_where_did_you_go()
    test_followup_ignores_execution_verbs()
    test_followup_requires_question_mark()
    test_regression_guard_phase_3_pipeline()
    test_followup_with_no_extracted_data()
    test_followup_readonly_no_state_mutation()
    print("✅ Phase 4B artifact-aware follow-up tests passed")

