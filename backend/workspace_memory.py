"""
Workspace Memory

Provides recent missions and artifact previews for UI context.
Deterministic, read-only. No execution.
"""

from __future__ import annotations

from typing import Dict, Any, List, Optional
from pathlib import Path
import json

from backend.mission_store import get_mission_store
from backend.artifact_preview_generator import ArtifactPreviewGenerator


class WorkspaceMemory:
    """Read-only workspace context helpers."""

    def __init__(self, artifacts_path: Optional[Path] = None) -> None:
        self._artifacts_path = artifacts_path or Path("outputs/phase25/artifacts.jsonl")
        self._preview_generator = ArtifactPreviewGenerator()

    def get_recent_work(self, limit: int = 10, max_artifacts_per_mission: int = 5) -> List[Dict[str, Any]]:
        """Return recent missions with artifact previews."""
        store = get_mission_store()
        missions = store.list_missions(limit=limit)
        artifacts = self._read_artifacts()

        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for artifact in artifacts:
            mission_id = artifact.get("mission_id")
            if not mission_id:
                continue
            grouped.setdefault(mission_id, []).append(artifact)

        work_items: List[Dict[str, Any]] = []
        for mission in missions:
            objective = mission.objective or {}
            objective_description = ""
            if isinstance(objective, dict):
                objective_description = objective.get("description") or objective.get("type") or ""
            else:
                objective_description = str(objective)

            mission_artifacts = grouped.get(mission.mission_id, [])[:max_artifacts_per_mission]
            artifact_previews = []
            for artifact in mission_artifacts:
                preview = self._preview_generator.generate_preview(artifact)
                artifact_previews.append({
                    "artifact_id": artifact.get("artifact_id"),
                    "artifact_type": artifact.get("artifact_type"),
                    "preview": preview,
                })

            work_items.append({
                "mission_id": mission.mission_id,
                "status": mission.status,
                "objective_description": objective_description,
                "timestamp": mission.timestamp,
                "artifacts": artifact_previews,
            })

        return work_items

    def _read_artifacts(self) -> List[Dict[str, Any]]:
        if not self._artifacts_path.exists():
            return []

        items: List[Dict[str, Any]] = []
        with self._artifacts_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    items.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return items
