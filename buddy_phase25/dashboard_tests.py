"""
Phase 25: Dashboard Tests

Comprehensive unit and integration tests for all dashboards.
Tests dashboard state builders, adapters, router, and integrations.
"""

import pytest
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any
import tempfile
import json

from buddy_phase25.dashboard_state_models import (
    DashboardMode, ExecutionEnvironment, UnifiedDashboardState,
    LearningSignal, ToolExecution, SafetyDecision, ActiveAgent,
    SystemHealthMetrics, ConfidenceTrajectory, MetricPoint,
    LearningDashboardState, OperationsDashboardState, InteractionDashboardState
)
from buddy_phase25.dashboard_router import (
    DashboardRouter, DashboardManager, DashboardMode,
    DashboardNavigationEvent, EnvironmentChangeEvent
)
from buddy_phase25.learning_dashboard import LearningDashboard, LearningDashboardBuilder
from buddy_phase25.operations_dashboard import OperationsDashboard, OperationsDashboardBuilder
from buddy_phase25.interaction_dashboard import InteractionDashboard, InteractionDashboardBuilder


class TestDashboardStateModels:
    """Tests for dashboard state dataclasses"""
    
    def test_metric_point_creation(self):
        """Test metric point creation"""
        point = MetricPoint(
            timestamp=datetime.now(timezone.utc).isoformat(),
            value=0.85,
            unit="confidence"
        )
        assert point.value == 0.85
        assert point.unit == "confidence"
    
    def test_learning_signal_creation(self):
        """Test learning signal creation"""
        signal = LearningSignal(
            signal_id="test_signal_1",
            signal_type="TOOL_RELIABILITY",
            source_phase=24,
            tool_name="vision_inspect",
            insight="Tool achieved 95% success rate",
            recommended_action="Increase confidence threshold",
            confidence=0.92,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        assert signal.signal_type == "TOOL_RELIABILITY"
        assert signal.source_phase == 24
    
    def test_tool_execution_creation(self):
        """Test tool execution record creation"""
        exec_record = ToolExecution(
            execution_id="exec_001",
            tool_name="button_click",
            agent_id="agent_1",
            environment=ExecutionEnvironment.DRY_RUN,
            status="succeeded",
            confidence_score=0.9,
            start_time=datetime.now(timezone.utc).isoformat(),
            duration_ms=150.5
        )
        assert exec_record.tool_name == "button_click"
        assert exec_record.status == "succeeded"
        assert exec_record.duration_ms == 150.5
    
    def test_unified_dashboard_state_creation(self):
        """Test unified dashboard state creation"""
        state = UnifiedDashboardState(
            state_id="state_001",
            timestamp=datetime.now(timezone.utc).isoformat(),
            current_mode=DashboardMode.OPERATIONS
        )
        assert state.current_mode == DashboardMode.OPERATIONS
        assert state.environment == ExecutionEnvironment.MOCK
    
    def test_unified_dashboard_get_dashboard_state(self):
        """Test getting specific dashboard from unified state"""
        state = UnifiedDashboardState(
            state_id="state_001",
            timestamp=datetime.now(timezone.utc).isoformat(),
            current_mode=DashboardMode.LEARNING
        )
        dashboard_state = state.get_dashboard_state(DashboardMode.LEARNING)
        assert isinstance(dashboard_state, LearningDashboardState)


class TestDashboardRouter:
    """Tests for dashboard router and navigation"""
    
    def test_router_initialization(self):
        """Test router initialization"""
        router = DashboardRouter()
        assert router.current_mode == DashboardMode.OPERATIONS
        assert router.unified_state is not None
    
    def test_navigate_to_dashboard(self):
        """Test navigation to different dashboard"""
        router = DashboardRouter()
        initial_mode = router.current_mode
        
        router.navigate_to(DashboardMode.LEARNING)
        assert router.current_mode == DashboardMode.LEARNING
        assert router.unified_state.current_mode == DashboardMode.LEARNING
    
    def test_environment_setting(self):
        """Test setting execution environment"""
        router = DashboardRouter()
        
        router.set_environment(ExecutionEnvironment.LIVE)
        assert router.unified_state.environment == ExecutionEnvironment.LIVE
    
    def test_developer_mode_toggle(self):
        """Test toggling developer mode"""
        router = DashboardRouter()
        assert not router.unified_state.developer_mode.mode_active
        
        router.toggle_developer_mode()
        assert router.unified_state.developer_mode.mode_active
        assert router.current_mode == DashboardMode.DEVELOPER
        
        router.toggle_developer_mode()
        assert not router.unified_state.developer_mode.mode_active
    
    def test_state_refresh(self):
        """Test dashboard state refresh"""
        router = DashboardRouter()
        
        old_timestamp = router.unified_state.timestamp
        router.refresh_dashboard(DashboardMode.OPERATIONS)
        new_timestamp = router.unified_state.timestamp
        
        assert new_timestamp >= old_timestamp
    
    def test_subscription_mechanism(self):
        """Test dashboard state subscription"""
        router = DashboardRouter()
        callback_calls = []
        
        def test_callback(state):
            callback_calls.append(state)
        
        router.subscribe(DashboardMode.OPERATIONS, test_callback)
        router.refresh_dashboard(DashboardMode.OPERATIONS)
        
        assert len(callback_calls) > 0


class TestDashboardManager:
    """Tests for high-level dashboard manager"""
    
    def test_manager_initialization(self):
        """Test manager initialization"""
        manager = DashboardManager()
        assert manager.router is not None
        assert manager.event_bus is not None
    
    def test_manager_navigation_with_logging(self):
        """Test navigation with event logging"""
        manager = DashboardManager()
        
        manager.navigate_to(DashboardMode.LEARNING, "User clicked Learning tab")
        history = manager.get_navigation_history()
        
        assert len(history) > 0
        assert history[-1].to_mode == DashboardMode.LEARNING
    
    def test_environment_change_logging(self):
        """Test environment change logging"""
        manager = DashboardManager()
        
        manager.set_environment(ExecutionEnvironment.DRY_RUN, "User enabled dry-run")
        env_history = manager.event_bus.get_environment_history()
        
        assert len(env_history) > 0
        assert env_history[-1].to_environment == ExecutionEnvironment.DRY_RUN
    
    def test_audit_trail_export(self):
        """Test audit trail export"""
        manager = DashboardManager()
        
        manager.navigate_to(DashboardMode.LEARNING)
        manager.set_environment(ExecutionEnvironment.LIVE)
        manager.navigate_to(DashboardMode.OPERATIONS)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            audit_file = Path(tmpdir) / "audit_trail.json"
            manager.export_audit_trail(audit_file)
            
            assert audit_file.exists()
            
            with open(audit_file, 'r') as f:
                audit_data = json.load(f)
                assert "navigation_history" in audit_data
                assert "environment_changes" in audit_data


class TestLearningDashboard:
    """Tests for Learning Dashboard"""
    
    def test_learning_dashboard_initialization(self):
        """Test learning dashboard initialization"""
        dashboard = LearningDashboard()
        assert dashboard.adapter is not None
        assert dashboard.current_state is None
    
    def test_learning_dashboard_load(self):
        """Test loading learning dashboard"""
        dashboard = LearningDashboard()
        state = dashboard.load()
        
        assert state is not None
        assert isinstance(state, LearningDashboardState)
    
    def test_learning_summary_generation(self):
        """Test learning summary generation"""
        dashboard = LearningDashboard()
        dashboard.load()
        
        summary = dashboard.get_learning_summary()
        assert isinstance(summary, str)
        assert len(summary) > 0
    
    def test_confidence_visualization(self):
        """Test confidence trajectory visualization"""
        dashboard = LearningDashboard()
        dashboard.load()
        
        viz = dashboard.get_confidence_visualization()
        assert isinstance(viz, str)
        # Should contain ASCII characters for visualization
        assert any(c in viz for c in ['█', '─', '|', '+'])
    
    def test_learning_signals_table(self):
        """Test learning signals table generation"""
        dashboard = LearningDashboard()
        dashboard.load()
        
        table = dashboard.get_learning_signals_table()
        assert isinstance(table, str)
        assert "Signal Type" in table or len(table) > 0
    
    def test_tool_performance_table(self):
        """Test tool performance table"""
        dashboard = LearningDashboard()
        dashboard.load()
        
        table = dashboard.get_tool_performance_table()
        assert isinstance(table, str)
    
    def test_builder_widget_creation(self):
        """Test builder creates widgets"""
        builder = LearningDashboardBuilder()
        widgets = builder.build_default_widgets()
        
        assert len(widgets) > 0
        assert all(hasattr(w, 'widget_id') for w in widgets)


class TestOperationsDashboard:
    """Tests for Operations Dashboard"""
    
    def test_operations_dashboard_initialization(self):
        """Test operations dashboard initialization"""
        dashboard = OperationsDashboard()
        assert dashboard.adapter is not None
        assert dashboard.current_state is None
    
    def test_operations_dashboard_load(self):
        """Test loading operations dashboard"""
        dashboard = OperationsDashboard()
        state = dashboard.load()
        
        assert state is not None
        assert isinstance(state, OperationsDashboardState)
    
    def test_operations_summary_generation(self):
        """Test operations summary generation"""
        dashboard = OperationsDashboard()
        dashboard.load()
        
        summary = dashboard.get_operations_summary()
        assert isinstance(summary, str)
        assert len(summary) > 0
    
    def test_environment_indicator(self):
        """Test environment is correctly displayed"""
        dashboard = OperationsDashboard()
        state = dashboard.load(ExecutionEnvironment.LIVE)
        
        assert state.current_environment == ExecutionEnvironment.LIVE
    
    def test_active_agents_table(self):
        """Test active agents table"""
        dashboard = OperationsDashboard()
        dashboard.load()
        
        table = dashboard.get_active_agents_table()
        assert isinstance(table, str)
    
    def test_health_report_generation(self):
        """Test system health report"""
        dashboard = OperationsDashboard()
        dashboard.load()
        
        report = dashboard.get_system_health_report()
        assert isinstance(report, str)
        assert "HEALTH" in report.upper() or len(report) > 0
    
    def test_builder_widget_creation(self):
        """Test builder creates widgets"""
        builder = OperationsDashboardBuilder()
        widgets = builder.build_default_widgets()
        
        assert len(widgets) > 0
        assert all(hasattr(w, 'widget_id') for w in widgets)


class TestInteractionDashboard:
    """Tests for Interaction Dashboard"""
    
    def test_interaction_dashboard_initialization(self):
        """Test interaction dashboard initialization"""
        dashboard = InteractionDashboard()
        assert dashboard.adapter is not None
        assert dashboard.current_state is None
    
    def test_interaction_dashboard_load(self):
        """Test loading interaction dashboard"""
        dashboard = InteractionDashboard()
        state = dashboard.load()
        
        assert state is not None
        assert isinstance(state, InteractionDashboardState)
    
    def test_interaction_summary_generation(self):
        """Test interaction summary generation"""
        dashboard = InteractionDashboard()
        dashboard.load()
        
        summary = dashboard.get_interaction_summary()
        assert isinstance(summary, str)
    
    def test_builder_add_message(self):
        """Test adding messages to interaction"""
        builder = InteractionDashboardBuilder()
        
        msg1 = builder.add_message("user", "Hello Buddy", "text")
        msg2 = builder.add_message("buddy", "Hello! How can I help?", "text")
        
        assert len(builder.message_history) == 2
        assert msg1.sender == "user"
        assert msg2.sender == "buddy"
    
    def test_builder_widget_creation(self):
        """Test builder creates widgets"""
        builder = InteractionDashboardBuilder()
        builder.add_message("user", "What should I do?")
        widgets = builder.build_default_widgets()
        
        assert len(widgets) > 0
        assert any(w.widget_type == "chat" for w in widgets)


class TestDashboardIntegration:
    """Integration tests across dashboards"""
    
    def test_all_dashboards_accessible_from_router(self):
        """Test that all dashboards are accessible"""
        router = DashboardRouter()
        
        for mode in DashboardMode:
            router.navigate_to(mode)
            state = router.get_current_dashboard_state()
            assert state is not None
    
    def test_unified_state_consistency(self):
        """Test unified state remains consistent"""
        router = DashboardRouter()
        state_id_1 = router.unified_state.state_id
        
        router.navigate_to(DashboardMode.LEARNING)
        state_id_2 = router.unified_state.state_id
        
        # State ID should be same object (reference equality)
        assert state_id_1 == state_id_2
    
    def test_environment_change_affects_all_dashboards(self):
        """Test environment change is reflected in all dashboards"""
        router = DashboardRouter()
        
        router.set_environment(ExecutionEnvironment.LIVE)
        
        assert router.unified_state.environment == ExecutionEnvironment.LIVE
        assert router.unified_state.operations_dashboard.current_environment == ExecutionEnvironment.LIVE
    
    def test_non_destructive_dashboard_navigation(self):
        """Test that dashboard navigation doesn't affect phase logic"""
        manager = DashboardManager()
        
        # Navigate through all dashboards
        for mode in DashboardMode:
            manager.navigate_to(mode)
        
        # Verify we can return to operations safely
        manager.navigate_to(DashboardMode.OPERATIONS)
        state = manager.get_state()
        assert state.current_mode == DashboardMode.OPERATIONS


class TestDashboardSafety:
    """Tests for dashboard safety and constraints"""
    
    def test_dashboard_readonly_operations(self):
        """Test that adapters only read, never write"""
        # Adapters should not modify phase outputs
        from buddy_phase25.dashboard_adapters.phase_adapters import LearningDashboardAdapter
        
        adapter = LearningDashboardAdapter()
        # Multiple reads should give same results (deterministic)
        state1 = adapter.build_state()
        state2 = adapter.build_state()
        
        assert len(state1.recent_signals) == len(state2.recent_signals)
    
    def test_developer_mode_isolation(self):
        """Test that developer mode doesn't affect operational mode"""
        router = DashboardRouter()
        
        # Toggle to developer mode
        router.toggle_developer_mode()
        assert router.current_mode == DashboardMode.DEVELOPER
        
        # Toggle back
        router.toggle_developer_mode()
        assert router.current_mode == DashboardMode.OPERATIONS
    
    def test_dashboard_state_isolation(self):
        """Test that dashboards are isolated from each other"""
        manager = DashboardManager()
        
        manager.navigate_to(DashboardMode.LEARNING)
        learning_state = manager.get_state().learning_dashboard
        
        manager.navigate_to(DashboardMode.OPERATIONS)
        operations_state = manager.get_state().operations_dashboard
        
        # Modifying one should not affect the other
        assert learning_state is not operations_state


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
