import os
import pytest
from fastapi.testclient import TestClient
from Back_End.main import app

RUN_E2E = os.getenv("RUN_E2E", "") == "1"
RUN_SELF_IMPROVE_APPLY = os.getenv("RUN_SELF_IMPROVE_APPLY", "") == "1"
RUN_VISION_E2E = os.getenv("RUN_VISION_E2E", "") == "1"


@pytest.mark.skipif(not RUN_E2E, reason="E2E tests disabled. Set RUN_E2E=1 to enable.")
def test_self_improve_confirmation_flow():
    client = TestClient(app)
    payload = {
        "file_path": "backend/code_analyzer.py",
        "improvement": "add safety and error handling for reliability",
        "require_confirmation": True,
        "confirmed": False,
    }
    resp = client.post("/self-improve/execute", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("success") is False
    result = data.get("result", {})
    assert result.get("needs_confirmation") is True
    proposal = result.get("proposal", {})
    assert "diff" in proposal


@pytest.mark.skipif(not (RUN_E2E and RUN_SELF_IMPROVE_APPLY), reason="Apply flow disabled. Set RUN_E2E=1 and RUN_SELF_IMPROVE_APPLY=1.")
def test_self_improve_confirm_apply_flow():
    client = TestClient(app)
    payload = {
        "file_path": "backend/code_analyzer.py",
        "improvement": "add safety and error handling for reliability",
        "require_confirmation": False,
        "confirmed": True,
    }
    resp = client.post("/self-improve/execute", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    result = data.get("result", {})
    assert result.get("ready_for_approval") is True
    improved_code = result.get("improved_code")
    assert improved_code

    approve = {
        "file_path": "backend/code_analyzer.py",
        "improved_code": improved_code,
        "approved": True,
    }
    approve_resp = client.post("/self-improve/approve", json=approve)
    assert approve_resp.status_code == 200
    approve_data = approve_resp.json()
    assert approve_data.get("success") is True


@pytest.mark.skipif(not (RUN_E2E and RUN_VISION_E2E), reason="Vision/Arms E2E disabled. Set RUN_E2E=1 and RUN_VISION_E2E=1.")
def test_vision_arms_flow():
    import selenium  # noqa: F401
    # Placeholder: requires Selenium driver, target site, and environment setup.
    # Implement test to navigate, inspect, fill, and submit when configured.
    assert True

