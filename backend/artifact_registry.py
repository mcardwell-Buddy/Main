"""
Artifact Registry: Deterministic definitions of all Buddy output types.

Registry only — no execution logic, no LLM calls, no UI rendering.
Pure data contract for what Buddy can produce.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import json
import uuid


class VisualizationType(Enum):
    """Allowed visualization modes for artifacts."""
    TABLE = "table"
    EXPANDED_PANEL = "expanded_panel"
    CARD = "card"
    TIMELINE = "timeline"
    CHART = "chart"
    DOCUMENT = "document"
    MONITOR = "live_monitor"
    CODE_BLOCK = "code_block"
    SUMMARY_ROW = "summary_row"


@dataclass
class SizeConstraints:
    """Size and content limits for artifacts."""
    max_fields: int = 50
    max_rows: int = 10000
    max_file_size_mb: int = 100
    max_text_length: int = 100000
    max_sections: int = 20
    max_items_in_list: int = 1000

    def to_dict(self) -> Dict[str, Any]:
        return {
            'max_fields': self.max_fields,
            'max_rows': self.max_rows,
            'max_file_size_mb': self.max_file_size_mb,
            'max_text_length': self.max_text_length,
            'max_sections': self.max_sections,
            'max_items_in_list': self.max_items_in_list,
        }


@dataclass
class ArtifactDefinition:
    """Registry entry for a single artifact type."""
    artifact_type: str
    description: str
    required_fields: List[str]
    optional_fields: List[str]
    allowed_visualizations: List[VisualizationType]
    size_constraints: SizeConstraints
    use_cases: List[str] = field(default_factory=list)
    storage_location: str = "mission_artifacts"
    is_streaming: bool = False
    supports_export: bool = True
    export_formats: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'artifact_type': self.artifact_type,
            'description': self.description,
            'required_fields': self.required_fields,
            'optional_fields': self.optional_fields,
            'allowed_visualizations': [v.value for v in self.allowed_visualizations],
            'size_constraints': self.size_constraints.to_dict(),
            'use_cases': self.use_cases,
            'storage_location': self.storage_location,
            'is_streaming': self.is_streaming,
            'supports_export': self.supports_export,
            'export_formats': self.export_formats,
        }


# =============================================================================
# ARTIFACT REGISTRY (9 artifact types)
# =============================================================================

BUSINESS_PLAN = ArtifactDefinition(
    artifact_type="business_plan",
    description="Comprehensive business plan document with strategy, financials, and roadmap",
    required_fields=[
        "executive_summary",
        "market_analysis",
        "value_proposition",
        "financial_projections",
    ],
    optional_fields=[
        "team_structure",
        "competitive_landscape",
        "risk_analysis",
        "go_to_market_strategy",
        "funding_requirements",
        "appendix",
    ],
    allowed_visualizations=[
        VisualizationType.DOCUMENT,
        VisualizationType.EXPANDED_PANEL,
        VisualizationType.CARD,
    ],
    size_constraints=SizeConstraints(
        max_sections=15,
        max_text_length=200000,
    ),
    use_cases=[
        "Startup planning",
        "Fundraising preparation",
        "Strategic planning",
        "Investor presentations",
    ],
    export_formats=["pdf", "docx", "md"],
)

FORECAST_REPORT = ArtifactDefinition(
    artifact_type="forecast_report",
    description="Data-driven forecast with predictions, confidence intervals, and assumptions",
    required_fields=[
        "metric",
        "forecast_values",
        "time_period",
        "confidence_intervals",
        "assumptions",
    ],
    optional_fields=[
        "historical_baseline",
        "sensitivity_analysis",
        "scenario_analysis",
        "error_metrics",
        "notes",
    ],
    allowed_visualizations=[
        VisualizationType.CHART,
        VisualizationType.TABLE,
        VisualizationType.EXPANDED_PANEL,
    ],
    size_constraints=SizeConstraints(
        max_rows=5000,
        max_fields=20,
    ),
    use_cases=[
        "Revenue forecasting",
        "Demand planning",
        "Resource allocation",
        "Risk assessment",
    ],
    export_formats=["csv", "xlsx", "json"],
)

OPPORTUNITY_BRIEF = ArtifactDefinition(
    artifact_type="opportunity_brief",
    description="Concise opportunity analysis with potential, impact, and action items",
    required_fields=[
        "opportunity_title",
        "description",
        "potential_impact",
        "effort_estimate",
        "recommended_actions",
    ],
    optional_fields=[
        "market_size",
        "competitive_advantages",
        "risks",
        "timeline",
        "required_resources",
        "success_metrics",
    ],
    allowed_visualizations=[
        VisualizationType.CARD,
        VisualizationType.EXPANDED_PANEL,
        VisualizationType.DOCUMENT,
    ],
    size_constraints=SizeConstraints(
        max_text_length=50000,
        max_items_in_list=20,
    ),
    use_cases=[
        "Business development",
        "Strategic initiatives",
        "Investment evaluation",
        "Project scoping",
    ],
    export_formats=["pdf", "md", "txt"],
)

MISSION_SUMMARY = ArtifactDefinition(
    artifact_type="mission_summary",
    description="Structured summary of completed mission with objectives, results, and metrics",
    required_fields=[
        "mission_id",
        "objective",
        "status",
        "completion_time",
        "key_results",
    ],
    optional_fields=[
        "actions_taken",
        "data_collected",
        "errors_encountered",
        "resources_used",
        "recommendations",
        "follow_up_actions",
    ],
    allowed_visualizations=[
        VisualizationType.CARD,
        VisualizationType.TABLE,
        VisualizationType.EXPANDED_PANEL,
    ],
    size_constraints=SizeConstraints(
        max_fields=30,
        max_items_in_list=50,
    ),
    use_cases=[
        "Mission tracking",
        "Audit logs",
        "Performance reporting",
        "Historical analysis",
    ],
    export_formats=["json", "csv", "md"],
)

RISK_MEMO = ArtifactDefinition(
    artifact_type="risk_memo",
    description="Risk assessment document with identified risks, impacts, and mitigation strategies",
    required_fields=[
        "risk_summary",
        "identified_risks",
        "impact_assessment",
        "probability",
    ],
    optional_fields=[
        "mitigation_strategies",
        "contingency_plans",
        "risk_owners",
        "review_date",
        "historical_precedent",
    ],
    allowed_visualizations=[
        VisualizationType.DOCUMENT,
        VisualizationType.TABLE,
        VisualizationType.EXPANDED_PANEL,
    ],
    size_constraints=SizeConstraints(
        max_text_length=75000,
        max_items_in_list=30,
    ),
    use_cases=[
        "Risk management",
        "Decision support",
        "Compliance reporting",
        "Strategic planning",
    ],
    export_formats=["pdf", "docx", "md"],
)

DATASET = ArtifactDefinition(
    artifact_type="dataset",
    description="Structured data collection with rows, columns, and metadata",
    required_fields=[
        "columns",
        "rows",
        "row_count",
        "column_count",
    ],
    optional_fields=[
        "metadata",
        "data_types",
        "statistics",
        "quality_score",
        "source",
        "timestamp",
    ],
    allowed_visualizations=[
        VisualizationType.TABLE,
        VisualizationType.CHART,
        VisualizationType.SUMMARY_ROW,
    ],
    size_constraints=SizeConstraints(
        max_rows=100000,
        max_fields=100,
        max_file_size_mb=500,
    ),
    use_cases=[
        "Data analysis",
        "Reporting",
        "Decision making",
        "Machine learning",
    ],
    export_formats=["csv", "json", "xlsx", "parquet"],
)

CHART = ArtifactDefinition(
    artifact_type="chart",
    description="Visual representation of data with chart type, series, and axis configuration",
    required_fields=[
        "chart_type",
        "data",
        "title",
    ],
    optional_fields=[
        "x_axis_label",
        "y_axis_label",
        "series_labels",
        "color_scheme",
        "legend",
        "annotations",
        "scale_type",
    ],
    allowed_visualizations=[
        VisualizationType.CHART,
        VisualizationType.EXPANDED_PANEL,
    ],
    size_constraints=SizeConstraints(
        max_rows=50000,
        max_fields=10,
    ),
    use_cases=[
        "Data visualization",
        "Trend analysis",
        "Comparative analysis",
        "Presentations",
    ],
    export_formats=["png", "svg", "json", "pdf"],
)

TIMELINE = ArtifactDefinition(
    artifact_type="timeline",
    description="Sequence of events, milestones, or actions ordered chronologically",
    required_fields=[
        "events",
        "start_date",
        "end_date",
    ],
    optional_fields=[
        "phases",
        "dependencies",
        "owner_assignments",
        "status_updates",
        "completion_percentage",
    ],
    allowed_visualizations=[
        VisualizationType.TIMELINE,
        VisualizationType.TABLE,
        VisualizationType.EXPANDED_PANEL,
    ],
    size_constraints=SizeConstraints(
        max_items_in_list=500,
        max_fields=20,
    ),
    use_cases=[
        "Project planning",
        "Roadmap visualization",
        "Process documentation",
        "Milestone tracking",
    ],
    export_formats=["json", "csv", "ics"],
)

LIVE_MONITOR = ArtifactDefinition(
    artifact_type="live_monitor",
    description="Real-time streaming data with updates, metrics, and status indicators",
    required_fields=[
        "stream_id",
        "metric_name",
        "current_value",
    ],
    optional_fields=[
        "historical_values",
        "thresholds",
        "status_indicator",
        "last_update",
        "update_frequency",
        "alerts",
    ],
    allowed_visualizations=[
        VisualizationType.MONITOR,
        VisualizationType.CHART,
        VisualizationType.SUMMARY_ROW,
    ],
    size_constraints=SizeConstraints(
        max_items_in_list=1000,
        max_fields=50,
    ),
    use_cases=[
        "Real-time monitoring",
        "System health tracking",
        "Mission progress updates",
        "Performance metrics",
    ],
    is_streaming=True,
    export_formats=["json", "csv"],
)

# =============================================================================
# REGISTRY OPERATIONS
# =============================================================================

# Master registry mapping artifact_type -> definition
ARTIFACT_REGISTRY: Dict[str, ArtifactDefinition] = {
    "business_plan": BUSINESS_PLAN,
    "forecast_report": FORECAST_REPORT,
    "opportunity_brief": OPPORTUNITY_BRIEF,
    "mission_summary": MISSION_SUMMARY,
    "risk_memo": RISK_MEMO,
    "dataset": DATASET,
    "chart": CHART,
    "timeline": TIMELINE,
    "live_monitor": LIVE_MONITOR,
}


def get_artifact_definition(artifact_type: str) -> Optional[ArtifactDefinition]:
    """Retrieve definition for a given artifact type."""
    return ARTIFACT_REGISTRY.get(artifact_type)


def validate_artifact_type(artifact_type: str) -> bool:
    """Check if artifact type is registered."""
    return artifact_type in ARTIFACT_REGISTRY


def list_all_artifact_types() -> List[str]:
    """Get list of all registered artifact types."""
    return list(ARTIFACT_REGISTRY.keys())


def get_artifact_types_by_visualization(
    visualization_type: VisualizationType,
) -> List[str]:
    """Get artifact types that support a given visualization."""
    return [
        artifact_type
        for artifact_type, definition in ARTIFACT_REGISTRY.items()
        if visualization_type in definition.allowed_visualizations
    ]


def get_artifact_types_by_use_case(use_case: str) -> List[str]:
    """Get artifact types matching a use case."""
    return [
        artifact_type
        for artifact_type, definition in ARTIFACT_REGISTRY.items()
        if use_case in definition.use_cases
    ]


def validate_required_fields(
    artifact_type: str, 
    provided_fields: List[str],
) -> tuple[bool, List[str]]:
    """
    Validate that all required fields are present.
    
    Returns:
        (is_valid, missing_fields)
    """
    definition = get_artifact_definition(artifact_type)
    if not definition:
        return False, []
    
    missing = set(definition.required_fields) - set(provided_fields)
    return len(missing) == 0, list(missing)


def validate_field_names(
    artifact_type: str,
    provided_fields: List[str],
) -> tuple[bool, List[str]]:
    """
    Validate that field names are in allowed set (required + optional).
    
    Returns:
        (is_valid, unknown_fields)
    """
    definition = get_artifact_definition(artifact_type)
    if not definition:
        return False, []
    
    allowed_fields = set(definition.required_fields + definition.optional_fields)
    unknown = set(provided_fields) - allowed_fields
    return len(unknown) == 0, list(unknown)


def serialize_registry() -> Dict[str, Any]:
    """Serialize entire registry to dictionary."""
    return {
        artifact_type: definition.to_dict()
        for artifact_type, definition in ARTIFACT_REGISTRY.items()
    }


# =============================================================================
# CONSTANTS
# =============================================================================

# All artifact types
ALL_ARTIFACT_TYPES = list(ARTIFACT_REGISTRY.keys())

# Document types (suitable for export to PDF/DOCX)
DOCUMENT_ARTIFACT_TYPES = [
    "business_plan",
    "risk_memo",
    "opportunity_brief",
    "mission_summary",
]

# Data types (suitable for export to CSV/JSON)
DATA_ARTIFACT_TYPES = [
    "dataset",
    "forecast_report",
    "timeline",
    "live_monitor",
]

# Visual types (suitable for chart rendering)
VISUAL_ARTIFACT_TYPES = [
    "chart",
    "timeline",
    "forecast_report",
    "live_monitor",
]

# Streaming types (support real-time updates)
STREAMING_ARTIFACT_TYPES = [
    "live_monitor",
]


# =============================================================================
# PHASE 12: ARTIFACT REGISTRY SCHEMA (FIRST-CLASS)
# =============================================================================


class ArtifactType(Enum):
    """Supported artifact types (Phase 12)."""
    REPORT = "report"
    DATASET = "dataset"
    CHART = "chart"
    PLAN = "plan"
    LOG = "log"
    BUILD_OUTPUT = "build_output"
    FORECAST = "forecast"


class PresentationHint(Enum):
    """Presentation hints for UI routing (read-only)."""
    TEXT = "text"
    TABLE = "table"
    CHART = "chart"
    DOCUMENT = "document"
    DOWNLOAD = "download"
    LIVE_PANEL = "live_panel"


class ArtifactStatus(Enum):
    """Artifact lifecycle status."""
    DRAFT = "draft"
    FINAL = "final"
    DEPRECATED = "deprecated"
    SUPERSEDED = "superseded"


@dataclass(frozen=True)
class Artifact:
    """Artifact registry record (Phase 12)."""
    artifact_id: str
    artifact_type: ArtifactType
    title: str
    description: str
    created_by: str
    source_module: str
    presentation_hint: PresentationHint
    created_at: str
    tags: List[str] = field(default_factory=list)
    file_path: Optional[str] = None
    mime_type: Optional[str] = None
    confidence: Optional[float] = None
    status: ArtifactStatus = ArtifactStatus.DRAFT

    @staticmethod
    def new(
        artifact_type: ArtifactType,
        title: str,
        description: str,
        created_by: str,
        source_module: str,
        presentation_hint: PresentationHint,
        tags: Optional[List[str]] = None,
        file_path: Optional[str] = None,
        mime_type: Optional[str] = None,
        confidence: Optional[float] = None,
        status: ArtifactStatus = ArtifactStatus.DRAFT,
    ) -> "Artifact":
        """Create a new Artifact with generated ID and timestamp."""
        return Artifact(
            artifact_id=str(uuid.uuid4()),
            artifact_type=artifact_type,
            title=title,
            description=description,
            created_by=created_by,
            source_module=source_module,
            file_path=file_path,
            mime_type=mime_type,
            presentation_hint=presentation_hint,
            confidence=confidence,
            created_at=datetime.now(timezone.utc).isoformat(),
            tags=tags or [],
            status=status,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "artifact_id": self.artifact_id,
            "artifact_type": self.artifact_type.value,
            "title": self.title,
            "description": self.description,
            "created_by": self.created_by,
            "source_module": self.source_module,
            "file_path": self.file_path,
            "mime_type": self.mime_type,
            "presentation_hint": self.presentation_hint.value,
            "confidence": self.confidence,
            "created_at": self.created_at,
            "tags": list(self.tags),
            "status": self.status.value,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Artifact":
        """Deserialize from dictionary."""
        return Artifact(
            artifact_id=data.get("artifact_id") or str(uuid.uuid4()),
            artifact_type=ArtifactType(data.get("artifact_type", ArtifactType.REPORT.value)),
            title=data.get("title", ""),
            description=data.get("description", ""),
            created_by=data.get("created_by", ""),
            source_module=data.get("source_module", ""),
            file_path=data.get("file_path"),
            mime_type=data.get("mime_type"),
            presentation_hint=PresentationHint(
                data.get("presentation_hint", PresentationHint.TEXT.value)
            ),
            confidence=data.get("confidence"),
            created_at=data.get("created_at") or datetime.now(timezone.utc).isoformat(),
            tags=list(data.get("tags", [])),
            status=ArtifactStatus(data.get("status", ArtifactStatus.DRAFT.value)),
        )


# =============================================================================
# BUILD ARTIFACT REGISTRY (Phase 11)
# =============================================================================


@dataclass(frozen=True)
class BuildArtifactRecord:
    """Immutable record of a build artifact."""
    artifact_id: str
    build_id: str
    artifact_type: str
    description: str
    created_from_mission: Optional[str]
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "build_id": self.build_id,
            "artifact_type": self.artifact_type,
            "description": self.description,
            "created_from_mission": self.created_from_mission,
            "timestamp": self.timestamp,
        }


class BuildArtifactRegistry:
    """Append-only registry of build artifacts (JSONL)."""

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or (Path(__file__).parent.parent / "outputs" / "phase11")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.artifacts_file = self.output_dir / "build_artifacts.jsonl"

    def register_artifact(
        self,
        artifact_id: str,
        build_id: str,
        artifact_type: str,
        description: str,
        created_from_mission: Optional[str] = None,
        timestamp: Optional[str] = None,
    ) -> BuildArtifactRecord:
        """Register a build artifact (append-only)."""
        record = BuildArtifactRecord(
            artifact_id=artifact_id,
            build_id=build_id,
            artifact_type=artifact_type,
            description=description,
            created_from_mission=created_from_mission,
            timestamp=timestamp or datetime.now(timezone.utc).isoformat(),
        )
        self._append_record(record)
        return record

    def get_artifacts_for_build(self, build_id: str) -> List[BuildArtifactRecord]:
        """Return all artifacts for a build."""
        return [r for r in self.read_records() if r.build_id == build_id]

    def read_records(self) -> List[BuildArtifactRecord]:
        """Read all build artifact records from JSONL."""
        if not self.artifacts_file.exists():
            return []
        records: List[BuildArtifactRecord] = []
        with self.artifacts_file.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                records.append(BuildArtifactRecord(**data))
        return records

    def _append_record(self, record: BuildArtifactRecord) -> None:
        with self.artifacts_file.open("a", encoding="utf-8") as f:
            json.dump(record.to_dict(), f)
            f.write("\n")
