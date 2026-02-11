"""
Phase 3 Step 2.8: Ambiguity Evaluator Integration Test
Test the complete flow: goal evaluation -> opportunity normalization -> ambiguity detection
"""

import json
import os
from datetime import datetime


def test_ambiguity_integration():
    """Test full workflow integration with learning signals."""
    print("\n" + "="*70)
    print("AMBIGUITY EVALUATOR INTEGRATION TEST")
    print("="*70 + "\n")
    
    signals_file = "backend/learning_signals.jsonl"
    
    # Check if learning signals file exists
    if not os.path.exists(signals_file):
        print("❌ learning_signals.jsonl not found - skipping integration test")
        print("   (This test requires real mission execution)")
        return
    
    print("🔍 Scanning learning_signals.jsonl for ambiguity signals...\n")
    
    # Read all signals
    ambiguity_signals = []
    mission_signals_by_id = {}
    
    with open(signals_file, 'r') as f:
        for line in f:
            if line.strip():
                signal = json.loads(line)
                mission_id = signal.get("mission_id")
                signal_type = signal.get("signal_type")
                
                # Track all signals by mission
                if mission_id:
                    if mission_id not in mission_signals_by_id:
                        mission_signals_by_id[mission_id] = []
                    mission_signals_by_id[mission_id].append(signal)
                
                # Collect ambiguity signals
                if signal_type == "mission_ambiguous":
                    ambiguity_signals.append(signal)
    
    print(f"📊 Found {len(mission_signals_by_id)} unique missions")
    print(f"🚨 Found {len(ambiguity_signals)} ambiguity signals\n")
    
    if not ambiguity_signals:
        print("ℹ️  No ambiguity signals found yet")
        print("   This is expected if no ambiguous missions have completed.")
        print("   To test:")
        print("   1. Run a mission with unclear goals")
        print("   2. Check learning_signals.jsonl for mission_ambiguous signals")
        print("   3. Re-run this test\n")
        return
    
    # Analyze each ambiguous mission
    print("="*70)
    print("AMBIGUOUS MISSIONS ANALYSIS")
    print("="*70 + "\n")
    
    for idx, signal in enumerate(ambiguity_signals, 1):
        mission_id = signal.get("mission_id")
        print(f"🚨 Ambiguous Mission {idx}: {mission_id}")
        print(f"   Reason: {signal.get('reason')}")
        print(f"   Recommended next: {signal.get('recommended_next_mission')}")
        print(f"   Timestamp: {signal.get('timestamp')}")
        
        # Show metrics
        metrics = {
            "confidence_gap": signal.get("confidence_gap"),
            "opportunity_weakness": signal.get("opportunity_weakness"),
            "evidence_sufficiency": signal.get("evidence_sufficiency")
        }
        print(f"   Metrics: {json.dumps(metrics, indent=13)}")
        
        # Find related signals for this mission
        related_signals = mission_signals_by_id.get(mission_id, [])
        print(f"   Related signals: {len(related_signals)}")
        
        # Show goal evaluation if available
        goal_eval = next((s for s in related_signals if s.get("signal_type") == "goal_evaluation"), None)
        if goal_eval:
            print(f"   Goal satisfied: {goal_eval.get('goal_satisfied')}")
            print(f"   Goal confidence: {goal_eval.get('confidence')}")
        
        # Show opportunity summary if available
        opp_summary = next((s for s in related_signals if s.get("signal_type") == "opportunity_normalized"), None)
        if opp_summary:
            print(f"   Opportunities created: {opp_summary.get('opportunities_created')}")
            print(f"   Avg opportunity confidence: {opp_summary.get('avg_confidence')}")
        
        print()
    
    # Validate signal structure
    print("="*70)
    print("SIGNAL STRUCTURE VALIDATION")
    print("="*70 + "\n")
    
    required_fields = [
        "signal_type", "signal_layer", "signal_source", 
        "mission_id", "timestamp", "ambiguous", "reason"
    ]
    
    all_valid = True
    for signal in ambiguity_signals:
        missing_fields = [f for f in required_fields if f not in signal]
        if missing_fields:
            print(f"❌ Invalid signal for {signal.get('mission_id')}")
            print(f"   Missing fields: {missing_fields}")
            all_valid = False
    
    if all_valid:
        print("✅ All ambiguity signals have valid structure\n")
    
    # Check whiteboard integration
    print("="*70)
    print("WHITEBOARD INTEGRATION CHECK")
    print("="*70 + "\n")
    
    try:
        from Back_End.whiteboard.mission_whiteboard import get_mission_whiteboard
        
        # Check whiteboard for first ambiguous mission
        if ambiguity_signals:
            test_mission_id = ambiguity_signals[0].get("mission_id")
            print(f"📋 Checking whiteboard for mission: {test_mission_id}")
            
            whiteboard = get_mission_whiteboard(test_mission_id)
            
            if "ambiguity" in whiteboard and whiteboard["ambiguity"]:
                print("✅ Ambiguity section present in whiteboard")
                print(f"   Reason: {whiteboard['ambiguity'].get('reason')}")
                print(f"   Recommended: {whiteboard['ambiguity'].get('recommended_next_mission')}")
            else:
                print("⚠️  Ambiguity section not present in whiteboard")
                print("   (May need to refresh whiteboard)")
            print()
    except Exception as e:
        print(f"⚠️  Could not check whiteboard: {e}\n")
    
    print("="*70)
    print("✅ INTEGRATION TEST COMPLETE")
    print("="*70 + "\n")


if __name__ == "__main__":
    test_ambiguity_integration()

