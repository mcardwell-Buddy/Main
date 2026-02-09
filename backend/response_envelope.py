"""
Response Envelope Schema

Standardized response format for Buddy's outputs to the UI.

NO execution logic, NO UI code, NO autonomy.
Pure data contract for agent → UI communication.
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import json


class ResponseType(Enum):
    """Supported response types."""
    TEXT = "text"
    TABLE = "table"
    REPORT = "report"
    FORECAST = "forecast"
    LIVE_EXECUTION = "live_execution"
    ARTIFACT_BUNDLE = "artifact_bundle"
    CLARIFICATION_REQUEST = "clarification_request"


class ArtifactType(Enum):
    """Typed artifact outputs."""
    TABLE = "table"
    CHART = "chart"
    DOCUMENT = "document"
    CODE_BLOCK = "code_block"
    TIMELINE = "timeline"
    FILE_REFERENCE = "file_reference"
    JSON_DATA = "json_data"
    MISSION_DRAFT = "mission_draft"
    SIGNAL_BATCH = "signal_batch"
    UNIFIED_PROPOSAL = "unified_proposal"  # NEW: Cohesive mission proposal


@dataclass
class Artifact:
    """
    Typed output artifact.
    
    Represents structured data produced by Buddy.
    """
    artifact_type: ArtifactType
    title: str
    content: Any  # Type depends on artifact_type
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            'artifact_type': self.artifact_type.value,
            'title': self.title,
            'content': self.content,
            'metadata': self.metadata
        }


@dataclass
class TableArtifact(Artifact):
    """Table data artifact."""
    
    def __init__(
        self,
        title: str,
        columns: List[str],
        rows: List[List[Any]],
        metadata: Optional[Dict[str, Any]] = None
    ):
        content = {
            'columns': columns,
            'rows': rows,
            'row_count': len(rows),
            'column_count': len(columns)
        }
        super().__init__(
            artifact_type=ArtifactType.TABLE,
            title=title,
            content=content,
            metadata=metadata or {}
        )


@dataclass
class ChartArtifact(Artifact):
    """Chart/visualization artifact."""
    
    def __init__(
        self,
        title: str,
        chart_type: str,  # 'line', 'bar', 'pie', 'scatter'
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ):
        content = {
            'chart_type': chart_type,
            'data': data
        }
        super().__init__(
            artifact_type=ArtifactType.CHART,
            title=title,
            content=content,
            metadata=metadata or {}
        )


@dataclass
class DocumentArtifact(Artifact):
    """Document/report artifact."""
    
    def __init__(
        self,
        title: str,
        sections: List[Dict[str, str]],  # [{'heading': '...', 'content': '...'}]
        format: str = 'markdown',
        metadata: Optional[Dict[str, Any]] = None
    ):
        content = {
            'format': format,
            'sections': sections,
            'section_count': len(sections)
        }
        super().__init__(
            artifact_type=ArtifactType.DOCUMENT,
            title=title,
            content=content,
            metadata=metadata or {}
        )


@dataclass
class CodeBlockArtifact(Artifact):
    """Code snippet artifact."""
    
    def __init__(
        self,
        title: str,
        code: str,
        language: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        content = {
            'code': code,
            'language': language,
            'line_count': len(code.split('\n'))
        }
        super().__init__(
            artifact_type=ArtifactType.CODE_BLOCK,
            title=title,
            content=content,
            metadata=metadata or {}
        )


@dataclass
class TimelineArtifact(Artifact):
    """Timeline/sequence artifact."""
    
    def __init__(
        self,
        title: str,
        events: List[Dict[str, Any]],  # [{'timestamp': '...', 'event': '...', 'status': '...'}]
        metadata: Optional[Dict[str, Any]] = None
    ):
        content = {
            'events': events,
            'event_count': len(events),
            'start_time': events[0]['timestamp'] if events else None,
            'end_time': events[-1]['timestamp'] if events else None
        }
        super().__init__(
            artifact_type=ArtifactType.TIMELINE,
            title=title,
            content=content,
            metadata=metadata or {}
        )


@dataclass
class FileReferenceArtifact(Artifact):
    """File reference artifact."""
    
    def __init__(
        self,
        title: str,
        file_path: str,
        file_type: str,
        size_bytes: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        content = {
            'file_path': file_path,
            'file_type': file_type,
            'size_bytes': size_bytes
        }
        super().__init__(
            artifact_type=ArtifactType.FILE_REFERENCE,
            title=title,
            content=content,
            metadata=metadata or {}
        )


@dataclass
class UIHints:
    """
    Non-binding display hints for UI.
    
    UI is free to ignore these. They're suggestions only.
    """
    layout: Optional[str] = None  # 'fullscreen', 'split', 'inline', 'modal'
    priority: Optional[str] = None  # 'urgent', 'normal', 'low'
    suggested_actions: List[str] = field(default_factory=list)
    color_scheme: Optional[str] = None  # 'success', 'warning', 'error', 'info'
    icon: Optional[str] = None
    expandable: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            'layout': self.layout,
            'priority': self.priority,
            'suggested_actions': self.suggested_actions,
            'color_scheme': self.color_scheme,
            'icon': self.icon,
            'expandable': self.expandable
        }


@dataclass
class MissionReference:
    """Reference to a spawned mission."""
    mission_id: str
    status: str
    objective_type: str
    objective_description: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            'mission_id': self.mission_id,
            'status': self.status,
            'objective_type': self.objective_type,
            'objective_description': self.objective_description
        }


@dataclass
class SignalReference:
    """Reference to an emitted signal."""
    signal_type: str
    signal_layer: str
    signal_source: str
    timestamp: str
    summary: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            'signal_type': self.signal_type,
            'signal_layer': self.signal_layer,
            'signal_source': self.signal_source,
            'timestamp': self.timestamp,
            'summary': self.summary
        }


@dataclass
class ResponseEnvelope:
    """
    Standardized response container for Buddy outputs.
    
    Contract between agent logic and UI rendering.
    NO execution logic. NO UI code. Pure data structure.
    """
    response_type: ResponseType
    summary: str
    artifacts: List[Artifact] = field(default_factory=list)
    missions_spawned: List[MissionReference] = field(default_factory=list)
    signals_emitted: List[SignalReference] = field(default_factory=list)
    reality_assessment: Optional[Dict[str, Any]] = None
    live_stream_id: Optional[str] = None
    ui_hints: Optional[UIHints] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            'response_type': self.response_type.value,
            'summary': self.summary,
            'artifacts': [art.to_dict() for art in self.artifacts],
            'missions_spawned': [m.to_dict() for m in self.missions_spawned],
            'signals_emitted': [s.to_dict() for s in self.signals_emitted],
            'reality_assessment': self.reality_assessment,
            'live_stream_id': self.live_stream_id,
            'ui_hints': self.ui_hints.to_dict() if self.ui_hints else None,
            'timestamp': self.timestamp,
            'metadata': self.metadata
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    def add_artifact(self, artifact: Artifact) -> 'ResponseEnvelope':
        """Add an artifact (fluent interface)."""
        self.artifacts.append(artifact)
        return self
    
    def add_mission(self, mission: MissionReference) -> 'ResponseEnvelope':
        """Add a mission reference (fluent interface)."""
        self.missions_spawned.append(mission)
        return self
    
    def add_signal(self, signal: SignalReference) -> 'ResponseEnvelope':
        """Add a signal reference (fluent interface)."""
        self.signals_emitted.append(signal)
        return self

    def set_reality_assessment(self, assessment: Dict[str, Any]) -> 'ResponseEnvelope':
        """Set the Phase 6 reality assessment (fluent interface)."""
        self.reality_assessment = assessment
        return self

    def set_live_stream_id(self, live_stream_id: str) -> 'ResponseEnvelope':
        """Set the live execution stream ID (fluent interface)."""
        self.live_stream_id = live_stream_id
        return self
    
    def set_ui_hints(self, ui_hints: UIHints) -> 'ResponseEnvelope':
        """Set UI hints (fluent interface)."""
        self.ui_hints = ui_hints
        return self


# ============================================================================
# VALIDATION HELPERS
# ============================================================================

class ResponseValidationError(Exception):
    """Raised when response envelope validation fails."""
    pass


def validate_response_envelope(envelope: ResponseEnvelope) -> bool:
    """
    Validate response envelope structure.
    
    Raises:
        ResponseValidationError: If validation fails
        
    Returns:
        bool: True if valid
    """
    # Check required fields
    if not isinstance(envelope.response_type, ResponseType):
        raise ResponseValidationError(f"Invalid response_type: {envelope.response_type}")
    
    if not envelope.summary or not envelope.summary.strip():
        raise ResponseValidationError("Summary cannot be empty")
    
    # Validate artifacts
    for i, artifact in enumerate(envelope.artifacts):
        if not isinstance(artifact, Artifact):
            raise ResponseValidationError(f"Artifact {i} is not an Artifact instance")
        if not isinstance(artifact.artifact_type, ArtifactType):
            raise ResponseValidationError(f"Artifact {i} has invalid artifact_type")
    
    # Validate missions
    for i, mission in enumerate(envelope.missions_spawned):
        if not isinstance(mission, MissionReference):
            raise ResponseValidationError(f"Mission {i} is not a MissionReference instance")
        if not mission.mission_id:
            raise ResponseValidationError(f"Mission {i} missing mission_id")
    
    # Validate signals
    for i, signal in enumerate(envelope.signals_emitted):
        if not isinstance(signal, SignalReference):
            raise ResponseValidationError(f"Signal {i} is not a SignalReference instance")
        if not signal.signal_type:
            raise ResponseValidationError(f"Signal {i} missing signal_type")
    
    return True


def minimal_response(summary: str, response_type: ResponseType = ResponseType.TEXT) -> ResponseEnvelope:
    """
    Create a minimal valid response envelope.
    
    Args:
        summary: Human-readable response text
        response_type: Type of response (defaults to TEXT)
        
    Returns:
        ResponseEnvelope: Minimal valid envelope
    """
    return ResponseEnvelope(
        response_type=response_type,
        summary=summary,
        artifacts=[],
        missions_spawned=[],
        signals_emitted=[],
        ui_hints=None,
        metadata={}
    )


def text_response(text: str, ui_hints: Optional[UIHints] = None) -> ResponseEnvelope:
    """
    Create a simple text response.
    
    Args:
        text: Response text
        ui_hints: Optional UI display hints
        
    Returns:
        ResponseEnvelope: Text response envelope
    """
    envelope = minimal_response(text, ResponseType.TEXT)
    if ui_hints:
        envelope.set_ui_hints(ui_hints)
    return envelope


def clarification_response(
    question: str,
    options: Optional[List[str]] = None,
    context: Optional[Dict[str, Any]] = None
) -> ResponseEnvelope:
    """
    Create a clarification request response.
    
    Args:
        question: Clarifying question to ask user
        options: Optional list of suggested responses
        context: Optional context for the clarification
        
    Returns:
        ResponseEnvelope: Clarification request envelope
    """
    envelope = ResponseEnvelope(
        response_type=ResponseType.CLARIFICATION_REQUEST,
        summary=question,
        metadata={
            'clarification': {
                'question': question,
                'options': options or [],
                'context': context or {}
            }
        }
    )
    
    envelope.set_ui_hints(UIHints(
        priority='urgent',
        color_scheme='info',
        icon='question',
        suggested_actions=['Respond', 'Cancel']
    ))
    
    return envelope


def mission_proposal_response(
    mission: MissionReference,
    summary: str,
    signal: Optional[SignalReference] = None
) -> ResponseEnvelope:
    """
    Create a mission proposal response.
    
    Args:
        mission: Mission reference
        summary: Human-readable summary
        signal: Optional signal reference
        
    Returns:
        ResponseEnvelope: Mission proposal envelope
    """
    envelope = ResponseEnvelope(
        response_type=ResponseType.ARTIFACT_BUNDLE,
        summary=summary,
        missions_spawned=[mission],
        signals_emitted=[signal] if signal else []
    )
    
    # Add mission details as artifact
    mission_artifact = Artifact(
        artifact_type=ArtifactType.MISSION_DRAFT,
        title="Mission Proposal",
        content={
            'mission_id': mission.mission_id,
            'status': mission.status,
            'objective_type': mission.objective_type,
            'objective_description': mission.objective_description
        },
        metadata={'awaiting_approval': True}
    )
    envelope.add_artifact(mission_artifact)
    
    envelope.set_ui_hints(UIHints(
        priority='normal',
        color_scheme='info',
        icon='clipboard',
        suggested_actions=['Review', 'Approve', 'Modify', 'Reject']
    ))
    
    return envelope


def unified_proposal_response(unified_proposal_dict: Dict[str, Any]) -> ResponseEnvelope:
    """
    Create a unified mission proposal response.
    
    This is the NEW cohesive proposal format (replaces fragmented proposal).
    
    Args:
        unified_proposal_dict: UnifiedProposal.to_dict() output
        
    Returns:
        ResponseEnvelope: Unified proposal envelope
    """
    # Extract key info for summary
    mission_title = unified_proposal_dict.get('mission_title', 'Mission')
    total_cost = unified_proposal_dict.get('costs', {}).get('total_usd', 0)
    total_time = unified_proposal_dict.get('time', {}).get('total_minutes', 0)
    
    summary = (
        f"Mission proposal: {mission_title}. "
        f"Estimated cost: ${total_cost:.2f}, time: ~{total_time}min. "
        f"Review details below."
    )
    
    envelope = ResponseEnvelope(
        response_type=ResponseType.ARTIFACT_BUNDLE,
        summary=summary
    )
    
    # Add unified proposal as artifact
    proposal_artifact = Artifact(
        artifact_type=ArtifactType.UNIFIED_PROPOSAL,
        title="Mission Proposal",
        content=unified_proposal_dict,
        metadata={
            'awaiting_approval': True,
            'mission_id': unified_proposal_dict.get('mission_id'),
            'requires_approval': unified_proposal_dict.get('human_involvement', {}).get('requires_approval', True)
        }
    )
    envelope.add_artifact(proposal_artifact)
    
    # Set UI hints
    approval_options = unified_proposal_dict.get('next_steps', {}).get('approval_options', ['Approve', 'Reject'])
    
    envelope.set_ui_hints(UIHints(
        priority='normal',
        color_scheme='info',
        icon='clipboard-list',
        suggested_actions=approval_options,
        layout='modal'  # Suggest modal for proposals
    ))
    
    return envelope


def error_response(error_message: str, error_details: Optional[Dict[str, Any]] = None) -> ResponseEnvelope:
    """
    Create an error response.
    
    Args:
        error_message: Error description
        error_details: Optional error details
        
    Returns:
        ResponseEnvelope: Error response envelope
    """
    envelope = ResponseEnvelope(
        response_type=ResponseType.TEXT,
        summary=f"❌ Error: {error_message}",
        metadata={
            'error': True,
            'error_message': error_message,
            'error_details': error_details or {}
        }
    )
    
    envelope.set_ui_hints(UIHints(
        priority='urgent',
        color_scheme='error',
        icon='alert',
        suggested_actions=['Retry', 'Cancel']
    ))
    
    return envelope


# ============================================================================
# CONVENIENCE BUILDERS
# ============================================================================

class ResponseBuilder:
    """
    Fluent builder for response envelopes.
    
    Example:
        response = (ResponseBuilder()
            .type(ResponseType.REPORT)
            .summary("Mission completed successfully")
            .add_table("Results", columns=['A', 'B'], rows=[[1, 2]])
            .add_mission(mission_ref)
            .hints(priority='normal', color_scheme='success')
            .build())
    """
    
    def __init__(self):
        self._response_type = ResponseType.TEXT
        self._summary = ""
        self._artifacts = []
        self._missions = []
        self._signals = []
        self._live_stream_id = None
        self._ui_hints = None
        self._metadata = {}
    
    def type(self, response_type: ResponseType) -> 'ResponseBuilder':
        """Set response type."""
        self._response_type = response_type
        return self
    
    def summary(self, text: str) -> 'ResponseBuilder':
        """Set summary text."""
        self._summary = text
        return self
    
    def add_artifact(self, artifact: Artifact) -> 'ResponseBuilder':
        """Add an artifact."""
        self._artifacts.append(artifact)
        return self
    
    def add_table(
        self,
        title: str,
        columns: List[str],
        rows: List[List[Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'ResponseBuilder':
        """Add a table artifact."""
        self._artifacts.append(TableArtifact(title, columns, rows, metadata))
        return self
    
    def add_chart(
        self,
        title: str,
        chart_type: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'ResponseBuilder':
        """Add a chart artifact."""
        self._artifacts.append(ChartArtifact(title, chart_type, data, metadata))
        return self
    
    def add_document(
        self,
        title: str,
        sections: List[Dict[str, str]],
        format: str = 'markdown',
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'ResponseBuilder':
        """Add a document artifact."""
        self._artifacts.append(DocumentArtifact(title, sections, format, metadata))
        return self
    
    def add_code(
        self,
        title: str,
        code: str,
        language: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'ResponseBuilder':
        """Add a code block artifact."""
        self._artifacts.append(CodeBlockArtifact(title, code, language, metadata))
        return self
    
    def add_timeline(
        self,
        title: str,
        events: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'ResponseBuilder':
        """Add a timeline artifact."""
        self._artifacts.append(TimelineArtifact(title, events, metadata))
        return self
    
    def add_file(
        self,
        title: str,
        file_path: str,
        file_type: str,
        size_bytes: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'ResponseBuilder':
        """Add a file reference artifact."""
        self._artifacts.append(FileReferenceArtifact(title, file_path, file_type, size_bytes, metadata))
        return self
    
    def add_mission(self, mission: MissionReference) -> 'ResponseBuilder':
        """Add a mission reference."""
        self._missions.append(mission)
        return self
    
    def add_signal(self, signal: SignalReference) -> 'ResponseBuilder':
        """Add a signal reference."""
        self._signals.append(signal)
        return self

    def live_stream(self, live_stream_id: str) -> 'ResponseBuilder':
        """Attach a live execution stream ID."""
        self._live_stream_id = live_stream_id
        return self
    
    def hints(
        self,
        layout: Optional[str] = None,
        priority: Optional[str] = None,
        suggested_actions: Optional[List[str]] = None,
        color_scheme: Optional[str] = None,
        icon: Optional[str] = None,
        expandable: bool = True
    ) -> 'ResponseBuilder':
        """Set UI hints."""
        self._ui_hints = UIHints(
            layout=layout,
            priority=priority,
            suggested_actions=suggested_actions or [],
            color_scheme=color_scheme,
            icon=icon,
            expandable=expandable
        )
        return self
    
    def metadata(self, key: str, value: Any) -> 'ResponseBuilder':
        """Add metadata entry."""
        self._metadata[key] = value
        return self
    
    def build(self) -> ResponseEnvelope:
        """Build the response envelope."""
        envelope = ResponseEnvelope(
            response_type=self._response_type,
            summary=self._summary,
            artifacts=self._artifacts,
            missions_spawned=self._missions,
            signals_emitted=self._signals,
            live_stream_id=self._live_stream_id,
            ui_hints=self._ui_hints,
            metadata=self._metadata
        )
        validate_response_envelope(envelope)
        return envelope
