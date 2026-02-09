"""
Phase 25: Autonomous Multi-Agent System - Core Orchestrator

Manages goal ingestion, task execution, and cross-agent coordination.
All actions log to JSONL for audit trail and dashboard consumption.
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Union, Any
from enum import Enum
from dataclasses import dataclass, field, asdict

from backend.learning.signal_priority import apply_signal_priority


class ExecutionMode(Enum):
    """Execution safety modes"""
    MOCK = "mock"  # Simulated execution only
    DRY_RUN = "dry_run"  # Full navigation, no permanent changes
    LIVE = "live"  # Actual execution


class TaskType(Enum):
    """Task types for Phase 25"""
    SCRAPE = "scrape"
    RESEARCH = "research"
    GHL_CAMPAIGN = "ghl_campaign"
    SIDE_HUSTLE = "side_hustle"
    MARKETING = "marketing"


class TaskPriority(Enum):
    """Task priority levels"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class GoalStatus(Enum):
    """Goal lifecycle status"""
    CREATED = "created"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class Task:
    """Individual task for execution"""
    task_id: str
    goal_id: str
    task_type: TaskType
    priority: TaskPriority
    status: TaskStatus = TaskStatus.PENDING
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    target_url: Optional[str] = None
    credentials_key: Optional[str] = None
    parameters: Dict = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3
    

@dataclass(frozen=True)
class Goal:
    """Autonomous goal with approval and tracking"""
    goal_id: str
    description: str
    owner: str
    goal_type: TaskType
    status: GoalStatus = GoalStatus.CREATED
    approval_required: bool = True
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    expected_completion: Optional[str] = None
    success_metrics: Dict = field(default_factory=dict)
    progress: int = 0  # 0-100%
    tags: List[str] = field(default_factory=list)


class Phase25Orchestrator:
    """Central orchestrator for Phase 25 autonomous system"""
    
    def __init__(self, data_dir: str = "./outputs/phase25"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.goals_file = self.data_dir / "goals.jsonl"
        self.tasks_file = self.data_dir / "tasks.jsonl"
        self.execution_log = self.data_dir / "tool_execution_log.jsonl"
        self.state_transitions = self.data_dir / "execution_state_transitions.jsonl"
        self.learning_signals = self.data_dir / "learning_signals.jsonl"
    
    def ingest_goal(self, goal: Goal) -> bool:
        """Ingest a new goal for autonomous execution"""
        try:
            with open(self.goals_file, 'a') as f:
                f.write(json.dumps(asdict(goal), default=str) + '\n')
            
            # Log state transition
            self._log_state_transition(
                from_state="none",
                to_state=goal.status.value,
                trigger="goal_creation",
                details=f"Goal created: {goal.description}"
            )
            return True
        except Exception as e:
            print(f"Error ingesting goal: {e}")
            return False
    
    def create_task(self, goal_id: str, task_type: TaskType, priority: TaskPriority,
                   target_url: Optional[str] = None, parameters: Dict = None) -> Optional[str]:
        """Create a new task for a goal"""
        import uuid
        task_id = str(uuid.uuid4())[:8]
        
        task = Task(
            task_id=task_id,
            goal_id=goal_id,
            task_type=task_type,
            priority=priority,
            target_url=target_url,
            parameters=parameters or {}
        )
        
        try:
            with open(self.tasks_file, 'a') as f:
                f.write(json.dumps(asdict(task), default=str) + '\n')
            return task_id
        except Exception as e:
            print(f"Error creating task: {e}")
            return None
    
    def log_execution(self, task_id: str, tool_name: str, action_type: str,
                     status: str, data: Dict = None, duration_ms: int = 0) -> None:
        """Log tool execution for audit trail"""
        execution_record = {
            "execution_id": task_id,
            "tool_name": tool_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "duration_ms": duration_ms,
            "status": status,
            "action_type": action_type,
            "data_extracted": data or {},
            "execution_mode": "LIVE"
        }
        
        try:
            with open(self.execution_log, 'a') as f:
                f.write(json.dumps(execution_record) + '\n')
        except Exception as e:
            print(f"Error logging execution: {e}")
    
    def _log_state_transition(self, from_state: str, to_state: str, trigger: str, 
                             details: str = "") -> None:
        """Log state transitions for dashboards"""
        transition = {
            "transition_id": f"{datetime.now(timezone.utc).isoformat()}_transition",
            "from_state": from_state,
            "to_state": to_state,
            "trigger": trigger,
            "details": details,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        try:
            with open(self.state_transitions, 'a') as f:
                f.write(json.dumps(transition) + '\n')
        except Exception as e:
            print(f"Error logging transition: {e}")
    
    def log_learning_signal(self, signal_data: Union[Dict[str, Any], str], tool_name: str = None,
                           insight: str = None, confidence: float = None,
                           recommended_action: str = None) -> None:
        """Log learning signals - accepts dict (Phase 1 selector signals) or individual params (Phase 25)"""
        try:
            if isinstance(signal_data, dict):
                # Phase 1 selector signals: tag and write dict directly
                # Safety hardening: inject identifying fields if missing
                if "signal_layer" not in signal_data:
                    signal_data["signal_layer"] = "selector"
                if "signal_source" not in signal_data:
                    signal_data["signal_source"] = "web_navigator"
                
                signal_data = apply_signal_priority(signal_data)
                with open(self.learning_signals, 'a') as f:
                    f.write(json.dumps(signal_data) + '\n')
            else:
                # Phase 25 meta signals: construct from parameters
                signal = {
                    "signal_id": f"sig_{datetime.now(timezone.utc).timestamp()}",
                    "signal_type": signal_data,
                    "tool_name": tool_name,
                    "insight": insight,
                    "confidence": confidence,
                    "recommended_action": recommended_action,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                signal = apply_signal_priority(signal)
                with open(self.learning_signals, 'a') as f:
                    f.write(json.dumps(signal) + '\n')
        except Exception as e:
            print(f"Error logging signal: {e}")
    
    def get_goals(self, status: Optional[GoalStatus] = None) -> List[Dict]:
        """Retrieve goals, optionally filtered by status"""
        goals = []
        try:
            if self.goals_file.exists():
                with open(self.goals_file, 'r') as f:
                    for line in f:
                        goal_data = json.loads(line)
                        if status is None or goal_data.get('status') == status.value:
                            goals.append(goal_data)
        except Exception as e:
            print(f"Error reading goals: {e}")
        return goals
    
    def get_tasks_for_goal(self, goal_id: str) -> List[Dict]:
        """Get all tasks for a specific goal"""
        tasks = []
        try:
            if self.tasks_file.exists():
                with open(self.tasks_file, 'r') as f:
                    for line in f:
                        task_data = json.loads(line)
                        if task_data.get('goal_id') == goal_id:
                            tasks.append(task_data)
        except Exception as e:
            print(f"Error reading tasks: {e}")
        return tasks


# Global orchestrator instance
orchestrator = Phase25Orchestrator()
