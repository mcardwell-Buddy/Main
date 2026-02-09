"""
Phase 25: Interaction Dashboard

Human-facing control surface for intent, approval, and collaboration.
Supports chat-based interaction, task submission, approvals, and execution summaries.
"""

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from .dashboard_state_models import (
    InteractionDashboardState, TaskRequest, ApprovalPrompt
)
from .dashboard_adapters.phase_adapters import InteractionDashboardAdapter
from .phase24_adapters import Phase24AggregateAdapter


class InteractionDashboard:
    """
    Interaction Dashboard displays:
    1. Chat-based interaction interface
    2. Task submission and previews
    3. Approval prompts with context
    4. Execution summaries and feedback
    5. Contextual explanations ("why Buddy did this")
    """
    
    def __init__(self):
        self.adapter = InteractionDashboardAdapter()
        self.phase24_adapter = Phase24AggregateAdapter()
        self.current_state: Optional[InteractionDashboardState] = None
    
    def load(self) -> InteractionDashboardState:
        """Load interaction dashboard state"""
        self.current_state = self.adapter.build_state()
        return self.current_state
    
    def get_interaction_summary(self) -> str:
        """Get human-readable interaction summary"""
        if not self.current_state:
            return "No interaction data available"
        
        summary_parts = []
        
        # Pending approvals
        if self.current_state.pending_approvals:
            summary_parts.append(f"⏳ {len(self.current_state.pending_approvals)} pending approvals")
        
        # Active tasks
        if self.current_state.active_tasks:
            summary_parts.append(f"📋 {len(self.current_state.active_tasks)} active tasks")
        
        # Completed tasks
        if self.current_state.completed_tasks:
            summary_parts.append(f"✓ {len(self.current_state.completed_tasks)} completed")
        
        # Pending clarifications
        if self.current_state.pending_clarifications:
            summary_parts.append(f"❓ {len(self.current_state.pending_clarifications)} pending clarifications")
        
        # Last action
        if self.current_state.last_action_explanation:
            summary_parts.append(f"📝 Last Action: {self.current_state.last_action_explanation[:50]}")
        
        return " | ".join(summary_parts) if summary_parts else "No pending interactions"
    
    def get_pending_approvals_display(self) -> str:
        """Display pending approval prompts"""
        if not self.current_state or not self.current_state.pending_approvals:
            return "No pending approvals"
        
        lines = ["PENDING APPROVALS", "=" * 70]
        
        for i, approval in enumerate(self.current_state.pending_approvals, 1):
            lines.append(f"\n#{i} - {approval.tool_name.upper()}")
            lines.append(f"Risk Level: {approval.risk_level}")
            lines.append(f"Context: {approval.context[:70]}")
            lines.append(f"Recommendation: {approval.recommended_action[:70]}")
            if approval.requires_confirmation:
                lines.append("Status: ⏳ REQUIRES CONFIRMATION")
            else:
                lines.append("Status: 📋 INFORMATIONAL")
        
        return "\n".join(lines)
    
    def get_active_tasks_display(self) -> str:
        """Display active tasks"""
        if not self.current_state or not self.current_state.active_tasks:
            return "No active tasks"
        
        lines = ["ACTIVE TASKS", "=" * 70]
        
        for i, task in enumerate(self.current_state.active_tasks, 1):
            lines.append(f"\n#{i} - {task.description[:50]}")
            lines.append(f"Priority: {task.priority}")
            lines.append(f"Requested: {task.timestamp[-19:]}")
            if task.required_approvals:
                lines.append(f"Approvals Needed: {', '.join(task.required_approvals)}")
        
        return "\n".join(lines)
    
    def get_task_preview(self, task: TaskRequest) -> str:
        """Generate preview of task before execution"""
        lines = [
            "TASK PREVIEW",
            "=" * 70,
            f"Description: {task.description}",
            f"Priority: {task.priority}",
            "",
            "Context:",
        ]
        
        for key, value in task.context.items():
            value_str = str(value)[:60]
            lines.append(f"  • {key}: {value_str}")
        
        if task.required_approvals:
            lines.append(f"\nRequired Approvals: {', '.join(task.required_approvals)}")
        
        return "\n".join(lines)
    
    def get_last_action_explanation(self) -> str:
        """Get explanation of last action taken"""
        if not self.current_state or not self.current_state.last_action_explanation:
            return "No recent action to explain"
        
        return self.current_state.last_action_explanation
    
    def get_execution_feedback_summary(self) -> str:
        """Get summary of recent execution feedback"""
        if not self.current_state or not self.current_state.recent_feedback:
            return "No recent feedback"
        
        lines = ["RECENT EXECUTION FEEDBACK", "─" * 70]
        
        for feedback in self.current_state.recent_feedback[:10]:
            lines.append(f"\n• {feedback.get('title', 'Feedback')}")
            lines.append(f"  Status: {feedback.get('status', 'unknown')}")
            if feedback.get('message'):
                message_trunc = feedback.get('message', '')[:60]
                lines.append(f"  Details: {message_trunc}")
        
        return "\n".join(lines)
    
    def get_pending_clarifications_display(self) -> str:
        """Display pending clarification requests"""
        if not self.current_state or not self.current_state.pending_clarifications:
            return "No pending clarifications"
        
        lines = ["PENDING CLARIFICATIONS", "─" * 70]
        
        for i, clarification in enumerate(self.current_state.pending_clarifications, 1):
            lines.append(f"\n{i}. {clarification}")
        
        return "\n".join(lines)
    
    def export_state(self, filepath: str):
        """Export dashboard state to JSON"""
        if self.current_state:
            import json
            with open(filepath, 'w') as f:
                json.dump(asdict(self.current_state), f, indent=2, default=str)


@dataclass
class InteractionMessage:
    """Single chat message"""
    message_id: str
    timestamp: str
    sender: str  # "user", "buddy", "system"
    content: str
    message_type: str = "text"  # "text", "approval_request", "task_preview", "feedback"


@dataclass
class InteractionDashboardWidget:
    """Individual widget in interaction dashboard"""
    widget_id: str
    widget_type: str  # "chat", "task_list", "approvals", "feedback"
    title: str
    data: Dict[str, Any]
    refresh_interval_seconds: int = 5


class InteractionDashboardBuilder:
    """Builder for interaction dashboard with custom widgets"""
    
    def __init__(self):
        self.dashboard = InteractionDashboard()
        self.widgets: List[InteractionDashboardWidget] = []
        self.message_history: List[InteractionMessage] = []
    
    def add_message(self, sender: str, content: str, message_type: str = "text") -> InteractionMessage:
        """Add message to chat history"""
        message = InteractionMessage(
            message_id=f"msg_{len(self.message_history)}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            sender=sender,
            content=content,
            message_type=message_type
        )
        self.message_history.append(message)
        return message
    
    def build_default_widgets(self) -> List[InteractionDashboardWidget]:
        """Build default set of widgets"""
        state = self.dashboard.load()
        
        widgets = []
        
        # Chat interface
        widgets.append(InteractionDashboardWidget(
            widget_id="chat_interface",
            widget_type="chat",
            title="Chat with Buddy",
            data={
                "messages": [asdict(m) for m in self.message_history[-20:]]
            },
            refresh_interval_seconds=2
        ))
        
        # Pending approvals
        if state.pending_approvals:
            widgets.append(InteractionDashboardWidget(
                widget_id="pending_approvals",
                widget_type="approvals",
                title="Pending Approvals",
                data={
                    "approvals": [asdict(a) for a in state.pending_approvals]
                },
                refresh_interval_seconds=5
            ))
        
        # Active tasks
        if state.active_tasks or state.task_requests:
            widgets.append(InteractionDashboardWidget(
                widget_id="task_list",
                widget_type="task_list",
                title="Tasks",
                data={
                    "active": [asdict(t) for t in state.active_tasks],
                    "requested": [asdict(t) for t in state.task_requests]
                },
                refresh_interval_seconds=10
            ))
        
        # Execution feedback
        if state.recent_feedback:
            widgets.append(InteractionDashboardWidget(
                widget_id="feedback",
                widget_type="feedback",
                title="Recent Feedback",
                data={
                    "feedback": state.recent_feedback[:10]
                },
                refresh_interval_seconds=15
            ))
        
        # Clarifications
        if state.pending_clarifications:
            widgets.append(InteractionDashboardWidget(
                widget_id="clarifications",
                widget_type="text",
                title="Pending Clarifications",
                data={
                    "clarifications": state.pending_clarifications
                },
                refresh_interval_seconds=20
            ))
        
        # Phase 24: Execution previews with risk levels
        try:
            execution_summary = self.dashboard.phase24_adapter.get_operations_summary()
            if execution_summary and "recent_executions" in execution_summary:
                widgets.append(InteractionDashboardWidget(
                    widget_id="phase24_execution_preview",
                    widget_type="execution_preview",
                    title="Execution Context",
                    data={
                        "execution_mode": execution_summary.get("execution_mode", "LIVE"),
                        "recent_executions": execution_summary.get("recent_executions", [])[:5],
                        "system_health": execution_summary.get("health_score", 0),
                        "active_tools": execution_summary.get("active_tools", 0)
                    },
                    refresh_interval_seconds=3
                ))
        except Exception:
            pass  # Phase 24 data not available, graceful degradation
        
        # Phase 24: Approval context and safety decisions
        try:
            interaction_summary = self.dashboard.phase24_adapter.get_interaction_summary()
            if interaction_summary and "pending_approvals" in interaction_summary:
                widgets.append(InteractionDashboardWidget(
                    widget_id="phase24_approval_context",
                    widget_type="approval_context",
                    title="Safety Context",
                    data={
                        "pending_approvals": interaction_summary.get("pending_approvals", 0),
                        "blocked_by_safety": interaction_summary.get("blocked_by_safety", 0),
                        "recent_conflicts": interaction_summary.get("recent_conflicts", [])[:3],
                        "rollback_summary": interaction_summary.get("rollback_summary", {})
                    },
                    refresh_interval_seconds=5
                ))
        except Exception:
            pass  # Phase 24 data not available, graceful degradation
        
        # Phase 24: Rollback explanations
        try:
            rollback_adapter = self.dashboard.phase24_adapter.rollback_adapter
            recent_rollbacks = rollback_adapter.get_recent_rollbacks(limit=5)
            if recent_rollbacks:
                widgets.append(InteractionDashboardWidget(
                    widget_id="phase24_rollback_explanation",
                    widget_type="rollback_explanation",
                    title="Recent Rollback Context",
                    data={
                        "rollbacks": [
                            {
                                "rollback_id": rb.rollback_id,
                                "trigger": rb.trigger,
                                "reason": rb.reason,
                                "recovery_status": rb.recovery_status,
                                "duration_ms": rb.duration_ms,
                                "affected_count": len(rb.affected_executions)
                            }
                            for rb in recent_rollbacks
                        ]
                    },
                    refresh_interval_seconds=10
                ))
        except Exception:
            pass  # Phase 24 data not available, graceful degradation
        
        self.widgets = widgets
        return widgets
