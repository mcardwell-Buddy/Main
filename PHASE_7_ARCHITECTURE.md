# Phase 7 Architecture: Visual Workflow & Execution Observatory

Generated: 2026-02-05

## Purpose
Phase 7 provides a read-only, execution-agnostic observability layer for Buddy. It visualizes reasoning, scheduling, dependencies, branching, recovery, and confidence without enabling any execution or edits.

## Boundaries (Hard Constraints)
- No modifications to Phase 1–6 code or behavior
- No task dispatch, tool execution, or workflow mutation
- No new execution state
- UI must function when execution is disabled

## Phase 7 Components (UI Layer Only)
- **Scheduler Observatory Panel**: task queue state, retries, failures, priority
- **Workflow DAG View**: nodes/edges from immutable task records
- **Conditional Branching View**: branch conditions and outcomes
- **Execution Timeline**: replay of task order and duration
- **Recovery View**: queue snapshots and recovered tasks
- **Data Source Panel**: read-only ingestion of logs/snapshots

Location:
- UI components live under [frontend/src/phase7](frontend/src/phase7)

## Data Contracts (Read-Only Inputs)

### 1) Scheduler Metrics JSONL
Primary: outputs/end_to_end/wave_metrics.jsonl
Schema (example fields):
- task_id
- workflow_id
- wave
- tool_used
- risk_level
- confidence_score
- approval_outcome
- approval_state
- execution_result
- retries
- execution_time_ms
- scheduler_queue_depth
- dependency_wait_time_ms
- timestamp
- session_id

### 2) Workflow Summaries
Primary: outputs/end_to_end/workflow_summaries.json
Schema:
- wave
- workflow_id
- session_id
- total_tasks
- completed
- success_rate

### 3) Scheduler Health Snapshot
Primary: outputs/end_to_end/scheduler_health.json
Schema (per wave):
- total_tasks
- total_executed
- total_succeeded
- total_failed
- total_deferred
- success_rate

### 4) Queue State Snapshot
Primary: outputs/task_scheduler_metrics/queue_state.json
Schema:
- timestamp
- version
- metrics
- tasks[]
  - id
  - description
  - status
  - priority
  - risk_level
  - confidence_score
  - dependencies[]
  - conditional_branches[]
  - attempt_count
  - metadata

## Visualization Encoding
- **Node color**: status (completed/failed/pending/deferred)
- **Border**: risk level
- **Badge**: retry count
- **Overlay**: confidence + approval outcome

## Phase 8–12 Hooks (Future-Proofing)
- **Phase 8 (Advisory)**: All outcomes logged; metrics exposed as immutable data
- **Phase 9 (Authoring)**: DAG is serializable and declarative
- **Phase 10+ (Autonomy)**: Recovery checkpoints and approval outcomes visible for deterministic replay

## Safety & Read-Only Guarantees
- No UI actions dispatch tasks
- No control surfaces for workflow editing
- Data inputs are logs/snapshots only
- All panels labeled “Read-Only”

## Integration Notes
- Phase 7 reads only from existing outputs or user-provided log files
- No new backend endpoints
- No code changes in Phase 1–6 modules
