# Phase 24 Integration Guide

## Overview

Phase 24 Integration enables the Phase 25 dashboards to display real-time observability data from the autonomous tool orchestration system (Phase 24) in a **purely read-only, observation-only** manner.

## Architecture

### Design Principles

1. **Read-Only Guarantee**: All adapters use immutable frozen dataclasses
2. **Zero Side Effects**: No write operations, no state mutations
3. **Graceful Degradation**: Missing Phase 24 files don't break dashboards
4. **Exception Safety**: All file I/O wrapped in try-catch with safe defaults
5. **Deterministic**: Same input files always produce same output views

### Adapter Hierarchy

```
Phase24AggregateAdapter (Coordinator)
├── ExecutionLogAdapter (tool_execution_log.jsonl)
├── StateTransitionAdapter (execution_state_transitions.jsonl)
├── SystemHealthAdapter (system_health.json)
├── RollbackAdapter (rollback_events.jsonl)
├── ConflictAdapter (tool_conflicts.json)
└── LearningSignalAdapter (learning_signals.jsonl)
```

## Core Components

### Phase 24 Data Sources

#### 1. `tool_execution_log.jsonl` (ExecutionLogAdapter)

**Purpose**: Track individual tool executions

**Data Structure**:
```python
ToolExecution:
  - execution_id: str
  - tool_name: str
  - timestamp: str (ISO8601)
  - duration_ms: int
  - status: "success" | "failed" | "blocked" | "rollback"
  - confidence_score: float (0.0-1.0)
  - risk_level: "low" | "medium" | "high"
  - approval_status: "approved" | "pending" | "denied"
  - dry_run_mode: bool
```

**Available Methods**:
- `get_recent_executions(limit=50)` → List[ToolExecution]
- `get_executions_by_status(status)` → List[ToolExecution]
- `get_tool_statistics()` → Dict[tool_name, {total_calls, successful, failed, blocked, avg_confidence, avg_duration_ms}]
- `get_execution_success_rate()` → float (0.0-1.0)

**Dashboard Integration**:
- Operations Dashboard: Execution preview widget
- Learning Dashboard: Tool performance trends widget
- Interaction Dashboard: Execution context widget

#### 2. `execution_state_transitions.jsonl` (StateTransitionAdapter)

**Purpose**: Track system state changes during execution

**Data Structure**:
```python
ExecutionStateTransition:
  - transition_id: str
  - from_state: str ("idle", "executing", "awaiting_approval", "rolled_back")
  - to_state: str
  - trigger: str ("completion", "approval", "error", "rollback", "safety_gate")
  - details: str
  - timestamp: str (ISO8601)
```

**Available Methods**:
- `get_recent_transitions(limit=50)` → List[ExecutionStateTransition]
- `get_state_timeline()` → List[Tuple[timestamp, from_state, to_state]]
- `get_transitions_by_trigger(trigger)` → List[ExecutionStateTransition]

**Dashboard Integration**:
- Operations Dashboard: System state monitoring
- Developer Mode: Phase tab state history

#### 3. `system_health.json` (SystemHealthAdapter)

**Purpose**: Current snapshot of overall system health

**Data Structure**:
```python
SystemHealthSnapshot:
  - timestamp: str (ISO8601)
  - health_score: float (0-100)
  - execution_mode: "MOCK" | "DRY_RUN" | "LIVE" | "LOCKED"
  - active_tools: int
  - completed_executions: int
  - failed_executions: int
  - blocked_executions: int
  - average_confidence: float (0.0-1.0)
  - anomalies: List[str]
```

**Health Tiers**:
- EXCELLENT: 90-100
- GOOD: 70-89
- WARNING: 50-69
- CRITICAL: 25-49
- FAILURE: 0-24

**Available Methods**:
- `get_health_snapshot()` → Optional[SystemHealthSnapshot]
- `get_health_tier(score: float)` → str
- `get_health_indicators()` → Dict[str, Any]

**Dashboard Integration**:
- Operations Dashboard: System health monitoring
- Interaction Dashboard: Safety context widget

#### 4. `rollback_events.jsonl` (RollbackAdapter)

**Purpose**: Track system rollback events and recovery

**Data Structure**:
```python
RollbackEvent:
  - rollback_id: str
  - trigger: "safety_violation" | "execution_failure" | "conflict_resolution" | "manual"
  - affected_executions: List[str]
  - reason: str
  - recovery_status: "in_progress" | "completed" | "failed"
  - duration_ms: int
  - timestamp: str (ISO8601)
```

**Available Methods**:
- `get_recent_rollbacks(limit=20)` → List[RollbackEvent]
- `get_rollback_summary()` → Dict[total, by_trigger, successful/failed/in_progress counts]
- `get_rollbacks_by_trigger(trigger)` → List[RollbackEvent]

**Dashboard Integration**:
- Operations Dashboard: Rollback monitoring widget
- Interaction Dashboard: Rollback explanation widget

#### 5. `tool_conflicts.json` (ConflictAdapter)

**Purpose**: Track and resolve tool execution conflicts

**Data Structure**:
```python
ToolConflict:
  - conflict_id: str
  - tools_involved: List[str]
  - conflict_type: str ("state_collision", "resource_contention", "timing", "dependency")
  - severity: "low" | "medium" | "high"
  - resolution_strategy: str
  - resolution_status: "unresolved" | "in_progress" | "resolved"
```

**Available Methods**:
- `get_conflicts()` → List[ToolConflict]
- `get_unresolved_conflicts()` → List[ToolConflict]
- `get_conflict_summary()` → Dict[total, unresolved, by_type, by_severity, resolution_strategies]
- `get_high_severity_conflicts()` → List[ToolConflict]

**Dashboard Integration**:
- Operations Dashboard: Conflict monitoring widget
- Interaction Dashboard: Safety context widget

#### 6. `learning_signals.jsonl` (LearningSignalAdapter)

**Purpose**: Track patterns and recommendations from autonomous system learning

**Data Structure**:
```python
LearningSignal:
  - signal_id: str
  - signal_type: "tool_reliability" | "timing_pattern" | "safety_pattern" | "conflict_pattern"
  - tool_name: str
  - insight: str
  - confidence: float (0.0-1.0)
  - recommended_action: str
  - affected_future_executions: int
```

**Available Methods**:
- `get_recent_signals(limit=20)` → List[LearningSignal]
- `get_signals_by_type(signal_type)` → List[LearningSignal]
- `get_high_confidence_signals(threshold=0.8)` → List[LearningSignal]
- `get_learning_summary()` → Dict[total, by_type, by_tool, avg_confidence, high_confidence_count]

**Dashboard Integration**:
- Learning Dashboard: High-confidence signals widget
- Learning Dashboard: Tool trends widget

### Phase24AggregateAdapter

Central coordinator that combines all 6 adapters for dashboard-specific summaries.

**Methods**:
- `get_operations_summary()` → Dict (for Operations Dashboard)
- `get_learning_summary()` → Dict (for Learning Dashboard)
- `get_interaction_summary()` → Dict (for Interaction Dashboard)

## Dashboard Integration

### Operations Dashboard

**Phase 24 Widgets Added**:

1. **Phase 24 Conflicts Widget**
   - Displays unresolved tool conflicts
   - Shows severity levels and affected tools
   - Data Source: `tool_conflicts.json`
   - Refresh: 5 seconds

2. **Phase 24 Rollbacks Widget**
   - Shows recent rollback events
   - Displays trigger reason and recovery status
   - Data Source: `rollback_events.jsonl`
   - Refresh: 10 seconds

### Learning Dashboard

**Phase 24 Widgets Added**:

1. **Phase 24 High-Confidence Signals Widget**
   - Displays learning signals with confidence ≥ 0.85
   - Shows tool, signal type, insight, and recommended action
   - Data Source: `learning_signals.jsonl`
   - Refresh: 15 seconds

2. **Phase 24 Tool Trends Widget**
   - Shows tool performance metrics
   - Sorted by average confidence score
   - Displays: tool name, total calls, success rate %, average confidence
   - Data Source: `tool_execution_log.jsonl`
   - Refresh: 20 seconds

### Interaction Dashboard

**Phase 24 Widgets Added**:

1. **Phase 24 Execution Preview Widget**
   - Displays execution mode and system health
   - Shows recent executions with risk levels
   - Data Source: `tool_execution_log.jsonl`, `system_health.json`
   - Refresh: 3 seconds (most responsive)

2. **Phase 24 Approval Context Widget**
   - Shows pending approvals and safety blocks
   - Displays recent conflicts
   - Data Source: `tool_conflicts.json`, `execution_state_transitions.jsonl`
   - Refresh: 5 seconds

3. **Phase 24 Rollback Explanation Widget**
   - Provides human-readable rollback context
   - Shows affected execution count and recovery status
   - Data Source: `rollback_events.jsonl`
   - Refresh: 10 seconds

## CLI Commands

Phase 24 data is accessible via dashboard CLI:

```bash
# View unresolved conflicts
python dashboard_app.py phase24-conflicts

# View recent rollbacks (limit optional)
python dashboard_app.py phase24-rollbacks 20

# View high-confidence learning signals
python dashboard_app.py phase24-signals

# View system health snapshot
python dashboard_app.py phase24-health

# View complete Phase 24 summary
python dashboard_app.py phase24-summary
```

## Safety Guarantees

### Immutability

All data types are frozen dataclasses:
```python
@dataclass(frozen=True)
class ToolExecution:
    execution_id: str
    tool_name: str
    # ... fields
```

Attempting to modify any field raises `FrozenInstanceError`.

### Exception Handling

All adapters handle missing or corrupted files gracefully:

```python
try:
    # Read Phase 24 data
    executions = adapter.get_recent_executions()
except Exception:
    # Return empty list, no crash
    executions = []
```

### No Write Operations

Adapters only implement read-only methods. No write/update/delete operations exist.

### Deterministic Behavior

- Same input files → Same output every time
- No random elements
- No side effects
- Pure functions throughout

## Data Consistency

### Timestamp Ordering

All adapters return data ordered by timestamp (most recent first):

```python
recent = adapter.get_recent_executions(limit=10)
# recent[0] has most recent timestamp
# recent[-1] has oldest timestamp
```

### Status Filtering

All status values are lowercase for consistency:
- "success" (not "SUCCESS" or "Success")
- "failed" (not "FAILED")
- "blocked" (not "BLOCKED")

### Confidence Scores

Always float between 0.0 and 1.0:
- 0.95 means 95% confidence
- Use `confidence >= threshold` for filtering

### Severity Levels

Standardized severity tiers:
- "low"
- "medium"
- "high"
- "critical"

## Performance Considerations

### Caching

Adapters do NOT cache data. Each call reads from disk:
- Ensures fresh data
- No stale state issues
- Minimal memory footprint

### Large Files

For large `tool_execution_log.jsonl` files:
- Use `limit` parameter to cap results
- Default limit: 50 entries
- Each entry parsed individually

### Thread Safety

Frozen dataclasses are thread-safe. Multiple threads can safely read from adapters.

## Error Handling

### Missing Files

If Phase 24 output file doesn't exist:
```python
adapter.get_recent_executions()
# Returns: [] (empty list, no exception)
```

### Corrupted JSON

If file contains invalid JSON:
```python
# Line is skipped, reading continues
# Valid lines are processed
# Invalid lines are logged (if debug enabled)
```

### Partial Data

If Phase 24 process is still writing:
```python
# Adapter reads what's available
# No waiting or blocking
# Fresh read on next call
```

## Testing

Comprehensive test suite in `phase24_integration_tests.py`:

- **Unit Tests**: Each adapter tested independently
- **Integration Tests**: Full workflow with all adapters
- **Safety Tests**: Immutability and exception handling verified
- **Fixture Tests**: Mock Phase 24 files for testing

Run tests:
```bash
pytest phase24_integration_tests.py -v
```

## Future Enhancements

### Potential Extensions

1. **Real-time Streaming**: WebSocket updates instead of polling
2. **Historical Analysis**: Time-series aggregation
3. **Predictive Analytics**: Pattern-based forecasting
4. **Custom Summaries**: User-defined aggregations
5. **Export Formats**: CSV, Parquet, Protocol Buffers

### Backwards Compatibility

All changes will maintain:
- Existing adapter method signatures
- Frozen dataclass structure
- Read-only constraint
- Exception safety

## Troubleshooting

### No Phase 24 Data Appearing

1. Verify Phase 24 output files exist in expected location
2. Check file permissions (readable by dashboard process)
3. Verify JSON format is valid
4. Check dashboard logs for exception details

### Stale Data in Widgets

- Phase 24 widgets refresh automatically per schedule
- Manual refresh: Navigate away and back to dashboard
- Force re-read: Restart dashboard_app

### High Memory Usage

- Check size of `tool_execution_log.jsonl`
- Use `limit` parameter to reduce data loaded
- Archive old log files

## Reference

### File Paths

Default Phase 24 output location:
```
./outputs/phase24/
├── tool_execution_log.jsonl
├── execution_state_transitions.jsonl
├── system_health.json
├── rollback_events.jsonl
├── tool_conflicts.json
└── learning_signals.jsonl
```

### Data Flow Diagram

```
Phase 24 Orchestrator (EXECUTION)
    ↓ (read-only)
Phase 24 Output Files (OBSERVATION)
    ↓ (immutable)
Phase 24 Adapters (READ-ONLY)
    ↓ (aggregation)
Dashboard Widgets (DISPLAY)
```

### Execution Modes

Phase 24 tracks execution in four modes:

| Mode | Purpose | Tool Execution | Side Effects |
|------|---------|---------------|----|
| MOCK | Testing | Simulated | None |
| DRY_RUN | Validation | Preview only | None |
| LIVE | Production | Real | Yes |
| LOCKED | Maintenance | Blocked | None |

## Summary

Phase 24 Integration provides comprehensive observability of the autonomous tool orchestration system through **purely read-only, immutable adapters** that guarantee:

✅ **Zero Side Effects** - No mutations or state changes  
✅ **Safety Guarantee** - Frozen dataclasses prevent modifications  
✅ **Graceful Degradation** - Missing files don't break dashboards  
✅ **Exception Safety** - All errors handled gracefully  
✅ **Deterministic Behavior** - Consistent, predictable results  

All dashboards can now display orchestration context, execution patterns, and system health while maintaining complete separation from the execution layer.
