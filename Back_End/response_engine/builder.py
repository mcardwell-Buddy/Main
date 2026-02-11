"""
Response Builder - Main class for constructing and managing responses.

The ResponseBuilder orchestrates the creation of responses, managing content items,
metadata, formatting, and output delivery.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

from Back_End.response_engine.types import Response, ContentMetadata, ResponseType
from Back_End.response_engine.formatters import (
    BaseFormatter,
    JSONFormatter,
    MarkdownFormatter,
    HTMLFormatter,
    CodeFormatter,
    PlainTextFormatter,
    DocumentFormatter,
    AnalysisFormatter,
    SearchResultsFormatter,
    BusinessPlanFormatter,
)


logger = logging.getLogger(__name__)


class ResponseBuilder:
    """
    Builds comprehensive responses with rich content and metadata.
    
    Features:
    - Create responses with multiple content types
    - Track content metadata and lifecycle
    - Support multiple output formats (JSON, Markdown, HTML, etc.)
    - Manage approval workflows
    - Handle error recovery
    
    Usage:
        builder = ResponseBuilder(mission_id="mission_123")
        builder.add_content("response", ResponseType.TEXT)
        builder.add_content("calculated value", ResponseType.CODE, language="python")
        response = builder.build()
    """
    
    # Available formatters
    FORMATTERS = {
        'json': JSONFormatter(),
        'markdown': MarkdownFormatter(),
        'html': HTMLFormatter(),
        'code': CodeFormatter(),
        'text': PlainTextFormatter(),
        'document': DocumentFormatter(),
        'analysis': AnalysisFormatter(),
        'search_results': SearchResultsFormatter(),
        'business_plan': BusinessPlanFormatter(),
    }
    
    def __init__(
        self,
        mission_id: str,
        response_id: Optional[str] = None,
        requires_approval: bool = True,
        output_channels: Optional[List[str]] = None,
        target_format: str = "markdown",
    ):
        """
        Initialize response builder.
        
        Args:
            mission_id: Parent mission identifier
            response_id: Custom response ID (auto-generated if not provided)
            requires_approval: Whether response needs user approval
            output_channels: Where to send response (text, api, web, email)
            target_format: Preferred output format (markdown, json, html, etc.)
        """
        self.mission_id = mission_id
        self.response_id = response_id or f"resp_{uuid.uuid4().hex[:12]}"
        self.requires_approval = requires_approval
        self._approval_reason: Optional[str] = None
        self._approval_notes: Optional[str] = None
        self.output_channels = output_channels or ["text"]
        self.target_format = target_format
        
        # Response components
        self._primary_content: Optional[str] = None
        self._content_items: List[ContentMetadata] = []
        self._interactive_elements: List[Dict[str, Any]] = []
        self._error_messages: List[str] = []
        self._confidence_score: Optional[float] = None
        self._completeness_score: Optional[float] = None
        
        # Metadata
        self._created_at = datetime.utcnow()
        self._custom_metadata: Dict[str, Any] = {}
    
    def set_primary_content(self, content: str) -> "ResponseBuilder":
        """
        Set the primary response content.
        
        Args:
            content: Main response text
            
        Returns:
            Self for method chaining
        """
        self._primary_content = content
        return self

    def set_requires_approval(self, required: bool, reason: Optional[str] = None) -> "ResponseBuilder":
        """
        Set whether approval is required and optionally set a reason.

        Args:
            required: Whether approval is required
            reason: Optional reason for approval

        Returns:
            Self for method chaining
        """
        self.requires_approval = required
        if reason:
            self._approval_reason = reason
        return self

    def set_approval_notes(self, notes: str) -> "ResponseBuilder":
        """
        Set approval notes.

        Args:
            notes: Notes to attach to approval request

        Returns:
            Self for method chaining
        """
        self._approval_notes = notes
        return self
    
    def add_content(
        self,
        content: str,
        response_type: ResponseType,
        title: Optional[str] = None,
        description: Optional[str] = None,
        generated_by: Optional[str] = None,
        language: Optional[str] = None,
        requires_approval: bool = False,
        cache_ttl_seconds: Optional[int] = None,
    ) -> "ResponseBuilder":
        """
        Add a content item to the response.
        
        Args:
            content: The actual content
            response_type: Type of content (TEXT, CODE, MARKDOWN, etc.)
            title: Human-readable title
            description: What this content is for
            generated_by: Tool or agent that generated this
            language: For code content, the programming language
            requires_approval: Whether this item needs approval
            cache_ttl_seconds: How long to cache this content
            
        Returns:
            Self for method chaining
        """
        content_id = f"content_{uuid.uuid4().hex[:12]}"
        
        metadata = ContentMetadata(
            content_id=content_id,
            response_type=response_type,
            mission_id=self.mission_id,
            title=title or response_type.value,
            description=description,
            generated_by=generated_by,
            requires_approval=requires_approval,
            cache_ttl_seconds=cache_ttl_seconds,
        )
        
        # Add custom language metadata for code
        if language:
            metadata.language = language
            metadata.custom_metadata['language'] = language
        
        # Store actual content in custom metadata (will be refactored in Phase 5)
        metadata.custom_metadata['content'] = content
        
        self._content_items.append(metadata)
        return self
    
    def add_code_content(
        self,
        code: str,
        language: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        generated_by: Optional[str] = None,
    ) -> "ResponseBuilder":
        """
        Convenience method to add code content.
        
        Args:
            code: Code to include
            language: Programming language
            title: Code title
            description: What the code does
            generated_by: Tool that generated it
            
        Returns:
            Self for method chaining
        """
        return self.add_content(
            content=code,
            response_type=ResponseType.CODE,
            title=title,
            description=description,
            generated_by=generated_by,
            language=language,
        )
    
    def add_analysis_content(
        self,
        analysis: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        generated_by: Optional[str] = None,
    ) -> "ResponseBuilder":
        """
        Convenience method to add analysis content.
        
        Args:
            analysis: Analysis text
            title: Analysis title
            description: What the analysis covers
            generated_by: Tool that generated it
            
        Returns:
            Self for method chaining
        """
        return self.add_content(
            content=analysis,
            response_type=ResponseType.ANALYSIS,
            title=title,
            description=description,
            generated_by=generated_by,
        )
    
    def set_confidence(self, score: float) -> "ResponseBuilder":
        """
        Set confidence score (0-1).
        
        Args:
            score: Confidence score
            
        Returns:
            Self for method chaining
        """
        if not 0 <= score <= 1:
            raise ValueError("Confidence score must be between 0 and 1")
        self._confidence_score = score
        return self
    
    def set_completeness(self, score: float) -> "ResponseBuilder":
        """
        Set completeness score (0-1).
        
        Args:
            score: Completeness score
            
        Returns:
            Self for method chaining
        """
        if not 0 <= score <= 1:
            raise ValueError("Completeness score must be between 0 and 1")
        self._completeness_score = score
        return self
    
    def add_error(self, error_message: str) -> "ResponseBuilder":
        """
        Add an error message to the response.
        
        Args:
            error_message: Error to include
            
        Returns:
            Self for method chaining
        """
        self._error_messages.append(error_message)
        return self
    
    def set_custom_metadata(self, key: str, value: Any) -> "ResponseBuilder":
        """
        Set custom metadata key-value pair.
        
        Args:
            key: Metadata key
            value: Metadata value
            
        Returns:
            Self for method chaining
        """
        self._custom_metadata[key] = value
        return self

    def add_interactive_element(self, element: Dict[str, Any]) -> "ResponseBuilder":
        """
        Add an interactive element (button, link, expandable section, progress, etc.).

        Args:
            element: Interactive element dictionary

        Returns:
            Self for method chaining
        """
        if not isinstance(element, dict):
            raise ValueError("Interactive element must be a dictionary")
        self._interactive_elements.append(element)
        return self
    
    def build(self) -> Response:
        """
        Build and return the complete response.
        
        Returns:
            Response object ready for formatting/delivery
        """
        last_error = self._error_messages[-1] if self._error_messages else None
        last_error_at = datetime.utcnow() if self._error_messages else None

        approval_status = "pending" if self.requires_approval else "not_required"

        response = Response(
            response_id=self.response_id,
            mission_id=self.mission_id,
            status="pending" if self.requires_approval else "ready",
            created_at=self._created_at,
            primary_content=self._primary_content,
            content_items=self._content_items,
            output_channels=self.output_channels,
            target_format=self.target_format,
            interactive_elements=list(self._interactive_elements),
            requires_approval=self.requires_approval,
            approval_reason=self._approval_reason,
            approval_status=approval_status,
            confidence_score=self._confidence_score,
            completeness_score=self._completeness_score,
            last_error=last_error,
            last_error_at=last_error_at,
            error_history=list(self._error_messages),
        )

        if self._approval_notes:
            response.approval_history.append({
                "action": "notes",
                "notes": self._approval_notes,
                "timestamp": datetime.utcnow().isoformat(),
            })
        
        logger.info(
            f"Built response {response.response_id} for mission {self.mission_id} "
            f"with {len(self._content_items)} content items"
        )
        
        return response
    
    def format(self, format_type: str = "markdown") -> str:
        """
        Format the built response.
        
        Args:
            format_type: Output format (markdown, json, html, code, text)
            
        Returns:
            Formatted response string
        """
        response = self.build()
        formatter = self.FORMATTERS.get(format_type)
        
        if not formatter:
            raise ValueError(
                f"Unknown format: {format_type}. "
                f"Available: {', '.join(self.FORMATTERS.keys())}"
            )
        
        return formatter.format(response)
    
    @classmethod
    def register_formatter(cls, name: str, formatter: BaseFormatter) -> None:
        """
        Register a custom formatter.
        
        Args:
            name: Formatter name
            formatter: BaseFormatter instance
        """
        cls.FORMATTERS[name] = formatter
    
    @classmethod
    def get_available_formats(cls) -> List[str]:
        """
        Get list of available format types.
        
        Returns:
            List of format names
        """
        return list(cls.FORMATTERS.keys())

