# Phase 20: Predictive Task Assignment - Implementation Guide

## Overview

Phase 20 implements **Predictive Task Assignment**, a system that leverages Phase 19 optimization outputs to:
- Predict task success probability for upcoming waves
- Assign tasks optimally across agents
- Generate feedback signals for continuous learning
- Monitor system health and detect anomalies
- Orchestrate the complete pipeline

## Architecture

```
Phase 19 Outputs (metrics, anomalies, signals, scheduled_tasks)
              ↓
    ┌─────────────────────┐
    │ AdaptivePredictor   │  ← Predict task outcomes (5 strategies)
    └─────────────────────┘
              ↓
    ┌─────────────────────┐
    │ PredictiveScheduler │  ← Assign tasks optimally (greedy algorithm)
    └─────────────────────┘
              ↓
    ┌──────────────────────┐
    │ Schedule Execution   │  ← Simulate execution
    └──────────────────────┘
              ↓
    ┌─────────────────────────┐
    │ PredictionFeedbackLoop  │  ← Generate learning signals
    └─────────────────────────┘
              ↓
    ┌──────────────────────┐
    │ PredictionMonitor    │  ← Track metrics, detect anomalies
    └──────────────────────┘
              ↓
    ┌─────────────────────────────┐
    │ Phase20Harness (Orchestrate)│  ← Coordinate all components
    └─────────────────────────────┘
              ↓
    Phase 20 Outputs + Reports + Feedback to Phase 16/18
```

## Core Modules

### 1. AdaptivePredictor (320 LOC)
**File:** `buddy_phase20_predictor.py`

**Purpose:** Predict task success probability using Phase 19 data and 5 prediction strategies.

**Key Classes:**
- `PredictionStrategy` (Enum): CONFIDENCE_BASED, HISTORICAL_PERFORMANCE, ENSEMBLE, CONSERVATIVE, OPTIMISTIC
- `TaskPrediction` (Dataclass): Prediction result with success probability, risk assessment, confidence delta
- `PredictionModel` (Dataclass): Trained model state with accuracy, weights, versioning
- `AdaptivePredictor` (Class): Main predictor engine

**Core Methods:**
- `load_phase19_data()` - Load metrics, anomalies, signals, scheduled_tasks from Phase 19
- `train_predictor(strategy)` - Train model with specified strategy
- `predict_task_outcomes(tasks, agents, wave)` - Generate predictions for all task-agent pairs
- `update_model(actual_outcomes)` - Update model based on actual results
- `generate_prediction_metrics()` - Generate accuracy and confidence metrics
- `write_prediction_outputs(wave)` - Write predicted_tasks.jsonl per agent

**Prediction Formula:**
```
predicted_success = base_probability + risk_penalty + complexity_penalty

where:
  base_probability = agent_success_rate (from Phase 19)
  risk_penalty = LOW:0, MEDIUM:-0.05, HIGH:-0.15
  complexity_penalty = -(1 - confidence) * 0.1
  result = clamp(result, 0.1, 0.99)
```

**5 Prediction Strategies:**
1. **CONFIDENCE_BASED** - Uses agent confidence levels from Phase 19
2. **HISTORICAL_PERFORMANCE** - Based on historical success rates
3. **ENSEMBLE** - Combines multiple strategies (DEFAULT)
4. **CONSERVATIVE** - Reduces predictions by 10% for safety
5. **OPTIMISTIC** - Increases predictions by 10% for throughput

### 2. PredictiveScheduler (245 LOC)
**File:** `buddy_phase20_scheduler.py`

**Purpose:** Assign tasks to agents optimally based on predictions.

**Key Classes:**
- `PredictedTaskAssignment` (Dataclass): Assignment with timing, success probability, priority
- `PredictedScheduleExecution` (Dataclass): Schedule execution result with metrics
- `PredictiveScheduler` (Class): Task assignment engine

**Core Methods:**
- `assign_tasks(predictions, agents, wave)` - Greedy assignment algorithm
- `balance_load()` - Rebalance if imbalance > 30%
- `adjust_confidence(confidence_adjustments)` - Update confidence estimates
- `execute_predicted_schedule()` - Simulate schedule execution
- `write_schedule_outputs(wave)` - Write predicted_schedule.jsonl per agent

**Assignment Algorithm:**
```
For each task:
  1. Calculate score for each agent: success_prob - (load × 0.1)
  2. Assign to highest-scoring agent
  3. Update agent load

Load Balancing:
  If (max_load - min_load) > max_load × 0.30:
    Reassign lowest-priority tasks to least-loaded agents
```

**Output Metrics:**
- predicted_success_rate - Tasks ≥0.75 probability / total
- predicted_throughput - Tasks completed / execution time
- predicted_avg_confidence_delta - Average confidence improvement
- load_balance - Distribution fairness score

### 3. PredictionFeedbackLoop (280 LOC)
**File:** `buddy_phase20_feedback_loop.py`

**Purpose:** Generate learning signals for Phase 16 (heuristics) and Phase 18 (coordination).

**Key Classes:**
- `PredictionComparison` (Dataclass): Prediction vs actual outcome comparison
- `LearningSignal` (Dataclass): Feedback signal with type, confidence, recommendation
- `PredictionFeedbackLoop` (Class): Feedback generation engine

**Core Methods:**
- `evaluate_predictions(predicted, actual)` - Compare predictions to actual outcomes
- `generate_feedback_events()` - Identify prediction errors and anomalies
- `generate_learning_signals()` - Generate 3 types of signals
- `write_feedback_outputs()` - Write feedback to Phase 16/18 directories

**3 Learning Signal Types:**
1. **P20_LS_MODEL_VALIDATION** (type: prediction_model_validation)
   - Confidence = prediction_accuracy
   - Triggered when accuracy ≥ 0.75
   - Target: Phase 20 feedback loop

2. **P20_LS_HEURISTIC_EFFECTIVENESS** (type: heuristic_effectiveness)
   - Confidence = avg_confidence_delta
   - Triggered when confidence_delta > 0.01
   - Target: Phase 16 heuristic refinement

3. **P20_LS_COORDINATION_INSIGHT** (type: multi_agent_coordination)
   - Identifies best-performing agent patterns
   - Target: Phase 18 multi-agent optimization

### 4. PredictionMonitor (310 LOC)
**File:** `buddy_phase20_monitor.py`

**Purpose:** Track 5 core metrics and detect 4 anomaly types.

**Key Classes:**
- `PredictionMetric` (Dataclass): Metric value with thresholds and status
- `PredictionAnomaly` (Dataclass): Detected anomaly with severity and recommendation
- `PredictionMonitor` (Class): Monitoring engine

**Core Methods:**
- `calculate_metrics(predictions, actual_outcomes)` - Calculate 5 core metrics
- `detect_anomalies()` - Detect 4 anomaly types
- `generate_system_health()` - Calculate 0-100 health score
- `write_monitoring_outputs()` - Write metrics.jsonl, anomalies.jsonl, system_health.json

**5 Core Metrics:**
1. **prediction_accuracy** - Correct predictions / total (target: 0.85)
2. **schedule_adherence** - Adherence to predicted timing (target: 0.90)
3. **load_balance_efficiency** - Even distribution across agents (target: 0.85)
4. **confidence_improvement** - Avg confidence delta (target: 0.03)
5. **model_reliability** - Prediction consistency (target: 0.80)

**4 Anomaly Types:**
1. **prediction_drift** - Accuracy drops below 0.60
2. **model_degradation** - Reliability drops below 0.70
3. **assignment_failure** - Load imbalance > 30%
4. **throughput_loss** - Confidence improvement < 0.005

**Health Score Calculation:**
```
health = (accuracy × 0.40) + (adherence × 0.25) + (balance × 0.20) + (reliability × 0.15)
health_scaled = health × 100, clamped to [0, 100]

Status:
  EXCELLENT: ≥ 85
  GOOD: 70-84
  FAIR: 55-69
  POOR: < 55
```

### 5. Phase20Harness (380 LOC)
**File:** `buddy_phase20_harness.py`

**Purpose:** Orchestrate complete Phase 20 pipeline.

**Key Classes:**
- `Phase20ExecutionReport` (Dataclass): Execution summary and metrics
- `Phase20Harness` (Class): Orchestration engine

**Core Methods:**
- `run_phase20(waves, agents)` - Execute complete pipeline
- `_generate_sample_tasks(wave)` - Sample task generation
- `_generate_sample_outcomes(assignments)` - Sample outcome generation
- `_generate_execution_report()` - Create execution summary
- `_write_execution_report()` - Write PHASE_20_AUTONOMOUS_EXECUTION.md

**Pipeline Steps:**
1. Load Phase 19 data (metrics, anomalies, signals, scheduled_tasks)
2. Initialize and train predictor
3. Predict task outcomes for each wave
4. Schedule tasks optimally
5. Execute scheduled tasks
6. Generate feedback signals
7. Monitor system health
8. Generate execution report

## Input/Output Structure

### Inputs (From Phase 19)

**Directory Structure:**
```
phase19/
  ├── metrics.jsonl          # 5 core metrics per agent/wave
  ├── anomalies.jsonl        # Detected anomalies
  ├── learning_signals.jsonl # Learning signals from optimization
  └── scheduled_tasks.jsonl  # Tasks scheduled by Phase 19
```

**File Format:** JSONL (one JSON object per line)

### Outputs (Phase 20)

**Directory Structure:**
```
phase20/
  ├── metrics.jsonl                      # Prediction metrics
  ├── anomalies.jsonl                    # Detected anomalies
  ├── system_health.json                 # Overall health score
  ├── learning_signals.jsonl             # Generated learning signals
  ├── PHASE_20_AUTONOMOUS_EXECUTION.md   # Execution report
  └── wave_X/
      ├── agent_Y/
      │   ├── predicted_tasks.jsonl      # Task predictions
      │   └── predicted_schedule.jsonl   # Task assignments
      ...
```

**Feedback Outputs:**

- **Phase 16 Feedback:** `phase16/phase20_feedback.jsonl`
  - Heuristic effectiveness signals from Phase 20
  
- **Phase 18 Feedback:** `phase18/phase20_feedback.jsonl`
  - Multi-agent coordination insights from Phase 20

## Testing

**Test Suite:** `buddy_phase20_tests.py`

**Coverage:**
- 7 unit tests for AdaptivePredictor
- 7 unit tests for PredictiveScheduler
- 6 unit tests for PredictionFeedbackLoop
- 5 unit tests for PredictionMonitor
- 5 unit tests for Phase20Harness
- 9 integration tests for end-to-end pipeline

**Total: 39 tests (24 unit + 15 integration)**

**Running Tests:**
```bash
# Run all tests
pytest buddy_phase20_tests.py -v

# Run specific test class
pytest buddy_phase20_tests.py::TestAdaptivePredictor -v

# Run with coverage
pytest buddy_phase20_tests.py --cov=buddy_phase20 -v
```

## Configuration & Usage

### Basic Usage

```python
from buddy_phase20_harness import Phase20Harness

# Initialize harness
harness = Phase20Harness(
    phase19_input_dir="./phase19",
    phase16_dir="./phase16",
    phase18_dir="./phase18",
    phase20_output_dir="./phase20",
    dry_run=True  # Set to False for actual execution
)

# Run Phase 20 pipeline
result = harness.run_phase20(
    waves=[1, 2, 3],
    agents=["agent_0", "agent_1", "agent_2", "agent_3"]
)

# Check results
print(f"Status: {result['status']}")
print(f"Predictions: {result['total_predictions']}")
print(f"Health Score: {result['system_health_score']}/100")
```

### Using Individual Components

```python
from buddy_phase20_predictor import AdaptivePredictor, PredictionStrategy
from buddy_phase20_scheduler import PredictiveScheduler
from buddy_phase20_feedback_loop import PredictionFeedbackLoop
from buddy_phase20_monitor import PredictionMonitor

# 1. Predict
predictor = AdaptivePredictor("./phase19", "./phase20", dry_run=True)
predictor.load_phase19_data()
predictor.train_predictor(PredictionStrategy.ENSEMBLE)
predictions = predictor.predict_task_outcomes(tasks, agents, wave=1)

# 2. Schedule
scheduler = PredictiveScheduler("./phase20", dry_run=True)
assignments = scheduler.assign_tasks(predictions, agents, wave=1)
scheduler.balance_load()
execution = scheduler.execute_predicted_schedule()

# 3. Feedback
feedback = PredictionFeedbackLoop("./phase16", "./phase18", "./phase20", dry_run=True)
feedback.evaluate_predictions(predicted_outcomes, actual_outcomes)
signals = feedback.generate_learning_signals()
feedback.write_feedback_outputs()

# 4. Monitor
monitor = PredictionMonitor("./phase20", dry_run=True)
metrics = monitor.calculate_metrics(predictions, actual_outcomes)
anomalies = monitor.detect_anomalies()
health = monitor.generate_system_health()
```

## Integration with Phase 16 & Phase 18

### Phase 16 Integration (Heuristic Feedback)
- **Input:** Phase 20 prediction signals for heuristic effectiveness
- **Signal Type:** heuristic_effectiveness
- **Use Case:** Refine heuristics based on prediction confidence trajectory
- **File:** `phase16/phase20_feedback.jsonl`

### Phase 18 Integration (Multi-Agent Coordination)
- **Input:** Phase 20 coordination insights from multi-agent performance
- **Signal Type:** multi_agent_coordination
- **Use Case:** Optimize agent selection and load distribution
- **File:** `phase18/phase20_feedback.jsonl`

## Safety & Dry-Run Mode

All modules support **dry-run mode** for safe testing:

```python
# Dry-run mode (no side effects, no file writes)
predictor = AdaptivePredictor("./phase19", "./phase20", dry_run=True)

# Production mode (full execution)
predictor = AdaptivePredictor("./phase19", "./phase20", dry_run=False)
```

## Performance Characteristics

| Metric | Target | Typical |
|--------|--------|---------|
| Prediction Accuracy | ≥ 85% | 75-90% |
| Schedule Adherence | ≥ 90% | 80-95% |
| Load Balance | ≥ 85% | 75-90% |
| Confidence Improvement | > 0.03 | 0.01-0.05 |
| System Health | ≥ 85/100 | 70-90/100 |

## Troubleshooting

### Low Prediction Accuracy
- **Cause:** Insufficient Phase 19 data or changing task patterns
- **Solution:** Increase training data window, switch to ENSEMBLE strategy, retrain model

### Unbalanced Load
- **Cause:** Task distribution mismatch or agent capability variance
- **Solution:** Reduce load balance threshold, adjust agent_load_factor in scheduler

### Degrading Model Reliability
- **Cause:** Drift in task patterns or agent performance
- **Solution:** Retrain predictor with recent data, update feature weights

### High Anomaly Rate
- **Cause:** System instability or changing conditions
- **Solution:** Review anomaly details, adjust detection thresholds, investigate root cause

## File Descriptions

| File | Lines | Purpose |
|------|-------|---------|
| buddy_phase20_predictor.py | 320 | Task outcome prediction using 5 strategies |
| buddy_phase20_scheduler.py | 245 | Optimal task assignment with load balancing |
| buddy_phase20_feedback_loop.py | 280 | Learning signal generation for Phase 16/18 |
| buddy_phase20_monitor.py | 310 | System health monitoring and anomaly detection |
| buddy_phase20_harness.py | 380 | Pipeline orchestration and reporting |
| buddy_phase20_tests.py | 900+ | 39 comprehensive tests (24 unit + 15 integration) |

**Total Implementation:** ~2,435 LOC

## Next Steps

1. **Execute Phase 20 pipeline** with real Phase 19 data
2. **Monitor system health** and review anomalies
3. **Validate learning signals** to Phase 16/18
4. **Iterate prediction strategies** based on accuracy metrics
5. **Prepare for Phase 21** (autonomous agent orchestration)

## References

- **Phase 19:** Optimization & Adaptive Scheduling (outputs: metrics, anomalies, signals, tasks)
- **Phase 16:** Heuristic Learning System (receives: heuristic_effectiveness signals)
- **Phase 18:** Multi-Agent Coordination (receives: coordination_insight signals)
- **Phase 13:** Safety Gates (integrated for safety validation)
