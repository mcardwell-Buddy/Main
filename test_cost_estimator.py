"""
Test script for CostEstimator

Validates:
- SerpAPI tier-based pricing
- OpenAI token-based pricing
- Firestore operation pricing
- Tier recommendations
- Tool-specific cost estimation
"""

import json
from backend.cost_estimator import CostEstimator, ServiceTier, ModelType

def test_serpapi_free_tier():
    """Test SerpAPI free tier cost calculation."""
    print("\n=== Test 1: SerpAPI Free Tier ===")
    estimator = CostEstimator(ServiceTier.FREE)
    
    # 5 searches on free tier
    cost = estimator.estimate_mission_cost(serpapi_searches=5)
    print(f"5 searches on FREE tier: ${cost.total_usd:.4f}")
    print(json.dumps(cost.to_dict(), indent=2))
    
    assert cost.total_usd == 0.0, "Free tier should be $0"
    print("[PASS] Free tier test passed\n")

def test_serpapi_starter_tier():
    """Test SerpAPI starter tier cost calculation."""
    print("\n=== Test 2: SerpAPI Starter Tier ===")
    estimator = CostEstimator(ServiceTier.STARTER)
    
    # 100 searches on starter tier ($25 for 1000 = $0.025 per search)
    cost = estimator.estimate_mission_cost(serpapi_searches=100)
    expected_cost = 100 * (25.00 / 1000)
    print(f"100 searches on STARTER tier: ${cost.total_usd:.4f}")
    print(f"Expected: ${expected_cost:.4f}")
    print(json.dumps(cost.to_dict(), indent=2))
    
    assert abs(cost.total_usd - expected_cost) < 0.001, f"Expected ${expected_cost}, got ${cost.total_usd}"
    print("[PASS] Starter tier test passed\n")

def test_serpapi_tier_recommendation():
    """Test tier recommendation when exceeding limits."""
    print("\n=== Test 3: SerpAPI Tier Recommendation ===")
    estimator = CostEstimator(ServiceTier.FREE)
    
    # 300 searches exceeds free tier (250 limit)
    cost = estimator.estimate_mission_cost(serpapi_searches=300)
    print(f"300 searches on FREE tier (limit 250):")
    print(f"Warnings: {cost.warnings}")
    print(f"Recommendations: {cost.tier_recommendations}")
    
    assert len(cost.warnings) > 0, "Should warn about exceeding tier limit"
    assert 'serpapi' in cost.tier_recommendations, "Should recommend tier upgrade"
    assert cost.tier_recommendations['serpapi'] == 'starter', "Should recommend starter tier"
    print("[PASS] Tier recommendation test passed\n")

def test_openai_gpt4o_mini():
    """Test OpenAI gpt-4o-mini cost calculation."""
    print("\n=== Test 4: OpenAI gpt-4o-mini ===")
    estimator = CostEstimator()
    
    # 1M input tokens + 500k output tokens
    # Input: 1M * $0.15 = $0.15
    # Output: 500k * $0.60 = $0.30
    # Total: $0.45
    cost = estimator.estimate_mission_cost(openai_calls=[{
        'model': ModelType.GPT_4O_MINI,
        'input_tokens': 1_000_000,
        'output_tokens': 500_000
    }])
    
    expected_input = 1_000_000 / 1_000_000 * 0.15
    expected_output = 500_000 / 1_000_000 * 0.60
    expected_total = expected_input + expected_output
    
    print(f"1M input + 500k output tokens (gpt-4o-mini): ${cost.total_usd:.4f}")
    print(f"Expected: ${expected_total:.4f}")
    print(json.dumps(cost.to_dict(), indent=2))
    
    assert abs(cost.total_usd - expected_total) < 0.001, f"Expected ${expected_total}, got ${cost.total_usd}"
    print("[PASS] OpenAI gpt-4o-mini test passed\n")

def test_openai_gpt4o():
    """Test OpenAI gpt-4o cost calculation."""
    print("\n=== Test 5: OpenAI gpt-4o ===")
    estimator = CostEstimator()
    
    # 100k input + 50k output tokens
    # Input: 100k * $2.50/1M = $0.25
    # Output: 50k * $10.00/1M = $0.50
    # Total: $0.75
    cost = estimator.estimate_mission_cost(openai_calls=[{
        'model': ModelType.GPT_4O,
        'input_tokens': 100_000,
        'output_tokens': 50_000
    }])
    
    expected_input = 100_000 / 1_000_000 * 2.50
    expected_output = 50_000 / 1_000_000 * 10.00
    expected_total = expected_input + expected_output
    
    print(f"100k input + 50k output tokens (gpt-4o): ${cost.total_usd:.4f}")
    print(f"Expected: ${expected_total:.4f}")
    print(json.dumps(cost.to_dict(), indent=2))
    
    assert abs(cost.total_usd - expected_total) < 0.001, f"Expected ${expected_total}, got ${cost.total_usd}"
    print("[PASS] OpenAI gpt-4o test passed\n")

def test_firestore_operations():
    """Test Firestore operation costs."""
    print("\n=== Test 6: Firestore Operations ===")
    estimator = CostEstimator()
    
    # 100k reads + 50k writes
    # Reads: 100k * $0.06/100k = $0.06
    # Writes: 50k * $0.18/100k = $0.09
    # Total: $0.15
    cost = estimator.estimate_mission_cost(
        firestore_reads=100_000,
        firestore_writes=50_000
    )
    
    expected_reads = 100_000 / 100_000 * 0.06
    expected_writes = 50_000 / 100_000 * 0.18
    expected_total = expected_reads + expected_writes
    
    print(f"100k reads + 50k writes: ${cost.total_usd:.4f}")
    print(f"Expected: ${expected_total:.4f}")
    print(json.dumps(cost.to_dict(), indent=2))
    
    assert abs(cost.total_usd - expected_total) < 0.001, f"Expected ${expected_total}, got ${cost.total_usd}"
    print("[PASS] Firestore operations test passed\n")

def test_combined_mission():
    """Test combined mission with multiple services."""
    print("\n=== Test 7: Combined Mission ===")
    estimator = CostEstimator(ServiceTier.STARTER)
    
    # Realistic mission: 10 searches + LLM call + Firestore ops
    cost = estimator.estimate_mission_cost(
        serpapi_searches=10,
        openai_calls=[{
            'model': ModelType.GPT_4O_MINI,
            'input_tokens': 5_000,
            'output_tokens': 2_000
        }],
        firestore_reads=100,
        firestore_writes=50
    )
    
    print(f"Combined mission cost: ${cost.total_usd:.4f}")
    print(json.dumps(cost.to_dict(), indent=2))
    
    assert cost.total_usd > 0, "Combined mission should have cost"
    assert len(cost.service_costs) == 3, "Should have 3 service costs"
    print("[PASS] Combined mission test passed\n")

def test_tool_cost_estimation():
    """Test tool-specific cost estimation."""
    print("\n=== Test 8: Tool Cost Estimation ===")
    estimator = CostEstimator(ServiceTier.STARTER)
    
    # Web search tool
    web_search_cost = estimator.estimate_tool_cost('web_search', {'queries': 5})
    print(f"Web search (5 queries): ${web_search_cost.total_usd:.4f}")
    
    # LLM call tool
    llm_cost = estimator.estimate_tool_cost('llm_call', {
        'model': 'gpt-4o-mini',
        'input_tokens': 1000,
        'output_tokens': 500
    })
    print(f"LLM call (1k in + 500 out): ${llm_cost.total_usd:.4f}")
    
    assert web_search_cost.total_usd > 0, "Web search should have cost"
    assert llm_cost.total_usd > 0, "LLM call should have cost"
    print("[PASS] Tool cost estimation test passed\n")

def run_all_tests():
    """Run all test scenarios."""
    print("=" * 60)
    print("COST ESTIMATOR TEST SUITE")
    print("=" * 60)
    
    try:
        test_serpapi_free_tier()
        test_serpapi_starter_tier()
        test_serpapi_tier_recommendation()
        test_openai_gpt4o_mini()
        test_openai_gpt4o()
        test_firestore_operations()
        test_combined_mission()
        test_tool_cost_estimation()
        
        print("=" * 60)
        print("[PASS] ALL TESTS PASSED!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n[FAIL] TEST FAILED: {e}\n")
        raise
    except Exception as e:
        print(f"\n[ERROR] UNEXPECTED ERROR: {e}\n")
        raise

if __name__ == "__main__":
    run_all_tests()
