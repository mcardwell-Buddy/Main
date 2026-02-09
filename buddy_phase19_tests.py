"""
Phase 19: Optimization & Adaptive Scheduling - Test Harness

Comprehensive test coverage for Phase 19 modules.
Validates optimization, scheduling, feedback, monitoring, and orchestration.
"""

import json
import pytest
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any

from buddy_phase19_optimizer import AdaptiveOptimizer, OptimizationStrategy
from buddy_phase19_scheduler import AdaptiveScheduler, ScheduleStatus
from buddy_phase19_feedback_loop import OptimizationFeedbackLoop
from buddy_phase19_monitor import OptimizationMonitor
from buddy_phase19_harness import Phase19Harness


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def temp_dirs(tmp_path):
    """Create temporary directories for testing."""
    phase18_dir = tmp_path / "phase18"
    phase19_dir = tmp_path / "phase19"
    phase18_dir.mkdir()
    phase19_dir.mkdir()
    return {"phase18": phase18_dir, "phase19": phase19_dir}


@pytest.fixture
def sample_phase18_data(temp_dirs):
    """Create sample Phase 18 outputs."""
    phase18_dir = temp_dirs["phase18"]
    
    # multi_agent_summary.json
    summary = {
        "total_agents": 4,
        "total_tasks": 12,
        "success_rate": 0.917,
        "avg_execution_time_ms": 28.5
    }
    (phase18_dir / "multi_agent_summary.json").write_text(json.dumps(summary))
    
    # coordination_patterns.json
    patterns = [
        {
            "pattern_type": "load_balanced",
            "agent_assignments": {"agent_0": ["task_0", "task_4"], "agent_1": ["task_1", "task_5"]},
            "success_rate": 0.95
        }
    ]
    (phase18_dir / "coordination_patterns.json").write_text(json.dumps(patterns))
    
    # system_health.json
    health = {
        "overall_health_score": 88.3,
        "health_status": "EXCELLENT"
    }
    (phase18_dir / "system_health.json").write_text(json.dumps(health))
    
    # learning_signals.jsonl
    signals = [
        {"signal_id": "LS_001", "type": "coordination_improvement", "confidence": 0.92, "description": "Load balancing effective"}
    ]
    (phase18_dir / "learning_signals.jsonl").write_text("\n".join(json.dumps(s) for s in signals))

    return phase18_dir


@pytest.fixture
def sample_tasks():
    """Create sample tasks for optimization."""
    return [
        {"task_id": "task_0", "risk_level": "LOW", "confidence": 0.85, "description": "Task 0"},
        {"task_id": "task_1", "risk_level": "MEDIUM", "confidence": 0.72, "description": "Task 1"},
        {"task_id": "task_2", "risk_level": "LOW", "confidence": 0.78, "description": "Task 2"},
        {"task_id": "task_3", "risk_level": "HIGH", "confidence": 0.65, "description": "Task 3"}
    ]


@pytest.fixture
def sample_agents():
    """Create sample agent list."""
    return ["agent_0", "agent_1", "agent_2", "agent_3"]


@pytest.fixture
def sample_optimization_result():
    """Create sample optimization result."""
    return {
        "strategy": "maximize_success",
        "expected_success_rate": 0.92,
        "expected_throughput": 40.0,
        "expected_confidence_delta": 0.05,
        "agent_assignments": {
            "agent_0": ["task_0", "task_2"],
            "agent_1": ["task_1"],
            "agent_2": ["task_3"]
        },
        "task_priorities": {
            "task_0": 1,
            "task_1": 2,
            "task_2": 3,
            "task_3": 4
        },
        "confidence": 0.88
    }


# =============================================================================
# TestAdaptiveOptimizer
# =============================================================================

class TestAdaptiveOptimizer:
    """Tests for AdaptiveOptimizer module."""
    
    def test_load_phase18_data(self, temp_dirs, sample_phase18_data):
        """Test loading Phase 18 multi-agent data."""
        optimizer = AdaptiveOptimizer(sample_phase18_data, temp_dirs["phase19"])
        counts = optimizer.load_phase18_data()
        assert counts["agents_loaded"] == 0
        assert counts["patterns_loaded"] == 1
        assert counts["signals_loaded"] == 1
        assert optimizer.multi_agent_summary["success_rate"] == 0.917
    
    def test_calculate_optimal_schedule_maximize_success(self, sample_tasks, sample_agents):
        """Test optimization for maximum success rate."""
        optimizer = AdaptiveOptimizer(Path("outputs/phase18"), Path("outputs/phase19"))
        result = optimizer.calculate_optimal_schedule(sample_tasks, sample_agents, OptimizationStrategy.MAXIMIZE_SUCCESS)
        assert result.expected_success_rate > 0.0
        assert len(result.agent_assignments) == len(sample_agents)
    
    def test_calculate_optimal_schedule_maximize_throughput(self, sample_tasks, sample_agents):
        """Test optimization for maximum throughput."""
        optimizer = AdaptiveOptimizer(Path("outputs/phase18"), Path("outputs/phase19"))
        result = optimizer.calculate_optimal_schedule(sample_tasks, sample_agents, OptimizationStrategy.MAXIMIZE_THROUGHPUT)
        loads = [len(v) for v in result.agent_assignments.values()]
        assert max(loads) - min(loads) <= 2
        assert result.expected_throughput > 0.0
    
    def test_optimize_for_confidence(self, sample_tasks, sample_agents):
        """Test confidence optimization strategy."""
        optimizer = AdaptiveOptimizer(Path("outputs/phase18"), Path("outputs/phase19"))
        assignments = optimizer.optimize_for_confidence(sample_tasks, sample_agents)
        total_assigned = sum(len(v) for v in assignments.values())
        assert total_assigned == len(sample_tasks)
    
    def test_simulate_schedule(self, sample_optimization_result):
        """Test schedule simulation."""
        optimizer = AdaptiveOptimizer(Path("outputs/phase18"), Path("outputs/phase19"))
        result = optimizer.calculate_optimal_schedule([], [], OptimizationStrategy.MAXIMIZE_SUCCESS)
        result.agent_assignments = sample_optimization_result["agent_assignments"]
        sim = optimizer.simulate_schedule(result)
        assert "simulated_success_rate" in sim
        assert "simulated_confidence_delta" in sim
    
    def test_update_confidence_estimates(self, sample_tasks):
        """Test confidence estimate updates."""
        optimizer = AdaptiveOptimizer(Path("outputs/phase18"), Path("outputs/phase19"))
        agent_perf = {"agent_0": 0.9}
        tasks = [dict(t, agent_id="agent_0") for t in sample_tasks]
        updated = optimizer.update_confidence_estimates(tasks, agent_perf)
        assert all(0.05 <= v <= 0.99 for v in updated.values())
    
    def test_generate_schedule_recommendations(self, sample_optimization_result):
        """Test schedule recommendation generation."""
        optimizer = AdaptiveOptimizer(Path("outputs/phase18"), Path("outputs/phase19"))
        result = optimizer.calculate_optimal_schedule([], [], OptimizationStrategy.MAXIMIZE_SUCCESS)
        result.agent_assignments = sample_optimization_result["agent_assignments"]
        recs = optimizer.generate_schedule_recommendations(1, result)
        assert recs
        assert all(r.rationale for r in recs)
    
    def test_write_optimization_outputs(self, temp_dirs):
        """Test writing optimization outputs to files."""
        optimizer = AdaptiveOptimizer(temp_dirs["phase18"], temp_dirs["phase19"])
        optimizer.optimization_results.append(
            optimizer.calculate_optimal_schedule([], [], OptimizationStrategy.MAXIMIZE_SUCCESS)
        )
        optimizer.write_optimization_outputs()
        assert (temp_dirs["phase19"] / "optimization_summary.json").exists()


# =============================================================================
# TestAdaptiveScheduler
# =============================================================================

class TestAdaptiveScheduler:
    """Tests for AdaptiveScheduler module."""
    
    def test_assign_tasks_to_agents(self, sample_tasks, sample_optimization_result):
        """Test task assignment from optimizer recommendations."""
        scheduler = AdaptiveScheduler(Path("outputs/phase19"), dry_run=True)
        scheduled = scheduler.assign_tasks_to_agents(sample_tasks, sample_optimization_result["agent_assignments"], 1)
        assert scheduled
        assert scheduler.agent_loads
    
    def test_prioritize_tasks_risk_confidence(self, sample_tasks):
        """Test task prioritization by risk and confidence."""
        scheduler = AdaptiveScheduler(Path("outputs/phase19"), dry_run=True)
        prioritized = scheduler.prioritize_tasks(sample_tasks)
        assert prioritized[0]["risk_level"] == "LOW"
    
    def test_adjust_for_agent_load(self):
        """Test dynamic load adjustment."""
        scheduler = AdaptiveScheduler(Path("outputs/phase19"), dry_run=True)
        scheduled = [
            scheduler.assign_tasks_to_agents(
                [{"task_id": "t1", "confidence": 0.8}],
                {"agent_0": ["t1"], "agent_1": []},
                1,
            )[0]
        ]
        adjusted = scheduler.adjust_for_agent_load(scheduled)
        assert adjusted
    
    def test_execute_schedule_dry_run(self, sample_tasks):
        """Test schedule execution in dry-run mode."""
        scheduler = AdaptiveScheduler(Path("outputs/phase19"), dry_run=True)
        scheduled = scheduler.assign_tasks_to_agents(sample_tasks, {"agent_0": ["task_0", "task_1"]}, 1)
        execution = scheduler.execute_schedule(1, scheduled)
        assert execution.actual_success_rate >= 0.0
    
    def test_simulate_task_execution(self):
        """Test task execution simulation."""
        scheduler = AdaptiveScheduler(Path("outputs/phase19"), dry_run=True)
        task = scheduler.assign_tasks_to_agents([
            {"task_id": "t1", "confidence": 0.8}
        ], {"agent_0": ["t1"]}, 1)[0]
        outcome = scheduler.simulate_task_execution(task)
        assert "success_probability" in outcome
    
    def test_calculate_schedule_adherence(self):
        """Test schedule adherence calculation."""
        scheduler = AdaptiveScheduler(Path("outputs/phase19"), dry_run=True)
        task = scheduler.assign_tasks_to_agents([
            {"task_id": "t1", "confidence": 0.8}
        ], {"agent_0": ["t1"]}, 1)[0]
        task.actual_start_time = task.scheduled_start_time
        task.actual_end_time = task.scheduled_end_time
        adherence = scheduler.calculate_schedule_adherence([task])
        assert 0.0 <= adherence <= 1.0
    
    def test_handle_task_failure_retry(self):
        """Test task failure handling with retry."""
        scheduler = AdaptiveScheduler(Path("outputs/phase19"), dry_run=True)
        task = scheduler.assign_tasks_to_agents([
            {"task_id": "t1", "confidence": 0.8}
        ], {"agent_0": ["t1"]}, 1)[0]
        task.status = ScheduleStatus.FAILED
        updated = scheduler.handle_task_failure(task)
        assert updated is not None
        assert updated.retry_count == 1
    
    def test_write_schedule_outputs(self, temp_dirs):
        """Test writing schedule outputs."""
        scheduler = AdaptiveScheduler(temp_dirs["phase19"], dry_run=True)
        scheduled = scheduler.assign_tasks_to_agents(
            [{"task_id": "t1", "confidence": 0.8}],
            {"agent_0": ["t1"]},
            1,
        )
        scheduler.execute_schedule(1, scheduled)
        scheduler.write_schedule_outputs(1)
        assert (temp_dirs["phase19"] / "wave_1" / "agent_0" / "scheduled_tasks.jsonl").exists()


# =============================================================================
# TestOptimizationFeedbackLoop
# =============================================================================

class TestOptimizationFeedbackLoop:
    """Tests for OptimizationFeedbackLoop module."""
    
    def test_evaluate_schedule_outcome(self):
        """Test schedule outcome evaluation."""
        feedback = OptimizationFeedbackLoop(Path("outputs/phase19"), Path("outputs/phase19"))
        comparison = feedback.evaluate_schedule_outcome(
            1,
            {"success_rate": 0.9, "throughput": 40.0, "confidence_delta": 0.05},
            {"success_rate": 0.88, "throughput": 38.0, "confidence_delta": 0.04},
        )
        assert comparison.accuracy_score > 0.0
    
    def test_generate_feedback_events(self):
        """Test feedback event generation."""
        feedback = OptimizationFeedbackLoop(Path("outputs/phase19"), Path("outputs/phase19"))
        feedback.evaluate_schedule_outcome(
            1,
            {"success_rate": 0.9, "throughput": 40.0, "confidence_delta": 0.05},
            {"success_rate": 0.7, "throughput": 30.0, "confidence_delta": 0.02},
        )
        count = feedback.generate_feedback_events()
        assert count >= 1
    
    def test_generate_learning_signals(self):
        """Test learning signal generation."""
        feedback = OptimizationFeedbackLoop(Path("outputs/phase19"), Path("outputs/phase19"))
        feedback.evaluate_schedule_outcome(
            1,
            {"success_rate": 0.9, "throughput": 40.0, "confidence_delta": 0.05},
            {"success_rate": 0.88, "throughput": 38.0, "confidence_delta": 0.04},
        )
        signals = feedback.generate_learning_signals()
        assert signals
    
    def test_update_heuristic_weights(self):
        """Test heuristic weight updates."""
        feedback = OptimizationFeedbackLoop(Path("outputs/phase19"), Path("outputs/phase19"))
        updated = feedback.update_heuristic_weights({"H16_001": 0.85, "H16_002": 0.6})
        assert updated["H16_001"] >= 1.0
        assert updated["H16_002"] <= 1.0
    
    def test_evaluate_strategy_effectiveness(self):
        """Test strategy effectiveness evaluation."""
        feedback = OptimizationFeedbackLoop(Path("outputs/phase19"), Path("outputs/phase19"))
        feedback.evaluate_schedule_outcome(
            1,
            {"success_rate": 0.9, "throughput": 40.0, "confidence_delta": 0.05},
            {"success_rate": 0.88, "throughput": 38.0, "confidence_delta": 0.04},
        )
        score = feedback.evaluate_strategy_effectiveness("maximize_success")
        assert 0.0 < score <= 1.0
    
    def test_write_feedback_outputs(self, temp_dirs):
        """Test writing feedback outputs."""
        feedback = OptimizationFeedbackLoop(temp_dirs["phase19"], temp_dirs["phase19"])
        feedback.evaluate_schedule_outcome(
            1,
            {"success_rate": 0.9, "throughput": 40.0, "confidence_delta": 0.05},
            {"success_rate": 0.88, "throughput": 38.0, "confidence_delta": 0.04},
        )
        feedback.generate_learning_signals()
        feedback.write_feedback_outputs()
        assert (temp_dirs["phase19"] / "schedule_comparisons.jsonl").exists()
        assert (temp_dirs["phase19"] / "optimization_feedback.jsonl").exists()


# =============================================================================
# TestOptimizationMonitor
# =============================================================================

class TestOptimizationMonitor:
    """Tests for OptimizationMonitor module."""
    
    def test_calculate_metrics(self):
        """Test real-time metric calculation."""
        output_dir = Path("outputs/phase19")
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "schedule_comparisons.jsonl").write_text(
            json.dumps({"accuracy_score": 0.95, "planned_throughput": 40.0, "actual_throughput": 38.0, "planned_confidence_delta": 0.05, "actual_confidence_delta": 0.04})
        )
        monitor = OptimizationMonitor(output_dir, output_dir)
        metrics = monitor.calculate_metrics()
        assert len(metrics) == 5
    
    def test_detect_anomalies_prediction_error(self):
        """Test detection of large prediction errors."""
        output_dir = Path("outputs/phase19")
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "schedule_comparisons.jsonl").write_text(
            json.dumps({"accuracy_score": 0.7, "planned_throughput": 40.0, "actual_throughput": 30.0, "planned_confidence_delta": 0.05, "actual_confidence_delta": 0.02})
        )
        monitor = OptimizationMonitor(output_dir, output_dir)
        monitor.calculate_metrics()
        anomalies = monitor.detect_anomalies()
        assert any(a.anomaly_type == "prediction_error" for a in anomalies)
    
    def test_detect_anomalies_schedule_drift(self):
        """Test detection of schedule drift."""
        output_dir = Path("outputs/phase19")
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "schedule_adherence.json").write_text(json.dumps({"schedule_adherence": 0.7}))
        monitor = OptimizationMonitor(output_dir, output_dir)
        monitor.calculate_metrics()
        anomalies = monitor.detect_anomalies()
        assert any(a.anomaly_type == "schedule_drift" for a in anomalies)
    
    def test_generate_system_health(self):
        """Test system health score generation."""
        output_dir = Path("outputs/phase19")
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "schedule_comparisons.jsonl").write_text(
            json.dumps({"accuracy_score": 0.95, "planned_throughput": 40.0, "actual_throughput": 38.0, "planned_confidence_delta": 0.05, "actual_confidence_delta": 0.04})
        )
        monitor = OptimizationMonitor(output_dir, output_dir)
        monitor.calculate_metrics()
        monitor.detect_anomalies()
        health = monitor.generate_system_health()
        assert 0.0 <= health["overall_health_score"] <= 100.0
    
    def test_write_monitoring_outputs(self, temp_dirs):
        """Test writing monitoring outputs."""
        output_dir = temp_dirs["phase19"]
        (output_dir / "schedule_comparisons.jsonl").write_text(
            json.dumps({"accuracy_score": 0.95, "planned_throughput": 40.0, "actual_throughput": 38.0, "planned_confidence_delta": 0.05, "actual_confidence_delta": 0.04})
        )
        monitor = OptimizationMonitor(output_dir, output_dir)
        monitor.calculate_metrics()
        monitor.detect_anomalies()
        monitor.write_monitoring_outputs()
        assert (output_dir / "metrics.jsonl").exists()
        assert (output_dir / "anomalies.jsonl").exists()


# =============================================================================
# TestPhase19Harness
# =============================================================================

class TestPhase19Harness:
    """Tests for Phase19Harness orchestration."""
    
    def test_harness_initialization(self, temp_dirs):
        """Test harness initialization."""
        harness = Phase19Harness(temp_dirs["phase18"], temp_dirs["phase19"], dry_run=True)
        assert harness.dry_run is True
        assert temp_dirs["phase19"].exists()
    
    def test_load_phase18_data(self, temp_dirs, sample_phase18_data):
        """Test loading Phase 18 data."""
        harness = Phase19Harness(temp_dirs["phase18"], temp_dirs["phase19"], dry_run=True)
        counts = harness._load_phase18_data()
        assert counts["patterns_loaded"] == 1
    
    def test_optimize_wave(self, sample_tasks, sample_agents):
        """Test single wave optimization."""
        harness = Phase19Harness(Path("outputs/phase18"), Path("outputs/phase19"), dry_run=True)
        harness._initialize_optimizer()
        result = harness._optimize_wave(1, sample_tasks, sample_agents)
        assert "optimization_result" in result
    
    def test_execute_wave_dry_run(self):
        """Test wave execution in dry-run mode."""
        harness = Phase19Harness(Path("outputs/phase18"), Path("outputs/phase19"), dry_run=True)
        outcome = harness._execute_wave(1, [])
        assert outcome["wave"] == 1
    
    def test_generate_feedback(self):
        """Test feedback generation."""
        harness = Phase19Harness(Path("outputs/phase18"), Path("outputs/phase19"), dry_run=True)
        harness.scheduler = AdaptiveScheduler(Path("outputs/phase19"), dry_run=True)
        counts = harness._generate_feedback()
        assert "learning_signals" in counts
    
    def test_monitor_optimization(self):
        """Test optimization monitoring."""
        output_dir = Path("outputs/phase19")
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "schedule_comparisons.jsonl").write_text(
            json.dumps({"accuracy_score": 0.95, "planned_throughput": 40.0, "actual_throughput": 38.0, "planned_confidence_delta": 0.05, "actual_confidence_delta": 0.04})
        )
        harness = Phase19Harness(Path("outputs/phase18"), output_dir, dry_run=True)
        metrics = harness._monitor_optimization()
        assert "health" in metrics
    
    def test_run_phase19_complete_pipeline(self, temp_dirs, sample_phase18_data):
        """Test complete Phase 19 pipeline execution."""
        harness = Phase19Harness(temp_dirs["phase18"], temp_dirs["phase19"], dry_run=True)
        summary = harness.run_phase19(waves=1, agents=2)
        assert summary["waves_optimized"] == 1
        assert (temp_dirs["phase19"] / "phase19_summary.json").exists()
    
    def test_output_files_generated(self, temp_dirs):
        """Test all output files are generated."""
        harness = Phase19Harness(temp_dirs["phase18"], temp_dirs["phase19"], dry_run=True)
        harness.run_phase19(waves=1, agents=2)
        assert (temp_dirs["phase19"] / "optimization_summary.json").exists()
        assert (temp_dirs["phase19"] / "system_health.json").exists()
        assert (temp_dirs["phase19"] / "learning_signals.jsonl").exists()


# =============================================================================
# Integration Tests
# =============================================================================

class TestPhase19Integration:
    """Integration tests for Phase 19 pipeline."""
    
    def test_end_to_end_optimization(self, temp_dirs, sample_phase18_data, sample_tasks):
        """Test end-to-end optimization pipeline."""
        harness = Phase19Harness(temp_dirs["phase18"], temp_dirs["phase19"], dry_run=True)
        summary = harness.run_phase19(waves=1, agents=2)
        assert summary["waves_optimized"] == 1
    
    def test_feedback_loop_integration(self):
        """Test feedback loop integration with Phase 16/18."""
        feedback = OptimizationFeedbackLoop(Path("outputs/phase19"), Path("outputs/phase19"))
        feedback.update_heuristic_weights({"H16_001": 0.85})
        feedback.update_phase16_heuristics()
        feedback.update_phase18_coordination()
        assert Path("outputs/phase16/phase19_feedback.jsonl").exists()
        assert Path("outputs/phase18/phase19_feedback.jsonl").exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
