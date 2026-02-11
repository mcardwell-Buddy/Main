"""
Validation test for Phase X: Execution Wiring

Tests the complete flow:
1. Chat intake → mission creation
2. Mission queued for execution
3. Executor processes mission
4. Mission status updated
5. Whiteboard shows results
"""

import pytest
import json
import os
import asyncio
import tempfile
from pathlib import Path
from datetime import datetime, timezone

from Back_End.execution import execution_queue, executor
from Back_End.interaction_orchestrator import InteractionOrchestrator
from Back_End.response_envelope import ResponseType
from Back_End.whiteboard.mission_whiteboard import get_mission_whiteboard


@pytest.mark.asyncio
async def test_execution_wiring_end_to_end():
    """Test complete chat → mission → execution → whiteboard flow."""
    
    # Use temp directories for test isolation
    with tempfile.TemporaryDirectory() as tmpdir:
        missions_file = Path(tmpdir) / "missions.jsonl"
        signals_file = Path(tmpdir) / "learning_signals.jsonl"
        
        # Create test executor with temp files
        test_executor = executor.__class__(
            missions_file=str(missions_file),
            signals_file=str(signals_file)
        )
        
        # Override environment for whiteboard
        os.environ["MISSIONS_FILE"] = str(missions_file)
        os.environ["LEARNING_SIGNALS_FILE"] = str(signals_file)
        
        # Step 1: Create a test mission manually (simulate orchestrator)
        mission_data = {
            "mission_id": "test-mission-001",
            "objective": {
                "type": "test_domain",
                "description": "What is 2+2?"
            },
            "constraints": {
                "allowed_domains": ["example.com"],
                "max_pages": 1,
                "max_duration_seconds": 5,
            }
        }
        
        # Step 2: Enqueue the mission
        execution_queue.enqueue(mission_data)
        assert execution_queue.size() == 1, "Mission should be queued"
        
        # Step 3: Execute the mission
        result = await test_executor.execute_mission(mission_data)
        
        assert result['success'] == True, "Mission execution should succeed"
        assert result['mission_id'] == "test-mission-001"
        assert result['status'] == 'completed'
        
        # Step 4: Verify missions.jsonl was written
        assert missions_file.exists(), "Missions file should exist"
        
        with open(missions_file, 'r') as f:
            lines = f.readlines()
        
        # Should have at least 2 records: mission_status_update active + completed
        status_updates = [json.loads(line) for line in lines]
        assert len(status_updates) >= 2, "Should have multiple status updates"
        
        # Verify status sequence
        active_update = next((u for u in status_updates if u.get('status') == 'active'), None)
        completed_update = next((u for u in status_updates if u.get('status') == 'completed'), None)
        
        assert active_update is not None, "Should have active status update"
        assert completed_update is not None, "Should have completed status update"
        
        # Step 5: Verify execution result is in the update
        assert 'execution_result' in completed_update, "Should have execution result"
        exec_result = completed_update['execution_result']
        assert 'final_answer' in exec_result or 'success' in exec_result, "Should have result data"
        
        # Step 6: Test whiteboard can read the mission
        mission_whiteboard = get_mission_whiteboard("test-mission-001")
        
        assert mission_whiteboard['mission_id'] == "test-mission-001"
        assert mission_whiteboard['status'] == 'completed', "Whiteboard should show completed status"
        
        print(f"✅ Execution wiring validated:")
        print(f"  - Mission queued: {mission_data['mission_id']}")
        print(f"  - Executed: {result['status']}")
        print(f"  - Status updates written: {len(status_updates)}")
        print(f"  - Whiteboard visible: {mission_whiteboard['status']}")


@pytest.mark.asyncio
async def test_mission_status_update_writes_to_jsonl():
    """Test that executor writes mission updates to JSONL correctly."""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        missions_file = Path(tmpdir) / "missions.jsonl"
        
        test_executor = executor.__class__(
            missions_file=str(missions_file),
            signals_file=str(Path(tmpdir) / "signals.jsonl")
        )
        
        # Write a status update
        test_executor._write_mission_update(
            mission_id="test-001",
            status="active",
            reason="test_started"
        )
        
        # Verify it was written
        assert missions_file.exists()
        
        with open(missions_file, 'r') as f:
            line = f.readline()
        
        record = json.loads(line)
        assert record['event_type'] == 'mission_status_update'
        assert record['mission_id'] == 'test-001'
        assert record['status'] == 'active'
        assert record['reason'] == 'test_started'


@pytest.mark.asyncio
async def test_execution_signal_writes_to_jsonl():
    """Test that executor emits signals to learning_signals.jsonl."""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        signals_file = Path(tmpdir) / "signals.jsonl"
        
        test_executor = executor.__class__(
            missions_file=str(Path(tmpdir) / "missions.jsonl"),
            signals_file=str(signals_file)
        )
        
        # Emit a signal
        test_executor._emit_execution_signal(
            mission_id="test-002",
            status="completed",
            result={'success': True, 'tools_used': ['tool1']}
        )
        
        # Verify it was written
        assert signals_file.exists()
        
        with open(signals_file, 'r') as f:
            line = f.readline()
        
        signal = json.loads(line)
        assert signal['event_type'] == 'mission_executed'
        assert signal['mission_id'] == 'test-002'
        assert signal['execution_status'] == 'completed'


def test_execution_queue_prevents_duplicates():
    """Test that execution queue prevents duplicate missions."""
    
    test_queue = execution_queue.__class__()
    
    mission_data = {'mission_id': 'dup-test', 'objective': {'description': 'test'}}
    
    # Enqueue twice
    test_queue.enqueue(mission_data)
    test_queue.enqueue(mission_data)
    
    # Should only be one in queue (second rejected)
    assert test_queue.size() == 1
    
    # Dequeue it
    test_queue.dequeue()
    
    # Second enqueue should also be rejected now
    test_queue.enqueue(mission_data)
    assert test_queue.size() == 0, "Already-processed mission should not be re-queued"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

