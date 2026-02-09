#!/usr/bin/env python3
"""
Test domain capsule isolation.
Verifies that tool performance is tracked separately by domain.
"""

import sys
sys.path.insert(0, '.')

from backend.agent import Agent, AgentState
from backend.tool_performance import tracker
from backend.memory import memory

def test_domain_inference():
    """Test that domains are correctly inferred from goals"""
    print("\n=== Testing Domain Inference ===\n")
    
    test_cases = [
        ("Design a marketing campaign for Q1", "marketing"),
        ("Analyze our competitor's blockchain strategy", "crypto"),
        ("Debug the API endpoint", "engineering"),
        ("Schedule the team meeting", "operations"),
        ("General question about life", "_global"),
    ]
    
    for goal, expected_domain in test_cases:
        state = AgentState(goal)
        result = "✓" if state.domain == expected_domain else "✗"
        print(f"{result} Goal: '{goal}'")
        print(f"  → Domain: {state.domain} (expected: {expected_domain})")
        print()

def test_domain_scoped_performance():
    """Test that performance metrics are tracked separately by domain"""
    print("\n=== Testing Domain-Scoped Performance ===\n")
    
    # Try to clear previous data (works with MockMemory)
    try:
        if hasattr(memory, 'data'):
            memory.data.clear()
    except:
        pass
    
    # Record web_search performance in marketing domain
    print("Recording web_search usage in 'marketing' domain:")
    tracker.record_usage('web_search', success=True, latency_ms=1200, domain='marketing')
    tracker.record_usage('web_search', success=True, latency_ms=1100, domain='marketing')
    print("  ✓ 2 successful calls recorded")
    
    # Record web_search performance in crypto domain
    print("\nRecording web_search usage in 'crypto' domain:")
    tracker.record_usage('web_search', success=False, latency_ms=1500, domain='crypto', failure_mode='timeout')
    tracker.record_usage('web_search', success=True, latency_ms=1400, domain='crypto')
    print("  ✓ 1 failure, 1 success recorded")
    
    # Verify marketing performance
    print("\n--- Marketing Domain Stats ---")
    marketing_stats = tracker.get_stats('web_search', domain='marketing')
    if marketing_stats:
        print(f"Total calls: {marketing_stats['total_calls']}")
        print(f"Success rate: {marketing_stats['successful_calls']}/{marketing_stats['total_calls']}")
        print(f"Avg latency: {marketing_stats['avg_latency_ms']:.1f}ms")
        print(f"Failure modes: {marketing_stats['failure_modes']}")
    
    # Verify crypto performance
    print("\n--- Crypto Domain Stats ---")
    crypto_stats = tracker.get_stats('web_search', domain='crypto')
    if crypto_stats:
        print(f"Total calls: {crypto_stats['total_calls']}")
        print(f"Success rate: {crypto_stats['successful_calls']}/{crypto_stats['total_calls']}")
        print(f"Avg latency: {crypto_stats['avg_latency_ms']:.1f}ms")
        print(f"Failure modes: {crypto_stats['failure_modes']}")
    
    # Verify usefulness scores are different
    print("\n--- Usefulness Scores (80/20 weighted) ---")
    marketing_usefulness = tracker.get_usefulness_score('web_search', domain='marketing')
    crypto_usefulness = tracker.get_usefulness_score('web_search', domain='crypto')
    
    print(f"Marketing usefulness: {marketing_usefulness:.2f}")
    print(f"Crypto usefulness: {crypto_usefulness:.2f}")
    
    if marketing_usefulness > crypto_usefulness:
        print("✓ Marketing usefulness > Crypto usefulness (as expected)")
    else:
        print("✗ Marketing usefulness should be higher!")
    
    # Verify global aggregate exists
    print("\n--- Global Aggregate Stats ---")
    global_stats = tracker.get_stats('web_search', domain='_global')
    if global_stats:
        print(f"Total calls across all domains: {global_stats['total_calls']}")
        print(f"Overall success rate: {global_stats['successful_calls']}/{global_stats['total_calls']}")
        print("✓ Global fallback aggregate exists")

def test_domain_fallback():
    """Test that unknown domains fall back to global stats"""
    print("\n=== Testing Domain Fallback ===\n")
    
    # Request stats for domain with no history
    print("Requesting stats for 'unknown_domain' (no history):")
    unknown_stats = tracker.get_stats('web_search', domain='unknown_domain')
    
    if unknown_stats:
        print("✓ Fallback to global aggregate successful")
        print(f"  Stats: {unknown_stats['total_calls']} total calls")
    else:
        print("✗ Fallback failed - no stats returned")

def test_agent_passes_domain():
    """Test that Agent passes domain through the execution loop"""
    print("\n=== Testing Agent Domain Passing ===\n")
    
    goals = [
        "Design a marketing campaign",
        "Research crypto trends",
        "Debug the backend API",
    ]
    
    for goal in goals:
        agent = Agent(goal)
        print(f"Goal: {goal}")
        print(f"  → Inferred domain: {agent.state.domain}")
        print(f"  → Domain persists: {agent.state.domain == AgentState(goal).domain}")
        print()

if __name__ == '__main__':
    print("=" * 60)
    print("DOMAIN CAPSULES TEST SUITE")
    print("=" * 60)
    
    test_domain_inference()
    test_domain_scoped_performance()
    test_domain_fallback()
    test_agent_passes_domain()
    
    print("\n" + "=" * 60)
    print("✓ All domain capsule tests completed!")
    print("=" * 60)
