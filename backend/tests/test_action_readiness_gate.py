import pytest

from backend.interaction_orchestrator import InteractionOrchestrator


def run_message(message: str, context=None):
    orchestrator = InteractionOrchestrator()
    return orchestrator.process_message(
        message=message,
        session_id="test_session",
        user_id="test_user",
        context=context,
    )


def test_block_incomplete_extract_missing_source():
    response = run_message("Extract the title from")
    assert response.missions_spawned == []
    assert response.summary == "I'm missing some required details before I can do that."


def test_block_incomplete_get_company_details():
    response = run_message("Get company details")
    assert response.missions_spawned == []
    assert response.summary == "I'm missing some required details before I can do that."


def test_block_incomplete_go_there_no_session_url():
    response = run_message("Go there", context={})
    assert response.missions_spawned == []


def test_ready_extract_with_url_creates_mission():
    response = run_message("Extract the title from https://example.com")
    assert len(response.missions_spawned) == 1


def test_ready_navigate_creates_mission():
    response = run_message("Go to example.com")
    assert len(response.missions_spawned) == 1
