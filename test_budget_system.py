#!/usr/bin/env python3
"""
Comprehensive tests for budget and cost tracking system.

Tests:
1. Credit budget with daily rollover
2. Budget enforcement blocks execution when over limit
3. Actual cost tracking and reconciliation
4. SerpAPI credits vs OpenAI dollars distinction
5. Budget status reporting
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from datetime import datetime, timezone
from pathlib import Path
from Back_End.budget_tracker import BudgetTracker, CreditBudget, DollarBudget, get_budget_tracker
from Back_End.budget_enforcer import BudgetEnforcer, get_budget_enforcer
from Back_End.cost_tracker import CostTracker, get_cost_tracker
from Back_End.cost_estimator import ServiceTier, MissionCost, ServiceCost, ModelType
from Back_End.task_breakdown_and_proposal import TaskBreakdown


def setup_test_environment():
    """Setup clean test environment"""
    test_data_dir = Path('data/test')
    test_data_dir.mkdir(parents=True, exist_ok=True)
    
    # Use test-specific files
    budget_file = test_data_dir / 'budgets_test.jsonl'
    cost_file = test_data_dir / 'cost_reconciliation_test.jsonl'
    
    # Clean old test data
    if budget_file.exists():
        budget_file.unlink()
    if cost_file.exists():
        cost_file.unlink()
    
    return str(budget_file), str(cost_file)


def test_1_credit_budget_rollover():
    """Test daily budget with rollover logic"""
    print("\n" + "="*80)
    print("TEST 1: Credit Budget with Daily Rollover")
    print("="*80)
    
    budget_file, _ = setup_test_environment()
    tracker = BudgetTracker(storage_path=budget_file)
    
    # Get STARTER tier budget (1000 searches/month)
    budget = tracker.get_serpapi_budget(ServiceTier.STARTER)
    
    print(f"\n📊 SerpAPI Budget Status:")
    print(f"  Tier: {budget.tier}")
    print(f"  Monthly Quota: {budget.monthly_quota} searches")
    print(f"  Credits Used: {budget.credits_used}")
    print(f"  Credits Remaining: {budget.credits_remaining}")
    print(f"  Daily Recommended: {budget.daily_recommended} searches/day")
    print(f"  Today's Budget (with rollover): {budget.calculate_todays_budget()} searches")
    print(f"  Days Remaining in Month: {budget.days_remaining_in_month}")
    
    pace = budget.pace_status()
    print(f"\n📈 Pacing:")
    print(f"  On Pace: {pace['on_pace']}")
    print(f"  Daily Rate: {pace['daily_rate']} searches/day")
    print(f"  Projected Monthly Usage: {pace['projected_usage']} searches")
    print(f"  Status: {pace['pace'].upper()}")
    
    # Simulate using 20 searches
    tracker.record_serpapi_usage(20, mission_id='test_mission_1')
    
    # Get updated budget
    updated_budget = tracker.get_serpapi_budget(ServiceTier.STARTER)
    print(f"\n✅ After using 20 searches:")
    print(f"  Credits Used: {updated_budget.credits_used}")
    print(f"  Credits Remaining: {updated_budget.credits_remaining}")
    
    assert updated_budget.credits_used == 20, "Credits not tracked correctly"
    assert updated_budget.credits_remaining == 980, "Credits remaining incorrect"
    
    print("\n✅ TEST 1 PASSED: Credit budget with rollover works correctly")
    return True


def test_2_budget_enforcement_blocks_execution():
    """Test that execution is blocked when over budget"""
    print("\n" + "="*80)
    print("TEST 2: Budget Enforcement Blocks Execution")
    print("="*80)
    
    budget_file, _ = setup_test_environment()
    tracker = BudgetTracker(storage_path=budget_file)
    enforcer = BudgetEnforcer()
    enforcer.budget_tracker = tracker
    
    # Use up all but 5 searches (FREE tier = 250)
    tracker.record_serpapi_usage(245, mission_id='test_setup')
    
    budget = tracker.get_serpapi_budget(ServiceTier.FREE)
    print(f"\n📊 Current Budget:")
    print(f"  Credits Remaining: {budget.credits_remaining}")
    
    # Try to execute mission needing 10 searches (should be blocked)
    mission_cost = MissionCost(
        total_usd=0.025,
        service_costs=[
            ServiceCost(
                service='serpapi',
                operation_count=10,
                unit_cost=0.0,
                total_cost=0.0,
                tier=ServiceTier.FREE.value
            )
        ]
    )
    
    task_breakdown = TaskBreakdown(
        goal='Test mission',
        steps=[],
        total_cost=mission_cost,
        total_buddy_time_seconds=10,
        total_human_time_minutes=0,
        pure_buddy_steps=1,
        pure_human_steps=0,
        hybrid_steps=0,
        has_blocking_steps=False,
        requires_human_approval=False
    )
    
    result = enforcer.check_mission_budget(mission_cost, task_breakdown, ServiceTier.FREE)
    
    print(f"\n🚫 Budget Check Result:")
    print(f"  Can Execute: {result['can_execute']}")
    if not result['can_execute']:
        print(f"  Reason: {result['reason']}")
        print(f"  Recommended Action: {result.get('recommended_action', 'N/A')}")
        print(f"  Action Detail: {result.get('action_detail', 'N/A')}")
    
    assert not result['can_execute'], "Should block execution when over budget"
    assert result['service'] == 'serpapi', "Should identify SerpAPI as limiting service"
    
    print("\n✅ TEST 2 PASSED: Budget enforcement blocks execution correctly")
    return True


def test_3_actual_cost_tracking():
    """Test actual vs estimated cost reconciliation"""
    print("\n" + "="*80)
    print("TEST 3: Actual Cost Tracking and Reconciliation")
    print("="*80)
    
    _, cost_file = setup_test_environment()
    tracker = CostTracker(storage_path=cost_file)
    
    # Simulate API response with usage data
    tool_response = {
        'results': ['result1', 'result2'],
        'usage': {
            'input_tokens': 1000,
            'output_tokens': 500
        }
    }
    
    # Extract usage
    actual_usage = tracker.extract_api_usage('web_search', tool_response)
    print(f"\n📊 Extracted Usage:")
    print(f"  SerpAPI Searches: {actual_usage.get('serpapi_searches', 0)}")
    print(f"  OpenAI Input Tokens: {actual_usage.get('openai_input_tokens', 0)}")
    print(f"  OpenAI Output Tokens: {actual_usage.get('openai_output_tokens', 0)}")
    
    # Calculate actual costs
    actual_costs = tracker.calculate_actual_cost(
        actual_usage,
        tier=ServiceTier.FREE,
        model=ModelType.GPT_4O_MINI
    )
    
    print(f"\n💵 Actual Costs:")
    print(f"  SerpAPI Credits Consumed: {actual_costs['serpapi_credits_consumed']}")
    print(f"  OpenAI Cost: ${actual_costs['openai_cost_usd']:.6f}")
    print(f"  Total Dollar Cost: ${actual_costs['total_dollar_cost']:.6f}")
    
    # Create estimated cost for comparison
    estimated_cost = MissionCost(
        total_usd=0.0008,
        service_costs=[
            ServiceCost(
                service='serpapi',
                operation_count=1,
                unit_cost=0.0,
                total_cost=0.0,
                tier=ServiceTier.FREE.value
            ),
            ServiceCost(
                service='openai',
                operation_count=1200,
                unit_cost=0.0008,
                total_cost=0.0008
            )
        ]
    )
    
    # Reconcile
    reconciliation = tracker.reconcile(
        'test_mission_123',
        estimated_cost,
        actual_usage,
        ServiceTier.FREE,
        ModelType.GPT_4O_MINI
    )
    
    print(f"\n📈 Reconciliation:")
    print(f"  Estimated Cost: ${reconciliation['total_estimated_usd']:.6f}")
    print(f"  Actual Cost: ${reconciliation['total_actual_usd']:.6f}")
    print(f"  Variance: ${reconciliation['total_variance_usd']:.6f}")
    print(f"  Estimation Accuracy: {reconciliation['estimation_accuracy']:.2%}")
    
    assert actual_costs['serpapi_credits_consumed'] == 1, "Should track 1 SerpAPI search"
    assert actual_costs['total_dollar_cost'] > 0, "Should calculate dollar costs"
    assert 'estimation_accuracy' in reconciliation, "Should include accuracy metric"
    
    print("\n✅ TEST 3 PASSED: Cost tracking and reconciliation works correctly")
    return True


def test_4_serpapi_credits_vs_openai_dollars():
    """Test that we track credits for SerpAPI, dollars for OpenAI"""
    print("\n" + "="*80)
    print("TEST 4: SerpAPI Credits vs OpenAI Dollars Distinction")
    print("="*80)
    
    budget_file, cost_file = setup_test_environment()
    budget_tracker = BudgetTracker(storage_path=budget_file)
    cost_tracker = CostTracker(storage_path=cost_file)
    
    # Get initial budgets
    serpapi_budget = budget_tracker.get_serpapi_budget(ServiceTier.STARTER)
    openai_budget = budget_tracker.get_openai_budget(monthly_limit=100.0)
    
    print(f"\n📊 Initial Budgets:")
    print(f"  SerpAPI: {serpapi_budget.credits_remaining} credits remaining")
    print(f"  OpenAI: ${openai_budget.dollars_remaining:.2f} remaining")
    
    # Simulate mission using both services
    budget_tracker.record_serpapi_usage(5, mission_id='test_mission_4')
    budget_tracker.record_openai_usage(0.0035, mission_id='test_mission_4', tokens={'input': 1000, 'output': 500})
    
    # Get updated budgets
    updated_serpapi = budget_tracker.get_serpapi_budget(ServiceTier.STARTER)
    updated_openai = budget_tracker.get_openai_budget(monthly_limit=100.0)
    
    print(f"\n📊 After Mission:")
    print(f"  SerpAPI: {updated_serpapi.credits_used} credits used, {updated_serpapi.credits_remaining} remaining")
    print(f"  OpenAI: ${updated_openai.dollars_spent:.4f} spent, ${updated_openai.dollars_remaining:.2f} remaining")
    
    print(f"\n✅ Verification:")
    print(f"  ✓ SerpAPI tracked as CREDITS (not dollars)")
    print(f"  ✓ OpenAI tracked as DOLLARS")
    print(f"  ✓ Both services independently managed")
    
    assert updated_serpapi.credits_used == 5, "Should track 5 SerpAPI credits"
    assert updated_openai.dollars_spent == 0.0035, "Should track $0.0035 OpenAI spending"
    
    print("\n✅ TEST 4 PASSED: Credits vs dollars tracked correctly")
    return True


def test_5_budget_status_summary():
    """Test budget status summary endpoint"""
    print("\n" + "="*80)
    print("TEST 5: Budget Status Summary")
    print("="*80)
    
    budget_file, _ = setup_test_environment()
    budget_tracker = BudgetTracker(storage_path=budget_file)
    enforcer = BudgetEnforcer()
    enforcer.budget_tracker = budget_tracker
    
    # Record some usage
    budget_tracker.record_serpapi_usage(50, mission_id='test')
    budget_tracker.record_openai_usage(5.50, mission_id='test')
    
    # Get summary
    summary = enforcer.get_budget_status_summary(ServiceTier.STARTER)
    
    print(f"\n📊 Budget Status Summary:")
    print(f"\n  SerpAPI ({summary['serpapi']['type'].upper()}):")
    print(f"    Tier: {summary['serpapi']['tier']}")
    print(f"    Monthly Quota: {summary['serpapi']['monthly_quota']}")
    print(f"    Credits Used: {summary['serpapi']['credits_used']}")
    print(f"    Credits Remaining: {summary['serpapi']['credits_remaining']}")
    print(f"    Today's Budget: {summary['serpapi']['todays_budget']}")
    print(f"    Pace: {summary['serpapi']['pace']['pace']}")
    
    print(f"\n  OpenAI ({summary['openai']['type'].upper()}):")
    print(f"    Monthly Limit: ${summary['openai']['monthly_limit']:.2f}")
    print(f"    Spent: ${summary['openai']['spent']:.2f}")
    print(f"    Remaining: ${summary['openai']['remaining']:.2f}")
    
    assert summary['serpapi']['type'] == 'credits', "SerpAPI should be credit-based"
    assert summary['openai']['type'] == 'dollars', "OpenAI should be dollar-based"
    assert summary['serpapi']['credits_used'] == 50, "Should show 50 credits used"
    assert summary['openai']['spent'] == 5.50, "Should show $5.50 spent"
    
    print("\n✅ TEST 5 PASSED: Budget status summary works correctly")
    return True


def run_all_tests():
    """Run all budget system tests"""
    print("\n" + "="*80)
    print("🧪 BUDGET SYSTEM COMPREHENSIVE TEST SUITE")
    print("="*80)
    
    tests = [
        ("Credit Budget with Rollover", test_1_credit_budget_rollover),
        ("Budget Enforcement Blocks Execution", test_2_budget_enforcement_blocks_execution),
        ("Actual Cost Tracking", test_3_actual_cost_tracking),
        ("SerpAPI Credits vs OpenAI Dollars", test_4_serpapi_credits_vs_openai_dollars),
        ("Budget Status Summary", test_5_budget_status_summary),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, "PASSED" if passed else "FAILED"))
        except Exception as e:
            print(f"\n❌ TEST FAILED: {test_name}")
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, "FAILED"))
    
    # Print summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    
    for test_name, status in results:
        icon = "✅" if status == "PASSED" else "❌"
        print(f"{icon} {test_name}: {status}")
    
    passed_count = sum(1 for _, status in results if status == "PASSED")
    total_count = len(results)
    
    print(f"\n📈 Results: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n🎉 ALL TESTS PASSED! Budget system is working correctly.")
        return True
    else:
        print(f"\n⚠️  {total_count - passed_count} test(s) failed. Review errors above.")
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)

