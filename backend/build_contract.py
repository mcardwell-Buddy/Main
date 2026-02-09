"""
Phase 11: Build Contract

Defines the deterministic, immutable schema for Build objects.
A build is a governed container for missions and artifacts.

Hard constraints:
- NO autonomy
- NO execution
- READ-ONLY schema
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Dict, Any
import uuid


class BuildType(Enum):
    """Allowed build types."""
    SOFTWARE = "software"
    MODEL = "model"
    CONTENT = "content"
    SYSTEM = "system"
    RESEARCH = "research"


class BuildStage(Enum):
    """Build lifecycle stages."""
    DESIGN = "design"
    IMPLEMENTATION = "implementation"
    VALIDATION = "validation"
    ITERATION = "iteration"
    COMPLETE = "complete"


class BuildStatus(Enum):
    """Build status values."""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABORTED = "aborted"


@dataclass(frozen=True)
class BuildContract:
    """Immutable build contract."""
    build_id: str
    name: str
    objective: str
    build_type: BuildType
    current_stage: BuildStage
    created_at: str
    updated_at: str
    mission_ids: List[str] = field(default_factory=list)
    artifact_ids: List[str] = field(default_factory=list)
    investment_score: Optional[float] = None
    status: BuildStatus = BuildStatus.ACTIVE

    @staticmethod
    def new(
        name: str,
        objective: str,
        build_type: BuildType,
        current_stage: BuildStage = BuildStage.DESIGN,
        mission_ids: Optional[List[str]] = None,
        artifact_ids: Optional[List[str]] = None,
        investment_score: Optional[float] = None,
        status: BuildStatus = BuildStatus.ACTIVE,
    ) -> "BuildContract":
        """Create a new build contract with generated ID and timestamps."""
        now = datetime.now(timezone.utc).isoformat()
        return BuildContract(
            build_id=str(uuid.uuid4()),
            name=name,
            objective=objective,
            build_type=build_type,
            current_stage=current_stage,
            created_at=now,
            updated_at=now,
            mission_ids=mission_ids or [],
            artifact_ids=artifact_ids or [],
            investment_score=investment_score,
            status=status,
        )

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "BuildContract":
        """Deserialize from dictionary."""
        return BuildContract(
            build_id=data.get("build_id") or str(uuid.uuid4()),
            name=data.get("name", ""),
            objective=data.get("objective", ""),
            build_type=BuildType(data.get("build_type", BuildType.SOFTWARE.value)),
            current_stage=BuildStage(data.get("current_stage", BuildStage.DESIGN.value)),
            created_at=data.get("created_at") or datetime.now(timezone.utc).isoformat(),
            updated_at=data.get("updated_at") or datetime.now(timezone.utc).isoformat(),
            mission_ids=list(data.get("mission_ids", [])),
            artifact_ids=list(data.get("artifact_ids", [])),
            investment_score=data.get("investment_score"),
            status=BuildStatus(data.get("status", BuildStatus.ACTIVE.value)),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "build_id": self.build_id,
            "name": self.name,
            "objective": self.objective,
            "build_type": self.build_type.value,
            "current_stage": self.current_stage.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "mission_ids": list(self.mission_ids),
            "artifact_ids": list(self.artifact_ids),
            "investment_score": self.investment_score,
            "status": self.status.value,
        }
