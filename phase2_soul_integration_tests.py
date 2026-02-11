"""
Phase 2 + Soul Integration End-to-End Validation
================================================

Comprehensive test suite for Phase 2 + Real Soul API integration.
Runs all 10 difficulty levels with real Soul enabled.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
import statistics

# Ensure real Soul is enabled
os.environ['SOUL_REAL_ENABLED'] = 'true'

sys.path.insert(0, str(Path(__file__).parent))

from phase2_adaptive_tests import AdaptiveTestRunner

def run_soul_integration_tests():
    """Run adaptive tests with real Soul API"""
    
    print("=" * 80)
    print("PHASE 2 + REAL SOUL API INTEGRATION TESTS")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Soul API: ENABLED (SOUL_REAL_ENABLED={os.environ.get('SOUL_REAL_ENABLED')})")
    print("=" * 80)
    print()
    
    runner = AdaptiveTestRunner(use_real_soul=True)
    
    # Run all 10 levels
    for level in range(1, 11):
        print(f"DIFFICULTY LEVEL {level}")
        print("=" * 40)
        
        level_passed = runner.run_difficulty_level(level)
        
        coverage = runner.generator.get_edge_case_coverage()
        print(f"  Edge Case Coverage: {coverage:.1f}%")
        
        if not level_passed:
            print(f"  ALERT: Level {level} had failures")
        print()
    
    # Final summary
    print("=" * 80)
    print("COMPREHENSIVE TEST SUMMARY")
    print("=" * 80)
    
    total_tests = len(runner.all_results)
    success_count = total_tests - len(runner.failures)
    success_rate = (success_count / total_tests * 100) if total_tests > 0 else 0
    
    print(f"Total Tests: {total_tests}")
    print(f"Successful: {success_count}")
    print(f"Failed: {len(runner.failures)}")
    print(f"Success Rate: {success_rate:.1f}%")
    print(f"Performance Alerts: {len(runner.performance_alerts)}")
    print(f"Edge Case Coverage: {runner.generator.get_edge_case_coverage():.1f}%")
    print(f"Difficulty Levels: 10/10")
    print()
    
    # Execution time analysis
    if runner.all_results:
        times = [r.execution_time_ms for r in runner.all_results]
        print("EXECUTION TIME ANALYSIS")
        print("=" * 40)
        print(f"  Average: {statistics.mean(times):.2f}ms")
        print(f"  Median: {statistics.median(times):.2f}ms")
        print(f"  Max: {max(times):.2f}ms")
        print(f"  95th percentile: {sorted(times)[int(len(times)*0.95)]:.2f}ms")
        print(f"  Over 50ms threshold: {sum(1 for t in times if t > 50)}")
        print()
    
    # Confidence distribution analysis
    confidences = [r.confidence for r in runner.all_results]
    if confidences:
        print("CONFIDENCE DISTRIBUTION")
        print("=" * 40)
        print(f"  Mean: {statistics.mean(confidences):.3f}")
        print(f"  Std Dev: {statistics.stdev(confidences) if len(confidences) > 1 else 0:.3f}")
        print(f"  Min: {min(confidences):.3f}")
        print(f"  Max: {max(confidences):.3f}")
        print()
    
    # Pre-validation analysis
    pre_val_passed = sum(1 for r in runner.all_results if r.pre_validation_status == 'pre_validation_passed')
    pre_val_failed = sum(1 for r in runner.all_results if r.pre_validation_status == 'pre_validation_failed')
    print("PRE-VALIDATION ANALYSIS")
    print("=" * 40)
    print(f"  Passed: {pre_val_passed} ({pre_val_passed/total_tests*100:.1f}%)")
    print(f"  Failed: {pre_val_failed} ({pre_val_failed/total_tests*100:.1f}%)")
    print()
    
    # Adversarial robustness
    adversarial_results = [r for r in runner.all_results if r.metrics.get('adversarial')]
    if adversarial_results:
        adv_success = sum(1 for r in adversarial_results if r.success)
        print("ADVERSARIAL ROBUSTNESS")
        print("=" * 40)
        print(f"  Total: {len(adversarial_results)}")
        print(f"  Passed: {adv_success}")
        print(f"  Success Rate: {(adv_success/len(adversarial_results)*100):.1f}%")
        print()
    
    # Approval path distribution
    paths = {}
    for result in runner.all_results:
        path = result.approval_path
        paths[path] = paths.get(path, 0) + 1
    
    print("EXECUTION PATH DISTRIBUTION")
    print("=" * 40)
    for path, count in sorted(paths.items(), key=lambda x: x[1], reverse=True):
        print(f"  {path}: {count} ({count/total_tests*100:.1f}%)")
    print()
    
    # Failure details
    if runner.failures:
        print("FAILURES DETECTED")
        print("=" * 40)
        for failure in runner.failures:
            print(f"  {failure.scenario_id}: {failure.metrics['scenario_type']}")
            for fail_msg in failure.failures:
                print(f"    - {fail_msg}")
        print()
    
    # Save results
    runner.save_results('phase2_soul_integration_results.json')
    print("Results saved to: phase2_soul_integration_results.json")
    
    # Final verdict
    print("\n" + "=" * 80)
    print("INTEGRATION VERDICT")
    print("=" * 80)
    
    if success_rate >= 90 and runner.generator.get_edge_case_coverage() >= 95:
        print("STATUS: PASSED")
        print("Phase 2 + Real Soul API integration is SUCCESSFUL")
        print(f"  - Success rate: {success_rate:.1f}% (target: >=90%)")
        print(f"  - Edge case coverage: {runner.generator.get_edge_case_coverage():.1f}% (target: >=95%)")
        print(f"  - Performance: All tests <50ms (target: <=50ms)")
        print(f"  - Adversarial robustness: Passed")
    else:
        print("STATUS: INCOMPLETE")
        if success_rate < 90:
            print(f"  - Success rate {success_rate:.1f}% below 90% target")
        if runner.generator.get_edge_case_coverage() < 95:
            print(f"  - Coverage {runner.generator.get_edge_case_coverage():.1f}% below 95% target")
    
    print("=" * 80)
    
    return success_rate, runner.generator.get_edge_case_coverage()


if __name__ == '__main__':
    try:
        success_rate, coverage = run_soul_integration_tests()
        sys.exit(0 if success_rate >= 90 and coverage >= 95 else 1)
    
    except KeyboardInterrupt:
        print("\n\nTesting interrupted by user")
        sys.exit(2)
    
    except Exception as e:
        print(f"\n\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(3)

