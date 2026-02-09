# ResponseEnvelope Examples
## Three Production Scenarios

**Location**: [backend/response_envelope.py](backend/response_envelope.py)  
**Date**: February 7, 2026  
**Status**: ✅ FINALIZED

---

## Example A: No-Op Response (No Mission)

**Scenario**: User asks a clarifying question about web scraping. No mission needed. Agent responds with information only.

**Code**:
```python
from backend.response_envelope import text_response, UIHints

response = text_response(
    text="Web scraping extracts data from websites using automated tools. "
         "Common approaches include: 1) XPath selectors, 2) CSS selectors, "
         "3) Regex patterns. Which site do you want to scrape?",
    ui_hints=UIHints(
        priority='normal',
        color_scheme='info',
        suggested_actions=['Answer', 'Show example'],
        icon='info'
    )
)
```

**JSON Output**:
```json
{
  "response_type": "text",
  "summary": "Web scraping extracts data from websites using automated tools. Common approaches include: 1) XPath selectors, 2) CSS selectors, 3) Regex patterns. Which site do you want to scrape?",
  "artifacts": [],
  "missions_spawned": [],
  "signals_emitted": [],
  "live_stream_id": null,
  "ui_hints": {
    "layout": null,
    "priority": "normal",
    "suggested_actions": [
      "Answer",
      "Show example"
    ],
    "color_scheme": "info",
    "icon": "info",
    "expandable": true
  },
  "timestamp": "2026-02-07T20:10:30.123456+00:00",
  "metadata": {}
}
```

**UI Behavior**:
- Display as simple text message
- Show suggested actions
- Use info icon
- No artifacts to render
- No mission created

---

## Example B: Mission Proposed

**Scenario**: User requests action: "Find 50 quotes from quotes.toscrape.com". Intent classifier recognizes this as executable. Mission is proposed but status='proposed' (not executed yet).

**Code**:
```python
from backend.response_envelope import ResponseBuilder, ResponseType, MissionReference, SignalReference, UIHints

mission_ref = MissionReference(
    mission_id="0035d374-2f36-499f-afba-10a2fd3d47e9",
    status="proposed",
    objective_type="extract",
    objective_description="Find 50 quotes from quotes.toscrape.com"
)

signal_ref = SignalReference(
    signal_type="mission_proposed",
    signal_layer="mission",
    signal_source="chat_intake",
    timestamp="2026-02-07T20:11:00.500000+00:00",
    summary="Mission proposal created from user intent"
)

response = (ResponseBuilder()
    .type(ResponseType.ARTIFACT_BUNDLE)
    .summary("I'll scrape those quotes for you. Creating a mission to handle this...")
    .add_mission(mission_ref)
    .add_signal(signal_ref)
    .hints(
        layout='split',
        priority='normal',
        suggested_actions=['Review', 'Approve', 'Modify', 'Reject'],
        color_scheme='info',
        icon='clipboard'
    )
    .metadata('intent_classification', 'execute')
    .metadata('confidence', 0.87)
    .metadata('action', 'mission_proposal')
    .build()
)
```

**JSON Output**:
```json
{
  "response_type": "artifact_bundle",
  "summary": "I'll scrape those quotes for you. Creating a mission to handle this...",
  "artifacts": [],
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
      "timestamp": "2026-02-07T20:11:00.500000+00:00",
      "summary": "Mission proposal created from user intent"
    }
  ],
  "live_stream_id": null,
  "ui_hints": {
    "layout": "split",
    "priority": "normal",
    "suggested_actions": [
      "Review",
      "Approve",
      "Modify",
      "Reject"
    ],
    "color_scheme": "info",
    "icon": "clipboard",
    "expandable": true
  },
  "timestamp": "2026-02-07T20:11:00.500000+00:00",
  "metadata": {
    "intent_classification": "execute",
    "confidence": 0.87,
    "action": "mission_proposal"
  }
}
```

**UI Behavior**:
- Display summary: "I'll scrape those quotes..."
- Show mission proposal card with: mission_id, status, objective
- Show signal reference (1 signal emitted)
- Suggest actions: Review, Approve, Modify, Reject
- Can link to `/api/whiteboard/{mission_id}` for full mission state
- Status='proposed' means mission not executing yet (awaiting approval)

---

## Example C: Mission Executed (Results Returned)

**Scenario**: Mission executed successfully. Returned with results: 50 quotes, 10 pages processed, timeline of execution, signals showing navigation and extraction steps.

**Code**:
```python
from backend.response_envelope import ResponseBuilder, ResponseType, SignalReference, UIHints, TableArtifact, DocumentArtifact, TimelineArtifact

response = (ResponseBuilder()
    .type(ResponseType.ARTIFACT_BUNDLE)
    .summary("✅ Mission completed! Found 50 quotes from quotes.toscrape.com across 10 pages.")
    .add_table(
        title="Top 10 Quotes",
        columns=["Quote", "Author", "Tags"],
        rows=[
            ["The only way to do great work is to love what you do", "Steve Jobs", "inspiration,work"],
            ["Innovation distinguishes between a leader and a follower", "Steve Jobs", "leadership,innovation"],
            ["Life is what happens when you're busy making other plans", "John Lennon", "life,wisdom"],
            ["The future belongs to those who believe in the beauty of their dreams", "Eleanor Roosevelt", "dreams,future"],
            ["Get busy living or get busy dying", "Stephen King", "life,action"],
            ["Two things are infinite: the universe and human stupidity", "Albert Einstein", "wisdom,humor"],
            ["To live is the rarest thing in the world", "Oscar Wilde", "life,wisdom"],
            ["It is during our darkest moments that we must focus", "Aristotle", "perseverance,challenges"],
            ["Be yourself; everyone else is already taken", "Oscar Wilde", "authenticity,self"],
            ["The way to get started is to quit talking", "Walt Disney", "action,success"]
        ]
    )
    .add_document(
        title="Execution Summary Report",
        sections=[
            {
                "heading": "Mission Overview",
                "content": "Successfully scraped quotes.toscrape.com to extract 50 unique quotes with author attribution and tags."
            },
            {
                "heading": "Execution Timeline",
                "content": "Started: 2026-02-07T20:11:05Z\nEnded: 2026-02-07T20:12:15Z\nDuration: 70 seconds"
            },
            {
                "heading": "Pages Processed",
                "content": "10 pages successfully navigated and processed. No failed pages."
            },
            {
                "heading": "Top Authors",
                "content": "1. Oscar Wilde (5 quotes)\n2. Steve Jobs (4 quotes)\n3. John Lennon (3 quotes)\n4. Eleanor Roosevelt (3 quotes)\n5. Others (36 quotes from various authors)"
            },
            {
                "heading": "Performance Metrics",
                "content": "Selector Success Rate: 92% (46/50 selectors succeeded)\nAverage Page Load: 7 seconds\nTotal Extraction Time: 70 seconds"
            }
        ],
        format="markdown"
    )
    .add_timeline(
        title="Execution Timeline",
        events=[
            {"timestamp": "2026-02-07T20:11:05Z", "event": "Started navigation to quotes.toscrape.com", "status": "success"},
            {"timestamp": "2026-02-07T20:11:12Z", "event": "Page 1 loaded, extracted 5 quotes", "status": "success"},
            {"timestamp": "2026-02-07T20:11:19Z", "event": "Navigated to page 2", "status": "success"},
            {"timestamp": "2026-02-07T20:11:25Z", "event": "Page 2 extracted 5 quotes", "status": "success"},
            {"timestamp": "2026-02-07T20:11:32Z", "event": "Pagination successful (pages 3-5)", "status": "success"},
            {"timestamp": "2026-02-07T20:11:45Z", "event": "Pagination successful (pages 6-8)", "status": "success"},
            {"timestamp": "2026-02-07T20:12:02Z", "event": "Pagination successful (pages 9-10)", "status": "success"},
            {"timestamp": "2026-02-07T20:12:15Z", "event": "Mission complete: 50 quotes extracted", "status": "success"}
        ]
    )
    .add_signal(SignalReference(
        signal_type="selector_aggregate",
        signal_layer="aggregate",
        signal_source="web_navigator",
        timestamp="2026-02-07T20:12:15.000000+00:00",
        summary="Total: 50 selectors attempted, 46 succeeded (92% success rate)"
    ))
    .add_signal(SignalReference(
        signal_type="mission_completed",
        signal_layer="mission",
        signal_source="mission_control",
        timestamp="2026-02-07T20:12:15.500000+00:00",
        summary="Mission reached target: 50 items collected"
    ))
    .add_signal(SignalReference(
        signal_type="navigation_intent_ranked",
        signal_layer="intent",
        signal_source="navigation_intent_engine",
        timestamp="2026-02-07T20:11:32.250000+00:00",
        summary="Pagination intent detected and executed (10 successful navigations)"
    ))
    .hints(
        layout='fullscreen',
        priority='normal',
        suggested_actions=['Download Results', 'Export CSV', 'New Mission', 'Done'],
        color_scheme='success',
        icon='checkmark'
    )
    .metadata('mission_id', '0035d374-2f36-499f-afba-10a2fd3d47e9')
    .metadata('mission_duration_ms', 70000)
    .metadata('items_collected', 50)
    .metadata('pages_processed', 10)
    .metadata('success_rate', 0.92)
    .metadata('status', 'ok')
    .metadata('confidence', 0.98)
    .build()
)
```

**JSON Output**:
```json
{
  "response_type": "artifact_bundle",
  "summary": "✅ Mission completed! Found 50 quotes from quotes.toscrape.com across 10 pages.",
  "artifacts": [
    {
      "artifact_type": "table",
      "title": "Top 10 Quotes",
      "content": {
        "columns": [
          "Quote",
          "Author",
          "Tags"
        ],
        "rows": [
          [
            "The only way to do great work is to love what you do",
            "Steve Jobs",
            "inspiration,work"
          ],
          [
            "Innovation distinguishes between a leader and a follower",
            "Steve Jobs",
            "leadership,innovation"
          ],
          [
            "Life is what happens when you're busy making other plans",
            "John Lennon",
            "life,wisdom"
          ],
          [
            "The future belongs to those who believe in the beauty of their dreams",
            "Eleanor Roosevelt",
            "dreams,future"
          ],
          [
            "Get busy living or get busy dying",
            "Stephen King",
            "life,action"
          ],
          [
            "Two things are infinite: the universe and human stupidity",
            "Albert Einstein",
            "wisdom,humor"
          ],
          [
            "To live is the rarest thing in the world",
            "Oscar Wilde",
            "life,wisdom"
          ],
          [
            "It is during our darkest moments that we must focus",
            "Aristotle",
            "perseverance,challenges"
          ],
          [
            "Be yourself; everyone else is already taken",
            "Oscar Wilde",
            "authenticity,self"
          ],
          [
            "The way to get started is to quit talking",
            "Walt Disney",
            "action,success"
          ]
        ],
        "row_count": 10,
        "column_count": 3
      },
      "metadata": {}
    },
    {
      "artifact_type": "document",
      "title": "Execution Summary Report",
      "content": {
        "format": "markdown",
        "sections": [
          {
            "heading": "Mission Overview",
            "content": "Successfully scraped quotes.toscrape.com to extract 50 unique quotes with author attribution and tags."
          },
          {
            "heading": "Execution Timeline",
            "content": "Started: 2026-02-07T20:11:05Z\nEnded: 2026-02-07T20:12:15Z\nDuration: 70 seconds"
          },
          {
            "heading": "Pages Processed",
            "content": "10 pages successfully navigated and processed. No failed pages."
          },
          {
            "heading": "Top Authors",
            "content": "1. Oscar Wilde (5 quotes)\n2. Steve Jobs (4 quotes)\n3. John Lennon (3 quotes)\n4. Eleanor Roosevelt (3 quotes)\n5. Others (36 quotes from various authors)"
          },
          {
            "heading": "Performance Metrics",
            "content": "Selector Success Rate: 92% (46/50 selectors succeeded)\nAverage Page Load: 7 seconds\nTotal Extraction Time: 70 seconds"
          }
        ],
        "section_count": 5
      },
      "metadata": {}
    },
    {
      "artifact_type": "timeline",
      "title": "Execution Timeline",
      "content": {
        "events": [
          {
            "timestamp": "2026-02-07T20:11:05Z",
            "event": "Started navigation to quotes.toscrape.com",
            "status": "success"
          },
          {
            "timestamp": "2026-02-07T20:11:12Z",
            "event": "Page 1 loaded, extracted 5 quotes",
            "status": "success"
          },
          {
            "timestamp": "2026-02-07T20:11:19Z",
            "event": "Navigated to page 2",
            "status": "success"
          },
          {
            "timestamp": "2026-02-07T20:11:25Z",
            "event": "Page 2 extracted 5 quotes",
            "status": "success"
          },
          {
            "timestamp": "2026-02-07T20:11:32Z",
            "event": "Pagination successful (pages 3-5)",
            "status": "success"
          },
          {
            "timestamp": "2026-02-07T20:11:45Z",
            "event": "Pagination successful (pages 6-8)",
            "status": "success"
          },
          {
            "timestamp": "2026-02-07T20:12:02Z",
            "event": "Pagination successful (pages 9-10)",
            "status": "success"
          },
          {
            "timestamp": "2026-02-07T20:12:15Z",
            "event": "Mission complete: 50 quotes extracted",
            "status": "success"
          }
        ],
        "event_count": 8,
        "start_time": "2026-02-07T20:11:05Z",
        "end_time": "2026-02-07T20:12:15Z"
      },
      "metadata": {}
    }
  ],
  "missions_spawned": [],
  "signals_emitted": [
    {
      "signal_type": "selector_aggregate",
      "signal_layer": "aggregate",
      "signal_source": "web_navigator",
      "timestamp": "2026-02-07T20:12:15.000000+00:00",
      "summary": "Total: 50 selectors attempted, 46 succeeded (92% success rate)"
    },
    {
      "signal_type": "mission_completed",
      "signal_layer": "mission",
      "signal_source": "mission_control",
      "timestamp": "2026-02-07T20:12:15.500000+00:00",
      "summary": "Mission reached target: 50 items collected"
    },
    {
      "signal_type": "navigation_intent_ranked",
      "signal_layer": "intent",
      "signal_source": "navigation_intent_engine",
      "timestamp": "2026-02-07T20:11:32.250000+00:00",
      "summary": "Pagination intent detected and executed (10 successful navigations)"
    }
  ],
  "live_stream_id": null,
  "ui_hints": {
    "layout": "fullscreen",
    "priority": "normal",
    "suggested_actions": [
      "Download Results",
      "Export CSV",
      "New Mission",
      "Done"
    ],
    "color_scheme": "success",
    "icon": "checkmark",
    "expandable": true
  },
  "timestamp": "2026-02-07T20:12:15.500000+00:00",
  "metadata": {
    "mission_id": "0035d374-2f36-499f-afba-10a2fd3d47e9",
    "mission_duration_ms": 70000,
    "items_collected": 50,
    "pages_processed": 10,
    "success_rate": 0.92,
    "status": "ok",
    "confidence": 0.98
  }
}
```

**UI Behavior**:
- Display success message: "✅ Mission completed!..."
- Render table: Top 10 Quotes (interactive, sortable)
- Render document: Full execution report (5 sections, markdown formatted)
- Render timeline: Visual execution timeline with 8 events
- Show 3 signal references (selector stats, mission completion, navigation intent)
- Suggest actions: Download, Export, New Mission, Done
- Use success/checkmark styling (green, success icon)
- Mission status available via `/api/whiteboard/{mission_id}`

---

## Key Differences Between Examples

| Aspect | Example A (No-Op) | Example B (Proposed) | Example C (Executed) |
|--------|-------------------|----------------------|----------------------|
| **Response Type** | TEXT | ARTIFACT_BUNDLE | ARTIFACT_BUNDLE |
| **Summary** | Informational | Action proposal | Success message |
| **Missions** | Empty | 1 proposed | 0 (executed, not proposed) |
| **Artifacts** | 0 | 0 | 3 (table, document, timeline) |
| **Signals** | 0 | 1 | 3 |
| **Status** | N/A | proposed (awaiting approval) | ok (completed) |
| **Confidence** | N/A | 0.87 | 0.98 |
| **UI Hints** | info/optional | info/split (for review) | success/fullscreen (results) |
| **Actions** | [Answer, Show example] | [Review, Approve, Modify, Reject] | [Download, Export, New Mission, Done] |

---

## Integration Points

### Example A → UI
```javascript
// No-op: Display text, show info icon
response.summary  → Display as chat message
response.ui_hints → Use 'info' color scheme
response.artifacts → (empty, no rendering)
```

### Example B → UI → Whiteboard
```javascript
// Mission proposal: Show approval UI, link to whiteboard
response.missions_spawned[0].mission_id → Link to whiteboard
GET /api/whiteboard/{mission_id} → View full mission state
// User approves → Mission execution begins (Example C)
```

### Example C → UI → Results
```javascript
// Executed: Show results, allow export
response.artifacts[0] → Render table
response.artifacts[1] → Render document
response.artifacts[2] → Render timeline
response.signals_emitted → Show navigation/extraction stats
GET /api/whiteboard/{mission_id} → View archived mission state
```

---

## Status: ✅ FINALIZED

All three examples are production-ready and demonstrate:
- ✅ No-op response (clarification, information)
- ✅ Mission proposal (awaiting approval)
- ✅ Mission execution (results with artifacts)
- ✅ All schema requirements met
- ✅ UI-safe and reference-only
- ✅ Validation-compliant

