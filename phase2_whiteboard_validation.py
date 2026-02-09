"""
Phase 2 Whiteboard Validation: Read-only Mission Whiteboard
"""

import json
from pathlib import Path

from backend.whiteboard.mission_whiteboard import get_mission_whiteboard


def _latest_completed_mission_id() -> str:
    missions_file = Path("outputs/phase25/missions.jsonl")
    if not missions_file.exists():
        return ""
    latest_completed = ""
    with open(missions_file, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("event_type") == "mission_status_update" and record.get("status") == "completed":
                latest_completed = record.get("mission_id", "")
    return latest_completed


def run_validation() -> None:
    mission_id = _latest_completed_mission_id()
    if not mission_id:
        print("No completed missions found.")
        return

    whiteboard = get_mission_whiteboard(mission_id)

    required_keys = {
        "mission_id",
        "status",
        "objective",
        "start_time",
        "end_time",
        "constraints",
        "progress",
        "navigation_summary",
        "selector_summary",
        "termination"
    }

    print("=== WHITEBOARD VIEW ===")
    print(json.dumps(whiteboard, indent=2))

    missing = required_keys - set(whiteboard.keys())
    if missing:
        print(f"[X] Missing keys: {sorted(missing)}")
    else:
        print("[OK] All required sections present")

    print("[OK] Read-only reconstruction complete")


if __name__ == "__main__":
    run_validation()
