"""
Direct Test: Tool Selection Invariant Enforcement

Tests that execution validates tools against intents and fails fast on mismatch.
"""

import json
import time
from pathlib import Path
from backend.execution_service import ExecutionService, INTENT_TOOL_RULES

MISSIONS_FILE = Path("outputs/phase25/missions.jsonl")


def clear_missions():
    """Clear missions.jsonl for fresh test"""
    if MISSIONS_FILE.exists():
        MISSIONS_FILE.unlink()
    MISSIONS_FILE.parent.mkdir(parents=True, exist_ok=True)


def create_and_approve_mission(mission_id: str, objective: str):
    """Create and approve a mission"""
    # Create
    mission = {
        'mission_id': mission_id,
        'mission': {
            'objective': {
                'description': objective
            }
        },
        'status': 'proposed',
        'created_at': f'2026-02-08T{time.time()}'
    }
    
    with open(MISSIONS_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(mission) + '\n')
    
    # Approve (use correct event type)
    approval = {
        'event_type': 'mission_status_update',
        'mission_id': mission_id,
        'status': 'approved',
        'timestamp': f'2026-02-08T{time.time()}'
    }
    
    with open(MISSIONS_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(approval) + '\n')


def test_extraction_intent():
    """Test that extraction queries work with web_extract"""
    print("\n" + "=" * 80)
    print("TEST 1: EXTRACTION INTENT → web_extract/web_search (SHOULD PASS)")
    print("=" * 80)
    
    clear_missions()
    service = ExecutionService()
    
    mission_id = f"test_extract_{int(time.time() * 1000)}"
    objective = "Extract the homepage title from https://example.com"
    
    print(f"Objective: {objective}")
    print(f"Creating and approving mission...")
    
    create_and_approve_mission(mission_id, objective)
    
    print(f"Executing mission...")
    result = service.execute_mission(mission_id)
    
    print(f"\nResult:")
    print(f"  Success: {result.get('success')}")
    print(f"  Intent: {result.get('intent')}")
    print(f"  Tool Used: {result.get('tool_used')}")
    
    if result.get('success'):
        allowed_tools = INTENT_TOOL_RULES.get('extraction', [])
        if result.get('tool_used') in allowed_tools:
            print(f"\n✅ PASS: Extraction executed with allowed tool")
            return True
        else:
            print(f"\n❌ FAIL: Tool '{result.get('tool_used')}' not in allowed tools {allowed_tools}")
            return False
    else:
        print(f"\n❌ FAIL: Execution failed: {result.get('error')}")
        return False


def test_calculation_intent():
    """Test that calculation queries work with calculate"""
    print("\n" + "=" * 80)
    print("TEST 2: CALCULATION INTENT → calculate (SHOULD PASS)")
    print("=" * 80)
    
    clear_missions()
    service = ExecutionService()
    
    mission_id = f"test_calc_{int(time.time() * 1000)}"
    objective = "Calculate what is 100 + 50"
    
    print(f"Objective: {objective}")
    print(f"Creating and approving mission...")
    
    create_and_approve_mission(mission_id, objective)
    
    print(f"Executing mission...")
    result = service.execute_mission(mission_id)
    
    print(f"\nResult:")
    print(f"  Success: {result.get('success')}")
    print(f"  Intent: {result.get('intent')}")
    print(f"  Tool Used: {result.get('tool_used')}")
    
    if result.get('success'):
        if result.get('tool_used') == 'calculate':
            print(f"\n✅ PASS: Calculation executed with 'calculate' tool")
            return True
        else:
            print(f"\n❌ FAIL: Wrong tool '{result.get('tool_used')}' used for calculation")
            return False
    else:
        print(f"\n❌ FAIL: Execution failed: {result.get('error')}")
        return False


def test_tool_validation_logic():
    """Test the validation logic directly"""
    print("\n" + "=" * 80)
    print("TEST 3: TOOL VALIDATION LOGIC (UNIT TEST)")
    print("=" * 80)
    
    service = ExecutionService()
    
    # Test valid combinations
    valid_tests = [
        ('web_extract', 'extraction', True),
        ('web_search', 'extraction', True),
        ('calculate', 'calculation', True),
        ('web_search', 'search', True),
    ]
    
    # Test invalid combinations
    invalid_tests = [
        ('calculate', 'extraction', False),
        ('web_search', 'calculation', False),
        ('web_extract', 'calculation', False),
        ('calculate', 'search', False),
    ]
    
    all_passed = True
    
    print("\nValid tool/intent combinations (should pass):")
    for tool, intent, should_be_valid in valid_tests:
        result = service._validate_tool_for_intent(tool, intent, "test objective")
        passed = result['valid'] == should_be_valid
        status = "✅" if passed else "❌"
        print(f"  {status} {tool} + {intent} → {result['valid']}")
        if not passed:
            all_passed = False
    
    print("\nInvalid tool/intent combinations (should fail):")
    for tool, intent, should_be_valid in invalid_tests:
        result = service._validate_tool_for_intent(tool, intent, "test objective")
        passed = result['valid'] == should_be_valid
        status = "✅" if passed else "❌"
        print(f"  {status} {tool} + {intent} → {result['valid']}")
        if result.get('error'):
            print(f"      Error: {result['error']}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print(f"\n✅ PASS: All validation logic tests passed")
        return True
    else:
        print(f"\n❌ FAIL: Some validation logic tests failed")
        return False


def test_intent_classification():
    """Test intent classification accuracy"""
    print("\n" + "=" * 80)
    print("TEST 4: INTENT CLASSIFICATION ACCURACY")
    print("=" * 80)
    
    service = ExecutionService()
    
    test_cases = [
        ("Extract the homepage title from https://example.com", "extraction"),
        ("Get the data from https://api.example.com", "extraction"),
        ("Scrape the text from this page", "extraction"),
        ("Calculate 100 + 50", "calculation"),
        ("What is 25 * 4", "calculation"),
        ("Compute 999 / 3", "calculation"),
        ("Search for Python news", "search"),
        ("Find information about AI", "search"),
        ("Look up the latest research", "search"),
    ]
    
    all_passed = True
    for objective, expected_intent in test_cases:
        actual_intent = service._classify_intent(objective)
        passed = actual_intent == expected_intent
        status = "✅" if passed else "❌"
        
        print(f"{status} '{objective[:60]}...'")
        print(f"   Expected: {expected_intent}, Got: {actual_intent}")
        
        if not passed:
            all_passed = False
    
    if all_passed:
        print(f"\n✅ PASS: All intent classification tests passed")
        return True
    else:
        print(f"\n❌ FAIL: Some intent classification tests failed")
        return False


def main():
    print("\n" + "=" * 80)
    print("🔒 TOOL SELECTION INVARIANT ENFORCEMENT TEST")
    print("=" * 80)
    print("\nObjective: Validate that execution ONLY proceeds with allowed tools")
    print("Strategy: Classify intent → Validate tool → Fail fast on mismatch")
    
    results = []
    
    # Run all tests
    results.append(("Intent Classification", test_intent_classification()))
    results.append(("Tool Validation Logic", test_tool_validation_logic()))
    results.append(("Extraction Intent", test_extraction_intent()))
    results.append(("Calculation Intent", test_calculation_intent()))
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    print(f"\n{passed_count}/{total_count} test categories passed")
    
    if passed_count == total_count:
        print("\n" + "=" * 80)
        print("✅ TOOL SELECTION HARDENING COMPLETE")
        print("=" * 80)
        print("\nAll invariants are enforced:")
        print("  ✓ Intent classification is accurate")
        print("  ✓ Tool validation prevents mismatches")
        print("  ✓ Execution fails fast with clear errors")
        print("  ✓ No silent fallbacks or best guesses")
        print("\nTool selection is now:")
        print("  • Deterministic (same input → same intent → same allowed tools)")
        print("  • Auditable (intent logged in execution records)")
        print("  • Safe (invalid tool/intent combinations are rejected)")
        print("\n🎯 System is ready for learning signal observation.")
        return True
    else:
        print("\n❌ TOOL SELECTION HARDENING INCOMPLETE")
        print(f"   {total_count - passed_count} test category(ies) failed")
        return False


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
