"""
Artifact Reader

Read-only helper to load latest artifacts by mission_id.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional


ARTIFACTS_FILE = Path("outputs/phase25/artifacts.jsonl")


def get_latest_artifact(mission_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Load the latest artifact, optionally filtered by mission_id.

    This is a direct file read with no indexing.
    """
    if not ARTIFACTS_FILE.exists():
        return None

    latest = None
    with ARTIFACTS_FILE.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if mission_id is None or record.get("mission_id") == mission_id:
                latest = record

    return latest
