"""
================================================================================
PHASE 2: APPROVAL GATES SYSTEM
================================================================================

Purpose: Determine execution path based on confidence level.
  - High Confidence (>=0.85): Execute tools immediately
  - Medium Confidence (0.55-0.85): Request user approval before execution
  - Low Confidence (<0.55): Clarify or reject

Reference: PHASE_2_DESIGN_DOCUMENT.md - Section 3

Key Constraint: Tool execution requires (confidence >= 0.85) OR (approval_granted).
                No autonomy escalation - stays Level 2 with approval.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid


class ApprovalState(Enum):
    """Current state of approval workflow."""
    NONE = "none"  # No approval needed
    AWAITING_APPROVAL = "awaiting_approval"  # Waiting for user to approve
    APPROVED = "approved"  # User approved
    DENIED = "denied"  # User denied
    TIMEOUT = "timeout"  # Approval request timed out


class ExecutionPath(Enum):
    """Path taken through approval gates."""
    HIGH_CONFIDENCE = "high_confidence"  # >= 0.85, execute immediately
    APPROVED = "approved"  # Approval granted, execute
    SUGGESTED = "suggested"  # Suggestion only, no execution
    CLARIFICATION = "clarification"  # Ask for clarification
    REJECTED = "rejected"  # Cannot execute, no action


@dataclass
class ApprovalRequest:
    """Request sent to user for approval."""
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    goal: str = ""
    confidence: float = 0.0
    reasoning_summary: str = ""
    tools_proposed: List[str] = field(default_factory=list)
    tool_descriptions: Dict[str, str] = field(default_factory=dict)
    risks: List[str] = field(default_factory=list)
    alternatives: List[str] = field(default_factory=list)
    time_limit_seconds: int = 300  # 5 minute default
    approval_callback_url: str = ""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON serialization."""
        return {
            'request_id': self.request_id,
            'goal': self.goal,
            'confidence': self.confidence,
            'reasoning_summary': self.reasoning_summary,
            'tools_proposed': self.tools_proposed,
            'tool_descriptions': self.tool_descriptions,
            'risks': self.risks,
            'alternatives': self.alternatives,
            'time_limit_seconds': self.time_limit_seconds,
            'approval_callback_url': self.approval_callback_url,
            'timestamp': self.timestamp,
        }


@dataclass
class ApprovalResponse:
    """Response from user to approval request."""
    request_id: str
    approved: bool
    feedback: str = ""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    approver_id: str = ""
    conditions: List[str] = field(default_factory=list)


@dataclass
class ApprovalGateDecision:
    """Decision made by approval gates."""
    execution_path: ExecutionPath
    approval_state: ApprovalState
    should_execute: bool  # True if tools should be executed
    approval_request: Optional[ApprovalRequest] = None
    explanation: str = ""
    clarification_needed: bool = False


class ApprovalGates:
    """
    Gate Logic:
    
    GATE 1: High Confidence (>=0.85)
      - Execute tools immediately
      - No approval needed
      - Return execution_path='high_confidence'
    
    GATE 2: Medium Confidence (0.55-0.85)
      - Generate approval request
      - Send to Soul system
      - Block execution until approval
      - Return execution_path='approved' (after approval)
    
    GATE 3: Low Confidence (<0.55)
      - IF ambiguous: generate clarification questions
      - ELSE: reject
      - Return execution_path='suggested' or 'rejected'
    
    Configuration (tunable):
      - HIGH_CONFIDENCE_THRESHOLD: default 0.85
      - MEDIUM_CONFIDENCE_THRESHOLD: default 0.55
      - APPROVAL_TIMEOUT_SECONDS: default 300
    """
    
    HIGH_CONFIDENCE_THRESHOLD = 0.85
    MEDIUM_CONFIDENCE_THRESHOLD = 0.55
    APPROVAL_TIMEOUT_SECONDS = 300
    
    def __init__(
        self,
        soul_integration=None,
        high_confidence_threshold: float = 0.85,
        medium_confidence_threshold: float = 0.55,
        approval_timeout_seconds: int = 300,
    ):
        """
        Initialize approval gates.
        
        Args:
            soul_integration: Soul system interface for approval callbacks
            high_confidence_threshold: Minimum confidence for auto-execution
            medium_confidence_threshold: Minimum confidence for approval request
            approval_timeout_seconds: How long to wait for approval
        """
        self.soul = soul_integration
        self.HIGH_CONFIDENCE_THRESHOLD = high_confidence_threshold
        self.MEDIUM_CONFIDENCE_THRESHOLD = medium_confidence_threshold
        self.APPROVAL_TIMEOUT_SECONDS = approval_timeout_seconds
        
        # In-memory storage (in production: use Soul system)
        self._pending_approvals: Dict[str, ApprovalRequest] = {}
        self._approval_decisions: Dict[str, ApprovalResponse] = {}
    
    def decide(
        self,
        confidence: float,
        goal: str,
        reasoning_summary: str = "",
        tools_proposed: List[str] = None,
        is_ambiguous: bool = False,
    ) -> ApprovalGateDecision:
        """
        Decide execution path based on confidence.
        
        Args:
            confidence: Graded confidence (0.0-1.0)
            goal: User's goal
            reasoning_summary: Agent's reasoning
            tools_proposed: List of tool names
            is_ambiguous: Whether goal is ambiguous (needs clarification)
        
        Returns:
            ApprovalGateDecision with execution path and approval status
        """
        tools_proposed = tools_proposed or []
        
        # GATE 1: High Confidence - Execute immediately
        if confidence >= self.HIGH_CONFIDENCE_THRESHOLD:
            return ApprovalGateDecision(
                execution_path=ExecutionPath.HIGH_CONFIDENCE,
                approval_state=ApprovalState.NONE,
                should_execute=True,
                explanation=f"Confidence {confidence:.2f} >= {self.HIGH_CONFIDENCE_THRESHOLD}. Executing immediately.",
            )
        
        # GATE 2: Medium Confidence - Request approval
        elif confidence >= self.MEDIUM_CONFIDENCE_THRESHOLD:
            approval_request = self._create_approval_request(
                goal=goal,
                confidence=confidence,
                reasoning_summary=reasoning_summary,
                tools_proposed=tools_proposed,
            )
            
            return ApprovalGateDecision(
                execution_path=ExecutionPath.APPROVED,
                approval_state=ApprovalState.AWAITING_APPROVAL,
                should_execute=False,
                approval_request=approval_request,
                explanation=f"Confidence {confidence:.2f} is medium. Requesting user approval.",
            )
        
        # GATE 3: Low Confidence - Clarify or reject
        else:
            if is_ambiguous:
                return ApprovalGateDecision(
                    execution_path=ExecutionPath.CLARIFICATION,
                    approval_state=ApprovalState.NONE,
                    should_execute=False,
                    explanation=f"Confidence {confidence:.2f} is low and goal is ambiguous. Requesting clarification.",
                    clarification_needed=True,
                )
            else:
                return ApprovalGateDecision(
                    execution_path=ExecutionPath.REJECTED,
                    approval_state=ApprovalState.NONE,
                    should_execute=False,
                    explanation=f"Confidence {confidence:.2f} is low. Cannot execute.",
                )
    
    def _create_approval_request(
        self,
        goal: str,
        confidence: float,
        reasoning_summary: str,
        tools_proposed: List[str],
    ) -> ApprovalRequest:
        """Create structured approval request."""
        # Identify risks
        risks = self._identify_risks(tools_proposed)
        
        # Generate alternatives
        alternatives = self._generate_alternatives(goal, tools_proposed)
        
        # Create tool descriptions
        tool_descriptions = {
            tool: f"Tool: {tool}" for tool in tools_proposed
        }
        
        return ApprovalRequest(
            goal=goal,
            confidence=confidence,
            reasoning_summary=reasoning_summary,
            tools_proposed=tools_proposed,
            tool_descriptions=tool_descriptions,
            risks=risks,
            alternatives=alternatives,
            time_limit_seconds=self.APPROVAL_TIMEOUT_SECONDS,
        )
    
    @staticmethod
    def _identify_risks(tools: List[str]) -> List[str]:
        """Identify potential risks of executing tools."""
        risks = []
        
        if not tools:
            return risks
        
        # Risk: Modifying state
        state_modifying_tools = {'button_clicker', 'file_writer', 'deleter'}
        if any(t in state_modifying_tools for t in tools):
            risks.append("Execution may modify system state")
        
        # Risk: Side effects
        if len(tools) > 1:
            risks.append("Multiple tools may have side effects")
        
        return risks
    
    @staticmethod
    def _generate_alternatives(goal: str, tools: List[str]) -> List[str]:
        """Generate alternative approaches."""
        return [
            "Review the goal with more context before executing",
            "Ask for clarification instead of proceeding",
            "Use read-only tools first to gather information",
        ]
    
    def submit_approval(
        self,
        request_id: str,
        approved: bool,
        feedback: str = "",
        approver_id: str = "",
    ) -> ApprovalResponse:
        """
        Submit an approval decision.
        
        Args:
            request_id: ID of approval request
            approved: True if approved, False if denied
            feedback: Optional feedback from approver
            approver_id: ID of user who made decision
        
        Returns:
            ApprovalResponse confirmation
        """
        response = ApprovalResponse(
            request_id=request_id,
            approved=approved,
            feedback=feedback,
            approver_id=approver_id,
        )
        
        self._approval_decisions[request_id] = response
        
        # In production: store in Soul system
        if self.soul:
            self.soul.store_approval_decision(response)
        
        return response
    
    def get_approval_status(self, request_id: str) -> Optional[ApprovalResponse]:
        """
        Check if approval decision has been made.
        
        Args:
            request_id: ID of approval request
        
        Returns:
            ApprovalResponse if decision made, None if still waiting
        """
        return self._approval_decisions.get(request_id)
    
    def check_approval_timeout(
        self,
        approval_request: ApprovalRequest,
    ) -> bool:
        """
        Check if approval request has timed out.
        
        Args:
            approval_request: The approval request to check
        
        Returns:
            True if timed out, False if still valid
        """
        # Parse timestamp
        request_time = datetime.fromisoformat(approval_request.timestamp)
        elapsed = (datetime.utcnow() - request_time).total_seconds()
        
        return elapsed > approval_request.time_limit_seconds


# =============================================================================
# EXAMPLES FOR TESTING
# =============================================================================

def example_high_confidence_execution():
    """Example: High confidence goal executes immediately."""
    gates = ApprovalGates()
    
    decision = gates.decide(
        confidence=0.92,
        goal="Click the submit button",
        reasoning_summary="Button is clearly identifiable",
        tools_proposed=['button_clicker'],
    )
    
    print("HIGH CONFIDENCE EXECUTION:")
    print(f"  Execution Path: {decision.execution_path.value}")
    print(f"  Approval State: {decision.approval_state.value}")
    print(f"  Should Execute: {decision.should_execute}")
    print(f"  Explanation: {decision.explanation}")
    return decision


def example_medium_confidence_approval():
    """Example: Medium confidence requests approval."""
    gates = ApprovalGates()
    
    decision = gates.decide(
        confidence=0.70,
        goal="Refactor this function",
        reasoning_summary="Function needs refactoring but context is limited",
        tools_proposed=['code_analyzer', 'code_refactorer'],
    )
    
    print("\nMEDIUM CONFIDENCE APPROVAL REQUEST:")
    print(f"  Execution Path: {decision.execution_path.value}")
    print(f"  Approval State: {decision.approval_state.value}")
    print(f"  Should Execute: {decision.should_execute}")
    if decision.approval_request:
        print(f"  Request ID: {decision.approval_request.request_id}")
        print(f"  Risks: {decision.approval_request.risks}")
        print(f"  Alternatives: {decision.approval_request.alternatives}")
    return decision


def example_low_confidence_clarification():
    """Example: Low confidence requests clarification."""
    gates = ApprovalGates()
    
    decision = gates.decide(
        confidence=0.30,
        goal="Help me",
        reasoning_summary="Goal is too vague",
        tools_proposed=[],
        is_ambiguous=True,
    )
    
    print("\nLOW CONFIDENCE CLARIFICATION:")
    print(f"  Execution Path: {decision.execution_path.value}")
    print(f"  Approval State: {decision.approval_state.value}")
    print(f"  Should Execute: {decision.should_execute}")
    print(f"  Clarification Needed: {decision.clarification_needed}")
    print(f"  Explanation: {decision.explanation}")
    return decision


if __name__ == '__main__':
    print("=" * 70)
    print("APPROVAL GATES SYSTEM - EXAMPLES")
    print("=" * 70)
    
    example_high_confidence_execution()
    example_medium_confidence_approval()
    example_low_confidence_clarification()

