"""
Operator Audit Log
Full audit trail for all operator control actions
Immutable log with complete decision tracking
"""

from enum import Enum
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Dict, List, Any, Optional
from uuid import uuid4
import json


class AuditEventType(Enum):
    """Types of audit events"""
    CONTROL_SUBMITTED = "control_submitted"
    CONTROL_APPROVED = "control_approved"
    CONTROL_REJECTED = "control_rejected"
    CONTROL_EXECUTED = "control_executed"
    CONTROL_FAILED = "control_failed"
    DOMAIN_LOCKED = "domain_locked"
    DOMAIN_UNLOCKED = "domain_unlocked"
    MISSION_PAUSED = "mission_paused"
    MISSION_KILLED = "mission_killed"
    MISSION_RESUMED = "mission_resumed"
    FORECAST_PROMOTED = "forecast_promoted"


@dataclass
class AuditEvent:
    """
    Immutable audit log entry
    All operator actions are logged with full context
    """
    
    event_id: str
    event_type: AuditEventType
    timestamp: datetime
    operator_id: str
    action_context: Dict[str, Any]
    
    # Optional approver info
    approver_id: Optional[str] = None
    approval_timestamp: Optional[datetime] = None
    approval_reason: Optional[str] = None
    
    # Execution result
    executed: bool = False
    execution_timestamp: Optional[datetime] = None
    execution_result: Optional[Dict[str, Any]] = None
    execution_error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data["event_type"] = self.event_type.value
        return data
    
    def to_json(self) -> str:
        """Convert to JSON"""
        return json.dumps(self.to_dict(), default=str)


class AuditLog:
    """
    Immutable audit log for all operator controls
    Ordered by timestamp, never modified after creation
    """
    
    def __init__(self):
        """Initialize audit log"""
        self.events: List[AuditEvent] = []
        self.index_by_operator: Dict[str, List[AuditEvent]] = {}
        self.index_by_target: Dict[str, List[AuditEvent]] = {}
    
    def add_event(self, event: AuditEvent) -> None:
        """
        Add an event to the audit log (immutable)
        Returns: None, but event is recorded permanently
        """
        self.events.append(event)
        
        # Build indices for fast lookup
        if event.operator_id not in self.index_by_operator:
            self.index_by_operator[event.operator_id] = []
        self.index_by_operator[event.operator_id].append(event)
        
        # Index by target (mission_id or domain)
        target_id = event.action_context.get("target_id")
        if target_id:
            if target_id not in self.index_by_target:
                self.index_by_target[target_id] = []
            self.index_by_target[target_id].append(event)
    
    def log_control_submitted(
        self,
        operator_id: str,
        action_name: str,
        target_id: str,
        reason: str,
        details: Dict[str, Any],
    ) -> str:
        """Log control request submission"""
        event = AuditEvent(
            event_id=str(uuid4()),
            event_type=AuditEventType.CONTROL_SUBMITTED,
            timestamp=datetime.utcnow(),
            operator_id=operator_id,
            action_context={
                "action": action_name,
                "target_id": target_id,
                "reason": reason,
                "details": details,
            },
        )
        self.add_event(event)
        return event.event_id
    
    def log_control_approved(
        self,
        request_id: str,
        approver_id: str,
        target_id: str,
        action_name: str,
        approval_reason: str,
    ) -> str:
        """Log control approval"""
        event = AuditEvent(
            event_id=str(uuid4()),
            event_type=AuditEventType.CONTROL_APPROVED,
            timestamp=datetime.utcnow(),
            operator_id=approver_id,
            approver_id=approver_id,
            approval_timestamp=datetime.utcnow(),
            approval_reason=approval_reason,
            action_context={
                "request_id": request_id,
                "target_id": target_id,
                "action": action_name,
            },
        )
        self.add_event(event)
        return event.event_id
    
    def log_control_rejected(
        self,
        request_id: str,
        rejector_id: str,
        target_id: str,
        action_name: str,
        rejection_reason: str,
    ) -> str:
        """Log control rejection"""
        event = AuditEvent(
            event_id=str(uuid4()),
            event_type=AuditEventType.CONTROL_REJECTED,
            timestamp=datetime.utcnow(),
            operator_id=rejector_id,
            approver_id=rejector_id,
            approval_timestamp=datetime.utcnow(),
            approval_reason=rejection_reason,
            action_context={
                "request_id": request_id,
                "target_id": target_id,
                "action": action_name,
            },
        )
        self.add_event(event)
        return event.event_id
    
    def log_control_executed(
        self,
        request_id: str,
        executor_id: str,
        action_name: str,
        target_id: str,
        result: Dict[str, Any],
    ) -> str:
        """Log control execution"""
        event = AuditEvent(
            event_id=str(uuid4()),
            event_type=AuditEventType.CONTROL_EXECUTED,
            timestamp=datetime.utcnow(),
            operator_id=executor_id,
            executed=True,
            execution_timestamp=datetime.utcnow(),
            execution_result=result,
            action_context={
                "request_id": request_id,
                "target_id": target_id,
                "action": action_name,
            },
        )
        self.add_event(event)
        return event.event_id
    
    def log_control_failed(
        self,
        request_id: str,
        executor_id: str,
        action_name: str,
        target_id: str,
        error: str,
    ) -> str:
        """Log control execution failure"""
        event = AuditEvent(
            event_id=str(uuid4()),
            event_type=AuditEventType.CONTROL_FAILED,
            timestamp=datetime.utcnow(),
            operator_id=executor_id,
            executed=False,
            execution_timestamp=datetime.utcnow(),
            execution_error=error,
            action_context={
                "request_id": request_id,
                "target_id": target_id,
                "action": action_name,
            },
        )
        self.add_event(event)
        return event.event_id
    
    def log_mission_paused(
        self,
        mission_id: str,
        operator_id: str,
        reason: str,
    ) -> str:
        """Log mission pause"""
        event = AuditEvent(
            event_id=str(uuid4()),
            event_type=AuditEventType.MISSION_PAUSED,
            timestamp=datetime.utcnow(),
            operator_id=operator_id,
            executed=True,
            execution_timestamp=datetime.utcnow(),
            execution_result={"status": "paused"},
            action_context={
                "target_id": mission_id,
                "action": "pause_mission",
                "reason": reason,
            },
        )
        self.add_event(event)
        return event.event_id
    
    def log_mission_killed(
        self,
        mission_id: str,
        operator_id: str,
        reason: str,
    ) -> str:
        """Log mission kill"""
        event = AuditEvent(
            event_id=str(uuid4()),
            event_type=AuditEventType.MISSION_KILLED,
            timestamp=datetime.utcnow(),
            operator_id=operator_id,
            executed=True,
            execution_timestamp=datetime.utcnow(),
            execution_result={"status": "killed", "final_artifacts": []},
            action_context={
                "target_id": mission_id,
                "action": "kill_mission",
                "reason": reason,
            },
        )
        self.add_event(event)
        return event.event_id
    
    def log_mission_resumed(
        self,
        mission_id: str,
        operator_id: str,
        reason: str,
    ) -> str:
        """Log mission resume"""
        event = AuditEvent(
            event_id=str(uuid4()),
            event_type=AuditEventType.MISSION_RESUMED,
            timestamp=datetime.utcnow(),
            operator_id=operator_id,
            executed=True,
            execution_timestamp=datetime.utcnow(),
            execution_result={"status": "resumed"},
            action_context={
                "target_id": mission_id,
                "action": "resume_mission",
                "reason": reason,
            },
        )
        self.add_event(event)
        return event.event_id
    
    def log_domain_locked(
        self,
        domain: str,
        locked_by: str,
        reason: str,
        duration_hours: int,
    ) -> str:
        """Log domain lock"""
        event = AuditEvent(
            event_id=str(uuid4()),
            event_type=AuditEventType.DOMAIN_LOCKED,
            timestamp=datetime.utcnow(),
            operator_id=locked_by,
            executed=True,
            execution_timestamp=datetime.utcnow(),
            execution_result={"status": "locked"},
            action_context={
                "target_id": domain,
                "action": "lock_domain",
                "reason": reason,
                "duration_hours": duration_hours,
            },
        )
        self.add_event(event)
        return event.event_id
    
    def log_domain_unlocked(
        self,
        domain: str,
        unlocked_by: str,
        reason: str,
    ) -> str:
        """Log domain unlock"""
        event = AuditEvent(
            event_id=str(uuid4()),
            event_type=AuditEventType.DOMAIN_UNLOCKED,
            timestamp=datetime.utcnow(),
            operator_id=unlocked_by,
            executed=True,
            execution_timestamp=datetime.utcnow(),
            execution_result={"status": "unlocked"},
            action_context={
                "target_id": domain,
                "action": "unlock_domain",
                "reason": reason,
            },
        )
        self.add_event(event)
        return event.event_id
    
    def log_forecast_promoted(
        self,
        forecast_id: str,
        promoted_by: str,
        new_mission_id: str,
        reason: str,
    ) -> str:
        """Log forecast promotion to mission"""
        event = AuditEvent(
            event_id=str(uuid4()),
            event_type=AuditEventType.FORECAST_PROMOTED,
            timestamp=datetime.utcnow(),
            operator_id=promoted_by,
            executed=True,
            execution_timestamp=datetime.utcnow(),
            execution_result={
                "status": "promoted",
                "new_mission_id": new_mission_id,
            },
            action_context={
                "forecast_id": forecast_id,
                "new_mission_id": new_mission_id,
                "action": "promote_forecast",
                "reason": reason,
            },
        )
        self.add_event(event)

        # Optional artifact registry hook (read-only, no behavior change)
        try:
            from Back_End.artifact_registry import Artifact, ArtifactType, PresentationHint, ArtifactStatus
            from Back_End.artifact_registry_store import ArtifactRegistryStore

            registry = ArtifactRegistryStore()
            artifact = Artifact.new(
                artifact_type=ArtifactType.FORECAST,
                title="Forecast Promoted",
                description=f"Forecast {forecast_id} promoted to mission {new_mission_id}",
                created_by=forecast_id,
                source_module="operator_audit_log",
                presentation_hint=PresentationHint.TEXT,
                tags=["forecast", "promotion"],
                status=ArtifactStatus.FINAL,
            )
            registry.register_artifact(artifact)
        except Exception:
            pass

        return event.event_id
    
    # Query methods
    
    def get_all_events(self) -> List[AuditEvent]:
        """Get all events in chronological order"""
        return list(self.events)
    
    def get_events_by_operator(self, operator_id: str) -> List[AuditEvent]:
        """Get all events for a specific operator"""
        return self.index_by_operator.get(operator_id, [])
    
    def get_events_by_target(self, target_id: str) -> List[AuditEvent]:
        """Get all events for a specific mission or domain"""
        return self.index_by_target.get(target_id, [])
    
    def get_events_by_type(
        self,
        event_type: AuditEventType,
    ) -> List[AuditEvent]:
        """Get all events of a specific type"""
        return [e for e in self.events if e.event_type == event_type]
    
    def get_events_in_range(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> List[AuditEvent]:
        """Get all events within a time range"""
        return [
            e
            for e in self.events
            if start_time <= e.timestamp <= end_time
        ]
    
    def get_control_history(self, request_id: str) -> List[AuditEvent]:
        """Get full history of a control request (submitted → approved → executed)"""
        return [
            e
            for e in self.events
            if e.action_context.get("request_id") == request_id
        ]
    
    def export_log(self, filename: str) -> None:
        """Export complete audit log to JSON file"""
        with open(filename, "w") as f:
            log_data = {
                "exported_at": datetime.utcnow().isoformat(),
                "total_events": len(self.events),
                "events": [e.to_dict() for e in self.events],
            }
            json.dump(log_data, f, indent=2, default=str)
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate summary report of audit activity"""
        event_counts = {}
        for event_type in AuditEventType:
            count = len([e for e in self.events if e.event_type == event_type])
            if count > 0:
                event_counts[event_type.value] = count
        
        operator_counts = {}
        for operator_id, events in self.index_by_operator.items():
            operator_counts[operator_id] = len(events)
        
        failed_controls = [
            e
            for e in self.events
            if e.event_type == AuditEventType.CONTROL_FAILED
        ]
        
        return {
            "total_events": len(self.events),
            "time_range": {
                "earliest": (
                    self.events[0].timestamp.isoformat()
                    if self.events
                    else None
                ),
                "latest": (
                    self.events[-1].timestamp.isoformat()
                    if self.events
                    else None
                ),
            },
            "event_breakdown": event_counts,
            "operators_involved": len(self.index_by_operator),
            "operators": operator_counts,
            "failed_controls": len(failed_controls),
            "approval_rate": (
                (
                    len(self.get_events_by_type(AuditEventType.CONTROL_APPROVED))
                    / (
                        len(
                            self.get_events_by_type(
                                AuditEventType.CONTROL_APPROVED
                            )
                        )
                        + len(
                            self.get_events_by_type(
                                AuditEventType.CONTROL_REJECTED
                            )
                        )
                    )
                )
                if (
                    len(
                        self.get_events_by_type(
                            AuditEventType.CONTROL_APPROVED
                        )
                    )
                    + len(
                        self.get_events_by_type(
                            AuditEventType.CONTROL_REJECTED
                        )
                    )
                )
                > 0
                else 0
            ),
        }


# Global audit log instance
_audit_log: Optional[AuditLog] = None


def get_audit_log() -> AuditLog:
    """Get or create global audit log"""
    global _audit_log
    if _audit_log is None:
        _audit_log = AuditLog()
    return _audit_log

