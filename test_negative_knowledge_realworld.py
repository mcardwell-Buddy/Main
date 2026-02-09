"""
Real-World Test: Process actual learning_signals.jsonl

This test processes the actual learning signals from the workspace
to demonstrate the Negative Knowledge Registry with real data.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from backend.learning.negative_knowledge_registry import (
    NegativeKnowledgeRegistry,
    get_negative_knowledge_for_whiteboard
)


def main():
    print("\n" + "="*70)
    print("REAL-WORLD TEST: Processing Actual Learning Signals")
    print("="*70)
    
    # Process real signals
    registry = NegativeKnowledgeRegistry(outputs_dir="outputs/phase25")
    
    print("\n📊 Processing learning_signals.jsonl...")
    stats = registry.process_learning_signals()
    
    print("\n" + "="*70)
    print("PROCESSING RESULTS")
    print("="*70)
    print(f"   Signals processed: {stats['processed']}")
    print(f"   Mission failures detected: {stats['mission_failures']}")
    print(f"   Selector failures detected: {stats['selector_failures']}")
    print(f"   Ambiguity patterns detected: {stats['ambiguity_patterns']}")
    print(f"   Cost patterns detected: {stats['cost_patterns']}")
    print(f"   Total patterns created: {stats['patterns_detected']}")
    
    # Get all patterns
    all_patterns = registry.get_all_patterns()
    
    print("\n" + "="*70)
    print(f"NEGATIVE KNOWLEDGE REGISTRY ({len(all_patterns)} patterns)")
    print("="*70)
    
    # Group by type
    by_type = {}
    for pattern in all_patterns:
        if pattern.pattern_type not in by_type:
            by_type[pattern.pattern_type] = []
        by_type[pattern.pattern_type].append(pattern)
    
    # Display by type
    for pattern_type, patterns in sorted(by_type.items()):
        print(f"\n📌 {pattern_type.upper()} Patterns ({len(patterns)}):")
        for i, pattern in enumerate(patterns[:5], 1):  # Show first 5
            print(f"   {i}. {pattern.reason}")
            print(f"      Confidence: {pattern.confidence:.2f}")
            print(f"      Occurrences: {pattern.occurrence_count}")
            print(f"      First seen: {pattern.first_observed[:19]}")
            print(f"      Last seen: {pattern.last_observed[:19]}")
        if len(patterns) > 5:
            print(f"   ... and {len(patterns) - 5} more")
    
    # High confidence patterns
    high_confidence = registry.get_high_confidence_patterns(min_confidence=0.7)
    
    print("\n" + "="*70)
    print(f"HIGH CONFIDENCE PATTERNS (≥0.7) - {len(high_confidence)} patterns")
    print("="*70)
    
    for pattern in high_confidence[:10]:
        print(f"\n⚠️  {pattern.reason}")
        print(f"   Type: {pattern.pattern_type}")
        print(f"   Confidence: {pattern.confidence:.2f}")
        print(f"   Occurrences: {pattern.occurrence_count}")
        print(f"   Evidence: {len(pattern.evidence)} signals")
    
    # Summary statistics
    summary = registry.get_summary_by_type()
    
    print("\n" + "="*70)
    print("SUMMARY STATISTICS BY TYPE")
    print("="*70)
    
    for pattern_type, stats in sorted(summary.items()):
        print(f"\n{pattern_type.upper()}:")
        print(f"   Unique patterns: {stats['pattern_count']}")
        print(f"   Total occurrences: {stats['total_occurrences']}")
        print(f"   Average confidence: {stats['avg_confidence']:.2f}")
        print(f"   High confidence count: {stats['high_confidence_count']}")
    
    # Whiteboard data
    print("\n" + "="*70)
    print("WHITEBOARD PREVIEW")
    print("="*70)
    
    whiteboard_data = get_negative_knowledge_for_whiteboard()
    
    print(f"\n📋 What Buddy Avoids:")
    print(f"   Total patterns tracked: {whiteboard_data['total_patterns']}")
    
    if whiteboard_data.get("high_confidence_patterns"):
        print(f"\n   High confidence patterns by type:")
        for ptype, patterns in whiteboard_data["high_confidence_patterns"].items():
            print(f"      {ptype}: {len(patterns)} patterns")
            for p in patterns[:3]:
                print(f"         • {p['reason']} (confidence: {p['confidence']:.2f})")
    
    print("\n" + "="*70)
    print("✅ REAL-WORLD TEST COMPLETE")
    print("="*70)
    print("\nFiles created:")
    print("   outputs/phase25/negative_knowledge.jsonl")
    print("\nThis registry will grow as Buddy encounters more failures.")
    print("It provides read-only insights without blocking execution.")
    print("="*70)


if __name__ == "__main__":
    main()
