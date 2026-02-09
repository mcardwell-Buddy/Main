"""
Presentation Router Examples: Deterministic routing decisions.

Shows how ResponseEnvelope + Artifacts route to presentation modes.
"""

from datetime import datetime
from backend.response_envelope import (
    ResponseType,
    ResponseBuilder,
    MissionReference,
    SignalReference,
    TableArtifact,
    ChartArtifact,
    DocumentArtifact,
    TimelineArtifact,
)
from backend.presentation_router import (
    resolve_presentation,
    route_all_artifacts,
    route_for_ui_layout,
    PresentationMode,
)
from backend.artifact_registry import VisualizationType


# =============================================================================
# EXAMPLE 1: Simple text response (chat_text)
# =============================================================================

def example_simple_text():
    """Route simple text response."""
    print("\n=== EXAMPLE 1: Simple Text Response ===")
    
    response = ResponseBuilder().type(
        ResponseType.TEXT
    ).summary(
        "I found 3 potential partnerships in your target market."
    ).build()
    
    decision = resolve_presentation(response)
    
    print(f"Response Type: {response.response_type.value}")
    print(f"Summary: {response.summary}")
    print(f"\nRouting Decision:")
    print(f"  Mode: {decision.mode.value}")
    print(f"  Priority: {decision.priority}")
    print(f"  Rationale: {decision.rationale}")
    print(f"  Interactive: {decision.interactive}")
    print(f"  Streaming: {decision.streaming}")


# =============================================================================
# EXAMPLE 2: Table artifact (table mode)
# =============================================================================

def example_table_artifact():
    """Route table artifact."""
    print("\n=== EXAMPLE 2: Table Artifact ===")
    
    table = TableArtifact(
        title="Market Opportunities",
        columns=["Company", "Sector", "Revenue", "Growth"],
        rows=[
            ["TechCorp", "SaaS", "$250M", "45%"],
            ["InnovateInc", "AI", "$180M", "65%"],
            ["DataFlow", "Analytics", "$120M", "38%"],
        ],
    )
    
    response = ResponseBuilder().type(
        ResponseType.TABLE
    ).summary(
        "Here are 3 high-potential market opportunities"
    ).add_artifact(table).build()
    
    decision = resolve_presentation(response)
    
    print(f"Response Type: {response.response_type.value}")
    print(f"Artifact Type: {table.artifact_type.value}")
    print(f"Rows: {table.content['row_count']}, Columns: {table.content['column_count']}")
    print(f"\nRouting Decision:")
    print(f"  Mode: {decision.mode.value}")
    print(f"  Priority: {decision.priority}")
    print(f"  Rationale: {decision.rationale}")
    print(f"  Size Hint: {decision.size_hint}")
    print(f"  Sortable: {decision.sortable}")
    print(f"  Filterable: {decision.filterable}")


# =============================================================================
# EXAMPLE 3: Chart artifact with visualization hint
# =============================================================================

def example_chart_with_hint():
    """Route chart artifact with UIHints."""
    print("\n=== EXAMPLE 3: Chart with Visualization Hint ===")
    
    chart = ChartArtifact(
        title="Revenue Forecast",
        chart_type="line",
        data=[
            {"month": "Jan", "value": 100},
            {"month": "Feb", "value": 115},
            {"month": "Mar", "value": 135},
        ],
    )
    
    response = ResponseBuilder().type(
        ResponseType.FORECAST
    ).summary(
        "Q1 revenue forecast showing 35% growth"
    ).add_artifact(chart).hints(
        layout="fullscreen"
    ).metadata(
        "visualization_hint", "chart"
    ).build()
    
    decision = resolve_presentation(response)
    
    print(f"Response Type: {response.response_type.value}")
    print(f"Artifact Type: {chart.artifact_type.value}")
    print(f"Chart Type: {chart.content['chart_type']}")
    print(f"Layout Hint: {response.ui_hints.layout}")
    print(f"\nRouting Decision:")
    print(f"  Mode: {decision.mode.value}")
    print(f"  Priority: {decision.priority}")
    print(f"  Rationale: {decision.rationale}")
    print(f"  Interactive: {decision.interactive}")
    print(f"  Exportable: {decision.exportable}")


# =============================================================================
# EXAMPLE 4: Document artifact (expandable_card)
# =============================================================================

def example_document_artifact():
    """Route document artifact."""
    print("\n=== EXAMPLE 4: Document Artifact (Expandable Card) ===")
    
    doc = DocumentArtifact(
        title="Q2 Strategic Plan",
        sections=[
            {
                "heading": "Executive Summary",
                "content": "We will expand into 3 new markets with $2M investment..."
            },
            {
                "heading": "Market Opportunity",
                "content": "TAM of $45B with 12% CAGR..."
            },
            {
                "heading": "Financial Projections",
                "content": "Year 1: Break-even, Year 2: $5M revenue..."
            },
        ],
    )
    
    response = ResponseBuilder().type(
        ResponseType.REPORT
    ).summary(
        "Strategic plan created with 3-year roadmap"
    ).add_artifact(doc).hints(
        priority="high",
        layout="expanded_panel",
    ).build()
    
    decision = resolve_presentation(response)
    
    print(f"Response Type: {response.response_type.value}")
    print(f"Artifact Type: {doc.artifact_type.value}")
    print(f"Sections: {doc.content['section_count']}")
    print(f"Priority: {response.ui_hints.priority}")
    print(f"\nRouting Decision:")
    print(f"  Mode: {decision.mode.value}")
    print(f"  Priority: {decision.priority}")
    print(f"  Rationale: {decision.rationale}")
    print(f"  Size Hint: {decision.size_hint}")


# =============================================================================
# EXAMPLE 5: Timeline artifact
# =============================================================================

def example_timeline_artifact():
    """Route timeline artifact."""
    print("\n=== EXAMPLE 5: Timeline Artifact ===")
    
    timeline = TimelineArtifact(
        title="2026 Roadmap",
        events=[
            {"timestamp": "2026-01-01", "title": "Phase 1: Research", "status": "completed"},
            {"timestamp": "2026-04-01", "title": "Phase 2: Development", "status": "in_progress"},
            {"timestamp": "2026-07-01", "title": "Phase 3: Testing", "status": "planned"},
            {"timestamp": "2026-10-01", "title": "Phase 4: Launch", "status": "planned"},
        ],
    )
    
    response = ResponseBuilder().type(
        ResponseType.ARTIFACT_BUNDLE
    ).summary(
        "Annual roadmap with 4 phases"
    ).add_artifact(timeline).hints(
        layout="fullscreen"
    ).metadata(
        "visualization_hint", "timeline"
    ).build()
    
    decision = resolve_presentation(response)
    
    print(f"Response Type: {response.response_type.value}")
    print(f"Artifact Type: {timeline.artifact_type.value}")
    print(f"Events: {timeline.content['event_count']}")
    print(f"\nRouting Decision:")
    print(f"  Mode: {decision.mode.value}")
    print(f"  Priority: {decision.priority}")
    print(f"  Rationale: {decision.rationale}")
    print(f"  Interactive: {decision.interactive}")


# =============================================================================
# EXAMPLE 6: Mission with live execution
# =============================================================================

def example_live_execution():
    """Route live execution response."""
    print("\n=== EXAMPLE 6: Live Execution (Streaming) ===")
    
    mission = MissionReference(
        mission_id="mission-abc123",
        status="executing",
        objective_type="data_extraction",
        objective_description="Extract competitor pricing data",
    )
    
    response = ResponseBuilder().type(
        ResponseType.LIVE_EXECUTION
    ).summary(
        "Mission executing: extracting competitor pricing..."
    ).add_mission(mission).live_stream(
        "stream-mission-abc123"
    ).build()
    
    decision = resolve_presentation(response)
    
    print(f"Response Type: {response.response_type.value}")
    print(f"Mission ID: {mission.mission_id}")
    print(f"Stream ID: {response.live_stream_id}")
    print(f"\nRouting Decision:")
    print(f"  Mode: {decision.mode.value}")
    print(f"  Priority: {decision.priority}")
    print(f"  Rationale: {decision.rationale}")
    print(f"  Streaming: {decision.streaming}")
    print(f"  Interactive: {decision.interactive}")


# =============================================================================
# EXAMPLE 7: Mixed artifacts (multiple presentation modes)
# =============================================================================

def example_mixed_artifacts():
    """Route response with multiple artifact types."""
    print("\n=== EXAMPLE 7: Mixed Artifacts (Multiple Modes) ===")
    
    table = TableArtifact(
        title="Companies Found",
        columns=["Name", "Sector"],
        rows=[["TechCorp", "SaaS"], ["InnovateInc", "AI"]],
    )
    
    doc = DocumentArtifact(
        title="Extraction Results",
        sections=[
            {"heading": "Summary", "content": "Found 2 companies matching criteria..."}
        ],
    )
    
    response = ResponseBuilder().type(
        ResponseType.ARTIFACT_BUNDLE
    ).summary(
        "Extraction complete: data and summary"
    ).add_artifact(table).add_artifact(doc).build()
    
    decisions = route_all_artifacts(response)
    
    print(f"Response Type: {response.response_type.value}")
    print(f"Artifacts: {len(response.artifacts)}")
    print(f"\nRouting Decisions:")
    for i, (idx, decision) in enumerate(decisions):
        artifact_type = response.artifacts[idx].artifact_type
        print(f"\n  Artifact {i}: {artifact_type}")
        print(f"    Mode: {decision.mode.value}")
        print(f"    Priority: {decision.priority}")
        print(f"    Rationale: {decision.rationale}")


# =============================================================================
# EXAMPLE 8: Large dataset (size-aware routing)
# =============================================================================

def example_large_dataset():
    """Route large dataset with size-aware decisions."""
    print("\n=== EXAMPLE 8: Large Dataset (Size-Aware) ===")
    
    # Simulate large dataset
    large_table = TableArtifact(
        title="All Market Data",
        columns=["ID", "Name", "Sector", "Revenue", "Growth", "Employees"],
        rows=[[i, f"Company{i}", "Tech", "$100M", "25%", "50"] for i in range(5000)],
    )
    
    response = ResponseBuilder().type(
        ResponseType.TABLE
    ).summary(
        "All 5000 companies in database"
    ).add_artifact(large_table).build()
    
    decision = resolve_presentation(response)
    
    print(f"Response Type: {response.response_type.value}")
    print(f"Rows: {large_table.content['row_count']}")
    print(f"Columns: {large_table.content['column_count']}")
    print(f"\nRouting Decision:")
    print(f"  Mode: {decision.mode.value}")
    print(f"  Priority: {decision.priority}")
    print(f"  Size Hint: {decision.size_hint} (paginated by UI)")
    print(f"  Sortable: {decision.sortable}")
    print(f"  Filterable: {decision.filterable}")


# =============================================================================
# EXAMPLE 9: Low priority content (inline text)
# =============================================================================

def example_low_priority():
    """Route low priority content."""
    print("\n=== EXAMPLE 9: Low Priority Content ===")
    
    response = ResponseBuilder().type(
        ResponseType.TEXT
    ).summary(
        "Additional note: This metric was updated last week"
    ).hints(
        priority="low",
    ).build()
    
    decision = resolve_presentation(response)
    
    print(f"Response Type: {response.response_type.value}")
    print(f"Summary: {response.summary}")
    print(f"Priority: {response.ui_hints.priority}")
    print(f"\nRouting Decision:")
    print(f"  Mode: {decision.mode.value}")
    print(f"  Priority: {decision.priority}")
    print(f"  Rationale: {decision.rationale}")
    print(f"  Interactive: {decision.interactive}")


# =============================================================================
# EXAMPLE 10: UI Layout Planning
# =============================================================================

def example_ui_layout_planning():
    """Show complete UI layout planning."""
    print("\n=== EXAMPLE 10: Complete UI Layout Planning ===")
    
    chart = ChartArtifact(
        title="Revenue Trend",
        chart_type="line",
        data=[{"month": "Jan", "value": 100}, {"month": "Feb", "value": 120}],
    )
    
    table = TableArtifact(
        title="Forecast Details",
        columns=["Month", "Value", "Confidence"],
        rows=[["Jan", "100", "95%"], ["Feb", "120", "92%"]],
    )
    
    response = ResponseBuilder().type(
        ResponseType.ARTIFACT_BUNDLE
    ).summary(
        "Q1 forecast with detailed breakdown"
    ).add_artifact(chart).add_artifact(table).build()
    
    layout = route_for_ui_layout(response)
    
    print(f"Response Type: {response.response_type.value}")
    print(f"Summary: {response.summary}")
    print(f"\nLayout Strategy:")
    print(f"  Strategy: {layout['presentation_strategy']}")
    print(f"  Primary Mode: {layout['primary_mode']}")
    print(f"  Artifact Count: {layout['artifact_count']}")
    print(f"\nArtifact Routing:")
    for artifact_info in layout['artifacts']:
        print(f"\n  Artifact {artifact_info['index']}: {artifact_info['type']}")
        print(f"    Mode: {artifact_info['decision']['mode']}")
        print(f"    Priority: {artifact_info['decision']['priority']}")
        print(f"    Sortable: {artifact_info['decision']['sortable']}")
        print(f"    Filterable: {artifact_info['decision']['filterable']}")


# =============================================================================
# RUN ALL EXAMPLES
# =============================================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("PRESENTATION ROUTER EXAMPLES")
    print("="*80)
    
    example_simple_text()
    example_table_artifact()
    example_chart_with_hint()
    example_document_artifact()
    example_timeline_artifact()
    example_live_execution()
    example_mixed_artifacts()
    example_large_dataset()
    example_low_priority()
    example_ui_layout_planning()
    
    print("\n" + "="*80)
    print("END OF EXAMPLES")
    print("="*80)
