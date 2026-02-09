# Phase 21: Autonomous Agent Orchestration - Architecture Guide

## Overview

Phase 21 implements autonomous multi-agent task orchestration with predictive task assignment, distributed execution, real-time monitoring, and bidirectional feedback loops.

**Phase 21 enables:**
- Autonomous coordination of 4+ agents
- Parallel task execution with wave-based synchronization
- Intelligent task assignment using Phase 20 predictions
- Real-time system health monitoring and anomaly detection
- Feedback generation for Phases 16, 18, 20 learning loops

**Integration Context:**
- **Input:** Phase 20 predicted task assignments, confidence scores, schedules
- **Output:** Execution results, agent performance metrics, learning signals
- **Feedback:** Performance data → Phase 18 (coordination), Phase 16 (heuristics), Phase 20 (prediction)
- **Safety:** Phase 13 safety gates enforce validation before all task execution

---

## Architecture Overview

### 5-Component Pipeline Architecture

```
Phase 20 Predictions
       ↓
┌──────────────────────────────────────────────────┐
│  1. AgentManager                                  │
│     - Load Phase 20 predictions                   │
│     - Assign tasks to agents using strategies     │
│     - Generate coordination plans                 │
│     - Output: agent_assignments.jsonl             │
└──────────────────────────────────────────────────┘
       ↓
┌──────────────────────────────────────────────────┐
│  2. AgentExecutor (parallel instances)            │
│     - Execute assigned tasks per agent            │
│     - Apply retry logic with safety gates         │
│     - Collect execution metrics                   │
│     - Output: executed_tasks.jsonl, metrics.jsonl │
└──────────────────────────────────────────────────┘
       ↓
┌──────────────────────────────────────────────────┐
│  3. Phase21FeedbackLoop                           │
│     - Evaluate execution outcomes                 │
│     - Generate learning signals (4 types)         │
│     - Route feedback to Phase 16/18/20            │
│     - Output: feedback_signals.jsonl              │
└──────────────────────────────────────────────────┘
       ↓
┌──────────────────────────────────────────────────┐
│  4. Phase21Monitor                                │
│     - Calculate per-agent and system metrics      │
│     - Detect anomalies (4 types)                  │
│     - Generate system health score (0-100)        │
│     - Output: system_health.json                  │
└──────────────────────────────────────────────────┘
       ↓
┌──────────────────────────────────────────────────┐
│  5. Phase21Harness                                │
│     - Orchestrate end-to-end pipeline             │
│     - Coordinate wave execution                   │
│     - Generate execution reports                  │
│     - Output: PHASE_21_AUTONOMOUS_EXECUTION.md   │
└──────────────────────────────────────────────────┘
```

---

## Component Specifications

### 1. AgentManager

**Purpose:** Central orchestrator for task assignment and agent coordination

**Key Responsibilities:**
- Load Phase 20 predicted tasks and schedules
- Assign tasks to agents using configurable strategies
- Evaluate per-agent performance metrics
- Generate coordination plans for multi-agent waves
- Maintain agent state (available, loaded, performance)

**Input:**
- Phase 20: `predicted_tasks.jsonl`, `predicted_schedule.jsonl`

**Output:**
- JSONL: `wave_X/agent_Y/agent_assignments.jsonl`
- Format: `{task_id, agent_id, predicted_success_rate, assigned_at, wave}`

**Assignment Strategies:**
| Strategy | Behavior | Use Case |
|----------|----------|----------|
| ROUND_ROBIN | Distribute tasks evenly across agents | Load balancing |
| LOAD_BALANCED | Assign to least-loaded agent | Minimize response time |
| PRIORITY_BASED | High-confidence tasks to high-availability agents | Maximize success |
| CONFIDENCE_BASED | Match task complexity to agent capability | Adaptive assignment |

**Key Methods:**
```python
load_phase20_predictions()          # Load Phase 20 JSONL
assign_tasks_to_agents(tasks)       # Apply assignment strategy
evaluate_agent_performance()        # Calculate per-agent metrics
generate_coordination_plan(tasks)   # Plan multi-agent execution
update_agent_state(agent_id)        # Track agent status
get_agent_availability()            # Check agent capacity
write_agent_state_outputs(wave)     # Write state to JSONL
```

---

### 2. AgentExecutor

**Purpose:** Distributed task execution with retry logic and safety validation

**Key Responsibilities:**
- Execute assigned tasks for single agent
- Apply retry strategies with exponential/linear backoff
- Enforce Phase 13 safety gates before execution
- Collect per-task execution metrics
- Handle failures gracefully with configurable retry limits

**Input:**
- Agent assignments: `wave_X/agent_Y/agent_assignments.jsonl`
- Task execution requests

**Output:**
- JSONL: `wave_X/agent_Y/executed_tasks.jsonl`
- Format: `{task_id, agent_id, status, start_time, end_time, success_indicator, error_msg}`

**Task Lifecycle:**
```
PENDING → IN_PROGRESS → COMPLETED (success)
              ↓
           FAILED (max retries exceeded)
         ↑ (if RetryStrategy.EXPONENTIAL_BACKOFF)
       RETRYING
```

**Retry Strategies:**
| Strategy | Formula | Example |
|----------|---------|---------|
| EXPONENTIAL_BACKOFF | delay = 2^(retry_count) | 1s, 2s, 4s, 8s... |
| LINEAR_BACKOFF | delay = retry_count * base | 2s, 4s, 6s, 8s... |
| NO_RETRY | max_retries = 1 | Fail immediately |

**Key Methods:**
```python
execute_task(task)                  # Execute single task with retries
execute_wave(wave, tasks)           # Execute all wave tasks
apply_retry_strategy(task, retry)   # Calculate backoff delay
collect_execution_metrics(task)     # Gather task metrics
write_execution_outputs(wave)       # Write JSONL results
_check_safety_gates(task)           # Phase 13 validation
_simulate_task_execution(task)      # Realistic execution simulation
```

---

### 3. Phase21FeedbackLoop

**Purpose:** Evaluate execution outcomes and generate learning signals

**Key Responsibilities:**
- Compare predicted vs actual execution results
- Generate 4 types of learning signals
- Route feedback to appropriate upstream phases
- Aggregate wave-level learning insights
- Calculate signal confidence scores

**Input:**
- Predicted tasks: Phase 20 `predicted_tasks.jsonl`
- Actual outcomes: `wave_X/agent_Y/executed_tasks.jsonl`

**Output:**
- JSONL: Phase 16 `heuristic_feedback.jsonl`
- JSONL: Phase 18 `coordination_feedback.jsonl`
- JSONL: Phase 20 `prediction_feedback.jsonl`
- JSONL: Agent performance feedback for Phase 18

**Learning Signal Types:**

| Signal Type | Target Phase | Content | Example |
|-------------|--------------|---------|---------|
| agent_performance | Phase 18 | Per-agent capability metrics | success_rate, avg_latency |
| multi_agent_coordination | Phase 18 | Coordination effectiveness | interference_count, load_balance |
| heuristic_feedback | Phase 16 | Heuristic quality assessment | accuracy_improvement, error_rate |
| prediction_validation | Phase 20 | Prediction model feedback | confidence_calibration, error_analysis |

**Key Methods:**
```python
evaluate_agent_outcomes(predicted, actual)  # Compare predictions to reality
generate_feedback_signals(wave)             # Create 4 signal types
write_feedback_outputs()                    # Route to Phase 16/18/20
aggregate_wave_learning(wave)               # Summarize wave insights
_calculate_signal_confidence(signal)        # Confidence scoring
_identify_patterns(outcomes)                # Pattern detection
```

---

### 4. Phase21Monitor

**Purpose:** Track system health and detect anomalies

**Key Responsibilities:**
- Calculate per-agent and system-wide metrics
- Detect 4 types of anomalies
- Generate system health score (0-100)
- Track confidence trajectory across waves
- Generate alerts and recommendations

**Input:**
- Execution results: `wave_X/agent_Y/executed_tasks.jsonl`
- Performance metrics: `wave_X/agent_Y/agent_metrics.jsonl`

**Output:**
- JSON: `phase21_system_health.json`
- Format: `{wave, health_score (0-100), health_status, metrics, anomalies}`

**Metrics Tracked:**

| Metric | Formula | Target Range |
|--------|---------|--------------|
| Success Rate | completed_tasks / total_tasks | ≥ 0.90 |
| Availability | available_agents / total_agents | ≥ 0.95 |
| Accuracy | \|predicted_success - actual_success\| | ≤ 0.10 |
| Load Balance | min_load / max_load | ≥ 0.70 |
| Confidence | avg(predicted_success_rates) | ≥ 0.80 |

**Health Score Calculation:**
```
health_score = (
    success_rate * 0.40 +
    availability * 0.20 +
    accuracy * 0.20 +
    load_balance * 0.20
) * 100

Health Status:
  ≥ 90: EXCELLENT
  ≥ 70: GOOD
  ≥ 50: FAIR
  < 50: POOR
```

**Anomalies Detected:**

| Anomaly Type | Condition | Severity | Action |
|--------------|-----------|----------|--------|
| agent_failure | success_rate < 0.50 | HIGH | Investigate agent, consider rebalancing |
| coordination_issue | load_imbalance > 40% | MEDIUM | Rebalance tasks, check agent coupling |
| prediction_drift | \|error\| > 0.25 | MEDIUM | Retrain Phase 20 model, adjust confidence |
| load_imbalance | max_load / min_load > 1.5 | LOW | Rebalance using Phase 20 scheduler |

**Key Methods:**
```python
calculate_metrics(wave, execution_results)  # Compute per-agent + system metrics
detect_anomalies(metrics)                   # Identify 4 anomaly types
generate_system_health(wave, summary)       # Calculate 0-100 health score
write_monitoring_outputs(wave)              # Write JSON/JSONL results
track_confidence_trajectory(wave)           # Monitor confidence trends
_calculate_imbalance_ratio()                # Load balance calculation
_detect_agent_failure_pattern()             # Failure pattern detection
```

---

### 5. Phase21Harness

**Purpose:** End-to-end orchestration and pipeline coordination

**Key Responsibilities:**
- Initialize all components (Manager, Executors, Loop, Monitor)
- Orchestrate wave-based parallel execution
- Apply Phase 13 safety gates before execution
- Generate comprehensive execution reports
- Coordinate output directory structure

**Input:**
- Phase 20 outputs: `phase20_output_dir/`
- Phase 16 heuristics: `phase16_output_dir/`
- Phase 18 coordination: `phase18_output_dir/`
- Configuration: num_agents, assignment_strategy, retry_strategy

**Output:**
- MARKDOWN: `PHASE_21_AUTONOMOUS_EXECUTION.md`
- JSON: `phase21_execution_summary.json`
- Directory structure: `wave_X/agent_Y/` with all module outputs

**Pipeline Execution Flow:**

```
Phase 21 Harness Entry Point
      ↓
  Load Phase 20 Data
      ↓
  For each wave:
    ├─ AgentManager.assign_tasks_to_agents()
    │   └─ Output: wave_X/agent_Y/agent_assignments.jsonl
    │
    ├─ For each agent (parallel):
    │   ├─ AgentExecutor.execute_wave()
    │   │   ├─ Check Phase 13 safety gates
    │   │   ├─ Execute assigned tasks
    │   │   └─ Output: executed_tasks.jsonl, metrics.jsonl
    │   │
    │   └─ Collect execution results
    │
    ├─ Phase21FeedbackLoop.generate_feedback_signals()
    │   ├─ Evaluate outcomes
    │   └─ Output: feedback to Phase 16/18/20
    │
    └─ Phase21Monitor.generate_system_health()
        ├─ Calculate metrics
        ├─ Detect anomalies
        └─ Output: phase21_system_health.json
      ↓
  Aggregate Results
      ↓
  Generate Reports
      ├─ PHASE_21_AUTONOMOUS_EXECUTION.md
      └─ phase21_execution_summary.json
```

**Key Methods:**
```python
run_phase21(waves, max_parallel=4)          # Main orchestration entry point
_execute_wave(wave)                         # Single wave execution
_apply_safety_gates(task)                   # Phase 13 enforcement
_generate_phase21_report(result)            # Create markdown report
_generate_phase21_summary()                 # Create JSON summary
_create_output_directories(waves)           # Scaffold directory structure
_load_phase20_data()                        # Validate Phase 20 data
```

---

## Data Flow and Integration

### Phase 20 → Phase 21

**Phase 20 provides:**
- `predicted_tasks.jsonl`: Task predictions with confidence
- `predicted_schedule.jsonl`: Predicted task assignments
- Prediction metrics for trend analysis

**Phase 21 consumes:**
- Predicted task assignments as input to AgentManager
- Confidence scores for assignment strategy tuning
- Schedule recommendations for planning

### Phase 21 → Phase 16 (Heuristics)

**Phase 21 generates:**
- `heuristic_feedback.jsonl`: Heuristic effectiveness assessment
- Signal type: "heuristic_feedback"
- Content: Which heuristics predicted outcomes correctly vs incorrectly

### Phase 21 → Phase 18 (Coordination)

**Phase 21 generates:**
- `coordination_feedback.jsonl`: Multi-agent coordination effectiveness
- Signal types: "agent_performance", "multi_agent_coordination"
- Content: Per-agent metrics, load balance assessment, coordination issues

### Phase 21 ← Phase 13 (Safety)

**Phase 13 integration:**
- Safety gates called before each task execution
- Phase 21 must verify safety clearance before proceeding
- Failures trigger anomaly detection and alerting

---

## Wave-Based Execution Model

**Waves** are sequential batches of tasks executed in parallel.

**Wave Structure:**
```
Wave 1: Tasks A, B, C assigned to Agent 0, 1, 2
  ↓ (all execute in parallel)
Wave 1 Complete → Feedback/Monitoring
  ↓
Wave 2: Tasks D, E, F assigned based on Wave 1 results
  ↓ (all execute in parallel)
Wave 2 Complete → Feedback/Monitoring
  ↓
Wave 3: Tasks G, H, I assigned based on Wave 1-2 results
  ↓
Pipeline Complete → Generate Reports
```

**Wave-Based Feedback:**
- After each wave, feedback generated from execution results
- Phase 20 uses feedback to update predictions for next wave
- Phase 18 uses feedback to adjust coordination strategies
- Phase 16 uses feedback to refine heuristics

---

## Output Directory Structure

```
phase21_outputs/
├── wave_1/
│   ├── agent_0/
│   │   ├── agent_assignments.jsonl       (input from AgentManager)
│   │   ├── executed_tasks.jsonl          (output from AgentExecutor)
│   │   ├── agent_metrics.jsonl           (output from Monitor)
│   │   └── agent_feedback.jsonl          (output from FeedbackLoop)
│   ├── agent_1/
│   │   └── ... (same structure)
│   ├── agent_2/
│   └── agent_3/
│
├── wave_2/
│   └── ... (same structure)
│
├── wave_3/
│   └── ... (same structure)
│
├── phase21_system_health.json            (output from Monitor)
├── phase21_execution_summary.json        (output from Harness)
├── phase21_learning_signals.jsonl        (aggregated from FeedbackLoop)
└── PHASE_21_AUTONOMOUS_EXECUTION.md      (output from Harness)
```

---

## Safety and Error Handling

### Phase 13 Safety Gates

**Before each task execution:**
1. Check Phase 13 safety clearance: `_check_safety_gates(task)`
2. Verify task constraints and dependencies
3. Validate resource availability
4. Confirm no blocking anomalies
5. Proceed only if all gates pass

**If safety gate fails:**
- Task marked as FAILED with safety violation error
- Retry logic respects retry_strategy
- Anomaly detected and logged
- Coordination loop notified for rebalancing

### Retry Logic

**On task failure:**
1. Check `max_retries` limit
2. Calculate backoff delay based on `retry_strategy`
3. Apply Phase 13 safety gates again
4. Execute task with exponential/linear backoff
5. Log all retry attempts and metrics

### Anomaly Handling

**When anomaly detected:**
1. Log anomaly with type, severity, timestamp
2. Generate recommendation for resolution
3. Include in system health assessment
4. Route to appropriate feedback loop
5. Trigger alerting if severity HIGH

---

## Configuration Parameters

### Phase 21Harness Configuration

```python
num_agents: int = 4                         # Number of parallel agents
assignment_strategy: AssignmentStrategy     # Task assignment strategy
retry_strategy: RetryStrategy               # Retry backoff strategy
max_retries: int = 3                        # Maximum retry attempts
dry_run: bool = True                        # Test mode (no state changes)
max_parallel_tasks: int = 4                 # Parallel task limit per wave
```

### AgentManager Configuration

```python
assignment_strategy: AssignmentStrategy     # Override default strategy
load_balance_threshold: float = 0.30        # Load balance trigger (30%)
confidence_threshold: float = 0.70          # Confidence filter threshold
```

### AgentExecutor Configuration

```python
retry_strategy: RetryStrategy               # Backoff strategy
max_retries: int = 3                        # Maximum retry attempts
exponential_base: float = 2.0               # Exponential backoff base
linear_base: float = 2.0                    # Linear backoff base (seconds)
```

### Phase21Monitor Configuration

```python
anomaly_sensitivity: float = 0.25           # Anomaly detection threshold
health_score_weights: dict = {              # Health score calculation
    "success_rate": 0.40,
    "availability": 0.20,
    "accuracy": 0.20,
    "load_balance": 0.20
}
```

---

## Testing Strategy

**Unit Tests (27+ tests):**
- AgentManager: 5 tests (initialization, task assignment, coordination, performance, outputs)
- AgentExecutor: 5 tests (execution, retries, metrics, safety gates, task simulation)
- Phase21FeedbackLoop: 4 tests (outcome evaluation, signal generation, routing, aggregation)
- Phase21Monitor: 4 tests (metrics, anomalies, health, trajectory)
- Phase21Harness: 6 tests (initialization, components, data loading, directories, wave execution, reporting)

**Integration Tests (5+ tests):**
- End-to-end single wave execution
- End-to-end multi-wave execution
- Agent parallel execution
- Feedback loop integration
- Monitoring throughout execution

**Test Focus:**
- JSONL output structure validation
- Phase 13 safety gate integration
- Retry logic correctness
- Anomaly detection accuracy
- Health score calculation
- Feedback routing to Phase 16/18/20

---

## Metrics and KPIs

### Execution Metrics
| Metric | Definition | Good Range |
|--------|------------|-----------|
| Task Success Rate | Tasks completed / Total tasks | ≥ 0.90 |
| Agent Availability | Available time / Total time | ≥ 0.95 |
| Prediction Accuracy | \|Predicted Success - Actual Success\| | ≤ 0.10 |
| Load Balance | Min agent load / Max agent load | ≥ 0.70 |
| System Health | Weighted metric average | ≥ 90 |

### Learning Metrics
| Metric | Definition | Good Trend |
|--------|------------|-----------|
| Prediction Drift | Change in error rate | Decreasing |
| Heuristic Effectiveness | Heuristic accuracy | Increasing |
| Coordination Quality | Load balance improvement | Increasing |
| Agent Capability | Per-agent success rate | Converging |

---

## Next Steps (Implementation Roadmap)

**Phase 21 Implementation Sequence:**

1. **AgentManager** (priority: HIGH)
   - Load Phase 20 predictions
   - Implement 4 assignment strategies
   - Generate coordination plans

2. **AgentExecutor** (priority: HIGH)
   - Implement task execution loop
   - Add retry logic with exponential backoff
   - Integrate Phase 13 safety gates

3. **Phase21FeedbackLoop** (priority: MEDIUM)
   - Implement outcome comparison
   - Generate 4 signal types
   - Route feedback to Phase 16/18/20

4. **Phase21Monitor** (priority: MEDIUM)
   - Calculate all 5 metrics
   - Detect all 4 anomaly types
   - Generate health scores

5. **Phase21Harness** (priority: HIGH)
   - Orchestrate component execution
   - Implement wave-based parallelism
   - Generate execution reports

6. **Phase21 Test Suite** (priority: HIGH)
   - Implement all 27+ unit tests
   - Add integration tests
   - Verify 100% test pass rate

---

## References

- **Phase 20**: Predictive Task Assignment (consumes output)
- **Phase 18**: Multi-Agent Coordination (receives feedback)
- **Phase 16**: Heuristic Learning (receives feedback)
- **Phase 13**: Safety Gates (integration point)
- **PHASE_21_READINESS_REPORT.md**: Scaffolding verification
- **PHASE_21_COMPLETION_SUMMARY.md**: Summary of Phase 21 implementation

