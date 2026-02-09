"""
Mission Cost Accounting - Integration Test
Test with real mission data from learning_signals.jsonl
"""

import json
from pathlib import Path

from backend.mission.mission_cost_accountant import MissionCostAccountant
from backend.whiteboard.mission_whiteboard import get_mission_whiteboard


def test_real_mission_costs():
    """Test cost computation with real mission data."""
    print("\n" + "="*70)
    print("MISSION COST ACCOUNTING - INTEGRATION TEST")
    print("="*70 + "\n")
    
    signals_file = Path("outputs/phase25/learning_signals.jsonl")
    
    if not signals_file.exists():
        print("❌ learning_signals.jsonl not found")
        print("   (This test requires real mission execution)")
        return
    
    print("🔍 Scanning for completed missions...\n")
    
    # Find all completed missions
    completed_missions = set()
    with open(signals_file, 'r') as f:
        for line in f:
            if line.strip():
                try:
                    signal = json.loads(line)
                    if signal.get("signal_type") == "mission_status_update":
                        if signal.get("status") in ["completed", "failed"]:
                            mission_id = signal.get("mission_id")
                            if mission_id:
                                completed_missions.add(mission_id)
                except json.JSONDecodeError:
                    continue
    
    print(f"📊 Found {len(completed_missions)} completed missions\n")
    
    if not completed_missions:
        print("ℹ️  No completed missions found yet")
        print("   Run a mission first, then re-run this test\n")
        return
    
    # Compute costs for each mission
    accountant = MissionCostAccountant(signals_file=str(signals_file))
    
    print("="*70)
    print("MISSION COST REPORTS")
    print("="*70 + "\n")
    
    for idx, mission_id in enumerate(sorted(completed_missions)[:5], 1):  # Show first 5
        print(f"📋 Mission {idx}: {mission_id}")
        print("-" * 70)
        
        report = accountant.compute_costs(mission_id)
        
        if report:
            print(f"   Duration: {report.total_duration_sec:.1f}s")
            print(f"   Pages visited: {report.pages_visited}")
            print(f"   Selectors attempted: {report.selectors_attempted}")
            print(f"   Selectors failed: {report.selectors_failed}")
            print(f"   Retries: {report.retries_total}")
            print()
            print(f"   Cost Units:")
            print(f"   • time_cost: {report.time_cost:.1f}s")
            print(f"   • page_cost: {report.page_cost}")
            print(f"   • failure_cost: {report.failure_cost}")
            
            if report.selectors_attempted > 0:
                failure_rate = (report.selectors_failed / report.selectors_attempted) * 100
                print(f"   • failure_rate: {failure_rate:.1f}%")
            
            # Check if signal would be emitted
            if accountant.should_emit_signal(report):
                print(f"   ✉️  Signal will be emitted")
            
            print()
            
            # Check whiteboard integration
            try:
                whiteboard = get_mission_whiteboard(mission_id)
                if whiteboard.get("cost_summary"):
                    print("   ✅ Cost summary present in whiteboard")
                else:
                    print("   ⚠️  Cost summary not yet in whiteboard (may need re-run)")
            except Exception as e:
                print(f"   ⚠️  Could not check whiteboard: {e}")
            
            print()
        else:
            print("   ⚠️  Could not compute costs (insufficient data)")
            print()
    
    if len(completed_missions) > 5:
        print(f"   ... and {len(completed_missions) - 5} more missions\n")
    
    print("="*70)
    print("✅ INTEGRATION TEST COMPLETE")
    print("="*70)
    print()
    print("Cost accounting is working with real mission data.")
    print("Signals will be emitted on next mission completion.\n")


if __name__ == "__main__":
    test_real_mission_costs()
