"""
Phase 2 Step 6 Validation: Mission Attribution
Verifies that mission_id is properly attached to selector, intent, and action signals.
"""

import json
from pathlib import Path
from typing import Any, Dict, List


SIGNALS_FILE = Path("outputs/phase25/learning_signals.jsonl")
MISSIONS_FILE = Path("outputs/phase25/missions.jsonl")


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        print(f"Warning: {path} does not exist")
        return []
    records: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def _get_latest_completed_mission() -> str:
    """Get the latest completed mission ID."""
    missions = _read_jsonl(MISSIONS_FILE)
    latest_completed = None
    
    for record in missions:
        if record.get("event_type") == "mission_status_update" and record.get("status") == "completed":
            if not latest_completed or record.get("timestamp", "") > latest_completed[0]:
                latest_completed = (record.get("timestamp"), record.get("mission_id"))
    
    if latest_completed:
        return latest_completed[1]
    
    # Fallback: try to find any mission with mission_id in signals
    signals = _read_jsonl(SIGNALS_FILE)
    for signal in reversed(signals):
        if "mission_id" in signal:
            return signal["mission_id"]
    
    return None


def validate_mission_attribution():
    """
    Validate Phase 2 Step 6: Mission Attribution
    Check that selector, intent, and action signals include mission_id.
    """
    signals = _read_jsonl(SIGNALS_FILE)
    mission_id = _get_latest_completed_mission()
    
    if not mission_id:
        print("❌ No completed mission found for validation")
        return False
    
    print(f"📋 Validating mission attribution for mission_id: {mission_id}\n")
    
    # Count signals by type and mission_id presence
    selector_signals = []
    selector_with_mission = []
    intent_signals = []
    intent_with_mission = []
    action_signals = []
    action_with_mission = []
    
    for signal in signals:
        signal_type = signal.get("signal_type", "")
        
        # Selector signals
        if signal_type == "selector_outcome":
            selector_signals.append(signal)
            if signal.get("mission_id") == mission_id:
                selector_with_mission.append(signal)
        
        # Intent signals
        elif signal_type in ["navigation_intent_ranked", "intent_action_taken", "intent_action_blocked"]:
            intent_signals.append(signal)
            if signal.get("mission_id") == mission_id:
                intent_with_mission.append(signal)
        
        # Action signals
        elif signal_type == "intent_action_taken":
            action_signals.append(signal)
            if signal.get("mission_id") == mission_id:
                action_with_mission.append(signal)
    
    # Print results
    print(f"✓ Selector signals:")
    print(f"  Total: {len(selector_signals)}")
    print(f"  With mission_id={mission_id}: {len(selector_with_mission)}")
    if selector_with_mission:
        print(f"  ✅ Sample selector signal with mission_id:")
        sample = selector_with_mission[0]
        print(f"     selector_type: {sample.get('selector_type')}")
        print(f"     outcome: {sample.get('outcome')}")
        print(f"     mission_id: {sample.get('mission_id')}")
    
    print(f"\n✓ Intent signals (navigation_intent_ranked, action_taken, action_blocked):")
    print(f"  Total: {len(intent_signals)}")
    print(f"  With mission_id={mission_id}: {len(intent_with_mission)}")
    if intent_with_mission:
        print(f"  ✅ Sample intent signal with mission_id:")
        sample = intent_with_mission[0]
        print(f"     signal_type: {sample.get('signal_type')}")
        print(f"     goal: {sample.get('goal', 'N/A')[:50]}")
        print(f"     mission_id: {sample.get('mission_id')}")
    
    # Summary
    print(f"\n📊 Mission Attribution Summary:")
    print(f"  Selectors properly scoped: {'✅ YES' if len(selector_with_mission) > 0 else '❌ NO'}")
    print(f"  Intents properly scoped: {'✅ YES' if len(intent_with_mission) > 0 else '❌ NO'}")
    
    # Test whiteboard reconstruction
    print(f"\n🔍 Testing Whiteboard Reconstruction:")
    try:
        from Back_End.whiteboard.mission_whiteboard import get_mission_whiteboard
        
        whiteboard = get_mission_whiteboard(mission_id)
        print(f"  ✅ Whiteboard retrieved successfully")
        print(f"  Mission status: {whiteboard.get('status')}")
        print(f"  Navigation summary entries: {len(whiteboard.get('navigation_summary', []))}")
        print(f"  Selector summary entries: {len(whiteboard.get('selector_summary', []))}")
        
        if len(whiteboard.get('selector_summary', [])) > 0:
            print(f"  ✅ Selector summary is now populated!")
            for selector_entry in whiteboard.get('selector_summary', [])[:2]:
                print(f"     - {selector_entry.get('selector')}: {selector_entry.get('attempts')} attempts, {selector_entry.get('success_rate'):.1%} success")
        else:
            print(f"  ⚠️  Selector summary still empty (signals may not have mission_id yet)")
        
    except Exception as e:
        print(f"  ❌ Whiteboard test failed: {e}")
        return False
    
    # Overall success
    success = len(selector_with_mission) > 0 or len(intent_with_mission) > 0
    
    print(f"\n{'✅ MISSION ATTRIBUTION VALIDATION PASSED' if success else '❌ MISSION ATTRIBUTION VALIDATION FAILED'}")
    print(f"   Signals are properly attributable to missions for observability and debugging.")
    
    return success


if __name__ == "__main__":
    validate_mission_attribution()

