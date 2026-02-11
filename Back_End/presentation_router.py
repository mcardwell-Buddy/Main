"""
Presentation Router: Deterministic routing of ResponseEnvelope + Artifacts
to presentation modes.

No UI code, no rendering, no execution logic. Pure routing rules.
"""

from enum import Enum
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from Back_End.response_envelope import (
    ResponseEnvelope,
    ResponseType,
    ArtifactType,
)
from Back_End.artifact_registry import (
    get_artifact_definition,
    VisualizationType,
)


class PresentationMode(Enum):
    """Available presentation modes for artifacts and responses."""
    CHAT_TEXT = "chat_text"
    EXPANDABLE_CARD = "expandable_card"
    TABLE = "table"
    CHART = "chart"
    TIMELINE = "timeline"
    LIVE_STREAM = "live_stream"


@dataclass
class PresentationDecision:
    """Routing decision with metadata."""
    mode: PresentationMode
    priority: int  # 0-100, higher = more important
    rationale: str  # Why this mode was chosen
    fallback_mode: Optional[PresentationMode] = None  # If primary fails
    size_hint: Optional[str] = None  # "compact", "normal", "expanded"
    interactive: bool = False  # Whether mode supports interaction
    sortable: bool = False  # Whether results can be sorted
    filterable: bool = False  # Whether results can be filtered
    exportable: bool = False  # Whether data can be exported
    streaming: bool = False  # Whether mode supports live updates

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            'mode': self.mode.value,
            'priority': self.priority,
            'rationale': self.rationale,
            'fallback_mode': self.fallback_mode.value if self.fallback_mode else None,
            'size_hint': self.size_hint,
            'interactive': self.interactive,
            'sortable': self.sortable,
            'filterable': self.filterable,
            'exportable': self.exportable,
            'streaming': self.streaming,
        }


# =============================================================================
# ROUTING RULES (Deterministic, pure functions)
# =============================================================================

def route_response_type(response_type: ResponseType) -> List[PresentationMode]:
    """
    Primary routing based on ResponseType.
    
    Returns ordered list of candidate presentation modes.
    """
    routing_map = {
        ResponseType.TEXT: [PresentationMode.CHAT_TEXT],
        ResponseType.TABLE: [PresentationMode.TABLE, PresentationMode.CHAT_TEXT],
        ResponseType.REPORT: [PresentationMode.EXPANDABLE_CARD, PresentationMode.CHAT_TEXT],
        ResponseType.FORECAST: [PresentationMode.CHART, PresentationMode.TABLE],
        ResponseType.LIVE_EXECUTION: [PresentationMode.LIVE_STREAM, PresentationMode.CHAT_TEXT],
        ResponseType.ARTIFACT_BUNDLE: [
            PresentationMode.EXPANDABLE_CARD,
            PresentationMode.CHART,
            PresentationMode.TABLE,
        ],
        ResponseType.CLARIFICATION_REQUEST: [PresentationMode.CHAT_TEXT],
    }
    return routing_map.get(response_type, [PresentationMode.CHAT_TEXT])


def route_artifact_type(artifact_type: str) -> List[PresentationMode]:
    """
    Route based on artifact type.
    
    Returns ordered list of candidate presentation modes.
    """
    routing_map = {
        "business_plan": [
            PresentationMode.EXPANDABLE_CARD,
            PresentationMode.CHAT_TEXT,
        ],
        "forecast_report": [
            PresentationMode.CHART,
            PresentationMode.TABLE,
            PresentationMode.EXPANDABLE_CARD,
        ],
        "opportunity_brief": [
            PresentationMode.EXPANDABLE_CARD,
            PresentationMode.CHAT_TEXT,
        ],
        "mission_summary": [
            PresentationMode.EXPANDABLE_CARD,
            PresentationMode.TABLE,
        ],
        "risk_memo": [
            PresentationMode.EXPANDABLE_CARD,
            PresentationMode.CHAT_TEXT,
        ],
        "dataset": [
            PresentationMode.TABLE,
            PresentationMode.CHART,
            PresentationMode.EXPANDABLE_CARD,
        ],
        "chart": [
            PresentationMode.CHART,
            PresentationMode.TABLE,
        ],
        "timeline": [
            PresentationMode.TIMELINE,
            PresentationMode.TABLE,
        ],
        "live_monitor": [
            PresentationMode.LIVE_STREAM,
            PresentationMode.CHART,
            PresentationMode.TABLE,
        ],
    }
    return routing_map.get(artifact_type, [PresentationMode.EXPANDABLE_CARD])


def route_visualization_type(viz_type: VisualizationType) -> List[PresentationMode]:
    """
    Route based on visualization hint from UIHints.
    
    Returns ordered list of candidate presentation modes.
    """
    routing_map = {
        VisualizationType.TABLE: [PresentationMode.TABLE],
        VisualizationType.EXPANDED_PANEL: [PresentationMode.EXPANDABLE_CARD],
        VisualizationType.CARD: [PresentationMode.EXPANDABLE_CARD],
        VisualizationType.TIMELINE: [PresentationMode.TIMELINE],
        VisualizationType.CHART: [PresentationMode.CHART],
        VisualizationType.DOCUMENT: [PresentationMode.EXPANDABLE_CARD],
        VisualizationType.MONITOR: [PresentationMode.LIVE_STREAM],
        VisualizationType.CODE_BLOCK: [PresentationMode.EXPANDABLE_CARD],
        VisualizationType.SUMMARY_ROW: [PresentationMode.TABLE],
    }
    return routing_map.get(viz_type, [PresentationMode.EXPANDABLE_CARD])


def route_by_size(
    row_count: int,
    field_count: int,
) -> Optional[PresentationMode]:
    """
    Route based on data size.
    
    Large datasets may need paginated tables vs inline rendering.
    Returns None if no size-based routing applies.
    """
    # Small dataset: inline table
    if row_count <= 100 and field_count <= 5:
        return PresentationMode.TABLE
    
    # Large dataset: paginated table
    if row_count > 10000 or field_count > 50:
        return PresentationMode.TABLE  # UI handles pagination
    
    # Medium dataset: chart for visualization
    if row_count > 500 and field_count <= 10:
        return PresentationMode.CHART
    
    return None


def route_by_priority(priority: Optional[str]) -> Optional[PresentationMode]:
    """
    Route based on UIHints priority level.
    
    High priority items may be presented prominently.
    Returns None if no priority-based routing applies.
    """
    if priority == "high":
        return PresentationMode.EXPANDABLE_CARD
    
    if priority == "normal":
        return None  # Use standard routing
    
    if priority == "low":
        return PresentationMode.CHAT_TEXT  # Inline as text
    
    return None


# =============================================================================
# RESOLUTION ENGINE (Deterministic decision making)
# =============================================================================

def resolve_presentation(
    response_envelope: ResponseEnvelope,
    artifact_index: int = 0,
) -> PresentationDecision:
    """
    Deterministically resolve presentation mode for ResponseEnvelope.
    
    Algorithm:
    1. Collect candidates from ResponseType, ArtifactType, UIHints, Size
    2. Find intersection (modes suggested by multiple sources)
    3. Pick highest priority intersection candidate
    4. Fall back to first response_type candidate
    
    Args:
        response_envelope: The response to route
        artifact_index: Which artifact to route (0-based)
    
    Returns:
        PresentationDecision with mode and metadata
    """
    
    # Step 1: Collect candidate modes from all sources
    candidates = {
        'response_type': route_response_type(response_envelope.response_type),
        'artifact_type': [],
        'visualization': [],
        'size': [],
        'priority': [],
    }
    
    # Get artifact-specific routing if artifacts exist
    if response_envelope.artifacts and artifact_index < len(response_envelope.artifacts):
        artifact = response_envelope.artifacts[artifact_index]
        candidates['artifact_type'] = route_artifact_type(artifact.artifact_type)
    
    # Get visualization hint routing if UIHints present
    if response_envelope.ui_hints and response_envelope.ui_hints.layout:
        viz_from_layout = {
            'fullscreen': [PresentationMode.CHART, PresentationMode.TABLE],
            'expanded_panel': [PresentationMode.EXPANDABLE_CARD],
            'split': [PresentationMode.TABLE, PresentationMode.CHART],
            'inline': [PresentationMode.CHAT_TEXT],
            'modal': [PresentationMode.EXPANDABLE_CARD],
        }.get(response_envelope.ui_hints.layout, [])
        candidates['visualization'] = viz_from_layout
    
    # Get size-based routing for datasets
    if response_envelope.artifacts and artifact_index < len(response_envelope.artifacts):
        artifact = response_envelope.artifacts[artifact_index]
        if hasattr(artifact, 'row_count') and hasattr(artifact, 'field_count'):
            size_mode = route_by_size(artifact.row_count, artifact.field_count)
            if size_mode:
                candidates['size'] = [size_mode]
    
    # Get priority-based routing
    if response_envelope.ui_hints and response_envelope.ui_hints.priority:
        priority_mode = route_by_priority(response_envelope.ui_hints.priority)
        if priority_mode:
            candidates['priority'] = [priority_mode]
    
    # Step 2: Find intersection (modes suggested by multiple sources)
    all_candidates = [
        mode for modes in candidates.values()
        for mode in modes
    ]
    
    # Intersection: modes that appear in multiple sources
    mode_scores = {}
    for mode in all_candidates:
        count = sum(1 for modes in candidates.values() if mode in modes)
        mode_scores[mode] = count
    
    # Step 3: Pick highest scoring mode
    if mode_scores:
        best_mode = max(mode_scores.items(), key=lambda x: x[1])[0]
        score = mode_scores[best_mode]
        priority_value = score * 33  # Convert to 0-100 scale (max 3 sources)
    else:
        # Fallback to response_type primary
        best_mode = candidates['response_type'][0] if candidates['response_type'] else PresentationMode.CHAT_TEXT
        priority_value = 50
    
    # Step 4: Determine rationale
    rationale_parts = []
    if best_mode in candidates['response_type']:
        rationale_parts.append(f"ResponseType={response_envelope.response_type.value}")
    if best_mode in candidates['artifact_type']:
        if response_envelope.artifacts:
            rationale_parts.append(f"ArtifactType={response_envelope.artifacts[artifact_index].artifact_type.value}")
    if best_mode in candidates['visualization']:
        if response_envelope.ui_hints and response_envelope.ui_hints.layout:
            rationale_parts.append(f"LayoutHint={response_envelope.ui_hints.layout}")
    if best_mode in candidates['size']:
        rationale_parts.append("SizeHint=optimized")
    if best_mode in candidates['priority']:
        rationale_parts.append(f"Priority={response_envelope.ui_hints.priority}")
    
    rationale = " + ".join(rationale_parts) if rationale_parts else "Default routing"
    
    # Determine capabilities based on mode
    capabilities = get_presentation_capabilities(best_mode)
    
    # Determine size hint
    size_hint = determine_size_hint(response_envelope, artifact_index)
    
    return PresentationDecision(
        mode=best_mode,
        priority=int(priority_value),
        rationale=rationale,
        fallback_mode=candidates['response_type'][1] if len(candidates['response_type']) > 1 else None,
        size_hint=size_hint,
        interactive=capabilities['interactive'],
        sortable=capabilities['sortable'],
        filterable=capabilities['filterable'],
        exportable=capabilities['exportable'],
        streaming=capabilities['streaming'],
    )


def get_presentation_capabilities(mode: PresentationMode) -> Dict[str, bool]:
    """Get capabilities for a presentation mode."""
    capabilities = {
        PresentationMode.CHAT_TEXT: {
            'interactive': False,
            'sortable': False,
            'filterable': False,
            'exportable': True,
            'streaming': False,
        },
        PresentationMode.EXPANDABLE_CARD: {
            'interactive': True,
            'sortable': False,
            'filterable': False,
            'exportable': True,
            'streaming': False,
        },
        PresentationMode.TABLE: {
            'interactive': True,
            'sortable': True,
            'filterable': True,
            'exportable': True,
            'streaming': False,
        },
        PresentationMode.CHART: {
            'interactive': True,
            'sortable': False,
            'filterable': True,
            'exportable': True,
            'streaming': False,
        },
        PresentationMode.TIMELINE: {
            'interactive': True,
            'sortable': False,
            'filterable': True,
            'exportable': True,
            'streaming': False,
        },
        PresentationMode.LIVE_STREAM: {
            'interactive': True,
            'sortable': False,
            'filterable': False,
            'exportable': False,
            'streaming': True,
        },
    }
    return capabilities.get(mode, {
        'interactive': False,
        'sortable': False,
        'filterable': False,
        'exportable': False,
        'streaming': False,
    })


def determine_size_hint(
    response_envelope: ResponseEnvelope,
    artifact_index: int = 0,
) -> Optional[str]:
    """Determine size hint based on content."""
    if not response_envelope.artifacts or artifact_index >= len(response_envelope.artifacts):
        return None
    
    artifact = response_envelope.artifacts[artifact_index]
    
    # Check if artifact has size indicators
    if hasattr(artifact, 'row_count'):
        row_count = artifact.row_count
        if row_count > 5000:
            return "compact"  # UI should paginate
        elif row_count > 100:
            return "normal"
        else:
            return "expanded"
    
    if hasattr(artifact, 'text_length'):
        text_len = artifact.text_length
        if text_len > 50000:
            return "compact"
        elif text_len > 10000:
            return "normal"
        else:
            return "expanded"
    
    return "normal"


# =============================================================================
# MULTI-ARTIFACT ROUTING
# =============================================================================

def route_all_artifacts(
    response_envelope: ResponseEnvelope,
) -> List[Tuple[int, PresentationDecision]]:
    """
    Route all artifacts in response.
    
    Returns:
        List of (artifact_index, PresentationDecision) tuples
    """
    decisions = []
    for i in range(len(response_envelope.artifacts)):
        decision = resolve_presentation(response_envelope, artifact_index=i)
        decisions.append((i, decision))
    return decisions


def has_mixed_presentation_modes(response_envelope: ResponseEnvelope) -> bool:
    """Check if response has artifacts requiring different presentation modes."""
    if not response_envelope.artifacts or len(response_envelope.artifacts) < 2:
        return False
    
    decisions = route_all_artifacts(response_envelope)
    modes = set(d[1].mode for d in decisions)
    return len(modes) > 1


# =============================================================================
# BATCH ROUTING (For UI planning)
# =============================================================================

def route_for_ui_layout(
    response_envelope: ResponseEnvelope,
) -> Dict[str, Any]:
    """
    Plan complete UI layout based on routing decisions.
    
    Returns dict with layout strategy.
    """
    decisions = route_all_artifacts(response_envelope)
    
    return {
        'response_type': response_envelope.response_type.value,
        'summary': response_envelope.summary,
        'artifact_count': len(response_envelope.artifacts),
        'has_missions': len(response_envelope.missions_spawned) > 0,
        'has_signals': len(response_envelope.signals_emitted) > 0,
        'presentation_strategy': 'mixed' if has_mixed_presentation_modes(response_envelope) else 'unified',
        'artifacts': [
            {
                'index': i,
                'type': response_envelope.artifacts[i].artifact_type,
                'decision': decision.to_dict(),
            }
            for i, decision in decisions
        ],
        'primary_mode': decisions[0][1].mode.value if decisions else None,
        'fallback_mode': decisions[0][1].fallback_mode.value if decisions and decisions[0][1].fallback_mode else None,
    }


# =============================================================================
# CONSTANTS
# =============================================================================

PRESENTATION_MODES = list(PresentationMode)
MODE_NAMES = [mode.value for mode in PRESENTATION_MODES]

