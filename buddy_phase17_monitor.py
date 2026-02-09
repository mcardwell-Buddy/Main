"""
Phase 17: Continuous Autonomous Execution - Real-Time Monitor

This module provides real-time monitoring of the autonomous execution system.
It tracks performance metrics, detects anomalies, and provides alerts.
"""

import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional


@dataclass
class PerformanceMetric:
    """Real-time performance metric"""
    metric_name: str
    value: float
    unit: str
    threshold_min: Optional[float]
    threshold_max: Optional[float]
    status: str  # "normal", "warning", "critical"
    timestamp: str


@dataclass
class AnomalyDetection:
    """Detected anomaly in execution"""
    anomaly_id: str
    anomaly_type: str  # "performance_degradation", "high_failure_rate", "confidence_drop"
    severity: str  # "low", "medium", "high"
    description: str
    affected_tasks: List[str]
    recommendation: str
    timestamp: str


class RealTimeMonitor:
    """
    Monitors Phase 17 execution in real-time, tracks metrics,
    and detects anomalies that require attention.
    """
    
    def __init__(self, phase17_output_dir: Path, monitor_output_dir: Path):
        self.phase17_output_dir = Path(phase17_output_dir)
        self.monitor_output_dir = Path(monitor_output_dir)
        self.monitor_output_dir.mkdir(parents=True, exist_ok=True)
        
        self.metrics: List[PerformanceMetric] = []
        self.anomalies: List[AnomalyDetection] = []
        
        self.execution_outcomes = []
        self.execution_stats = {}
    
    def load_execution_data(self):
        """Load execution outcomes and statistics"""
        # Load outcomes
        outcomes_file = self.phase17_output_dir / "execution_outcomes.jsonl"
        if outcomes_file.exists():
            with open(outcomes_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        self.execution_outcomes.append(json.loads(line))
        
        # Load stats
        stats_file = self.phase17_output_dir / "phase17_execution_stats.json"
        if stats_file.exists():
            with open(stats_file, 'r', encoding='utf-8') as f:
                self.execution_stats = json.load(f)
    
    def calculate_realtime_metrics(self) -> List[PerformanceMetric]:
        """Calculate real-time performance metrics"""
        print("\n=== Real-Time Performance Metrics ===")
        timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        
        metrics = []
        
        # Metric 1: Success Rate
        if self.execution_stats.get("success_rate") is not None:
            success_rate = self.execution_stats["success_rate"]
            status = "normal" if success_rate >= 0.75 else "warning" if success_rate >= 0.6 else "critical"
            
            metric = PerformanceMetric(
                metric_name="Success Rate",
                value=success_rate,
                unit="ratio",
                threshold_min=0.75,
                threshold_max=None,
                status=status,
                timestamp=timestamp
            )
            metrics.append(metric)
            print(f"  Success Rate: {success_rate:.1%} [{status.upper()}]")
        
        # Metric 2: Average Execution Time
        if self.execution_stats.get("avg_execution_time_ms") is not None:
            avg_time = self.execution_stats["avg_execution_time_ms"]
            status = "normal" if avg_time <= 30 else "warning" if avg_time <= 50 else "critical"
            
            metric = PerformanceMetric(
                metric_name="Average Execution Time",
                value=avg_time,
                unit="ms",
                threshold_min=None,
                threshold_max=30.0,
                status=status,
                timestamp=timestamp
            )
            metrics.append(metric)
            print(f"  Avg Execution Time: {avg_time:.2f}ms [{status.upper()}]")
        
        # Metric 3: Confidence Improvement Rate
        if self.execution_stats.get("avg_confidence_improvement") is not None:
            conf_delta = self.execution_stats["avg_confidence_improvement"]
            status = "normal" if conf_delta >= 0.02 else "warning" if conf_delta >= 0 else "critical"
            
            metric = PerformanceMetric(
                metric_name="Average Confidence Delta",
                value=conf_delta,
                unit="ratio",
                threshold_min=0.02,
                threshold_max=None,
                status=status,
                timestamp=timestamp
            )
            metrics.append(metric)
            print(f"  Avg Confidence Δ: {conf_delta:+.4f} [{status.upper()}]")
        
        # Metric 4: Retry Rate
        if self.execution_stats.get("total_retries") is not None and self.execution_stats.get("tasks_executed") is not None:
            retry_rate = self.execution_stats["total_retries"] / self.execution_stats["tasks_executed"]
            status = "normal" if retry_rate <= 0.2 else "warning" if retry_rate <= 0.4 else "critical"
            
            metric = PerformanceMetric(
                metric_name="Retry Rate",
                value=retry_rate,
                unit="ratio",
                threshold_min=None,
                threshold_max=0.2,
                status=status,
                timestamp=timestamp
            )
            metrics.append(metric)
            print(f"  Retry Rate: {retry_rate:.1%} [{status.upper()}]")
        
        # Metric 5: Task Throughput
        if self.execution_stats.get("tasks_executed") is not None and self.execution_stats.get("avg_execution_time_ms") is not None:
            throughput = 1000.0 / self.execution_stats["avg_execution_time_ms"]  # tasks/second
            status = "normal" if throughput >= 30 else "warning" if throughput >= 20 else "critical"
            
            metric = PerformanceMetric(
                metric_name="Task Throughput",
                value=throughput,
                unit="tasks/sec",
                threshold_min=30.0,
                threshold_max=None,
                status=status,
                timestamp=timestamp
            )
            metrics.append(metric)
            print(f"  Task Throughput: {throughput:.1f} tasks/sec [{status.upper()}]")
        
        self.metrics = metrics
        return metrics
    
    def detect_anomalies(self) -> List[AnomalyDetection]:
        """Detect anomalies in execution patterns"""
        print("\n=== Anomaly Detection ===")
        anomaly_count = 0
        timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        
        # Anomaly 1: High failure rate in specific wave
        wave_failures = {}
        for outcome in self.execution_outcomes:
            wave = outcome["wave"]
            if wave not in wave_failures:
                wave_failures[wave] = {"total": 0, "failed": 0, "tasks": []}
            wave_failures[wave]["total"] += 1
            if outcome["status"] != "success":
                wave_failures[wave]["failed"] += 1
                wave_failures[wave]["tasks"].append(outcome["task_id"])
        
        for wave, stats in wave_failures.items():
            if stats["total"] >= 3:
                failure_rate = stats["failed"] / stats["total"]
                if failure_rate > 0.5:
                    severity = "high" if failure_rate > 0.75 else "medium"
                    anomaly = AnomalyDetection(
                        anomaly_id=f"anomaly_{anomaly_count:03d}",
                        anomaly_type="high_failure_rate",
                        severity=severity,
                        description=f"Wave {wave} has {failure_rate:.1%} failure rate",
                        affected_tasks=stats["tasks"],
                        recommendation=f"Investigate wave {wave} task configuration or increase confidence thresholds",
                        timestamp=timestamp
                    )
                    self.anomalies.append(anomaly)
                    anomaly_count += 1
                    print(f"  ⚠ High failure rate in Wave {wave}: {failure_rate:.1%} ({len(stats['tasks'])} failed tasks)")
        
        # Anomaly 2: Performance degradation over time
        if len(self.execution_outcomes) >= 6:
            # Compare first half vs second half
            mid_point = len(self.execution_outcomes) // 2
            first_half = self.execution_outcomes[:mid_point]
            second_half = self.execution_outcomes[mid_point:]
            
            first_success_rate = sum(1 for o in first_half if o["status"] == "success") / len(first_half)
            second_success_rate = sum(1 for o in second_half if o["status"] == "success") / len(second_half)
            
            if first_success_rate - second_success_rate > 0.2:
                anomaly = AnomalyDetection(
                    anomaly_id=f"anomaly_{anomaly_count:03d}",
                    anomaly_type="performance_degradation",
                    severity="medium",
                    description=f"Performance degraded from {first_success_rate:.1%} to {second_success_rate:.1%}",
                    affected_tasks=[o["task_id"] for o in second_half if o["status"] != "success"],
                    recommendation="Investigate system resource constraints or increasing task complexity",
                    timestamp=timestamp
                )
                self.anomalies.append(anomaly)
                anomaly_count += 1
                print(f"  ⚠ Performance degradation detected: {first_success_rate:.1%} → {second_success_rate:.1%}")
        
        # Anomaly 3: Confidence drop pattern
        negative_deltas = [o for o in self.execution_outcomes if o["confidence_delta"] < -0.03]
        if len(negative_deltas) > len(self.execution_outcomes) * 0.3:
            anomaly = AnomalyDetection(
                anomaly_id=f"anomaly_{anomaly_count:03d}",
                anomaly_type="confidence_drop",
                severity="medium",
                description=f"{len(negative_deltas)} tasks with significant confidence drops (>{len(negative_deltas)/len(self.execution_outcomes):.0%})",
                affected_tasks=[o["task_id"] for o in negative_deltas],
                recommendation="Review confidence calibration or increase task preparation phase",
                timestamp=timestamp
            )
            self.anomalies.append(anomaly)
            anomaly_count += 1
            print(f"  ⚠ Confidence drop pattern: {len(negative_deltas)} tasks with Δconf < -0.03")
        
        # Anomaly 4: Excessive retries
        excessive_retries = [o for o in self.execution_outcomes if o["attempts"] > 2]
        if len(excessive_retries) > len(self.execution_outcomes) * 0.25:
            anomaly = AnomalyDetection(
                anomaly_id=f"anomaly_{anomaly_count:03d}",
                anomaly_type="excessive_retries",
                severity="low",
                description=f"{len(excessive_retries)} tasks required >2 attempts",
                affected_tasks=[o["task_id"] for o in excessive_retries],
                recommendation="Adjust retry thresholds or improve initial task confidence estimation",
                timestamp=timestamp
            )
            self.anomalies.append(anomaly)
            anomaly_count += 1
            print(f"  ⚠ Excessive retries: {len(excessive_retries)} tasks needed >2 attempts")
        
        if anomaly_count == 0:
            print("  ✓ No anomalies detected - system operating normally")
        
        return self.anomalies
    
    def generate_health_score(self) -> Dict[str, Any]:
        """Calculate overall system health score"""
        # Weight factors
        weights = {
            "success_rate": 0.40,
            "execution_time": 0.20,
            "confidence_delta": 0.20,
            "retry_rate": 0.10,
            "anomaly_severity": 0.10
        }
        
        scores = {}
        
        # Score success rate (0-100)
        if self.execution_stats.get("success_rate") is not None:
            scores["success_rate"] = self.execution_stats["success_rate"] * 100
        else:
            scores["success_rate"] = 50.0
        
        # Score execution time (0-100, lower is better)
        if self.execution_stats.get("avg_execution_time_ms") is not None:
            avg_time = self.execution_stats["avg_execution_time_ms"]
            scores["execution_time"] = max(0, min(100, 100 - (avg_time - 20)))
        else:
            scores["execution_time"] = 50.0
        
        # Score confidence improvement (0-100)
        if self.execution_stats.get("avg_confidence_improvement") is not None:
            conf_delta = self.execution_stats["avg_confidence_improvement"]
            scores["confidence_delta"] = min(100, max(0, 50 + (conf_delta * 500)))
        else:
            scores["confidence_delta"] = 50.0
        
        # Score retry rate (0-100, lower is better)
        if self.execution_stats.get("total_retries") is not None:
            retry_rate = self.execution_stats["total_retries"] / max(1, self.execution_stats["tasks_executed"])
            scores["retry_rate"] = max(0, 100 - (retry_rate * 200))
        else:
            scores["retry_rate"] = 50.0
        
        # Score anomaly severity (0-100, fewer/lower is better)
        if self.anomalies:
            severity_penalties = {"low": 5, "medium": 15, "high": 30}
            total_penalty = sum(severity_penalties.get(a.severity, 10) for a in self.anomalies)
            scores["anomaly_severity"] = max(0, 100 - total_penalty)
        else:
            scores["anomaly_severity"] = 100.0
        
        # Calculate weighted health score
        health_score = sum(scores[k] * weights[k] for k in weights.keys())
        
        # Determine health status
        if health_score >= 85:
            health_status = "EXCELLENT"
        elif health_score >= 70:
            health_status = "GOOD"
        elif health_score >= 55:
            health_status = "FAIR"
        else:
            health_status = "POOR"
        
        return {
            "overall_health_score": health_score,
            "health_status": health_status,
            "component_scores": scores,
            "weights": weights,
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        }
    
    def write_monitoring_report(self):
        """Write monitoring report and metrics"""
        # Write metrics
        metrics_file = self.monitor_output_dir / "realtime_metrics.jsonl"
        with open(metrics_file, 'w', encoding='utf-8') as f:
            for metric in self.metrics:
                metric_dict = {
                    "metric_name": metric.metric_name,
                    "value": metric.value,
                    "unit": metric.unit,
                    "threshold_min": metric.threshold_min,
                    "threshold_max": metric.threshold_max,
                    "status": metric.status,
                    "timestamp": metric.timestamp
                }
                f.write(json.dumps(metric_dict) + '\n')
        
        # Write anomalies
        anomalies_file = self.monitor_output_dir / "detected_anomalies.jsonl"
        with open(anomalies_file, 'w', encoding='utf-8') as f:
            for anomaly in self.anomalies:
                anomaly_dict = {
                    "anomaly_id": anomaly.anomaly_id,
                    "anomaly_type": anomaly.anomaly_type,
                    "severity": anomaly.severity,
                    "description": anomaly.description,
                    "affected_tasks": anomaly.affected_tasks,
                    "recommendation": anomaly.recommendation,
                    "timestamp": anomaly.timestamp
                }
                f.write(json.dumps(anomaly_dict) + '\n')
        
        # Write health score
        health = self.generate_health_score()
        health_file = self.monitor_output_dir / "system_health.json"
        with open(health_file, 'w', encoding='utf-8') as f:
            json.dump(health, f, indent=2)
        
        print(f"\n✓ Monitoring report written to {self.monitor_output_dir}")
        
        return health


def main():
    """Main monitoring execution"""
    phase17_output_dir = Path("outputs/phase17")
    monitor_output_dir = Path("outputs/phase17")
    
    print(f"\n{'='*70}")
    print(f"Phase 17: Real-Time Monitoring")
    print(f"{'='*70}")
    
    monitor = RealTimeMonitor(phase17_output_dir, monitor_output_dir)
    
    # Load execution data
    monitor.load_execution_data()
    print(f"Loaded {len(monitor.execution_outcomes)} execution outcomes")
    
    # Calculate metrics
    metrics = monitor.calculate_realtime_metrics()
    
    # Detect anomalies
    anomalies = monitor.detect_anomalies()
    
    # Generate health score and write report
    health = monitor.write_monitoring_report()
    
    # Print summary
    print(f"\n{'='*70}")
    print(f"System Health Summary:")
    print(f"  Overall Health Score: {health['overall_health_score']:.1f}/100")
    print(f"  Health Status: {health['health_status']}")
    print(f"  Metrics Tracked: {len(metrics)}")
    print(f"  Anomalies Detected: {len(anomalies)}")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
