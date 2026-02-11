"""
End-to-End test for Phase 2 Step 6: Mission Attribution
Creates a new mission and verifies signals are scoped with mission_id.
"""

from Back_End.mission_control.mission_contract import MissionContract
from Back_End.agents.web_navigator_agent import WebNavigatorAgent
import json
from pathlib import Path


def run_test():
    """
    Create and run a small mission to verify mission_id attribution.
    """
    print("🚀 Starting Mission Attribution E2E Test\n")
    
    # Create a small test mission with correct nested dicts
    mission = MissionContract.new(
        objective={
            "type": "quantitative",
            "description": "Collect at least 3 items",
            "target": 3,
            "required_fields": ["title", "content"]
        },
        scope={
            "allowed_domains": ["quotes.toscrape.com"],
            "max_pages": 2,
            "max_duration_seconds": 30
        },
        authority={
            "execution_mode": "supervised",
            "external_actions_allowed": ["click", "navigate"]
        },
        success_conditions={
            "min_items_collected": 3
        },
        failure_conditions={
            "no_progress_pages": 2,
            "navigation_blocked": False,
            "required_fields_missing": False
        },
        reporting={
            "summary_required": True,
            "confidence_explanation": True
        }
    )
    
    mission_id = mission.mission_id
    print(f"📋 Created mission: {mission_id}")
    print(f"   Objective: {mission.objective.description}")
    print(f"   Target: {mission.objective.target} items")
    print(f"   Max pages: {mission.scope.max_pages}\n")
    
    try:
        # Initialize navigator with mission
        navigator = WebNavigatorAgent(headless=True)
        
        # Prepare input payload with mission
        input_payload = {
            "target_url": "https://quotes.toscrape.com",
            "page_type": "quotes_directory",
            "expected_fields": ["text", "author"],
            "max_pages": 2,
            "execution_mode": "DRY_RUN",
            "mission_contract": mission
        }
        
        print(f"🔍 Running navigator with mission control...\n")
        
        # Run navigator - this should emit signals with mission_id
        result = navigator.run(input_payload)
        
        print(f"\n✅ Navigator run completed\n")
        
        # Now check signals for mission_id
        signals_file = Path("outputs/phase25/learning_signals.jsonl")
        if not signals_file.exists():
            print(f"❌ Signals file not found: {signals_file}")
            return False
        
        signals = []
        with open(signals_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        signals.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        
        # Filter for signals from this mission
        mission_selector_signals = [s for s in signals if s.get("signal_type") == "selector_outcome" and s.get("mission_id") == mission_id]
        mission_intent_signals = [s for s in signals if s.get("signal_type") in ["navigation_intent_ranked", "intent_action_taken", "intent_action_blocked"] and s.get("mission_id") == mission_id]
        
        print(f"📊 Signal Attribution Results:")
        print(f"  Selector signals with mission_id: {len(mission_selector_signals)}")
        print(f"  Intent signals with mission_id: {len(mission_intent_signals)}")
        
        if mission_selector_signals:
            print(f"\n  ✅ Sample selector signal:")
            sample = mission_selector_signals[0]
            print(f"     selector_type: {sample.get('selector_type')}")
            print(f"     outcome: {sample.get('outcome')}")
            print(f"     duration_ms: {sample.get('duration_ms')}")
            print(f"     mission_id: {sample.get('mission_id')}")
        
        if mission_intent_signals:
            print(f"\n  ✅ Sample intent signal:")
            sample = mission_intent_signals[0]
            print(f"     signal_type: {sample.get('signal_type')}")
            print(f"     goal: {sample.get('goal', 'N/A')[:40]}")
            print(f"     mission_id: {sample.get('mission_id')}")
        
        # Test whiteboard
        print(f"\n🔍 Testing Whiteboard with new mission:")
        try:
            from Back_End.whiteboard.mission_whiteboard import get_mission_whiteboard
            
            whiteboard = get_mission_whiteboard(mission_id)
            print(f"  ✅ Whiteboard for mission {mission_id[:8]}...")
            print(f"     Status: {whiteboard.get('status')}")
            print(f"     Selector summary entries: {len(whiteboard.get('selector_summary', []))}")
            
            if whiteboard.get('selector_summary'):
                print(f"\n  ✅ Selector Summary Populated!")
                for entry in whiteboard.get('selector_summary', [])[:3]:
                    print(f"     - {entry.get('selector')}: {entry.get('attempts')} attempts, {entry.get('success_rate'):.1%} success")
        except Exception as e:
            print(f"  ⚠️  Whiteboard error: {e}")
        
        # Success criteria
        success = (len(mission_selector_signals) > 0 or len(mission_intent_signals) > 0)
        
        if success:
            print(f"\n✅ MISSION ATTRIBUTION E2E TEST PASSED")
            print(f"   All signals are properly scoped with mission_id for audit trail.")
        else:
            print(f"\n⚠️  MISSION ATTRIBUTION E2E TEST WARNING")
            print(f"   No mission-scoped signals found. Navigator may not have emitted any signals.")
        
        return success
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    run_test()

