# Operator Control Schema

**Status**: ✅ **SAFETY-FIRST CONTROLS WITH FULL AUDIT TRAIL**

---

## Objective

Enable operator-level safety controls with manual approval and complete observability.

**Key Principles**:
- ✅ NO auto-execution (manual approval only)
- ✅ Full audit trail (every action logged)
- ✅ Approval workflow (submit → approve/reject → execute)
- ✅ Domain safety (lock mechanism with expiration)

---

## Control Actions

### 1. Pause Mission

**Purpose**: Pause a running mission without termination  
**Status**: Active mission → Paused state  
**Approval**: REQUIRED  
**Reversible**: YES (can resume)

**Schema**:
```python
PauseMissionControl.create(
    operator_id="op-alice-001",
    mission_id="mission-abc123",
    reason="High error rate detected in selector attempts"
)
```

**Workflow**:
```
1. Operator submits pause request
   ↓
2. System awaits approval (PENDING)
   ↓
3. Approver reviews reason → APPROVED
   ↓
4. System pauses mission
   ↓
5. Mission state: PAUSED
6. Can be resumed later with ResumeMissionControl
```

**Audit Trail**:
```
control_submitted: pause_mission for mission-abc123
  operator_id: op-alice-001
  reason: "High error rate detected in selector attempts"
  
control_approved: pause_mission for mission-abc123
  approver_id: op-bob-001
  approval_reason: "Confirmed high error rate, pausing approved"
  
mission_paused: mission-abc123
  operator_id: op-bob-001 (executor)
  timestamp: 2026-02-07T15:45:30Z
```

---

### 2. Kill Mission

**Purpose**: Terminate a mission immediately  
**Status**: Any state → Killed  
**Approval**: REQUIRED (critical action)  
**Reversible**: NO (creates artifacts from partial progress)  
**Severity**: CRITICAL

**Schema**:
```python
KillMissionControl.create(
    operator_id="op-alice-001",
    mission_id="mission-abc123",
    reason="Security incident: unauthorized data access attempt"
)
```

**Workflow**:
```
1. Operator submits kill request with critical reason
   ↓
2. System flags as critical (AWAITING_APPROVAL)
   ↓
3. Approver reviews (elevated scrutiny for critical actions)
   ↓
4. If APPROVED: System kills mission + finalizes artifacts
   ↓
5. Mission state: KILLED
6. ResponseEnvelope generated with partial artifacts
7. Cannot be resumed (terminal state)
```

**Result**:
- Mission execution stops immediately
- Any in-progress operations are halted
- Partial artifacts are captured and returned
- ResponseEnvelope reflects final state
- Full audit trail preserved

**Audit Trail**:
```
control_submitted: kill_mission for mission-abc123
  operator_id: op-alice-001
  reason: "Security incident: unauthorized data access attempt"
  severity: "critical"
  
control_approved: kill_mission for mission-abc123
  approver_id: op-security-001
  approval_reason: "Confirmed security incident, immediate termination approved"
  
mission_killed: mission-abc123
  operator_id: op-security-001 (executor)
  timestamp: 2026-02-07T15:46:00Z
  final_artifacts: [artifact-1, artifact-2]  # Partial results
```

---

### 3. Promote Forecast → Mission

**Purpose**: Manually promote a forecast to a live mission  
**Status**: Forecast → Mission (manual only)  
**Approval**: REQUIRED  
**Reversible**: NO (mission is live)  
**Constraint**: NO automatic promotion

**Schema**:
```python
PromoteForecastControl.create(
    operator_id="op-alice-001",
    forecast_id="forecast-xyz789",
    reason="Forecast validation passed, ready for production",
    mission_params={
        "priority": "high",
        "timeout_seconds": 3600,
        "retry_count": 3,
    }
)
```

**Workflow**:
```
1. Operator reviews forecast predictions
   ↓
2. Operator submits promotion request with parameters
   ↓
3. System awaits approval (PENDING)
   ↓
4. Approver validates forecast + parameters
   ↓
5. If APPROVED: System creates mission from forecast
   ↓
6. Mission state: CREATED (queued for execution)
7. Execution begins after approval (not before)
8. ResponseEnvelope created for new mission
```

**Parameters** (operator-controlled):
```json
{
  "priority": "high|normal|low",
  "timeout_seconds": 3600,
  "retry_count": 3,
  "max_retries_per_selector": 5,
  "allowed_domains": ["competitor-site.com"],
  "blocked_domains": [],
  "rate_limit_delay_ms": 1000
}
```

**NO Automatic Promotion**:
- ✅ Operator manually decides
- ❌ NO auto-promotion based on confidence score
- ❌ NO auto-promotion based on validation results
- ❌ NO autonomous workflow

**Audit Trail**:
```
control_submitted: promote_forecast for forecast-xyz789
  operator_id: op-alice-001
  reason: "Forecast validation passed, ready for production"
  mission_params: {...}
  
control_approved: promote_forecast for forecast-xyz789
  approver_id: op-bob-001
  approval_reason: "Forecast validated, parameters reviewed"
  new_mission_id: "mission-new-001"
  
forecast_promoted: forecast-xyz789 → mission-new-001
  operator_id: op-bob-001 (executor)
  timestamp: 2026-02-07T16:00:00Z
```

---

### 4. Lock Domain

**Purpose**: Prevent missions from accessing a domain  
**Status**: Domain → Locked  
**Approval**: REQUIRED  
**Reversible**: YES (unlock)  
**Duration**: Operator-specified (hours)  
**Auto-expiration**: YES

**Schema**:
```python
LockDomainControl.create(
    operator_id="op-alice-001",
    domain="competitor-api.com",
    reason="Rate limit exceeded, maintenance window expected",
    duration_hours=4
)
```

**Reasons** (common):
- `"rate limit exceeded"` - Temporary block to avoid blocks
- `"maintenance window"` - Planned downtime
- `"security incident"` - Unauthorized access detected
- `"domain unreachable"` - Service unavailable
- `"policy violation"` - Disabled per company policy

**Workflow**:
```
1. Operator detects issue with domain
   ↓
2. Operator submits lock request with duration
   ↓
3. System awaits approval (PENDING)
   ↓
4. Approver reviews reason + duration
   ↓
5. If APPROVED: System creates domain lock
   ↓
6. Domain locked for specified duration
7. All missions blocked from accessing domain
8. Lock auto-expires after duration elapsed
9. Can be manually unlocked earlier
```

**Lock Enforcement**:
```
Before mission accesses domain:
  ├── Check domain lock status
  ├── If locked + active: BLOCK mission
  ├── If locked + expired: REMOVE lock, allow mission
  └── If not locked: Allow mission
```

**Lock Info**:
```python
lock = DomainLock(
    domain="competitor-api.com",
    locked_at=datetime.utcnow(),
    locked_by="op-alice-001",
    locked_until=datetime.utcnow() + timedelta(hours=4),
    reason="Rate limit exceeded, maintenance window expected",
    lock_id="lock-abc123"
)

lock.is_active()  # True
lock.time_remaining()  # timedelta(hours=3, minutes=45)
```

**Audit Trail**:
```
control_submitted: lock_domain for competitor-api.com
  operator_id: op-alice-001
  reason: "Rate limit exceeded, maintenance window expected"
  duration_hours: 4
  
control_approved: lock_domain for competitor-api.com
  approver_id: op-bob-001
  approval_reason: "Rate limit issue confirmed, 4-hour lock approved"
  
domain_locked: competitor-api.com
  operator_id: op-bob-001 (executor)
  locked_until: 2026-02-07T20:00:00Z
  timestamp: 2026-02-07T16:00:00Z
```

---

### 5. Unlock Domain (Lower Priority)

**Purpose**: Remove lock from a domain  
**Status**: Locked domain → Unlocked  
**Approval**: NOT REQUIRED (lower priority)  
**Reversible**: YES (can re-lock)

**Schema**:
```python
UnlockDomainControl.create(
    operator_id="op-alice-001",
    domain="competitor-api.com",
    reason="Maintenance complete, service restored"
)
```

**Workflow**:
```
1. Operator confirms domain issue resolved
   ↓
2. Operator submits unlock request
   ↓
3. System auto-approves (no approval required)
   ↓
4. System removes domain lock
   ↓
5. Domain accessible to missions again
```

---

### 6. Resume Mission (Lower Priority)

**Purpose**: Resume a paused mission  
**Status**: Paused → Running  
**Approval**: NOT REQUIRED (lower priority)  
**Reversible**: YES (can pause again)

**Schema**:
```python
ResumeMissionControl.create(
    operator_id="op-alice-001",
    mission_id="mission-abc123",
    reason="Pause issue resolved, resuming execution"
)
```

---

## Approval Workflow

### Actions Requiring Approval
✅ PAUSE_MISSION  
✅ KILL_MISSION (critical)  
✅ PROMOTE_FORECAST  
✅ LOCK_DOMAIN  

### Actions NOT Requiring Approval
✅ RESUME_MISSION  
✅ UNLOCK_DOMAIN  

### Approval Process

```
1. SUBMIT (operator)
   ├── Create control request
   ├── Operator provides reason
   └── Request stored with PENDING status

2. REVIEW (approver - must be different operator)
   ├── View control request
   ├── Review operator's reason
   ├── Review action parameters
   └── Make approval decision

3. DECISION (approver)
   ├── APPROVE with reason
   │   └── Request moved to AWAITING_EXECUTION
   ├── REJECT with reason
   │   └── Request marked REJECTED, no execution
   └── (no auto-timeout, requires explicit decision)

4. EXECUTE (can be same as operator or different)
   ├── Execute control action
   ├── Log result
   └── Request marked EXECUTED
```

**Key Constraints**:
- ✅ Operator cannot approve own control
- ✅ All decisions require explicit reason
- ✅ No automatic timeouts or defaults
- ✅ Complete audit trail of all decisions

---

## Audit Log Examples

### Example 1: Pause Mission (Approved)

**Scenario**: High error rate detected, operator pauses for investigation

```json
{
  "event_id": "audit-001",
  "event_type": "control_submitted",
  "timestamp": "2026-02-07T15:40:00Z",
  "operator_id": "op-alice-001",
  "action_context": {
    "action": "pause_mission",
    "target_id": "mission-abc123",
    "reason": "High error rate in selector attempts (98% failures)",
    "details": {
      "error_count": 98,
      "success_count": 2,
      "error_types": ["selector_not_found", "timeout"]
    }
  }
}
```

```json
{
  "event_id": "audit-002",
  "event_type": "control_approved",
  "timestamp": "2026-02-07T15:42:00Z",
  "operator_id": "op-bob-001",
  "approver_id": "op-bob-001",
  "approval_timestamp": "2026-02-07T15:42:00Z",
  "approval_reason": "Confirmed high error rate in logs, pause is appropriate",
  "action_context": {
    "request_id": "audit-001",
    "target_id": "mission-abc123",
    "action": "pause_mission"
  }
}
```

```json
{
  "event_id": "audit-003",
  "event_type": "mission_paused",
  "timestamp": "2026-02-07T15:42:30Z",
  "operator_id": "op-bob-001",
  "executed": true,
  "execution_timestamp": "2026-02-07T15:42:30Z",
  "execution_result": {
    "status": "paused",
    "paused_at": "2026-02-07T15:42:30Z",
    "progress_at_pause": 45,
    "artifacts_created": ["artifact-1", "artifact-2"]
  },
  "action_context": {
    "target_id": "mission-abc123",
    "action": "pause_mission",
    "reason": "High error rate in selector attempts (98% failures)"
  }
}
```

---

### Example 2: Kill Mission (Critical Action)

**Scenario**: Security incident - unauthorized data access detected

```json
{
  "event_id": "audit-004",
  "event_type": "control_submitted",
  "timestamp": "2026-02-07T15:50:00Z",
  "operator_id": "op-alice-001",
  "action_context": {
    "action": "kill_mission",
    "target_id": "mission-sec-001",
    "reason": "SECURITY INCIDENT: Unauthorized data access detected in ResponseEnvelope",
    "details": {
      "severity": "critical",
      "description": "Mission attempted to access restricted fields in competitor database",
      "detected_at": "2026-02-07T15:49:45Z",
      "field_accessed": "customer_credit_cards"
    }
  }
}
```

```json
{
  "event_id": "audit-005",
  "event_type": "control_approved",
  "timestamp": "2026-02-07T15:50:30Z",
  "operator_id": "op-security-001",
  "approver_id": "op-security-001",
  "approval_timestamp": "2026-02-07T15:50:30Z",
  "approval_reason": "Confirmed security incident: unauthorized field access. Immediate termination APPROVED. Security team notified.",
  "action_context": {
    "request_id": "audit-004",
    "target_id": "mission-sec-001",
    "action": "kill_mission"
  }
}
```

```json
{
  "event_id": "audit-006",
  "event_type": "mission_killed",
  "timestamp": "2026-02-07T15:50:45Z",
  "operator_id": "op-security-001",
  "executed": true,
  "execution_timestamp": "2026-02-07T15:50:45Z",
  "execution_result": {
    "status": "killed",
    "killed_at": "2026-02-07T15:50:45Z",
    "reason": "Security incident",
    "final_artifacts": [
      {
        "id": "artifact-1",
        "type": "partial_extraction",
        "safe": true
      }
    ],
    "data_discarded": [
      {
        "field": "customer_credit_cards",
        "reason": "Unauthorized access, purged from artifacts"
      }
    ]
  },
  "action_context": {
    "target_id": "mission-sec-001",
    "action": "kill_mission",
    "reason": "SECURITY INCIDENT: Unauthorized data access detected"
  }
}
```

---

### Example 3: Promote Forecast (Manual Only)

**Scenario**: Forecast validated, operator decides to promote to production

```json
{
  "event_id": "audit-007",
  "event_type": "control_submitted",
  "timestamp": "2026-02-07T16:00:00Z",
  "operator_id": "op-alice-001",
  "action_context": {
    "action": "promote_forecast",
    "target_id": "forecast-xyz789",
    "reason": "Forecast validation completed: 94% accuracy on validation set, ready for production",
    "details": {
      "forecast_id": "forecast-xyz789",
      "confidence_score": 0.94,
      "validation_samples": 1000,
      "success_rate": 0.94,
      "estimated_competitors": 47,
      "mission_params": {
        "priority": "high",
        "timeout_seconds": 3600,
        "retry_count": 3,
        "rate_limit_delay_ms": 2000
      }
    }
  }
}
```

```json
{
  "event_id": "audit-008",
  "event_type": "control_approved",
  "timestamp": "2026-02-07T16:05:00Z",
  "operator_id": "op-bob-001",
  "approver_id": "op-bob-001",
  "approval_timestamp": "2026-02-07T16:05:00Z",
  "approval_reason": "Forecast validation verified: 94% accuracy confirmed. Mission parameters reviewed and appropriate. Promotion APPROVED.",
  "action_context": {
    "request_id": "audit-007",
    "target_id": "forecast-xyz789",
    "action": "promote_forecast"
  }
}
```

```json
{
  "event_id": "audit-009",
  "event_type": "forecast_promoted",
  "timestamp": "2026-02-07T16:05:15Z",
  "operator_id": "op-bob-001",
  "executed": true,
  "execution_timestamp": "2026-02-07T16:05:15Z",
  "execution_result": {
    "status": "promoted",
    "new_mission_id": "mission-prod-001",
    "promoted_at": "2026-02-07T16:05:15Z",
    "execution_status": "queued"
  },
  "action_context": {
    "forecast_id": "forecast-xyz789",
    "new_mission_id": "mission-prod-001",
    "action": "promote_forecast",
    "reason": "Forecast validation completed: 94% accuracy on validation set, ready for production"
  }
}
```

---

### Example 4: Lock Domain (Rate Limit)

**Scenario**: Rate limit exceeded on competitor API

```json
{
  "event_id": "audit-010",
  "event_type": "control_submitted",
  "timestamp": "2026-02-07T16:10:00Z",
  "operator_id": "op-alice-001",
  "action_context": {
    "action": "lock_domain",
    "target_id": "competitor-api.com",
    "reason": "Rate limit exceeded: 429 responses received. Maintenance window expected 2-4 hours.",
    "details": {
      "domain": "competitor-api.com",
      "duration_hours": 3,
      "error_status": 429,
      "requests_blocked": 24,
      "rate_limit_reset_at": "2026-02-07T19:00:00Z"
    }
  }
}
```

```json
{
  "event_id": "audit-011",
  "event_type": "control_approved",
  "timestamp": "2026-02-07T16:11:00Z",
  "operator_id": "op-bob-001",
  "approver_id": "op-bob-001",
  "approval_timestamp": "2026-02-07T16:11:00Z",
  "approval_reason": "Rate limit issue confirmed in logs. 3-hour lock appropriate for expected maintenance window.",
  "action_context": {
    "request_id": "audit-010",
    "target_id": "competitor-api.com",
    "action": "lock_domain"
  }
}
```

```json
{
  "event_id": "audit-012",
  "event_type": "domain_locked",
  "timestamp": "2026-02-07T16:11:15Z",
  "operator_id": "op-bob-001",
  "executed": true,
  "execution_timestamp": "2026-02-07T16:11:15Z",
  "execution_result": {
    "status": "locked",
    "lock_id": "lock-001",
    "locked_until": "2026-02-07T19:11:15Z",
    "active_missions_affected": 3
  },
  "action_context": {
    "target_id": "competitor-api.com",
    "action": "lock_domain",
    "reason": "Rate limit exceeded: 429 responses received. Maintenance window expected 2-4 hours.",
    "duration_hours": 3
  }
}
```

---

### Example 5: Audit Report

**Scenario**: Generate summary of all operator controls over past 7 days

```json
{
  "report_generated_at": "2026-02-07T20:00:00Z",
  "period": {
    "start": "2026-02-01T00:00:00Z",
    "end": "2026-02-07T20:00:00Z",
    "days": 7
  },
  "total_events": 127,
  "event_breakdown": {
    "control_submitted": 32,
    "control_approved": 28,
    "control_rejected": 4,
    "control_executed": 28,
    "control_failed": 0,
    "mission_paused": 8,
    "mission_killed": 1,
    "mission_resumed": 7,
    "domain_locked": 12,
    "domain_unlocked": 11,
    "forecast_promoted": 3
  },
  "operators_involved": 6,
  "operators": {
    "op-alice-001": 35,
    "op-bob-001": 42,
    "op-charlie-001": 18,
    "op-dave-001": 12,
    "op-security-001": 15,
    "op-eva-001": 5
  },
  "approval_metrics": {
    "submissions_requiring_approval": 32,
    "approvals": 28,
    "rejections": 4,
    "approval_rate": 0.875,
    "avg_approval_time_minutes": 2.4,
    "critical_approvals": 1,
    "critical_approval_time_minutes": 0.5
  },
  "control_actions": {
    "pause_mission": {
      "submitted": 12,
      "approved": 11,
      "rejected": 1,
      "executed": 11
    },
    "kill_mission": {
      "submitted": 1,
      "approved": 1,
      "executed": 1,
      "severity": "critical"
    },
    "promote_forecast": {
      "submitted": 3,
      "approved": 3,
      "executed": 3
    },
    "lock_domain": {
      "submitted": 12,
      "approved": 11,
      "rejected": 1,
      "executed": 12
    }
  },
  "failed_controls": 0,
  "security_incidents": 1,
  "incidents_resolved": 1
}
```

---

## Integration with ResponseEnvelope & Whiteboard

### Control Impact on ResponseEnvelope

When a mission is killed, the final ResponseEnvelope reflects:

```python
response_envelope = ResponseEnvelope(
    response_type=ResponseType.MISSION_COMPLETED,
    missions_spawned=[
        {
            "mission_id": "mission-abc123",
            "status": "killed",  # NOT "completed"
            "reason": "Operator control: Security incident",
            "killed_by": "op-security-001",
            "killed_at": "2026-02-07T15:50:45Z",
        }
    ],
    artifacts=[
        # Only safe artifacts included
        {"id": "artifact-1", "type": "partial_extraction", ...},
    ],
    signals_emitted=[
        # All events including kill signal
        {"id": "signal-1", ...},
        {"id": "signal-kill", "type": "mission_killed", ...},
    ],
    ui_hints={
        "control_action": "kill_mission",
        "operator_message": "Mission terminated due to security incident"
    }
)
```

### Whiteboard Display

Whiteboard shows control history and final state:

```python
whiteboard_view = WhiteboardMissionView(
    mission_id="mission-abc123",
    objective="Extract competitor pricing",
    status="killed",  # Final state
    artifacts=[...],  # Partial results
    signals=[...],    # All signals including kill event
    timeline=[        # Complete timeline with control events
        {"seq": 1, "event": "mission_start", "time": "15:30:45"},
        ...
        {"seq": N-1, "event": "mission_killed", "time": "15:50:45"},
        {"seq": N, "event": "operator_control", "actor": "op-security-001"},
    ],
    metrics={...},
    control_metadata={
        "killed_by": "op-security-001",
        "kill_reason": "SECURITY INCIDENT: Unauthorized data access",
        "audit_trail_available": True,
    }
)
```

---

## Security & Compliance

### Audit Trail Guarantees

✅ **Immutable**: Events never modified after creation  
✅ **Complete**: Every action logged (submit, approve, execute)  
✅ **Traceable**: All actors identified (operator, approver, executor)  
✅ **Timestamped**: UTC timestamps on all events  
✅ **Exportable**: Full log exportable to JSON for external audit  
✅ **Queryable**: Search by operator, target, type, time range

### Separation of Concerns

✅ **Operator**: Submits control request  
✅ **Approver**: Reviews and approves/rejects (must be different operator)  
✅ **Executor**: Performs the action (can be approver)  
✅ **Auditor**: Reviews logs (read-only access)

### Critical Actions

**KILL_MISSION** triggers:
- ✅ Extra scrutiny on approval
- ✅ Security team notification
- ✅ Data sanitization (remove unauthorized fields)
- ✅ Permanent audit log entry
- ✅ Non-reversible termination

---

## API Endpoints

### Submit Control Request
```
POST /api/controls/request
{
  "action": "pause_mission|kill_mission|promote_forecast|lock_domain",
  "target_id": "mission-id or domain or forecast-id",
  "reason": "Human-readable reason",
  "details": {...}
}
Response: {"request_id": "..."}
```

### Get Pending Approvals
```
GET /api/controls/pending-approvals
Response: [ControlRequest, ...]
```

### Approve Control Request
```
POST /api/controls/{request_id}/approve
{
  "approval_reason": "Reason for approval"
}
Response: {"status": "approved"}
```

### Reject Control Request
```
POST /api/controls/{request_id}/reject
{
  "rejection_reason": "Reason for rejection"
}
Response: {"status": "rejected"}
```

### Get Audit Log
```
GET /api/audit-log?start_time=...&end_time=...&operator_id=...&action=...
Response: [AuditEvent, ...]
```

### Export Audit Log
```
GET /api/audit-log/export?format=json
Response: File download
```

---

## Files

| File | Purpose |
|------|---------|
| [backend/operator_controls.py](backend/operator_controls.py) | Control schema, approval workflow, domain locks |
| [backend/operator_audit_log.py](backend/operator_audit_log.py) | Immutable audit trail, event logging |

---

## Status: ✅ COMPLETE

- ✅ 6 control actions defined (4 require approval, 2 don't)
- ✅ Approval workflow (submit → approve/reject → execute)
- ✅ NO auto-execution (manual only)
- ✅ Full audit trail (immutable events)
- ✅ Domain locks with auto-expiration
- ✅ Forecast promotion (manual only, no auto)
- ✅ Integration with ResponseEnvelope & Whiteboard
- ✅ Security incident handling (kill mission)
- ✅ Operator accountability (full traceability)
- ✅ Exportable audit logs
- ✅ All constraints satisfied

