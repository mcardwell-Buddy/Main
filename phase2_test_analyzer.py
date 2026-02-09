"""
Phase 2 Adaptive Test Results Analyzer
======================================

Analyzes results from adaptive testing and provides insights.
"""

import json
from pathlib import Path
from typing import Dict, List


def analyze_results():
    """Analyze adaptive test results"""
    
    if not Path('phase2_adaptive_test_results.json').exists():
        print("❌ Results file not found. Run phase2_adaptive_tests.py first.")
        return
    
    with open('phase2_adaptive_test_results.json') as f:
        data = json.load(f)
    
    print("=" * 80)
    print("🔍 PHASE 2 ADAPTIVE TEST ANALYSIS")
    print("=" * 80)
    print()
    
    # Overall metrics
    run = data['test_run']
    summary = data['summary']
    
    print("📊 OVERALL METRICS:")
    print(f"   Total Tests: {run['total_tests']}")
    print(f"   Success Rate: {summary['success_rate']:.1f}%")
    print(f"   Failures: {run['total_failures']}")
    print(f"   Performance Alerts: {run['performance_alerts']}")
    print(f"   Edge Case Coverage: {run['edge_case_coverage']:.1f}%")
    print(f"   Avg Execution Time: {summary['avg_execution_time_ms']:.2f}ms")
    print(f"   Max Execution Time: {summary['max_execution_time_ms']:.2f}ms")
    print()
    
    # Analyze by difficulty level
    print("📈 DIFFICULTY LEVEL BREAKDOWN:")
    results_by_level = {}
    for result in data['results']:
        level = result['metrics']['difficulty_level']
        if level not in results_by_level:
            results_by_level[level] = {'total': 0, 'success': 0, 'failed': 0}
        results_by_level[level]['total'] += 1
        if result['success']:
            results_by_level[level]['success'] += 1
        else:
            results_by_level[level]['failed'] += 1
    
    for level in sorted(results_by_level.keys()):
        stats = results_by_level[level]
        success_rate = (stats['success'] / stats['total'] * 100) if stats['total'] > 0 else 0
        status = "✅" if success_rate >= 90 else "⚠️" if success_rate >= 70 else "❌"
        print(f"   Level {level}: {status} {success_rate:.0f}% ({stats['success']}/{stats['total']})")
    print()
    
    # Analyze by scenario type
    print("🎯 SCENARIO TYPE ANALYSIS:")
    scenario_stats = {}
    for result in data['results']:
        stype = result['metrics']['scenario_type']
        if stype not in scenario_stats:
            scenario_stats[stype] = {'total': 0, 'success': 0}
        scenario_stats[stype]['total'] += 1
        if result['success']:
            scenario_stats[stype]['success'] += 1
    
    # Top failures
    failures = [(k, v) for k, v in scenario_stats.items() if v['success'] < v['total']]
    failures.sort(key=lambda x: x[1]['success'] / x[1]['total'])
    
    print("   Top Failure Types:")
    for stype, stats in failures[:5]:
        rate = (stats['success'] / stats['total'] * 100) if stats['total'] > 0 else 0
        print(f"      {stype}: {rate:.0f}% success ({stats['success']}/{stats['total']})")
    print()
    
    # Confidence distribution analysis
    print("📊 CONFIDENCE DISTRIBUTION:")
    confidences = [r['confidence'] for r in data['results']]
    if confidences:
        import statistics
        print(f"   Mean: {statistics.mean(confidences):.3f}")
        print(f"   Std Dev: {statistics.stdev(confidences) if len(confidences) > 1 else 0:.3f}")
        print(f"   Min: {min(confidences):.3f}")
        print(f"   Max: {max(confidences):.3f}")
    print()
    
    # Pre-validation analysis
    print("🔍 PRE-VALIDATION ANALYSIS:")
    pre_val_passed = sum(1 for r in data['results'] if r['pre_validation_status'] == 'pre_validation_passed')
    pre_val_failed = sum(1 for r in data['results'] if r['pre_validation_status'] == 'pre_validation_failed')
    print(f"   Passed: {pre_val_passed} ({pre_val_passed/run['total_tests']*100:.1f}%)")
    print(f"   Failed: {pre_val_failed} ({pre_val_failed/run['total_tests']*100:.1f}%)")
    print()
    
    # Execution path analysis
    print("🛤️  EXECUTION PATH ANALYSIS:")
    paths = {}
    for result in data['results']:
        path = result['approval_path']
        paths[path] = paths.get(path, 0) + 1
    
    for path, count in sorted(paths.items(), key=lambda x: x[1], reverse=True):
        print(f"   {path}: {count} ({count/run['total_tests']*100:.1f}%)")
    print()
    
    # Adversarial test results
    adversarial_count = sum(1 for r in data['results'] if r['metrics'].get('adversarial'))
    adversarial_success = sum(1 for r in data['results'] if r['metrics'].get('adversarial') and r['success'])
    
    print("⚔️  ADVERSARIAL TEST RESULTS:")
    print(f"   Total: {adversarial_count}")
    print(f"   Success: {adversarial_success}")
    print(f"   Success Rate: {(adversarial_success/adversarial_count*100) if adversarial_count > 0 else 0:.1f}%")
    print()
    
    # Performance analysis
    print("⚡ PERFORMANCE ANALYSIS:")
    execution_times = [r['execution_time_ms'] for r in data['results']]
    if execution_times:
        import statistics
        print(f"   Average: {statistics.mean(execution_times):.2f}ms")
        print(f"   Median: {statistics.median(execution_times):.2f}ms")
        print(f"   95th percentile: {sorted(execution_times)[int(len(execution_times)*0.95)] if execution_times else 0:.2f}ms")
        print(f"   Max: {max(execution_times):.2f}ms")
        print(f"   Over Threshold (>50ms): {sum(1 for t in execution_times if t > 50)}")
    print()
    
    # Key findings
    print("=" * 80)
    print("🔑 KEY FINDINGS:")
    print("=" * 80)
    
    findings = []
    
    # Finding 1: Edge case coverage
    if run['edge_case_coverage'] >= 95:
        findings.append("✅ Excellent edge case coverage (100%)")
    else:
        findings.append(f"⚠️  Edge case coverage at {run['edge_case_coverage']:.1f}%")
    
    # Finding 2: Success rate
    if summary['success_rate'] >= 90:
        findings.append(f"✅ High success rate ({summary['success_rate']:.1f}%)")
    elif summary['success_rate'] >= 70:
        findings.append(f"⚠️  Moderate success rate ({summary['success_rate']:.1f}%)")
    else:
        findings.append(f"❌ Low success rate ({summary['success_rate']:.1f}%)")
    
    # Finding 3: Performance
    if summary['max_execution_time_ms'] <= 50:
        findings.append(f"✅ All tests under 50ms threshold")
    else:
        findings.append(f"⚠️  Some tests exceeded 50ms ({run['performance_alerts']} alerts)")
    
    # Finding 4: Adversarial robustness
    if adversarial_count > 0:
        adv_rate = (adversarial_success/adversarial_count*100)
        if adv_rate >= 80:
            findings.append(f"✅ Strong adversarial robustness ({adv_rate:.0f}%)")
        else:
            findings.append(f"⚠️  Adversarial robustness needs improvement ({adv_rate:.0f}%)")
    
    # Finding 5: Confidence distribution
    if confidences and len(confidences) > 1:
        std_dev = statistics.stdev(confidences)
        if std_dev > 0.2:
            findings.append(f"✅ Continuous confidence distribution (σ={std_dev:.3f})")
        else:
            findings.append(f"⚠️  Bimodal confidence distribution (σ={std_dev:.3f})")
    
    for finding in findings:
        print(f"   {finding}")
    
    print()
    print("=" * 80)
    
    # Overall recommendation
    if run['edge_case_coverage'] >= 95 and summary['success_rate'] >= 80:
        print("✅ RECOMMENDATION: Phase 2 systems are robust and ready for production")
    elif run['edge_case_coverage'] >= 95:
        print("⚠️  RECOMMENDATION: Address failing test scenarios before production")
    else:
        print("⚠️  RECOMMENDATION: Continue testing to reach 95% edge case coverage")
    
    print("=" * 80)


if __name__ == '__main__':
    analyze_results()
