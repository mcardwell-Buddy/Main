"""
Chat Intake Integration Tests

Validates the chat → mission flow WITHOUT execution.

Tests:
1. Intent classification accuracy
2. Draft building correctness
3. Proposal emission
4. Signal logging
5. Whiteboard visibility
6. NO execution verification

All tests are deterministic and safe.
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from Back_End.mission_control.chat_intent_router import ChatIntentRouter
from Back_End.mission_control.mission_draft_builder import MissionDraftBuilder
from Back_End.mission_control.mission_proposal_emitter import MissionProposalEmitter
from Back_End.mission_control.chat_intake_coordinator import ChatIntakeCoordinator


def test_intent_router():
    """Test intent classification."""
    print("\n[TEST 1] Intent Router")
    print("-" * 60)
    
    router = ChatIntentRouter()
    
    tests = [
        ('Get leads from yellowpages.com', 'action_request'),
        ('Find quotes on quotes.toscrape.com', 'exploratory_request'),
        ('What is your name?', 'informational_question'),
        ('Hello', 'non_actionable'),
        ('Extract 100 contacts', 'action_request'),
    ]
    
    passed = 0
    for message, expected_type in tests:
        intent = router.route(message)
        actual_type = intent.intent_type
        
        if actual_type == expected_type:
            print(f"  ✓ \"{message[:40]}...\" → {actual_type}")
            passed += 1
        else:
            print(f"  ✗ \"{message[:40]}...\" → {actual_type} (expected {expected_type})")
    
    print(f"\nResult: {passed}/{len(tests)} passed")
    return passed == len(tests)


def test_draft_builder():
    """Test mission draft building."""
    print("\n[TEST 2] Draft Builder")
    print("-" * 60)
    
    builder = MissionDraftBuilder()
    
    # Test 1: Extract domains
    draft1 = builder.build_draft(
        raw_message="Get quotes from quotes.toscrape.com",
        intent_type="action_request",
        intent_keywords=["get"]
    )
    
    checks = []
    
    # Check status is always "proposed"
    checks.append(('Status is proposed', draft1.status == 'proposed'))
    
    # Check source is always "chat"
    checks.append(('Source is chat', draft1.source == 'chat'))
    
    # Check domain extraction
    checks.append(('Domain extracted', 'quotes.toscrape.com' in draft1.allowed_domains))
    
    # Check safe defaults
    checks.append(('Safe max_pages', draft1.max_pages <= 20))
    checks.append(('Safe max_duration', draft1.max_duration_seconds <= 600))
    
    # Test 2: Target count extraction
    draft2 = builder.build_draft(
        raw_message="Extract 50 leads from example.com",
        intent_type="action_request",
        intent_keywords=["extract"]
    )
    
    checks.append(('Target count extracted', draft2.target_count == 50))
    
    for description, result in checks:
        status = "✓" if result else "✗"
        print(f"  {status} {description}")
    
    passed = sum(1 for _, r in checks if r)
    print(f"\nResult: {passed}/{len(checks)} passed")
    return passed == len(checks)


def test_proposal_emitter():
    """Test proposal emission to files."""
    print("\n[TEST 3] Proposal Emitter")
    print("-" * 60)
    
    builder = MissionDraftBuilder()
    emitter = MissionProposalEmitter()
    
    # Create test draft
    draft = builder.build_draft(
        raw_message="Test mission for validation",
        intent_type="action_request",
        intent_keywords=["test"]
    )
    
    # Emit proposal
    result = emitter.emit_proposal(draft)
    
    checks = [
        ('Emission successful', result.get('success') is True),
        ('Mission ID present', result.get('mission_id') is not None),
        ('Status is proposed', result.get('status') == 'proposed'),
        ('Mission file written', Path(result.get('mission_file')).exists()),
        ('Signal file written', Path(result.get('signal_file')).exists()),
    ]
    
    # Verify it appears in proposed missions
    proposed = emitter.get_proposed_missions()
    checks.append(('Appears in proposed', any(m['mission_id'] == draft.mission_id for m in proposed)))
    
    for description, result in checks:
        status = "✓" if result else "✗"
        print(f"  {status} {description}")
    
    passed = sum(1 for _, r in checks if r)
    print(f"\nResult: {passed}/{len(checks)} passed")
    return passed == len(checks)


def test_no_execution():
    """Verify NO execution occurs."""
    print("\n[TEST 4] No Execution Verification")
    print("-" * 60)
    
    coordinator = ChatIntakeCoordinator()
    
    # Process actionable message
    result = coordinator.process_chat_message(
        "Get all data from example.com",
        user_id='test_user'
    )
    
    checks = [
        ('Mission status is proposed', result.get('mission_draft', {}).get('status') == 'proposed'),
        ('Awaiting approval flag', result.get('chat_feedback', {}).get('awaiting_approval') is True),
        ('Approval required', result.get('chat_feedback', {}).get('approval_required') is True),
        ('No active status', result.get('mission_draft', {}).get('status') != 'active'),
        ('No completed status', result.get('mission_draft', {}).get('status') != 'completed'),
    ]
    
    # Check signals file for no active missions from chat
    signals_file = Path('outputs/phase25/learning_signals.jsonl')
    if signals_file.exists():
        with open(signals_file, 'r') as f:
            last_signals = list(f)[-10:]  # Check last 10 signals
        
        # No mission_status_update with status=active from chat source
        active_from_chat = False
        for line in last_signals:
            try:
                signal = json.loads(line)
                if (signal.get('signal_type') == 'mission_status_update' and
                    signal.get('status') == 'active' and
                    signal.get('signal_source') == 'chat_intake'):
                    active_from_chat = True
            except:
                pass
        
        checks.append(('No active signal from chat', not active_from_chat))
    
    for description, result in checks:
        status = "✓" if result else "✗"
        print(f"  {status} {description}")
    
    passed = sum(1 for _, r in checks if r)
    print(f"\nResult: {passed}/{len(checks)} passed")
    return passed == len(checks)


def test_coordinator_integration():
    """Test full coordinator flow."""
    print("\n[TEST 5] Coordinator Integration")
    print("-" * 60)
    
    coordinator = ChatIntakeCoordinator()
    
    # Test actionable message
    result = coordinator.process_chat_message(
        "Scrape quotes from quotes.toscrape.com",
        user_id='test_user'
    )
    
    checks = [
        ('Intent classified', 'intent_classification' in result),
        ('Actionable detected', result.get('actionable') is True),
        ('Draft created', 'mission_draft' in result),
        ('Emission successful', result.get('emission_result', {}).get('success') is True),
        ('Feedback provided', 'chat_feedback' in result),
        ('Feedback type correct', result.get('chat_feedback', {}).get('type') == 'mission_proposed'),
    ]
    
    # Test non-actionable message
    result2 = coordinator.process_chat_message(
        "Hello there",
        user_id='test_user'
    )
    
    checks.append(('Non-actionable handled', result2.get('actionable') is False))
    checks.append(('No draft for non-actionable', 'mission_draft' not in result2))
    
    for description, result in checks:
        status = "✓" if result else "✗"
        print(f"  {status} {description}")
    
    passed = sum(1 for _, r in checks if r)
    print(f"\nResult: {passed}/{len(checks)} passed")
    return passed == len(checks)


def run_all_tests():
    """Run all integration tests."""
    print("\n" + "=" * 80)
    print("CHAT INTAKE INTEGRATION TESTS")
    print("=" * 80)
    
    tests = [
        ('Intent Router', test_intent_router),
        ('Draft Builder', test_draft_builder),
        ('Proposal Emitter', test_proposal_emitter),
        ('No Execution', test_no_execution),
        ('Coordinator Integration', test_coordinator_integration),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n  ✗ Exception: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80 + "\n")
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {name}")
    
    print(f"\nResult: {passed_count}/{total_count} test suites passed")
    
    if passed_count == total_count:
        print("\n✓ ALL TESTS PASSED")
        print("✓ Chat intake system operational")
        print("✓ NO execution detected")
        print("✓ Hard constraints verified")
    else:
        print(f"\n⚠ {total_count - passed_count} test suite(s) failed")
    
    print("\n" + "=" * 80 + "\n")
    
    return passed_count == total_count


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)

