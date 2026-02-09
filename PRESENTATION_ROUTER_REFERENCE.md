## Presentation Router: Complete Reference

**Status**: ✅ **FINALIZED & PRODUCTION READY**

---

## Overview

The **Presentation Router** is a deterministic mapping engine that routes ResponseEnvelope + Artifacts to presentation modes. It has no UI code, no rendering, and no execution logic—just pure routing rules.

---

## The 6 Presentation Modes

| Mode | Purpose | Interactive | Streaming | Best For |
|------|---------|-------------|-----------|----------|
| **chat_text** | Plain text in conversation | No | No | Simple messages, low priority content |
| **expandable_card** | Collapsible card/panel | Yes | No | Documents, reports, business plans |
| **table** | Sortable/filterable table | Yes | No | Datasets, structured data |
| **chart** | Interactive visualization | Yes | No | Forecasts, trends, comparisons |
| **timeline** | Chronological sequence | Yes | No | Roadmaps, events, milestones |
| **live_stream** | Real-time updates | Yes | Yes ⭐ | Mission progress, monitoring |

---

## Routing Algorithm

**Deterministic decision engine:**

1. **Collect candidates** from multiple sources:
   - ResponseType (e.g., TEXT → chat_text)
   - ArtifactType (e.g., dataset → table)
   - UIHints/Layout (e.g., fullscreen → chart)
   - Data size (e.g., >5000 rows → paginated table)
   - Priority (e.g., high → expandable_card)

2. **Find intersection**: Modes suggested by multiple sources score higher

3. **Pick best mode**: Highest scoring mode wins

4. **Fall back to response_type**: If no intersection, use response_type primary

5. **Determine capabilities**: Enable/disable sortable, filterable, streaming, etc.

---

## Routing Rules

### By ResponseType

| Type | Primary Mode | Fallbacks |
|------|---|---|
| TEXT | `chat_text` | — |
| TABLE | `table` | chat_text |
| REPORT | `expandable_card` | chat_text |
| FORECAST | `chart` | table |
| LIVE_EXECUTION | `live_stream` | chat_text |
| ARTIFACT_BUNDLE | `expandable_card` | chart, table |
| CLARIFICATION_REQUEST | `chat_text` | — |

### By ArtifactType

| Type | Primary Mode | Fallbacks |
|---|---|---|
| business_plan | `expandable_card` | chat_text |
| forecast_report | `chart` | table, expandable_card |
| opportunity_brief | `expandable_card` | chat_text |
| mission_summary | `expandable_card` | table |
| risk_memo | `expandable_card` | chat_text |
| dataset | `table` | chart, expandable_card |
| chart | `chart` | table |
| timeline | `timeline` | table |
| live_monitor | `live_stream` | chart, table |

### By UIHints Layout

| Layout | Modes |
|---|---|
| fullscreen | chart, table |
| expanded_panel | expandable_card |
| split | table, chart |
| inline | chat_text |
| modal | expandable_card |

### By Data Size

| Condition | Decision |
|---|---|
| rows ≤ 100, fields ≤ 5 | inline table |
| rows > 10,000 OR fields > 50 | paginated table |
| rows > 500, fields ≤ 10 | chart (for visualization) |

### By Priority

| Priority | Mode |
|---|---|
| high | `expandable_card` (prominent) |
| normal | (standard routing) |
| low | `chat_text` (inline) |

---

## API Reference

### Core Function: resolve_presentation

```python
from backend.presentation_router import resolve_presentation

response = build_response(...)
decision = resolve_presentation(response, artifact_index=0)

print(f"Mode: {decision.mode.value}")  # 'chart', 'table', etc.
print(f"Priority: {decision.priority}")  # 0-100
print(f"Rationale: {decision.rationale}")  # Why this mode?
print(f"Sortable: {decision.sortable}")  # Can sort?
print(f"Streaming: {decision.streaming}")  # Live updates?
```

### Multi-Artifact Routing: route_all_artifacts

```python
from backend.presentation_router import route_all_artifacts

response = ResponseBuilder().add_artifact(table).add_artifact(chart).build()
decisions = route_all_artifacts(response)

for artifact_index, decision in decisions:
    print(f"Artifact {artifact_index}: {decision.mode.value}")
```

### UI Layout Planning: route_for_ui_layout

```python
from backend.presentation_router import route_for_ui_layout

response = build_response(...)
layout = route_for_ui_layout(response)

print(f"Strategy: {layout['presentation_strategy']}")  # 'mixed' or 'unified'
print(f"Primary mode: {layout['primary_mode']}")
for artifact in layout['artifacts']:
    print(f"  Artifact {artifact['index']}: {artifact['decision']['mode']}")
```

### Query Functions

```python
from backend.presentation_router import PresentationMode, PRESENTATION_MODES

# List all available modes
modes = PRESENTATION_MODES  # [chart, table, expandable_card, ...]

# Get capabilities of a mode
from backend.presentation_router import get_presentation_capabilities
caps = get_presentation_capabilities(PresentationMode.TABLE)
# Returns: {'interactive': True, 'sortable': True, 'filterable': True, ...}
```

---

## PresentationDecision Output

```python
@dataclass
class PresentationDecision:
    mode: PresentationMode              # Which presentation mode
    priority: int                        # 0-100 (higher = more important)
    rationale: str                       # "ResponseType=chart + LayoutHint=fullscreen"
    fallback_mode: Optional[PresentationMode]  # If primary unavailable
    size_hint: Optional[str]            # 'compact', 'normal', 'expanded'
    interactive: bool                    # Can interact? (click, sort, etc.)
    sortable: bool                       # Can sort columns?
    filterable: bool                     # Can filter data?
    exportable: bool                     # Can export to CSV/PDF?
    streaming: bool                      # Supports live updates?
```

---

## Example Routing Decisions

### Example 1: Simple Text Response
```
Response: Text("Found 3 partnerships")
↓
Decision: chat_text
  Mode: chat_text
  Priority: 33
  Interactive: False
```

### Example 2: Dataset Artifact
```
Response: Table(rows=50, columns=4)
↓
Decision: table
  Mode: table
  Priority: 33
  Sortable: True
  Filterable: True
```

### Example 3: Chart with Layout Hint
```
Response: Chart(type=line) + Layout(fullscreen)
↓
Decision: chart
  Mode: chart
  Priority: 66  (ResponseType + Layout agree)
  Interactive: True
```

### Example 4: Document with High Priority
```
Response: Document(sections=5) + Priority(high) + Layout(expanded_panel)
↓
Decision: expandable_card
  Mode: expandable_card
  Priority: 132  (Multiple sources agree)
  Interactive: True
```

### Example 5: Large Dataset (5000 rows)
```
Response: Table(rows=5000, columns=6)
↓
Decision: table
  Mode: table
  Priority: 33
  Size Hint: compact  (UI will paginate)
  Sortable: True
  Filterable: True
```

### Example 6: Live Execution Stream
```
Response: LiveExecution(stream_id=abc123)
↓
Decision: live_stream
  Mode: live_stream
  Priority: 33
  Streaming: True  (Real-time updates)
  Interactive: True
```

---

## Integration Architecture

```
ResponseEnvelope
    ↓
[resolve_presentation(response, artifact_index)]
    ↓
PresentationDecision
    ├── mode: 'chart' | 'table' | 'expandable_card' | ...
    ├── priority: 0-100
    ├── rationale: "ResponseType=chart + LayoutHint=fullscreen"
    ├── capabilities: {sortable, filterable, streaming, ...}
    └── size_hint: 'compact' | 'normal' | 'expanded'
    ↓
[UI consumes decision]
    ├── Selects React component based on mode
    ├── Enables/disables features based on capabilities
    ├── Applies size hint for rendering
    └── Subscribes to stream if streaming=True
```

---

## Capabilities by Mode

### chat_text
- ✓ Export to text/markdown
- ✗ No sorting, filtering, interactive features

### expandable_card
- ✓ Expand/collapse
- ✓ Export to PDF/markdown
- ✓ Interactive navigation
- ✗ No sorting/filtering

### table
- ✓ Sort columns
- ✓ Filter rows
- ✓ Paginate large datasets
- ✓ Export to CSV/Excel
- ✓ Interactive cell selection

### chart
- ✓ Interactive zooming/panning
- ✓ Filter by series
- ✓ Export to PNG/SVG
- ✓ Hover tooltips
- ✗ No sorting (data visualization only)

### timeline
- ✓ Scroll/zoom chronologically
- ✓ Filter by phase/status
- ✓ Export to ICS/JSON
- ✓ Interactive event details
- ✗ No sorting (chronological order fixed)

### live_stream
- ✓ Real-time updates via WebSocket
- ✓ Live status indicators
- ✓ Stream control (pause/resume)
- ✗ No export during live stream
- ✗ Limited history (last N items)

---

## Design Principles

1. **Deterministic** — Same inputs always produce same routing
2. **Testable** — Pure functions, no side effects
3. **Extensible** — Add new modes by updating routing tables
4. **Prioritized** — High-priority content routed prominently
5. **Fallback-Safe** — Always has a fallback mode
6. **Capability-Aware** — Respects artifact capabilities
7. **Size-Aware** — Adapts presentation for large datasets
8. **Hint-Respecting** — Considers UIHints from agent

---

## Files

**Implementation**: [backend/presentation_router.py](backend/presentation_router.py) (350+ lines)
- `resolve_presentation()` — Main routing engine
- `route_response_type()` — Type-based routing
- `route_artifact_type()` — Artifact-based routing
- `route_by_size()` — Size-aware routing
- `route_all_artifacts()` — Multi-artifact routing
- `route_for_ui_layout()` — UI planning
- `PresentationMode` enum (6 modes)
- `PresentationDecision` dataclass
- Helper functions

**Examples**: [backend/presentation_router_examples.py](backend/presentation_router_examples.py) (450+ lines)
- 10 runnable examples showing all routing scenarios
- All examples verified to work

---

## Status: ✅ COMPLETE

The Presentation Router is:
- ✅ Fully implemented
- ✅ Deterministic routing logic
- ✅ All 6 presentation modes defined
- ✅ Size-aware routing
- ✅ Priority-aware routing
- ✅ Multi-artifact support
- ✅ 10 working examples
- ✅ Zero UI code
- ✅ Zero rendering code
- ✅ Zero execution logic
- ✅ Production-ready

---

## Next Phase (Phase 5)

**Artifact Presentation Manager**: How to render each artifact type in each presentation mode.

