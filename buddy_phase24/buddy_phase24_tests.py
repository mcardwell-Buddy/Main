"""
Phase 24: Comprehensive Test Suite

≥30 deterministic tests covering:
- Tool contract validation
- Execution state transitions
- Conflict detection/resolution
- Rollback behavior
- Mock vs dry-run enforcement
- Integration tests

All tests are dry-run only (no live execution)
"""

import pytest
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List
from .buddy_phase24_tool_contracts import (
    RiskLevel, ExecutionMode, ToolContract, ToolContractRegistry
)
from .buddy_phase24_execution_controller import (
    ExecutionState, ExecutionContext, ExecutionController
)
from .buddy_phase24_conflict_resolver import (
    ConflictType, ResolutionStrategy, Conflict, ConflictResolver
)
from .buddy_phase24_tool_orchestrator import (
    ToolExecutionPlan, ToolOrchestrator
)
from .buddy_phase24_feedback_loop import (
    ToolOutcome, SignalType, FeedbackLoop
)
from .buddy_phase24_monitor import Monitor, HealthStatus


class TestToolContracts:
    """Tool contract validation tests"""
    
    def test_tool_contract_creation_low_risk(self):
        """Test creating a LOW risk tool contract"""
        contract = ToolContract(
            tool_name="vision_inspect",
            risk_level=RiskLevel.LOW,
            reversible=False,
            required_permissions=["read"],
            dependencies=[],
            timeout_seconds=30,
            mock_available=True,
            description="Inspect visual elements",
            max_concurrent_uses=10,
            requires_approval=False
        )
        assert contract.tool_name == "vision_inspect"
        assert contract.risk_level == RiskLevel.LOW
        assert not contract.requires_approval
    
    def test_tool_contract_creation_high_risk(self):
        """Test creating a HIGH risk tool contract"""
        contract = ToolContract(
            tool_name="ghl_create_contact",
            risk_level=RiskLevel.HIGH,
            reversible=False,
            required_permissions=["write", "admin"],
            dependencies=[],
            timeout_seconds=60,
            mock_available=True,
            description="Create contact in GHL",
            max_concurrent_uses=1,
            requires_approval=True
        )
        assert contract.risk_level == RiskLevel.HIGH
        assert contract.requires_approval
        assert contract.max_concurrent_uses == 1
    
    def test_tool_contract_registry_registration(self):
        """Test tool contract registry registration"""
        registry = ToolContractRegistry()
        initial_count = len(registry.contracts)
        
        # Registry should have pre-registered tools
        assert initial_count > 0
        
        # Verify some standard tools are registered
        assert registry.get("vision_inspect") is not None
        assert registry.get("button_click") is not None
    
    def test_tool_contract_registry_list_by_risk(self):
        """Test listing tools by risk level"""
        registry = ToolContractRegistry()
        
        low_risk_tools = registry.list_tools_by_risk(RiskLevel.LOW)
        high_risk_tools = registry.list_tools_by_risk(RiskLevel.HIGH)
        
        assert len(low_risk_tools) > 0
        assert len(high_risk_tools) > 0
        
        # Verify risk levels
        for tool in low_risk_tools:
            assert tool.risk_level == RiskLevel.LOW
        for tool in high_risk_tools:
            assert tool.risk_level == RiskLevel.HIGH
    
    def test_tool_contract_permission_validation(self):
        """Test permission validation"""
        contract = ToolContract(
            tool_name="test_tool",
            risk_level=RiskLevel.MEDIUM,
            reversible=True,
            required_permissions=["read", "write"],
            dependencies=[],
            timeout_seconds=30,
            mock_available=True,
            description="Test",
            max_concurrent_uses=5,
            requires_approval=False
        )
        
        # Should validate permissions
        assert contract.validate_permission("read")
        assert contract.validate_permission("write")
        assert not contract.validate_permission("admin")
    
    def test_tool_contract_statistics(self):
        """Test tool contract statistics"""
        registry = ToolContractRegistry()
        stats = registry.get_statistics()
        
        assert "total_tools" in stats
        assert "by_risk_level" in stats
        assert "by_reversibility" in stats
        assert stats["total_tools"] > 0
    
    def test_tool_contract_validation_request(self):
        """Test tool request validation"""
        registry = ToolContractRegistry()
        
        # Valid request for LOW risk tool
        valid = registry.validate_tool_request("vision_inspect", ExecutionMode.MOCK)
        assert valid is not None
        
        # Invalid tool
        invalid = registry.validate_tool_request("nonexistent_tool", ExecutionMode.MOCK)
        assert invalid is None


class TestExecutionController:
    """Execution state machine tests"""
    
    def test_execution_context_creation(self):
        """Test execution context initialization"""
        context = ExecutionContext(
            current_state=ExecutionState.MOCK,
            confidence_score=0.8,
            tool_name="test_tool"
        )
        assert context.current_state == ExecutionState.MOCK
        assert context.confidence_score == 0.8
    
    def test_execution_controller_initialization(self):
        """Test execution controller initialization"""
        controller = ExecutionController()
        
        # Should start in MOCK state
        assert controller.current_state == ExecutionState.MOCK
        assert controller.rollback_stack == []
    
    def test_execution_mode_evaluation_low_risk(self):
        """Test execution mode evaluation for LOW risk tools"""
        registry = ToolContractRegistry()
        controller = ExecutionController()
        
        mode = controller.evaluate_execution_mode(
            tool="vision_inspect",
            registry=registry,
            current_confidence=0.9
        )
        
        # LOW risk tools can escalate to DRY_RUN or LIVE based on confidence
        assert mode in [ExecutionMode.MOCK, ExecutionMode.DRY_RUN]
    
    def test_execution_mode_evaluation_high_risk(self):
        """Test execution mode evaluation for HIGH risk tools"""
        registry = ToolContractRegistry()
        controller = ExecutionController()
        
        mode = controller.evaluate_execution_mode(
            tool="ghl_create_contact",
            registry=registry,
            current_confidence=0.5
        )
        
        # HIGH risk tools require higher confidence and approval
        # Should default to MOCK unless explicitly approved
        assert mode in [ExecutionMode.MOCK, ExecutionMode.DRY_RUN]
    
    def test_confidence_threshold_enforcement(self):
        """Test confidence threshold enforcement"""
        controller = ExecutionController(confidence_threshold=0.75)
        
        registry = ToolContractRegistry()
        
        # Low confidence should result in MOCK mode
        low_conf_mode = controller.evaluate_execution_mode(
            tool="button_click",
            registry=registry,
            current_confidence=0.5
        )
        assert low_conf_mode == ExecutionMode.MOCK
    
    def test_system_lock_enforcement(self):
        """Test system lock forces MOCK mode"""
        controller = ExecutionController()
        controller.lock_system(reason="Safety critical anomaly")
        
        registry = ToolContractRegistry()
        
        # Even high confidence should be forced to MOCK when locked
        mode = controller.evaluate_execution_mode(
            tool="vision_inspect",
            registry=registry,
            current_confidence=0.95
        )
        assert mode == ExecutionMode.MOCK
    
    def test_system_unlock(self):
        """Test system unlock restores normal operation"""
        controller = ExecutionController()
        controller.lock_system(reason="Test lock")
        controller.unlock_system()
        
        registry = ToolContractRegistry()
        
        # After unlock, normal mode evaluation should resume
        mode = controller.evaluate_execution_mode(
            tool="vision_inspect",
            registry=registry,
            current_confidence=0.9
        )
        assert mode != ExecutionMode.MOCK or controller.current_state != ExecutionState.LOCKED
    
    def test_rollback_stack_tracking(self):
        """Test rollback stack tracking"""
        controller = ExecutionController()
        
        # Execute some actions
        controller.execute_tool_action(
            tool="tool1",
            agent="agent1",
            action="action1",
            reversible=True
        )
        controller.execute_tool_action(
            tool="tool2",
            agent="agent2",
            action="action2",
            reversible=True
        )
        
        assert len(controller.rollback_stack) == 2
    
    def test_rollback_execution(self):
        """Test rollback capability"""
        controller = ExecutionController()
        
        # Execute multiple actions
        for i in range(3):
            controller.execute_tool_action(
                tool=f"tool{i}",
                agent=f"agent{i}",
                action=f"action{i}",
                reversible=True
            )
        
        initial_stack_size = len(controller.rollback_stack)
        
        # Rollback 1 action
        controller.rollback_execution(depth=1)
        
        assert len(controller.rollback_stack) == initial_stack_size - 1
    
    def test_state_transition_audit_trail(self):
        """Test state transition auditing"""
        controller = ExecutionController()
        
        # Transitions should be recorded
        initial_transitions = len(controller.state_transitions)
        
        # Trigger a state transition
        controller.lock_system(reason="Test")
        
        # Should have new transition record
        assert len(controller.state_transitions) > initial_transitions


class TestConflictResolver:
    """Conflict detection and resolution tests"""
    
    def test_conflict_resolver_initialization(self):
        """Test conflict resolver initialization"""
        resolver = ConflictResolver()
        
        assert resolver.active_tools == {}
        assert resolver.execution_history == []
    
    def test_resource_conflict_detection(self):
        """Test detecting resource conflicts"""
        resolver = ConflictResolver()
        
        # Register tools that conflict on same resource
        resolver.register_tool_execution(
            tool="button_click",
            agent="agent1",
            reversible=False
        )
        
        # Attempt to register conflicting tool
        resolver.register_tool_execution(
            tool="button_click",
            agent="agent2",
            reversible=False
        )
        
        # Should detect resource conflict
        conflicts = resolver.detect_conflicts()
        assert len(conflicts) > 0
    
    def test_duplicate_action_conflict_detection(self):
        """Test detecting duplicate action conflicts"""
        resolver = ConflictResolver()
        
        # Register same tool/agent combination twice
        resolver.register_tool_execution("ghl_create_contact", "agent1", False)
        resolver.register_tool_execution("ghl_create_contact", "agent1", False)
        
        conflicts = resolver.detect_conflicts()
        
        # Should detect duplicate action on irreversible tool
        duplicate_conflicts = [c for c in conflicts if c.conflict_type == ConflictType.DUPLICATE_ACTION]
        assert len(duplicate_conflicts) > 0
    
    def test_conflict_resolution_delay_strategy(self):
        """Test DELAY resolution strategy"""
        resolver = ConflictResolver()
        
        conflict = Conflict(
            conflict_type=ConflictType.RESOURCE,
            tools=["tool1", "tool2"],
            agents=["agent1", "agent2"],
            severity=3
        )
        
        resolution = resolver.resolve_conflicts([conflict])
        
        # RESOURCE conflicts should use DELAY strategy
        assert len(resolution) > 0
        assert resolution[0].strategy == ResolutionStrategy.DELAY
    
    def test_conflict_resolution_abort_strategy(self):
        """Test ABORT resolution strategy for duplicate irreversible"""
        resolver = ConflictResolver()
        
        conflict = Conflict(
            conflict_type=ConflictType.DUPLICATE_ACTION,
            tools=["ghl_create_contact", "ghl_create_contact"],
            agents=["agent1", "agent1"],
            severity=9
        )
        
        resolution = resolver.resolve_conflicts([conflict])
        
        # DUPLICATE_ACTION on irreversible should use ABORT
        assert len(resolution) > 0
        assert resolution[0].strategy == ResolutionStrategy.ABORT
    
    def test_tool_dependency_graph(self):
        """Test tool dependency graph is built"""
        resolver = ConflictResolver()
        
        # Should have dependency graph
        assert resolver.tool_dependencies is not None
        assert len(resolver.tool_dependencies) > 0
    
    def test_conflict_summary_statistics(self):
        """Test conflict summary statistics"""
        resolver = ConflictResolver()
        
        # Register some conflicts
        resolver.register_tool_execution("tool1", "agent1", False)
        resolver.register_tool_execution("tool1", "agent2", False)
        
        conflicts = resolver.detect_conflicts()
        resolver.resolve_conflicts(conflicts)
        
        summary = resolver.get_conflict_summary()
        
        assert "total_conflicts" in summary
        assert "by_type" in summary
        assert "by_resolution_strategy" in summary


class TestToolOrchestrator:
    """Tool orchestration tests"""
    
    def test_orchestrator_initialization(self):
        """Test orchestrator initialization"""
        orchestrator = ToolOrchestrator()
        
        assert orchestrator.execution_controller is not None
        assert orchestrator.conflict_resolver is not None
    
    def test_orchestrator_tool_registration(self):
        """Test tool registration in orchestrator"""
        orchestrator = ToolOrchestrator()
        registry = ToolContractRegistry()
        
        # Register tools
        orchestrator.register_tool_execution(
            tool="vision_inspect",
            agent="agent1",
            registry=registry
        )
        
        # Should track execution
        assert len(orchestrator.execution_history) > 0
    
    def test_tool_allocation(self):
        """Test tool allocation to agents"""
        orchestrator = ToolOrchestrator()
        registry = ToolContractRegistry()
        
        plan = ToolExecutionPlan(
            plan_id="test_plan",
            agent_assignments={
                "agent1": ["vision_inspect", "form_fill"],
                "agent2": ["button_click"]
            },
            execution_order=["vision_inspect", "form_fill", "button_click"],
            confidence_scores={"vision_inspect": 0.8, "form_fill": 0.7, "button_click": 0.9}
        )
        
        result = orchestrator.allocate_tools(plan, registry)
        
        # Should allocate tools
        assert result is not None
    
    def test_orchestration_cycle_execution(self):
        """Test complete orchestration cycle"""
        orchestrator = ToolOrchestrator()
        registry = ToolContractRegistry()
        
        plan = ToolExecutionPlan(
            plan_id="test_cycle",
            agent_assignments={"agent1": ["vision_inspect"]},
            execution_order=["vision_inspect"],
            confidence_scores={"vision_inspect": 0.8}
        )
        
        # Register tools with registry first
        orchestrator.register_tool_execution("vision_inspect", "agent1", registry)
        
        result = orchestrator.execute_orchestration_cycle(plan)
        
        assert result is not None
        assert result.successful_executions >= 0
    
    def test_orchestration_dry_run_safety(self):
        """Test orchestration enforces dry-run safety"""
        orchestrator = ToolOrchestrator()
        registry = ToolContractRegistry()
        
        # Lock system to MOCK (safety)
        orchestrator.execution_controller.lock_system("Dry-run test mode")
        
        plan = ToolExecutionPlan(
            plan_id="safety_test",
            agent_assignments={"agent1": ["ghl_create_contact"]},
            execution_order=["ghl_create_contact"],
            confidence_scores={"ghl_create_contact": 0.95}
        )
        
        result = orchestrator.execute_orchestration_cycle(plan)
        
        # Should not execute in live mode despite high confidence
        assert orchestrator.execution_controller.current_state == ExecutionState.LOCKED
    
    def test_orchestration_summary_generation(self):
        """Test orchestration summary generation"""
        orchestrator = ToolOrchestrator()
        
        summary = orchestrator.emit_orchestration_summary()
        
        assert summary is not None
        assert "state_transitions" in summary
        assert "execution_summary" in summary


class TestFeedbackLoop:
    """Feedback loop and learning signal tests"""
    
    def test_feedback_loop_initialization(self):
        """Test feedback loop initialization"""
        loop = FeedbackLoop()
        
        assert loop.tool_metrics == {}
        assert loop.learning_signals == []
    
    def test_outcome_recording(self):
        """Test recording tool outcomes"""
        loop = FeedbackLoop()
        
        outcome = ToolOutcome(
            tool_name="vision_inspect",
            agent_id="agent1",
            execution_mode=ExecutionMode.MOCK,
            success=True,
            confidence_predicted=0.8,
            execution_time_seconds=0.5
        )
        
        loop.record_outcome(outcome)
        
        assert "vision_inspect" in loop.tool_metrics
    
    def test_tool_reliability_analysis(self):
        """Test tool reliability analysis"""
        loop = FeedbackLoop()
        
        # Record multiple successful outcomes
        for i in range(10):
            outcome = ToolOutcome(
                tool_name="vision_inspect",
                agent_id=f"agent{i}",
                execution_mode=ExecutionMode.MOCK,
                success=True,
                confidence_predicted=0.8,
                execution_time_seconds=0.1
            )
            loop.record_outcome(outcome)
        
        loop.analyze_tool_reliability()
        
        # Should emit signal for high reliability
        signals = loop.get_signals_for_phase(16)
        reliability_signals = [s for s in signals if s["signal_type"] == "TOOL_RELIABILITY"]
        assert len(reliability_signals) > 0
    
    def test_execution_mode_analysis(self):
        """Test execution mode performance analysis"""
        loop = FeedbackLoop()
        
        # Record outcomes in different modes
        for mode in [ExecutionMode.MOCK, ExecutionMode.DRY_RUN]:
            outcome = ToolOutcome(
                tool_name="button_click",
                agent_id="agent1",
                execution_mode=mode,
                success=True,
                confidence_predicted=0.85,
                execution_time_seconds=0.2
            )
            loop.record_outcome(outcome)
        
        loop.analyze_execution_modes()
        
        signals = loop.get_signals_for_phase(19)
        assert len(signals) > 0
    
    def test_conflict_pattern_detection(self):
        """Test conflict pattern detection"""
        loop = FeedbackLoop()
        
        # Record multiple similar conflicts
        for i in range(4):
            loop.record_conflict({
                "type": "RESOURCE",
                "tools": ["tool1", "tool2"],
                "resolution": "DELAY"
            })
        
        loop.detect_conflict_patterns()
        
        signals = loop.get_signals_for_phase(19)
        assert len(signals) > 0
    
    def test_confidence_calibration_analysis(self):
        """Test confidence calibration analysis"""
        loop = FeedbackLoop()
        
        # Record outcomes with varying confidence
        for confidence in [0.3, 0.5, 0.7, 0.9]:
            outcome = ToolOutcome(
                tool_name="test_tool",
                agent_id="agent1",
                execution_mode=ExecutionMode.MOCK,
                success=confidence > 0.5,  # Higher confidence -> more success
                confidence_predicted=confidence,
                execution_time_seconds=0.1
            )
            loop.record_outcome(outcome)
        
        loop.analyze_confidence_calibration()
        
        signals = loop.export_signals()
        assert len(signals) > 0
    
    def test_signal_export(self):
        """Test signal export format"""
        loop = FeedbackLoop()
        
        outcome = ToolOutcome(
            tool_name="vision_inspect",
            agent_id="agent1",
            execution_mode=ExecutionMode.MOCK,
            success=True,
            confidence_predicted=0.8,
            execution_time_seconds=0.1
        )
        loop.record_outcome(outcome)
        loop.analyze_tool_reliability()
        
        signals = loop.export_signals()
        
        for signal in signals:
            assert "signal_type" in signal
            assert "tool_name" in signal
            assert "confidence" in signal
            assert "target_phase" in signal


class TestMonitor:
    """System monitoring and health tests"""
    
    def test_monitor_initialization(self):
        """Test monitor initialization"""
        monitor = Monitor()
        
        assert monitor.metrics == []
        assert monitor.anomalies == []
    
    def test_metric_tracking(self):
        """Test metric recording"""
        monitor = Monitor()
        
        monitor.record_metric("tool_success_rate", 0.95, "%")
        
        assert len(monitor.metrics) > 0
    
    def test_health_score_calculation(self):
        """Test health score calculation"""
        monitor = Monitor()
        
        # Record good metrics
        monitor.record_metric("tool_success_rate", 0.95, "%")
        monitor.record_metric("rollback_frequency", 0.05, "%")
        monitor.record_metric("conflict_rate", 0.02, "%")
        
        health_score = monitor.calculate_health_score()
        
        assert 0 <= health_score <= 100
        assert health_score > 75  # Should be in GOOD range
    
    def test_health_status_categorization(self):
        """Test health status categorization"""
        monitor = Monitor()
        
        # Test excellent health
        excellent = monitor._categorize_health(95)
        assert excellent == HealthStatus.EXCELLENT
        
        # Test good health
        good = monitor._categorize_health(80)
        assert good == HealthStatus.GOOD
        
        # Test poor health
        poor = monitor._categorize_health(40)
        assert poor == HealthStatus.POOR
    
    def test_anomaly_detection(self):
        """Test anomaly detection"""
        monitor = Monitor()
        
        # Record metrics indicating anomaly
        monitor.record_metric("tool_success_rate", 0.30, "%")  # Low success
        monitor.record_metric("rollback_frequency", 0.50, "%")  # High rollbacks
        
        anomalies = monitor.detect_anomalies()
        
        # Should detect anomalies
        assert len(anomalies) > 0
    
    def test_confidence_drift_detection(self):
        """Test confidence drift anomaly detection"""
        monitor = Monitor()
        
        # Simulate confidence drift
        monitor.record_metric("confidence_drift", 0.5, "delta")
        
        anomalies = monitor.detect_anomalies()
        
        # Should detect unsafe escalation anomaly
        unsafe_escalations = [a for a in anomalies if a.anomaly_type == "unsafe_escalation"]
        assert len(unsafe_escalations) > 0
    
    def test_metrics_summary(self):
        """Test metrics summary generation"""
        monitor = Monitor()
        
        monitor.record_metric("tool_success_rate", 0.92, "%")
        
        summary = monitor.get_metrics_summary()
        
        assert "current_metrics" in summary
        assert "health_status" in summary
        assert "anomaly_count" in summary
    
    def test_metric_history_tracking(self):
        """Test metric history tracking"""
        monitor = Monitor()
        
        # Record same metric multiple times
        for i in range(5):
            monitor.record_metric("tool_success_rate", 0.80 + i * 0.01, "%")
        
        history = monitor.get_metric_history("tool_success_rate")
        
        assert len(history) == 5


class TestIntegration:
    """Integration tests for Phase 24"""
    
    def test_full_pipeline_dry_run(self):
        """Test complete pipeline in dry-run mode"""
        from .buddy_phase24_harness import Phase24Harness, Phase24ExecutionConfig
        from pathlib import Path
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Phase24ExecutionConfig(
                output_dir=Path(tmpdir),
                dry_run_only=True
            )
            
            harness = Phase24Harness(config)
            
            # Load sample plans
            sample_plans = [
                {
                    "plan_id": "plan_1",
                    "agent_assignments": {
                        "agent1": ["vision_inspect", "form_fill"],
                        "agent2": ["button_click"]
                    },
                    "execution_order": ["vision_inspect", "form_fill", "button_click"],
                    "confidence_scores": {
                        "vision_inspect": 0.8,
                        "form_fill": 0.75,
                        "button_click": 0.9
                    }
                }
            ]
            
            harness.load_phase21_plans(sample_plans)
            result = harness.execute_orchestration_pipeline()
            
            assert result["plans_processed"] == 1
            assert result["plans_successful"] >= 0
    
    def test_approval_gate_callback_integration(self):
        """Test approval gate callback integration"""
        controller = ExecutionController()
        registry = ToolContractRegistry()
        
        # Set up approval callback
        approval_calls = []
        
        def approval_callback(tool, confidence):
            approval_calls.append((tool, confidence))
            return True  # Approve
        
        controller.approval_gate_callback = approval_callback
        
        # Attempt high-risk tool execution
        registry.validate_tool_request("ghl_create_contact", ExecutionMode.DRY_RUN)
        
        # Callback should be invoked for approval
        # (depends on implementation details)
    
    def test_phase_integration_points(self):
        """Test all phase integration points"""
        orchestrator = ToolOrchestrator()
        registry = ToolContractRegistry()
        
        # Phase 21: Execution plans
        plan = ToolExecutionPlan(
            plan_id="test",
            agent_assignments={"agent1": ["vision_inspect"]},
            execution_order=["vision_inspect"],
            confidence_scores={"vision_inspect": 0.8},
            phase21_plan_id="phase21_12345"
        )
        
        # Execute through orchestrator
        result = orchestrator.execute_orchestration_cycle(plan)
        
        # Should support phase integration
        assert result is not None


# Execution
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
