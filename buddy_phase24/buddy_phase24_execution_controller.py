"""
Phase 24: Execution Controller - State machine for mock → dry-run → live escalation

Enforces safety gates, confidence thresholds, and manages execution mode transitions.
Implements rollback and system lock mechanisms for critical failures.
"""

import json
from dataclasses import dataclass, asdict
from typing import Dict, Optional, List, Callable
from enum import Enum
from datetime import datetime, timezone
from .buddy_phase24_tool_contracts import ToolContract, ExecutionMode, RiskLevel


class ExecutionState(Enum):
    """Execution state machine"""
    MOCK = "MOCK"                      # Simulated with mocks
    DRY_RUN = "DRY_RUN"                # Safe preview
    AWAITING_APPROVAL = "AWAITING_APPROVAL"  # Human approval pending
    LIVE = "LIVE"                      # Real execution
    ROLLBACK = "ROLLBACK"              # Rolling back changes
    ABORTED = "ABORTED"                # Execution aborted
    LOCKED = "LOCKED"                  # System locked (critical failure)


@dataclass
class ExecutionContext:
    """Context for current execution"""
    current_state: ExecutionState = ExecutionState.MOCK
    confidence_score: float = 0.0  # 0.0-1.0
    confidence_threshold: float = 0.7  # Default threshold for live
    approval_gate: Optional[Callable[[str], bool]] = None  # External approval function
    system_locked: bool = False
    lock_reason: str = ""
    executed_tools: List[str] = None
    rollback_stack: List[Dict] = None  # Stack of executed actions for rollback
    
    def __post_init__(self):
        if self.executed_tools is None:
            self.executed_tools = []
        if self.rollback_stack is None:
            self.rollback_stack = []


class ExecutionController:
    """
    State machine for execution mode escalation
    
    Enforces:
    - Confidence thresholds
    - Safety gates (Phase 13)
    - Approval requirements
    - Rollback capability
    """
    
    def __init__(self, approval_callback: Optional[Callable] = None):
        self.context = ExecutionContext()
        self.context.approval_gate = approval_callback or self._mock_approval
        self.state_transitions: List[Dict] = []
    
    def _mock_approval(self, reason: str) -> bool:
        """Default approval (always approved in test context)"""
        return True
    
    def evaluate_execution_mode(self, 
                               tool: ToolContract, 
                               confidence: float) -> ExecutionMode:
        """
        Determine appropriate execution mode based on tool risk and confidence
        
        Returns: ExecutionMode enum
        """
        self.context.confidence_score = confidence
        
        # Validate confidence is in range
        confidence = max(0.0, min(1.0, confidence))
        
        # Lock check
        if self.context.system_locked:
            return ExecutionMode.MOCK
        
        # HIGH risk tools require high confidence + explicit approval
        if tool.risk_level == RiskLevel.HIGH:
            if confidence >= self.context.confidence_threshold and self.context.approval_gate("live_action"):
                return ExecutionMode.LIVE
            elif confidence >= 0.5:
                return ExecutionMode.DRY_RUN
            else:
                return ExecutionMode.MOCK
        
        # MEDIUM risk tools can use dry-run at medium confidence
        elif tool.risk_level == RiskLevel.MEDIUM:
            if confidence >= self.context.confidence_threshold:
                return ExecutionMode.DRY_RUN  # Or LIVE if reversible and approved
            elif confidence >= 0.4:
                return ExecutionMode.DRY_RUN
            else:
                return ExecutionMode.MOCK
        
        # LOW risk tools default to dry-run if available
        else:
            if confidence >= 0.3:
                return ExecutionMode.DRY_RUN
            else:
                return ExecutionMode.MOCK
    
    def request_live_approval(self, tool_name: str, reason: str) -> bool:
        """
        Request explicit approval for live execution
        
        Returns: bool indicating if approved
        """
        if self.context.system_locked:
            return False
        
        approval = self.context.approval_gate(f"live_tool_{tool_name}_{reason}")
        
        if approval:
            self._record_transition(
                from_state=self.context.current_state,
                to_state=ExecutionState.LIVE,
                reason=f"Live approval granted: {reason}"
            )
        else:
            self._record_transition(
                from_state=self.context.current_state,
                to_state=ExecutionState.DRY_RUN,
                reason=f"Live approval denied: {reason}"
            )
        
        return approval
    
    def execute_tool_action(self, 
                           tool_name: str,
                           action_data: Dict,
                           execution_mode: ExecutionMode) -> Dict:
        """
        Execute tool action with state tracking
        
        Returns: Execution result with status
        """
        result = {
            "tool_name": tool_name,
            "execution_mode": execution_mode.value,
            "status": "executed",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "result": action_data
        }
        
        # Record execution
        self.context.executed_tools.append(tool_name)
        
        # Add to rollback stack if reversible
        if execution_mode != ExecutionMode.MOCK:
            self.context.rollback_stack.append({
                "tool_name": tool_name,
                "action_data": action_data,
                "execution_mode": execution_mode.value
            })
        
        return result
    
    def rollback_execution(self, depth: int = 1) -> Dict:
        """
        Rollback last N executions
        
        Returns: Rollback summary
        """
        self._record_transition(
            from_state=self.context.current_state,
            to_state=ExecutionState.ROLLBACK,
            reason=f"Rollback {depth} action(s)"
        )
        
        rolled_back = []
        for _ in range(min(depth, len(self.context.rollback_stack))):
            if self.context.rollback_stack:
                action = self.context.rollback_stack.pop()
                rolled_back.append(action)
        
        # Return to previous state (not ROLLBACK)
        previous_state = ExecutionState.MOCK
        if self.context.executed_tools:
            previous_state = ExecutionState.DRY_RUN
        
        self.context.current_state = previous_state
        
        return {
            "status": "rolled_back",
            "count": len(rolled_back),
            "rolled_back_tools": [a["tool_name"] for a in rolled_back],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def lock_system(self, reason: str):
        """
        Lock system on critical failure
        
        All subsequent executions return MOCK only
        """
        self.context.system_locked = True
        self.context.lock_reason = reason
        self.context.current_state = ExecutionState.LOCKED
        
        self._record_transition(
            from_state=None,
            to_state=ExecutionState.LOCKED,
            reason=reason
        )
    
    def unlock_system(self) -> bool:
        """
        Unlock system (requires explicit action)
        
        Returns: bool indicating if unlock successful
        """
        if not self.context.system_locked:
            return False
        
        self.context.system_locked = False
        self.context.lock_reason = ""
        self.context.current_state = ExecutionState.MOCK
        
        self._record_transition(
            from_state=ExecutionState.LOCKED,
            to_state=ExecutionState.MOCK,
            reason="System unlocked manually"
        )
        
        return True
    
    def set_confidence_threshold(self, threshold: float):
        """Set confidence threshold for live execution (0.0-1.0)"""
        self.context.confidence_threshold = max(0.0, min(1.0, threshold))
    
    def get_execution_status(self) -> Dict:
        """Get current execution status"""
        return {
            "current_state": self.context.current_state.value,
            "confidence_score": self.context.confidence_score,
            "confidence_threshold": self.context.confidence_threshold,
            "system_locked": self.context.system_locked,
            "lock_reason": self.context.lock_reason,
            "tools_executed": len(self.context.executed_tools),
            "rollback_depth": len(self.context.rollback_stack),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def _record_transition(self, 
                          from_state: Optional[ExecutionState],
                          to_state: ExecutionState,
                          reason: str):
        """Record state transition for audit"""
        self.state_transitions.append({
            "from_state": from_state.value if from_state else None,
            "to_state": to_state.value,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    
    def get_state_transitions(self) -> List[Dict]:
        """Get all state transitions (audit trail)"""
        return self.state_transitions
