"""
Phase 25: Operations / Monitoring Dashboard

Real-time and historical operational awareness.
Displays active agents, tool executions, safety decisions, health metrics,
and system anomalies.
"""

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from .dashboard_state_models import (
    OperationsDashboardState, ExecutionEnvironment, ToolExecution
)
from .dashboard_adapters.phase_adapters import OperationsDashboardAdapter
from .phase24_adapters import Phase24AggregateAdapter


class OperationsDashboard:
    """
    Operations Dashboard displays:
    1. Active agents and their roles/status
    2. Real-time and recent tool executions
    3. Safety gate decisions and approvals
    4. System health score and metrics
    5. Rollbacks, retries, and anomalies
    6. Environment status (DRY_RUN, LIVE, MOCK, LOCKED)
    """
    
    def __init__(self):
        self.adapter = OperationsDashboardAdapter()
        self.phase24_adapter = Phase24AggregateAdapter()
        self.current_state: Optional[OperationsDashboardState] = None
    
    def load(self, environment: ExecutionEnvironment = ExecutionEnvironment.MOCK) -> OperationsDashboardState:
        """Load operations dashboard state"""
        self.current_state = self.adapter.build_state(environment)
        return self.current_state
    
    def get_operations_summary(self) -> str:
        """Get human-readable operations summary"""
        if not self.current_state:
            return "No operations data available"
        
        summary_parts = []
        
        # Environment
        summary_parts.append(f"🌍 Environment: {self.current_state.current_environment.value}")
        
        # Health score
        health = self.current_state.system_health
        health_emoji = "🟢" if health.health_score >= 75 else "🟡" if health.health_score >= 60 else "🔴"
        summary_parts.append(f"{health_emoji} Health: {health.health_score:.0f}/100 ({health.health_status})")
        
        # Active executions
        summary_parts.append(
            f"⚙️  Active Executions: {len(self.current_state.active_executions)} "
            f"(recent: {len(self.current_state.recent_executions)})"
        )
        
        # Active agents
        summary_parts.append(
            f"🤖 Agents: {len(self.current_state.active_agents)} active"
        )
        
        # Safety decisions
        approvals = sum(1 for s in self.current_state.recent_safety_events if s.decision == "APPROVED")
        denials = sum(1 for s in self.current_state.recent_safety_events if s.decision == "DENIED")
        summary_parts.append(f"🔐 Safety: {approvals} approved, {denials} denied")
        
        # Alerts
        if self.current_state.active_alerts:
            summary_parts.append(f"⚠️  {len(self.current_state.active_alerts)} active alerts")
        
        return " | ".join(summary_parts)
    
    def get_active_agents_table(self) -> str:
        """Generate table of active agents"""
        if not self.current_state or not self.current_state.active_agents:
            return "No active agents"
        
        lines = ["Agent ID | Role | Status | Tasks | Success Rate | Last Activity"]
        lines.append("─" * 80)
        
        for agent in self.current_state.active_agents:
            lines.append(
                f"{agent.agent_id:<8s} | "
                f"{agent.role:<10s} | "
                f"{agent.status:<9s} | "
                f"{agent.tasks_completed:>5d}  | "
                f"{agent.success_rate:>8.0%}       | "
                f"{agent.last_activity[-8:]}"
            )
        
        return "\n".join(lines)
    
    def get_tool_executions_table(self, limit: int = 20) -> str:
        """Generate table of recent tool executions"""
        executions = self.current_state.recent_executions[:limit] if self.current_state else []
        
        if not executions:
            return "No recent tool executions"
        
        lines = ["Exec ID | Tool | Agent | Env | Status | Confidence | Time (ms)"]
        lines.append("─" * 75)
        
        for exec in executions:
            status_emoji = "✓" if exec.status == "succeeded" else "✗" if exec.status == "failed" else "⏳"
            
            lines.append(
                f"{exec.execution_id[:6]} | "
                f"{exec.tool_name:<10s} | "
                f"{exec.agent_id:<6s} | "
                f"{exec.environment.value:<7s} | "
                f"{status_emoji} {exec.status:<6s} | "
                f"{exec.confidence_score:>7.0%}      | "
                f"{exec.duration_ms or 0:>7.1f}"
            )
        
        return "\n".join(lines)
    
    def get_safety_decisions_table(self, limit: int = 15) -> str:
        """Generate table of safety decisions"""
        decisions = self.current_state.recent_safety_events[:limit] if self.current_state else []
        
        if not decisions:
            return "No recent safety decisions"
        
        lines = ["Time | Tool | Risk | Decision | Reasoning"]
        lines.append("─" * 80)
        
        for decision in decisions:
            time_str = decision.timestamp[-8:] if decision.timestamp else "N/A"
            reason_trunc = (decision.reasoning[:30] + "...") if len(decision.reasoning) > 30 else decision.reasoning
            
            decision_emoji = "✓" if decision.decision == "APPROVED" else "✗" if decision.decision == "DENIED" else "⚠️"
            
            lines.append(
                f"{time_str} | "
                f"{decision.tool_name:<10s} | "
                f"{decision.risk_level:<6s} | "
                f"{decision_emoji} {decision.decision:<8s} | "
                f"{reason_trunc}"
            )
        
        return "\n".join(lines)
    
    def get_system_health_report(self) -> str:
        """Generate comprehensive system health report"""
        if not self.current_state:
            return "No health data available"
        
        health = self.current_state.system_health
        
        lines = [
            "═" * 60,
            f"SYSTEM HEALTH REPORT",
            "═" * 60,
            f"Status: {health.health_status} (Score: {health.health_score:.0f}/100)",
            f"Timestamp: {health.timestamp[-19:]}",
            "",
            "METRICS:",
        ]
        
        for metric_name, metric_value in sorted(health.metrics.items()):
            lines.append(f"  • {metric_name}: {metric_value:.2f}")
        
        if health.anomalies:
            lines.append("\nANOMALIES DETECTED:")
            for anomaly in health.anomalies:
                lines.append(f"  • {anomaly.get('anomaly_type', 'Unknown')}: {anomaly.get('description', 'No description')}")
        else:
            lines.append("\nNo anomalies detected")
        
        lines.append("═" * 60)
        
        return "\n".join(lines)
    
    def get_execution_summary_table(self) -> str:
        """Generate execution summary statistics"""
        if not self.current_state:
            return "No execution data"
        
        summary = self.current_state.execution_summary
        
        lines = [
            "EXECUTION SUMMARY",
            "─" * 40,
            f"Total Executions: {summary.get('total_executions', 0)}",
            f"Active Executions: {summary.get('active_executions', 0)}",
            f"Success Rate: {summary.get('success_rate', 0):.1%}",
            f"Environment: {summary.get('environment', 'UNKNOWN')}",
        ]
        
        return "\n".join(lines)
    
    def export_state(self, filepath: str):
        """Export dashboard state to JSON"""
        if self.current_state:
            import json
            with open(filepath, 'w') as f:
                json.dump(asdict(self.current_state), f, indent=2, default=str)


@dataclass
class OperationsDashboardWidget:
    """Individual widget in operations dashboard"""
    widget_id: str
    widget_type: str  # "chart", "table", "gauge", "alert", "metric"
    title: str
    data: Dict[str, Any]
    refresh_interval_seconds: int = 5  # Faster refresh for operations


class OperationsDashboardBuilder:
    """Builder for operations dashboard with custom widgets"""
    
    def __init__(self):
        self.dashboard = OperationsDashboard()
        self.widgets: List[OperationsDashboardWidget] = []
    
    def build_default_widgets(self, environment: ExecutionEnvironment = ExecutionEnvironment.MOCK) -> List[OperationsDashboardWidget]:
        """Build default set of widgets"""
        state = self.dashboard.load(environment)
        
        widgets = []
        
        # Health gauge
        widgets.append(OperationsDashboardWidget(
            widget_id="health_gauge",
            widget_type="gauge",
            title="System Health",
            data={
                "score": state.system_health.health_score,
                "status": state.system_health.health_status,
                "metrics": state.system_health.metrics
            },
            refresh_interval_seconds=10
        ))
        
        # Environment indicator
        widgets.append(OperationsDashboardWidget(
            widget_id="environment_indicator",
            widget_type="metric",
            title="Execution Environment",
            data={
                "current": state.current_environment.value,
                "timestamp": state.timestamp
            },
            refresh_interval_seconds=5
        ))
        
        # Active agents
        widgets.append(OperationsDashboardWidget(
            widget_id="active_agents",
            widget_type="table",
            title="Active Agents",
            data={
                "agents": [asdict(a) for a in state.active_agents]
            },
            refresh_interval_seconds=10
        ))
        
        # Tool executions
        widgets.append(OperationsDashboardWidget(
            widget_id="tool_executions",
            widget_type="table",
            title="Recent Tool Executions",
            data={
                "executions": [asdict(e) for e in state.recent_executions[:10]]
            },
            refresh_interval_seconds=5
        ))
        
        # Safety decisions
        widgets.append(OperationsDashboardWidget(
            widget_id="safety_decisions",
            widget_type="table",
            title="Safety Gate Decisions",
            data={
                "decisions": [asdict(d) for d in state.recent_safety_events[:10]]
            },
            refresh_interval_seconds=15
        ))
        
        # Phase 24: Orchestration Conflicts
        conflicts = self.phase24_adapter.conflicts.get_unresolved_conflicts()
        if conflicts:
            widgets.append(OperationsDashboardWidget(
                widget_id="phase24_conflicts",
                widget_type="alert",
                title="Orchestration Conflicts (Phase 24)",
                data={
                    "unresolved": len(conflicts),
                    "conflicts": [
                        {
                            "tools": ", ".join(c.tools_involved),
                            "type": c.conflict_type,
                            "severity": c.severity
                        }
                        for c in conflicts[:5]
                    ]
                },
                refresh_interval_seconds=10
            ))
        
        # Phase 24: Rollback Events
        recent_rollbacks = self.phase24_adapter.rollbacks.get_recent_rollbacks(limit=5)
        if recent_rollbacks:
            widgets.append(OperationsDashboardWidget(
                widget_id="phase24_rollbacks",
                widget_type="log",
                title="Recent Rollbacks (Phase 24)",
                data={
                    "rollbacks": [
                        {
                            "trigger": r.trigger,
                            "reason": r.reason,
                            "status": r.recovery_status,
                            "timestamp": r.timestamp
                        }
                        for r in recent_rollbacks
                    ]
                },
                refresh_interval_seconds=15
            ))
        
        # Alerts
        if state.active_alerts:
            widgets.append(OperationsDashboardWidget(
                widget_id="alerts",
                widget_type="alert",
                title="Active Alerts",
                data={
                    "alerts": state.active_alerts
                },
                refresh_interval_seconds=5
            ))
        
        self.widgets = widgets
        return widgets
