"""
Phase 25: Dashboard State Models

Unified state representations for all three dashboards.
Read-only adapters from phase outputs to dashboard views.
"""

from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime, timezone


class DashboardMode(Enum):
    """Dashboard operation mode"""
    LEARNING = "learning"
    OPERATIONS = "operations"
    INTERACTION = "interaction"
    DEVELOPER = "developer"


class ExecutionEnvironment(Enum):
    """Execution environment state"""
    MOCK = "MOCK"
    DRY_RUN = "DRY_RUN"
    LIVE = "LIVE"
    LOCKED = "LOCKED"


@dataclass
class MetricPoint:
    """Time-series metric data point"""
    timestamp: str
    value: float
    unit: str
    source_phase: int = 0
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class LearningSignal:
    """Learning signal from Phase 16/19/24"""
    signal_id: str
    signal_type: str  # TOOL_RELIABILITY, CONFIDENCE_CALIBRATION, etc.
    source_phase: int
    tool_name: Optional[str]
    insight: str
    recommended_action: str
    confidence: float
    timestamp: str


@dataclass
class ToolExecution:
    """Single tool execution record"""
    execution_id: str
    tool_name: str
    agent_id: str
    environment: ExecutionEnvironment
    status: str  # "pending", "executing", "succeeded", "failed", "rolled_back"
    confidence_score: float
    start_time: str
    end_time: Optional[str] = None
    duration_ms: Optional[float] = None
    error_message: Optional[str] = None


@dataclass
class SafetyDecision:
    """Safety gate decision from Phase 13"""
    decision_id: str
    timestamp: str
    tool_name: str
    risk_level: str  # "LOW", "MEDIUM", "HIGH"
    decision: str  # "APPROVED", "DENIED", "ESCALATED"
    reasoning: str
    approver_phase: int


@dataclass
class ActiveAgent:
    """Active agent in system"""
    agent_id: str
    role: str  # "planner", "executor", "learner", etc.
    status: str  # "idle", "executing", "waiting"
    current_task: Optional[str]
    tasks_completed: int
    success_rate: float
    last_activity: str


@dataclass
class SystemHealthMetrics:
    """System-wide health snapshot"""
    health_score: float  # 0-100
    health_status: str  # "EXCELLENT", "GOOD", "FAIR", "POOR"
    timestamp: str
    metrics: Dict[str, float] = field(default_factory=dict)
    anomalies: List[Dict[str, Any]] = field(default_factory=list)
    environment: ExecutionEnvironment = ExecutionEnvironment.MOCK


@dataclass
class ConfidenceTrajectory:
    """Confidence metrics over time"""
    metric_points: List[MetricPoint] = field(default_factory=list)
    current_confidence: float = 0.5
    average_confidence: float = 0.5
    confidence_trend: str = "stable"  # "increasing", "decreasing", "stable"
    by_phase: Dict[int, float] = field(default_factory=dict)


@dataclass
class LearningDashboardState:
    """State for Learning Dashboard"""
    dashboard_id: str
    timestamp: str
    
    # Learning signals
    recent_signals: List[LearningSignal] = field(default_factory=list)
    signals_by_phase: Dict[int, List[LearningSignal]] = field(default_factory=dict)
    signals_by_type: Dict[str, List[LearningSignal]] = field(default_factory=dict)
    
    # Confidence tracking
    confidence_trajectory: ConfidenceTrajectory = field(default_factory=ConfidenceTrajectory)
    
    # Tool performance
    tool_metrics: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    # Strategy evolution
    strategy_updates: List[Dict[str, Any]] = field(default_factory=list)
    
    # Improvement chains
    failure_to_insight_chains: List[Dict[str, Any]] = field(default_factory=list)
    
    # Summary
    learning_summary: str = ""


@dataclass
class OperationsDashboardState:
    """State for Operations/Monitoring Dashboard"""
    dashboard_id: str
    timestamp: str
    
    # Active agents
    active_agents: List[ActiveAgent] = field(default_factory=list)
    
    # Tool executions
    active_executions: List[ToolExecution] = field(default_factory=list)
    recent_executions: List[ToolExecution] = field(default_factory=list)
    
    # Safety events
    safety_decisions: List[SafetyDecision] = field(default_factory=list)
    recent_safety_events: List[SafetyDecision] = field(default_factory=list)
    
    # System health
    system_health: SystemHealthMetrics = field(default_factory=SystemHealthMetrics)
    
    # Environment
    current_environment: ExecutionEnvironment = ExecutionEnvironment.MOCK
    
    # Anomalies & alerts
    active_alerts: List[Dict[str, Any]] = field(default_factory=list)
    recent_rollbacks: List[Dict[str, Any]] = field(default_factory=list)
    
    # Execution summary
    execution_summary: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskRequest:
    """Task submission request"""
    request_id: str
    timestamp: str
    description: str
    context: Dict[str, Any]
    required_approvals: List[str] = field(default_factory=list)
    priority: str = "normal"


@dataclass
class ApprovalPrompt:
    """Approval request prompt"""
    prompt_id: str
    timestamp: str
    tool_name: str
    risk_level: str
    context: str
    recommended_action: str
    requires_confirmation: bool


@dataclass
class InteractionDashboardState:
    """State for Interaction Dashboard"""
    dashboard_id: str
    timestamp: str
    
    # Chat/conversation
    chat_history: List[Dict[str, str]] = field(default_factory=list)
    
    # Task management
    task_requests: List[TaskRequest] = field(default_factory=list)
    active_tasks: List[TaskRequest] = field(default_factory=list)
    completed_tasks: List[TaskRequest] = field(default_factory=list)
    
    # Approval state
    pending_approvals: List[ApprovalPrompt] = field(default_factory=list)
    recent_approvals: List[Dict[str, Any]] = field(default_factory=list)
    
    # Contextual explanations
    last_action_explanation: Optional[str] = None
    pending_clarifications: List[str] = field(default_factory=list)
    
    # Execution feedback
    recent_feedback: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class DeveloperModeState:
    """State for Developer/Audit Mode"""
    mode_active: bool = False
    
    # Phase data
    phase_tabs: Dict[int, Dict[str, Any]] = field(default_factory=dict)
    
    # Raw streams
    jsonl_streams: Dict[str, List[str]] = field(default_factory=dict)
    
    # Verification reports
    verification_reports: List[Dict[str, Any]] = field(default_factory=list)
    
    # Test execution views
    test_results: Dict[str, Any] = field(default_factory=dict)
    
    # Audit timeline
    audit_timeline: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class UnifiedDashboardState:
    """Unified state for all dashboards"""
    state_id: str
    timestamp: str
    current_mode: DashboardMode
    
    # Individual dashboard states
    learning_dashboard: LearningDashboardState = field(default_factory=LearningDashboardState)
    operations_dashboard: OperationsDashboardState = field(default_factory=OperationsDashboardState)
    interaction_dashboard: InteractionDashboardState = field(default_factory=InteractionDashboardState)
    
    # Developer mode
    developer_mode: DeveloperModeState = field(default_factory=DeveloperModeState)
    
    # Global context
    environment: ExecutionEnvironment = ExecutionEnvironment.MOCK
    user_context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    def get_dashboard_state(self, mode: DashboardMode) -> Any:
        """Get state for specific dashboard mode"""
        if mode == DashboardMode.LEARNING:
            return self.learning_dashboard
        elif mode == DashboardMode.OPERATIONS:
            return self.operations_dashboard
        elif mode == DashboardMode.INTERACTION:
            return self.interaction_dashboard
        elif mode == DashboardMode.DEVELOPER:
            return self.developer_mode
        return None
