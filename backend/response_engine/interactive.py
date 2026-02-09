"""
Interactive Components - Structured elements for rich responses.

Phase 6: Buttons, links, expandable sections, and progress indicators.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime


@dataclass
class InteractiveElement:
    """Base class for interactive elements."""
    element_type: str
    element_id: str
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "element_type": self.element_type,
            "element_id": self.element_id,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class Button(InteractiveElement):
    label: str = "Button"
    action: str = ""  # e.g., approve, deny, open_url, run
    payload: Dict[str, Any] = field(default_factory=dict)
    style: str = "primary"  # primary, secondary, danger

    def __init__(self, element_id: str, label: str, action: str, payload: Optional[Dict[str, Any]] = None, style: str = "primary"):
        super().__init__(element_type="button", element_id=element_id)
        self.label = label
        self.action = action
        self.payload = payload or {}
        self.style = style

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "label": self.label,
            "action": self.action,
            "payload": self.payload,
            "style": self.style,
        })
        return data


@dataclass
class Link(InteractiveElement):
    label: str = "Link"
    url: str = ""

    def __init__(self, element_id: str, label: str, url: str):
        super().__init__(element_type="link", element_id=element_id)
        self.label = label
        self.url = url

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "label": self.label,
            "url": self.url,
        })
        return data


@dataclass
class ExpandableSection(InteractiveElement):
    title: str = "Details"
    content: str = ""
    expanded: bool = False

    def __init__(self, element_id: str, title: str, content: str, expanded: bool = False):
        super().__init__(element_type="expandable", element_id=element_id)
        self.title = title
        self.content = content
        self.expanded = expanded

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "title": self.title,
            "content": self.content,
            "expanded": self.expanded,
        })
        return data


@dataclass
class ProgressIndicator(InteractiveElement):
    label: str = "Progress"
    value: float = 0.0  # 0-1
    status: str = "in_progress"  # in_progress, complete, error

    def __init__(self, element_id: str, label: str, value: float, status: str = "in_progress"):
        super().__init__(element_type="progress", element_id=element_id)
        self.label = label
        self.value = value
        self.status = status

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "label": self.label,
            "value": self.value,
            "status": self.status,
        })
        return data


def interactive_to_dict(element: Any) -> Dict[str, Any]:
    """Convert interactive element to dict regardless of type."""
    if hasattr(element, "to_dict"):
        return element.to_dict()
    if isinstance(element, dict):
        return element
    return {
        "element_type": "unknown",
        "element_id": "unknown",
        "value": str(element),
    }
