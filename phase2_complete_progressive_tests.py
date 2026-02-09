"""
Phase 2 Progressive Adaptive Testing - Full Suite (Levels 1-10)
================================================================

Runs all 10 difficulty levels regardless of coverage to ensure
comprehensive testing of all edge cases, adversarial inputs, and stress tests.
"""

import sys
from pathlib import Path

# Import the adaptive test system
sys.path.insert(0, str(Path(__file__).parent))

from phase2_adaptive_tests import AdaptiveTestRunner

def run_complete_test_suite():
    """Run complete test suite through all 10 levels"""
    
    print("=" * 80)
    print("PHASE 2 COMPLETE PROGRESSIVE TEST SUITE")
    print("=" * 80)
    print("Running ALL 10 difficulty levels for comprehensive validation")
    print("=" * 80)
    print()
    
    runner = AdaptiveTestRunner()
    
    # Run all 10 levels
    for level in range(1, 11):
        print(f"\n{'=' * 80}")
        print(f"DIFFICULTY LEVEL {level}")
        print(f"{'=' * 80}")
        
        level_passed = runner.run_difficulty_level(level)
        
        coverage = runner.generator.get_edge_case_coverage()
        print(f"\n  📊 Edge Case Coverage: {coverage:.1f}%")
        
        if not level_passed:
            print(f"  ⚠️  ALERT: Level {level} had failures!")
    
    # Final comprehensive summary
    print(f"\n{'=' * 80}")
    print("COMPREHENSIVE TEST SUITE SUMMARY")
    print(f"{'=' * 80}")
    
    total_tests = len(runner.all_results)
    success_count = total_tests - len(runner.failures)
    success_rate = (success_count / total_tests * 100) if total_tests > 0 else 0
    
    print(f"Total Tests: {total_tests}")
    print(f"Successful: {success_count}")
    print(f"Failed: {len(runner.failures)}")
    print(f"Success Rate: {success_rate:.1f}%")
    print(f"Performance Alerts: {len(runner.performance_alerts)}")
    print(f"Edge Case Coverage: {runner.generator.get_edge_case_coverage():.1f}%")
    print(f"Difficulty Levels Completed: 10/10")
    print()
    
    # Execution time analysis
    if runner.all_results:
        import statistics
        times = [r.execution_time_ms for r in runner.all_results]
        print("⚡ EXECUTION TIME ANALYSIS:")
        print(f"   Average: {statistics.mean(times):.2f}ms")
        print(f"   Median: {statistics.median(times):.2f}ms")
        print(f"   Max: {max(times):.2f}ms")
        print(f"   95th percentile: {sorted(times)[int(len(times)*0.95)]:.2f}ms")
        print()
    
    # Confidence distribution analysis
    confidences = [r.confidence for r in runner.all_results]
    if confidences:
        import statistics
        print("📊 CONFIDENCE DISTRIBUTION:")
        print(f"   Mean: {statistics.mean(confidences):.3f}")
        print(f"   Std Dev: {statistics.stdev(confidences) if len(confidences) > 1 else 0:.3f}")
        print(f"   Min: {min(confidences):.3f}")
        print(f"   Max: {max(confidences):.3f}")
        print()
    
    # Adversarial test analysis
    adversarial_results = [r for r in runner.all_results if r.metrics.get('adversarial')]
    if adversarial_results:
        adv_success = sum(1 for r in adversarial_results if r.success)
        print(f"⚔️  ADVERSARIAL ROBUSTNESS:")
        print(f"   Total: {len(adversarial_results)}")
        print(f"   Passed: {adv_success}")
        print(f"   Success Rate: {(adv_success/len(adversarial_results)*100):.1f}%")
        print()
    
    # Failure analysis
    if runner.failures:
        print(f"❌ FAILURE DETAILS:")
        for failure in runner.failures:
            print(f"   {failure.scenario_id}: {failure.metrics['scenario_type']}")
            for fail_msg in failure.failures:
                print(f"      - {fail_msg}")
        print()
    
    # Performance alerts
    if runner.performance_alerts:
        print(f"⚠️  PERFORMANCE ALERTS:")
        for alert in runner.performance_alerts:
            print(f"   {alert.scenario_id}: {alert.execution_time_ms:.2f}ms (threshold: {runner.max_execution_time_ms}ms)")
        print()
    
    # Save results
    runner.save_results('phase2_complete_test_results.json')
    
    print(f"{'=' * 80}")
    
    # Final verdict
    if success_rate >= 85 and runner.generator.get_edge_case_coverage() >= 95:
        print("✅ COMPREHENSIVE TEST SUITE PASSED")
        print("   Phase 2 systems are production-ready")
    elif success_rate >= 85:
        print("⚠️  SUCCESS RATE ACHIEVED BUT COVERAGE INCOMPLETE")
    elif runner.generator.get_edge_case_coverage() >= 95:
        print("⚠️  COVERAGE ACHIEVED BUT SUCCESS RATE BELOW TARGET (85%)")
    else:
        print("❌ TEST SUITE INCOMPLETE")
    
    print(f"{'=' * 80}")
    
    return success_rate, runner.generator.get_edge_case_coverage()


if __name__ == '__main__':
    try:
        success_rate, coverage = run_complete_test_suite()
        
        # Exit with appropriate code
        if success_rate >= 85 and coverage >= 95:
            sys.exit(0)
        else:
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Testing interrupted by user")
        sys.exit(2)
    
    except Exception as e:
        print(f"\n\n❌ Testing failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(3)
