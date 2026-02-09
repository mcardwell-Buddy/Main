"""
Phase 4 Step 2: Expectation Delta Evaluation - Validation Tests

Tests that expectation delta evaluates alignment between mission outcomes
and user expectations without changing execution behavior.

Test Requirements:
1. Test aligned outcomes (target met)
2. Test misaligned outcomes (target missed, failures)
3. Test unclear outcomes (ambiguous results)
4. Verify whiteboard displays expectation delta
5. Verify signal includes mission_thread_id
"""

import os
import uuid
import pytest
import json
from datetime import datetime
from typing import Optional

from backend.evaluation.expectation_delta_evaluator import ExpectationDeltaEvaluator
from backend.mission_control.mission_contract import MissionContract
from backend.mission_control.mission_registry import MissionRegistry


@pytest.fixture
def temp_signal_file(tmp_path):
    """Create temporary signal file for testing."""
    signal_file = tmp_path / "learning_signals.jsonl"
    return signal_file


@pytest.fixture
def evaluator(temp_signal_file):
    """Create ExpectationDeltaEvaluator with temp file."""
    return ExpectationDeltaEvaluator(signals_file=temp_signal_file)


def test_aligned_outcome_target_met(evaluator, temp_signal_file):
    """Test 1: Aligned outcome - target met."""
    mission_id = str(uuid.uuid4())
    thread_id = str(uuid.uuid4())
    
    objective = {
        "type": "data_collection",
        "description": "Collect 50 quotes",
        "target": 50,
        "required_fields": ["text", "author"]
    }
    
    outcome = {
        "status": "completed",
        "items_collected": 50,
        "reason": "target_reached"
    }
    
    signal = evaluator.evaluate(
        mission_id=mission_id,
        objective=objective,
        outcome_summary=outcome,
        mission_thread_id=thread_id
    )
    
    # Verify alignment
    assert signal["alignment"] == "aligned"
    assert signal["confidence"] >= 0.8
    assert "met target" in signal["reason"].lower()
    
    # Verify signal structure
    assert signal["signal_type"] == "expectation_delta"
    assert signal["mission_id"] == mission_id
    assert signal["mission_thread_id"] == thread_id
    assert "timestamp" in signal
    
    # Verify persisted
    with open(temp_signal_file, "r") as f:
        persisted = json.loads(f.read())
    
    assert persisted["alignment"] == "aligned"
    assert persisted["mission_id"] == mission_id


def test_aligned_outcome_no_target(evaluator, temp_signal_file):
    """Test 2: Aligned outcome - no explicit target, items collected."""
    mission_id = str(uuid.uuid4())
    
    objective = {
        "type": "data_collection",
        "description": "Collect quotes",
        "target": None,
        "required_fields": ["text"]
    }
    
    outcome = {
        "status": "completed",
        "items_collected": 25,
        "reason": "execution_completed"
    }
    
    signal = evaluator.evaluate(
        mission_id=mission_id,
        objective=objective,
        outcome_summary=outcome
    )
    
    assert signal["alignment"] == "aligned"
    assert signal["confidence"] >= 0.6
    assert "no specific target" in signal["reason"].lower()


def test_misaligned_below_target(evaluator, temp_signal_file):
    """Test 3: Misaligned outcome - below target."""
    mission_id = str(uuid.uuid4())
    
    objective = {
        "type": "data_collection",
        "description": "Collect 100 items",
        "target": 100,
        "required_fields": ["title"]
    }
    
    outcome = {
        "status": "completed",
        "items_collected": 30,
        "reason": "execution_completed"
    }
    
    signal = evaluator.evaluate(
        mission_id=mission_id,
        objective=objective,
        outcome_summary=outcome
    )
    
    assert signal["alignment"] == "misaligned"
    assert signal["confidence"] >= 0.6
    assert "below target" in signal["reason"].lower()


def test_misaligned_zero_items(evaluator, temp_signal_file):
    """Test 4: Misaligned outcome - completed but zero items."""
    mission_id = str(uuid.uuid4())
    
    objective = {
        "type": "data_collection",
        "description": "Collect data",
        "target": 10,
        "required_fields": ["data"]
    }
    
    outcome = {
        "status": "completed",
        "items_collected": 0,
        "reason": "execution_completed"
    }
    
    signal = evaluator.evaluate(
        mission_id=mission_id,
        objective=objective,
        outcome_summary=outcome
    )
    
    assert signal["alignment"] == "misaligned"
    assert signal["confidence"] >= 0.7
    assert "no data collected" in signal["reason"].lower()


def test_misaligned_failed_no_progress(evaluator, temp_signal_file):
    """Test 5: Misaligned outcome - mission failed."""
    mission_id = str(uuid.uuid4())
    
    objective = {
        "type": "data_collection",
        "description": "Scrape products",
        "target": 50,
        "required_fields": ["name", "price"]
    }
    
    outcome = {
        "status": "failed",
        "items_collected": 0,
        "reason": "no_progress"
    }
    
    signal = evaluator.evaluate(
        mission_id=mission_id,
        objective=objective,
        outcome_summary=outcome
    )
    
    assert signal["alignment"] == "misaligned"
    assert signal["confidence"] >= 0.8
    assert "no progress" in signal["reason"].lower()


def test_misaligned_aborted_timeout(evaluator, temp_signal_file):
    """Test 6: Misaligned outcome - mission aborted due to timeout."""
    mission_id = str(uuid.uuid4())
    
    objective = {
        "type": "data_collection",
        "description": "Collect articles",
        "target": 100,
        "required_fields": ["title", "content"]
    }
    
    outcome = {
        "status": "aborted",
        "items_collected": 20,
        "reason": "max_duration_exceeded"
    }
    
    signal = evaluator.evaluate(
        mission_id=mission_id,
        objective=objective,
        outcome_summary=outcome
    )
    
    assert signal["alignment"] == "misaligned"
    assert signal["confidence"] >= 0.5  # Lower confidence for timeout
    assert "timeout" in signal["reason"].lower()


def test_unclear_active_mission(evaluator, temp_signal_file):
    """Test 7: Unclear outcome - mission still active (premature evaluation)."""
    mission_id = str(uuid.uuid4())
    
    objective = {
        "type": "data_collection",
        "description": "Collect data",
        "target": 50,
        "required_fields": ["data"]
    }
    
    outcome = {
        "status": "active",
        "items_collected": 10,
        "reason": "in_progress"
    }
    
    signal = evaluator.evaluate(
        mission_id=mission_id,
        objective=objective,
        outcome_summary=outcome
    )
    
    assert signal["alignment"] == "unclear"
    assert signal["confidence"] <= 0.5
    assert "premature" in signal["reason"].lower()


def test_thread_id_propagation(evaluator, temp_signal_file):
    """Test 8: Verify mission_thread_id propagates to signal."""
    mission_id = str(uuid.uuid4())
    thread_id = str(uuid.uuid4())
    
    objective = {
        "type": "data_collection",
        "description": "Test mission",
        "target": 10,
        "required_fields": ["data"]
    }
    
    outcome = {
        "status": "completed",
        "items_collected": 10,
        "reason": "target_reached"
    }
    
    signal = evaluator.evaluate(
        mission_id=mission_id,
        objective=objective,
        outcome_summary=outcome,
        mission_thread_id=thread_id
    )
    
    assert signal["mission_thread_id"] == thread_id
    
    # Verify persisted with thread_id
    with open(temp_signal_file, "r") as f:
        persisted = json.loads(f.read())
    
    assert persisted["mission_thread_id"] == thread_id


def test_whiteboard_displays_expectation_delta(tmp_path):
    """Test 9: Verify whiteboard displays expectation delta."""
    # Setup temp files
    missions_file = tmp_path / "missions.jsonl"
    signals_file = tmp_path / "learning_signals.jsonl"
    # Set environment variables BEFORE importing whiteboard
    os.environ["MISSIONS_FILE"] = str(missions_file)
    os.environ["LEARNING_SIGNALS_FILE"] = str(signals_file)
    
    # Import after setting env vars (module-level constants read env vars at import)
    import importlib
    import backend.whiteboard.mission_whiteboard as wb_module
    importlib.reload(wb_module)
    from backend.whiteboard.mission_whiteboard import get_mission_whiteboard
    
    try:
        # Create mission
        mission_id = str(uuid.uuid4())
        thread_id = str(uuid.uuid4())
        
        mission_data = {
            "event_type": "mission_created",
            "mission": {
                "mission_id": mission_id,
                "objective": {
                    "type": "data_collection",
                    "description": "Test mission",
                    "target": 50,
                    "required_fields": ["data"]
                },
                "scope": {"allowed_domains": ["example.com"], "max_pages": 100, "max_duration_seconds": 300},
                "authority": {"execution_mode": "supervised", "external_actions_allowed": []},
                "success_conditions": {"min_items_collected": 50},
                "failure_conditions": {"no_progress_pages": 5, "navigation_blocked": False, "required_fields_missing": False},
                "reporting": {"summary_required": True, "confidence_explanation": True},
                "status": "completed",
                "created_at": datetime.now().isoformat(),
                "completed_at": datetime.now().isoformat(),
                "mission_thread_id": thread_id
            },
            "timestamp": datetime.now().isoformat()
        }
        
        with open(missions_file, "w") as f:
            f.write(json.dumps(mission_data) + "\n")
        
        # Create expectation delta signal
        evaluator = ExpectationDeltaEvaluator(signals_file=signals_file)
        evaluator.evaluate(
            mission_id=mission_id,
            objective={
                "type": "data_collection",
                "description": "Test mission",
                "target": 50,
                "required_fields": ["data"]
            },
            outcome_summary={
                "status": "completed",
                "items_collected": 30,
                "reason": "execution_completed"
            },
            mission_thread_id=thread_id
        )
        
        # Get whiteboard
        whiteboard = get_mission_whiteboard(mission_id)
        
        # Verify expectation_delta present
        assert "expectation_delta" in whiteboard
        assert whiteboard["expectation_delta"] is not None
        assert whiteboard["expectation_delta"]["alignment"] == "misaligned"
        assert whiteboard["expectation_delta"]["confidence"] > 0
        assert "below target" in whiteboard["expectation_delta"]["reason"].lower()
        
    finally:
        if "MISSIONS_FILE" in os.environ:
            del os.environ["MISSIONS_FILE"]
        if "LEARNING_SIGNALS_FILE" in os.environ:
            del os.environ["LEARNING_SIGNALS_FILE"]


def test_multiple_evaluations_latest_used(evaluator, temp_signal_file):
    """Test 10: Multiple evaluations - latest is used in whiteboard."""
    mission_id = str(uuid.uuid4())
    
    objective = {
        "type": "data_collection",
        "description": "Test",
        "target": 10,
        "required_fields": ["data"]
    }
    
    # First evaluation - unclear
    evaluator.evaluate(
        mission_id=mission_id,
        objective=objective,
        outcome_summary={"status": "active", "items_collected": 5, "reason": "in_progress"}
    )
    
    # Second evaluation - aligned
    signal2 = evaluator.evaluate(
        mission_id=mission_id,
        objective=objective,
        outcome_summary={"status": "completed", "items_collected": 10, "reason": "target_reached"}
    )
    
    # Verify second evaluation stored
    with open(temp_signal_file, "r") as f:
        lines = f.readlines()
    
    assert len(lines) == 2
    
    # Parse both signals
    signal1_persisted = json.loads(lines[0])
    signal2_persisted = json.loads(lines[1])
    
    assert signal1_persisted["alignment"] == "unclear"
    assert signal2_persisted["alignment"] == "aligned"


def test_no_execution_changes(evaluator, temp_signal_file):
    """Test 11: Verify evaluation does not modify mission execution."""
    mission_id = str(uuid.uuid4())
    
    objective = {
        "type": "data_collection",
        "description": "Test",
        "target": 100,
        "required_fields": ["data"]
    }
    
    # Misaligned outcome
    outcome = {
        "status": "failed",
        "items_collected": 0,
        "reason": "no_progress"
    }
    
    # Evaluate
    signal = evaluator.evaluate(
        mission_id=mission_id,
        objective=objective,
        outcome_summary=outcome
    )
    
    # Verify evaluation is read-only (no retry, no corrective action)
    assert signal["alignment"] == "misaligned"
    
    # Outcome unchanged - evaluator should not modify input
    assert outcome["status"] == "failed"
    assert outcome["items_collected"] == 0
    
    # No additional signals beyond expectation_delta
    with open(temp_signal_file, "r") as f:
        signals = [json.loads(line) for line in f]
    
    assert len(signals) == 1
    assert signals[0]["signal_type"] == "expectation_delta"
    # No retry signals, no corrective action signals


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
