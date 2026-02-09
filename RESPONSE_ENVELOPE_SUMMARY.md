# ResponseEnvelope Schema: Canonical Format
## Executive Summary

**Status**: ✅ **FINALIZED & PRODUCTION READY**

---

## What Is ResponseEnvelope?

The **canonical, UI-safe response format** for all Buddy outputs. It's a data contract between agent logic and UI rendering that contains:

- Human-readable messages
- Structured artifacts (tables, charts, documents, code, timelines)
- Mission references (proposed or executed)
- Signal references (navigation, extraction, synthesis events)
- Confidence metrics
- Status indicators
- Timestamps
- UI rendering hints

**Key Principle**: Pure data. No execution logic. No UI code.

---

## Core Fields

| Field | Type | Example |
|-------|------|---------|
| `response_type` | Enum | "text", "artifact_bundle", "report" |
| `summary` | String | "Found 50 quotes successfully" |
| `artifacts` | List[Artifact] | [table, chart, document, code, timeline, file] |
| `missions_spawned` | List[MissionRef] | [{mission_id, status, objective}] |
| `signals_emitted` | List[SignalRef] | [{signal_type, source, timestamp}] |
| `confidence` | Float 0.0-1.0 | 0.92 (via metadata) |
| `status` | String | "ok", "blocked", "failed", "noop" (via metadata) |
| `timestamp` | ISO 8601 | "2026-02-07T20:12:15.500000Z" |
| `ui_hints` | UIHints | {layout, priority, actions, icon} |
| `live_stream_id` | String (UUID) | "stream-abc-123" (for real-time updates) |

---

## Requirements Met

✅ **All requirements satisfied:**

1. ✅ Message text (human-readable summary)
2. ✅ Intent classification (optional via metadata)
3. ✅ Proposed missions (optional list)
4. ✅ Executed missions (optional via metadata)
5. ✅ Artifacts (0..n, 9 typed variants)
6. ✅ Signals emitted (IDs only, no heavy data)
7. ✅ Confidence (0.0-1.0, optional)
8. ✅ Status (ok|blocked|failed|noop, optional)
9. ✅ Timestamps (ISO 8601, auto-generated)

---

## Artifact Types (9 Variants)

All artifacts are **references only** — no heavy data blobs:

1. **TableArtifact** — Tabular data (columns, rows)
2. **ChartArtifact** — Visualizations (line, bar, pie, scatter)
3. **DocumentArtifact** — Multi-section reports (markdown)
4. **CodeBlockArtifact** — Code snippets (with language)
5. **TimelineArtifact** — Event sequences (with timestamps)
6. **FileReferenceArtifact** — File references (path, type, size)
7. **JSONDataArtifact** — Structured data (generic JSON)
8. **MissionDraftArtifact** — Mission details
9. **SignalBatchArtifact** — Signal summaries

---

## Three Example Scenarios

### Scenario A: No-Op (No Mission)
User asks a question → Agent responds with information → No mission created

**Response Type**: `TEXT`  
**Artifacts**: 0  
**Missions**: 0  
**Signals**: 0  
**Status**: Info message only

### Scenario B: Mission Proposed
User requests action → Intent classifier recognizes → Mission proposal created

**Response Type**: `ARTIFACT_BUNDLE`  
**Artifacts**: 0-1 (mission draft)  
**Missions**: 1 (status='proposed')  
**Signals**: 1 (mission_proposed)  
**Status**: Awaiting approval

### Scenario C: Mission Executed
Mission runs → Results returned with artifacts → Full summary with signals

**Response Type**: `ARTIFACT_BUNDLE`  
**Artifacts**: 3+ (table, document, timeline)  
**Missions**: 0 (already executed)  
**Signals**: 3+ (selector stats, completion, navigation)  
**Status**: ok (success)

---

## How To Use

### Creating a Response (Helper Functions)

```python
# Simple text response
from backend.response_envelope import text_response
response = text_response("Found 50 quotes")

# Mission proposal
from backend.response_envelope import mission_proposal_response, MissionReference
mission = MissionReference(mission_id="abc", status="proposed", ...)
response = mission_proposal_response(mission, "Creating mission...")

# Error
from backend.response_envelope import error_response
response = error_response("Navigation failed", {"reason": "timeout"})

# Complex response (builder)
from backend.response_envelope import ResponseBuilder
response = (ResponseBuilder()
    .type(ResponseType.ARTIFACT_BUNDLE)
    .summary("Mission completed!")
    .add_table("Results", columns=["A"], rows=[[1]])
    .add_mission(mission_ref)
    .hints(priority='normal', color_scheme='success')
    .build()
)
```

### Serialization

```python
# To dict
data = response.to_dict()

# To JSON
json_string = response.to_json()

# HTTP response
from fastapi.responses import JSONResponse
return JSONResponse(content=response.to_dict())
```

### Validation

```python
from backend.response_envelope import validate_response_envelope
validate_response_envelope(response)  # Raises if invalid
```

---

## Integration Status

### ✅ Implemented
- ✅ ChatSessionHandler returns ResponseEnvelope
- ✅ InteractionOrchestrator returns ResponseEnvelope
- ✅ Phase 1 & 2 tests validate ResponseEnvelope
- ✅ `/chat/integrated` endpoint returns ResponseEnvelope (Phase 3)

### ✅ Ready
- ✅ Production-ready code (702 lines in response_envelope.py)
- ✅ Fully tested and validated
- ✅ Extensible for Phase 4+

### 🔄 Phase 4 (Future)
- Artifact Registry (how to store/retrieve artifacts)
- Presentation Router (how to render artifact types)
- WebSocket integration (consume live_stream_id)

---

## Design Principles

1. **No Execution Logic** — Pure data only
2. **No UI Code** — No HTML, CSS, React
3. **Data Contract** — Agent provides data, UI renders it
4. **References Only** — Artifacts reference external data, don't embed blobs
5. **UI-Agnostic** — Hints are suggestions; UI decides rendering
6. **Validated** — All envelopes validated before serialization
7. **Extensible** — Metadata field for custom data
8. **Backward Compatible** — All new fields optional

---

## Constraints Met

✅ No new execution logic  
✅ No mission behavior changes  
✅ No autonomy changes  
✅ No Selenium changes  
✅ UI-safe (no HTML/CSS/JS)  
✅ Fully compatible with existing code  

---

## Documentation

Three detailed documents provided:

1. **[RESPONSE_ENVELOPE_SCHEMA.md](RESPONSE_ENVELOPE_SCHEMA.md)**
   - Full schema definition (all fields, types, methods)
   - Usage examples
   - Design principles
   - Integration points

2. **[RESPONSE_ENVELOPE_CONFORMANCE.md](RESPONSE_ENVELOPE_CONFORMANCE.md)**
   - Requirements vs implementation checklist
   - Proof that all 9 requirements met
   - Artifact reference-only design
   - UI-safe properties

3. **[RESPONSE_ENVELOPE_EXAMPLES.md](RESPONSE_ENVELOPE_EXAMPLES.md)**
   - Example A: No-op response (JSON + behavior)
   - Example B: Mission proposed (JSON + behavior)
   - Example C: Mission executed (JSON + behavior)
   - UI integration points for each

---

## Files

**Implementation**: [backend/response_envelope.py](backend/response_envelope.py) (702 lines)

**Location in codebase**:
```
backend/
├── response_envelope.py           ← All ResponseEnvelope code
├── chat_session_handler.py        → Returns ResponseEnvelope
├── interaction_orchestrator.py    → Returns ResponseEnvelope
└── main.py                        → /chat/integrated endpoint returns ResponseEnvelope
```

---

## Status: ✅ FINALIZED

The ResponseEnvelope schema is:
- ✅ Fully implemented
- ✅ Fully tested
- ✅ Fully documented
- ✅ Production-ready
- ✅ Meeting all requirements
- ✅ No changes needed

---

## Next Steps

**No immediate action required.** ResponseEnvelope is ready.

**Phase 3** will integrate it into HTTP endpoints:
- `/chat/integrated` ← Returns ResponseEnvelope
- `/api/whiteboard/{mission_id}` ← Reads mission state

**Phase 4** will build on it:
- Artifact Registry (store/retrieve artifacts)
- Presentation Router (render artifacts)
- Real-time WebSocket updates (live_stream_id)

---

## Questions?

See the detailed documentation for:
- **Schema details** → [RESPONSE_ENVELOPE_SCHEMA.md](RESPONSE_ENVELOPE_SCHEMA.md)
- **Requirements proof** → [RESPONSE_ENVELOPE_CONFORMANCE.md](RESPONSE_ENVELOPE_CONFORMANCE.md)
- **Working examples** → [RESPONSE_ENVELOPE_EXAMPLES.md](RESPONSE_ENVELOPE_EXAMPLES.md)

