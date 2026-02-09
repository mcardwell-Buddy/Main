"""
Mission Control: Mission Registry for persistent mission state.

Append-only persistence to outputs/phase25/missions.jsonl
"""

from __future__ import annotations

from typing import Dict, Any, Optional
from datetime import datetime, timezone
from pathlib import Path
import json

from backend.mission_control.mission_contract import MissionContract


class MissionRegistry:
    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or (Path(__file__).parent.parent.parent / "outputs" / "phase25")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.missions_file = self.output_dir / "missions.jsonl"
        # Cache for mission thread IDs (mission_id -> thread_id)
        self._thread_cache: Dict[str, Optional[str]] = {}

    def register_mission(self, contract: MissionContract) -> None:
        # Cache the thread_id for later use in status updates
        if contract.mission_thread_id:
            self._thread_cache[contract.mission_id] = contract.mission_thread_id
        
        record = {
            "event_type": "mission_created",
            "mission": contract.to_dict(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self._append_record(record)

    def update_status(self, mission_id: str, status: str, reason: str, completed_at: Optional[str] = None) -> None:
        # Get thread_id from cache if available
        mission_thread_id = self._thread_cache.get(mission_id)
        
        record = {
            "event_type": "mission_status_update",
            "mission_id": mission_id,
            "status": status,
            "reason": reason,
            "completed_at": completed_at,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Include mission_thread_id if present
        if mission_thread_id:
            record["mission_thread_id"] = mission_thread_id
        
        self._append_record(record)

        # Optional artifact registry hook for mission deliverables (read-only)
        try:
            if status == "completed":
                from backend.build_deliverable import DeliverableRegistry
                from backend.artifact_registry import Artifact, ArtifactType, PresentationHint, ArtifactStatus
                from backend.artifact_registry_store import ArtifactRegistryStore

                deliverable_registry = DeliverableRegistry()
                deliverables = deliverable_registry.list_by_mission(mission_id)
                if deliverables:
                    registry = ArtifactRegistryStore()
                    for deliverable in deliverables:
                        artifact = Artifact.new(
                            artifact_type=ArtifactType.BUILD_OUTPUT,
                            title=deliverable.description or "Mission Deliverable",
                            description=f"Deliverable from mission {mission_id}",
                            created_by=mission_id,
                            source_module="mission_registry",
                            presentation_hint=PresentationHint.DOCUMENT,
                            confidence=deliverable.completeness_score,
                            tags=["mission_deliverable"],
                            status=ArtifactStatus.FINAL,
                        )
                        registry.register_artifact(artifact)
        except Exception:
            pass

    def _append_record(self, record: Dict[str, Any]) -> None:
        with open(self.missions_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
