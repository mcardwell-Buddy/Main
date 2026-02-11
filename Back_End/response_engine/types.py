"""
Response Engine Types - Enums, data classes, and core types.

Defines ResponseType (text, code, document, analysis, etc.) and ContentMetadata
for tracking content throughout its lifecycle.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime


class ResponseType(Enum):
    """Enumeration of supported response content types."""
    
    TEXT = "text"                    # Plain text responses
    CODE = "code"                    # Code snippets or full programs
    MARKDOWN = "markdown"            # Markdown formatted content
    JSON = "json"                    # JSON data structures
    HTML = "html"                    # HTML formatted content
    DOCUMENT = "document"            # Full documents (reports, plans)
    ANALYSIS = "analysis"            # Data analysis and insights
    SEARCH_RESULTS = "search_results"  # Web search aggregation
    BUSINESS_PLAN = "business_plan"  # Business planning documents
    TERMINAL_OUTPUT = "terminal"     # Terminal/console output
    ERROR = "error"                  # Error messages and diagnostics


@dataclass
class ContentMetadata:
    """
    Tracks content lifecycle, dependencies, formats, and audit trail.
    
    This metadata enables:
    - Lifecycle tracking (created, modified, cached, executed)
    - Dependency management (what content depends on this)
    - Multi-format export (code as Markdown, JSON, HTML)
    - Audit trail (who generated, when, from what)
    - Error recovery (rollback, regeneration)
    """
    
    content_id: str                          # Unique identifier for this content
    response_type: ResponseType              # Type of content
    mission_id: str                          # Parent mission
    created_at: datetime = field(default_factory=datetime.utcnow)
    cached_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    cached_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    cached_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    cached_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    cached_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    cached_at: Optional[datetime] = None
    last_accessed_at: Optional[datetime] = None
    content_status: str = "draft"           # draft, ready, executed, archived
    
    # Content properties
    title: Optional[str] = None              # Human-readable title
    description: Optional[str] = None        # What this content is for
    version: int = 1                         # Version number for updates
    language: Optional[str] = None           # Programming or natural language
    mime_type: Optional[str] = None          # Content mime type (text/markdown, application/json)
    content_size_bytes: Optional[int] = None # Size of content
    content_hash: Optional[str] = None       # Hash for deduplication/integrity
    tags: List[str] = field(default_factory=list)
    audience: Optional[str] = None           # internal, external, user, system
    sensitivity: Optional[str] = None        # public, internal, confidential
    
    # Format tracking - which formats have been generated
    available_formats: List[str] = field(default_factory=lambda: ["markdown"])
    preferred_format: str = "markdown"       # Default display format
    
    # Dependency tracking
    depends_on: List[str] = field(default_factory=list)  # Other content IDs this needs
    generated_by: Optional[str] = None       # Tool/agent that created this
    lineage: Dict[str, Any] = field(default_factory=dict)  # Derivation info
    source_refs: List[Dict[str, Any]] = field(default_factory=list)  # URLs, files, citations
    
    # Execution tracking
    executed: bool = False                   # Has this content been executed?
    execution_result: Optional[Any] = None   # Result of execution
    execution_error: Optional[str] = None    # Error if execution failed
    execution_time_ms: Optional[float] = None  # How long execution took
    
    # Approval tracking
    requires_approval: bool = False          # Does user need to approve?
    approved: bool = False                   # Has user approved?
    approved_at: Optional[datetime] = None
    approval_notes: Optional[str] = None
    approval_status: str = "pending"         # pending, approved, denied, not_required
    approval_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # Caching & retention
    cache_ttl_seconds: Optional[int] = 3600  # How long to cache (1h default)
    regenerate_if_older_than: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    retention_policy: Optional[str] = None
    
    # Audit trail
    audit_trail: List[Dict[str, Any]] = field(default_factory=list)
    quality_checks: Dict[str, Any] = field(default_factory=dict)
    validation_errors: List[str] = field(default_factory=list)
    
    # Custom metadata
    custom_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'content_id': self.content_id,
            'response_type': self.response_type.value,
            'mission_id': self.mission_id,
            'created_at': self.created_at.isoformat(),
            'modified_at': self.modified_at.isoformat() if self.modified_at else None,
            'cached_at': self.cached_at.isoformat() if self.cached_at else None,
            'last_accessed_at': self.last_accessed_at.isoformat() if self.last_accessed_at else None,
            'content_status': self.content_status,
            'title': self.title,
            'description': self.description,
            'version': self.version,
            'language': self.language,
            'mime_type': self.mime_type,
            'content_size_bytes': self.content_size_bytes,
            'content_hash': self.content_hash,
            'tags': self.tags,
            'audience': self.audience,
            'sensitivity': self.sensitivity,
            'available_formats': self.available_formats,
            'preferred_format': self.preferred_format,
            'depends_on': self.depends_on,
            'generated_by': self.generated_by,
            'lineage': self.lineage,
            'source_refs': self.source_refs,
            'executed': self.executed,
            'execution_result': self.execution_result,
            'execution_error': self.execution_error,
            'execution_time_ms': self.execution_time_ms,
            'requires_approval': self.requires_approval,
            'approved': self.approved,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'approval_notes': self.approval_notes,
            'approval_status': self.approval_status,
            'approval_history': self.approval_history,
            'cache_ttl_seconds': self.cache_ttl_seconds,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'retention_policy': self.retention_policy,
            'audit_trail': self.audit_trail,
            'quality_checks': self.quality_checks,
            'validation_errors': self.validation_errors,
            'custom_metadata': self.custom_metadata,
        }


@dataclass
class Response:
    """
    Complete response with content and metadata.
    
    A response contains one or more pieces of content, each with their own
    metadata and formatting options.
    """
    
    response_id: str                         # Unique identifier
    mission_id: str                          # Parent mission
    status: str = "pending"                  # pending, ready, approved, executed, completed
    created_at: datetime = field(default_factory=datetime.utcnow)
    cached_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    # Content
    primary_content: Optional[str] = None    # Main response text
    content_items: List[ContentMetadata] = field(default_factory=list)  # Rich content pieces
    
    # Formatting
    output_channels: List[str] = field(default_factory=lambda: ["text"])  # text, api, web, email
    target_format: str = "markdown"          # Preferred output format
    interactive_elements: List[Dict[str, Any]] = field(default_factory=list)
    
    # Approval
    requires_approval: bool = True
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    approval_reason: Optional[str] = None
    approval_status: str = "pending"         # pending, approved, denied, not_required
    approval_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # Quality metrics
    confidence_score: Optional[float] = None  # 0-1 confidence in response quality
    completeness_score: Optional[float] = None  # 0-1 how complete is the response
    
    # Error handling
    error_recovery_attempts: int = 0
    last_error: Optional[str] = None
    last_error_at: Optional[datetime] = None
    error_history: List[str] = field(default_factory=list)
    recovery_actions: List[Dict[str, Any]] = field(default_factory=list)
    
    def add_content(self, content: ContentMetadata) -> None:
        """Add a content item to this response."""
        self.content_items.append(content)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'response_id': self.response_id,
            'mission_id': self.mission_id,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'cached_at': self.cached_at.isoformat() if self.cached_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'primary_content': self.primary_content,
            'content_items': [item.to_dict() for item in self.content_items],
            'output_channels': self.output_channels,
            'target_format': self.target_format,
            'interactive_elements': self.interactive_elements,
            'requires_approval': self.requires_approval,
            'approved_by': self.approved_by,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'approval_reason': self.approval_reason,
            'approval_status': self.approval_status,
            'approval_history': self.approval_history,
            'confidence_score': self.confidence_score,
            'completeness_score': self.completeness_score,
            'error_recovery_attempts': self.error_recovery_attempts,
            'last_error': self.last_error,
            'last_error_at': self.last_error_at.isoformat() if self.last_error_at else None,
            'error_history': self.error_history,
            'recovery_actions': self.recovery_actions,
        }

