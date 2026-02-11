"""
Phase 8: Phase25 Integration Bridge

Connects the mission execution system to the Phase25 autonomous multi-agent orchestrator.
Enables routing missions to Phase25 for:
- Multi-agent execution
- Goal planning
- Task orchestration
- Autonomous coordination

Integration Points:
- Mission → Goal creation
- Execution context → Task parameters
- Outcome → Learning signals
"""

from typing import Dict, Any, Optional, List
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)


class Phase25MissionBridge:
    """Bridges missions to Phase25 autonomous multi-agent execution."""
    
    def __init__(self, orchestrator):
        """
        Initialize bridge with Phase25 orchestrator.
        
        Args:
            orchestrator: Phase25Orchestrator instance
        """
        self.orchestrator = orchestrator
    
    def mission_to_goal(
        self,
        mission_id: str,
        objective: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Convert a mission to a Phase25 goal for autonomous execution.
        
        Args:
            mission_id: Mission identifier
            objective: Mission objective/description
            context: Mission context (tools, parameters, etc.)
        
        Returns:
            goal_id if successful, None if failed
        """
        try:
            from Back_End.phase25_orchestrator import Goal, ExecutionMode, GoalStatus
            
            goal_id = str(uuid4())[:12]
            
            # Create goal with mission context
            goal = Goal(
                goal_id=goal_id,
                description=objective,
                status=GoalStatus.PENDING.value if hasattr(GoalStatus, 'PENDING') else "pending",
                created_at=None,  # Will be set by orchestrator
                execution_mode=ExecutionMode.DRY_RUN.value if hasattr(ExecutionMode, 'DRY_RUN') else "dry_run",
                context={
                    "mission_id": mission_id,
                    "objective": objective,
                    **(context or {})
                }
            )
            
            # Ingest goal into Phase25
            success = self.orchestrator.ingest_goal(goal)
            
            if success:
                logger.info(f"[PHASE25_BRIDGE] Mission {mission_id} → Goal {goal_id}")
                return goal_id
            else:
                logger.error(f"[PHASE25_BRIDGE] Failed to ingest goal for mission {mission_id}")
                return None
        except Exception as e:
            logger.error(f"[PHASE25_BRIDGE] Error converting mission to goal: {e}")
            return None
    
    def create_execution_task(
        self,
        goal_id: str,
        mission_id: str,
        task_description: str,
        tool_name: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        priority: str = "NORMAL",
    ) -> Optional[str]:
        """
        Create a Phase25 task for goal execution.
        
        Args:
            goal_id: Parent goal ID
            mission_id: Associated mission
            task_description: Task description
            tool_name: Tool to use (optional)
            parameters: Tool parameters
            priority: Task priority (HIGH, NORMAL, LOW)
        
        Returns:
            task_id if successful, None if failed
        """
        try:
            from Back_End.phase25_orchestrator import TaskType, TaskPriority
            
            # Map priority string to enum
            priority_map = {
                "HIGH": TaskPriority.HIGH.value if hasattr(TaskPriority, 'HIGH') else "high",
                "NORMAL": TaskPriority.NORMAL.value if hasattr(TaskPriority, 'NORMAL') else "normal",
                "LOW": TaskPriority.LOW.value if hasattr(TaskPriority, 'LOW') else "low",
            }
            mapped_priority = priority_map.get(priority, "normal")
            
            # Determine task type based on tool
            task_type_map = {
                "web_search": TaskType.SEARCH.value if hasattr(TaskType, 'SEARCH') else "search",
                "web_extract": TaskType.EXTRACT.value if hasattr(TaskType, 'EXTRACT') else "extract",
                "calculate": TaskType.ANALYZE.value if hasattr(TaskType, 'ANALYZE') else "analyze",
            }
            task_type = task_type_map.get(tool_name, "execute")
            
            # Create task
            task_id = self.orchestrator.create_task(
                goal_id=goal_id,
                task_type=task_type,
                priority=mapped_priority,
                target_url=parameters.get("url") if parameters else None,
                parameters={
                    "mission_id": mission_id,
                    "tool_name": tool_name,
                    "description": task_description,
                    **(parameters or {})
                }
            )
            
            if task_id:
                logger.info(f"[PHASE25_BRIDGE] Created task {task_id} for goal {goal_id}")
                return task_id
            else:
                logger.error(f"[PHASE25_BRIDGE] Failed to create task for goal {goal_id}")
                return None
        except Exception as e:
            logger.error(f"[PHASE25_BRIDGE] Error creating execution task: {e}")
            return None
    
    def log_task_execution(
        self,
        task_id: str,
        tool_name: str,
        action_type: str,
        status: str,
        result: Optional[Dict[str, Any]] = None,
        duration_ms: int = 0,
    ) -> bool:
        """
        Log task execution to Phase25 for audit trail.
        
        Args:
            task_id: Task identifier
            tool_name: Tool that executed
            action_type: Type of action (execute, retry, etc.)
            status: Execution status (success, failed, retrying)
            result: Execution result data
            duration_ms: Execution duration in milliseconds
        
        Returns:
            True if logged successfully
        """
        try:
            self.orchestrator.log_execution(
                task_id=task_id,
                tool_name=tool_name,
                action_type=action_type,
                status=status,
                data=result or {},
                duration_ms=duration_ms,
            )
            logger.info(f"[PHASE25_BRIDGE] Logged execution for task {task_id}: {status}")
            return True
        except Exception as e:
            logger.error(f"[PHASE25_BRIDGE] Error logging task execution: {e}")
            return False
    
    def log_learning_signal(
        self,
        tool_name: str,
        signal_type: str,
        insight: str,
        confidence: float,
        recommended_action: str,
    ) -> bool:
        """
        Log learning signal from mission execution.
        
        Args:
            tool_name: Tool that generated signal
            signal_type: Type of signal (success, efficiency, safety, etc.)
            insight: Description of insight
            confidence: Confidence score (0-1)
            recommended_action: Recommended next action
        
        Returns:
            True if logged successfully
        """
        try:
            self.orchestrator.log_learning_signal(
                signal_data=signal_type,
                tool_name=tool_name,
                insight=insight,
                confidence=confidence,
                recommended_action=recommended_action,
            )
            logger.info(f"[PHASE25_BRIDGE] Logged learning signal: {signal_type} ({confidence:.2f})")
            return True
        except Exception as e:
            logger.error(f"[PHASE25_BRIDGE] Error logging learning signal: {e}")
            return False
    
    def get_goal_status(self, goal_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current status of a goal.
        
        Args:
            goal_id: Goal identifier
        
        Returns:
            Goal status dict or None
        """
        try:
            goals = self.orchestrator.get_goals()
            for goal in goals:
                if goal.get("goal_id") == goal_id:
                    return goal
            logger.warning(f"[PHASE25_BRIDGE] Goal {goal_id} not found")
            return None
        except Exception as e:
            logger.error(f"[PHASE25_BRIDGE] Error retrieving goal status: {e}")
            return None
    
    def get_goal_tasks(self, goal_id: str) -> List[Dict[str, Any]]:
        """
        Get all tasks for a goal.
        
        Args:
            goal_id: Goal identifier
        
        Returns:
            List of task dicts
        """
        try:
            return self.orchestrator.get_tasks_for_goal(goal_id)
        except Exception as e:
            logger.error(f"[PHASE25_BRIDGE] Error retrieving goal tasks: {e}")
            return []


# Global bridge instance
_phase25_bridge: Optional[Phase25MissionBridge] = None


def get_phase25_bridge(orchestrator=None) -> Phase25MissionBridge:
    """
    Get or create the Phase25 mission bridge.
    
    Args:
        orchestrator: Phase25Orchestrator instance (for initialization)
    
    Returns:
        Phase25MissionBridge instance
    """
    global _phase25_bridge
    
    if _phase25_bridge is None:
        if orchestrator is None:
            try:
                from Back_End.phase25_orchestrator import orchestrator as default_orchestrator
                orchestrator = default_orchestrator
            except ImportError:
                from phase25_orchestrator import orchestrator as default_orchestrator
                orchestrator = default_orchestrator
        
        _phase25_bridge = Phase25MissionBridge(orchestrator)
        logger.info("[PHASE25_BRIDGE] Initialized")
    
    return _phase25_bridge


logger.info("[PHASE25_BRIDGE] Module loaded")
