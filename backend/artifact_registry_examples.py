"""
Example Artifact Definitions: How to create and work with artifacts.

These are registry-based examples showing deterministic artifact structures.
Registry only — no execution logic.
"""

from backend.artifact_registry import (
    ArtifactDefinition,
    VisualizationType,
    SizeConstraints,
    get_artifact_definition,
    validate_required_fields,
    validate_field_names,
    list_all_artifact_types,
    serialize_registry,
)


# =============================================================================
# EXAMPLE 1: Retrieve and validate a business plan
# =============================================================================

def example_business_plan_usage():
    """Show how to retrieve and use business_plan definition."""
    
    # Get the artifact definition
    definition = get_artifact_definition("business_plan")
    
    print("=== Business Plan Artifact ===")
    print(f"Type: {definition.artifact_type}")
    print(f"Description: {definition.description}")
    print(f"\nRequired Fields:")
    for field in definition.required_fields:
        print(f"  - {field}")
    
    print(f"\nOptional Fields:")
    for field in definition.optional_fields:
        print(f"  - {field}")
    
    print(f"\nAllowed Visualizations:")
    for viz in definition.allowed_visualizations:
        print(f"  - {viz.value}")
    
    print(f"\nSize Constraints:")
    constraints = definition.size_constraints.to_dict()
    for key, value in constraints.items():
        print(f"  {key}: {value}")
    
    print(f"\nUse Cases:")
    for use_case in definition.use_cases:
        print(f"  - {use_case}")
    
    print(f"\nExport Formats: {', '.join(definition.export_formats)}")
    
    # Validate a hypothetical business plan submission
    submitted_fields = [
        "executive_summary",
        "market_analysis",
        "value_proposition",
        "financial_projections",
        "team_structure",
        "competitive_landscape",
    ]
    
    is_valid, missing = validate_required_fields("business_plan", submitted_fields)
    print(f"\nValidation: {'PASS' if is_valid else 'FAIL'}")
    if not is_valid:
        print(f"Missing required fields: {missing}")


# =============================================================================
# EXAMPLE 2: Validate field names against registry
# =============================================================================

def example_field_validation():
    """Show how to validate fields against artifact definition."""
    
    print("\n=== Field Validation Example ===")
    
    # Good submission (all fields are in allowed set)
    good_fields = ["metric", "forecast_values", "time_period", "confidence_intervals", "assumptions"]
    is_valid, unknown = validate_field_names("forecast_report", good_fields)
    print(f"Good submission: {is_valid}")
    if unknown:
        print(f"  Unknown fields: {unknown}")
    
    # Bad submission (contains unknown field)
    bad_fields = ["metric", "forecast_values", "invalid_field", "time_period"]
    is_valid, unknown = validate_field_names("forecast_report", bad_fields)
    print(f"\nBad submission: {is_valid}")
    if unknown:
        print(f"  Unknown fields: {unknown}")


# =============================================================================
# EXAMPLE 3: List all artifacts and their types
# =============================================================================

def example_list_artifacts():
    """Show how to discover all registered artifacts."""
    
    print("\n=== Registered Artifacts ===")
    
    for artifact_type in list_all_artifact_types():
        definition = get_artifact_definition(artifact_type)
        print(f"\n{artifact_type.upper()}")
        print(f"  {definition.description}")
        print(f"  Visualizations: {', '.join([v.value for v in definition.allowed_visualizations])}")
        print(f"  Streaming: {definition.is_streaming}")


# =============================================================================
# EXAMPLE 4: Working with opportunity brief
# =============================================================================

def example_opportunity_brief():
    """Show opportunity brief structure."""
    
    print("\n=== Opportunity Brief Example ===")
    
    definition = get_artifact_definition("opportunity_brief")
    
    # Hypothetical opportunity brief data
    opportunity_data = {
        "opportunity_title": "Expand into European Market",
        "description": "Establish business presence in 5 European countries",
        "potential_impact": "$2.5M annual revenue",
        "effort_estimate": "6-9 months, 8 full-time staff",
        "recommended_actions": [
            "Conduct market research",
            "Identify local partners",
            "Develop regulatory strategy",
            "Build regional team",
        ],
        "market_size": "$45B TAM",
        "competitive_advantages": ["Technology IP", "Cost structure", "Customer base"],
        "risks": ["Regulatory complexity", "Competition", "Execution risk"],
        "timeline": "Q2-Q4 2026",
        "required_resources": ["Marketing team", "Legal counsel", "Operations staff"],
        "success_metrics": ["50% market penetration", "$2M revenue", "50k users"],
    }
    
    # Validate
    field_names = list(opportunity_data.keys())
    has_required, missing = validate_required_fields("opportunity_brief", field_names)
    has_valid_names, unknown = validate_field_names("opportunity_brief", field_names)
    
    print(f"Data validation:")
    print(f"  Has all required fields: {has_required}")
    print(f"  Field names valid: {has_valid_names}")
    if unknown:
        print(f"  Unknown fields: {unknown}")
    
    print(f"\nData:")
    for key, value in opportunity_data.items():
        if isinstance(value, list):
            print(f"  {key}:")
            for item in value:
                print(f"    - {item}")
        else:
            print(f"  {key}: {value}")


# =============================================================================
# EXAMPLE 5: Working with dataset
# =============================================================================

def example_dataset():
    """Show dataset structure."""
    
    print("\n=== Dataset Example ===")
    
    definition = get_artifact_definition("dataset")
    
    # Hypothetical dataset
    dataset_data = {
        "columns": ["date", "revenue", "users", "retention"],
        "rows": [
            ["2026-01-01", 15000, 250, 0.85],
            ["2026-01-02", 16200, 265, 0.84],
            ["2026-01-03", 17500, 280, 0.86],
        ],
        "row_count": 3,
        "column_count": 4,
        "data_types": ["date", "number", "number", "percent"],
        "source": "Analytics database",
        "quality_score": 0.98,
    }
    
    # Validate
    field_names = list(dataset_data.keys())
    has_required, missing = validate_required_fields("dataset", field_names)
    has_valid_names, unknown = validate_field_names("dataset", field_names)
    
    print(f"Data validation:")
    print(f"  Has all required fields: {has_required}")
    print(f"  Field names valid: {has_valid_names}")
    
    print(f"\nDataset structure:")
    print(f"  Columns: {dataset_data['columns']}")
    print(f"  Row count: {dataset_data['row_count']}")
    print(f"  Column count: {dataset_data['column_count']}")
    print(f"  Quality score: {dataset_data['quality_score']}")
    
    print(f"\nSize constraints:")
    constraints = definition.size_constraints.to_dict()
    for key, value in constraints.items():
        print(f"  {key}: {value}")


# =============================================================================
# EXAMPLE 6: Working with timeline
# =============================================================================

def example_timeline():
    """Show timeline structure."""
    
    print("\n=== Timeline Example ===")
    
    definition = get_artifact_definition("timeline")
    
    # Hypothetical timeline
    timeline_data = {
        "events": [
            {"date": "2026-Q1", "title": "Phase 1: Research", "status": "completed"},
            {"date": "2026-Q2", "title": "Phase 2: Development", "status": "in_progress"},
            {"date": "2026-Q3", "title": "Phase 3: Testing", "status": "planned"},
            {"date": "2026-Q4", "title": "Phase 4: Launch", "status": "planned"},
        ],
        "start_date": "2026-01-01",
        "end_date": "2026-12-31",
        "phases": ["Research", "Development", "Testing", "Launch"],
    }
    
    # Validate
    field_names = list(timeline_data.keys())
    has_required, missing = validate_required_fields("timeline", field_names)
    
    print(f"Data validation:")
    print(f"  Has all required fields: {has_required}")
    
    print(f"\nTimeline structure:")
    print(f"  Start: {timeline_data['start_date']}")
    print(f"  End: {timeline_data['end_date']}")
    print(f"  Phases: {timeline_data['phases']}")
    
    print(f"\nEvents:")
    for event in timeline_data['events']:
        print(f"  {event['date']}: {event['title']} [{event['status']}]")


# =============================================================================
# EXAMPLE 7: Working with forecast report
# =============================================================================

def example_forecast_report():
    """Show forecast report structure."""
    
    print("\n=== Forecast Report Example ===")
    
    definition = get_artifact_definition("forecast_report")
    
    # Hypothetical forecast
    forecast_data = {
        "metric": "Monthly Revenue",
        "time_period": "2026-01 to 2026-12",
        "forecast_values": [
            {"month": "2026-01", "value": 15000},
            {"month": "2026-02", "value": 18000},
            {"month": "2026-03", "value": 21500},
        ],
        "confidence_intervals": [0.95, 0.80, 0.70],
        "assumptions": [
            "Customer acquisition rate: +10% MoM",
            "Churn rate: 5% MoM",
            "ARPU: $60",
        ],
        "historical_baseline": {
            "average": 12000,
            "std_dev": 2500,
        },
    }
    
    # Validate
    field_names = list(forecast_data.keys())
    has_required, missing = validate_required_fields("forecast_report", field_names)
    
    print(f"Data validation:")
    print(f"  Has all required fields: {has_required}")
    
    print(f"\nForecast structure:")
    print(f"  Metric: {forecast_data['metric']}")
    print(f"  Period: {forecast_data['time_period']}")
    print(f"  Confidence levels: {forecast_data['confidence_intervals']}")
    
    print(f"\nAssumptions:")
    for assumption in forecast_data['assumptions']:
        print(f"  - {assumption}")


# =============================================================================
# EXAMPLE 8: Working with live monitor
# =============================================================================

def example_live_monitor():
    """Show live monitor structure."""
    
    print("\n=== Live Monitor Example ===")
    
    definition = get_artifact_definition("live_monitor")
    
    # Hypothetical live monitor
    monitor_data = {
        "stream_id": "stream-mission-abc-123",
        "metric_name": "Data Extraction Progress",
        "current_value": 75,
        "status_indicator": "in_progress",
        "historical_values": [
            {"timestamp": "2026-02-07T20:00:00Z", "value": 25},
            {"timestamp": "2026-02-07T20:15:00Z", "value": 50},
            {"timestamp": "2026-02-07T20:30:00Z", "value": 75},
        ],
        "last_update": "2026-02-07T20:30:15Z",
    }
    
    # Validate
    field_names = list(monitor_data.keys())
    has_required, missing = validate_required_fields("live_monitor", field_names)
    
    print(f"Data validation:")
    print(f"  Has all required fields: {has_required}")
    print(f"  Is streaming: {definition.is_streaming}")
    
    print(f"\nLive Monitor:")
    print(f"  Stream ID: {monitor_data['stream_id']}")
    print(f"  Metric: {monitor_data['metric_name']}")
    print(f"  Current value: {monitor_data['current_value']}%")
    print(f"  Status: {monitor_data['status_indicator']}")
    print(f"  Last update: {monitor_data['last_update']}")


# =============================================================================
# EXAMPLE 9: Serialize entire registry
# =============================================================================

def example_serialize_registry():
    """Show how to serialize the entire registry."""
    
    import json
    
    print("\n=== Serialized Registry (Sample) ===")
    
    registry = serialize_registry()
    
    # Print first artifact only (for brevity)
    first_type = list(registry.keys())[0]
    first_def = registry[first_type]
    
    print(f"\n{first_type}:")
    print(json.dumps(first_def, indent=2))


# =============================================================================
# RUN ALL EXAMPLES
# =============================================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("ARTIFACT REGISTRY EXAMPLES")
    print("="*80)
    
    example_business_plan_usage()
    example_field_validation()
    example_list_artifacts()
    example_opportunity_brief()
    example_dataset()
    example_timeline()
    example_forecast_report()
    example_live_monitor()
    example_serialize_registry()
    
    print("\n" + "="*80)
    print("END OF EXAMPLES")
    print("="*80)
