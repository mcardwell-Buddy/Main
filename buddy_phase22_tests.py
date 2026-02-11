"""
Phase 22: Meta-Optimization & Autonomous Tuning - Test Suite

Coverage:
    - Meta optimizer strategies and outputs
    - Agent tuner adjustments and outputs
    - Adaptive scheduler behavior
    - Feedback loop generation and routing
    - Monitoring metrics, anomalies, and health
    - Harness integration and dry-run execution

Total: 32 tests
"""

import json
import tempfile
from pathlib import Path

import pytest

from buddy_phase22_meta_optimizer import (
    Phase22MetaOptimizer,
    OptimizationStrategy,
)
from buddy_phase22_agent_tuner import Phase22AgentTuner
from buddy_phase22_scheduler import Phase22AdaptiveScheduler
from buddy_phase22_feedback_loop import Phase22FeedbackLoop
from buddy_phase22_monitor import Phase22Monitor
from buddy_phase22_harness import Phase22Harness


@pytest.fixture
def temp_dirs():
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        phase20 = base / "phase20"
        phase21 = base / "phase21"
        phase16 = base / "phase16"
        phase18 = base / "phase18"
        phase22 = base / "phase22"
        for path in [phase20, phase21, phase16, phase18, phase22]:
            path.mkdir(parents=True, exist_ok=True)
        yield {
            "base": base,
            "phase20": phase20,
            "phase21": phase21,
            "phase16": phase16,
            "phase18": phase18,
            "phase22": phase22,
        }


def test_meta_optimizer_strategy_success(temp_dirs):
    optimizer = Phase22MetaOptimizer(temp_dirs["phase22"], dry_run=True)
    metrics = {"success_rate": 0.85, "throughput": 50, "load_balance": 1.0, "retry_rate": 0.0, "confidence_trajectory": 0.96}
    recommendation = optimizer.optimize_wave(1, metrics)
    assert recommendation.strategy == OptimizationStrategy.MAXIMIZE_SUCCESS


def test_meta_optimizer_strategy_throughput(temp_dirs):
    optimizer = Phase22MetaOptimizer(temp_dirs["phase22"], dry_run=True)
    metrics = {"success_rate": 0.95, "throughput": 10, "load_balance": 1.0, "retry_rate": 0.0, "confidence_trajectory": 0.96}
    recommendation = optimizer.optimize_wave(1, metrics)
    assert recommendation.strategy == OptimizationStrategy.MAXIMIZE_THROUGHPUT


def test_meta_optimizer_strategy_balance(temp_dirs):
    optimizer = Phase22MetaOptimizer(temp_dirs["phase22"], dry_run=True)
    metrics = {"success_rate": 0.95, "throughput": 50, "load_balance": 0.7, "retry_rate": 0.0, "confidence_trajectory": 0.96}
    recommendation = optimizer.optimize_wave(1, metrics)
    assert recommendation.strategy == OptimizationStrategy.BALANCE_LOAD


def test_meta_optimizer_strategy_retries(temp_dirs):
    optimizer = Phase22MetaOptimizer(temp_dirs["phase22"], dry_run=True)
    metrics = {"success_rate": 0.95, "throughput": 50, "load_balance": 1.0, "retry_rate": 0.2, "confidence_trajectory": 0.96}
    recommendation = optimizer.optimize_wave(1, metrics)
    assert recommendation.strategy == OptimizationStrategy.MINIMIZE_RETRIES


def test_meta_optimizer_strategy_confidence(temp_dirs):
    optimizer = Phase22MetaOptimizer(temp_dirs["phase22"], dry_run=True)
    metrics = {"success_rate": 0.95, "throughput": 50, "load_balance": 1.0, "retry_rate": 0.0, "confidence_trajectory": 0.9}
    recommendation = optimizer.optimize_wave(1, metrics)
    assert recommendation.strategy == OptimizationStrategy.MAXIMIZE_CONFIDENCE


def test_meta_optimizer_recommendation_fields(temp_dirs):
    optimizer = Phase22MetaOptimizer(temp_dirs["phase22"], dry_run=True)
    metrics = {"success_rate": 0.85, "throughput": 50, "load_balance": 1.0, "retry_rate": 0.0, "confidence_trajectory": 0.96}
    recommendation = optimizer.optimize_wave(1, metrics)
    assert recommendation.adjustments
    assert recommendation.expected_impact
    assert recommendation.confidence >= 0.7


def test_meta_optimizer_phase16_adjustments(temp_dirs):
    optimizer = Phase22MetaOptimizer(temp_dirs["phase22"], dry_run=True)
    metrics = {"success_rate": 0.85, "throughput": 50, "load_balance": 1.0, "retry_rate": 0.0, "confidence_trajectory": 0.96}
    recommendation = optimizer.optimize_wave(1, metrics)
    adjustments = optimizer.suggest_phase16_adjustments(recommendation)
    assert adjustments
    assert adjustments[0]["strategy"] == recommendation.strategy.value


def test_meta_optimizer_reinforcement_weights(temp_dirs):
    optimizer = Phase22MetaOptimizer(temp_dirs["phase22"], dry_run=True)
    weights = optimizer.apply_reinforcement_signals(
        {"confidence": 0.95},
        {"failure_rate": 0.05, "throughput": 40, "load_imbalance": 0.1, "retry_rate": 0.05}
    )
    assert weights[OptimizationStrategy.MAXIMIZE_SUCCESS.value] > 0.9
    assert weights[OptimizationStrategy.MAXIMIZE_THROUGHPUT.value] >= 1.0


def test_meta_optimizer_write_dry_run(temp_dirs):
    optimizer = Phase22MetaOptimizer(temp_dirs["phase22"], dry_run=True)
    optimizer.optimize_wave(1, {"success_rate": 0.92, "throughput": 40, "load_balance": 0.9, "retry_rate": 0.01, "confidence_trajectory": 0.96})
    result = optimizer.write_recommendations()
    assert result is not None
    assert Path(result).exists()


def test_agent_tuner_initialize(temp_dirs):
    tuner = Phase22AgentTuner(temp_dirs["phase22"], dry_run=True)
    tuner.initialize_agents(["agent_0", "agent_1"])
    assert "agent_0" in tuner.agent_parameters


def test_agent_tuner_tune_low_success(temp_dirs):
    tuner = Phase22AgentTuner(temp_dirs["phase22"], dry_run=True)
    tuner.initialize_agents(["agent_0"])
    results = tuner.tune_agents(1, {"agent_0": {"success_rate": 0.8}})
    assert results[0].after.retry_threshold >= results[0].before.retry_threshold


def test_agent_tuner_tune_low_throughput(temp_dirs):
    tuner = Phase22AgentTuner(temp_dirs["phase22"], dry_run=True)
    tuner.initialize_agents(["agent_0"])
    results = tuner.tune_agents(1, {"agent_0": {"throughput": 10.0}})
    assert results[0].after.speed_multiplier >= results[0].before.speed_multiplier


def test_agent_tuner_tune_low_confidence(temp_dirs):
    tuner = Phase22AgentTuner(temp_dirs["phase22"], dry_run=True)
    tuner.initialize_agents(["agent_0"])
    results = tuner.tune_agents(1, {"agent_0": {"confidence": 0.9}})
    assert results[0].after.confidence_weight >= results[0].before.confidence_weight


def test_agent_tuner_tune_low_utilization(temp_dirs):
    tuner = Phase22AgentTuner(temp_dirs["phase22"], dry_run=True)
    tuner.initialize_agents(["agent_0"])
    results = tuner.tune_agents(1, {"agent_0": {"utilization": 0.5}})
    assert results[0].after.max_parallel_tasks >= results[0].before.max_parallel_tasks


def test_agent_tuner_write_outputs(temp_dirs):
    tuner = Phase22AgentTuner(temp_dirs["phase22"], dry_run=False)
    tuner.initialize_agents(["agent_0"])
    tuner.tune_agents(1, {"agent_0": {"success_rate": 0.8}})
    outputs = tuner.write_tuning_outputs(1)
    assert outputs["agent_0"] is not None
    assert Path(outputs["agent_0"]).exists()


def test_scheduler_initial_schedule(temp_dirs):
    scheduler = Phase22AdaptiveScheduler(temp_dirs["phase22"], dry_run=True)
    tasks = [
        {"task_id": "task_1", "priority": 1, "predicted_success": 0.9},
        {"task_id": "task_2", "priority": 2, "predicted_success": 0.9},
    ]
    assignments = scheduler.generate_initial_schedule(tasks, ["agent_0", "agent_1"], 1)
    assert len(assignments["agent_0"]) + len(assignments["agent_1"]) == 2


def test_scheduler_rebalance_schedule(temp_dirs):
    scheduler = Phase22AdaptiveScheduler(temp_dirs["phase22"], dry_run=True)
    tasks = [{"task_id": f"task_{i}", "priority": 1, "predicted_success": 0.9} for i in range(5)]
    assignments = scheduler.generate_initial_schedule(tasks, ["agent_0", "agent_1"], 1)
    assignments["agent_0"].append(assignments["agent_1"].pop())
    rebalanced = scheduler.rebalance_schedule(assignments, {})
    assert sum(len(v) for v in rebalanced.values()) == 5


def test_scheduler_failover(temp_dirs):
    scheduler = Phase22AdaptiveScheduler(temp_dirs["phase22"], dry_run=True)
    tasks = [{"task_id": "task_1", "priority": 1, "predicted_success": 0.9}]
    assignments = scheduler.generate_initial_schedule(tasks, ["agent_0", "agent_1"], 1)
    failed = assignments["agent_0"]
    updated = scheduler.apply_failover(failed, assignments)
    assert sum(len(v) for v in updated.values()) >= 1


def test_scheduler_write_adjusted_schedule(temp_dirs):
    scheduler = Phase22AdaptiveScheduler(temp_dirs["phase22"], dry_run=False)
    tasks = [{"task_id": "task_1", "priority": 1, "predicted_success": 0.9}]
    assignments = scheduler.generate_initial_schedule(tasks, ["agent_0"], 1)
    outputs = scheduler.write_adjusted_schedule(1, assignments)
    assert outputs["agent_0"] is not None
    assert Path(outputs["agent_0"]).exists()


def test_feedback_generate_signals(temp_dirs):
    feedback = Phase22FeedbackLoop(
        temp_dirs["phase16"], temp_dirs["phase18"], temp_dirs["phase20"], temp_dirs["phase22"], dry_run=True
    )
    signals = feedback.generate_feedback_signals(
        wave=1,
        metrics={"system_health": 0.95, "load_balance": 0.9, "agent_utilization": 0.8, "schedule_adherence": 0.97, "confidence_trajectory": 0.96, "success_rate": 0.92},
        anomalies=[],
        tuning_results=[],
        optimization_result={"strategy": "balance_load", "adjustments": {"rebalance_threshold": 0.1}},
    )
    assert len(signals) == 3
    assert signals[0].target_phase == 16


def test_feedback_write_outputs_dry_run(temp_dirs):
    feedback = Phase22FeedbackLoop(
        temp_dirs["phase16"], temp_dirs["phase18"], temp_dirs["phase20"], temp_dirs["phase22"], dry_run=True
    )
    feedback.generate_feedback_signals(
        wave=1,
        metrics={"system_health": 0.95, "load_balance": 0.9, "agent_utilization": 0.8, "schedule_adherence": 0.97, "confidence_trajectory": 0.96, "success_rate": 0.92},
        anomalies=[],
        tuning_results=[],
        optimization_result={"strategy": "balance_load", "adjustments": {"rebalance_threshold": 0.1}},
    )
    outputs = feedback.write_feedback_outputs()
    assert outputs["learning_signals"] is not None
    assert Path(outputs["learning_signals"]).exists()
    assert outputs["phase16_feedback"] is None


def test_feedback_write_outputs_real(temp_dirs):
    feedback = Phase22FeedbackLoop(
        temp_dirs["phase16"], temp_dirs["phase18"], temp_dirs["phase20"], temp_dirs["phase22"], dry_run=False
    )
    feedback.generate_feedback_signals(
        wave=1,
        metrics={"system_health": 0.95, "load_balance": 0.9, "agent_utilization": 0.8, "schedule_adherence": 0.97, "confidence_trajectory": 0.96, "success_rate": 0.92},
        anomalies=[],
        tuning_results=[],
        optimization_result={"strategy": "balance_load", "adjustments": {"rebalance_threshold": 0.1}},
    )
    outputs = feedback.write_feedback_outputs()
    assert outputs["learning_signals"] is not None
    assert Path(outputs["learning_signals"]).exists()


def test_monitor_calculate_metrics(temp_dirs):
    monitor = Phase22Monitor(temp_dirs["phase22"], dry_run=True)
    metrics = monitor.calculate_metrics(
        wave=1,
        execution_summary={"success_rate": 0.92, "throughput": 40, "agent_utilization": 0.8, "confidence_trajectory": 0.96},
        tuning_summary={},
        schedule_summary={"schedule_adherence": 0.96},
        optimization_summary={"learning_impact": 0.95, "optimization_efficiency": 0.92},
    )
    assert any(m.metric_name == "success_rate" for m in metrics)


def test_monitor_detect_anomalies(temp_dirs):
    monitor = Phase22Monitor(temp_dirs["phase22"], dry_run=True)
    metrics = monitor.calculate_metrics(
        wave=1,
        execution_summary={"success_rate": 0.80, "throughput": 20, "agent_utilization": 0.6, "confidence_trajectory": 0.90},
        tuning_summary={},
        schedule_summary={"schedule_adherence": 0.90},
        optimization_summary={"learning_impact": 0.85, "optimization_efficiency": 0.80},
    )
    anomalies = monitor.detect_anomalies(1, metrics)
    assert anomalies


def test_monitor_generate_system_health(temp_dirs):
    monitor = Phase22Monitor(temp_dirs["phase22"], dry_run=True)
    metrics = monitor.calculate_metrics(
        wave=1,
        execution_summary={"success_rate": 0.92, "throughput": 40, "agent_utilization": 0.8, "confidence_trajectory": 0.96},
        tuning_summary={},
        schedule_summary={"schedule_adherence": 0.96},
        optimization_summary={"learning_impact": 0.95, "optimization_efficiency": 0.92},
    )
    anomalies = monitor.detect_anomalies(1, metrics)
    health = monitor.generate_system_health(1, metrics, anomalies)
    assert health.overall_health_score >= 0


def test_monitor_write_outputs(temp_dirs):
    monitor = Phase22Monitor(temp_dirs["phase22"], dry_run=False)
    metrics = monitor.calculate_metrics(
        wave=1,
        execution_summary={"success_rate": 0.92, "throughput": 40, "agent_utilization": 0.8, "confidence_trajectory": 0.96},
        tuning_summary={},
        schedule_summary={"schedule_adherence": 0.96},
        optimization_summary={"learning_impact": 0.95, "optimization_efficiency": 0.92},
    )
    anomalies = monitor.detect_anomalies(1, metrics)
    monitor.generate_system_health(1, metrics, anomalies)
    outputs = monitor.write_monitoring_outputs()
    assert outputs["metrics"] is not None


def test_harness_load_inputs_empty(temp_dirs):
    harness = Phase22Harness(
        temp_dirs["phase20"], temp_dirs["phase21"], temp_dirs["phase16"], temp_dirs["phase18"], temp_dirs["phase22"], dry_run=True
    )
    inputs = harness.load_inputs()
    assert "phase20_metrics" in inputs


def test_harness_run_phase22_dry_run(temp_dirs):
    harness = Phase22Harness(
        temp_dirs["phase20"], temp_dirs["phase21"], temp_dirs["phase16"], temp_dirs["phase18"], temp_dirs["phase22"], dry_run=True
    )
    result = harness.run_phase22([1], tasks_per_wave=5)
    assert result.total_tasks == 5
    assert result.waves_executed == 1


def test_harness_wave_metrics_success(temp_dirs):
    harness = Phase22Harness(
        temp_dirs["phase20"], temp_dirs["phase21"], temp_dirs["phase16"], temp_dirs["phase18"], temp_dirs["phase22"], dry_run=True
    )
    harness.load_inputs()
    result = harness.run_phase22([1], tasks_per_wave=5)
    assert result.success_rate >= 0.8


def test_harness_deterministic_success(temp_dirs):
    harness = Phase22Harness(
        temp_dirs["phase20"], temp_dirs["phase21"], temp_dirs["phase16"], temp_dirs["phase18"], temp_dirs["phase22"], dry_run=True
    )
    success_a = harness._deterministic_success("task_A", 0.9)
    success_b = harness._deterministic_success("task_A", 0.9)
    assert success_a == success_b


def test_harness_outputs_on_write(temp_dirs):
    harness = Phase22Harness(
        temp_dirs["phase20"], temp_dirs["phase21"], temp_dirs["phase16"], temp_dirs["phase18"], temp_dirs["phase22"], dry_run=False
    )
    result = harness.run_phase22([1], tasks_per_wave=3)
    summary_path = temp_dirs["phase22"] / "phase22_summary.json"
    assert summary_path.exists()
    assert result.waves_executed == 1


def test_monitor_health_status_threshold(temp_dirs):
    monitor = Phase22Monitor(temp_dirs["phase22"], dry_run=True)
    metrics = monitor.calculate_metrics(
        wave=1,
        execution_summary={"success_rate": 0.99, "throughput": 60, "agent_utilization": 0.9, "confidence_trajectory": 0.98},
        tuning_summary={},
        schedule_summary={"schedule_adherence": 0.98},
        optimization_summary={"learning_impact": 0.97, "optimization_efficiency": 0.96},
    )
    anomalies = monitor.detect_anomalies(1, metrics)
    health = monitor.generate_system_health(1, metrics, anomalies)
    assert health.health_status == "EXCELLENT"

