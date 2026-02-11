"""
Response Formatters - Convert content to different output formats.

Base formatter provides interface; specific formatters handle JSON, Markdown, HTML, etc.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
import json


class BaseFormatter(ABC):
    """
    Abstract base class for all content formatters.
    
    Each formatter is responsible for converting Response objects into
    a specific output format (JSON, Markdown, HTML, etc.).
    """
    
    def __init__(self, include_metadata: bool = True):
        """
        Initialize formatter.
        
        Args:
            include_metadata: Whether to include ContentMetadata in output
        """
        self.include_metadata = include_metadata
    
    @abstractmethod
    def format(self, response: Any) -> str:
        """
        Format a response object.
        
        Args:
            response: Response object to format
            
        Returns:
            Formatted string representation
        """
        pass
    
    @abstractmethod
    def can_format(self, response_type: str) -> bool:
        """
        Check if this formatter can handle a given response type.
        
        Args:
            response_type: ResponseType value to check
            
        Returns:
            True if formatter can handle this type
        """
        pass


class JSONFormatter(BaseFormatter):
    """Format responses as JSON."""
    
    def __init__(self, include_metadata: bool = True, pretty: bool = True):
        super().__init__(include_metadata)
        self.pretty = pretty
    
    def format(self, response: Any) -> str:
        """
        Format response as JSON.
        
        Args:
            response: Response or dict-like object
            
        Returns:
            JSON string
        """
        if hasattr(response, 'to_dict'):
            data = response.to_dict()
        else:
            data = response if isinstance(response, dict) else {'data': response}
        
        if self.pretty:
            return json.dumps(data, indent=2, default=str)
        else:
            return json.dumps(data, default=str)
    
    def can_format(self, response_type: str) -> bool:
        """JSON can format any response type."""
        return True


class MarkdownFormatter(BaseFormatter):
    """Format responses as Markdown."""
    
    def format(self, response: Any) -> str:
        """
        Format response as Markdown.
        
        Args:
            response: Response object
            
        Returns:
            Markdown string
        """
        if not hasattr(response, 'to_dict'):
            return self._format_simple(response)
        
        response_dict = response.to_dict()
        lines = []
        
        # Header
        if 'response_id' in response_dict:
            lines.append(f"# Response: {response_dict.get('response_id', 'Unknown')}")
            lines.append("")
        
        # Status and metadata
        if self.include_metadata:
            lines.append("## Metadata")
            lines.append(f"- **Status**: {response_dict.get('status', 'unknown')}")
            lines.append(f"- **Mission**: {response_dict.get('mission_id', 'unknown')}")
            lines.append(f"- **Created**: {response_dict.get('created_at', 'unknown')}")
            if response_dict.get('confidence_score') is not None:
                lines.append(f"- **Confidence**: {response_dict.get('confidence_score'):.1%}")
            lines.append("")
        
        # Primary content
        if response_dict.get('primary_content'):
            lines.append("## Content")
            lines.append(response_dict['primary_content'])
            lines.append("")
        
        # Content items
        if response_dict.get('content_items'):
            lines.append("## Detailed Content")
            for item in response_dict['content_items']:
                if isinstance(item, dict):
                    title = item.get('title', item.get('response_type', 'Content'))
                    lines.append(f"### {title}")
                    if item.get('description'):
                        lines.append(f"{item['description']}")
                    lines.append("")
        
        # Approval info
        if response_dict.get('requires_approval'):
            lines.append("## Approval Required")
            lines.append(f"- **Status**: {'Approved' if response_dict.get('approved') else 'Pending'}")
            if response_dict.get('approved_at'):
                lines.append(f"- **Approved At**: {response_dict['approved_at']}")
            lines.append("")

        # Interactive elements
        if response_dict.get('interactive_elements'):
            lines.append("## Actions")
            for element in response_dict.get('interactive_elements', []):
                if not isinstance(element, dict):
                    continue
                element_type = element.get('element_type', 'action')
                label = element.get('label', element.get('title', element_type))
                if element_type == 'link' and element.get('url'):
                    lines.append(f"- [{label}]({element['url']})")
                elif element_type == 'button':
                    lines.append(f"- **{label}** (action: {element.get('action')})")
                elif element_type == 'expandable':
                    lines.append(f"- **{label}** (expandable)")
                elif element_type == 'progress':
                    value = element.get('value')
                    if value is not None:
                        lines.append(f"- **{label}**: {float(value) * 100:.0f}%")
                    else:
                        lines.append(f"- **{label}**")
                else:
                    lines.append(f"- **{label}**")
            lines.append("")
        
        return "\n".join(lines)
    
    def _format_simple(self, response: Any) -> str:
        """Format simple response as markdown."""
        return f"```\n{str(response)}\n```"
    
    def can_format(self, response_type: str) -> bool:
        """Markdown can format any response type."""
        return True


class HTMLFormatter(BaseFormatter):
    """Format responses as HTML."""
    
    def __init__(self, include_metadata: bool = True, include_styles: bool = True):
        super().__init__(include_metadata)
        self.include_styles = include_styles
    
    def format(self, response: Any) -> str:
        """
        Format response as HTML.
        
        Args:
            response: Response object
            
        Returns:
            HTML string
        """
        if not hasattr(response, 'to_dict'):
            return self._format_simple(response)
        
        response_dict = response.to_dict()
        html_parts = []
        
        if self.include_styles:
            html_parts.append(self._get_styles())
        
        html_parts.append("<div class='buddy-response'>")
        
        # Header
        if 'response_id' in response_dict:
            html_parts.append(f"<h1>Response: {response_dict.get('response_id', 'Unknown')}</h1>")
        
        # Status and metadata
        if self.include_metadata:
            html_parts.append("<section class='metadata'>")
            html_parts.append("<h2>Metadata</h2>")
            html_parts.append("<dl>")
            html_parts.append(f"<dt>Status</dt><dd>{response_dict.get('status', 'unknown')}</dd>")
            html_parts.append(f"<dt>Mission</dt><dd>{response_dict.get('mission_id', 'unknown')}</dd>")
            html_parts.append(f"<dt>Created</dt><dd>{response_dict.get('created_at', 'unknown')}</dd>")
            if response_dict.get('confidence_score') is not None:
                confidence = f"{response_dict.get('confidence_score'):.1%}"
                html_parts.append(f"<dt>Confidence</dt><dd>{confidence}</dd>")
            html_parts.append("</dl>")
            html_parts.append("</section>")
        
        # Primary content
        if response_dict.get('primary_content'):
            html_parts.append("<section class='content'>")
            html_parts.append("<h2>Content</h2>")
            # Escape HTML
            content = response_dict['primary_content'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            html_parts.append(f"<p>{content}</p>")
            html_parts.append("</section>")
        
        # Content items
        if response_dict.get('content_items'):
            html_parts.append("<section class='content-items'>")
            html_parts.append("<h2>Detailed Content</h2>")
            for item in response_dict['content_items']:
                if isinstance(item, dict):
                    title = item.get('title', item.get('response_type', 'Content'))
                    html_parts.append(f"<article class='content-item'>")
                    html_parts.append(f"<h3>{title}</h3>")
                    if item.get('description'):
                        html_parts.append(f"<p>{item['description']}</p>")
                    html_parts.append("</article>")
            html_parts.append("</section>")
        
        # Approval info
        if response_dict.get('requires_approval'):
            status = 'approved' if response_dict.get('approved') else 'pending'
            html_parts.append(f"<section class='approval approval-{status}'>")
            html_parts.append("<h2>Approval Required</h2>")
            html_parts.append(f"<p><strong>Status</strong>: {status.capitalize()}</p>")
            if response_dict.get('approved_at'):
                html_parts.append(f"<p><strong>Approved At</strong>: {response_dict['approved_at']}</p>")
            html_parts.append("</section>")

        # Interactive elements
        if response_dict.get('interactive_elements'):
            html_parts.append("<section class='interactive'>")
            html_parts.append("<h2>Actions</h2>")
            html_parts.append("<div class='interactive-elements'>")
            for element in response_dict.get('interactive_elements', []):
                if not isinstance(element, dict):
                    continue
                element_type = element.get('element_type', 'action')
                label = element.get('label', element.get('title', element_type))
                if element_type == 'link' and element.get('url'):
                    html_parts.append(
                        f"<a class='action-link' href='{element['url']}' target='_blank' rel='noopener noreferrer'>{label}</a>"
                    )
                elif element_type == 'button':
                    action = element.get('action', '')
                    html_parts.append(
                        f"<button class='action-button' data-action='{action}'>{label}</button>"
                    )
                elif element_type == 'expandable':
                    content = element.get('content', '')
                    html_parts.append("<details class='action-expandable'>")
                    html_parts.append(f"<summary>{label}</summary>")
                    html_parts.append(f"<div>{content}</div>")
                    html_parts.append("</details>")
                elif element_type == 'progress':
                    value = element.get('value')
                    percent = f"{float(value) * 100:.0f}%" if value is not None else "0%"
                    html_parts.append(
                        f"<div class='action-progress'><span>{label}</span><progress value='{percent.strip('%')}' max='100'></progress><span>{percent}</span></div>"
                    )
                else:
                    html_parts.append(f"<div class='action-item'>{label}</div>")
            html_parts.append("</div>")
            html_parts.append("</section>")
        
        html_parts.append("</div>")
        
        return "\n".join(html_parts)
    
    def _format_simple(self, response: Any) -> str:
        """Format simple response as HTML."""
        content = str(response).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        return f"<pre>{content}</pre>"
    
    def _get_styles(self) -> str:
        """Get embedded CSS styles."""
        return """<style>
.buddy-response {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    max-width: 900px;
    margin: 0 auto;
    padding: 20px;
    background: #f9f9f9;
}

.buddy-response h1, .buddy-response h2, .buddy-response h3 {
    color: #333;
    margin-top: 1.5em;
    margin-bottom: 0.5em;
}

.buddy-response h1 { font-size: 2em; }
.buddy-response h2 { font-size: 1.5em; }
.buddy-response h3 { font-size: 1.2em; }

.metadata {
    background: white;
    padding: 15px;
    border-radius: 4px;
    border-left: 4px solid #4CAF50;
}

.metadata dl {
    margin: 0;
}

.metadata dt {
    font-weight: bold;
    color: #666;
    margin-top: 8px;
}

.metadata dd {
    margin-left: 20px;
    color: #333;
    margin-bottom: 8px;
}

.content {
    background: white;
    padding: 15px;
    border-radius: 4px;
    margin-top: 20px;
    border-left: 4px solid #2196F3;
}

.content-items {
    margin-top: 20px;
}

.content-item {
    background: white;
    padding: 15px;
    border-radius: 4px;
    margin-bottom: 15px;
    border-left: 4px solid #FF9800;
}

.approval {
    margin-top: 20px;
    padding: 15px;
    border-radius: 4px;
    border-left: 4px solid #f44336;
}

.approval-pending {
    background: #fff3cd;
    border-left-color: #ffc107;
}

.approval-approved {
    background: #d4edda;
    border-left-color: #28a745;
}

.approval h2 {
    color: #333;
    margin-top: 0;
}

.interactive {
    margin-top: 20px;
    padding: 15px;
    border-radius: 4px;
    background: #ffffff;
    border-left: 4px solid #673ab7;
}

.interactive-elements {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
}

.action-button {
    background: #673ab7;
    color: white;
    border: none;
    padding: 8px 14px;
    border-radius: 4px;
    cursor: pointer;
}

.action-link {
    color: #2196F3;
    text-decoration: none;
}

.action-expandable {
    width: 100%;
}

.action-progress {
    display: flex;
    align-items: center;
    gap: 8px;
}
</style>"""
    
    def can_format(self, response_type: str) -> bool:
        """HTML can format any response type."""
        return True


class CodeFormatter(BaseFormatter):
    """Format responses as code blocks with syntax highlighting metadata."""
    
    def __init__(self, include_metadata: bool = True, language: str = "python"):
        super().__init__(include_metadata)
        self.language = language
    
    def format(self, response: Any) -> str:
        """
        Format response as code block.
        
        Args:
            response: Response object
            
        Returns:
            Code-formatted string
        """
        if hasattr(response, 'primary_content'):
            code = response.primary_content
        else:
            code = str(response)
        
        return f"```{self.language}\n{code}\n```"
    
    def can_format(self, response_type: str) -> bool:
        """Can format code response types."""
        return response_type in ["code", "terminal", "error"]


class PlainTextFormatter(BaseFormatter):
    """Format responses as plain text."""
    
    def format(self, response: Any) -> str:
        """
        Format response as plain text.
        
        Args:
            response: Response object
            
        Returns:
            Plain text string
        """
        if hasattr(response, 'primary_content'):
            return response.primary_content
        return str(response)
    
    def can_format(self, response_type: str) -> bool:
        """Plain text can format any response type."""
        return True


def _get_response_dict(response: Any) -> Dict[str, Any]:
    if hasattr(response, 'to_dict'):
        return response.to_dict()
    if isinstance(response, dict):
        return response
    return {'primary_content': str(response), 'content_items': []}


def _extract_content_items(response_dict: Dict[str, Any], target_types: List[str]) -> List[Dict[str, Any]]:
    items = []
    for item in response_dict.get('content_items', []):
        if not isinstance(item, dict):
            continue
        if item.get('response_type') in target_types:
            items.append(item)
    return items


def _format_markdown_block(item: Dict[str, Any]) -> List[str]:
    title = item.get('title', item.get('response_type', 'Content'))
    description = item.get('description')
    content = None
    if isinstance(item.get('custom_metadata'), dict):
        content = item.get('custom_metadata', {}).get('content')
        if content is None:
            content = item.get('custom_metadata', {}).get('results')
    if content is None:
        content = item.get('content')

    lines = [f"### {title}"]
    if description:
        lines.append(description)
        lines.append("")

    if isinstance(content, list):
        for entry in content:
            if isinstance(entry, dict):
                label = entry.get('title') or entry.get('name') or entry.get('url') or str(entry)
                url = entry.get('url')
                summary = entry.get('summary') or entry.get('snippet')
                if url:
                    lines.append(f"- [{label}]({url})")
                else:
                    lines.append(f"- {label}")
                if summary:
                    lines.append(f"  - {summary}")
            else:
                lines.append(f"- {entry}")
    elif isinstance(content, dict):
        for key, value in content.items():
            lines.append(f"- **{key}**: {value}")
    elif content is not None:
        lines.append(str(content))

    if item.get('source_refs'):
        lines.append("")
        lines.append("**Sources**")
        for source in item.get('source_refs', []):
            if isinstance(source, dict):
                label = source.get('title') or source.get('url') or 'source'
                url = source.get('url')
                if url:
                    lines.append(f"- [{label}]({url})")
                else:
                    lines.append(f"- {label}")
            else:
                lines.append(f"- {source}")

    lines.append("")
    return lines


class DocumentFormatter(BaseFormatter):
    """Format document-style responses as Markdown."""

    def format(self, response: Any) -> str:
        response_dict = _get_response_dict(response)
        items = _extract_content_items(response_dict, ["document"])
        lines = ["# Document"]
        for item in items:
            lines.extend(_format_markdown_block(item))
        if not items and response_dict.get('primary_content'):
            lines.append(response_dict.get('primary_content'))
        return "\n".join(lines)

    def can_format(self, response_type: str) -> bool:
        return response_type == "document"


class AnalysisFormatter(BaseFormatter):
    """Format analysis responses as Markdown with sections."""

    def format(self, response: Any) -> str:
        response_dict = _get_response_dict(response)
        items = _extract_content_items(response_dict, ["analysis"])
        lines = ["# Analysis"]
        for item in items:
            lines.extend(_format_markdown_block(item))
        if not items and response_dict.get('primary_content'):
            lines.append(response_dict.get('primary_content'))
        return "\n".join(lines)

    def can_format(self, response_type: str) -> bool:
        return response_type == "analysis"


class SearchResultsFormatter(BaseFormatter):
    """Format search results as Markdown list."""

    def format(self, response: Any) -> str:
        response_dict = _get_response_dict(response)
        items = _extract_content_items(response_dict, ["search_results"])
        lines = ["# Search Results"]
        for item in items:
            lines.extend(_format_markdown_block(item))
        if not items and response_dict.get('primary_content'):
            lines.append(response_dict.get('primary_content'))
        return "\n".join(lines)

    def can_format(self, response_type: str) -> bool:
        return response_type == "search_results"


class BusinessPlanFormatter(BaseFormatter):
    """Format business plan content as a structured Markdown document."""

    def format(self, response: Any) -> str:
        response_dict = _get_response_dict(response)
        items = _extract_content_items(response_dict, ["business_plan"])
        lines = ["# Business Plan"]
        for item in items:
            lines.extend(_format_markdown_block(item))
        if not items and response_dict.get('primary_content'):
            lines.append(response_dict.get('primary_content'))
        return "\n".join(lines)

    def can_format(self, response_type: str) -> bool:
        return response_type == "business_plan"

