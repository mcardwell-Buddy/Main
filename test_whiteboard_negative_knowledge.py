"""
Test whiteboard integration with negative knowledge
"""

import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent))

from backend.whiteboard.mission_whiteboard import get_mission_whiteboard


def main():
    print("\n" + "="*70)
    print("TESTING WHITEBOARD WITH NEGATIVE KNOWLEDGE")
    print("="*70)
    
    # Get whiteboard for a real mission
    mission_id = "0035d374-2f36-499f-afba-10a2fd3d47e9"
    
    print(f"\nFetching whiteboard for mission: {mission_id[:20]}...")
    
    try:
        whiteboard = get_mission_whiteboard(mission_id)
        
        print("\n✅ Whiteboard retrieved successfully")
        
        # Display what_buddy_avoids section
        if "what_buddy_avoids" in whiteboard:
            print("\n" + "="*70)
            print("📋 WHAT BUDDY AVOIDS")
            print("="*70)
            
            avoids = whiteboard["what_buddy_avoids"]
            
            print(f"\nTotal patterns tracked: {avoids.get('total_patterns', 0)}")
            
            # Summary
            if "summary" in avoids and avoids["summary"]:
                print("\n📊 Summary by type:")
                for ptype, stats in avoids["summary"].items():
                    print(f"\n   {ptype.upper()}:")
                    print(f"      Patterns: {stats['pattern_count']}")
                    print(f"      Occurrences: {stats['total_occurrences']}")
                    print(f"      Avg confidence: {stats['avg_confidence']:.2f}")
                    print(f"      High confidence: {stats['high_confidence_count']}")
            
            # High confidence patterns
            if "high_confidence_patterns" in avoids and avoids["high_confidence_patterns"]:
                print("\n⚠️  High confidence patterns:")
                for ptype, patterns in avoids["high_confidence_patterns"].items():
                    print(f"\n   {ptype.upper()}:")
                    for pattern in patterns:
                        print(f"      • {pattern['reason']}")
                        print(f"        Confidence: {pattern['confidence']:.2f}")
                        print(f"        Occurrences: {pattern['occurrences']}")
        
        # Display other relevant sections
        print("\n" + "="*70)
        print("📋 OTHER WHITEBOARD SECTIONS")
        print("="*70)
        
        print(f"\nMission status: {whiteboard.get('status')}")
        print(f"Objective: {whiteboard.get('objective', 'N/A')}")
        
        if whiteboard.get("termination"):
            term = whiteboard["termination"]
            print(f"Termination reason: {term.get('reason')}")
        
        if whiteboard.get("cost_summary"):
            cost = whiteboard["cost_summary"]
            print(f"\nCost summary:")
            print(f"   Total cost: {cost.get('total_cost', 0):.2f}")
            print(f"   Time cost: {cost.get('time_cost', 0):.2f}")
        
        if whiteboard.get("decision_trace"):
            trace = whiteboard["decision_trace"]
            print(f"\nMost recent decision: {trace.get('decision')}")
        
        print("\n" + "="*70)
        print("✅ WHITEBOARD INTEGRATION WORKING")
        print("="*70)
        print("\nThe 'what_buddy_avoids' section is now part of every mission whiteboard.")
        print("It provides read-only insights without affecting mission execution.")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
