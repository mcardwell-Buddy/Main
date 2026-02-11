"""
Phase 17: Continuous Autonomous Execution - Complete Harness

Orchestrates the full Phase 17 pipeline: execution → feedback → monitoring
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

from buddy_phase17_executor import ContinuousAutonomousExecutor
from buddy_phase17_feedback_loop import FeedbackLoop
from buddy_phase17_monitor import RealTimeMonitor


class Phase17Harness:
    """
    Complete Phase 17 orchestration harness.
    Executes planned tasks, generates feedback, and monitors performance.
    """
    
    def __init__(self, phase16_dir: Path = None, phase17_output_dir: Path = None):
        self.phase16_dir = Path(phase16_dir or "outputs/phase16")
        self.phase17_output_dir = Path(phase17_output_dir or "outputs/phase17")
        self.phase17_output_dir.mkdir(parents=True, exist_ok=True)
        
        self.executor = ContinuousAutonomousExecutor(self.phase16_dir, self.phase17_output_dir)
        self.feedback_loop = FeedbackLoop(self.phase17_output_dir, self.phase17_output_dir)
        self.monitor = RealTimeMonitor(self.phase17_output_dir, self.phase17_output_dir)
        
        self.start_time = None
        self.end_time = None
    
    def run_complete_pipeline(self) -> Dict[str, Any]:
        """Execute the complete Phase 17 pipeline"""
        print(f"\n{'='*70}")
        print(f"PHASE 17: CONTINUOUS AUTONOMOUS EXECUTION")
        print(f"{'='*70}")
        print(f"Pipeline: Execution → Feedback → Monitoring")
        print(f"Phase 16 Input: {self.phase16_dir}")
        print(f"Phase 17 Output: {self.phase17_output_dir}")
        print(f"{'='*70}\n")
        
        self.start_time = time.time()
        
        # Step 1: Load Phase 16 heuristics and tasks
        print("Step 1: Loading Phase 16 Data...")
        num_heuristics = self.executor.load_heuristics()
        num_tasks = self.executor.load_planned_tasks()
        print(f"  ✓ Loaded {num_heuristics} heuristics")
        print(f"  ✓ Loaded {num_tasks} tasks")
        
        # Step 2: Execute all planned waves
        print("\nStep 2: Executing Planned Waves...")
        execution_summary = self.executor.execute_all_waves()
        print(f"  ✓ Executed {execution_summary['statistics']['tasks_executed']} tasks")
        print(f"  ✓ Success rate: {execution_summary['statistics']['success_rate']:.1%}")
        
        # Step 3: Write execution results
        print("\nStep 3: Writing Execution Results...")
        self.executor.write_results()
        
        # Step 4: Generate feedback loop
        print("\nStep 4: Generating Feedback Loop...")
        self.feedback_loop.load_execution_outcomes()
        self.feedback_loop.analyze_heuristic_effectiveness()
        num_events = self.feedback_loop.generate_feedback_events()
        num_signals = self.feedback_loop.generate_learning_signals()
        self.feedback_loop.write_feedback()
        print(f"  ✓ Generated {num_events} feedback events")
        print(f"  ✓ Generated {num_signals} learning signals")
        
        # Step 5: Real-time monitoring
        print("\nStep 5: Running Real-Time Monitoring...")
        self.monitor.load_execution_data()
        self.monitor.calculate_realtime_metrics()
        self.monitor.detect_anomalies()
        health = self.monitor.write_monitoring_report()
        print(f"  ✓ System health: {health['overall_health_score']:.1f}/100 ({health['health_status']})")
        
        # Step 6: Write Phase 17 summary
        self.end_time = time.time()
        summary = self._create_phase17_summary(execution_summary, health)
        self._write_phase17_summary(summary)
        
        # Step 7: Generate markdown report
        self._write_markdown_report(summary)
        
        print(f"\n{'='*70}")
        print(f"PHASE 17 COMPLETE")
        print(f"{'='*70}")
        print(f"Total Execution Time: {(self.end_time - self.start_time)*1000:.2f}ms")
        print(f"Tasks Executed: {execution_summary['statistics']['tasks_executed']}")
        print(f"Success Rate: {execution_summary['statistics']['success_rate']:.1%}")
        print(f"Learning Signals: {num_signals}")
        print(f"System Health: {health['health_status']}")
        print(f"{'='*70}\n")
        
        return summary
    
    def _create_phase17_summary(self, execution_summary: Dict, health: Dict) -> Dict[str, Any]:
        """Create comprehensive Phase 17 summary"""
        return {
            "phase": 17,
            "name": "Continuous Autonomous Execution",
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "execution_time_ms": (self.end_time - self.start_time) * 1000,
            "execution_summary": {
                "total_tasks": execution_summary["total_tasks"],
                "total_waves": execution_summary["total_waves"],
                "tasks_executed": execution_summary["statistics"]["tasks_executed"],
                "tasks_succeeded": execution_summary["statistics"]["tasks_succeeded"],
                "tasks_failed": execution_summary["statistics"]["tasks_failed"],
                "success_rate": execution_summary["statistics"]["success_rate"],
                "total_retries": execution_summary["statistics"]["total_retries"],
                "avg_execution_time_ms": execution_summary["statistics"]["avg_execution_time_ms"],
                "avg_confidence_improvement": execution_summary["statistics"]["avg_confidence_improvement"]
            },
            "feedback_summary": {
                "feedback_events": len(self.feedback_loop.feedback_events),
                "learning_signals": len(self.feedback_loop.learning_signals),
                "heuristics_analyzed": len(self.feedback_loop.heuristic_performance)
            },
            "monitoring_summary": {
                "metrics_tracked": len(self.monitor.metrics),
                "anomalies_detected": len(self.monitor.anomalies),
                "overall_health_score": health["overall_health_score"],
                "health_status": health["health_status"]
            },
            "heuristic_performance": self.feedback_loop.heuristic_performance,
            "outputs_generated": [
                "execution_outcomes.jsonl",
                "phase17_execution_stats.json",
                "feedback_events.jsonl",
                "learning_signals.jsonl",
                "heuristic_performance.json",
                "realtime_metrics.jsonl",
                "detected_anomalies.jsonl",
                "system_health.json",
                "phase17_summary.json",
                "PHASE_17_EXECUTION_REPORT.md"
            ]
        }
    
    def _write_phase17_summary(self, summary: Dict[str, Any]):
        """Write Phase 17 summary JSON"""
        summary_file = self.phase17_output_dir / "phase17_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
    
    def _write_markdown_report(self, summary: Dict[str, Any]):
        """Write comprehensive markdown report"""
        report_file = self.phase17_output_dir / "PHASE_17_EXECUTION_REPORT.md"
        
        report = f"""# Phase 17: Continuous Autonomous Execution Report

**Generated:** {summary['timestamp']}  
**Total Execution Time:** {summary['execution_time_ms']:.2f}ms

---

## Executive Summary

Phase 17 successfully executed **{summary['execution_summary']['tasks_executed']} tasks** across **{summary['execution_summary']['total_waves']} waves** with a **{summary['execution_summary']['success_rate']:.1%} success rate**. The system generated **{summary['feedback_summary']['learning_signals']} learning signals** for Phase 16 meta-learning adaptation and achieved an overall system health score of **{summary['monitoring_summary']['overall_health_score']:.1f}/100 ({summary['monitoring_summary']['health_status']})**.

---

## Execution Performance

### Task Statistics
- **Total Tasks Executed:** {summary['execution_summary']['tasks_executed']}
- **Successful:** {summary['execution_summary']['tasks_succeeded']} ({summary['execution_summary']['success_rate']:.1%})
- **Failed:** {summary['execution_summary']['tasks_failed']}
- **Total Retries:** {summary['execution_summary']['total_retries']}

### Performance Metrics
- **Average Execution Time:** {summary['execution_summary']['avg_execution_time_ms']:.2f}ms
- **Average Confidence Improvement:** {summary['execution_summary']['avg_confidence_improvement']:+.4f}
- **Task Throughput:** {1000.0 / summary['execution_summary']['avg_execution_time_ms']:.1f} tasks/sec

---

## Heuristic Performance Analysis

Phase 17 applied {summary['feedback_summary']['heuristics_analyzed']} learned heuristics from Phase 16:

"""
        
        for heuristic_id, stats in summary.get('heuristic_performance', {}).items():
            report += f"""
### {heuristic_id}
- **Applications:** {stats['applications']}
- **Success Rate:** {stats['success_rate']:.1%}
- **Avg Confidence Delta:** {stats['avg_confidence_delta']:+.4f}
- **Successes/Failures:** {stats['successes']}/{stats['failures']}
"""
        
        report += f"""
---

## Feedback Loop Summary

The feedback loop analyzed execution outcomes and generated actionable insights:

- **Feedback Events Generated:** {summary['feedback_summary']['feedback_events']}
- **Learning Signals Created:** {summary['feedback_summary']['learning_signals']}
- **Heuristics Analyzed:** {summary['feedback_summary']['heuristics_analyzed']}

### Learning Signals

Learning signals provide recommendations for Phase 16 meta-learning adaptation:

"""
        
        for signal in self.feedback_loop.learning_signals:
            report += f"""
#### {signal.signal_id} - {signal.signal_type.replace('_', ' ').title()}
- **Confidence:** {signal.confidence:.1%}
- **Description:** {signal.description}
- **Recommendation:** {signal.recommendation}
- **Evidence:**
"""
            for evidence in signal.supporting_evidence:
                report += f"  - {evidence}\n"
        
        report += f"""
---

## Real-Time Monitoring

### System Health
- **Overall Score:** {summary['monitoring_summary']['overall_health_score']:.1f}/100
- **Status:** {summary['monitoring_summary']['health_status']}
- **Metrics Tracked:** {summary['monitoring_summary']['metrics_tracked']}
- **Anomalies Detected:** {summary['monitoring_summary']['anomalies_detected']}

### Performance Metrics

"""
        
        for metric in self.monitor.metrics:
            status_icon = "✓" if metric.status == "normal" else "⚠" if metric.status == "warning" else "✗"
            report += f"""
#### {status_icon} {metric.metric_name}
- **Value:** {metric.value:.4f} {metric.unit}
- **Status:** {metric.status.upper()}
"""
            if metric.threshold_min:
                report += f"- **Threshold Min:** {metric.threshold_min}\n"
            if metric.threshold_max:
                report += f"- **Threshold Max:** {metric.threshold_max}\n"
        
        if self.monitor.anomalies:
            report += "\n### Detected Anomalies\n"
            for anomaly in self.monitor.anomalies:
                severity_icon = "⚠" if anomaly.severity == "low" else "⚠⚠" if anomaly.severity == "medium" else "⚠⚠⚠"
                report += f"""
#### {severity_icon} {anomaly.anomaly_type.replace('_', ' ').title()} [{anomaly.severity.upper()}]
- **Description:** {anomaly.description}
- **Affected Tasks:** {len(anomaly.affected_tasks)}
- **Recommendation:** {anomaly.recommendation}
"""
        
        report += f"""
---

## Output Files Generated

Phase 17 generated the following output files in `{self.phase17_output_dir}`:

"""
        for output_file in summary['outputs_generated']:
            report += f"- `{output_file}`\n"
        
        report += """
---

## Next Steps

1. **Phase 16 Feedback:** Learning signals should be fed back to Phase 16 for heuristic refinement
2. **Phase 18 Preparation:** Execution data ready for multi-agent coordination analysis
3. **Continuous Improvement:** Monitor system health and adjust thresholds as needed

---

**Phase 17 Status:** ✓ COMPLETE
"""
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n✓ Markdown report written to {report_file}")


def main():
    """Main Phase 17 execution"""
    harness = Phase17Harness()
    summary = harness.run_complete_pipeline()
    
    print(f"\n{'='*70}")
    print("Phase 17 execution complete!")
    print(f"View detailed report: {harness.phase17_output_dir / 'PHASE_17_EXECUTION_REPORT.md'}")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()

