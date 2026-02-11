"""
Approval System - Requests, decisions, and application to responses.

Phase 4: Provides a structured approval flow for responses and content items.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional
import uuid

from Back_End.response_engine.types import Response, ContentMetadata


@dataclass
class ApprovalRequest:
    """Represents an approval request for a response or content item."""
    request_id: str
    mission_id: str
    response_id: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    reason: Optional[str] = None
    notes: Optional[str] = None
    status: str = "pending"  # pending, approved, denied, expired

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "mission_id": self.mission_id,
            "response_id": self.response_id,
            "created_at": self.created_at.isoformat(),
            "reason": self.reason,
            "notes": self.notes,
            "status": self.status,
        }


@dataclass
class ApprovalDecision:
    """Decision made by user/system on an approval request."""
    approved: bool
    decided_by: Optional[str] = None
    decided_at: datetime = field(default_factory=datetime.utcnow)
    decision_notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "approved": self.approved,
            "decided_by": self.decided_by,
            "decided_at": self.decided_at.isoformat(),
            "decision_notes": self.decision_notes,
        }


class ApprovalManager:
    """Handles approval request creation and decision application."""

    def create_request(
        self,
        response: Response,
        reason: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> ApprovalRequest:
        request = ApprovalRequest(
            request_id=f"apr_{uuid.uuid4().hex[:12]}",
            mission_id=response.mission_id,
            response_id=response.response_id,
            reason=reason or response.approval_reason,
            notes=notes,
        )
        response.approval_status = "pending"
        response.approval_history.append({
            "action": "request_created",
            "request_id": request.request_id,
            "timestamp": request.created_at.isoformat(),
            "reason": request.reason,
            "notes": request.notes,
        })
        return request

    def apply_decision(self, response: Response, decision: ApprovalDecision) -> None:
        response.approved_at = decision.decided_at if decision.approved else None
        response.approved_by = decision.decided_by if decision.approved else None
        response.approval_status = "approved" if decision.approved else "denied"
        response.status = "approved" if decision.approved else "pending"
        response.approval_history.append({
            "action": "decision",
            "approved": decision.approved,
            "decided_by": decision.decided_by,
            "decided_at": decision.decided_at.isoformat(),
            "decision_notes": decision.decision_notes,
        })

    def apply_content_decision(self, content: ContentMetadata, decision: ApprovalDecision) -> None:
        content.approved = decision.approved
        content.approved_at = decision.decided_at if decision.approved else None
        content.approval_status = "approved" if decision.approved else "denied"
        content.approval_history.append({
            "action": "decision",
            "approved": decision.approved,
            "decided_by": decision.decided_by,
            "decided_at": decision.decided_at.isoformat(),
            "decision_notes": decision.decision_notes,
        })

