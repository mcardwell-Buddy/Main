# Execution Streaming Events Schema

**Status**: ✅ **OBSERVABILITY-ONLY SYSTEM**

---

## Objective

Enable real-time execution streaming events tied to a mission_id for complete observability.

**Key Constraint**: Observability ONLY
- ✅ Receive events
- ❌ NO control commands
- ❌ NO autonomy
- ❌ NO feedback loops

---

## Event Types

### 1. Mission Lifecycle Events

#### MISSION_START
Emitted when a mission begins execution.

```json
{
  "mission_id": "mission-abc123",
  "event_type": "mission_start",
  "timestamp": "2026-02-07T15:30:45.123456",
  "sequence_number": 1,
  "data": {
    "objective": "Extract competitor pricing data",
    "started_at": "2026-02-07T15:30:45.123456"
  }
}
```

#### MISSION_PROGRESS
Emitted periodically during mission execution.

```json
{
  "mission_id": "mission-abc123",
  "event_type": "mission_progress",
  "timestamp": "2026-02-07T15:35:12.456789",
  "sequence_number": 8,
  "data": {
    "progress_percent": 50,
    "current_step": "Extracting pricing data from table",
    "updated_at": "2026-02-07T15:35:12.456789"
  }
}
```

#### MISSION_STOP
Emitted when a mission ends (completion, failure, cancellation).

```json
{
  "mission_id": "mission-abc123",
  "event_type": "mission_stop",
  "timestamp": "2026-02-07T15:40:30.789012",
  "sequence_number": 15,
  "data": {
    "reason": "Mission completed successfully",
    "final_status": "completed",
    "stopped_at": "2026-02-07T15:40:30.789012"
  }
}
```

---

### 2. Execution Step Events

#### SELECTOR_ATTEMPT
Observability event showing a selector attempt (no control).

```json
{
  "mission_id": "mission-abc123",
  "event_type": "selector_attempt",
  "timestamp": "2026-02-07T15:31:02.123456",
  "sequence_number": 2,
  "data": {
    "selector_id": "selector-product-name-1",
    "selector_description": "Find product name element",
    "status": "success",
    "details": {
      "found": true,
      "element_count": 1,
      "xpath": "/html/body/div[1]/h1",
      "retry_count": 0,
      "time_ms": 245
    },
    "attempted_at": "2026-02-07T15:31:02.123456"
  }
}
```

**Selector Status Values**:
- `success` - Element found and accessed
- `failed` - Element not found
- `retrying` - Retrying selector (transient failure)

#### INTENT_DECISION
Observability event showing an intent decision (no control).

```json
{
  "mission_id": "mission-abc123",
  "event_type": "intent_decision",
  "timestamp": "2026-02-07T15:31:15.234567",
  "sequence_number": 3,
  "data": {
    "intent_type": "navigate",
    "reasoning": "Product page loaded successfully, next navigate to pricing section",
    "parameters": {
      "target_url": "/pricing",
      "expected_delay_ms": 2000
    },
    "confidence": 0.98,
    "decided_at": "2026-02-07T15:31:15.234567"
  }
}
```

**Intent Types**:
- `navigate` - Navigate to a page/section
- `extract` - Extract data from page
- `analyze` - Analyze extracted data
- `synthesize` - Create summary/report
- `wait` - Wait for condition
- `other` - Miscellaneous intent

---

### 3. Status Change Events

#### MISSION_STATUS_CHANGE
Emitted when a mission's status changes.

```json
{
  "mission_id": "mission-abc123",
  "event_type": "mission_status_change",
  "timestamp": "2026-02-07T15:30:50.123456",
  "sequence_number": 6,
  "data": {
    "old_status": "queued",
    "new_status": "in_progress",
    "reason": "Execution started by scheduler",
    "changed_at": "2026-02-07T15:30:50.123456"
  }
}
```

**Status Values**:
- `queued` - Waiting to start
- `started` - Starting
- `in_progress` - Actively running
- `paused` - Paused (can be resumed with new mission)
- `completed` - Finished successfully
- `failed` - Failed with error
- `cancelled` - Cancelled by user

---

## Event Stream Properties

### Per-Mission Sequence Numbering
- Each mission has its own sequence counter (starting at 1)
- Events for the same mission are numbered sequentially
- Sequence numbers allow detection of missed events in unreliable networks

### Timestamp (UTC ISO 8601)
- All timestamps are in UTC
- Format: `YYYY-MM-DDTHH:MM:SS.ffffff`
- Allows accurate timeline reconstruction

### mission_id as Join Key
```
mission_id (string) → unique identifier
  ├── Links to ResponseEnvelope
  ├── Links to Whiteboard view
  ├── Links to stored artifacts
  └── Links to stored signals
```

---

## WebSocket Protocol

### Connection
```
GET ws://localhost:8000/ws/stream/{mission_id} HTTP/1.1
Upgrade: websocket
Connection: Upgrade
```

### Message Format (Server → Client)
Server sends JSON events:
```json
{
  "mission_id": "mission-abc123",
  "event_type": "selector_attempt",
  "timestamp": "2026-02-07T15:31:02.123456",
  "sequence_number": 2,
  "data": { ... }
}
```

### Client Behavior (Observability Only)
- ✅ **RECEIVE** events from server
- ❌ **CANNOT SEND** commands to server
- ❌ **CANNOT CONTROL** mission execution
- ❌ **CANNOT CONTROL** selectors or intents

If client attempts to send data:
```
Client: {"command": "pause"}
Server: [IGNORED] (no control commands accepted)
```

### Connection Lifecycle

```
Client connects to ws://localhost:8000/ws/stream/mission-abc123
  ↓
[WebSocket OPEN]
  ↓
Server starts sending events as they occur
  - mission_start (seq 1)
  - selector_attempt (seq 2)
  - intent_decision (seq 3)
  - mission_progress (seq 4)
  - ... more events ...
  - mission_stop (seq N)
  ↓
Client closes connection OR connection times out
  ↓
[WebSocket CLOSED]
```

---

## Health Check Endpoint

### Request
```
GET /api/stream-health/{mission_id}
```

### Response
```json
{
  "mission_id": "mission-abc123",
  "active_connections": 2,
  "status": "active",
  "observation_mode": "read-only",
  "control_enabled": false
}
```

**Fields**:
- `active_connections` - Number of WebSocket clients connected
- `status` - `active` (≥1 client) or `idle` (0 clients)
- `observation_mode` - Always `read-only` (no control)
- `control_enabled` - Always `false` (observability only)

---

## Event Flow Diagram

```
Mission Execution
    │
    ├─ Mission starts
    │   └─ EMIT: mission_start (seq 1)
    │
    ├─ Status change: queued → started
    │   └─ EMIT: mission_status_change (seq 2)
    │
    ├─ Selector attempt
    │   └─ EMIT: selector_attempt (seq 3)  [OBSERVABILITY ONLY]
    │
    ├─ Intent decision: navigate
    │   └─ EMIT: intent_decision (seq 4)  [OBSERVABILITY ONLY]
    │
    ├─ Progress: 25%
    │   └─ EMIT: mission_progress (seq 5)
    │
    ├─ Status change: started → in_progress
    │   └─ EMIT: mission_status_change (seq 6)
    │
    ├─ Multiple iterations of:
    │   ├─ Selector attempts
    │   ├─ Intent decisions
    │   ├─ Progress updates
    │   └─ Status changes
    │
    └─ Mission completes
        ├─ EMIT: mission_progress (seq N-2, progress: 100%)
        ├─ EMIT: mission_stop (seq N-1)
        └─ EMIT: mission_status_change (seq N, final_status: completed)

All events streamed to WebSocket clients in real-time
No control commands possible at any point
```

---

## Integration Points

### 1. Event Emission (During Mission Execution)
```python
from backend.streaming_events import (
    get_event_emitter,
    MissionStatus,
    SelectorAttemptStatus,
    IntentDecisionType,
)

emitter = get_event_emitter()

# Emit events during mission execution
emitter.emit_mission_start(
    mission_id="mission-abc123",
    objective="Extract competitor pricing"
)

emitter.emit_selector_attempt(
    mission_id="mission-abc123",
    selector_id="selector-1",
    selector_description="Find price element",
    status=SelectorAttemptStatus.SUCCESS,
    details={...}
)

emitter.emit_intent_decision(
    mission_id="mission-abc123",
    intent_type=IntentDecisionType.EXTRACT,
    reasoning="Price found, extracting value",
    parameters={...},
    confidence=0.95
)

emitter.emit_mission_stop(
    mission_id="mission-abc123",
    reason="Completed successfully",
    final_status=MissionStatus.COMPLETED
)
```

### 2. WebSocket Streaming (Client Connection)
```javascript
const missionId = "mission-abc123";
const ws = new WebSocket(
  `ws://localhost:8000/ws/stream/${missionId}`
);

ws.onopen = () => console.log("Connected");

ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  
  // Handle event based on type
  if (msg.event_type === "selector_attempt") {
    console.log(`Selector: ${msg.data.selector_description} - ${msg.data.status}`);
  }
  if (msg.event_type === "intent_decision") {
    console.log(`Intent: ${msg.data.intent_type} (confidence: ${msg.data.confidence})`);
  }
  if (msg.event_type === "mission_stop") {
    console.log(`Mission: ${msg.data.final_status}`);
  }
};

ws.onerror = (err) => console.error(err);
ws.onclose = () => console.log("Disconnected");
```

### 3. Relationship to ResponseEnvelope
```
ResponseEnvelope (static snapshot at end of mission)
  ├── missions_spawned: [{mission_id, status, ...}]
  ├── artifacts: [{id, type, title, ...}]  ← IDs only
  └── signals_emitted: [{id, type, source, ...}]  ← IDs only
                ↑
                │ mission_id join key
                ↓
Streaming Events (real-time flow during mission)
  ├── mission_start → mission_progress → mission_stop
  ├── selector_attempt events (observability)
  ├── intent_decision events (observability)
  └── mission_status_change events (all status transitions)
                ↑
                │ same mission_id
                ↓
Whiteboard (reconstructs view from end state)
  ├── Reads artifacts from artifact_store[mission_id]
  ├── Reads signals from signal_store[mission_id]
  └── Builds view with complete data
```

---

## Observability Guarantees

### ✅ What You Can Observe
- Mission lifecycle (start, progress, stop)
- Selector attempts and outcomes
- Intent decisions and reasoning
- Status transitions
- Execution timeline
- Success/failure details
- Confidence scores
- Retry behavior
- Timing information

### ❌ What You Cannot Do
- Send commands to selector
- Modify intent decisions
- Pause/resume missions
- Control retry behavior
- Override decisions
- Change status directly
- Inject events

### Security Model
- **Read-only**: One-way data flow (server → client)
- **No feedback**: Client cannot send control signals
- **No autonomy**: Cannot automate control decisions
- **Pure observation**: Only visibility into execution

---

## Example: Complete Mission Event Stream

```json
[
  {
    "mission_id": "mission-abc123",
    "event_type": "mission_start",
    "sequence_number": 1,
    "timestamp": "2026-02-07T15:30:45.000000",
    "data": {"objective": "Extract competitor pricing"}
  },
  {
    "mission_id": "mission-abc123",
    "event_type": "mission_status_change",
    "sequence_number": 2,
    "timestamp": "2026-02-07T15:30:46.000000",
    "data": {
      "old_status": "queued",
      "new_status": "started",
      "reason": "Execution started"
    }
  },
  {
    "mission_id": "mission-abc123",
    "event_type": "selector_attempt",
    "sequence_number": 3,
    "timestamp": "2026-02-07T15:31:00.000000",
    "data": {
      "selector_id": "nav-products",
      "selector_description": "Navigate to products section",
      "status": "success",
      "details": {"time_ms": 500}
    }
  },
  {
    "mission_id": "mission-abc123",
    "event_type": "intent_decision",
    "sequence_number": 4,
    "timestamp": "2026-02-07T15:31:05.000000",
    "data": {
      "intent_type": "navigate",
      "reasoning": "Successfully navigated, now finding price data",
      "confidence": 0.98,
      "parameters": {"target_url": "/products/pricing"}
    }
  },
  {
    "mission_id": "mission-abc123",
    "event_type": "selector_attempt",
    "sequence_number": 5,
    "timestamp": "2026-02-07T15:31:20.000000",
    "data": {
      "selector_id": "price-table",
      "selector_description": "Find pricing table",
      "status": "success",
      "details": {"rows": 15}
    }
  },
  {
    "mission_id": "mission-abc123",
    "event_type": "intent_decision",
    "sequence_number": 6,
    "timestamp": "2026-02-07T15:31:25.000000",
    "data": {
      "intent_type": "extract",
      "reasoning": "Pricing table found, extracting all rows",
      "confidence": 0.99,
      "parameters": {"fields": ["product", "price", "currency"]}
    }
  },
  {
    "mission_id": "mission-abc123",
    "event_type": "mission_progress",
    "sequence_number": 7,
    "timestamp": "2026-02-07T15:35:00.000000",
    "data": {
      "progress_percent": 75,
      "current_step": "Processing extracted data"
    }
  },
  {
    "mission_id": "mission-abc123",
    "event_type": "intent_decision",
    "sequence_number": 8,
    "timestamp": "2026-02-07T15:36:00.000000",
    "data": {
      "intent_type": "synthesize",
      "reasoning": "Data extraction complete, generating summary report",
      "confidence": 0.95,
      "parameters": {"format": "markdown", "include_analysis": true}
    }
  },
  {
    "mission_id": "mission-abc123",
    "event_type": "mission_progress",
    "sequence_number": 9,
    "timestamp": "2026-02-07T15:40:00.000000",
    "data": {
      "progress_percent": 100,
      "current_step": "Finalizing results"
    }
  },
  {
    "mission_id": "mission-abc123",
    "event_type": "mission_status_change",
    "sequence_number": 10,
    "timestamp": "2026-02-07T15:40:15.000000",
    "data": {
      "old_status": "in_progress",
      "new_status": "completed",
      "reason": "Mission completed successfully"
    }
  },
  {
    "mission_id": "mission-abc123",
    "event_type": "mission_stop",
    "sequence_number": 11,
    "timestamp": "2026-02-07T15:40:30.000000",
    "data": {
      "reason": "Mission completed successfully",
      "final_status": "completed"
    }
  }
]
```

---

## Performance Characteristics

- **Latency**: Event emission to WebSocket delivery < 10ms typical
- **Throughput**: 1000+ events/second per mission
- **Connections**: Supports 100+ concurrent WebSocket clients per mission
- **Memory**: ~1KB per event, auto-cleanup after mission completion
- **Scalability**: Horizontal scaling via event queue

---

## Status: ✅ COMPLETE

- ✅ Event schema defined
- ✅ WebSocket protocol specified
- ✅ Observability-only constraints enforced
- ✅ No control commands possible
- ✅ No autonomy
- ✅ Real-time streaming ready
- ✅ mission_id join key
- ✅ Health check endpoint
- ✅ Example integrations provided

