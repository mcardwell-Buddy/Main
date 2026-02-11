"""
Mission Control: MissionContract schema and helpers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid


@dataclass
class MissionObjective:
    type: str
    description: str
    target: Optional[int]
    required_fields: List[str]


@dataclass
class MissionScope:
    allowed_domains: List[str]
    max_pages: int
    max_duration_seconds: int


@dataclass
class MissionAuthority:
    execution_mode: str
    external_actions_allowed: List[str]


@dataclass
class MissionSuccessConditions:
    min_items_collected: Optional[int]


@dataclass
class MissionFailureConditions:
    no_progress_pages: int
    navigation_blocked: bool
    required_fields_missing: bool


@dataclass
class MissionReporting:
    summary_required: bool
    confidence_explanation: bool


@dataclass
class MissionContract:
    mission_id: str
    objective: MissionObjective
    scope: MissionScope
    authority: MissionAuthority
    success_conditions: MissionSuccessConditions
    failure_conditions: MissionFailureConditions
    reporting: MissionReporting
    status: str
    created_at: str
    completed_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    goal_id: Optional[str] = None
    program_id: Optional[str] = None
    mission_thread_id: Optional[str] = None

    @staticmethod
    def new(
        objective: Dict[str, Any],
        scope: Dict[str, Any],
        authority: Dict[str, Any],
        success_conditions: Dict[str, Any],
        failure_conditions: Dict[str, Any],
        reporting: Dict[str, Any],
        goal_id: Optional[str] = None,
        program_id: Optional[str] = None,
        mission_thread_id: Optional[str] = None
    ) -> "MissionContract":
        mission_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        return MissionContract(
            mission_id=mission_id,
            objective=MissionObjective(**objective),
            scope=MissionScope(**scope),
            authority=MissionAuthority(**authority),
            success_conditions=MissionSuccessConditions(**success_conditions),
            failure_conditions=MissionFailureConditions(**failure_conditions),
            reporting=MissionReporting(**reporting),
            status="created",
            created_at=now,
            completed_at=None,
            goal_id=goal_id,
            program_id=program_id,
            mission_thread_id=mission_thread_id
        )

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "MissionContract":
        return MissionContract(
            mission_id=data.get("mission_id") or str(uuid.uuid4()),
            objective=MissionObjective(**data["objective"]),
            scope=MissionScope(**data["scope"]),
            authority=MissionAuthority(**data["authority"]),
            success_conditions=MissionSuccessConditions(**data["success_conditions"]),
            failure_conditions=MissionFailureConditions(**data["failure_conditions"]),
            reporting=MissionReporting(**data["reporting"]),
            status=data.get("status", "created"),
            created_at=data.get("created_at") or datetime.now(timezone.utc).isoformat(),
            completed_at=data.get("completed_at"),
            metadata=data.get("metadata", {}),
            goal_id=data.get("goal_id"),
            program_id=data.get("program_id"),
            mission_thread_id=data.get("mission_thread_id")
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mission_id": self.mission_id,
            "objective": {
                "type": self.objective.type,
                "description": self.objective.description,
                "target": self.objective.target,
                "required_fields": self.objective.required_fields
            },
            "scope": {
                "allowed_domains": self.scope.allowed_domains,
                "max_pages": self.scope.max_pages,
                "max_duration_seconds": self.scope.max_duration_seconds
            },
            "authority": {
                "execution_mode": self.authority.execution_mode,
                "external_actions_allowed": self.authority.external_actions_allowed
            },
            "success_conditions": {
                "min_items_collected": self.success_conditions.min_items_collected
            },
            "failure_conditions": {
                "no_progress_pages": self.failure_conditions.no_progress_pages,
                "navigation_blocked": self.failure_conditions.navigation_blocked,
                "required_fields_missing": self.failure_conditions.required_fields_missing
            },
            "reporting": {
                "summary_required": self.reporting.summary_required,
                "confidence_explanation": self.reporting.confidence_explanation
            },
            "status": self.status,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "metadata": self.metadata,
            "goal_id": self.goal_id,
            "program_id": self.program_id,
            "mission_thread_id": self.mission_thread_id
        }

