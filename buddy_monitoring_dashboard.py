#!/usr/bin/env python3
"""
Buddy Traffic Monitoring Dashboard
===================================

Real-time monitoring dashboard showing key metrics and alerts.
Provides continuous monitoring of traffic simulation.

Status: PRODUCTION READY
Safe: YES (read-only to all files)
"""

import json
import time
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional
import threading

class BuddyMonitoringDashboard:
    """Real-time monitoring dashboard for Buddy traffic."""
    
    def __init__(self, metrics_file: str = 'buddy_traffic_metrics.json',
                 refresh_interval: int = 10):
        """Initialize dashboard."""
        self.metrics_file = metrics_file
        self.refresh_interval = refresh_interval
        self.last_data = None
        self.last_report_count = 0
        self.alert_history = []
        self.running = True
        
    def load_metrics(self) -> Optional[Dict[str, Any]]:
        """Load latest metrics."""
        if not os.path.exists(self.metrics_file):
            return None
        
        try:
            with open(self.metrics_file, 'r') as f:
                return json.load(f)
        except:
            return None
    
    def clear_screen(self) -> None:
        """Clear terminal screen."""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def format_time(self, seconds: float) -> str:
        """Format seconds to readable time."""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{int(seconds/60)}m {int(seconds%60)}s"
        else:
            return f"{int(seconds/3600)}h {int((seconds%3600)/60)}m"
    
    def check_alerts(self, report: Dict[str, Any]) -> list:
        """Check for alert conditions."""
        alerts = []
        
        # Performance alert
        if report['execution_time']['average'] > 5.0:
            alerts.append({
                'severity': 'HIGH',
                'message': f"High execution time: {report['execution_time']['average']:.2f}ms",
            })
        
        # Success rate alert
        if report['success_rate'] < 90.0:
            alerts.append({
                'severity': 'HIGH',
                'message': f"Low success rate: {report['success_rate']:.1f}%",
            })
        
        # Error rate alert
        if report['error_rate'] > 5.0:
            alerts.append({
                'severity': 'MEDIUM',
                'message': f"High error rate: {report['error_rate']:.2f}%",
            })
        
        # Adversarial blocking alert
        if report['adversarial']['block_rate'] < 90.0:
            alerts.append({
                'severity': 'HIGH',
                'message': f"Low adversarial block rate: {report['adversarial']['block_rate']:.1f}%",
            })
        
        # Pre-validation alert
        if report['pre_validation']['pass_rate'] < 30.0 or report['pre_validation']['pass_rate'] > 70.0:
            alerts.append({
                'severity': 'MEDIUM',
                'message': f"Unusual pre-validation rate: {report['pre_validation']['pass_rate']:.1f}%",
            })
        
        return alerts
    
    def print_header(self) -> None:
        """Print dashboard header."""
        print("╔" + "═"*78 + "╗")
        print("║" + " "*78 + "║")
        print("║" + "BUDDY TRAFFIC MONITORING DASHBOARD".center(78) + "║")
        print("║" + f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}".ljust(78) + "║")
        print("║" + " "*78 + "║")
        print("╚" + "═"*78 + "╝")
    
    def print_metrics_section(self, report: Dict[str, Any]) -> None:
        """Print metrics section."""
        print("\n┌─ KEY METRICS " + "─"*63 + "┐")
        
        metrics_rows = [
            ("Total Requests", f"{report['total_requests']}"),
            ("Success Rate", f"{report['success_rate']:.1f}%"),
            ("Failure Rate", f"{report['failure_rate']:.1f}%"),
            ("Avg Execution", f"{report['execution_time']['average']:.2f}ms"),
            ("Max Execution", f"{report['execution_time']['max']:.2f}ms"),
            ("P95/P99", f"{report['execution_time']['p95']:.2f}ms / {report['execution_time']['p99']:.2f}ms"),
            ("Confidence Mean", f"{report['confidence']['mean']:.3f}"),
            ("Confidence σ", f"{report['confidence']['std_dev']:.3f}"),
            ("Pre-val Pass Rate", f"{report['pre_validation']['pass_rate']:.1f}%"),
            ("Approval Rate", f"{report['approval_path']['approval_rate']:.1f}%"),
            ("Adversarial Block", f"{report['adversarial']['block_rate']:.1f}%"),
            ("Error Rate", f"{report['error_rate']:.2f}%"),
        ]
        
        for label, value in metrics_rows:
            print(f"│ {label:.<35} {value:>40} │")
        
        print("└" + "─"*78 + "┘")
    
    def print_load_section(self, report: Dict[str, Any]) -> None:
        """Print load and interval section."""
        print("\n┌─ LOAD & CONFIGURATION " + "─"*52 + "┐")
        
        load_bars = {
            1: "████░░░░░░",
            2: "████████░░",
            3: "██████████",
        }
        
        load_level = report.get('load_level', 1)
        bar = load_bars.get(load_level, "░░░░░░░░░░")
        
        print(f"│ Load Level: {load_level} {bar} {report.get('request_interval', '?')}".ljust(78) + "│")
        print(f"│ Elapsed: {self.format_time(report['elapsed_time'])}".ljust(78) + "│")
        print("└" + "─"*78 + "┘")
    
    def print_alerts_section(self, alerts: list) -> None:
        """Print alerts section."""
        if not alerts:
            print("\n┌─ ALERTS " + "─"*66 + "┐")
            print("│ ✓ No alerts".ljust(78) + "│")
            print("└" + "─"*78 + "┘")
            return
        
        print("\n┌─ ALERTS " + "─"*66 + "┐")
        
        for alert in alerts:
            severity = alert['severity']
            message = alert['message']
            
            # Color-code severity
            if severity == 'HIGH':
                icon = "⚠️ "
            elif severity == 'MEDIUM':
                icon = "ℹ️  "
            else:
                icon = "•  "
            
            full_msg = f"{icon}{message}"
            print(f"│ {full_msg}".ljust(78) + "│")
        
        print("└" + "─"*78 + "┘")
    
    def print_status_indicators(self, report: Dict[str, Any]) -> None:
        """Print status indicators."""
        print("\n┌─ STATUS INDICATORS " + "─"*55 + "┐")
        
        # Overall health
        health_score = (
            report['success_rate'] * 0.4 +
            (100 - report['error_rate']) * 0.3 +
            report['adversarial']['block_rate'] * 0.3
        )
        
        if health_score >= 95:
            health = "🟢 EXCELLENT"
        elif health_score >= 85:
            health = "🟡 GOOD"
        elif health_score >= 70:
            health = "🟠 FAIR"
        else:
            health = "🔴 POOR"
        
        # Performance status
        if report['execution_time']['average'] < 1.0:
            perf = "🟢 FAST"
        elif report['execution_time']['average'] < 3.0:
            perf = "🟡 NORMAL"
        elif report['execution_time']['average'] < 5.0:
            perf = "🟠 SLOW"
        else:
            perf = "🔴 CRITICAL"
        
        # Stability status
        if report['error_rate'] < 1.0:
            stability = "🟢 STABLE"
        elif report['error_rate'] < 5.0:
            stability = "🟡 STABLE"
        else:
            stability = "🔴 UNSTABLE"
        
        print(f"│ Overall Health: {health}".ljust(78) + "│")
        print(f"│ Performance: {perf}".ljust(78) + "│")
        print(f"│ Stability: {stability}".ljust(78) + "│")
        
        print("└" + "─"*78 + "┘")
    
    def display(self) -> None:
        """Display dashboard."""
        data = self.load_metrics()
        
        if not data or 'reports' not in data or not data['reports']:
            print("Waiting for metrics data... (no reports yet)")
            return
        
        report = data['reports'][-1]
        alerts = self.check_alerts(report)
        
        self.clear_screen()
        self.print_header()
        self.print_metrics_section(report)
        self.print_load_section(report)
        self.print_alerts_section(alerts)
        self.print_status_indicators(report)
        
        # Store alerts
        if alerts:
            self.alert_history.extend(alerts)
        
        # Summary
        print("\n" + "─"*80)
        print(f"Next update in {self.refresh_interval}s... (Press Ctrl+C to stop)")
        print("─"*80 + "\n")
    
    def run(self) -> None:
        """Run dashboard continuously."""
        try:
            while self.running:
                self.display()
                time.sleep(self.refresh_interval)
        except KeyboardInterrupt:
            print("\n⏹️  Dashboard stopped")
            self.running = False

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Buddy Traffic Monitoring Dashboard')
    parser.add_argument('--file', default='buddy_traffic_metrics.json',
                       help='Metrics JSON file')
    parser.add_argument('--interval', type=int, default=10,
                       help='Refresh interval in seconds (default: 10)')
    
    args = parser.parse_args()
    
    dashboard = BuddyMonitoringDashboard(
        metrics_file=args.file,
        refresh_interval=args.interval
    )
    dashboard.run()

if __name__ == '__main__':
    main()

