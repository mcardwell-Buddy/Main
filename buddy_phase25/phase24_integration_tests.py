"""
Phase 24 Integration Tests
Tests for all Phase 24 adapters and aggregate functionality
"""

import json
import tempfile
from pathlib import Path
from typing import List, Dict, Any
import pytest
from dataclasses import asdict

from phase24_adapters import (
    Phase24Adapter,
    ExecutionLogAdapter,
    StateTransitionAdapter,
    SystemHealthAdapter,
    RollbackAdapter,
    ConflictAdapter,
    LearningSignalAdapter,
    Phase24AggregateAdapter,
    ToolExecution,
    ExecutionStateTransition,
    SystemHealthSnapshot,
    RollbackEvent,
    ToolConflict,
    LearningSignal,
    ExecutionMode,
)


class TestExecutionLogAdapter:
    """Test ExecutionLogAdapter"""
    
    def test_initialization_without_file(self):
        """Should handle missing file gracefully"""
        adapter = ExecutionLogAdapter()
        assert adapter.get_recent_executions(limit=5) == []
        assert adapter.get_executions_by_status("success") == []
        assert adapter.get_tool_statistics() == {}
        assert adapter.get_execution_success_rate() == 0.0
    
    def test_recent_executions_ordering(self):
        """Recent executions should be ordered by timestamp"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test file
            adapter = ExecutionLogAdapter()
            adapter.data_dir = tmpdir
            
            test_data = [
                {
                    "execution_id": "exec_1",
                    "tool_name": "tool_a",
                    "timestamp": "2024-01-01T10:00:00",
                    "duration_ms": 100,
                    "status": "success",
                    "confidence_score": 0.95,
                    "risk_level": "low",
                    "approval_status": "approved",
                    "dry_run_mode": False
                },
                {
                    "execution_id": "exec_2",
                    "tool_name": "tool_b",
                    "timestamp": "2024-01-01T10:00:10",
                    "duration_ms": 200,
                    "status": "success",
                    "confidence_score": 0.85,
                    "risk_level": "medium",
                    "approval_status": "approved",
                    "dry_run_mode": False
                }
            ]
            
            with open(Path(tmpdir) / "tool_execution_log.jsonl", 'w') as f:
                for item in test_data:
                    f.write(json.dumps(item) + '\n')
            
            execs = adapter.get_recent_executions(limit=2)
            assert len(execs) == 2
            assert execs[0].execution_id == "exec_2"  # Most recent first
            assert execs[1].execution_id == "exec_1"
    
    def test_executions_by_status(self):
        """Should filter executions by status correctly"""
        with tempfile.TemporaryDirectory() as tmpdir:
            adapter = ExecutionLogAdapter()
            adapter.data_dir = tmpdir
            
            test_data = [
                {"execution_id": "exec_1", "tool_name": "tool_a", "timestamp": "2024-01-01T10:00:00",
                 "duration_ms": 100, "status": "success", "confidence_score": 0.95, "risk_level": "low",
                 "approval_status": "approved", "dry_run_mode": False},
                {"execution_id": "exec_2", "tool_name": "tool_b", "timestamp": "2024-01-01T10:00:01",
                 "duration_ms": 50, "status": "failed", "confidence_score": 0.3, "risk_level": "high",
                 "approval_status": "approved", "dry_run_mode": False},
            ]
            
            with open(Path(tmpdir) / "tool_execution_log.jsonl", 'w') as f:
                for item in test_data:
                    f.write(json.dumps(item) + '\n')
            
            success_execs = adapter.get_executions_by_status("success")
            assert len(success_execs) == 1
            assert success_execs[0].status == "success"
            
            failed_execs = adapter.get_executions_by_status("failed")
            assert len(failed_execs) == 1
            assert failed_execs[0].status == "failed"
    
    def test_tool_statistics(self):
        """Should calculate tool statistics correctly"""
        with tempfile.TemporaryDirectory() as tmpdir:
            adapter = ExecutionLogAdapter()
            adapter.data_dir = tmpdir
            
            test_data = [
                {"execution_id": "exec_1", "tool_name": "tool_a", "timestamp": "2024-01-01T10:00:00",
                 "duration_ms": 100, "status": "success", "confidence_score": 0.95, "risk_level": "low",
                 "approval_status": "approved", "dry_run_mode": False},
                {"execution_id": "exec_2", "tool_name": "tool_a", "timestamp": "2024-01-01T10:00:01",
                 "duration_ms": 150, "status": "success", "confidence_score": 0.9, "risk_level": "low",
                 "approval_status": "approved", "dry_run_mode": False},
                {"execution_id": "exec_3", "tool_name": "tool_a", "timestamp": "2024-01-01T10:00:02",
                 "duration_ms": 50, "status": "failed", "confidence_score": 0.2, "risk_level": "high",
                 "approval_status": "approved", "dry_run_mode": False},
            ]
            
            with open(Path(tmpdir) / "tool_execution_log.jsonl", 'w') as f:
                for item in test_data:
                    f.write(json.dumps(item) + '\n')
            
            stats = adapter.get_tool_statistics()
            assert "tool_a" in stats
            assert stats["tool_a"]["total_calls"] == 3
            assert stats["tool_a"]["successful"] == 2
            assert stats["tool_a"]["failed"] == 1
            assert stats["tool_a"]["avg_duration_ms"] == 100.0  # (100 + 150 + 50) / 3
    
    def test_execution_success_rate(self):
        """Should calculate success rate correctly"""
        with tempfile.TemporaryDirectory() as tmpdir:
            adapter = ExecutionLogAdapter()
            adapter.data_dir = tmpdir
            
            test_data = [
                {"execution_id": "exec_1", "tool_name": "tool_a", "timestamp": "2024-01-01T10:00:00",
                 "duration_ms": 100, "status": "success", "confidence_score": 0.95, "risk_level": "low",
                 "approval_status": "approved", "dry_run_mode": False},
                {"execution_id": "exec_2", "tool_name": "tool_a", "timestamp": "2024-01-01T10:00:01",
                 "duration_ms": 50, "status": "failed", "confidence_score": 0.2, "risk_level": "high",
                 "approval_status": "approved", "dry_run_mode": False},
            ]
            
            with open(Path(tmpdir) / "tool_execution_log.jsonl", 'w') as f:
                for item in test_data:
                    f.write(json.dumps(item) + '\n')
            
            rate = adapter.get_execution_success_rate()
            assert rate == pytest.approx(0.5, rel=0.01)


class TestSystemHealthAdapter:
    """Test SystemHealthAdapter"""
    
    def test_health_snapshot_missing(self):
        """Should handle missing health file"""
        adapter = SystemHealthAdapter()
        assert adapter.get_health_snapshot() is None
        assert adapter.get_health_indicators() == {}
    
    def test_health_tier_calculation(self):
        """Should classify health tiers correctly"""
        adapter = SystemHealthAdapter()
        
        assert adapter.get_health_tier(95) == "EXCELLENT"
        assert adapter.get_health_tier(75) == "GOOD"
        assert adapter.get_health_tier(50) == "WARNING"
        assert adapter.get_health_tier(25) == "CRITICAL"
        assert adapter.get_health_tier(5) == "FAILURE"
    
    def test_health_snapshot_parsing(self):
        """Should parse health snapshot correctly"""
        with tempfile.TemporaryDirectory() as tmpdir:
            adapter = SystemHealthAdapter()
            adapter.data_dir = tmpdir
            
            health_data = {
                "timestamp": "2024-01-01T10:00:00",
                "health_score": 85.5,
                "execution_mode": "LIVE",
                "active_tools": 3,
                "completed_executions": 150,
                "failed_executions": 5,
                "blocked_executions": 2,
                "average_confidence": 0.92,
                "anomalies": ["tool_a_timeout", "high_rollback_rate"]
            }
            
            with open(Path(tmpdir) / "system_health.json", 'w') as f:
                json.dump(health_data, f)
            
            snapshot = adapter.get_health_snapshot()
            assert snapshot is not None
            assert snapshot.health_score == 85.5
            assert snapshot.execution_mode == "LIVE"
            assert len(snapshot.anomalies) == 2
            
            indicators = adapter.get_health_indicators()
            assert indicators["current_mode"] == "LIVE"
            assert indicators["active_tools"] == 3


class TestRollbackAdapter:
    """Test RollbackAdapter"""
    
    def test_rollback_missing(self):
        """Should handle missing rollback file"""
        adapter = RollbackAdapter()
        assert adapter.get_recent_rollbacks() == []
        assert adapter.get_rollback_summary() == {}
    
    def test_recent_rollbacks(self):
        """Should return recent rollbacks ordered by timestamp"""
        with tempfile.TemporaryDirectory() as tmpdir:
            adapter = RollbackAdapter()
            adapter.data_dir = tmpdir
            
            test_data = [
                {
                    "rollback_id": "rb_1",
                    "trigger": "safety_violation",
                    "affected_executions": ["exec_1", "exec_2"],
                    "reason": "Tool confidence dropped below threshold",
                    "recovery_status": "completed",
                    "duration_ms": 500,
                    "timestamp": "2024-01-01T10:00:00"
                },
                {
                    "rollback_id": "rb_2",
                    "trigger": "manual",
                    "affected_executions": ["exec_3"],
                    "reason": "User initiated rollback",
                    "recovery_status": "in_progress",
                    "duration_ms": 100,
                    "timestamp": "2024-01-01T10:00:10"
                }
            ]
            
            with open(Path(tmpdir) / "rollback_events.jsonl", 'w') as f:
                for item in test_data:
                    f.write(json.dumps(item) + '\n')
            
            rollbacks = adapter.get_recent_rollbacks(limit=2)
            assert len(rollbacks) == 2
            assert rollbacks[0].rollback_id == "rb_2"  # Most recent first
    
    def test_rollback_summary(self):
        """Should summarize rollbacks by trigger"""
        with tempfile.TemporaryDirectory() as tmpdir:
            adapter = RollbackAdapter()
            adapter.data_dir = tmpdir
            
            test_data = [
                {
                    "rollback_id": "rb_1",
                    "trigger": "safety_violation",
                    "affected_executions": ["exec_1"],
                    "reason": "Safety threshold exceeded",
                    "recovery_status": "completed",
                    "duration_ms": 500,
                    "timestamp": "2024-01-01T10:00:00"
                },
                {
                    "rollback_id": "rb_2",
                    "trigger": "safety_violation",
                    "affected_executions": ["exec_2"],
                    "reason": "Safety threshold exceeded",
                    "recovery_status": "completed",
                    "duration_ms": 500,
                    "timestamp": "2024-01-01T10:00:01"
                },
                {
                    "rollback_id": "rb_3",
                    "trigger": "manual",
                    "affected_executions": ["exec_3"],
                    "reason": "User request",
                    "recovery_status": "completed",
                    "duration_ms": 200,
                    "timestamp": "2024-01-01T10:00:02"
                }
            ]
            
            with open(Path(tmpdir) / "rollback_events.jsonl", 'w') as f:
                for item in test_data:
                    f.write(json.dumps(item) + '\n')
            
            summary = adapter.get_rollback_summary()
            assert summary["total"] == 3
            assert summary["by_trigger"]["safety_violation"] == 2
            assert summary["by_trigger"]["manual"] == 1


class TestConflictAdapter:
    """Test ConflictAdapter"""
    
    def test_conflicts_missing(self):
        """Should handle missing conflicts file"""
        adapter = ConflictAdapter()
        assert adapter.get_conflicts() == []
        assert adapter.get_unresolved_conflicts() == []
    
    def test_conflict_summary(self):
        """Should summarize conflicts by type and severity"""
        with tempfile.TemporaryDirectory() as tmpdir:
            adapter = ConflictAdapter()
            adapter.data_dir = tmpdir
            
            test_data = [
                {
                    "conflict_id": "cf_1",
                    "tools_involved": ["tool_a", "tool_b"],
                    "conflict_type": "state_collision",
                    "severity": "high",
                    "resolution_strategy": "sequential_execution",
                    "resolution_status": "resolved"
                },
                {
                    "conflict_id": "cf_2",
                    "tools_involved": ["tool_c", "tool_d"],
                    "conflict_type": "resource_contention",
                    "severity": "medium",
                    "resolution_strategy": "lock_acquisition",
                    "resolution_status": "unresolved"
                }
            ]
            
            with open(Path(tmpdir) / "tool_conflicts.json", 'w') as f:
                json.dump(test_data, f)
            
            summary = adapter.get_conflict_summary()
            assert summary["total"] == 2
            assert summary["unresolved"] == 1
            assert summary["by_severity"]["high"] == 1
            assert summary["by_type"]["state_collision"] == 1
    
    def test_high_severity_conflicts(self):
        """Should filter high severity conflicts"""
        with tempfile.TemporaryDirectory() as tmpdir:
            adapter = ConflictAdapter()
            adapter.data_dir = tmpdir
            
            test_data = [
                {
                    "conflict_id": "cf_1",
                    "tools_involved": ["tool_a", "tool_b"],
                    "conflict_type": "state_collision",
                    "severity": "high",
                    "resolution_strategy": "sequential",
                    "resolution_status": "unresolved"
                },
                {
                    "conflict_id": "cf_2",
                    "tools_involved": ["tool_c"],
                    "conflict_type": "timing",
                    "severity": "low",
                    "resolution_strategy": "retry",
                    "resolution_status": "unresolved"
                }
            ]
            
            with open(Path(tmpdir) / "tool_conflicts.json", 'w') as f:
                json.dump(test_data, f)
            
            high_severity = adapter.get_high_severity_conflicts()
            assert len(high_severity) == 1
            assert high_severity[0].conflict_id == "cf_1"


class TestLearningSignalAdapter:
    """Test LearningSignalAdapter"""
    
    def test_signals_missing(self):
        """Should handle missing signals file"""
        adapter = LearningSignalAdapter()
        assert adapter.get_recent_signals() == []
        assert adapter.get_signals_by_type("tool_reliability") == []
    
    def test_high_confidence_signals(self):
        """Should filter signals by confidence threshold"""
        with tempfile.TemporaryDirectory() as tmpdir:
            adapter = LearningSignalAdapter()
            adapter.data_dir = tmpdir
            
            test_data = [
                {
                    "signal_id": "sig_1",
                    "signal_type": "tool_reliability",
                    "tool_name": "tool_a",
                    "insight": "Tool A shows consistent performance",
                    "confidence": 0.95,
                    "recommended_action": "increase_usage",
                    "affected_future_executions": 5
                },
                {
                    "signal_id": "sig_2",
                    "signal_type": "tool_reliability",
                    "tool_name": "tool_b",
                    "insight": "Tool B has increasing failure rate",
                    "confidence": 0.45,
                    "recommended_action": "review_implementation",
                    "affected_future_executions": 3
                }
            ]
            
            with open(Path(tmpdir) / "learning_signals.jsonl", 'w') as f:
                for item in test_data:
                    f.write(json.dumps(item) + '\n')
            
            high_conf = adapter.get_high_confidence_signals(threshold=0.8)
            assert len(high_conf) == 1
            assert high_conf[0].signal_id == "sig_1"
            assert high_conf[0].confidence >= 0.8
    
    def test_learning_summary(self):
        """Should summarize learning signals"""
        with tempfile.TemporaryDirectory() as tmpdir:
            adapter = LearningSignalAdapter()
            adapter.data_dir = tmpdir
            
            test_data = [
                {
                    "signal_id": "sig_1",
                    "signal_type": "tool_reliability",
                    "tool_name": "tool_a",
                    "insight": "Consistent performance",
                    "confidence": 0.95,
                    "recommended_action": "increase_usage",
                    "affected_future_executions": 5
                },
                {
                    "signal_id": "sig_2",
                    "signal_type": "safety_pattern",
                    "tool_name": "tool_a",
                    "insight": "Pattern detected",
                    "confidence": 0.85,
                    "recommended_action": "apply_pattern",
                    "affected_future_executions": 2
                }
            ]
            
            with open(Path(tmpdir) / "learning_signals.jsonl", 'w') as f:
                for item in test_data:
                    f.write(json.dumps(item) + '\n')
            
            summary = adapter.get_learning_summary()
            assert summary["total"] == 2
            assert summary["by_type"]["tool_reliability"] == 1
            assert summary["by_type"]["safety_pattern"] == 1


class TestPhase24AggregateAdapter:
    """Test Phase24AggregateAdapter"""
    
    def test_aggregate_initialization(self):
        """Should initialize all sub-adapters"""
        adapter = Phase24AggregateAdapter()
        assert adapter.execution_adapter is not None
        assert adapter.transition_adapter is not None
        assert adapter.health_adapter is not None
        assert adapter.rollback_adapter is not None
        assert adapter.conflict_adapter is not None
        assert adapter.learning_adapter is not None
    
    def test_operations_summary(self):
        """Should aggregate operations data"""
        with tempfile.TemporaryDirectory() as tmpdir:
            adapter = Phase24AggregateAdapter()
            adapter.execution_adapter.data_dir = tmpdir
            adapter.health_adapter.data_dir = tmpdir
            
            # Create health data
            health_data = {
                "timestamp": "2024-01-01T10:00:00",
                "health_score": 85.0,
                "execution_mode": "LIVE",
                "active_tools": 3,
                "completed_executions": 100,
                "failed_executions": 5,
                "blocked_executions": 2,
                "average_confidence": 0.9,
                "anomalies": []
            }
            
            with open(Path(tmpdir) / "system_health.json", 'w') as f:
                json.dump(health_data, f)
            
            summary = adapter.get_operations_summary()
            assert summary is not None
            assert "execution_mode" in summary or "health_score" in summary
    
    def test_learning_summary_aggregate(self):
        """Should aggregate learning data"""
        with tempfile.TemporaryDirectory() as tmpdir:
            adapter = Phase24AggregateAdapter()
            adapter.learning_adapter.data_dir = tmpdir
            
            test_data = [
                {
                    "signal_id": "sig_1",
                    "signal_type": "tool_reliability",
                    "tool_name": "tool_a",
                    "insight": "Good performance",
                    "confidence": 0.9,
                    "recommended_action": "continue",
                    "affected_future_executions": 1
                }
            ]
            
            with open(Path(tmpdir) / "learning_signals.jsonl", 'w') as f:
                for item in test_data:
                    f.write(json.dumps(item) + '\n')
            
            summary = adapter.get_learning_summary()
            assert summary is not None
            assert "total" in summary or "by_type" in summary


class TestPhase24SafetyGuarantees:
    """Test safety guarantees for Phase 24 adapters"""
    
    def test_dataclass_immutability(self):
        """All dataclasses should be frozen (immutable)"""
        execution = ToolExecution(
            execution_id="test",
            tool_name="test_tool",
            timestamp="2024-01-01T10:00:00",
            duration_ms=100,
            status="success",
            confidence_score=0.95,
            risk_level="low",
            approval_status="approved",
            dry_run_mode=False
        )
        
        # Attempting to modify should raise FrozenInstanceError
        with pytest.raises(Exception):  # FrozenInstanceError
            execution.status = "failed"
    
    def test_no_write_operations(self):
        """Adapters should never write to disk"""
        adapter = ExecutionLogAdapter()
        
        # get_recent_executions should not create files
        with tempfile.TemporaryDirectory() as tmpdir:
            adapter.data_dir = tmpdir
            adapter.get_recent_executions()
            
            # No new files should be created
            files_created = list(Path(tmpdir).glob("*"))
            assert len(files_created) == 0
    
    def test_exception_safety(self):
        """Adapters should handle exceptions gracefully"""
        with tempfile.TemporaryDirectory() as tmpdir:
            adapter = ExecutionLogAdapter()
            adapter.data_dir = tmpdir
            
            # Create corrupted JSON file
            with open(Path(tmpdir) / "tool_execution_log.jsonl", 'w') as f:
                f.write("{invalid json\n")
                f.write('{"valid": "json"}\n')
            
            # Should not raise, should handle gracefully
            executions = adapter.get_recent_executions()
            assert isinstance(executions, list)


def test_full_integration_workflow():
    """Test complete Phase 24 integration workflow"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create all Phase 24 output files
        
        # 1. Execution log
        exec_data = [
            {
                "execution_id": "exec_1",
                "tool_name": "tool_a",
                "timestamp": "2024-01-01T10:00:00",
                "duration_ms": 100,
                "status": "success",
                "confidence_score": 0.95,
                "risk_level": "low",
                "approval_status": "approved",
                "dry_run_mode": False
            }
        ]
        with open(Path(tmpdir) / "tool_execution_log.jsonl", 'w') as f:
            for item in exec_data:
                f.write(json.dumps(item) + '\n')
        
        # 2. State transitions
        trans_data = [
            {
                "transition_id": "trans_1",
                "from_state": "idle",
                "to_state": "executing",
                "trigger": "completion",
                "details": "Tool A completed successfully",
                "timestamp": "2024-01-01T10:00:00"
            }
        ]
        with open(Path(tmpdir) / "execution_state_transitions.jsonl", 'w') as f:
            for item in trans_data:
                f.write(json.dumps(item) + '\n')
        
        # 3. Health
        health_data = {
            "timestamp": "2024-01-01T10:00:00",
            "health_score": 90.0,
            "execution_mode": "LIVE",
            "active_tools": 1,
            "completed_executions": 1,
            "failed_executions": 0,
            "blocked_executions": 0,
            "average_confidence": 0.95,
            "anomalies": []
        }
        with open(Path(tmpdir) / "system_health.json", 'w') as f:
            json.dump(health_data, f)
        
        # 4. Rollbacks
        rb_data = [
            {
                "rollback_id": "rb_1",
                "trigger": "safety_violation",
                "affected_executions": ["exec_1"],
                "reason": "Threshold exceeded",
                "recovery_status": "completed",
                "duration_ms": 500,
                "timestamp": "2024-01-01T10:00:01"
            }
        ]
        with open(Path(tmpdir) / "rollback_events.jsonl", 'w') as f:
            for item in rb_data:
                f.write(json.dumps(item) + '\n')
        
        # 5. Conflicts
        cf_data = [
            {
                "conflict_id": "cf_1",
                "tools_involved": ["tool_a", "tool_b"],
                "conflict_type": "state_collision",
                "severity": "high",
                "resolution_strategy": "sequential",
                "resolution_status": "resolved"
            }
        ]
        with open(Path(tmpdir) / "tool_conflicts.json", 'w') as f:
            json.dump(cf_data, f)
        
        # 6. Learning signals
        sig_data = [
            {
                "signal_id": "sig_1",
                "signal_type": "tool_reliability",
                "tool_name": "tool_a",
                "insight": "Consistent performance",
                "confidence": 0.95,
                "recommended_action": "increase_usage",
                "affected_future_executions": 5
            }
        ]
        with open(Path(tmpdir) / "learning_signals.jsonl", 'w') as f:
            for item in sig_data:
                f.write(json.dumps(item) + '\n')
        
        # Now use aggregate adapter
        adapter = Phase24AggregateAdapter()
        adapter.execution_adapter.data_dir = tmpdir
        adapter.transition_adapter.data_dir = tmpdir
        adapter.health_adapter.data_dir = tmpdir
        adapter.rollback_adapter.data_dir = tmpdir
        adapter.conflict_adapter.data_dir = tmpdir
        adapter.learning_adapter.data_dir = tmpdir
        
        # Verify all adapters work
        ops_summary = adapter.get_operations_summary()
        assert ops_summary is not None
        
        learn_summary = adapter.get_learning_summary()
        assert learn_summary is not None
        
        interact_summary = adapter.get_interaction_summary()
        assert interact_summary is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
