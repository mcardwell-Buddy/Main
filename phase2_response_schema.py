"""
================================================================================
PHASE 2: RESPONSE SCHEMA & BUILDERS
================================================================================

Purpose: Unified response schema for all /reasoning/execute responses.

Reference: PHASE_2_DESIGN_DOCUMENT.md - Section 6

Response Structure (Extended from Phase 1):
{
    "success": bool,
    "result": {
        "reasoning_summary": str,
        "tool_results": list,
        "tools_used": list,
        "understanding": dict,
        "confidence": float  # NEW: Graded confidence [0.0, 1.0]
    },
    "approval_state": str,  # NEW: none | awaiting_approval | approved | denied | timeout
    "soul_request_id": str or null,  # NEW: ID for tracking in Soul
    "execution_path": str  # NEW: high_confidence | approved | suggested | clarification | rejected
}

Backward Compatibility:
- All Phase 1 fields preserved
- New fields added (optional for old clients)
- HTTP 200 for all responses (no 5xx errors)
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class ToolResult:
    """Result from single tool execution."""
    tool_name: str
    success: bool
    message: str = ""
    result: Any = None
    duration_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON serialization."""
        return asdict(self)


@dataclass
class Understanding:
    """Agent's understanding of the goal."""
    goal_text: str
    clarity: float  # 0.0-1.0
    interpreted_action: str = ""
    detected_target: str = ""
    confidence_factors: Dict[str, float] = None
    error: str = ""  # If goal is impossible
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict."""
        return {
            'goal_text': self.goal_text,
            'clarity': self.clarity,
            'interpreted_action': self.interpreted_action,
            'detected_target': self.detected_target,
            'confidence_factors': self.confidence_factors or {},
            'error': self.error,
        }


@dataclass
class ReasoningResult:
    """Core reasoning output (Phase 1 compatible)."""
    reasoning_summary: str
    tool_results: List[Dict[str, Any]]
    tools_used: List[str]
    understanding: Dict[str, Any]
    confidence: float  # NEW: Graded confidence [0.0, 1.0]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict."""
        return {
            'reasoning_summary': self.reasoning_summary,
            'tool_results': self.tool_results,
            'tools_used': self.tools_used,
            'understanding': self.understanding,
            'confidence': self.confidence,
        }


@dataclass
class Phase2Response:
    """
    Complete Phase 2 response.
    
    Extends Phase 1 with approval state, soul tracking, and execution path.
    """
    success: bool  # Did tools execute successfully?
    result: ReasoningResult
    approval_state: str  # none | awaiting_approval | approved | denied | timeout
    soul_request_id: Optional[str] = None
    execution_path: str = "suggested"  # high_confidence | approved | suggested | clarification | rejected
    timestamp: str = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        """Set defaults."""
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON serialization (Phase 1 compatible)."""
        return {
            'success': self.success,
            'result': self.result.to_dict(),
            'approval_state': self.approval_state,
            'soul_request_id': self.soul_request_id,
            'execution_path': self.execution_path,
            'timestamp': self.timestamp,
            'metadata': self.metadata,
        }


class Phase2ResponseBuilder:
    """
    Builder for constructing Phase 2 responses.
    
    Handles common patterns:
    - High confidence execution (auto-execute)
    - Approval request (awaiting approval)
    - Clarification needed (ambiguous goal)
    - Execution failed (impossible goal)
    
    Usage:
        builder = Phase2ResponseBuilder()
        
        # High confidence
        response = builder.build_high_confidence_execution(
            goal="Click button",
            tools=["button_clicker"],
            results=[...],
            confidence=0.92
        )
        
        # Approval needed
        response = builder.build_awaiting_approval(
            goal="Refactor code",
            confidence=0.72,
            approval_request_id="req_123"
        )
    """
    
    @staticmethod
    def build_high_confidence_execution(
        goal: str,
        tools_used: List[str],
        tool_results: List[Dict[str, Any]],
        confidence: float,
        reasoning_summary: str = "",
    ) -> Phase2Response:
        """
        Build response for high confidence execution.
        
        Success path: Tools executed immediately without approval.
        """
        success = all(
            tr.get('success', False)
            for tr in tool_results
        )
        
        understanding = Understanding(
            goal_text=goal,
            clarity=1.0,
            interpreted_action=goal,
            confidence_factors={'confidence': confidence},
        )
        
        result = ReasoningResult(
            reasoning_summary=reasoning_summary or f"Executing {len(tools_used)} tools",
            tool_results=tool_results,
            tools_used=tools_used,
            understanding=understanding.to_dict(),
            confidence=confidence,
        )
        
        return Phase2Response(
            success=success,
            result=result,
            approval_state="none",
            execution_path="high_confidence",
        )
    
    @staticmethod
    def build_awaiting_approval(
        goal: str,
        confidence: float,
        approval_request_id: str,
        reasoning_summary: str = "",
        tools_proposed: List[str] = None,
    ) -> Phase2Response:
        """
        Build response waiting for user approval.
        
        Medium confidence: Approval gate triggered, awaiting decision.
        """
        tools_proposed = tools_proposed or []
        
        understanding = Understanding(
            goal_text=goal,
            clarity=0.7,
            interpreted_action=goal,
            confidence_factors={'confidence': confidence},
        )
        
        result = ReasoningResult(
            reasoning_summary=reasoning_summary or f"Awaiting approval for {len(tools_proposed)} tools",
            tool_results=[],  # Not executed yet
            tools_used=[],
            understanding=understanding.to_dict(),
            confidence=confidence,
        )
        
        return Phase2Response(
            success=False,  # Not executed yet
            result=result,
            approval_state="awaiting_approval",
            soul_request_id=approval_request_id,
            execution_path="approved",
        )
    
    @staticmethod
    def build_clarification_needed(
        goal: str,
        confidence: float,
        clarification_request_id: str,
        ambiguity_reason: str = "",
    ) -> Phase2Response:
        """
        Build response requesting clarification.
        
        Low confidence, ambiguous goal: Request user input before proceeding.
        """
        understanding = Understanding(
            goal_text=goal,
            clarity=min(confidence, 0.3),  # Very low clarity
            error=ambiguity_reason or "Goal is ambiguous",
            confidence_factors={'confidence': confidence},
        )
        
        result = ReasoningResult(
            reasoning_summary=f"Goal needs clarification: {ambiguity_reason}",
            tool_results=[],
            tools_used=[],
            understanding=understanding.to_dict(),
            confidence=confidence,
        )
        
        return Phase2Response(
            success=False,
            result=result,
            approval_state="none",
            soul_request_id=clarification_request_id,
            execution_path="clarification",
        )
    
    @staticmethod
    def build_execution_failed(
        goal: str,
        confidence: float,
        error_message: str,
        suggestion: str = "",
    ) -> Phase2Response:
        """
        Build response for failed execution.
        
        Failure: Goal is impossible or pre-validation failed.
        """
        understanding = Understanding(
            goal_text=goal,
            clarity=confidence,
            error=error_message,
            confidence_factors={'confidence': confidence},
        )
        
        result = ReasoningResult(
            reasoning_summary=f"Execution failed: {error_message}",
            tool_results=[],
            tools_used=[],
            understanding=understanding.to_dict(),
            confidence=confidence,
        )
        
        response = Phase2Response(
            success=False,
            result=result,
            approval_state="none",
            execution_path="rejected",
        )
        
        if suggestion:
            response.metadata['suggestion'] = suggestion
        
        return response
    
    @staticmethod
    def build_approval_granted_execution(
        goal: str,
        tools_used: List[str],
        tool_results: List[Dict[str, Any]],
        confidence: float,
        approval_request_id: str,
        reasoning_summary: str = "",
    ) -> Phase2Response:
        """
        Build response for approved execution.
        
        User approved, tools executed successfully.
        """
        success = all(
            tr.get('success', False)
            for tr in tool_results
        )
        
        understanding = Understanding(
            goal_text=goal,
            clarity=0.7,  # Medium clarity (needed approval)
            interpreted_action=goal,
            confidence_factors={'confidence': confidence},
        )
        
        result = ReasoningResult(
            reasoning_summary=reasoning_summary or f"Approved, executing {len(tools_used)} tools",
            tool_results=tool_results,
            tools_used=tools_used,
            understanding=understanding.to_dict(),
            confidence=confidence,
        )
        
        return Phase2Response(
            success=success,
            result=result,
            approval_state="approved",
            soul_request_id=approval_request_id,
            execution_path="approved",
        )


# =============================================================================
# SCHEMA VALIDATION
# =============================================================================

class ResponseValidator:
    """
    Validate Phase 2 responses meet schema invariants.
    
    Invariants:
    - success is bool
    - confidence is float in [0.0, 1.0]
    - tool_results and tools_used lengths match
    - approval_state is valid
    - execution_path is valid
    """
    
    VALID_APPROVAL_STATES = {
        "none", "awaiting_approval", "approved", "denied", "timeout"
    }
    
    VALID_EXECUTION_PATHS = {
        "high_confidence", "approved", "suggested", "clarification", "rejected"
    }
    
    @staticmethod
    def validate(response: Phase2Response) -> Dict[str, Any]:
        """
        Validate response meets all invariants.
        
        Returns:
            {
                'valid': bool,
                'errors': List[str]
            }
        """
        errors = []
        
        # Check success is bool
        if not isinstance(response.success, bool):
            errors.append("success must be bool")
        
        # Check confidence is in range
        conf = response.result.confidence
        if not isinstance(conf, (int, float)) or not (0.0 <= conf <= 1.0):
            errors.append(f"confidence must be float in [0.0, 1.0], got {conf}")
        
        # Check tools match
        tools_len = len(response.result.tools_used)
        results_len = len(response.result.tool_results)
        if tools_len != results_len:
            errors.append(
                f"tools_used ({tools_len}) and tool_results ({results_len}) length mismatch"
            )
        
        # Check approval_state is valid
        if response.approval_state not in ResponseValidator.VALID_APPROVAL_STATES:
            errors.append(
                f"approval_state must be one of {ResponseValidator.VALID_APPROVAL_STATES}, "
                f"got {response.approval_state}"
            )
        
        # Check execution_path is valid
        if response.execution_path not in ResponseValidator.VALID_EXECUTION_PATHS:
            errors.append(
                f"execution_path must be one of {ResponseValidator.VALID_EXECUTION_PATHS}, "
                f"got {response.execution_path}"
            )
        
        # Check tool_results have required fields
        for i, tr in enumerate(response.result.tool_results):
            if not isinstance(tr, dict):
                errors.append(f"tool_results[{i}] must be dict")
                continue
            
            if 'tool_name' not in tr:
                errors.append(f"tool_results[{i}] missing 'tool_name'")
            
            if 'success' not in tr:
                errors.append(f"tool_results[{i}] missing 'success'")
            elif not isinstance(tr['success'], bool):
                errors.append(f"tool_results[{i}]['success'] must be bool")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
        }


# =============================================================================
# EXAMPLES FOR TESTING
# =============================================================================

def example_high_confidence_response():
    """Example: Response for high confidence execution."""
    builder = Phase2ResponseBuilder()
    
    response = builder.build_high_confidence_execution(
        goal="Click the submit button",
        tools_used=["button_clicker"],
        tool_results=[
            {
                'tool_name': 'button_clicker',
                'success': True,
                'message': 'Button clicked successfully',
            }
        ],
        confidence=0.92,
        reasoning_summary="Button was located and clicked",
    )
    
    print("HIGH CONFIDENCE RESPONSE:")
    print(f"  Success: {response.success}")
    print(f"  Confidence: {response.result.confidence}")
    print(f"  Execution Path: {response.execution_path}")
    print(f"  Approval State: {response.approval_state}")
    
    # Validate
    validation = ResponseValidator.validate(response)
    print(f"  Valid: {validation['valid']}")
    return response


def example_awaiting_approval_response():
    """Example: Response awaiting approval."""
    builder = Phase2ResponseBuilder()
    
    response = builder.build_awaiting_approval(
        goal="Refactor this function",
        confidence=0.70,
        approval_request_id="req_abc123",
        tools_proposed=["code_analyzer", "code_refactorer"],
    )
    
    print("\nAWAITING APPROVAL RESPONSE:")
    print(f"  Success: {response.success}")
    print(f"  Confidence: {response.result.confidence}")
    print(f"  Execution Path: {response.execution_path}")
    print(f"  Approval State: {response.approval_state}")
    print(f"  Soul Request ID: {response.soul_request_id}")
    
    # Validate
    validation = ResponseValidator.validate(response)
    print(f"  Valid: {validation['valid']}")
    return response


def example_clarification_response():
    """Example: Response requesting clarification."""
    builder = Phase2ResponseBuilder()
    
    response = builder.build_clarification_needed(
        goal="Help me",
        confidence=0.20,
        clarification_request_id="clar_xyz789",
        ambiguity_reason="Goal is too vague - no specific action mentioned",
    )
    
    print("\nCLARIFICATION NEEDED RESPONSE:")
    print(f"  Success: {response.success}")
    print(f"  Confidence: {response.result.confidence}")
    print(f"  Execution Path: {response.execution_path}")
    print(f"  Soul Request ID: {response.soul_request_id}")
    
    # Validate
    validation = ResponseValidator.validate(response)
    print(f"  Valid: {validation['valid']}")
    return response


if __name__ == '__main__':
    print("=" * 70)
    print("RESPONSE SCHEMA & BUILDERS - EXAMPLES")
    print("=" * 70)
    
    example_high_confidence_response()
    example_awaiting_approval_response()
    example_clarification_response()

