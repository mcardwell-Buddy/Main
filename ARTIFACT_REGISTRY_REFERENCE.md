## Artifact Registry: Complete Reference

**Status**: ✅ **FINALIZED & PRODUCTION READY**

---

## Overview

The **Artifact Registry** is a deterministic definition of all artifacts Buddy can produce. It contains no execution logic, no LLM calls, and no UI rendering—just pure data definitions.

---

## The 9 Artifact Types

### 1. **business_plan**
Comprehensive business plan document with strategy, financials, and roadmap.

**Required Fields:**
- `executive_summary` — High-level overview
- `market_analysis` — Market opportunity and dynamics
- `value_proposition` — Unique value offered
- `financial_projections` — Revenue, costs, margins

**Optional Fields:**
- `team_structure` — Organizational setup
- `competitive_landscape` — Competitor analysis
- `risk_analysis` — Risks and mitigation
- `go_to_market_strategy` — Launch strategy
- `funding_requirements` — Capital needs
- `appendix` — Supporting materials

**Visualizations:** `document`, `expanded_panel`, `card`  
**Size Constraints:** max_sections=15, max_text_length=200k  
**Export Formats:** `pdf`, `docx`, `md`  
**Use Cases:** Startup planning, fundraising, strategic planning, investor presentations

---

### 2. **forecast_report**
Data-driven forecast with predictions, confidence intervals, and assumptions.

**Required Fields:**
- `metric` — What is being forecasted
- `forecast_values` — Predicted values
- `time_period` — Duration of forecast
- `confidence_intervals` — Uncertainty ranges
- `assumptions` — Key assumptions

**Optional Fields:**
- `historical_baseline` — Historical comparison
- `sensitivity_analysis` — Sensitivity to assumptions
- `scenario_analysis` — Alternative scenarios
- `error_metrics` — Accuracy measures
- `notes` — Additional context

**Visualizations:** `chart`, `table`, `expanded_panel`  
**Size Constraints:** max_rows=5k, max_fields=20  
**Export Formats:** `csv`, `xlsx`, `json`  
**Use Cases:** Revenue forecasting, demand planning, resource allocation, risk assessment

---

### 3. **opportunity_brief**
Concise opportunity analysis with potential, impact, and action items.

**Required Fields:**
- `opportunity_title` — Opportunity name
- `description` — What is the opportunity
- `potential_impact` — Business value
- `effort_estimate` — Resources needed
- `recommended_actions` — Action steps

**Optional Fields:**
- `market_size` — TAM/SAM/SOM
- `competitive_advantages` — Why we win
- `risks` — Risk factors
- `timeline` — Implementation timeline
- `required_resources` — People, budget, tools
- `success_metrics` — How to measure success

**Visualizations:** `card`, `expanded_panel`, `document`  
**Size Constraints:** max_text_length=50k, max_items=20  
**Export Formats:** `pdf`, `md`, `txt`  
**Use Cases:** Business development, strategic initiatives, investment evaluation, project scoping

---

### 4. **mission_summary**
Structured summary of completed mission with objectives, results, and metrics.

**Required Fields:**
- `mission_id` — Unique mission identifier
- `objective` — What was the mission trying to do
- `status` — final outcome (completed, failed, etc.)
- `completion_time` — How long it took
- `key_results` — Main results achieved

**Optional Fields:**
- `actions_taken` — Steps executed
- `data_collected` — Data gathered
- `errors_encountered` — Issues faced
- `resources_used` — Compute, time, budget
- `recommendations` — Follow-up suggestions
- `follow_up_actions` — Next steps

**Visualizations:** `card`, `table`, `expanded_panel`  
**Size Constraints:** max_fields=30, max_items=50  
**Export Formats:** `json`, `csv`, `md`  
**Use Cases:** Mission tracking, audit logs, performance reporting, historical analysis

---

### 5. **risk_memo**
Risk assessment document with identified risks, impacts, and mitigation strategies.

**Required Fields:**
- `risk_summary` — Overall risk assessment
- `identified_risks` — Specific risks
- `impact_assessment` — Consequence severity
- `probability` — Likelihood of occurrence

**Optional Fields:**
- `mitigation_strategies` — How to reduce risk
- `contingency_plans` — Backup plans
- `risk_owners` — Responsible parties
- `review_date` — When to re-evaluate
- `historical_precedent` — Similar past events

**Visualizations:** `document`, `table`, `expanded_panel`  
**Size Constraints:** max_text_length=75k, max_items=30  
**Export Formats:** `pdf`, `docx`, `md`  
**Use Cases:** Risk management, decision support, compliance reporting, strategic planning

---

### 6. **dataset**
Structured data collection with rows, columns, and metadata.

**Required Fields:**
- `columns` — Column names
- `rows` — Data rows
- `row_count` — Number of rows
- `column_count` — Number of columns

**Optional Fields:**
- `metadata` — Additional context
- `data_types` — Column types
- `statistics` — Summary statistics
- `quality_score` — Data quality 0-1
- `source` — Data source
- `timestamp` — When collected

**Visualizations:** `table`, `chart`, `summary_row`  
**Size Constraints:** max_rows=100k, max_fields=100, max_file_size=500MB  
**Export Formats:** `csv`, `json`, `xlsx`, `parquet`  
**Use Cases:** Data analysis, reporting, decision making, machine learning

---

### 7. **chart**
Visual representation of data with chart type, series, and axis configuration.

**Required Fields:**
- `chart_type` — Type (line, bar, pie, scatter, etc.)
- `data` — Data to visualize
- `title` — Chart title

**Optional Fields:**
- `x_axis_label` — X-axis name
- `y_axis_label` — Y-axis name
- `series_labels` — Series names
- `color_scheme` — Colors
- `legend` — Legend configuration
- `annotations` — Data labels/notes
- `scale_type` — Linear, log, etc.

**Visualizations:** `chart`, `expanded_panel`  
**Size Constraints:** max_rows=50k, max_fields=10  
**Export Formats:** `png`, `svg`, `json`, `pdf`  
**Use Cases:** Data visualization, trend analysis, comparative analysis, presentations

---

### 8. **timeline**
Sequence of events, milestones, or actions ordered chronologically.

**Required Fields:**
- `events` — List of events
- `start_date` — Timeline start
- `end_date` — Timeline end

**Optional Fields:**
- `phases` — Logical phases
- `dependencies` — Event dependencies
- `owner_assignments` — Responsibility mapping
- `status_updates` — Progress status
- `completion_percentage` — Overall progress

**Visualizations:** `timeline`, `table`, `expanded_panel`  
**Size Constraints:** max_items=500, max_fields=20  
**Export Formats:** `json`, `csv`, `ics`  
**Use Cases:** Project planning, roadmap visualization, process documentation, milestone tracking

---

### 9. **live_monitor** ⭐ (Streaming)
Real-time streaming data with updates, metrics, and status indicators.

**Required Fields:**
- `stream_id` — Unique stream identifier (UUID)
- `metric_name` — What is being tracked
- `current_value` — Current metric value

**Optional Fields:**
- `historical_values` — Past values
- `thresholds` — Alert thresholds
- `status_indicator` — Status (ok, warning, error)
- `last_update` — Last update timestamp
- `update_frequency` — How often it updates
- `alerts` — Active alerts

**Visualizations:** `live_monitor`, `chart`, `summary_row`  
**Size Constraints:** max_items=1k, max_fields=50  
**Export Formats:** `json`, `csv`  
**Streaming:** Yes ⭐  
**Use Cases:** Real-time monitoring, system health, mission progress, performance metrics

---

## Groupings

### Document Types (Export to PDF/DOCX)
- `business_plan`
- `risk_memo`
- `opportunity_brief`
- `mission_summary`

### Data Types (Export to CSV/JSON)
- `dataset`
- `forecast_report`
- `timeline`
- `live_monitor`

### Visual Types (Chart Rendering)
- `chart`
- `timeline`
- `forecast_report`
- `live_monitor`

### Streaming Types (Real-time Updates)
- `live_monitor`

---

## Registry API

### Retrieve an artifact definition
```python
from backend.artifact_registry import get_artifact_definition

definition = get_artifact_definition("business_plan")
print(definition.required_fields)
print(definition.size_constraints)
```

### Validate artifact type
```python
from backend.artifact_registry import validate_artifact_type

if validate_artifact_type("business_plan"):
    # Type is registered
    pass
```

### List all artifact types
```python
from backend.artifact_registry import list_all_artifact_types

all_types = list_all_artifact_types()
# Returns: ['business_plan', 'forecast_report', 'opportunity_brief', ...]
```

### Get artifacts by visualization type
```python
from backend.artifact_registry import get_artifact_types_by_visualization, VisualizationType

chart_artifacts = get_artifact_types_by_visualization(VisualizationType.CHART)
# Returns: ['chart', 'timeline', 'forecast_report', 'live_monitor']
```

### Get artifacts by use case
```python
from backend.artifact_registry import get_artifact_types_by_use_case

planning_artifacts = get_artifact_types_by_use_case("Strategic planning")
# Returns: ['business_plan', 'risk_memo']
```

### Validate required fields
```python
from backend.artifact_registry import validate_required_fields

submitted_fields = ["executive_summary", "market_analysis", "value_proposition", "financial_projections"]
is_valid, missing = validate_required_fields("business_plan", submitted_fields)

if not is_valid:
    print(f"Missing: {missing}")
```

### Validate field names
```python
from backend.artifact_registry import validate_field_names

fields = ["metric", "forecast_values", "invalid_field"]
is_valid, unknown = validate_field_names("forecast_report", fields)

if not is_valid:
    print(f"Unknown fields: {unknown}")
```

### Serialize entire registry
```python
from backend.artifact_registry import serialize_registry
import json

registry = serialize_registry()
print(json.dumps(registry, indent=2))
```

---

## Size Constraints Summary

| Constraint | Default | Notes |
|-----------|---------|-------|
| `max_fields` | 50 | Total fields allowed |
| `max_rows` | 10,000 | Rows for datasets |
| `max_file_size_mb` | 100 | File size limit |
| `max_text_length` | 100,000 | Characters for text |
| `max_sections` | 20 | Sections for documents |
| `max_items_in_list` | 1,000 | Items in lists |

**Override per artifact:** Each artifact can customize these limits.

---

## Design Principles

1. **Pure Data** — No execution logic, no LLM calls, no UI rendering
2. **Deterministic** — Same inputs always produce same outputs
3. **Reference-Only** — Artifacts reference data, don't embed it
4. **Validatable** — All inputs validated against registry
5. **Extensible** — New artifact types added to registry, no code changes
6. **UI-Agnostic** — Registry defines data, UI decides presentation
7. **Type-Safe** — Strong typing prevents errors
8. **Queryable** — Find artifacts by visualization, use case, streaming, etc.

---

## Files

**Implementation**: [backend/artifact_registry.py](backend/artifact_registry.py)  
**Examples**: [backend/artifact_registry_examples.py](backend/artifact_registry_examples.py)

---

## Status: ✅ COMPLETE

The Artifact Registry is:
- ✅ Fully implemented
- ✅ All 9 artifact types defined
- ✅ All required/optional fields documented
- ✅ All visualizations mapped
- ✅ All size constraints defined
- ✅ Production-ready
- ✅ Zero execution logic
- ✅ Zero LLM dependencies

---

## Next Phase (Phase 4)

**Presentation Router**: How to render each artifact type in the UI based on visualization hints.

