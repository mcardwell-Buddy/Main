"""
Phase 2 Step 5 Validation: Mission Progress & Completion Detection
"""

import json
from pathlib import Path

from backend.agents.web_navigator_agent import WebNavigatorAgent
from backend.mission_control.mission_contract import MissionContract


def _latest_mission_status(mission_id: str) -> dict:
    missions_file = Path("outputs/phase25/missions.jsonl")
    latest = {}
    if not missions_file.exists():
        return latest
    with open(missions_file, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("event_type") == "mission_status_update" and record.get("mission_id") == mission_id:
                latest = record
    return latest


def _mission_signals(mission_id: str) -> list:
    signals_file = Path("outputs/phase25/learning_signals.jsonl")
    signals = []
    if not signals_file.exists():
        return signals
    with open(signals_file, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            signal = json.loads(line)
            if signal.get("mission_id") == mission_id:
                signals.append(signal)
    return signals


def run_validation():
    mission = MissionContract.new(
        objective={
            "type": "quantitative",
            "description": "Collect at least 5 items",
            "target": 5,
            "required_fields": ["name", "url"]
        },
        scope={
            "allowed_domains": ["quotes.toscrape.com"],
            "max_pages": 1,
            "max_duration_seconds": 30
        },
        authority={
            "execution_mode": "guided",
            "external_actions_allowed": ["navigate"]
        },
        success_conditions={
            "min_items_collected": 5
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
        "expected_fields": ["name", "url"],
        "max_pages": 1,
        "execution_mode": "LIVE",
        "mission_contract": mission.to_dict()
    }

    agent = WebNavigatorAgent()
    result = agent.run(payload)

    latest_status = _latest_mission_status(mission.mission_id)
    mission_signals = _mission_signals(mission.mission_id)

    progress_signals = [s for s in mission_signals if s.get("signal_type") == "mission_progress_update"]
    completed_signals = [s for s in mission_signals if s.get("signal_type") == "mission_completed"]
    failed_signals = [s for s in mission_signals if s.get("signal_type") == "mission_failed"]

    print("=== PHASE 2 STEP 5 VALIDATION ===")
    print(f"Mission ID: {mission.mission_id}")
    print(f"Run status: {result.get('status')}")
    print(f"Final mission status: {latest_status.get('status')}")
    print(f"Stop reason: {latest_status.get('reason')}")
    print(f"Progress signals: {len(progress_signals)}")
    print(f"Completed signals: {len(completed_signals)}")
    print(f"Failed signals: {len(failed_signals)}")
    print("=================================")


if __name__ == "__main__":
    run_validation()
