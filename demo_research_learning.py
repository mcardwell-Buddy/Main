"""
Research Learning System Demo

Demonstrates how the research engine learns and improves through feedback.
Shows:
1. Research execution
2. Outcome evaluation
3. Learning signal generation
4. Adaptive improvement
"""

import json
from pathlib import Path
from Back_End.research_intelligence_engine import research_intelligence_engine
from Back_End.research_feedback_loop import research_feedback_loop


def demo_research_with_learning():
    """Demonstrate research execution with learning feedback loop."""
    
    print("\n" + "="*80)
    print("BUDDY RESEARCH LEARNING SYSTEM DEMO")
    print("="*80)
    
    # Test queries for different research types
    test_queries = [
        "Find all contact information for Cardwell Associates",
        "Research pricing information for enterprise software",
        "Tell me about competitors in the SaaS space",
    ]
    
    all_feedback_results = []
    
    for query in test_queries:
        print(f"\n{'='*80}")
        print(f"RESEARCH QUERY: {query}")
        print(f"{'='*80}")
        
        try:
            # Step 1: Execute research
            print("\n[1] Executing research...")
            research_output = research_intelligence_engine.research(query)
            
            session_id = research_output.get("session_id", "unknown")
            task_type = research_output.get("task_type", "unknown")
            completeness = research_output.get("completeness_score", 0.0)
            
            print(f"   Session ID: {session_id}")
            print(f"   Task Type: {task_type}")
            print(f"   Completeness: {completeness:.1%}")
            
            findings = research_output.get("findings", {})
            print(f"   Data Types Found: {list(findings.keys())}")
            print(f"   Total Entities: {sum(len(v) for v in findings.values())}")
            
            # Step 2: Process through feedback loop
            print("\n[2] Processing through feedback loop...")
            feedback_result = research_feedback_loop.process_research_session(research_output)
            
            print(f"   Outcome: {feedback_result['feedback']['outcome']}")
            print(f"   Confidence: {feedback_result['feedback']['confidence']:.2f}")
            print(f"   Signals Generated: {feedback_result['signals_generated']}")
            print(f"   Recommendation: {feedback_result['feedback']['recommendation']}")
            
            all_feedback_results.append(feedback_result)
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    # Step 3: Show learning insights
    print(f"\n{'='*80}")
    print("LEARNING INSIGHTS")
    print(f"{'='*80}")
    
    # Engine rankings
    print("\n[Engine Effectiveness Rankings]")
    rankings = research_feedback_loop.get_engine_rankings()
    if rankings:
        for engine, score in sorted(rankings.items(), key=lambda x: x[1], reverse=True):
            print(f"   {engine:20s}: {score:.2f}")
    else:
        print("   No engine data yet")
    
    # Task type insights
    print("\n[Task Type Performance]")
    task_types = set()
    for m in research_feedback_loop.metrics_history:
        task_types.add(m.task_type)
    
    for task_type in sorted(task_types):
        insights = research_feedback_loop.get_task_type_insights(task_type)
        print(f"\n   {task_type}:")
        print(f"     Sessions: {insights.get('sessions', 0)}")
        print(f"     Success Rate: {insights.get('success_rate', 0):.1%}")
        print(f"     Avg Completeness: {insights.get('avg_completeness', 0):.2f}")
        print(f"     Avg Confidence: {insights.get('avg_confidence', 0):.2f}")
        best_engines = insights.get('best_engines', {})
        if best_engines:
            print(f"     Best Engines: {', '.join(sorted(best_engines.keys()))}")
    
    # Step 4: Show learning signals
    print(f"\n{'='*80}")
    print("LEARNING SIGNALS (Sample)")
    print(f"{'='*80}")
    
    signal_types = {}
    for signal in research_feedback_loop.learning_signals:
        signal_type = signal.signal_type
        if signal_type not in signal_types:
            signal_types[signal_type] = []
        signal_types[signal_type].append(signal)
    
    for signal_type, signals in signal_types.items():
        print(f"\n[{signal_type}] - {len(signals)} signals")
        if signals:
            sample = signals[0]
            print(f"   Sample Recommendation: {sample.recommendation[:60]}...")
            print(f"   Confidence: {sample.confidence:.2f}")
    
    # Step 5: Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"Research Sessions: {len(research_feedback_loop.metrics_history)}")
    print(f"Feedback Events: {len(research_feedback_loop.feedback_events)}")
    print(f"Learning Signals Generated: {len(research_feedback_loop.learning_signals)}")
    print(f"Learning Signals File: {Path('outputs/research/learning_signals.jsonl').exists()}")
    
    print(f"\n{'='*80}")
    print("✅ RESEARCH LEARNING SYSTEM READY")
    print(f"{'='*80}")
    print("""
Now Buddy can:
1. ✅ Execute intelligent multi-step research across 10 SerpAPI engines
2. ✅ Evaluate research outcomes with detailed metrics
3. ✅ Generate learning signals for continuous improvement
4. ✅ Track engine effectiveness per task type
5. ✅ Adjust strategies based on past performance
6. ✅ Emit signals to the broader learning system

The Research Intelligence Engine is now fully connected to Buddy's
learning infrastructure, enabling adaptive improvement over time.
""")


if __name__ == "__main__":
    demo_research_with_learning()

