# ResponseEnvelope Schema Definition
## Canonical Output Format for Buddy

**Status**: ✅ FINALIZED  
**Location**: [backend/response_envelope.py](backend/response_envelope.py)  
**Version**: 2.0 (Phase 3)  
**Last Updated**: February 7, 2026

---

## Overview

`ResponseEnvelope` is the **canonical, UI-safe response format** for all Buddy outputs. It standardizes communication between agent logic and UI rendering without mixing execution logic or UI code.

**Key Principle**: The ResponseEnvelope is a **data contract** — the agent provides data, the UI decides how to render it. No business logic. No UI code. Pure structure.

---

## Core Fields

| Field | Type | Required | Purpose |
|-------|------|----------|---------|
| `response_type` | ResponseType enum | ✅ | Categorizes the response (text, table, report, etc.) |
| `summary` | string | ✅ | Human-readable summary (never empty) |
| `artifacts` | Artifact[] | ❌ | Structured outputs (tables, charts, documents, code, etc.) |
| `missions_spawned` | MissionReference[] | ❌ | Proposed or created missions |
| `signals_emitted` | SignalReference[] | ❌ | References to emitted signals (navigation, extraction, etc.) |
| `live_stream_id` | string (UUID) | ❌ | Live execution stream ID (for real-time updates) |
| `ui_hints` | UIHints | ❌ | Non-binding display suggestions |
| `timestamp` | ISO 8601 | ✅ | When response was generated |
| `metadata` | Dict[str, Any] | ❌ | Additional context (error details, custom data) |

---

## ResponseType Enum

```python
class ResponseType(Enum):
    TEXT = "text"
    TABLE = "table"
    REPORT = "report"
    FORECAST = "forecast"
    LIVE_EXECUTION = "live_execution"
    ARTIFACT_BUNDLE = "artifact_bundle"
    CLARIFICATION_REQUEST = "clarification_request"
```

**Usage**:
- `TEXT` — Simple message response
- `TABLE` — Tabular data response
- `REPORT` — Multi-section document
- `FORECAST` — Predictive output
- `LIVE_EXECUTION` — Real-time streaming
- `ARTIFACT_BUNDLE` — Multiple artifacts (missions, signals, etc.)
- `CLARIFICATION_REQUEST` — Agent asking for clarification

---

## Artifact Types

```python
class ArtifactType(Enum):
    TABLE = "table"
    CHART = "chart"
    DOCUMENT = "document"
    CODE_BLOCK = "code_block"
    TIMELINE = "timeline"
    FILE_REFERENCE = "file_reference"
    JSON_DATA = "json_data"
    MISSION_DRAFT = "mission_draft"
    SIGNAL_BATCH = "signal_batch"
```

Each artifact is a **reference** with minimal metadata, not a heavy data blob:

### TableArtifact
```python
TableArtifact(
    title="Query Results",
    columns=["Name", "Email", "Status"],
    rows=[
        ["Alice", "alice@example.com", "active"],
        ["Bob", "bob@example.com", "inactive"]
    ]
)
```

### ChartArtifact
```python
ChartArtifact(
    title="Revenue Trend",
    chart_type="line",  # 'line', 'bar', 'pie', 'scatter'
    data={
        "labels": ["Jan", "Feb", "Mar"],
        "datasets": [{"label": "Sales", "data": [100, 200, 150]}]
    }
)
```

### DocumentArtifact
```python
DocumentArtifact(
    title="Mission Report",
    sections=[
        {"heading": "Summary", "content": "Scraped 50 quotes successfully"},
        {"heading": "Findings", "content": "Top author: Oscar Wilde"}
    ],
    format="markdown"
)
```

### CodeBlockArtifact
```python
CodeBlockArtifact(
    title="Generated Script",
    code="def hello():\n    print('Hello, World!')",
    language="python"
)
```

### TimelineArtifact
```python
TimelineArtifact(
    title="Mission Execution",
    events=[
        {"timestamp": "2026-02-07T14:00:00Z", "event": "Navigation started", "status": "success"},
        {"timestamp": "2026-02-07T14:05:00Z", "event": "Extraction complete", "status": "success"}
    ]
)
```

### FileReferenceArtifact
```python
FileReferenceArtifact(
    title="Results Export",
    file_path="/outputs/quotes.csv",
    file_type="csv",
    size_bytes=2048
)
```

---

## Mission Reference

```python
@dataclass
class MissionReference:
    mission_id: str              # UUID of mission
    status: str                  # 'proposed', 'active', 'completed', 'failed'
    objective_type: str          # 'navigate', 'extract', 'synthesize'
    objective_description: str   # Human-readable goal
```

**Example**:
```json
{
  "mission_id": "0035d374-2f36-499f-afba-10a2fd3d47e9",
  "status": "proposed",
  "objective_type": "extract",
  "objective_description": "Find 50 quotes from quotes.toscrape.com"
}
```

---

## Signal Reference

```python
@dataclass
class SignalReference:
    signal_type: str             # 'selector_outcome', 'navigation_intent', 'goal_evaluation'
    signal_layer: str            # 'selector', 'intent', 'mission', 'aggregate'
    signal_source: str           # 'web_navigator', 'navigation_intent_engine', 'goal_evaluator'
    timestamp: str               # ISO 8601
    summary: Optional[str]       # Optional human-readable summary
```

**Example**:
```json
{
  "signal_type": "selector_outcome",
  "signal_layer": "selector",
  "signal_source": "web_navigator",
  "timestamp": "2026-02-07T14:50:41.828368+00:00",
  "summary": "Found pagination link (xpath)"
}
```

---

## UIHints

Non-binding display suggestions for the UI:

```python
@dataclass
class UIHints:
    layout: Optional[str]           # 'fullscreen', 'split', 'inline', 'modal'
    priority: Optional[str]         # 'urgent', 'normal', 'low'
    suggested_actions: List[str]    # ['Review', 'Approve', 'Modify']
    color_scheme: Optional[str]     # 'success', 'warning', 'error', 'info'
    icon: Optional[str]             # 'clipboard', 'alert', 'checkmark'
    expandable: bool                # Can be collapsed/expanded
```

**Purpose**: Suggests how the UI *might* display the response, but the UI is free to ignore.

**Example**:
```python
UIHints(
    layout='inline',
    priority='normal',
    suggested_actions=['Review', 'Approve', 'Reject'],
    color_scheme='info',
    icon='clipboard',
    expandable=True
)
```

---

## Helper Functions

### Minimal Response
```python
from backend.response_envelope import minimal_response, ResponseType

response = minimal_response(
    summary="Task completed",
    response_type=ResponseType.TEXT
)
```

### Text Response
```python
from backend.response_envelope import text_response, UIHints

response = text_response(
    text="I found 50 quotes",
    ui_hints=UIHints(priority='normal', color_scheme='success')
)
```

### Clarification Request
```python
from backend.response_envelope import clarification_response

response = clarification_response(
    question="How many quotes would you like?",
    options=["10", "50", "100", "All"],
    context={"source": "user_chat"}
)
```

### Mission Proposal
```python
from backend.response_envelope import mission_proposal_response, MissionReference

mission = MissionReference(
    mission_id="abc-123",
    status="proposed",
    objective_type="extract",
    objective_description="Find 50 quotes"
)

response = mission_proposal_response(
    mission=mission,
    summary="I'll scrape those quotes for you"
)
```

### Error Response
```python
from backend.response_envelope import error_response

response = error_response(
    error_message="Navigation failed",
    error_details={"reason": "timeout", "retry_count": 3}
)
```

---

## ResponseBuilder (Fluent Interface)

```python
from backend.response_envelope import ResponseBuilder, ResponseType

response = (ResponseBuilder()
    .type(ResponseType.ARTIFACT_BUNDLE)
    .summary("Mission completed successfully")
    .add_table(
        title="Results",
        columns=["Quote", "Author"],
        rows=[["To be or not to be", "Shakespeare"]]
    )
    .add_mission(mission_ref)
    .add_signal(signal_ref)
    .live_stream("stream-123")
    .hints(
        priority='normal',
        color_scheme='success',
        suggested_actions=['Done', 'Export']
    )
    .metadata('mission_duration_ms', 2500)
    .build()
)
```

---

## JSON Serialization

All ResponseEnvelope objects have `.to_dict()` and `.to_json()` methods:

```python
response = text_response("Done")

# Convert to dict
data = response.to_dict()

# Convert to JSON string
json_string = response.to_json()
```

---

## Validation

```python
from backend.response_envelope import validate_response_envelope, ResponseValidationError

try:
    validate_response_envelope(response)
    print("✅ Valid")
except ResponseValidationError as e:
    print(f"❌ Invalid: {e}")
```

**Validation checks**:
- `response_type` is a valid ResponseType
- `summary` is non-empty
- All artifacts are valid Artifact instances
- All missions have mission_id
- All signals have signal_type
- Timestamps are ISO 8601

---

## Example Responses

### Example 1: No-Op Response (No Mission)

**Scenario**: User asks a question, no mission required

```json
{
  "response_type": "text",
  "summary": "That's interesting. Here's what I found about web scraping...",
  "artifacts": [],
  "missions_spawned": [],
  "signals_emitted": [],
  "live_stream_id": null,
  "ui_hints": {
    "layout": "inline",
    "priority": "normal",
    "suggested_actions": [],
    "color_scheme": "info",
    "icon": null,
    "expandable": true
  },
  "timestamp": "2026-02-07T20:07:00.000000+00:00",
  "metadata": {}
}
```

---

### Example 2: Mission Proposed

**Scenario**: User requests action, mission created

```json
{
  "response_type": "artifact_bundle",
  "summary": "I'll find those quotes for you. Creating a mission...",
  "artifacts": [
    {
      "artifact_type": "mission_draft",
      "title": "Mission Proposal",
      "content": {
        "mission_id": "0035d374-2f36-499f-afba-10a2fd3d47e9",
        "status": "proposed",
        "objective_type": "extract",
        "objective_description": "Find 50 quotes from quotes.toscrape.com"
      },
      "metadata": {
        "awaiting_approval": true
      }
    }
  ],
  "missions_spawned": [
    {
      "mission_id": "0035d374-2f36-499f-afba-10a2fd3d47e9",
      "status": "proposed",
      "objective_type": "extract",
      "objective_description": "Find 50 quotes from quotes.toscrape.com"
    }
  ],
  "signals_emitted": [
    {
      "signal_type": "mission_proposed",
      "signal_layer": "mission",
      "signal_source": "chat_intake",
      "timestamp": "2026-02-07T20:07:02.031542+00:00",
      "summary": "Mission proposal created from chat intent"
    }
  ],
  "live_stream_id": null,
  "ui_hints": {
    "layout": "split",
    "priority": "normal",
    "suggested_actions": ["Review", "Approve", "Modify", "Reject"],
    "color_scheme": "info",
    "icon": "clipboard",
    "expandable": true
  },
  "timestamp": "2026-02-07T20:07:02.031542+00:00",
  "metadata": {
    "intent_classification": "execute",
    "confidence": 0.87
  }
}
```

---

### Example 3: Mission Executed (Results)

**Scenario**: Mission completes, results returned

```json
{
  "response_type": "artifact_bundle",
  "summary": "✅ Mission completed! Found 50 quotes from 10 pages.",
  "artifacts": [
    {
      "artifact_type": "table",
      "title": "Top Quotes",
      "content": {
        "columns": ["Quote", "Author", "Tags"],
        "rows": [
          ["The only way to do great work is to love what you do", "Steve Jobs", "inspiration"],
          ["Innovation distinguishes between a leader and a follower", "Steve Jobs", "leadership"],
          ["Life is what happens when you're busy making other plans", "John Lennon", "life"]
        ],
        "row_count": 3,
        "column_count": 3
      },
      "metadata": {}
    },
    {
      "artifact_type": "document",
      "title": "Summary Report",
      "content": {
        "format": "markdown",
        "sections": [
          {
            "heading": "Execution Summary",
            "content": "Successfully navigated 10 pages and extracted 50 unique quotes"
          },
          {
            "heading": "Top Authors",
            "content": "Steve Jobs (5 quotes), John Lennon (3 quotes), Oscar Wilde (2 quotes)"
          },
          {
            "heading": "Performance",
            "content": "Completed in 45 seconds with 100% success rate"
          }
        ],
        "section_count": 3
      },
      "metadata": {}
    },
    {
      "artifact_type": "timeline",
      "title": "Execution Timeline",
      "content": {
        "events": [
          {
            "timestamp": "2026-02-07T20:07:15.000000Z",
            "event": "Started navigation",
            "status": "success"
          },
          {
            "timestamp": "2026-02-07T20:07:45.000000Z",
            "event": "Page 1 navigation complete, extracted 5 quotes",
            "status": "success"
          },
          {
            "timestamp": "2026-02-07T20:08:00.000000Z",
            "event": "All 10 pages processed",
            "status": "success"
          }
        ],
        "event_count": 3,
        "start_time": "2026-02-07T20:07:15.000000Z",
        "end_time": "2026-02-07T20:08:00.000000Z"
      },
      "metadata": {}
    }
  ],
  "missions_spawned": [],
  "signals_emitted": [
    {
      "signal_type": "selector_outcome",
      "signal_layer": "selector",
      "signal_source": "web_navigator",
      "timestamp": "2026-02-07T20:07:45.500000Z",
      "summary": "Found pagination links (5 attempts, 1 success)"
    },
    {
      "signal_type": "selector_aggregate",
      "signal_layer": "aggregate",
      "signal_source": "web_navigator",
      "timestamp": "2026-02-07T20:08:00.000000Z",
      "summary": "Total: 50 selectors attempted, 45 succeeded, 5 failed (90% success rate)"
    },
    {
      "signal_type": "mission_completed",
      "signal_layer": "mission",
      "signal_source": "mission_control",
      "timestamp": "2026-02-07T20:08:00.500000Z",
      "summary": "Mission reached target: 50 items collected"
    }
  ],
  "live_stream_id": null,
  "ui_hints": {
    "layout": "fullscreen",
    "priority": "normal",
    "suggested_actions": ["Download", "Share", "New Mission", "Done"],
    "color_scheme": "success",
    "icon": "checkmark",
    "expandable": true
  },
  "timestamp": "2026-02-07T20:08:00.500000Z",
  "metadata": {
    "mission_id": "0035d374-2f36-499f-afba-10a2fd3d47e9",
    "mission_duration_ms": 45500,
    "items_collected": 50,
    "pages_processed": 10,
    "success_rate": 0.9
  }
}
```

---

## Design Principles

1. **No Execution Logic**: ResponseEnvelope contains NO business logic
2. **No UI Code**: ResponseEnvelope contains NO HTML, CSS, or React code
3. **Data Contract**: Pure data structure between agent and UI
4. **References Only**: Artifacts reference data, don't embed large blobs
5. **UI-Agnostic**: Hints are suggestions; UI decides rendering
6. **Validation**: All envelopes validated before serialization
7. **Extensible**: Metadata field for custom data
8. **Backward Compatible**: New fields are optional

---

## Integration Points

### With ChatSessionHandler
```python
chat_response = handler.handle_message(chat_msg)
envelope = chat_response.envelope  # Get ResponseEnvelope
return JSONResponse(content=envelope.to_dict())
```

### With InteractionOrchestrator
```python
result = orchestrate_message(chat_msg)
# Result contains ResponseEnvelope
# Return directly to HTTP endpoint
```

### With UI
```javascript
const response = await fetch('/chat/integrated');
const envelope = await response.json();

// envelope.response_type tells UI what to render
// envelope.artifacts tells UI what data to display
// envelope.missions_spawned tells UI what missions were created
```

---

## Constraints (Hard)

✅ **This schema DOES**:
- Standardize agent → UI communication
- Support all current Buddy outputs (missions, signals, artifacts)
- Enable future Phase 4 (Artifact Registry, Presentation Router)
- Allow real-time updates via live_stream_id
- Provide validation and consistency

❌ **This schema DOES NOT**:
- Contain execution logic
- Mix UI concerns with data
- Change mission behavior
- Add autonomy
- Modify Selenium navigation

---

## Status

**✅ FINALIZED**

The ResponseEnvelope schema is:
- ✅ Implemented (688 lines in response_envelope.py)
- ✅ Validated
- ✅ Tested (Phase 1 & 2)
- ✅ Ready for Phase 3 integration
- ✅ Extensible for Phase 4+

**No changes needed.** This is the canonical format.

