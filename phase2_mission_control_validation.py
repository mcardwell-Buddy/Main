"""
Phase 2 Step 4 Validation: Mission Control

Creates a MissionContract, runs WebNavigatorAgent under mission,
triggers stop condition, and verifies persistence and signals.
"""

import json
from pathlib import Path
from datetime import datetime, timezone

from Back_End.agents.web_navigator_agent import WebNavigatorAgent
from Back_End.mission_control.mission_contract import MissionContract


def load_latest_mission_status(mission_id: str) -> dict:
    missions_file = Path("outputs/phase25/missions.jsonl")
    latest = None
    if not missions_file.exists():
        return {}
    with open(missions_file, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("event_type") == "mission_status_update" and record.get("mission_id") == mission_id:
                latest = record
    return latest or {}


def load_mission_signals(mission_id: str) -> list:
    signals_file = Path("outputs/phase25/learning_signals.jsonl")
    signals = []
    if not signals_file.exists():
        return signals
    with open(signals_file, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            signal = json.loads(line)
            if signal.get("signal_type") == "mission_status_update" and signal.get("mission_id") == mission_id:
                signals.append(signal)
    return signals


def run_validation():
    mission = MissionContract.new(
        objective={
            "type": "navigational",
            "description": "Collect quotes listing",
            "target": None,
            "required_fields": ["text", "author"]
        },
        scope={
            "allowed_domains": ["quotes.toscrape.com"],
            "max_pages": 1,
            "max_duration_seconds": 5
        },
        authority={
            "execution_mode": "guided",
            "external_actions_allowed": ["navigate"]
        },
        success_conditions={
            "min_items_collected": None
        },
        failure_conditions={
            "no_progress_pages": 1,
            "navigation_blocked": False,
            "required_fields_missing": False
        },
        reporting={
            "summary_required": True,
            "confidence_explanation": False
        }
    )

    payload = {
        "target_url": "http://quotes.toscrape.com/",
        "page_type": "listing",
        "expected_fields": ["text", "author"],
        "max_pages": 5,
        "execution_mode": "LIVE",
        "mission_contract": mission.to_dict()
    }

    agent = WebNavigatorAgent()
    result = agent.run(payload)

    mission_status = load_latest_mission_status(mission.mission_id)
    mission_signals = load_mission_signals(mission.mission_id)

    print("=== PHASE 2 STEP 4 VALIDATION ===")
    print(f"Mission ID: {mission.mission_id}")
    print(f"Final status: {mission_status.get('status')}")
    print(f"Stop reason: {mission_status.get('reason')}")
    print(f"Signals emitted: {len(mission_signals)}")
    print(f"Run status: {result.get('status')}")
    print("=================================")


if __name__ == "__main__":
    run_validation()

