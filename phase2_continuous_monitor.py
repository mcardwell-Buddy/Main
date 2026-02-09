"""
Phase 2 Continuous Monitoring System
====================================

Runs synthetic tests every 10-15 minutes and tracks metrics over time.
Alerts if any metric falls outside expected range.
"""

import json
import time
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any


class Phase2ContinuousMonitor:
    """Continuous monitoring system for Phase 2 staging"""
    
    def __init__(self, interval_minutes: int = 10, max_runs: int = 10):
        self.interval_minutes = interval_minutes
        self.max_runs = max_runs
        self.test_history: List[Dict] = []
        
        self.thresholds = {
            'confidence_std_dev_min': 0.2,
            'approval_rate_min': 10.0,
            'approval_rate_max': 30.0,
            'pre_validation_catch_rate_min': 80.0,
            'latency_max_ms': 50.0,
        }
    
    def run_single_test_cycle(self) -> Dict:
        """Run one cycle of synthetic tests"""
        print(f"\n{'=' * 80}")
        print(f"TEST CYCLE: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'=' * 80}")
        
        try:
            # Run synthetic harness
            print("Running synthetic tests...")
            start_time = time.time()
            
            result = subprocess.run(
                ['python', 'phase2_synthetic_harness.py'],
                capture_output=True,
                text=True,
                timeout=300,
            )
            
            elapsed = time.time() - start_time
            
            # Load results
            if Path('phase2_test_report.json').exists():
                with open('phase2_test_report.json') as f:
                    report = json.load(f)
                
                metrics = report['metrics']
                
                cycle_result = {
                    'timestamp': datetime.now().isoformat(),
                    'elapsed_seconds': elapsed,
                    'total_goals': report['test_run']['total_goals'],
                    'confidence_std_dev': metrics['confidence']['std_dev'],
                    'confidence_mean': metrics['confidence']['mean'],
                    'pre_validation_catch_rate': metrics['pre_validation']['catch_rate_percent'],
                    'approval_rate': metrics['approval_requests']['rate_percent'],
                    'clarification_rate': metrics['clarification_requests']['rate_percent'],
                    'latency_per_goal_ms': (elapsed / report['test_run']['total_goals']) * 1000,
                    'execution_paths': metrics['execution_paths'],
                }
                
                # Check for anomalies
                anomalies = self.check_for_anomalies(cycle_result)
                cycle_result['anomalies'] = anomalies
                
                # Display results
                self.display_cycle_results(cycle_result)
                
                return cycle_result
            else:
                return {'status': 'error', 'message': 'Report not found'}
        
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def check_for_anomalies(self, result: Dict) -> List[str]:
        """Check if any metrics are outside expected range"""
        anomalies = []
        
        # Check confidence std dev
        if result['confidence_std_dev'] < self.thresholds['confidence_std_dev_min']:
            anomalies.append(
                f"⚠️  Confidence std dev too low: {result['confidence_std_dev']:.3f} < {self.thresholds['confidence_std_dev_min']}"
            )
        
        # Check approval rate
        if result['approval_rate'] < self.thresholds['approval_rate_min']:
            anomalies.append(
                f"⚠️  Approval rate too low: {result['approval_rate']:.1f}% < {self.thresholds['approval_rate_min']}%"
            )
        elif result['approval_rate'] > self.thresholds['approval_rate_max']:
            anomalies.append(
                f"⚠️  Approval rate too high: {result['approval_rate']:.1f}% > {self.thresholds['approval_rate_max']}%"
            )
        
        # Check pre-validation catch rate
        if result['pre_validation_catch_rate'] < self.thresholds['pre_validation_catch_rate_min']:
            anomalies.append(
                f"⚠️  Pre-validation catch rate too low: {result['pre_validation_catch_rate']:.1f}% < {self.thresholds['pre_validation_catch_rate_min']}%"
            )
        
        # Check latency
        if result['latency_per_goal_ms'] > self.thresholds['latency_max_ms']:
            anomalies.append(
                f"⚠️  Latency too high: {result['latency_per_goal_ms']:.2f}ms > {self.thresholds['latency_max_ms']}ms"
            )
        
        return anomalies
    
    def display_cycle_results(self, result: Dict):
        """Display results of one test cycle"""
        print(f"\nResults:")
        print(f"  Goals Tested: {result['total_goals']}")
        print(f"  Elapsed Time: {result['elapsed_seconds']:.2f}s")
        print(f"  Latency: {result['latency_per_goal_ms']:.2f}ms/goal")
        print(f"\n  Confidence σ: {result['confidence_std_dev']:.3f} {'✅' if result['confidence_std_dev'] >= 0.2 else '❌'}")
        print(f"  Pre-Val Catch: {result['pre_validation_catch_rate']:.1f}% {'✅' if result['pre_validation_catch_rate'] >= 80 else '❌'}")
        print(f"  Approval Rate: {result['approval_rate']:.1f}% {'✅' if 10 <= result['approval_rate'] <= 30 else '⚠️'}")
        print(f"  Clarification: {result['clarification_rate']:.1f}%")
        
        if result.get('anomalies'):
            print(f"\n  ANOMALIES DETECTED:")
            for anomaly in result['anomalies']:
                print(f"    {anomaly}")
        else:
            print(f"\n  ✅ All metrics within expected range")
    
    def display_trend_summary(self):
        """Display summary of trends across test cycles"""
        if len(self.test_history) < 2:
            return
        
        print(f"\n{'=' * 80}")
        print(f"TREND SUMMARY (Last {len(self.test_history)} cycles)")
        print(f"{'=' * 80}")
        
        # Calculate trends
        metrics = ['confidence_std_dev', 'pre_validation_catch_rate', 'approval_rate', 'latency_per_goal_ms']
        
        print("\nMetric Trends:")
        for metric in metrics:
            values = [r[metric] for r in self.test_history if metric in r]
            if len(values) >= 2:
                avg = sum(values) / len(values)
                min_val = min(values)
                max_val = max(values)
                trend = "📈" if values[-1] > values[0] else "📉" if values[-1] < values[0] else "➡️"
                
                print(f"  {metric}:")
                print(f"    {trend} Current: {values[-1]:.3f}, Avg: {avg:.3f}, Range: [{min_val:.3f}, {max_val:.3f}]")
        
        # Count anomalies
        total_anomalies = sum(len(r.get('anomalies', [])) for r in self.test_history)
        print(f"\n  Total Anomalies: {total_anomalies}")
        
        if total_anomalies == 0:
            print(f"  ✅ No anomalies detected across all cycles")
        else:
            print(f"  ⚠️  {total_anomalies} anomalies detected - review required")
    
    def save_history(self):
        """Save test history to file"""
        history_path = 'phase2_monitoring_history.json'
        with open(history_path, 'w') as f:
            json.dump({
                'interval_minutes': self.interval_minutes,
                'max_runs': self.max_runs,
                'total_cycles': len(self.test_history),
                'test_history': self.test_history,
                'last_updated': datetime.now().isoformat(),
            }, f, indent=2)
        
        print(f"\n💾 History saved to: {history_path}")
    
    def run_continuous_monitoring(self):
        """Run continuous monitoring"""
        print("=" * 80)
        print("🔄 PHASE 2 CONTINUOUS MONITORING")
        print("=" * 80)
        print(f"Interval: {self.interval_minutes} minutes")
        print(f"Max Cycles: {self.max_runs}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        print("\nPress Ctrl+C to stop monitoring")
        
        try:
            for cycle in range(self.max_runs):
                print(f"\n\nCYCLE {cycle + 1}/{self.max_runs}")
                
                # Run test cycle
                result = self.run_single_test_cycle()
                
                if result.get('status') != 'error':
                    self.test_history.append(result)
                    
                    # Keep only last max_runs
                    if len(self.test_history) > self.max_runs:
                        self.test_history = self.test_history[-self.max_runs:]
                    
                    # Display trend summary
                    self.display_trend_summary()
                    
                    # Save history
                    self.save_history()
                else:
                    print(f"❌ Cycle failed: {result.get('message')}")
                
                # Wait for next cycle (unless last cycle)
                if cycle < self.max_runs - 1:
                    wait_seconds = self.interval_minutes * 60
                    print(f"\n⏳ Waiting {self.interval_minutes} minutes until next cycle...")
                    print(f"   Next cycle at: {datetime.fromtimestamp(time.time() + wait_seconds).strftime('%H:%M:%S')}")
                    time.sleep(wait_seconds)
            
            print("\n" + "=" * 80)
            print(f"✅ MONITORING COMPLETE ({self.max_runs} cycles)")
            print("=" * 80)
        
        except KeyboardInterrupt:
            print("\n\n⚠️  Monitoring stopped by user")
            self.save_history()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Phase 2 Continuous Monitoring')
    parser.add_argument('--interval', type=int, default=10, help='Interval between tests in minutes')
    parser.add_argument('--max-runs', type=int, default=10, help='Maximum number of test cycles')
    
    args = parser.parse_args()
    
    monitor = Phase2ContinuousMonitor(
        interval_minutes=args.interval,
        max_runs=args.max_runs,
    )
    
    monitor.run_continuous_monitoring()
