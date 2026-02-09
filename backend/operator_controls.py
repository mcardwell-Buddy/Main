"""
Operator Controls Schema
Safety-first operator interventions with manual approval and full audit trail
NO auto-execution, NO autonomy, manual approval only
"""

from enum import Enum
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json
from uuid import uuid4


class ControlAction(Enum):
    """Operator control actions"""
    PAUSE_MISSION = "pause_mission"
    KILL_MISSION = "kill_mission"
    PROMOTE_FORECAST = "promote_forecast"
    LOCK_DOMAIN = "lock_domain"
    UNLOCK_DOMAIN = "unlock_domain"
    RESUME_MISSION = "resume_mission"


class ApprovalStatus(Enum):
    """Approval workflow states"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class ControlStatus(Enum):
    """Control execution status"""
    SUBMITTED = "submitted"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    EXECUTING = "executing"
    EXECUTED = "executed"
    FAILED = "failed"
    REJECTED = "rejected"


@dataclass
class ControlRequest:
    """
    Operator control request
    Requires manual approval before execution
    """
    
    request_id: str
    operator_id: str
    action: ControlAction
    target_id: str  # mission_id or domain
    reason: str
    details: Dict[str, Any]
    submitted_at: datetime
    approval_status: ApprovalStatus = ApprovalStatus.PENDING
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    approval_reason: Optional[str] = None
    executed_at: Optional[datetime] = None
    execution_status: Optional[str] = None
    execution_result: Optional[Dict[str, Any]] = None
    
    @staticmethod
    def create(
        operator_id: str,
        action: ControlAction,
        target_id: str,
        reason: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> "ControlRequest":
        """Create a new control request"""
        return ControlRequest(
            request_id=str(uuid4()),
            operator_id=operator_id,
            action=action,
            target_id=target_id,
            reason=reason,
            details=details or {},
            submitted_at=datetime.utcnow(),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data["action"] = self.action.value
        data["approval_status"] = self.approval_status.value
        if self.execution_status:
            data["execution_status"] = self.execution_status
        return data
    
    def to_json(self) -> str:
        """Convert to JSON"""
        return json.dumps(self.to_dict(), default=str)


@dataclass
class PauseMissionControl(ControlRequest):
    """
    Pause a running mission
    Operator: {operator_id}
    Reason: {reason}
    Approval Required: YES
    Effect: Mission execution paused, can be resumed
    """
    
    @staticmethod
    def create(
        operator_id: str,
        mission_id: str,
        reason: str,
    ) -> "PauseMissionControl":
        """Create pause mission control"""
        return PauseMissionControl(
            request_id=str(uuid4()),
            operator_id=operator_id,
            action=ControlAction.PAUSE_MISSION,
            target_id=mission_id,
            reason=reason,
            details={
                "mission_id": mission_id,
                "paused_at": datetime.utcnow().isoformat(),
            },
            submitted_at=datetime.utcnow(),
        )


@dataclass
class KillMissionControl(ControlRequest):
    """
    Terminate a mission immediately
    Operator: {operator_id}
    Reason: {reason}
    Approval Required: YES (critical action)
    Effect: Mission terminated, cannot be resumed, generates artifacts from partial progress
    """
    
    @staticmethod
    def create(
        operator_id: str,
        mission_id: str,
        reason: str,
    ) -> "KillMissionControl":
        """Create kill mission control"""
        return KillMissionControl(
            request_id=str(uuid4()),
            operator_id=operator_id,
            action=ControlAction.KILL_MISSION,
            target_id=mission_id,
            reason=reason,
            details={
                "mission_id": mission_id,
                "killed_at": datetime.utcnow().isoformat(),
                "severity": "critical",
            },
            submitted_at=datetime.utcnow(),
        )


@dataclass
class PromoteForecastControl(ControlRequest):
    """
    Promote a forecast to a live mission
    Operator: {operator_id}
    Reason: {reason}
    Approval Required: YES (creates live mission)
    Effect: Forecast converted to mission, execution starts after approval
    Constraints: Manual only, NO automatic promotion
    """
    
    @staticmethod
    def create(
        operator_id: str,
        forecast_id: str,
        reason: str,
        mission_params: Optional[Dict[str, Any]] = None,
    ) -> "PromoteForecastControl":
        """Create promote forecast control"""
        return PromoteForecastControl(
            request_id=str(uuid4()),
            operator_id=operator_id,
            action=ControlAction.PROMOTE_FORECAST,
            target_id=forecast_id,
            reason=reason,
            details={
                "forecast_id": forecast_id,
                "mission_params": mission_params or {},
                "promoted_at": datetime.utcnow().isoformat(),
            },
            submitted_at=datetime.utcnow(),
        )


@dataclass
class LockDomainControl(ControlRequest):
    """
    Lock a domain to prevent any missions from accessing it
    Operator: {operator_id}
    Reason: {reason} (e.g., "maintenance", "security", "rate limit")
    Approval Required: YES
    Effect: All missions blocked from accessing domain
    Duration: Lockout period (hours)
    """
    
    @staticmethod
    def create(
        operator_id: str,
        domain: str,
        reason: str,
        duration_hours: int = 1,
    ) -> "LockDomainControl":
        """Create lock domain control"""
        locked_until = datetime.utcnow() + timedelta(hours=duration_hours)
        
        return LockDomainControl(
            request_id=str(uuid4()),
            operator_id=operator_id,
            action=ControlAction.LOCK_DOMAIN,
            target_id=domain,
            reason=reason,
            details={
                "domain": domain,
                "duration_hours": duration_hours,
                "locked_at": datetime.utcnow().isoformat(),
                "locked_until": locked_until.isoformat(),
            },
            submitted_at=datetime.utcnow(),
        )


@dataclass
class UnlockDomainControl(ControlRequest):
    """
    Unlock a previously locked domain
    Operator: {operator_id}
    Reason: {reason} (e.g., "maintenance complete", "issue resolved")
    Approval Required: NO (lower priority)
    Effect: Domain accessible to missions again
    """
    
    @staticmethod
    def create(
        operator_id: str,
        domain: str,
        reason: str,
    ) -> "UnlockDomainControl":
        """Create unlock domain control"""
        return UnlockDomainControl(
            request_id=str(uuid4()),
            operator_id=operator_id,
            action=ControlAction.UNLOCK_DOMAIN,
            target_id=domain,
            reason=reason,
            details={
                "domain": domain,
                "unlocked_at": datetime.utcnow().isoformat(),
            },
            submitted_at=datetime.utcnow(),
        )


@dataclass
class ResumeMissionControl(ControlRequest):
    """
    Resume a paused mission
    Operator: {operator_id}
    Reason: {reason}
    Approval Required: NO (lower priority)
    Effect: Mission execution resumes from pause point
    """
    
    @staticmethod
    def create(
        operator_id: str,
        mission_id: str,
        reason: str,
    ) -> "ResumeMissionControl":
        """Create resume mission control"""
        return ResumeMissionControl(
            request_id=str(uuid4()),
            operator_id=operator_id,
            action=ControlAction.RESUME_MISSION,
            target_id=mission_id,
            reason=reason,
            details={
                "mission_id": mission_id,
                "resumed_at": datetime.utcnow().isoformat(),
            },
            submitted_at=datetime.utcnow(),
        )


class ControlApprovalManager:
    """Manages control request approvals with manual intervention"""
    
    def __init__(self):
        """Initialize approval manager"""
        self.pending_requests: Dict[str, ControlRequest] = {}
        self.approved_requests: Dict[str, ControlRequest] = {}
        self.rejected_requests: Dict[str, ControlRequest] = {}
        self.executed_requests: Dict[str, ControlRequest] = {}
        
        # Actions requiring approval
        self.requires_approval = {
            ControlAction.PAUSE_MISSION,
            ControlAction.KILL_MISSION,
            ControlAction.PROMOTE_FORECAST,
            ControlAction.LOCK_DOMAIN,
        }
        
        # Actions that can bypass approval (lower priority)
        self.no_approval_required = {
            ControlAction.RESUME_MISSION,
            ControlAction.UNLOCK_DOMAIN,
        }
    
    def submit_control_request(self, request: ControlRequest) -> str:
        """
        Submit a control request for approval
        Returns: request_id
        """
        if request.action in self.requires_approval:
            request.approval_status = ApprovalStatus.PENDING
        elif request.action in self.no_approval_required:
            request.approval_status = ApprovalStatus.APPROVED
            request.approved_at = datetime.utcnow()
        
        self.pending_requests[request.request_id] = request
        return request.request_id
    
    def approve_control_request(
        self,
        request_id: str,
        approver_id: str,
        approval_reason: str,
    ) -> bool:
        """
        Manually approve a control request
        Requires operator intervention
        Returns: True if approved, False if request not found or already decided
        """
        if request_id not in self.pending_requests:
            return False
        
        request = self.pending_requests[request_id]
        
        if request.approval_status != ApprovalStatus.PENDING:
            return False  # Already decided
        
        request.approval_status = ApprovalStatus.APPROVED
        request.approved_by = approver_id
        request.approved_at = datetime.utcnow()
        request.approval_reason = approval_reason
        
        # Move to approved
        self.approved_requests[request_id] = request
        del self.pending_requests[request_id]
        
        return True
    
    def reject_control_request(
        self,
        request_id: str,
        rejector_id: str,
        rejection_reason: str,
    ) -> bool:
        """
        Manually reject a control request
        Requires operator intervention
        Returns: True if rejected, False if request not found or already decided
        """
        if request_id not in self.pending_requests:
            return False
        
        request = self.pending_requests[request_id]
        
        if request.approval_status != ApprovalStatus.PENDING:
            return False  # Already decided
        
        request.approval_status = ApprovalStatus.REJECTED
        request.approved_by = rejector_id
        request.approved_at = datetime.utcnow()
        request.approval_reason = rejection_reason
        
        # Move to rejected
        self.rejected_requests[request_id] = request
        del self.pending_requests[request_id]
        
        return True
    
    def mark_executed(
        self,
        request_id: str,
        result: Dict[str, Any],
    ) -> bool:
        """
        Mark a control request as executed
        Called after the control action is performed
        Returns: True if marked, False if request not found
        """
        if request_id not in self.approved_requests:
            return False
        
        request = self.approved_requests[request_id]
        request.executed_at = datetime.utcnow()
        request.execution_status = "executed"
        request.execution_result = result
        
        self.executed_requests[request_id] = request
        del self.approved_requests[request_id]
        
        return True
    
    def get_pending_approvals(self) -> List[ControlRequest]:
        """Get all pending control requests awaiting approval"""
        return list(self.pending_requests.values())
    
    def get_pending_execution(self) -> List[ControlRequest]:
        """Get all approved controls awaiting execution"""
        return list(self.approved_requests.values())
    
    def get_request_history(self, request_id: str) -> Optional[ControlRequest]:
        """Get full history of a control request"""
        return (
            self.pending_requests.get(request_id)
            or self.approved_requests.get(request_id)
            or self.rejected_requests.get(request_id)
            or self.executed_requests.get(request_id)
        )


@dataclass
class DomainLock:
    """Domain lock with expiration"""
    
    domain: str
    locked_at: datetime
    locked_by: str
    locked_until: datetime
    reason: str
    lock_id: str = field(default_factory=lambda: str(uuid4()))
    
    def is_active(self) -> bool:
        """Check if lock is currently active"""
        return datetime.utcnow() < self.locked_until
    
    def time_remaining(self) -> Optional[timedelta]:
        """Get remaining lock time"""
        if self.is_active():
            return self.locked_until - datetime.utcnow()
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "lock_id": self.lock_id,
            "domain": self.domain,
            "locked_at": self.locked_at.isoformat(),
            "locked_by": self.locked_by,
            "locked_until": self.locked_until.isoformat(),
            "reason": self.reason,
            "is_active": self.is_active(),
            "time_remaining_seconds": (
                self.time_remaining().total_seconds()
                if self.time_remaining()
                else None
            ),
        }


class DomainLockManager:
    """Manages domain locks with automatic expiration"""
    
    def __init__(self):
        """Initialize lock manager"""
        self.active_locks: Dict[str, DomainLock] = {}
    
    def lock_domain(
        self,
        domain: str,
        locked_by: str,
        reason: str,
        duration_hours: int,
    ) -> DomainLock:
        """Lock a domain"""
        locked_until = datetime.utcnow() + timedelta(hours=duration_hours)
        
        lock = DomainLock(
            domain=domain,
            locked_at=datetime.utcnow(),
            locked_by=locked_by,
            locked_until=locked_until,
            reason=reason,
        )
        
        self.active_locks[domain] = lock
        return lock
    
    def unlock_domain(self, domain: str) -> bool:
        """Unlock a domain"""
        if domain in self.active_locks:
            del self.active_locks[domain]
            return True
        return False
    
    def is_domain_locked(self, domain: str) -> bool:
        """Check if domain is currently locked"""
        if domain in self.active_locks:
            lock = self.active_locks[domain]
            if lock.is_active():
                return True
            else:
                # Expired, remove it
                del self.active_locks[domain]
                return False
        return False
    
    def get_lock(self, domain: str) -> Optional[DomainLock]:
        """Get lock info for a domain"""
        if domain in self.active_locks:
            lock = self.active_locks[domain]
            if lock.is_active():
                return lock
            else:
                del self.active_locks[domain]
        return None
    
    def get_all_active_locks(self) -> List[DomainLock]:
        """Get all active locks, cleaning expired ones"""
        expired = []
        for domain, lock in list(self.active_locks.items()):
            if not lock.is_active():
                expired.append(domain)
        
        for domain in expired:
            del self.active_locks[domain]
        
        return list(self.active_locks.values())


# Global instances
_approval_manager: Optional[ControlApprovalManager] = None
_domain_lock_manager: Optional[DomainLockManager] = None


def get_approval_manager() -> ControlApprovalManager:
    """Get or create global approval manager"""
    global _approval_manager
    if _approval_manager is None:
        _approval_manager = ControlApprovalManager()
    return _approval_manager


def get_domain_lock_manager() -> DomainLockManager:
    """Get or create global domain lock manager"""
    global _domain_lock_manager
    if _domain_lock_manager is None:
        _domain_lock_manager = DomainLockManager()
    return _domain_lock_manager
