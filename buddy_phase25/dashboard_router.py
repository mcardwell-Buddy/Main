"""
Phase 25: Dashboard Router

Central router that manages dashboard navigation and state transitions.
Implements unified state management for all dashboards.
"""

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timezone
from enum import Enum

from .dashboard_state_models import (
    DashboardMode, UnifiedDashboardState, LearningDashboardState,
    OperationsDashboardState, InteractionDashboardState, DeveloperModeState,
    ExecutionEnvironment
)
from .dashboard_adapters.phase_adapters import (
    LearningDashboardAdapter, OperationsDashboardAdapter,
    InteractionDashboardAdapter, DeveloperModeAdapter
)
from .phase24_adapters import Phase24AggregateAdapter


class DashboardRouter:
    """
    Central router for dashboard management and navigation.
    
    Responsibilities:
    - Dashboard state management
    - Navigation routing
    - Data refresh from phase outputs
    - Developer mode toggling
    - Event subscription/notification
    """
    
    def __init__(self, outputs_base_path: Path = Path("outputs")):
        self.outputs_base = outputs_base_path
        self.current_mode = DashboardMode.OPERATIONS  # Default dashboard
        self.unified_state = None
        self.subscribers: Dict[DashboardMode, list] = {
            mode: [] for mode in DashboardMode
        }
        self.adapters = {
            "learning": LearningDashboardAdapter(outputs_base_path),
            "operations": OperationsDashboardAdapter(outputs_base_path),
            "interaction": InteractionDashboardAdapter(outputs_base_path),
            "developer": DeveloperModeAdapter(outputs_base_path)
        }
        
        # Initialize state
        self._initialize_state()
    
    def _initialize_state(self):
        """Initialize unified dashboard state"""
        self.unified_state = UnifiedDashboardState(
            state_id=f"unified_{datetime.now(timezone.utc).isoformat()}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            current_mode=self.current_mode,
            environment=ExecutionEnvironment.MOCK
        )
    
    def refresh_dashboard(self, mode: Optional[DashboardMode] = None) -> UnifiedDashboardState:
        """
        Refresh dashboard state from phase outputs.
        
        If mode not specified, refreshes current dashboard.
        """
        target_mode = mode or self.current_mode
        
        if target_mode == DashboardMode.LEARNING:
            self.unified_state.learning_dashboard = self.adapters["learning"].build_state()
        
        elif target_mode == DashboardMode.OPERATIONS:
            self.unified_state.operations_dashboard = self.adapters["operations"].build_state(
                environment=self.unified_state.environment
            )
        
        elif target_mode == DashboardMode.INTERACTION:
            self.unified_state.interaction_dashboard = self.adapters["interaction"].build_state()
        
        elif target_mode == DashboardMode.DEVELOPER:
            self._build_developer_mode()
        
        self.unified_state.timestamp = datetime.now(timezone.utc).isoformat()
        self._notify_subscribers(target_mode)
        
        return self.unified_state
    
    def _build_developer_mode(self):
        """Build developer mode state"""
        dev_adapter = self.adapters["developer"]
        
        self.unified_state.developer_mode = DeveloperModeState(
            mode_active=True,
            phase_tabs=dev_adapter.build_phase_tabs(),
            audit_timeline=dev_adapter.build_audit_timeline()
        )
    
    def navigate_to(self, mode: DashboardMode) -> UnifiedDashboardState:
        """Navigate to specific dashboard"""
        if mode not in DashboardMode:
            raise ValueError(f"Invalid dashboard mode: {mode}")
        
        self.current_mode = mode
        self.unified_state.current_mode = mode
        
        # Refresh the dashboard being navigated to
        return self.refresh_dashboard(mode)
    
    def toggle_developer_mode(self) -> bool:
        """Toggle developer mode on/off"""
        if self.unified_state.developer_mode.mode_active:
            self.unified_state.developer_mode.mode_active = False
            self.current_mode = DashboardMode.OPERATIONS  # Return to ops
        else:
            self.unified_state.developer_mode.mode_active = True
            self.current_mode = DashboardMode.DEVELOPER
        
        self.unified_state.current_mode = self.current_mode
        return self.unified_state.developer_mode.mode_active
    
    def set_environment(self, environment: ExecutionEnvironment) -> UnifiedDashboardState:
        """Set execution environment (MOCK, DRY_RUN, LIVE, LOCKED)"""
        self.unified_state.environment = environment
        self.unified_state.operations_dashboard.current_environment = environment
        
        # Refresh operations dashboard to reflect environment change
        self.refresh_dashboard(DashboardMode.OPERATIONS)
        
        return self.unified_state
    
    def get_current_dashboard_state(self) -> Any:
        """Get state for currently active dashboard"""
        return self.unified_state.get_dashboard_state(self.current_mode)
    
    def get_unified_state(self) -> UnifiedDashboardState:
        """Get complete unified state"""
        return self.unified_state
    
    def subscribe(self, mode: DashboardMode, callback: Callable[[UnifiedDashboardState], None]):
        """Subscribe to dashboard state changes"""
        if mode not in self.subscribers:
            self.subscribers[mode] = []
        self.subscribers[mode].append(callback)
    
    def unsubscribe(self, mode: DashboardMode, callback: Callable):
        """Unsubscribe from dashboard state changes"""
        if mode in self.subscribers and callback in self.subscribers[mode]:
            self.subscribers[mode].remove(callback)
    
    def _notify_subscribers(self, mode: DashboardMode):
        """Notify all subscribers of state change"""
        for callback in self.subscribers.get(mode, []):
            try:
                callback(self.unified_state)
            except Exception as e:
                print(f"Error notifying subscriber: {e}")
    
    def export_state_json(self, filepath: Path):
        """Export current state to JSON including Phase 24 orchestration data"""
        import json
        
        export_data = {
            "dashboard_state": asdict(self.unified_state),
            "phase24_data": {}
        }
        
        # Include Phase 24 orchestration data (read-only)
        try:
            phase24_adapter = Phase24AggregateAdapter()
            
            export_data["phase24_data"] = {
                "operations_summary": phase24_adapter.get_operations_summary(),
                "learning_summary": phase24_adapter.get_learning_summary(),
                "interaction_summary": phase24_adapter.get_interaction_summary(),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception:
            # Phase 24 data not available, graceful degradation
            pass
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
    
    def export_current_dashboard_json(self, filepath: Path):
        """Export current dashboard state to JSON"""
        with open(filepath, 'w') as f:
            import json
            dashboard_state = self.get_current_dashboard_state()
            json.dump(asdict(dashboard_state) if hasattr(dashboard_state, '__dataclass_fields__') else dashboard_state, 
                     f, indent=2, default=str)


@dataclass
class DashboardNavigationEvent:
    """Event for dashboard navigation"""
    timestamp: str
    from_mode: DashboardMode
    to_mode: DashboardMode
    reason: str = ""


@dataclass
class EnvironmentChangeEvent:
    """Event for environment changes"""
    timestamp: str
    from_environment: ExecutionEnvironment
    to_environment: ExecutionEnvironment
    reason: str = ""


class DashboardEventBus:
    """Event bus for dashboard events"""
    
    def __init__(self):
        self.navigation_history: list[DashboardNavigationEvent] = []
        self.environment_changes: list[EnvironmentChangeEvent] = []
        self.listeners: Dict[str, list] = {
            "navigation": [],
            "environment": [],
            "state_change": []
        }
    
    def on_navigation(self, event: DashboardNavigationEvent):
        """Record navigation event"""
        self.navigation_history.append(event)
        for listener in self.listeners.get("navigation", []):
            listener(event)
    
    def on_environment_change(self, event: EnvironmentChangeEvent):
        """Record environment change event"""
        self.environment_changes.append(event)
        for listener in self.listeners.get("environment", []):
            listener(event)
    
    def add_listener(self, event_type: str, callback: Callable):
        """Add event listener"""
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        self.listeners[event_type].append(callback)
    
    def get_navigation_history(self) -> list[DashboardNavigationEvent]:
        """Get navigation history"""
        return self.navigation_history
    
    def get_environment_history(self) -> list[EnvironmentChangeEvent]:
        """Get environment change history"""
        return self.environment_changes


class DashboardManager:
    """High-level dashboard manager combining router and event bus"""
    
    def __init__(self, outputs_base_path: Path = Path("outputs")):
        self.router = DashboardRouter(outputs_base_path)
        self.event_bus = DashboardEventBus()
    
    def navigate_to(self, mode: DashboardMode, reason: str = "") -> UnifiedDashboardState:
        """Navigate to dashboard with event logging"""
        old_mode = self.router.current_mode
        state = self.router.navigate_to(mode)
        
        # Log navigation event
        self.event_bus.on_navigation(DashboardNavigationEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            from_mode=old_mode,
            to_mode=mode,
            reason=reason
        ))
        
        return state
    
    def set_environment(self, environment: ExecutionEnvironment, reason: str = "") -> UnifiedDashboardState:
        """Set environment with event logging"""
        old_env = self.router.unified_state.environment
        state = self.router.set_environment(environment)
        
        # Log environment change
        self.event_bus.on_environment_change(EnvironmentChangeEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            from_environment=old_env,
            to_environment=environment,
            reason=reason
        ))
        
        return state
    
    def refresh(self, mode: Optional[DashboardMode] = None) -> UnifiedDashboardState:
        """Refresh dashboard"""
        return self.router.refresh_dashboard(mode)
    
    def toggle_developer_mode(self) -> bool:
        """Toggle developer mode"""
        return self.router.toggle_developer_mode()
    
    def get_state(self) -> UnifiedDashboardState:
        """Get current unified state"""
        return self.router.get_unified_state()
    
    def get_navigation_history(self) -> list[DashboardNavigationEvent]:
        """Get navigation history"""
        return self.event_bus.get_navigation_history()
    
    def export_audit_trail(self, filepath: Path):
        """Export complete audit trail"""
        import json
        audit_trail = {
            "navigation_history": [asdict(e) for e in self.event_bus.navigation_history],
            "environment_changes": [asdict(e) for e in self.event_bus.environment_changes],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        with open(filepath, 'w') as f:
            json.dump(audit_trail, f, indent=2)
