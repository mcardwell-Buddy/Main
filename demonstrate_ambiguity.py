"""
VISUAL DEMONSTRATION: Ambiguity Evaluator in Action
===================================================
"""

from backend.mission_control.ambiguity_evaluator import AmbiguityEvaluator
import json


def demonstrate_ambiguity_detection():
    """Show visual examples of ambiguity detection."""
    
    print("\n" + "="*70)
    print("BUDDY'S AMBIGUITY DETECTION SYSTEM")
    print("Real-time Mission Outcome Analysis")
    print("="*70 + "\n")
    
    evaluator = AmbiguityEvaluator()
    
    scenarios = [
        {
            "name": "🎯 Scenario 1: Clear Success",
            "description": "High confidence, good opportunities, sufficient evidence",
            "goal_eval": {
                "goal_satisfied": True,
                "confidence": 0.85,
                "evidence": ["10 items collected", "All keywords found", "Navigation successful"]
            },
            "opp_summary": {
                "opportunities_created": 5,
                "avg_confidence": 0.80
            },
            "items": 10,
            "status": "completed"
        },
        {
            "name": "⚠️  Scenario 2: Low Confidence Warning",
            "description": "Mission completed but goal confidence is suspiciously low",
            "goal_eval": {
                "goal_satisfied": False,
                "confidence": 0.40,
                "evidence": ["Only 3 items found", "Missing key information"]
            },
            "opp_summary": {
                "opportunities_created": 2,
                "avg_confidence": 0.75
            },
            "items": 3,
            "status": "completed"
        },
        {
            "name": "🔍 Scenario 3: Weak Opportunities",
            "description": "Many opportunities found but all have low quality",
            "goal_eval": {
                "goal_satisfied": True,
                "confidence": 0.70,
                "evidence": ["8 items collected", "Broad search results"]
            },
            "opp_summary": {
                "opportunities_created": 7,
                "avg_confidence": 0.50
            },
            "items": 8,
            "status": "completed"
        },
        {
            "name": "📊 Scenario 4: Insufficient Evidence",
            "description": "Mission completed but very little data collected",
            "goal_eval": {
                "goal_satisfied": True,
                "confidence": 0.65,
                "evidence": ["Only 1 item found"]
            },
            "opp_summary": {
                "opportunities_created": 1,
                "avg_confidence": 0.70
            },
            "items": 1,
            "status": "completed"
        },
        {
            "name": "❌ Scenario 5: Failed But Found Opportunities",
            "description": "Mission failed but discovered valuable opportunities",
            "goal_eval": {
                "goal_satisfied": False,
                "confidence": 0.30,
                "evidence": ["Navigation blocked", "Found some data"]
            },
            "opp_summary": {
                "opportunities_created": 4,
                "avg_confidence": 0.70
            },
            "items": 4,
            "status": "failed"
        }
    ]
    
    for scenario in scenarios:
        print(scenario["name"])
        print("-" * 70)
        print(f"Description: {scenario['description']}")
        print()
        
        # Run evaluation
        evaluation = evaluator.evaluate(
            mission_id="demo-mission",
            goal_evaluation=scenario["goal_eval"],
            opportunity_summary=scenario["opp_summary"],
            items_collected=scenario["items"],
            mission_status=scenario["status"]
        )
        
        # Show results
        if evaluation.ambiguous:
            print("🚨 AMBIGUITY DETECTED")
            print()
            print(f"   Reason: {evaluation.reason}")
            print(f"   Recommended Next Mission: {evaluation.recommended_next_mission}")
            print()
            print("   Metrics:")
            print(f"   • Confidence Gap: {evaluation.confidence_gap:.2f}")
            print(f"   • Opportunity Weakness: {evaluation.opportunity_weakness:.2f}")
            print(f"   • Evidence Sufficiency: {evaluation.evidence_sufficiency:.2f}")
            print()
            
            if evaluator.should_emit_signal(evaluation):
                print("   ✉️  Signal will be emitted to learning_signals.jsonl")
                signal = evaluation.to_signal("demo-mission")
                print()
                print("   Signal Preview:")
                print(f"   {json.dumps(signal, indent=6)}")
        else:
            print("✅ CLEAR OUTCOME - No ambiguity detected")
            print()
            print(f"   Reason: {evaluation.reason}")
            print()
            print("   Metrics:")
            print(f"   • Confidence Gap: {evaluation.confidence_gap:.2f}")
            print(f"   • Opportunity Weakness: {evaluation.opportunity_weakness:.2f}")
            print(f"   • Evidence Sufficiency: {evaluation.evidence_sufficiency:.2f}")
        
        print()
        print("="*70)
        print()
    
    # Show configuration
    print("⚙️  CONFIGURATION")
    print("-" * 70)
    print(f"Goal Confidence Threshold: {evaluator.goal_confidence_threshold}")
    print(f"Opportunity Confidence Threshold: {evaluator.opportunity_confidence_threshold}")
    print(f"Evidence Minimum Items: {evaluator.evidence_minimum_items}")
    print()
    print("="*70)
    print()
    
    # Show workflow
    print("🔄 INTEGRATION WORKFLOW")
    print("-" * 70)
    print()
    print("1. Mission Completes")
    print("   ↓")
    print("2. Goal Satisfaction Evaluated (Phase 3 Step 1)")
    print("   ↓")
    print("3. Opportunities Normalized (Phase 3 Step 2)")
    print("   ↓")
    print("4. Ambiguity Detected (Phase 3 Step 2.8) ← YOU ARE HERE")
    print("   ↓")
    print("5. Signal Emitted (if ambiguous)")
    print("   ↓")
    print("6. Whiteboard Updated")
    print("   ↓")
    print("7. Human Review (if needed)")
    print()
    print("="*70)
    print()


if __name__ == "__main__":
    demonstrate_ambiguity_detection()
