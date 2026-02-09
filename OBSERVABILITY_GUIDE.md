# System Observability - Complete Guide

## Overview

The observability layer adds end-to-end tracing to Buddy's chat system without changing any behavior. Every chat request generates:

1. **Unique trace_id** - Attached to all downstream objects and logs
2. **Decision traces** - Records of every decision point (classification, routing, shortcuts)
3. **Duplicate detection** - Guards against repeated messages
4. **Query APIs** - Retrieve full execution traces for debugging

## Architecture Components

### 1. Trace Context Flow

```
POST /chat/integrated
  ↓
Generate trace_id (UUID)
  ↓
Create ChatMessage(trace_id=...)
  ↓
ChatSessionHandler.handle_message()
  ↓
orchestrate_message(trace_id=...)
  ↓
Intent Classification (log to decision_traces.jsonl)
  ↓
Routing Decision (log to decision_traces.jsonl)
  ↓
Handler Execution
  ↓
Return ResponseEnvelope + trace_id in JSON
```

### 2. Decision Traces

**File**: `outputs/debug/decision_traces.jsonl`

Each line is a JSON record capturing a decision point:

```json
{
  "decision_point": "intent_classification",
  "trace_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "timestamp": "2026-02-07T15:30:45.123456",
  "input_message": "Calculate 100 + 50",
  "chosen_intent": "request_execution",
  "confidence": 0.85,
  "keyword_analysis": {
    "execute_keywords": 1,
    "math_keywords": 2
  },
  "reasoning": "Selected request_execution with confidence 0.85"
}
```

**Decision Point Types**:
- `intent_classification` - When message intent is determined
- `routing` - When handler is selected
- `deterministic_shortcut` - When math/deterministic path is taken
- `mission_creation` - When mission is created

### 3. Duplicate Detection

**File**: `outputs/debug/duplicates.jsonl`

Catches messages sent twice within 500ms:

```json
{
  "event": "duplicate_detected",
  "timestamp": "2026-02-07T15:30:45.600000",
  "session_id": "chat_abc123",
  "message_hash": "a1b2c3d4e5f6g7h8",
  "message": "Get product prices from example.com",
  "current_trace_id": "current-uuid",
  "previous_trace_id": "previous-uuid",
  "elapsed_ms": 250,
  "action": "dropped"
}
```

## Query APIs

### Get Execution Trace

**Endpoint**: `GET /api/debug/trace/{trace_id}`

Returns all decision points for a single request.

**Example**:
```bash
curl http://localhost:8000/api/debug/trace/12345678-1234-1234-1234-123456789012
```

**Response**:
```json
{
  "trace_id": "12345678-1234-1234-1234-123456789012",
  "decision_points": [
    {
      "decision_point": "intent_classification",
      "chosen_intent": "request_execution",
      "confidence": 0.85,
      "reasoning": "Selected request_execution with confidence 0.85"
    },
    {
      "decision_point": "routing",
      "chosen_handler": "execute",
      "reasoning": "Routed request_execution to handler execute"
    },
    {
      "decision_point": "deterministic_shortcut",
      "shortcut_type": "math_calculation",
      "result_summary": "150"
    }
  ],
  "summary": "Intent: request_execution (0.85) → Routed to: execute → Shortcut: math_calculation"
}
```

### Get Duplicate Detection Records

**Endpoint**: `GET /api/debug/duplicates`

Returns recent duplicate message detections.

**Example**:
```bash
curl http://localhost:8000/api/debug/duplicates
```

**Response**:
```json
{
  "total_duplicates": 3,
  "recent_duplicates": [
    {
      "timestamp": "2026-02-07T15:30:45.600000",
      "session_id": "chat_abc123",
      "elapsed_ms": 250,
      "action": "dropped"
    }
  ]
}
```

## Using Traces for Debugging

### Scenario 1: "Why didn't my request create a mission?"

**Steps**:
1. Get trace_id from `/chat/integrated` response
2. Query `/api/debug/trace/{trace_id}`
3. Check `decision_points` array:
   - Did intent classification select `request_execution`?
   - Did routing select `execute` handler?
   - Was there a `deterministic_shortcut` instead?
   - Did `mission_creation` appear?

**Example Investigation**:
```bash
# Response had trace_id: "abc123"
curl http://localhost:8000/api/debug/trace/abc123

# Trace shows:
# {
#   "decision_points": [
#     {"decision_point": "intent_classification", "chosen_intent": "question", ...},
#     {"decision_point": "routing", "chosen_handler": "respond", ...}
#   ]
# }
# → Intent was classified as "question", not "request_execution"
# → Went to respond handler instead of execute
# → This is why no mission was created
```

### Scenario 2: "The same message was sent twice, why?"

**Steps**:
1. Check `/api/debug/duplicates`
2. Look for `session_id` and `elapsed_ms`
3. Duplicate was detected and dropped if `elapsed_ms < 500`

### Scenario 3: "Why was deterministic math used instead of creating a mission?"

**Query the trace**:
```json
{
  "decision_point": "deterministic_shortcut",
  "shortcut_type": "math_calculation",
  "reasoning": "Took math_calculation shortcut (no mission created)"
}
```

This record indicates the system correctly identified pure math and answered directly.

## File Locations

```
outputs/
├── debug/
│   ├── decision_traces.jsonl      # All classification/routing/shortcut decisions
│   └── duplicates.jsonl            # Duplicate message detections
├── phase25/
│   ├── learning_signals.jsonl      # All signals (missions, chat observations, etc)
│   └── missions.jsonl              # Mission records
```

## Grep Patterns

### Find all traces for a specific session

```bash
grep "session_id.*chat_abc123" outputs/debug/decision_traces.jsonl
```

### Find all classifications with low confidence

```bash
grep "confidence.*0\.[0-4]" outputs/debug/decision_traces.jsonl
```

### Find all deterministic shortcuts

```bash
grep "deterministic_shortcut" outputs/debug/decision_traces.jsonl
```

### Find all duplicates in last 5 minutes

```bash
grep "duplicate_detected" outputs/debug/duplicates.jsonl | tail -20
```

### Get complete trace for a message

```bash
TRACE_ID="abc-def-123"
grep "$TRACE_ID" outputs/debug/decision_traces.jsonl
```

## Integration with Existing Systems

### ✓ No Behavior Changes
- Intent classification works exactly as before
- Routing logic unchanged
- Mission creation logic unchanged
- Deterministic math detection unchanged
- All handlers behave identically

### ✓ Backward Compatible
- Existing endpoints work without modification
- trace_id is optional (generated if not provided)
- Trace queries are separate, non-blocking APIs
- Signal failures never affect response

### ✓ Append-Only Logging
- All traces written to JSONL (never modified)
- Perfect audit trail
- Can be rotated/archived independently

## Response Envelope Changes

Chat endpoint now returns trace_id:

```json
{
  "status": "success",
  "trace_id": "12345678-1234-1234-1234-123456789012",
  "chat_message_id": "msg_abc123",
  "session_id": "session_xyz789",
  "envelope": { ... }
}
```

**Note**: trace_id returned for client-side correlation with debug logs.

## Example: End-to-End Trace

### Request
```bash
curl -X POST http://localhost:8000/chat/integrated \
  -H "Content-Type: application/json" \
  -d '{"text": "Calculate 45 + 55", "session_id": "test_session"}'
```

### Response
```json
{
  "status": "success",
  "trace_id": "abcd1234-efgh5678-ijkl9012-mnop3456",
  "chat_message_id": "msg_xyz789",
  ...
}
```

### Query Trace
```bash
curl http://localhost:8000/api/debug/trace/abcd1234-efgh5678-ijkl9012-mnop3456
```

### Result
```json
{
  "trace_id": "abcd1234-efgh5678-ijkl9012-mnop3456",
  "decision_points": [
    {
      "decision_point": "intent_classification",
      "timestamp": "2026-02-07T15:30:45.123456",
      "input_message": "Calculate 45 + 55",
      "chosen_intent": "request_execution",
      "confidence": 0.85,
      "keyword_analysis": {"execute_keywords": 1, "math_keywords": 1},
      "reasoning": "Selected request_execution with confidence 0.85"
    },
    {
      "decision_point": "routing",
      "chosen_handler": "execute",
      "reasoning": "Routed request_execution to handler execute"
    },
    {
      "decision_point": "deterministic_shortcut",
      "shortcut_type": "math_calculation",
      "result_summary": "100"
    }
  ],
  "summary": "Intent: request_execution (0.85) → Routed to: execute → Shortcut: math_calculation"
}
```

## Monitoring & Maintenance

### Check Debug Files Size
```bash
ls -lh outputs/debug/
# Monitor file sizes to plan rotation
```

### Archive Old Traces
```bash
# Find traces older than 7 days
find outputs/debug/ -name "*.jsonl" -mtime +7 -exec ls -lh {} \;
```

### Clean Up Duplicates File
```bash
# Get count of duplicate detections
wc -l outputs/debug/duplicates.jsonl
```

## Summary

| Component | Purpose | Location | Query API |
|-----------|---------|----------|-----------|
| Decision Traces | Log all classification/routing/shortcut decisions | `outputs/debug/decision_traces.jsonl` | `GET /api/debug/trace/{trace_id}` |
| Duplicate Detection | Guard against repeated messages within 500ms | `outputs/debug/duplicates.jsonl` | `GET /api/debug/duplicates` |
| trace_id | Correlate requests across all systems | ResponseEnvelope + all signals | Returned in `/chat/integrated` response |

## Files Modified

1. **backend/observability.py** (NEW)
   - TraceContext class
   - DecisionTraceLogger class
   - DuplicateDetector class

2. **backend/chat_session_handler.py**
   - ChatMessage: Added trace_id field
   - ChatResponse: Added trace_id field
   - handle_message(): Pass trace_id to orchestrator

3. **backend/interaction_orchestrator.py**
   - process_message(): Accept trace_id, log classifications and routing
   - orchestrate_message(): Accept and pass through trace_id
   - _handle_execute(): Log deterministic shortcuts and mission creation
   - All handlers: Accept trace_id parameter

4. **backend/main.py**
   - /chat/integrated: Generate trace_id, check duplicates, return trace_id
   - /api/debug/trace/{trace_id}: Query execution traces
   - /api/debug/duplicates: Query duplicate detections

## Success Criteria

✅ **Traceability**: Can answer "Why did Buddy respond this way?" using logs alone
✅ **No Behavior Changes**: All intent classification and routing works identically  
✅ **Duplicate Guard**: Backend prevents repeated messages within 500ms
✅ **Query APIs**: Can retrieve complete execution traces via REST endpoints
✅ **Append-Only**: All traces logged to JSONL for perfect audit trail
✅ **Safety**: Signal failures never affect responses
