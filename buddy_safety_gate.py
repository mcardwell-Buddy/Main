"""
Phase 13: Safety Gate Module
Enforces safety constraints for live web action execution.
"""

import logging
from enum import Enum
from typing import Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)


class ApprovalStatus(Enum):
    """Approval status for task execution."""
    APPROVED = "approved"
    DEFERRED = "deferred"
    REJECTED = "rejected"


class SafetyGate:
    """
    Enforces safety constraints for live web action execution.
    
    Rules:
    - LOW risk: Always approved (confidence ≥ 0.5)
    - MEDIUM risk: Approved if confidence ≥ 0.75, requires explicit approval
    - HIGH risk: Deferred unless confidence ≥ 0.9 AND explicitly approved
    """
    
    def __init__(self, require_approval: bool = False):
        self.require_approval = require_approval
        self.approved_task_ids = set()
        self.decisions = []
    
    def approve_task(self, task_id: str):
        """Explicitly approve a task for execution."""
        self.approved_task_ids.add(task_id)
        logger.info(f"Approved task: {task_id}")
    
    def evaluate(
        self,
        task_id: str,
        risk_level: str,
        confidence: float,
        is_dry_run: bool = False
    ) -> Tuple[ApprovalStatus, str]:
        """
        Evaluate task for safety approval.
        
        Args:
            task_id: Task identifier
            risk_level: LOW, MEDIUM, or HIGH
            confidence: Confidence score 0.0-1.0
            is_dry_run: Whether this is a dry-run execution
        
        Returns:
            Tuple of (approval_status, reason)
        """
        reason = ""
        approval = ApprovalStatus.DEFERRED
        
        # Dry-run tasks always approved
        if is_dry_run:
            approval = ApprovalStatus.APPROVED
            reason = "Dry-run mode: no safety constraints"
            self.decisions.append({
                "task_id": task_id,
                "risk_level": risk_level,
                "confidence": confidence,
                "approval": approval.value,
                "reason": reason
            })
            return approval, reason
        
        # LOW risk: Approve if confidence ≥ 0.5
        if risk_level == "LOW":
            if confidence >= 0.5:
                approval = ApprovalStatus.APPROVED
                reason = f"LOW risk approved (confidence {confidence:.2f} ≥ 0.5)"
            else:
                approval = ApprovalStatus.DEFERRED
                reason = f"LOW risk deferred (confidence {confidence:.2f} < 0.5)"
        
        # MEDIUM risk: Require ≥ 0.75 confidence AND approval
        elif risk_level == "MEDIUM":
            if confidence >= 0.75:
                if task_id in self.approved_task_ids or not self.require_approval:
                    approval = ApprovalStatus.APPROVED
                    reason = f"MEDIUM risk approved (confidence {confidence:.2f} ≥ 0.75, pre-approved)"
                else:
                    approval = ApprovalStatus.DEFERRED
                    reason = f"MEDIUM risk deferred (confidence {confidence:.2f} ≥ 0.75 but requires approval)"
            else:
                approval = ApprovalStatus.DEFERRED
                reason = f"MEDIUM risk deferred (confidence {confidence:.2f} < 0.75)"
        
        # HIGH risk: Require ≥ 0.9 confidence AND explicit approval
        elif risk_level == "HIGH":
            if confidence >= 0.9 and task_id in self.approved_task_ids:
                approval = ApprovalStatus.APPROVED
                reason = f"HIGH risk approved (confidence {confidence:.2f} ≥ 0.9, explicitly approved)"
            else:
                approval = ApprovalStatus.DEFERRED
                if confidence < 0.9:
                    reason = f"HIGH risk deferred (confidence {confidence:.2f} < 0.9)"
                else:
                    reason = f"HIGH risk deferred (not explicitly approved)"
        
        self.decisions.append({
            "task_id": task_id,
            "risk_level": risk_level,
            "confidence": confidence,
            "approval": approval.value,
            "reason": reason
        })
        
        logger.info(f"{task_id}: {approval.value.upper()} - {reason}")
        return approval, reason
    
    def get_decisions(self) -> list:
        """Get all safety gate decisions."""
        return self.decisions
    
    def reset(self):
        """Reset decisions for new wave."""
        self.decisions = []
