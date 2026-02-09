"""
Phase 2 + Soul Integration Validation Script
=============================================

Runs comprehensive validation with real Soul API enabled.
"""

import os
import sys
import json
import subprocess
from pathlib import Path

# Enable real Soul
os.environ['SOUL_REAL_ENABLED'] = 'true'

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from phase2_complete_progressive_tests import run_complete_test_suite

print("=" * 80)
print("PHASE 2 + REAL SOUL API INTEGRATION VALIDATION")
print("=" * 80)
print(f"\nSOUL_REAL_ENABLED = {os.environ.get('SOUL_REAL_ENABLED')}\n")

try:
    # Run complete test suite
    success_rate, coverage = run_complete_test_suite()
    
    # Load results
    with open('phase2_complete_test_results.json') as f:
        results = json.load(f)
    
    print("\n" + "=" * 80)
    print("INTEGRATION VALIDATION RESULTS")
    print("=" * 80)
    
    # Key metrics
    print(f"\nSUCCESS RATE: {success_rate:.1f}%")
    print(f"EDGE CASE COVERAGE: {coverage:.1f}%")
    print(f"TOTAL TESTS: {len(results['results'])}")
    print(f"FAILURES: {len(results['failures'])}")
    
    # Performance
    times = [r['execution_time_ms'] for r in results['results']]
    print(f"\nPERFORMANCE:")
    print(f"  Average: {sum(times)/len(times):.2f}ms")
    print(f"  Max: {max(times):.2f}ms")
    print(f"  All under 50ms: {'YES' if max(times) <= 50 else 'NO'}")
    
    # Soul integration metrics
    print(f"\nSOUL INTEGRATION STATUS:")
    print(f"  Real Soul API: ENABLED")
    print(f"  Tests Executed: {len(results['results'])}")
    
    # Confidence distribution
    confidences = [r['confidence'] for r in results['results']]
    import statistics
    print(f"\nCONFIDENCE DISTRIBUTION:")
    print(f"  Mean: {statistics.mean(confidences):.3f}")
    print(f"  StdDev: {statistics.stdev(confidences) if len(confidences) > 1 else 0:.3f}")
    print(f"  Range: {min(confidences):.3f} - {max(confidences):.3f}")
    
    # Pre-validation
    pre_val_failed = sum(1 for r in results['results'] if r['pre_validation_status'] == 'pre_validation_failed')
    print(f"\nPRE-VALIDATION:")
    print(f"  Catch Rate: {(pre_val_failed/len(results['results'])*100):.1f}%")
    
    # Adversarial robustness
    adversarial = [r for r in results['results'] if r['metrics'].get('adversarial')]
    adv_passed = sum(1 for r in adversarial if r['success'])
    print(f"\nADVERSARIAL ROBUSTNESS:")
    print(f"  Total Tests: {len(adversarial)}")
    print(f"  Passed: {adv_passed}")
    print(f"  Success Rate: {(adv_passed/len(adversarial)*100) if adversarial else 0:.1f}%")
    
    # Summary
    print("\n" + "=" * 80)
    if success_rate >= 85 and coverage >= 95:
        print("VALIDATION PASSED - Phase 2 + Soul API integration successful")
    else:
        print("VALIDATION INCOMPLETE - Some metrics below target")
        if success_rate < 85:
            print(f"  - Success rate {success_rate:.1f}% below 85% target")
        if coverage < 95:
            print(f"  - Coverage {coverage:.1f}% below 95% target")
    print("=" * 80)
    
    sys.exit(0 if success_rate >= 85 and coverage >= 95 else 1)

except Exception as e:
    print(f"\nERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
