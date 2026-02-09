"""
Execution Stream Event Schema

READ-ONLY. Append-only. JSONL-compatible.
No execution control. No retries. No pausing. No autonomy.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, Optional, Union
from datetime import datetime
import json


class ExecutionEventType(Enum):
    """Supported execution stream event types."""
    NAVIGATION = "navigation"
    EXTRACTION = "extraction"
    SIGNAL = "signal"
    STATUS = "status"


@dataclass(frozen=True)
class NavigationEventPayload:
    """Minimal navigation event payload."""
    url: str
    action: str  # e.g., "open", "click", "scroll", "paginate"
    detail: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "url": self.url,
            "action": self.action,
            "detail": self.detail
        }


@dataclass(frozen=True)
class ExtractionEventPayload:
    """Minimal extraction event payload."""
    target: str  # e.g., "listing", "profile", "table"
    items_extracted: int
    detail: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target": self.target,
            "items_extracted": self.items_extracted,
            "detail": self.detail
        }


@dataclass(frozen=True)
class SignalEventPayload:
    """Minimal signal event payload."""
    signal_type: str
    signal_layer: str
    signal_source: str
    summary: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "signal_type": self.signal_type,
            "signal_layer": self.signal_layer,
            "signal_source": self.signal_source,
            "summary": self.summary
        }


@dataclass(frozen=True)
class StatusEventPayload:
    """Minimal status event payload."""
    status: str  # e.g., "proposed", "active", "completed", "failed"
    reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "reason": self.reason
        }


ExecutionPayload = Union[
    NavigationEventPayload,
    ExtractionEventPayload,
    SignalEventPayload,
    StatusEventPayload
]


@dataclass(frozen=True)
class ExecutionStreamEvent:
    """
    Append-only execution stream event.

    JSONL-compatible, emitted during mission execution.
    """
    timestamp: str
    mission_id: str
    event_type: ExecutionEventType
    payload: ExecutionPayload

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "mission_id": self.mission_id,
            "event_type": self.event_type.value,
            "payload": self.payload.to_dict()
        }

    def to_json(self) -> str:
        """Convert to JSON string (single line for JSONL)."""
        return json.dumps(self.to_dict(), separators=(",", ":"))


# ---------------------------------------------------------------------------
# Factory helpers
# ---------------------------------------------------------------------------

def utc_now_iso() -> str:
    """UTC timestamp in ISO format."""
    return datetime.utcnow().isoformat()


def navigation_event(
    mission_id: str,
    url: str,
    action: str,
    detail: Optional[str] = None,
    timestamp: Optional[str] = None
) -> ExecutionStreamEvent:
    """Create a navigation event."""
    payload = NavigationEventPayload(url=url, action=action, detail=detail)
    return ExecutionStreamEvent(
        timestamp=timestamp or utc_now_iso(),
        mission_id=mission_id,
        event_type=ExecutionEventType.NAVIGATION,
        payload=payload
    )


def extraction_event(
    mission_id: str,
    target: str,
    items_extracted: int,
    detail: Optional[str] = None,
    timestamp: Optional[str] = None
) -> ExecutionStreamEvent:
    """Create an extraction event."""
    payload = ExtractionEventPayload(
        target=target,
        items_extracted=items_extracted,
        detail=detail
    )
    return ExecutionStreamEvent(
        timestamp=timestamp or utc_now_iso(),
        mission_id=mission_id,
        event_type=ExecutionEventType.EXTRACTION,
        payload=payload
    )


def signal_event(
    mission_id: str,
    signal_type: str,
    signal_layer: str,
    signal_source: str,
    summary: Optional[str] = None,
    timestamp: Optional[str] = None
) -> ExecutionStreamEvent:
    """Create a signal event."""
    payload = SignalEventPayload(
        signal_type=signal_type,
        signal_layer=signal_layer,
        signal_source=signal_source,
        summary=summary
    )
    return ExecutionStreamEvent(
        timestamp=timestamp or utc_now_iso(),
        mission_id=mission_id,
        event_type=ExecutionEventType.SIGNAL,
        payload=payload
    )


def status_event(
    mission_id: str,
    status: str,
    reason: Optional[str] = None,
    timestamp: Optional[str] = None
) -> ExecutionStreamEvent:
    """Create a status event."""
    payload = StatusEventPayload(status=status, reason=reason)
    return ExecutionStreamEvent(
        timestamp=timestamp or utc_now_iso(),
        mission_id=mission_id,
        event_type=ExecutionEventType.STATUS,
        payload=payload
    )
