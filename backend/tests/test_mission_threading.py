"""
Phase 4 Step 1: Mission Threading Validation Tests

Tests that mission_thread_id links missions in the same session without
changing mission execution behavior or autonomy.

Test Requirements:
1. Create 2 missions under same thread
2. Confirm thread groups correctly in whiteboard
3. Confirm missions still terminate independently
"""

import os
import uuid
import pytest
from datetime import datetime
from typing import Optional

from backend.mission_control.mission_contract import MissionContract
from backend.mission_control.mission_registry import MissionRegistry
from backend.whiteboard.mission_whiteboard import get_mission_whiteboard, get_missions_by_thread


@pytest.fixture
def temp_mission_file(tmp_path):
    """Create temporary mission file for testing."""
    mission_file = tmp_path / "missions.jsonl"
    os.environ["MISSIONS_FILE"] = str(mission_file)
    yield mission_file
    if "MISSIONS_FILE" in os.environ:
        del os.environ["MISSIONS_FILE"]


@pytest.fixture
def temp_signal_file(tmp_path):
    """Create temporary signal file for testing."""
    signal_file = tmp_path / "learning_signals.jsonl"
    os.environ["LEARNING_SIGNALS_FILE"] = str(signal_file)
    yield signal_file
    if "LEARNING_SIGNALS_FILE" in os.environ:
        del os.environ["LEARNING_SIGNALS_FILE"]


@pytest.fixture
def mission_registry(temp_mission_file, temp_signal_file):
    """Create MissionRegistry with temp files."""
    return MissionRegistry()


def _create_test_mission(objective: str, mission_thread_id: Optional[str] = None) -> MissionContract:
    """Helper to create a complete test mission."""
    return MissionContract.new(
        objective={
            "type": "data_collection",
            "description": objective,
            "target": 5,
            "required_fields": ["title", "url"]
        },
        scope={
            "allowed_domains": ["example.com"],
            "max_pages": 100,
            "max_duration_seconds": 300
        },
        authority={
            "execution_mode": "supervised",
            "external_actions_allowed": ["navigate", "click"]
        },
        success_conditions={"min_items_collected": 1},
        failure_conditions={
            "no_progress_pages": 5,
            "navigation_blocked": True,
            "required_fields_missing": True
        },
        reporting={
            "summary_required": True,
            "confidence_explanation": True
        },
        mission_thread_id=mission_thread_id
    )


def test_mission_thread_id_in_contract():
    """Test 1: MissionContract stores mission_thread_id."""
    thread_id = str(uuid.uuid4())
    
    mission = _create_test_mission("Test mission 1", thread_id)
    
    assert mission.mission_thread_id == thread_id
    assert mission.mission_id is not None


def test_two_missions_same_thread(mission_registry):
    """Test 2: Create 2 missions under the same thread."""
    thread_id = str(uuid.uuid4())
    
    # Create mission 1
    mission1 = _create_test_mission("Search for Python tutorials", thread_id)
    mission_registry.register_mission(mission1)
    
    # Create mission 2
    mission2 = _create_test_mission("Search for JavaScript tutorials", thread_id)
    mission_registry.register_mission(mission2)
    
    # Both missions should have same thread_id
    assert mission1.mission_thread_id == thread_id
    assert mission2.mission_thread_id == thread_id
    assert mission1.mission_id != mission2.mission_id  # Different mission IDs


def test_thread_id_in_mission_registry(mission_registry):
    """Test 3: Thread ID cached and propagated by MissionRegistry."""
    thread_id = str(uuid.uuid4())
    
    mission = _create_test_mission("Test mission", thread_id)
    mission_registry.register_mission(mission)
    
    # Thread ID should be cached
    assert mission.mission_id in mission_registry._thread_cache
    assert mission_registry._thread_cache[mission.mission_id] == thread_id
    
    # Update status and verify thread_id propagates
    mission_registry.update_status(mission.mission_id, "in_progress", "Test update")
    
    # Read missions file and verify thread_id in status update
    import json
    with open(mission_registry.missions_file, "r") as f:
        records = [json.loads(line) for line in f]
    
    # Find our specific status update (last one with our mission_id)
    status_updates = [r for r in records if r.get("event_type") == "mission_status_update" and r.get("mission_id") == mission.mission_id]
    assert len(status_updates) >= 1
    # Check the most recent status update for our mission has the thread_id
    assert status_updates[-1].get("mission_thread_id") == thread_id


def test_thread_grouping_in_whiteboard(mission_registry):
    """Test 4: Confirm thread groups correctly in whiteboard."""
    thread_id = str(uuid.uuid4())
    
    # Create 2 missions in same thread
    mission1 = _create_test_mission("First mission in thread", thread_id)
    mission_registry.register_mission(mission1)
    
    mission2 = _create_test_mission("Second mission in thread", thread_id)
    mission_registry.register_mission(mission2)
    
    # Get missions by thread
    thread_missions = get_missions_by_thread(thread_id)
    
    # Should return both missions
    assert len(thread_missions) == 2
    assert thread_missions[0]["mission_id"] == mission1.mission_id
    assert thread_missions[1]["mission_id"] == mission2.mission_id
    
    # Verify chronological order (first created appears first)
    assert thread_missions[0]["objective"] == "First mission in thread"
    assert thread_missions[1]["objective"] == "Second mission in thread"


def test_mission_whiteboard_displays_thread_id(mission_registry):
    """Test 5: Whiteboard displays mission_thread_id."""
    thread_id = str(uuid.uuid4())
    
    mission = _create_test_mission("Test mission", thread_id)
    mission_registry.register_mission(mission)
    
    # Get whiteboard
    whiteboard = get_mission_whiteboard(mission.mission_id)
    
    # Verify thread_id displayed
    assert whiteboard.get("mission_thread_id") == thread_id


def test_missions_terminate_independently(mission_registry):
    """Test 6: Confirm missions still terminate independently."""
    thread_id = str(uuid.uuid4())
    
    # Create 2 missions in same thread
    mission1 = _create_test_mission("Mission 1", thread_id)
    mission_registry.register_mission(mission1)
    
    mission2 = _create_test_mission("Mission 2", thread_id)
    mission_registry.register_mission(mission2)
    
    # Complete mission 1
    mission_registry.update_status(mission1.mission_id, "completed", "Test completion")
    
    # Mission 1 should be completed
    whiteboard1 = get_mission_whiteboard(mission1.mission_id)
    assert whiteboard1.get("status") == "completed"
    
    # Mission 2 should still be created (not affected by mission 1 completion)
    whiteboard2 = get_mission_whiteboard(mission2.mission_id)
    assert whiteboard2.get("status") == "created"
    
    # Fail mission 2
    mission_registry.update_status(mission2.mission_id, "failed", "Test failure")
    
    # Mission 2 should be failed
    whiteboard2 = get_mission_whiteboard(mission2.mission_id)
    assert whiteboard2.get("status") == "failed"
    
    # Mission 1 should remain completed (not affected by mission 2 failure)
    whiteboard1 = get_mission_whiteboard(mission1.mission_id)
    assert whiteboard1.get("status") == "completed"


def test_mission_without_thread_id(mission_registry):
    """Test 7: Missions without thread_id still work (backward compatibility)."""
    # Create mission without thread_id
    mission = _create_test_mission("Mission without thread")
    mission_registry.register_mission(mission)
    
    assert mission.mission_thread_id is None
    
    # Should still work normally
    whiteboard = get_mission_whiteboard(mission.mission_id)
    assert whiteboard.get("objective") == "Mission without thread"
    assert whiteboard.get("mission_thread_id") is None


def test_mixed_thread_and_no_thread_missions(mission_registry):
    """Test 8: Missions with and without thread_id coexist."""
    thread_id = str(uuid.uuid4())
    
    # Create mission with thread_id
    mission_with_thread = _create_test_mission("Mission with thread", thread_id)
    mission_registry.register_mission(mission_with_thread)
    
    # Create mission without thread_id
    mission_without_thread = _create_test_mission("Mission without thread")
    mission_registry.register_mission(mission_without_thread)
    
    # Both should work independently
    whiteboard1 = get_mission_whiteboard(mission_with_thread.mission_id)
    assert whiteboard1.get("mission_thread_id") == thread_id
    
    whiteboard2 = get_mission_whiteboard(mission_without_thread.mission_id)
    assert whiteboard2.get("mission_thread_id") is None
    
    # Thread grouping should only return threaded mission
    thread_missions = get_missions_by_thread(thread_id)
    assert len(thread_missions) == 1
    assert thread_missions[0]["mission_id"] == mission_with_thread.mission_id


def test_thread_id_serialization():
    """Test 9: Thread ID serializes/deserializes correctly."""
    thread_id = str(uuid.uuid4())
    
    # Create mission
    mission = _create_test_mission("Test serialization", thread_id)
    
    # Serialize to dict
    mission_dict = mission.to_dict()
    assert mission_dict["mission_thread_id"] == thread_id
    
    # Deserialize from dict
    restored_mission = MissionContract.from_dict(mission_dict)
    assert restored_mission.mission_thread_id == thread_id
    assert restored_mission.mission_id == mission.mission_id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
