"""
Phase 12: Artifact Registry Store

Append-only JSONL registry for artifacts.
Read/write metadata only. No execution changes.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, List, Optional
import json

from backend.artifact_registry import Artifact


class ArtifactRegistryStore:
    """Append-only artifact registry."""

    def __init__(self, stream_file: Optional[Path] = None):
        self._stream_file = stream_file or Path("outputs/phase25/artifacts.jsonl")
        self._stream_file.parent.mkdir(parents=True, exist_ok=True)

    def register_artifact(self, artifact: Artifact) -> None:
        """Persist artifact (append-only)."""
        self._validate(artifact)
        with self._stream_file.open("a", encoding="utf-8") as f:
            json.dump(artifact.to_dict(), f)
            f.write("\n")

    def list_artifacts(self, filters: Optional[Dict[str, Any]] = None) -> List[Artifact]:
        """List artifacts, optionally filtered by fields."""
        artifacts = self._read_all()
        if not filters:
            return artifacts

        def _matches(a: Artifact) -> bool:
            for key, value in filters.items():
                if value is None:
                    continue
                if not hasattr(a, key):
                    return False
                if getattr(a, key) != value:
                    return False
            return True

        return [a for a in artifacts if _matches(a)]

    def get_artifacts_by_mission(self, mission_id: str) -> List[Artifact]:
        """Get artifacts created by a mission."""
        return [a for a in self._read_all() if a.created_by == mission_id]

    def get_latest_artifact_by_type(self, artifact_type: str) -> Optional[Artifact]:
        """Get most recent artifact by type."""
        matches = [a for a in self._read_all() if a.artifact_type.value == artifact_type]
        return matches[-1] if matches else None

    def _read_all(self) -> List[Artifact]:
        if not self._stream_file.exists():
            return []
        items: List[Artifact] = []
        with self._stream_file.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                items.append(Artifact.from_dict(data))
        return items

    def _validate(self, artifact: Artifact) -> None:
        if not artifact.artifact_id:
            raise ValueError("artifact_id is required")
        if not artifact.title:
            raise ValueError("title is required")
        if not artifact.description:
            raise ValueError("description is required")
        if not artifact.created_by:
            raise ValueError("created_by is required")
        if not artifact.source_module:
            raise ValueError("source_module is required")
        if not artifact.created_at:
            raise ValueError("created_at is required")
