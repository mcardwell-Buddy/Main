"""
Artifact Writer

Append-only JSONL writer for durable artifacts.
NO reads. NO updates. NO deletes.
"""

import json
from pathlib import Path
from typing import Dict, Any


class ArtifactWriter:
    """Append-only artifact writer."""

    def __init__(self, log_path: str = "outputs/phase25/artifacts.jsonl"):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def write_artifact(self, artifact: Dict[str, Any]) -> None:
        """Append a single artifact record (one JSON object per line)."""
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(artifact, ensure_ascii=False) + "\n")


def get_artifact_writer(log_path: str = "outputs/phase25/artifacts.jsonl") -> ArtifactWriter:
    """Get a new artifact writer instance."""
    return ArtifactWriter(log_path)

