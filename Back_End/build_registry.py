"""
Phase 11: Build Registry

Append-only persistence for build lifecycle events.
Read-only governance - no execution logic.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List
import json

from Back_End.build_contract import BuildContract, BuildStage, BuildStatus


class BuildRegistry:
    """Persist build lifecycle events to JSONL (append-only)."""

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or (Path(__file__).parent.parent / "outputs" / "phase11")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.builds_file = self.output_dir / "builds.jsonl"

    def register_build(self, contract: BuildContract) -> None:
        """Register a new build contract."""
        record = {
            "event_type": "build_created",
            "build": contract.to_dict(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._append_record(record)

    def update_stage(
        self,
        build_id: str,
        new_stage: BuildStage,
        reason: str,
        readiness: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Persist a build stage update (no execution)."""
        record = {
            "event_type": "build_stage_update",
            "build_id": build_id,
            "new_stage": new_stage.value,
            "reason": reason,
            "readiness": readiness or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._append_record(record)

    def update_status(
        self,
        build_id: str,
        status: BuildStatus,
        reason: str,
        completed_at: Optional[str] = None,
    ) -> None:
        """Persist a build status update (no execution)."""
        record = {
            "event_type": "build_status_update",
            "build_id": build_id,
            "status": status.value,
            "reason": reason,
            "completed_at": completed_at,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._append_record(record)

    def attach_artifact(
        self,
        build_id: str,
        artifact_id: str,
        artifact_type: str,
        reason: Optional[str] = None,
    ) -> None:
        """Record artifact attachment to build (append-only)."""
        record = {
            "event_type": "build_artifact_attached",
            "build_id": build_id,
            "artifact_id": artifact_id,
            "artifact_type": artifact_type,
            "reason": reason or "artifact_registered",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._append_record(record)

    def update_investment_score(self, build_id: str, score: float, reason: str) -> None:
        """Record investment score update (append-only)."""
        record = {
            "event_type": "build_investment_update",
            "build_id": build_id,
            "investment_score": score,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._append_record(record)

    def read_records(self) -> List[Dict[str, Any]]:
        """Read all build event records from JSONL."""
        if not self.builds_file.exists():
            return []

        records: List[Dict[str, Any]] = []
        with self.builds_file.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return records

    def get_latest_builds(self) -> Dict[str, BuildContract]:
        """Reconstruct latest build state from event log."""
        records = self.read_records()
        builds: Dict[str, BuildContract] = {}

        for record in records:
            event_type = record.get("event_type")

            if event_type == "build_created":
                build_data = record.get("build", {})
                build = BuildContract.from_dict(build_data)
                builds[build.build_id] = build
                continue

            build_id = record.get("build_id")
            if not build_id or build_id not in builds:
                continue

            current = builds[build_id]

            if event_type == "build_stage_update":
                builds[build_id] = BuildContract(
                    build_id=current.build_id,
                    name=current.name,
                    objective=current.objective,
                    build_type=current.build_type,
                    current_stage=BuildStage(record.get("new_stage", current.current_stage.value)),
                    created_at=current.created_at,
                    updated_at=record.get("timestamp", current.updated_at),
                    mission_ids=list(current.mission_ids),
                    artifact_ids=list(current.artifact_ids),
                    investment_score=current.investment_score,
                    status=current.status,
                )
            elif event_type == "build_status_update":
                builds[build_id] = BuildContract(
                    build_id=current.build_id,
                    name=current.name,
                    objective=current.objective,
                    build_type=current.build_type,
                    current_stage=current.current_stage,
                    created_at=current.created_at,
                    updated_at=record.get("timestamp", current.updated_at),
                    mission_ids=list(current.mission_ids),
                    artifact_ids=list(current.artifact_ids),
                    investment_score=current.investment_score,
                    status=BuildStatus(record.get("status", current.status.value)),
                )
            elif event_type == "build_artifact_attached":
                artifact_ids = list(current.artifact_ids)
                artifact_id = record.get("artifact_id")
                if artifact_id and artifact_id not in artifact_ids:
                    artifact_ids.append(artifact_id)
                builds[build_id] = BuildContract(
                    build_id=current.build_id,
                    name=current.name,
                    objective=current.objective,
                    build_type=current.build_type,
                    current_stage=current.current_stage,
                    created_at=current.created_at,
                    updated_at=record.get("timestamp", current.updated_at),
                    mission_ids=list(current.mission_ids),
                    artifact_ids=artifact_ids,
                    investment_score=current.investment_score,
                    status=current.status,
                )
            elif event_type == "build_investment_update":
                builds[build_id] = BuildContract(
                    build_id=current.build_id,
                    name=current.name,
                    objective=current.objective,
                    build_type=current.build_type,
                    current_stage=current.current_stage,
                    created_at=current.created_at,
                    updated_at=record.get("timestamp", current.updated_at),
                    mission_ids=list(current.mission_ids),
                    artifact_ids=list(current.artifact_ids),
                    investment_score=record.get("investment_score", current.investment_score),
                    status=current.status,
                )

        return builds

    def _append_record(self, record: Dict[str, Any]) -> None:
        with self.builds_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

