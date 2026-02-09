"""
Phase 17: Continuous Autonomous Execution - Test Suite

Comprehensive unit and integration tests for Phase 17 components.
"""

import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from buddy_phase17_executor import (
    ContinuousAutonomousExecutor, Task, Heuristic, 
    RiskLevel, ExecutionStatus, ExecutionResult
)
from buddy_phase17_feedback_loop import FeedbackLoop, FeedbackEvent, LearningSignal
from buddy_phase17_monitor import RealTimeMonitor, PerformanceMetric, AnomalyDetection
from buddy_phase17_harness import Phase17Harness


@pytest.fixture
def temp_dirs():
    """Create temporary directories for testing"""
    with tempfile.TemporaryDirectory() as phase16_dir:
        with tempfile.TemporaryDirectory() as phase17_dir:
            p16 = Path(phase16_dir)
            p17 = Path(phase17_dir)
            yield p16, p17


@pytest.fixture
def sample_heuristics(temp_dirs):
    """Create sample heuristics file"""
    phase16_dir, _ = temp_dirs
    heuristics_file = phase16_dir / "heuristics.jsonl"
    
    heuristics = [
        {
            "heuristic_id": "H16_001",
            "category": "task_prioritization",
            "name": "Risk-Confidence Prioritization",
            "description": "Prioritize HIGH-confidence LOW-risk tasks first",
            "rule": {"priority_order": [{"risk_level": "LOW", "confidence_min": 0.85}]},
            "confidence": 0.92,
            "applicability": {"all_risk_levels": True, "min_confidence": 0.5},
            "expected_improvement": 0.08
        },
        {
            "heuristic_id": "H16_002",
            "category": "confidence_elevation",
            "name": "Pre-execution Confidence Boost",
            "description": "Apply +0.05 confidence boost to MEDIUM-risk tasks",
            "rule": {"condition": {"risk_level": "MEDIUM", "confidence_range": [0.7, 0.75]}, 
                     "action": "boost_confidence_by", "amount": 0.05},
            "confidence": 0.85,
            "applicability": {"risk_level": "MEDIUM", "confidence_range": [0.7, 0.75]},
            "expected_improvement": 0.05
        },
        {
            "heuristic_id": "H16_003",
            "category": "risk_assessment",
            "name": "Intelligent Retry Strategy",
            "description": "Retry failed LOW/MEDIUM risk tasks",
            "rule": {"condition": {"status": "failed", "risk_level": ["LOW", "MEDIUM"]}, 
                     "action": "retry_with_confidence_recalibration", 
                     "max_retries": 3, "confidence_penalty": -0.05},
            "confidence": 0.88,
            "applicability": {"applicable_statuses": ["failed"], 
                            "applicable_risk_levels": ["LOW", "MEDIUM"]},
            "expected_improvement": 0.03
        }
    ]
    
    with open(heuristics_file, 'w', encoding='utf-8') as f:
        for h in heuristics:
            f.write(json.dumps(h) + '\n')
    
    return heuristics_file


@pytest.fixture
def sample_tasks(temp_dirs):
    """Create sample planned tasks file"""
    phase16_dir, _ = temp_dirs
    tasks_file = phase16_dir / "planned_tasks.jsonl"
    
    tasks = [
        {
            "task_id": "wave1_task1",
            "wave": 1,
            "risk_level": "LOW",
            "confidence": 0.88,
            "priority": 1,
            "heuristics_applied": [],
            "predicted_success_rate": 0.89,
            "predicted_confidence_delta": 0.058,
            "approval_status": "APPROVED",
            "reason": "Task planned for wave 1"
        },
        {
            "task_id": "wave1_task2",
            "wave": 1,
            "risk_level": "MEDIUM",
            "confidence": 0.72,
            "priority": 2,
            "heuristics_applied": [],
            "predicted_success_rate": 0.75,
            "predicted_confidence_delta": 0.045,
            "approval_status": "APPROVED",
            "reason": "Task planned for wave 1"
        },
        {
            "task_id": "wave2_task1",
            "wave": 2,
            "risk_level": "LOW",
            "confidence": 0.85,
            "priority": 1,
            "heuristics_applied": [],
            "predicted_success_rate": 0.87,
            "predicted_confidence_delta": 0.052,
            "approval_status": "APPROVED",
            "reason": "Task planned for wave 2"
        }
    ]
    
    with open(tasks_file, 'w', encoding='utf-8') as f:
        for t in tasks:
            f.write(json.dumps(t) + '\n')
    
    return tasks_file


class TestContinuousAutonomousExecutor:
    """Test suite for ContinuousAutonomousExecutor"""
    
    def test_load_heuristics(self, temp_dirs, sample_heuristics):
        """Test loading heuristics from Phase 16"""
        phase16_dir, phase17_dir = temp_dirs
        executor = ContinuousAutonomousExecutor(phase16_dir, phase17_dir)
        
        num_heuristics = executor.load_heuristics()
        
        assert num_heuristics == 3
        assert len(executor.heuristics) == 3
        assert executor.heuristics[0].heuristic_id == "H16_001"
        assert executor.heuristics[1].category == "confidence_elevation"
    
    def test_load_planned_tasks(self, temp_dirs, sample_tasks):
        """Test loading planned tasks from Phase 16"""
        phase16_dir, phase17_dir = temp_dirs
        executor = ContinuousAutonomousExecutor(phase16_dir, phase17_dir)
        
        num_tasks = executor.load_planned_tasks()
        
        assert num_tasks == 3
        assert len(executor.tasks) == 3
        assert executor.tasks[0].task_id == "wave1_task1"
        assert executor.tasks[1].risk_level == RiskLevel.MEDIUM
    
    def test_apply_confidence_boost_heuristic(self, temp_dirs, sample_heuristics, sample_tasks):
        """Test applying H16_002 confidence boost heuristic"""
        phase16_dir, phase17_dir = temp_dirs
        executor = ContinuousAutonomousExecutor(phase16_dir, phase17_dir)
        
        executor.load_heuristics()
        executor.load_planned_tasks()
        
        # Task with MEDIUM risk and confidence 0.72 should get boost
        task = executor.tasks[1]  # wave1_task2
        assert task.risk_level == RiskLevel.MEDIUM
        initial_confidence = task.confidence
        
        applied = executor.apply_heuristics_to_task(task)
        
        assert "H16_002" in applied  # Confidence boost heuristic applied
        assert task.confidence > initial_confidence  # Confidence increased
        assert task.confidence == pytest.approx(initial_confidence + 0.05, abs=0.01)
    
    def test_execute_task(self, temp_dirs, sample_heuristics, sample_tasks):
        """Test executing a single task"""
        phase16_dir, phase17_dir = temp_dirs
        executor = ContinuousAutonomousExecutor(phase16_dir, phase17_dir)
        
        executor.load_heuristics()
        executor.load_planned_tasks()
        
        task = executor.tasks[0]
        result = executor.execute_task(task)
        
        assert isinstance(result, ExecutionResult)
        assert result.task_id == task.task_id
        assert result.status in [ExecutionStatus.SUCCESS, ExecutionStatus.FAILED]
        assert result.execution_time_ms > 0
        assert result.attempts == 1
        assert task.status in [ExecutionStatus.SUCCESS, ExecutionStatus.FAILED]
    
    def test_retry_failed_task(self, temp_dirs, sample_heuristics, sample_tasks):
        """Test retry mechanism for failed tasks"""
        phase16_dir, phase17_dir = temp_dirs
        executor = ContinuousAutonomousExecutor(phase16_dir, phase17_dir)
        
        executor.load_heuristics()
        executor.load_planned_tasks()
        
        task = executor.tasks[0]
        task.status = ExecutionStatus.FAILED
        task.attempts = 1
        task.confidence = 0.80
        
        initial_confidence = task.confidence
        retry_result = executor.retry_failed_task(task)
        
        if retry_result:  # If retry heuristic found
            assert task.confidence < initial_confidence  # Penalty applied
            assert retry_result.attempts == 2
    
    def test_execute_wave(self, temp_dirs, sample_heuristics, sample_tasks):
        """Test executing all tasks in a wave"""
        phase16_dir, phase17_dir = temp_dirs
        executor = ContinuousAutonomousExecutor(phase16_dir, phase17_dir)
        
        executor.load_heuristics()
        executor.load_planned_tasks()
        
        wave_results = executor.execute_wave(1)
        
        assert len(wave_results) >= 2  # At least 2 tasks in wave 1
        assert all(isinstance(r, ExecutionResult) for r in wave_results)
        assert all(r.wave == 1 for r in wave_results)
    
    def test_calculate_success_probability(self, temp_dirs, sample_heuristics, sample_tasks):
        """Test success probability calculation"""
        phase16_dir, phase17_dir = temp_dirs
        executor = ContinuousAutonomousExecutor(phase16_dir, phase17_dir)
        
        executor.load_heuristics()
        executor.load_planned_tasks()
        
        task = executor.tasks[0]
        prob = executor._calculate_success_probability(task)
        
        assert 0.0 <= prob <= 1.0
        assert prob > 0.5  # Should be reasonably high for LOW risk, high confidence


class TestFeedbackLoop:
    """Test suite for FeedbackLoop"""
    
    def test_load_execution_outcomes(self, temp_dirs):
        """Test loading execution outcomes"""
        phase16_dir, phase17_dir = temp_dirs
        
        # Create sample execution outcomes
        outcomes_file = phase17_dir / "execution_outcomes.jsonl"
        outcomes = [
            {
                "task_id": "task1",
                "wave": 1,
                "status": "success",
                "initial_confidence": 0.85,
                "final_confidence": 0.90,
                "confidence_delta": 0.05,
                "execution_time_ms": 25.0,
                "attempts": 1,
                "heuristics_applied": ["H16_001"],
                "error_message": None,
                "timestamp": "2026-02-05T12:00:00Z"
            }
        ]
        
        with open(outcomes_file, 'w', encoding='utf-8') as f:
            for o in outcomes:
                f.write(json.dumps(o) + '\n')
        
        feedback_loop = FeedbackLoop(phase17_dir, phase17_dir)
        num_outcomes = feedback_loop.load_execution_outcomes()
        
        assert num_outcomes == 1
        assert len(feedback_loop.execution_outcomes) == 1
    
    def test_analyze_heuristic_effectiveness(self, temp_dirs):
        """Test analyzing heuristic effectiveness"""
        phase16_dir, phase17_dir = temp_dirs
        
        # Create sample execution outcomes with heuristics
        outcomes_file = phase17_dir / "execution_outcomes.jsonl"
        outcomes = [
            {
                "task_id": "task1", "wave": 1, "status": "success",
                "confidence_delta": 0.05, "heuristics_applied": ["H16_001"],
                "initial_confidence": 0.85, "final_confidence": 0.90,
                "execution_time_ms": 25.0, "attempts": 1, "error_message": None,
                "timestamp": "2026-02-05T12:00:00Z"
            },
            {
                "task_id": "task2", "wave": 1, "status": "success",
                "confidence_delta": 0.03, "heuristics_applied": ["H16_001"],
                "initial_confidence": 0.82, "final_confidence": 0.85,
                "execution_time_ms": 22.0, "attempts": 1, "error_message": None,
                "timestamp": "2026-02-05T12:00:01Z"
            }
        ]
        
        with open(outcomes_file, 'w', encoding='utf-8') as f:
            for o in outcomes:
                f.write(json.dumps(o) + '\n')
        
        feedback_loop = FeedbackLoop(phase17_dir, phase17_dir)
        feedback_loop.load_execution_outcomes()
        stats = feedback_loop.analyze_heuristic_effectiveness()
        
        assert "H16_001" in stats
        assert stats["H16_001"]["applications"] == 2
        assert stats["H16_001"]["successes"] == 2
        assert stats["H16_001"]["success_rate"] == 1.0
    
    def test_generate_feedback_events(self, temp_dirs):
        """Test generating feedback events from outcomes"""
        phase16_dir, phase17_dir = temp_dirs
        
        outcomes_file = phase17_dir / "execution_outcomes.jsonl"
        outcomes = [
            {
                "task_id": "task1", "wave": 1, "status": "success",
                "confidence_delta": 0.05, "heuristics_applied": ["H16_001"],
                "initial_confidence": 0.85, "final_confidence": 0.90,
                "execution_time_ms": 25.0, "attempts": 1, "error_message": None,
                "timestamp": "2026-02-05T12:00:00Z"
            }
        ]
        
        with open(outcomes_file, 'w', encoding='utf-8') as f:
            for o in outcomes:
                f.write(json.dumps(o) + '\n')
        
        feedback_loop = FeedbackLoop(phase17_dir, phase17_dir)
        feedback_loop.load_execution_outcomes()
        num_events = feedback_loop.generate_feedback_events()
        
        assert num_events >= 2  # Task completion + heuristic application
        assert len(feedback_loop.feedback_events) >= 2
    
    def test_generate_learning_signals(self, temp_dirs):
        """Test generating learning signals"""
        phase16_dir, phase17_dir = temp_dirs
        
        outcomes_file = phase17_dir / "execution_outcomes.jsonl"
        outcomes = [
            {"task_id": f"task{i}", "wave": 1, "status": "success",
             "confidence_delta": 0.05, "heuristics_applied": ["H16_001"],
             "initial_confidence": 0.85, "final_confidence": 0.90,
             "execution_time_ms": 25.0, "attempts": 1, "error_message": None,
             "timestamp": "2026-02-05T12:00:00Z"}
            for i in range(5)
        ]
        
        with open(outcomes_file, 'w', encoding='utf-8') as f:
            for o in outcomes:
                f.write(json.dumps(o) + '\n')
        
        feedback_loop = FeedbackLoop(phase17_dir, phase17_dir)
        feedback_loop.load_execution_outcomes()
        feedback_loop.analyze_heuristic_effectiveness()
        num_signals = feedback_loop.generate_learning_signals()
        
        assert num_signals > 0
        assert len(feedback_loop.learning_signals) > 0


class TestRealTimeMonitor:
    """Test suite for RealTimeMonitor"""
    
    def test_calculate_realtime_metrics(self, temp_dirs):
        """Test calculating real-time metrics"""
        phase16_dir, phase17_dir = temp_dirs
        
        # Create sample stats
        stats_file = phase17_dir / "phase17_execution_stats.json"
        stats = {
            "tasks_executed": 10,
            "tasks_succeeded": 8,
            "tasks_failed": 2,
            "success_rate": 0.8,
            "total_retries": 2,
            "avg_execution_time_ms": 25.0,
            "avg_confidence_improvement": 0.04
        }
        
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f)
        
        monitor = RealTimeMonitor(phase17_dir, phase17_dir)
        monitor.load_execution_data()
        metrics = monitor.calculate_realtime_metrics()
        
        assert len(metrics) > 0
        assert all(isinstance(m, PerformanceMetric) for m in metrics)
        assert any(m.metric_name == "Success Rate" for m in metrics)
    
    def test_detect_anomalies(self, temp_dirs):
        """Test anomaly detection"""
        phase16_dir, phase17_dir = temp_dirs
        
        # Create outcomes with high failure rate in wave 1
        outcomes_file = phase17_dir / "execution_outcomes.jsonl"
        outcomes = [
            {"task_id": f"wave1_task{i}", "wave": 1, "status": "failed" if i < 3 else "success",
             "confidence_delta": -0.02 if i < 3 else 0.03,
             "heuristics_applied": [], "initial_confidence": 0.80,
             "final_confidence": 0.78 if i < 3 else 0.83,
             "execution_time_ms": 25.0, "attempts": 1, "error_message": "Failed" if i < 3 else None,
             "timestamp": "2026-02-05T12:00:00Z"}
            for i in range(5)
        ]
        
        with open(outcomes_file, 'w', encoding='utf-8') as f:
            for o in outcomes:
                f.write(json.dumps(o) + '\n')
        
        monitor = RealTimeMonitor(phase17_dir, phase17_dir)
        monitor.load_execution_data()
        anomalies = monitor.detect_anomalies()
        
        assert len(anomalies) > 0
        assert any(a.anomaly_type == "high_failure_rate" for a in anomalies)
    
    def test_generate_health_score(self, temp_dirs):
        """Test health score generation"""
        phase16_dir, phase17_dir = temp_dirs
        
        stats_file = phase17_dir / "phase17_execution_stats.json"
        stats = {
            "tasks_executed": 10,
            "tasks_succeeded": 9,
            "success_rate": 0.9,
            "total_retries": 1,
            "avg_execution_time_ms": 22.0,
            "avg_confidence_improvement": 0.05
        }
        
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f)
        
        monitor = RealTimeMonitor(phase17_dir, phase17_dir)
        monitor.load_execution_data()
        health = monitor.generate_health_score()
        
        assert "overall_health_score" in health
        assert "health_status" in health
        assert 0 <= health["overall_health_score"] <= 100
        assert health["health_status"] in ["EXCELLENT", "GOOD", "FAIR", "POOR"]


class TestPhase17Harness:
    """Test suite for Phase17Harness"""
    
    def test_complete_pipeline(self, temp_dirs, sample_heuristics, sample_tasks):
        """Test complete Phase 17 pipeline execution"""
        phase16_dir, phase17_dir = temp_dirs
        
        harness = Phase17Harness(phase16_dir, phase17_dir)
        summary = harness.run_complete_pipeline()
        
        assert summary["phase"] == 17
        assert summary["name"] == "Continuous Autonomous Execution"
        assert "execution_summary" in summary
        assert "feedback_summary" in summary
        assert "monitoring_summary" in summary
        assert summary["execution_summary"]["total_tasks"] == 3
    
    def test_output_files_generated(self, temp_dirs, sample_heuristics, sample_tasks):
        """Test that all expected output files are generated"""
        phase16_dir, phase17_dir = temp_dirs
        
        harness = Phase17Harness(phase16_dir, phase17_dir)
        harness.run_complete_pipeline()
        
        expected_files = [
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
        
        for filename in expected_files:
            file_path = phase17_dir / filename
            assert file_path.exists(), f"Expected output file not found: {filename}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
