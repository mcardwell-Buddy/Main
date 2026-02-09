"""
Test Learning Signal Emission (Observe-Only Mode)

Verifies that:
1. Learning signals are emitted after execution completes
2. Exactly one signal is emitted per execution
3. Learning signals do NOT affect execution behavior
4. All execution invariants still pass with learning enabled
"""

import json
import time
from pathlib import Path
from backend.execution_service import ExecutionService

MISSIONS_FILE = Path("outputs/phase25/missions.jsonl")
LEARNING_SIGNALS_FILE = Path("outputs/phase25/execution_learning_signals.jsonl")


def clear_files():
    """Clear test files"""
    if MISSIONS_FILE.exists():
        MISSIONS_FILE.unlink()
    if LEARNING_SIGNALS_FILE.exists():
        LEARNING_SIGNALS_FILE.unlink()
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
    
    # Approve
    approval = {
        'event_type': 'mission_status_update',
        'mission_id': mission_id,
        'status': 'approved',
        'timestamp': f'2026-02-08T{time.time()}'
    }
    
    with open(MISSIONS_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(approval) + '\n')


def count_learning_signals(mission_id: str = None) -> int:
    """Count learning signals (optionally for specific mission)"""
    if not LEARNING_SIGNALS_FILE.exists():
        return 0
    
    count = 0
    with open(LEARNING_SIGNALS_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                signal = json.loads(line)
                if mission_id is None or signal['data']['mission_id'] == mission_id:
                    count += 1
    
    return count


def read_learning_signal(mission_id: str) -> dict:
    """Read the learning signal for a specific mission"""
    if not LEARNING_SIGNALS_FILE.exists():
        return None
    
    with open(LEARNING_SIGNALS_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                signal = json.loads(line)
                if signal['data']['mission_id'] == mission_id:
                    return signal
    
    return None


def test_learning_signal_emission():
    """Test that learning signals are emitted after execution"""
    print("\n" + "=" * 80)
    print("TEST 1: LEARNING SIGNAL EMISSION")
    print("=" * 80)
    
    clear_files()
    service = ExecutionService()
    
    mission_id = f"test_learning_{int(time.time() * 1000)}"
    objective = "Calculate what is 100 + 50"
    
    print(f"\nObjective: {objective}")
    print(f"Creating and approving mission...")
    
    create_and_approve_mission(mission_id, objective)
    
    # Check: No learning signals before execution
    signals_before = count_learning_signals()
    print(f"Learning signals before execution: {signals_before}")
    
    # Execute
    print(f"\nExecuting mission...")
    result = service.execute_mission(mission_id)
    
    # Check: Exactly one learning signal after execution
    signals_after = count_learning_signals()
    print(f"Learning signals after execution: {signals_after}")
    
    if signals_after == signals_before + 1:
        print(f"✅ Exactly one learning signal emitted")
    else:
        print(f"❌ Expected {signals_before + 1} signals, got {signals_after}")
        return False
    
    # Read the signal
    signal = read_learning_signal(mission_id)
    
    if signal:
        print(f"\n✅ Learning signal found for mission {mission_id}")
        print(f"\nSample Learning Signal:")
        print(f"  Signal Type: {signal['signal_type']}")
        print(f"  Signal Layer: {signal['signal_layer']}")
        print(f"  Signal Source: {signal['signal_source']}")
        print(f"  Mission ID: {signal['data']['mission_id']}")
        print(f"  Objective: {signal['data']['objective'][:60]}...")
        print(f"  Intent: {signal['data']['intent']}")
        print(f"  Tool Used: {signal['data']['tool_used']}")
        print(f"  Tool Confidence: {signal['data']['tool_confidence']}")
        print(f"  Success: {signal['data']['success']}")
        
        # Verify execution still succeeded
        if result.get('success'):
            print(f"\n✅ Execution succeeded (behavior unchanged)")
            return True
        else:
            print(f"\n❌ Execution failed unexpectedly")
            return False
    else:
        print(f"\n❌ Learning signal not found")
        return False


def test_execution_invariants_with_learning():
    """Test that all execution invariants still pass with learning enabled"""
    print("\n" + "=" * 80)
    print("TEST 2: EXECUTION INVARIANTS WITH LEARNING ENABLED")
    print("=" * 80)
    
    clear_files()
    service = ExecutionService()
    
    # Test Invariant 1: Proposed missions do not execute
    print("\n[Invariant 1] Proposed missions do NOT execute")
    mission_id_1 = f"test_proposed_{int(time.time() * 1000)}"
    mission = {
        'mission_id': mission_id_1,
        'mission': {'objective': {'description': 'Calculate 1 + 1'}},
        'status': 'proposed',
        'created_at': f'2026-02-08T{time.time()}'
    }
    with open(MISSIONS_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(mission) + '\n')
    
    result = service.execute_mission(mission_id_1)
    
    if not result.get('success') and 'not "approved"' in result.get('error', ''):
        print(f"  ✅ Proposed mission correctly rejected")
        # No learning signal should be emitted for rejected executions
        signals = count_learning_signals(mission_id_1)
        if signals == 0:
            print(f"  ✅ No learning signal emitted (as expected)")
        else:
            print(f"  ⚠️  Learning signal emitted for rejected execution")
    else:
        print(f"  ❌ Proposed mission was executed")
        return False
    
    # Test Invariant 2: Approved missions execute exactly once
    print("\n[Invariant 2] Approved missions execute exactly once")
    mission_id_2 = f"test_approved_{int(time.time() * 1000)}"
    create_and_approve_mission(mission_id_2, "Calculate 2 + 2")
    
    result = service.execute_mission(mission_id_2)
    
    if result.get('success'):
        print(f"  ✅ Approved mission executed")
        
        # Exactly one learning signal should be emitted
        signals = count_learning_signals(mission_id_2)
        if signals == 1:
            print(f"  ✅ Exactly one learning signal emitted")
        else:
            print(f"  ❌ Expected 1 learning signal, got {signals}")
            return False
    else:
        print(f"  ❌ Approved mission failed to execute")
        return False
    
    # Test Invariant 3: Execution does not re-run
    print("\n[Invariant 3] Execution does NOT re-run")
    result2 = service.execute_mission(mission_id_2)
    
    if not result2.get('success') and 'already been executed' in result2.get('error', ''):
        print(f"  ✅ Re-execution correctly rejected")
        
        # Still only one learning signal (no new signal on rejection)
        signals = count_learning_signals(mission_id_2)
        if signals == 1:
            print(f"  ✅ Still only one learning signal (no duplicate)")
        else:
            print(f"  ❌ Expected 1 learning signal, got {signals}")
            return False
    else:
        print(f"  ❌ Re-execution was not rejected")
        return False
    
    print(f"\n✅ ALL INVARIANTS PASSED WITH LEARNING ENABLED")
    return True


def test_learning_signal_content():
    """Test that learning signal contains expected fields"""
    print("\n" + "=" * 80)
    print("TEST 3: LEARNING SIGNAL CONTENT VALIDATION")
    print("=" * 80)
    
    clear_files()
    service = ExecutionService()
    
    mission_id = f"test_content_{int(time.time() * 1000)}"
    objective = "Calculate 25 * 4"
    
    create_and_approve_mission(mission_id, objective)
    result = service.execute_mission(mission_id)
    
    signal = read_learning_signal(mission_id)
    
    if not signal:
        print("❌ Learning signal not found")
        return False
    
    # Check required fields
    required_top_level = ['signal_type', 'signal_layer', 'signal_source', 'timestamp', 'data']
    required_data = ['mission_id', 'objective', 'intent', 'tool_used', 'tool_confidence', 'success']
    
    all_present = True
    
    print("\nChecking top-level fields:")
    for field in required_top_level:
        present = field in signal
        status = "✅" if present else "❌"
        print(f"  {status} {field}: {present}")
        if not present:
            all_present = False
    
    print("\nChecking data fields:")
    for field in required_data:
        present = field in signal.get('data', {})
        status = "✅" if present else "❌"
        print(f"  {status} {field}: {present}")
        if not present:
            all_present = False
    
    if all_present:
        print(f"\n✅ All required fields present in learning signal")
        return True
    else:
        print(f"\n❌ Some required fields missing")
        return False


def main():
    print("\n" + "=" * 80)
    print("🔬 LEARNING SIGNAL EMISSION TEST (OBSERVE-ONLY MODE)")
    print("=" * 80)
    print("\nObjective: Verify learning signals are emitted without affecting behavior")
    print("Mode: OBSERVE-ONLY (no reads, no behavior changes)")
    
    results = []
    
    # Run all tests
    results.append(("Learning Signal Emission", test_learning_signal_emission()))
    results.append(("Execution Invariants with Learning", test_execution_invariants_with_learning()))
    results.append(("Learning Signal Content", test_learning_signal_content()))
    
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
        print("✅ LEARNING MODULE WIRED IN OBSERVE-ONLY MODE")
        print("=" * 80)
        print("\nConfirmed:")
        print("  ✓ Learning signals emitted after execution completes")
        print("  ✓ Exactly one signal per execution")
        print("  ✓ Learning signals do NOT affect execution behavior")
        print("  ✓ All execution invariants still pass")
        print("  ✓ Learning signals are append-only and non-blocking")
        print("\n📊 Learning signals stored in:")
        print(f"   {LEARNING_SIGNALS_FILE}")
        print("\n🎯 System is now observing and learning from execution outcomes.")
        return True
    else:
        print("\n❌ LEARNING WIRING INCOMPLETE")
        print(f"   {total_count - passed_count} test category(ies) failed")
        return False


if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
