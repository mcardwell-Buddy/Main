# Phase 15 Architecture: Autonomous Real-Time Operation

## Overview

Phase 15 implements autonomous real-time task execution with dynamic policy adaptation. It integrates Phase 13 safety gates and Phase 14 meta-learning to execute planned tasks autonomously while continuously monitoring outcomes and adapting policies based on real-time execution metrics.

## Architecture Stack

```
┌─────────────────────────────────────────────────────────────┐
│              AutonomousOperationHarness                      │
│         (Orchestration & Workflow Management)                │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
┌──────────────┐ ┌──────────────┐ ┌────────────────┐
│ Autonomous   │ │   Policy     │ │  Safety Gate   │
│  Executor    │ │   Adapter    │ │  (Phase 13)    │
└──────────────┘ └──────────────┘ └────────────────┘
        │            │                     │
        └────────────┼─────────────────────┘
                     │
              Load Phase 14:
              ├─ planned_tasks.jsonl
              ├─ meta_insights.jsonl
              ├─ heuristics.jsonl
              └─ phase14_ui_state.json
```

## Core Components

### 1. AutonomousExecutor

**Purpose**: Executes tasks with real-time safety gate enforcement and confidence recalibration.

**Key Methods**:
- `execute_wave(wave, tasks)` - Execute all tasks in a wave
- `_execute_task(wave, task)` - Execute single task with safety gates
- `_simulate_execution(task_id, risk_level, confidence)` - Simulate task execution
- `_record_confidence_update(...)` - Log confidence changes

**Execution Flow**:
```
Task Received
    │
    ▼
Safety Gate Evaluation
    │
    ├─ APPROVED → Execute task
    ├─ DEFERRED → Confidence -0.02, log outcome
    └─ REJECTED → Confidence -0.15, trigger rollback
    │
    ▼
Task Execution (if approved)
    │
    ├─ Success → Confidence +0.05 to +0.08
    └─ Failure → Confidence -0.05 to -0.10 (with possible rollback)
    │
    ▼
Record Outcome & Confidence Update
```

**Confidence Deltas**:
- Task Completed Successfully: +0.05 to +0.08
- Task Deferred: -0.02
- Task Failed: -0.05
- Task Failed with Rollback: -0.10
- Task Rejected: -0.15

**Data Structures**:

```python
@dataclass
class TaskOutcome:
    task_id: str
    wave: int
    status: ExecutionStatus  # COMPLETED, FAILED, DEFERRED, ROLLED_BACK
    risk_level: str
    confidence_before: float
    confidence_after: float
    confidence_delta: float
    safety_gate_status: str  # APPROVED, DEFERRED, REJECTED
    execution_time_ms: float
    error: str = None
    rollback_triggered: bool = False
    retries: int = 0

@dataclass
class ConfidenceUpdate:
    task_id: str
    wave: int
    confidence_before: float
    confidence_after: float
    delta: float
    reason: str
    timestamp: str
```

### 2. PolicyAdapter

**Purpose**: Monitors execution outcomes and dynamically adapts policies based on real-time metrics.

**Key Methods**:
- `record_wave_metrics(wave, outcomes, insights)` - Analyze outcomes and trigger adaptations
- `_adapt_policy_from_metrics(wave, success_rate, failure_rate, deferral_rate)` - Apply adaptation rules
- `apply_meta_insights(insights)` - Boost policies based on insights
- `get_policy_history()` - Track all policy changes
- `get_summary()` - Generate policy summary

**Adaptation Rules**:

| Condition | Action | Effect |
|-----------|--------|--------|
| failure_rate > 0.20 | retry_multiplier += 0.1 | More retries on failures |
| deferral_rate > 0.30 | high_risk_threshold += 0.05 | Stricter approval requirements |
| success_rate > 0.85 | priority_bias += 0.05 | Faster execution for high-confidence tasks |
| success_rate < 0.60 | priority_bias -= 0.10 | More conservative execution |

**Policy Structure**:
```python
policy = {
    "high_risk_threshold": float,     # Confidence threshold for HIGH-risk tasks
    "retry_multiplier": float,         # Multiplier for retry count
    "priority_bias": float,            # Bias for task prioritization
}
```

**Data Structure**:
```python
@dataclass
class PolicyUpdate:
    wave: int
    timestamp: str
    old_policy: Dict[str, float]
    new_policy: Dict[str, float]
    metrics: Dict[str, float]  # success_rate, failure_rate, deferral_rate
    reason: str
```

### 3. SafetyGate (Phase 13 Integration)

**Multi-Tier Approval System**:

| Risk Level | Confidence Threshold | Approval Status |
|------------|-------------------|-----------------|
| LOW | ≥ 0.50 | APPROVED or DEFERRED |
| MEDIUM | ≥ 0.75 | APPROVED or DEFERRED |
| HIGH | ≥ 0.90 | APPROVED, DEFERRED, or REJECTED |

**Approval Decision**:
```
if dry_run:
    return APPROVED

if risk_level == "LOW":
    if confidence ≥ 0.50:
        return APPROVED
    else:
        return DEFERRED

elif risk_level == "MEDIUM":
    if confidence ≥ 0.75:
        return APPROVED
    else:
        return DEFERRED

elif risk_level == "HIGH":
    if confidence ≥ 0.90:
        return APPROVED
    elif confidence ≥ 0.75:
        return DEFERRED
    else:
        return REJECTED
```

## Orchestration Flow: AutonomousOperationHarness

```
Start Harness
    │
    ├─ Load Phase 14 artifacts
    │  ├─ planned_tasks.jsonl (12 tasks)
    │  ├─ meta_insights.jsonl (3 insights)
    │  ├─ heuristics.jsonl (2 heuristics)
    │  └─ phase14_ui_state.json (initial policy)
    │
    ├─ For each wave (1 to N):
    │  │
    │  ├─ Create AutonomousExecutor
    │  ├─ Execute all wave tasks
    │  │  └─ For each task:
    │  │     ├─ Safety gate evaluation
    │  │     ├─ Task execution (if approved)
    │  │     └─ Confidence update
    │  │
    │  ├─ Create PolicyAdapter
    │  ├─ Record wave metrics
    │  │  └─ Trigger policy adaptations
    │  │
    │  └─ Write wave outputs:
    │     ├─ task_outcomes.jsonl (append)
    │     ├─ confidence_updates.jsonl (append)
    │     ├─ policy_updates.jsonl (append)
    │     └─ safety_gate_decisions.jsonl (append)
    │
    ├─ Write aggregate outputs:
    │  ├─ phase15_ui_state.json (complete state)
    │  └─ PHASE_15_AUTONOMOUS_EXECUTION.md (report)
    │
    └─ Complete
```

## Output Files

### 1. task_outcomes.jsonl
One JSON object per line, containing task execution results:
```json
{
  "task_id": "wave1_task1",
  "wave": 1,
  "status": "completed",
  "risk_level": "LOW",
  "confidence_before": 0.85,
  "confidence_after": 0.91,
  "confidence_delta": 0.06,
  "safety_gate_status": "APPROVED",
  "execution_time_ms": 47.23,
  "rollback_triggered": false,
  "retries": 0
}
```

### 2. confidence_updates.jsonl
Track confidence changes throughout execution:
```json
{
  "task_id": "wave1_task1",
  "wave": 1,
  "confidence_before": 0.85,
  "confidence_after": 0.91,
  "delta": 0.06,
  "reason": "Task completed successfully",
  "timestamp": "2024-11-21T10:30:45.123Z"
}
```

### 3. policy_updates.jsonl
Log all policy adaptations:
```json
{
  "wave": 1,
  "timestamp": "2024-11-21T10:31:00.456Z",
  "old_policy": {
    "high_risk_threshold": 0.80,
    "retry_multiplier": 1.00,
    "priority_bias": 1.00
  },
  "new_policy": {
    "high_risk_threshold": 0.80,
    "retry_multiplier": 1.10,
    "priority_bias": 1.00
  },
  "metrics": {
    "success_rate": 0.75,
    "failure_rate": 0.25,
    "deferral_rate": 0.00
  },
  "reason": "Failure rate (0.25) exceeds threshold (0.20)"
}
```

### 4. safety_gate_decisions.jsonl
Complete safety gate evaluation log:
```json
{
  "task_id": "wave1_task1",
  "risk_level": "LOW",
  "confidence": 0.85,
  "approval": "APPROVED",
  "reason": "LOW risk approved (confidence 0.85 ≥ 0.50)"
}
```

### 5. phase15_ui_state.json
Complete Phase 15 state snapshot:
```json
{
  "generated_at": "2024-11-21T10:32:00.789Z",
  "phase": 15,
  "execution_mode": "dry_run",
  "wave_stats": [
    {
      "wave": 1,
      "total_tasks": 4,
      "completed": 4,
      "failed": 0,
      "deferred": 0,
      "rolled_back": 0,
      "success_rate": 1.0,
      "avg_confidence_delta": 0.065
    }
  ],
  "policy_summary": {
    "initial_policy": {...},
    "current_policy": {...},
    "updates_count": 0
  }
}
```

### 6. PHASE_15_AUTONOMOUS_EXECUTION.md
Comprehensive execution report with metrics, adaptations, and decisions.

## Safety & Observability

### Multi-Layer Safety Enforcement

1. **Pre-Execution Safety Gate** (Phase 13)
   - Evaluates confidence vs. risk level
   - Makes APPROVED/DEFERRED/REJECTED decisions
   - Logged in safety_gate_decisions.jsonl

2. **Execution Monitoring**
   - Tracks task success/failure
   - Records execution time
   - Monitors rollback conditions

3. **Post-Execution Adaptation**
   - Analyzes outcome metrics
   - Adapts policy based on patterns
   - Logs all policy changes

### Observability

**Real-Time Metrics**:
- Task execution status (COMPLETED, FAILED, DEFERRED, ROLLED_BACK)
- Confidence before/after with delta
- Safety gate decisions and reasons
- Execution timing and performance

**Aggregate Metrics**:
- Wave success rates
- Policy evolution over waves
- Confidence trend analysis
- Risk distribution

## Integration Points

### Phase 13 (SafetyGate)
- Multi-tier approval based on risk/confidence
- APPROVED → Execute
- DEFERRED → Log and skip
- REJECTED → Rollback

### Phase 14 (Meta-Learning)
- Load planned_tasks.jsonl for task specifications
- Load meta_insights.jsonl for pattern guidance
- Load heuristics.jsonl for execution hints
- Load phase14_ui_state.json for initial policy

## Configuration

**CLI Arguments**:
```bash
python buddy_phase15_harness.py \
    --waves 3 \                              # Number of waves to execute
    --output-dir outputs/phase15 \           # Output directory
    --phase14-dir outputs/phase14 \          # Phase 14 artifacts directory
    --dry-run \                              # Dry-run mode (no actual execution)
    --require-approval                       # Require explicit approval for tasks
```

## Performance Characteristics

- **Per-Task Overhead**: ~50-100ms (includes safety gate evaluation and confidence recalibration)
- **Per-Wave Overhead**: ~500ms-1s (policy adaptation analysis)
- **Memory Usage**: O(tasks_per_wave) for outcome tracking
- **Output Size**: ~500KB-1MB per wave (JSONL logs)

## Future Enhancements

1. **Real-Time Rollback Optimization**: Improve rollback decision logic based on task criticality
2. **Parallel Wave Execution**: Execute multiple waves concurrently when safe
3. **Machine Learning Policy Adaptation**: Use ML models for advanced policy optimization
4. **Advanced Confidence Calibration**: Implement Bayesian confidence updates
5. **Cross-Phase Learning**: Integrate learnings from previous phases
