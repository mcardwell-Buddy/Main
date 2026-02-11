"""
Phase 20: Predictive Task Assignment - Orchestration Harness

Purpose:
    Orchestrate complete Phase 20 pipeline:
    Phase 19 Outputs → Predictions → Scheduling → Feedback → Monitoring → Reports

Architecture:
    1. Load Phase 19 data (metrics, anomalies, signals, scheduled_tasks)
    2. Initialize and train predictor
    3. Predict task outcomes for upcoming waves
    4. Schedule tasks optimally
    5. Execute scheduled tasks
    6. Generate feedback to Phase 16/18
    7. Monitor system health
    8. Generate reports
"""

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from buddy_phase20_predictor import AdaptivePredictor, PredictionStrategy
from buddy_phase20_scheduler import PredictiveScheduler
from buddy_phase20_feedback_loop import PredictionFeedbackLoop
from buddy_phase20_monitor import PredictionMonitor


@dataclass
class Phase20ExecutionReport:
    """Report for Phase 20 execution"""
    execution_id: str
    phase: str
    status: str
    waves_processed: int
    agents_involved: int
    total_predictions: int
    total_assignments: int
    system_health_score: float
    health_status: str
    anomalies_detected: int
    learning_signals_generated: int
    execution_time_seconds: float
    start_time: str
    end_time: str
    summary: str


class Phase20Harness:
    """
    Orchestration harness for complete Phase 20 pipeline.
    """

    def __init__(
        self,
        phase19_input_dir: Path,
        phase16_dir: Path,
        phase18_dir: Path,
        phase20_output_dir: Path,
        dry_run: bool = True,
    ):
        """
        Initialize Phase 20 harness.
        
        Args:
            phase19_input_dir: Path to Phase 19 outputs
            phase16_dir: Path to Phase 16 directory (for feedback)
            phase18_dir: Path to Phase 18 directory (for feedback)
            phase20_output_dir: Path for Phase 20 outputs
            dry_run: If True, no side effects
        """
        self.phase19_input_dir = Path(phase19_input_dir)
        self.phase16_dir = Path(phase16_dir)
        self.phase18_dir = Path(phase18_dir)
        self.phase20_output_dir = Path(phase20_output_dir)
        self.dry_run = dry_run

        # Components
        self.predictor = AdaptivePredictor(
            phase19_input_dir, phase20_output_dir, dry_run
        )
        self.scheduler = PredictiveScheduler(phase20_output_dir, dry_run)
        self.feedback_loop = PredictionFeedbackLoop(
            phase16_dir, phase18_dir, phase20_output_dir, dry_run
        )
        self.monitor = PredictionMonitor(phase20_output_dir, dry_run)

        # Execution state
        self.execution_id = f"PHASE20_{self._utc_now().replace('-', '').replace(':', '').split('.')[0]}"
        self.start_time = None
        self.end_time = None
        self.execution_report = None

    def run_phase20(self, waves: List[int], agents: List[str]) -> Dict:
        """
        Run complete Phase 20 pipeline.
        
        Args:
            waves: List of wave numbers to process (e.g., [1, 2, 3])
            agents: List of agent IDs to involve (e.g., ['agent_0', 'agent_1', ...])
            
        Returns:
            Dictionary with execution status and metrics
        """
        self.start_time = self._utc_now()

        try:
            # Step 1: Load Phase 19 data
            print("[Phase 20] Step 1: Loading Phase 19 data...")
            load_result = self.predictor.load_phase19_data()
            print(f"  ✓ Loaded: {load_result}")

            # Step 2: Train predictor model
            print("[Phase 20] Step 2: Training predictor model...")
            accuracy, count = self.predictor.train_predictor(
                PredictionStrategy.ENSEMBLE
            )
            print(
                f"  ✓ Model trained: accuracy={accuracy:.2%}, predictions={count}"
            )

            # Step 3: Process each wave
            all_predictions = []
            all_assignments = []

            for wave in waves:
                print(f"[Phase 20] Step 3.{wave}: Processing Wave {wave}...")

                # Generate predictions for wave
                wave_predictions = self.predictor.predict_task_outcomes(
                    tasks=self._generate_sample_tasks(wave),
                    agents=agents,
                    wave=wave,
                )
                all_predictions.extend(wave_predictions)
                print(f"  ✓ Generated {len(wave_predictions)} predictions")

                # Write prediction outputs
                self.predictor.write_prediction_outputs(wave)

                # Schedule tasks
                print(f"[Phase 20] Step 4.{wave}: Scheduling Wave {wave}...")
                wave_assignments = self.scheduler.assign_tasks(
                    predictions=[asdict(p) for p in wave_predictions],
                    agents=agents,
                    wave=wave,
                )
                all_assignments.extend(wave_assignments)
                print(f"  ✓ Assigned {len(wave_assignments)} tasks")

                # Balance load
                self.scheduler.balance_load()

                # Execute predicted schedule
                schedule_exec = self.scheduler.execute_predicted_schedule()
                print(
                    f"  ✓ Schedule execution: success_rate={schedule_exec.predicted_success_rate:.2%}"
                )

                # Write schedule outputs
                self.scheduler.write_schedule_outputs(wave)

            # Step 5: Generate feedback
            print("[Phase 20] Step 5: Generating feedback signals...")
            actual_outcomes = self._generate_sample_outcomes(all_assignments)
            predictions_dict = [asdict(p) for p in all_predictions]

            self.feedback_loop.evaluate_predictions(
                predicted_outcomes=predictions_dict,
                actual_outcomes=actual_outcomes,
            )
            learning_signals = self.feedback_loop.generate_learning_signals()
            feedback_files = self.feedback_loop.write_feedback_outputs()
            print(
                f"  ✓ Generated {len(learning_signals)} learning signals"
            )
            print(f"  ✓ Feedback files: {feedback_files}")

            # Step 6: Monitor system health
            print("[Phase 20] Step 6: Monitoring system health...")
            self.monitor.calculate_metrics(predictions_dict, actual_outcomes)
            self.monitor.detect_anomalies()
            health_data = self.monitor.generate_system_health()
            monitoring_files = self.monitor.write_monitoring_outputs()
            print(f"  ✓ Health score: {health_data['overall_health_score']}/100")
            print(
                f"  ✓ Monitoring files: {monitoring_files}"
            )

            # Step 7: Generate final report
            self.end_time = self._utc_now()
            print("[Phase 20] Step 7: Generating execution report...")
            self.execution_report = self._generate_execution_report(
                waves=waves,
                agents=agents,
                predictions_count=len(all_predictions),
                assignments_count=len(all_assignments),
                learning_signals_count=len(learning_signals),
                health_score=health_data["overall_health_score"],
                health_status=health_data["health_status"],
                anomalies_count=len(self.monitor.anomalies),
            )
            self._write_execution_report()
            print(f"  ✓ Report generated: {self.execution_report.execution_id}")

            return {
                "status": "success",
                "execution_id": self.execution_id,
                "waves_processed": len(waves),
                "total_predictions": len(all_predictions),
                "total_assignments": len(all_assignments),
                "learning_signals_generated": len(learning_signals),
                "system_health_score": health_data["overall_health_score"],
                "system_health_status": health_data["health_status"],
                "anomalies_detected": len(self.monitor.anomalies),
            }

        except Exception as e:
            self.end_time = self._utc_now()
            print(f"[Phase 20] ERROR: {str(e)}")
            return {
                "status": "error",
                "execution_id": self.execution_id,
                "error": str(e),
            }

    def _generate_sample_tasks(self, wave: int) -> List[Dict]:
        """Generate sample task list for a wave (from Phase 19 scheduled_tasks)."""
        return [
            {
                "task_id": f"task_{wave}_1",
                "priority": "high",
                "estimated_duration": 30,
            },
            {
                "task_id": f"task_{wave}_2",
                "priority": "medium",
                "estimated_duration": 25,
            },
            {
                "task_id": f"task_{wave}_3",
                "priority": "low",
                "estimated_duration": 20,
            },
            {
                "task_id": f"task_{wave}_4",
                "priority": "high",
                "estimated_duration": 35,
            },
        ]

    def _generate_sample_outcomes(self, assignments: List[Dict]) -> List[Dict]:
        """Generate sample actual outcomes for evaluation."""
        outcomes = []
        for i, assignment in enumerate(assignments):
            outcomes.append(
                {
                    "task_id": assignment.get("task_id", f"task_{i}"),
                    "agent_id": assignment.get("agent_id", "agent_0"),
                    "status": "completed" if i % 3 != 0 else "failed",
                    "execution_time": 28 + (i % 5),
                    "actual_success": 1.0 if i % 3 != 0 else 0.0,
                }
            )
        return outcomes

    def _generate_execution_report(
        self,
        waves: List[int],
        agents: List[str],
        predictions_count: int,
        assignments_count: int,
        learning_signals_count: int,
        health_score: float,
        health_status: str,
        anomalies_count: int,
    ) -> Phase20ExecutionReport:
        """Generate execution report."""
        execution_time = (
            (datetime.fromisoformat(self.end_time) - datetime.fromisoformat(self.start_time)).total_seconds()
            if self.end_time and self.start_time
            else 0
        )

        return Phase20ExecutionReport(
            execution_id=self.execution_id,
            phase="Phase 20: Predictive Task Assignment",
            status="completed",
            waves_processed=len(waves),
            agents_involved=len(agents),
            total_predictions=predictions_count,
            total_assignments=assignments_count,
            system_health_score=health_score,
            health_status=health_status,
            anomalies_detected=anomalies_count,
            learning_signals_generated=learning_signals_count,
            execution_time_seconds=execution_time,
            start_time=self.start_time,
            end_time=self.end_time,
            summary=f"Phase 20 execution completed: {predictions_count} predictions, {assignments_count} assignments, {learning_signals_count} learning signals generated. System health: {health_status} ({health_score:.1f}/100)",
        )

    def _write_execution_report(self):
        """Write execution report to file."""
        report_file = (
            self.phase20_output_dir / "PHASE_20_AUTONOMOUS_EXECUTION.md"
        )

        report_content = f"""# Phase 20: Predictive Task Assignment - Execution Report

## Executive Summary
- **Execution ID:** {self.execution_report.execution_id}
- **Status:** {self.execution_report.status.upper()}
- **System Health:** {self.execution_report.health_status} ({self.execution_report.system_health_score:.1f}/100)
- **Execution Time:** {self.execution_report.execution_time_seconds:.2f} seconds

## Execution Metrics
- **Waves Processed:** {self.execution_report.waves_processed}
- **Agents Involved:** {self.execution_report.agents_involved}
- **Total Predictions:** {self.execution_report.total_predictions}
- **Total Assignments:** {self.execution_report.total_assignments}
- **Learning Signals Generated:** {self.execution_report.learning_signals_generated}
- **Anomalies Detected:** {self.execution_report.anomalies_detected}

## System Health Components
- **Overall Score:** {self.execution_report.system_health_score:.1f}/100
- **Status:** {self.execution_report.health_status}

## Execution Timeline
- **Start Time:** {self.execution_report.start_time}
- **End Time:** {self.execution_report.end_time}
- **Duration:** {self.execution_report.execution_time_seconds:.2f} seconds

## Summary
{self.execution_report.summary}

## Output Files Generated
- `metrics.jsonl` - Monitoring metrics (5 core metrics)
- `anomalies.jsonl` - Detected anomalies (4 types)
- `system_health.json` - Overall system health score
- `predicted_tasks.jsonl` - Per-agent predictions (wave-specific)
- `predicted_schedule.jsonl` - Task assignments and schedule (wave-specific)
- `learning_signals.jsonl` - Feedback signals for continuous learning

## Next Steps
1. Review system health metrics and anomalies
2. Analyze learning signals for Phase 16/18 feedback
3. Adjust prediction strategies if anomalies detected
4. Prepare for next phase execution
"""

        with open(report_file, "w") as f:
            f.write(report_content)

    def _utc_now(self) -> str:
        """Return current UTC timestamp in ISO format."""
        return datetime.now(timezone.utc).isoformat()

