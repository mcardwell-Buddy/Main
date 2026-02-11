"""
Phase 12.2: Build → Deliverable Contract

Formalizes build outputs as first-class deliverables.
Read-only persistence, no pricing, no selling, no execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Any
import json
import uuid


class DeliverableType(Enum):
    """Allowed deliverable types."""
    DOCUMENT = "document"
    DATASET = "dataset"
    CODE = "code"
    REPORT = "report"
    FORECAST = "forecast"
    ANALYSIS = "analysis"


class DeliverableReadiness(Enum):
    """Deliverable readiness states."""
    DRAFT = "draft"
    REVIEWABLE = "reviewable"
    FINAL = "final"


@dataclass(frozen=True)
class BuildDeliverable:
    """Immutable build deliverable record."""
    deliverable_id: str
    build_id: str
    deliverable_type: DeliverableType
    format: str
    description: str
    completeness_score: float
    readiness_state: DeliverableReadiness
    timestamp: str
    mission_id: Optional[str] = None

    @staticmethod
    def new(
        build_id: str,
        deliverable_type: DeliverableType,
        format: str,
        description: str,
        completeness_score: float,
        readiness_state: DeliverableReadiness,
        mission_id: Optional[str] = None,
    ) -> "BuildDeliverable":
        """Create a new build deliverable with generated ID and timestamp."""
        return BuildDeliverable(
            deliverable_id=str(uuid.uuid4()),
            build_id=build_id,
            deliverable_type=deliverable_type,
            format=format,
            description=description,
            completeness_score=completeness_score,
            readiness_state=readiness_state,
            timestamp=datetime.now(timezone.utc).isoformat(),
            mission_id=mission_id,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "deliverable_id": self.deliverable_id,
            "build_id": self.build_id,
            "type": self.deliverable_type.value,
            "format": self.format,
            "description": self.description,
            "completeness_score": self.completeness_score,
            "readiness_state": self.readiness_state.value,
            "timestamp": self.timestamp,
            "mission_id": self.mission_id,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "BuildDeliverable":
        """Deserialize from dictionary."""
        return BuildDeliverable(
            deliverable_id=data.get("deliverable_id") or str(uuid.uuid4()),
            build_id=data.get("build_id", ""),
            deliverable_type=DeliverableType(data.get("type", DeliverableType.DOCUMENT.value)),
            format=data.get("format", ""),
            description=data.get("description", ""),
            completeness_score=float(data.get("completeness_score", 0.0)),
            readiness_state=DeliverableReadiness(
                data.get("readiness_state", DeliverableReadiness.DRAFT.value)
            ),
            timestamp=data.get("timestamp") or datetime.now(timezone.utc).isoformat(),
            mission_id=data.get("mission_id"),
        )


class DeliverableRegistry:
    """Append-only registry for build deliverables."""

    def __init__(self, stream_file: Optional[Path] = None):
        self._stream_file = stream_file or Path("outputs/phase25/build_deliverables.jsonl")
        self._stream_file.parent.mkdir(parents=True, exist_ok=True)

    def register_deliverable(self, deliverable: BuildDeliverable) -> None:
        """Persist deliverable (append-only)."""
        self._validate(deliverable)
        with self._stream_file.open("a", encoding="utf-8") as f:
            json.dump(deliverable.to_dict(), f)
            f.write("\n")

    def list_by_build(self, build_id: str) -> List[BuildDeliverable]:
        """List deliverables for a build."""
        return [d for d in self._read_all() if d.build_id == build_id]

    def list_by_mission(self, mission_id: str) -> List[BuildDeliverable]:
        """List deliverables created from a mission."""
        return [d for d in self._read_all() if d.mission_id == mission_id]

    def _read_all(self) -> List[BuildDeliverable]:
        if not self._stream_file.exists():
            return []
        items: List[BuildDeliverable] = []
        with self._stream_file.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                items.append(BuildDeliverable.from_dict(data))
        return items

    def _validate(self, deliverable: BuildDeliverable) -> None:
        if not deliverable.deliverable_id:
            raise ValueError("deliverable_id is required")
        if not deliverable.build_id:
            raise ValueError("build_id is required")
        if not isinstance(deliverable.deliverable_type, DeliverableType):
            raise ValueError("type must be DeliverableType")
        if not isinstance(deliverable.readiness_state, DeliverableReadiness):
            raise ValueError("readiness_state must be DeliverableReadiness")
        if not isinstance(deliverable.completeness_score, (float, int)):
            raise ValueError("completeness_score must be a number")
        if deliverable.completeness_score < 0.0 or deliverable.completeness_score > 1.0:
            raise ValueError("completeness_score must be between 0 and 1")
        if not deliverable.format:
            raise ValueError("format is required")
        if not deliverable.description:
            raise ValueError("description is required")
        if not deliverable.timestamp:
            raise ValueError("timestamp is required")

