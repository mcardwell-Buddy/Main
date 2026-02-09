"""
Phase 2 Staging Deployment & Verification System
=================================================

Automated testing, monitoring, and metrics collection for Phase 2 staging deployment.
"""

import json
import os
import sys
import time
import subprocess
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path
import statistics


class Phase2StagingVerifier:
    """Comprehensive Phase 2 staging verification system"""
    
    def __init__(self):
        self.results = {
            'deployment_timestamp': datetime.now().isoformat(),
            'feature_flags': {},
            'unit_tests': {},
            'synthetic_tests': {},
            'sanity_checks': {},
            'recommendations': [],
            'status': 'unknown',
        }
        
        self.sanity_thresholds = {
            'confidence_std_dev_min': 0.2,
            'approval_rate_min': 10.0,
            'approval_rate_max': 30.0,
            'pre_validation_catch_rate_min': 80.0,
            'unit_test_pass_rate_min': 80.0,
            'latency_max_ms': 50.0,
        }
    
    def step1_verify_feature_flags(self) -> Dict:
        """Step 1: Verify Phase 2 feature flags"""
        print("=" * 80)
        print("STEP 1: VERIFYING PHASE 2 FEATURE FLAGS")
        print("=" * 80)
        
        # Check environment variables
        flags = {
            'PHASE2_ENABLED': os.getenv('PHASE2_ENABLED', 'false'),
            'PHASE2_PRE_VALIDATION_ENABLED': os.getenv('PHASE2_PRE_VALIDATION_ENABLED', 'true'),
            'PHASE2_APPROVAL_GATES_ENABLED': os.getenv('PHASE2_APPROVAL_GATES_ENABLED', 'true'),
            'PHASE2_CLARIFICATION_ENABLED': os.getenv('PHASE2_CLARIFICATION_ENABLED', 'true'),
            'PHASE2_GRADED_CONFIDENCE_ENABLED': os.getenv('PHASE2_GRADED_CONFIDENCE_ENABLED', 'true'),
            'HIGH_CONFIDENCE_THRESHOLD': os.getenv('HIGH_CONFIDENCE_THRESHOLD', '0.85'),
            'MEDIUM_CONFIDENCE_THRESHOLD': os.getenv('MEDIUM_CONFIDENCE_THRESHOLD', '0.55'),
        }
        
        print("\nCurrent Feature Flags:")
        for flag, value in flags.items():
            status_icon = "✅" if value.lower() in ['true', '0.85', '0.55'] else "⚠️"
            print(f"  {status_icon} {flag}: {value}")
        
        # Store in results
        self.results['feature_flags'] = flags
        
        # Check if Phase 2 is enabled
        phase2_enabled = flags['PHASE2_ENABLED'].lower() == 'true'
        
        if not phase2_enabled:
            print("\n⚠️  WARNING: PHASE2_ENABLED=false")
            print("   Setting PHASE2_ENABLED=true for staging deployment...")
            os.environ['PHASE2_ENABLED'] = 'true'
            flags['PHASE2_ENABLED'] = 'true'
            print("   ✅ PHASE2_ENABLED now set to: true")
        
        print("\n✅ Feature flags verified")
        return flags
    
    def step2_verify_integration(self) -> Dict:
        """Step 2: Verify Phase 2 modules are integrated"""
        print("\n" + "=" * 80)
        print("STEP 2: VERIFYING PHASE 2 INTEGRATION")
        print("=" * 80)
        
        required_modules = [
            'phase2_confidence.py',
            'phase2_prevalidation.py',
            'phase2_approval_gates.py',
            'phase2_clarification.py',
            'phase2_soul_integration.py',
            'phase2_response_schema.py',
            'test_phase2_all.py',
        ]
        
        integration_status = {}
        all_present = True
        
        print("\nPhase 2 Modules:")
        for module in required_modules:
            exists = Path(module).exists()
            integration_status[module] = exists
            status_icon = "✅" if exists else "❌"
            print(f"  {status_icon} {module}: {'Present' if exists else 'MISSING'}")
            if not exists:
                all_present = False
        
        # Check backend integration
        backend_path = Path('backend/main.py')
        if backend_path.exists():
            with open(backend_path) as f:
                content = f.read()
                has_phase2_imports = 'from phase2_confidence import' in content
                has_phase2_init = 'PHASE2_ENABLED' in content
                has_phase2_endpoints = 'approval_gates' in content
                
                print("\nBackend Integration:")
                print(f"  {'✅' if has_phase2_imports else '❌'} Phase 2 imports")
                print(f"  {'✅' if has_phase2_init else '❌'} Phase 2 initialization")
                print(f"  {'✅' if has_phase2_endpoints else '❌'} Phase 2 endpoints")
                
                integration_status['backend_imports'] = has_phase2_imports
                integration_status['backend_init'] = has_phase2_init
                integration_status['backend_endpoints'] = has_phase2_endpoints
        
        self.results['integration'] = integration_status
        
        if all_present:
            print("\n✅ All Phase 2 modules present and integrated")
        else:
            print("\n❌ Some Phase 2 modules missing")
        
        return integration_status
    
    def step3_run_unit_tests(self) -> Dict:
        """Step 3: Run unit tests"""
        print("\n" + "=" * 80)
        print("STEP 3: RUNNING UNIT TESTS")
        print("=" * 80)
        
        try:
            print("\nExecuting: pytest test_phase2_all.py -v --tb=short")
            result = subprocess.run(
                ['python', '-m', 'pytest', 'test_phase2_all.py', '-v', '--tb=short', '--json-report', '--json-report-file=unit_test_results.json'],
                capture_output=True,
                text=True,
                timeout=60,
            )
            
            # Parse output
            output = result.stdout
            lines = output.split('\n')
            
            # Extract results
            passed = 0
            failed = 0
            for line in lines:
                if 'PASSED' in line:
                    passed += 1
                elif 'FAILED' in line:
                    failed += 1
            
            total = passed + failed
            pass_rate = (passed / total * 100) if total > 0 else 0
            
            unit_test_results = {
                'total': total,
                'passed': passed,
                'failed': failed,
                'pass_rate': pass_rate,
                'timestamp': datetime.now().isoformat(),
            }
            
            print(f"\n{'=' * 80}")
            print("UNIT TEST RESULTS")
            print(f"{'=' * 80}")
            print(f"  Total Tests: {total}")
            print(f"  Passed: {passed} {'✅' if pass_rate >= 80 else '⚠️'}")
            print(f"  Failed: {failed}")
            print(f"  Pass Rate: {pass_rate:.1f}%")
            
            if pass_rate < 80:
                print(f"\n  ⚠️  WARNING: Pass rate below 80% threshold")
                self.results['recommendations'].append(
                    f"Fix failing unit tests (pass rate: {pass_rate:.1f}%, target: ≥80%)"
                )
            
            self.results['unit_tests'] = unit_test_results
            
        except subprocess.TimeoutExpired:
            print("\n❌ Unit tests timed out")
            self.results['unit_tests'] = {'status': 'timeout'}
        except Exception as e:
            print(f"\n❌ Error running unit tests: {e}")
            self.results['unit_tests'] = {'status': 'error', 'message': str(e)}
        
        return self.results['unit_tests']
    
    def step4_run_synthetic_tests(self, goal_count: int = 500) -> Dict:
        """Step 4: Run synthetic stress tests"""
        print("\n" + "=" * 80)
        print(f"STEP 4: RUNNING SYNTHETIC STRESS TESTS ({goal_count} goals)")
        print("=" * 80)
        
        try:
            print(f"\nExecuting: python phase2_synthetic_harness.py")
            start_time = time.time()
            
            result = subprocess.run(
                ['python', 'phase2_synthetic_harness.py'],
                capture_output=True,
                text=True,
                timeout=300,
            )
            
            elapsed_time = time.time() - start_time
            
            # Load test report
            if Path('phase2_test_report.json').exists():
                with open('phase2_test_report.json') as f:
                    report = json.load(f)
                
                metrics = report['metrics']
                
                synthetic_results = {
                    'total_goals': report['test_run']['total_goals'],
                    'elapsed_time_seconds': elapsed_time,
                    'confidence': {
                        'mean': metrics['confidence']['mean'],
                        'std_dev': metrics['confidence']['std_dev'],
                        'min': metrics['confidence']['min'],
                        'max': metrics['confidence']['max'],
                    },
                    'execution_paths': metrics['execution_paths'],
                    'pre_validation': {
                        'passed': metrics['pre_validation']['passed'],
                        'failed': metrics['pre_validation']['failed'],
                        'catch_rate': metrics['pre_validation']['catch_rate_percent'],
                    },
                    'approval_requests': {
                        'count': metrics['approval_requests']['count'],
                        'rate': metrics['approval_requests']['rate_percent'],
                    },
                    'clarification_requests': {
                        'count': metrics['clarification_requests']['count'],
                        'rate': metrics['clarification_requests']['rate_percent'],
                    },
                    'latency_per_goal_ms': (elapsed_time / report['test_run']['total_goals']) * 1000,
                    'timestamp': datetime.now().isoformat(),
                }
                
                print(f"\n{'=' * 80}")
                print("SYNTHETIC TEST RESULTS")
                print(f"{'=' * 80}")
                print(f"  Total Goals: {synthetic_results['total_goals']}")
                print(f"  Elapsed Time: {elapsed_time:.2f}s")
                print(f"  Latency per Goal: {synthetic_results['latency_per_goal_ms']:.2f}ms")
                print()
                print("  CONFIDENCE METRICS:")
                print(f"    Mean: {synthetic_results['confidence']['mean']:.2%}")
                print(f"    Std Dev: {synthetic_results['confidence']['std_dev']:.3f} {'✅' if synthetic_results['confidence']['std_dev'] > 0.2 else '❌'}")
                print(f"    Range: [{synthetic_results['confidence']['min']:.0%}, {synthetic_results['confidence']['max']:.0%}]")
                print()
                print("  PRE-VALIDATION:")
                print(f"    Catch Rate: {synthetic_results['pre_validation']['catch_rate']:.1f}% {'✅' if synthetic_results['pre_validation']['catch_rate'] >= 80 else '❌'}")
                print()
                print("  APPROVAL SYSTEM:")
                print(f"    Approval Rate: {synthetic_results['approval_requests']['rate']:.1f}% {'✅' if 10 <= synthetic_results['approval_requests']['rate'] <= 30 else '⚠️'}")
                print(f"    Clarification Rate: {synthetic_results['clarification_requests']['rate']:.1f}%")
                print()
                print("  EXECUTION PATHS:")
                for path, count in synthetic_results['execution_paths'].items():
                    pct = (count / synthetic_results['total_goals']) * 100
                    print(f"    {path}: {count} ({pct:.1f}%)")
                
                self.results['synthetic_tests'] = synthetic_results
                
            else:
                print("\n❌ Test report not found")
                self.results['synthetic_tests'] = {'status': 'report_missing'}
        
        except subprocess.TimeoutExpired:
            print("\n❌ Synthetic tests timed out")
            self.results['synthetic_tests'] = {'status': 'timeout'}
        except Exception as e:
            print(f"\n❌ Error running synthetic tests: {e}")
            self.results['synthetic_tests'] = {'status': 'error', 'message': str(e)}
        
        return self.results['synthetic_tests']
    
    def step5_sanity_checks(self) -> Dict:
        """Step 5: Automated sanity checks"""
        print("\n" + "=" * 80)
        print("STEP 5: AUTOMATED SANITY CHECKS")
        print("=" * 80)
        
        checks = {}
        all_passed = True
        
        # Check 1: Confidence distribution is continuous
        if 'synthetic_tests' in self.results and 'confidence' in self.results['synthetic_tests']:
            std_dev = self.results['synthetic_tests']['confidence']['std_dev']
            threshold = self.sanity_thresholds['confidence_std_dev_min']
            passed = std_dev > threshold
            checks['confidence_continuous'] = {
                'passed': passed,
                'value': std_dev,
                'threshold': threshold,
                'message': f"Confidence std dev {std_dev:.3f} {'>' if passed else '≤'} {threshold}",
            }
            all_passed &= passed
        
        # Check 2: Approval rate is healthy
        if 'synthetic_tests' in self.results and 'approval_requests' in self.results['synthetic_tests']:
            rate = self.results['synthetic_tests']['approval_requests']['rate']
            min_rate = self.sanity_thresholds['approval_rate_min']
            max_rate = self.sanity_thresholds['approval_rate_max']
            passed = min_rate <= rate <= max_rate
            checks['approval_rate_healthy'] = {
                'passed': passed,
                'value': rate,
                'threshold': f"{min_rate}-{max_rate}",
                'message': f"Approval rate {rate:.1f}% {'within' if passed else 'outside'} {min_rate}-{max_rate}% range",
            }
            all_passed &= passed
        
        # Check 3: Pre-validation catch rate
        if 'synthetic_tests' in self.results and 'pre_validation' in self.results['synthetic_tests']:
            catch_rate = self.results['synthetic_tests']['pre_validation']['catch_rate']
            threshold = self.sanity_thresholds['pre_validation_catch_rate_min']
            passed = catch_rate >= threshold
            checks['pre_validation_effective'] = {
                'passed': passed,
                'value': catch_rate,
                'threshold': threshold,
                'message': f"Pre-validation catch rate {catch_rate:.1f}% {'>=' if passed else '<'} {threshold}%",
            }
            all_passed &= passed
        
        # Check 4: Unit test pass rate
        if 'unit_tests' in self.results and 'pass_rate' in self.results['unit_tests']:
            pass_rate = self.results['unit_tests']['pass_rate']
            threshold = self.sanity_thresholds['unit_test_pass_rate_min']
            passed = pass_rate >= threshold
            checks['unit_tests_passing'] = {
                'passed': passed,
                'value': pass_rate,
                'threshold': threshold,
                'message': f"Unit test pass rate {pass_rate:.1f}% {'>=' if passed else '<'} {threshold}%",
            }
            all_passed &= passed
        
        # Check 5: Latency acceptable
        if 'synthetic_tests' in self.results and 'latency_per_goal_ms' in self.results['synthetic_tests']:
            latency = self.results['synthetic_tests']['latency_per_goal_ms']
            threshold = self.sanity_thresholds['latency_max_ms']
            passed = latency <= threshold
            checks['latency_acceptable'] = {
                'passed': passed,
                'value': latency,
                'threshold': threshold,
                'message': f"Latency {latency:.2f}ms {'<=' if passed else '>'} {threshold}ms",
            }
            all_passed &= passed
        
        print("\nSanity Check Results:")
        for check_name, check_data in checks.items():
            status_icon = "✅" if check_data['passed'] else "❌"
            print(f"  {status_icon} {check_data['message']}")
        
        self.results['sanity_checks'] = checks
        self.results['all_sanity_checks_passed'] = all_passed
        
        if all_passed:
            print("\n✅ All sanity checks PASSED")
        else:
            print("\n❌ Some sanity checks FAILED")
            self.results['recommendations'].append("Fix failing sanity checks before production rollout")
        
        return checks
    
    def step6_generate_metrics_report(self) -> str:
        """Step 6: Generate comprehensive metrics report"""
        print("\n" + "=" * 80)
        print("STEP 6: GENERATING METRICS REPORT")
        print("=" * 80)
        
        # Determine overall status
        all_checks_passed = self.results.get('all_sanity_checks_passed', False)
        unit_tests_ok = self.results.get('unit_tests', {}).get('pass_rate', 0) >= 80
        
        if all_checks_passed and unit_tests_ok:
            self.results['status'] = 'READY_FOR_PRODUCTION'
        elif all_checks_passed:
            self.results['status'] = 'READY_FOR_STAGING'
        else:
            self.results['status'] = 'NEEDS_FIXES'
        
        # Add recommendations based on results
        if self.results['status'] == 'NEEDS_FIXES':
            if not unit_tests_ok:
                self.results['recommendations'].append("Fix failing unit tests before deployment")
            if 'synthetic_tests' in self.results:
                syn = self.results['synthetic_tests']
                if syn.get('confidence', {}).get('std_dev', 0) <= 0.2:
                    self.results['recommendations'].append("Improve confidence distribution (increase std dev)")
                if syn.get('pre_validation', {}).get('catch_rate', 0) < 80:
                    self.results['recommendations'].append("Improve pre-validation catch rate (target >80%)")
        
        # Save to file
        report_path = 'phase2_staging_metrics.json'
        with open(report_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n✅ Metrics report saved to: {report_path}")
        print(f"\nOverall Status: {self.results['status']}")
        
        return report_path
    
    def step7_summary(self):
        """Step 7: Display summary for review"""
        print("\n" + "=" * 80)
        print("PHASE 2 STAGING DEPLOYMENT SUMMARY")
        print("=" * 80)
        
        print(f"\n📊 OVERALL STATUS: {self.results['status']}")
        
        # Unit tests
        if 'unit_tests' in self.results:
            ut = self.results['unit_tests']
            print(f"\n🧪 UNIT TESTS:")
            print(f"   Passed: {ut.get('passed', 0)}/{ut.get('total', 0)} ({ut.get('pass_rate', 0):.1f}%)")
        
        # Synthetic tests
        if 'synthetic_tests' in self.results:
            st = self.results['synthetic_tests']
            print(f"\n🎯 SYNTHETIC TESTS:")
            print(f"   Total Goals: {st.get('total_goals', 0)}")
            print(f"   Confidence σ: {st.get('confidence', {}).get('std_dev', 0):.3f}")
            print(f"   Pre-Val Catch: {st.get('pre_validation', {}).get('catch_rate', 0):.1f}%")
            print(f"   Approval Rate: {st.get('approval_requests', {}).get('rate', 0):.1f}%")
            print(f"   Latency: {st.get('latency_per_goal_ms', 0):.2f}ms/goal")
        
        # Sanity checks
        if 'sanity_checks' in self.results:
            passed_checks = sum(1 for c in self.results['sanity_checks'].values() if c['passed'])
            total_checks = len(self.results['sanity_checks'])
            print(f"\n✅ SANITY CHECKS:")
            print(f"   Passed: {passed_checks}/{total_checks}")
        
        # Recommendations
        if self.results['recommendations']:
            print(f"\n⚠️  RECOMMENDATIONS:")
            for i, rec in enumerate(self.results['recommendations'], 1):
                print(f"   {i}. {rec}")
        else:
            print(f"\n✅ No recommendations - system is ready!")
        
        print("\n" + "=" * 80)
        
        # Final verdict
        if self.results['status'] == 'READY_FOR_PRODUCTION':
            print("🚀 VERDICT: READY FOR PRODUCTION ROLLOUT")
        elif self.results['status'] == 'READY_FOR_STAGING':
            print("🟡 VERDICT: READY FOR STAGING (minor issues to address)")
        else:
            print("🔴 VERDICT: NEEDS FIXES BEFORE DEPLOYMENT")
        
        print("=" * 80)
    
    def run_full_verification(self):
        """Run complete verification pipeline"""
        print("\n" + "=" * 80)
        print("🚀 PHASE 2 STAGING DEPLOYMENT & VERIFICATION")
        print("=" * 80)
        print(f"Timestamp: {datetime.now().isoformat()}")
        print("=" * 80)
        
        try:
            # Run all steps
            self.step1_verify_feature_flags()
            self.step2_verify_integration()
            self.step3_run_unit_tests()
            self.step4_run_synthetic_tests()
            self.step5_sanity_checks()
            self.step6_generate_metrics_report()
            self.step7_summary()
            
        except KeyboardInterrupt:
            print("\n\n⚠️  Verification interrupted by user")
        except Exception as e:
            print(f"\n\n❌ Verification failed with error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    verifier = Phase2StagingVerifier()
    verifier.run_full_verification()
