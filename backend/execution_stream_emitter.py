"""
Execution Stream Emitter

Append-only JSONL writer for execution stream events.
READ-ONLY: emits events only. No control signals.
"""

from dataclasses import dataclass
from typing import Optional
from pathlib import Path
from uuid import uuid4

from backend.execution_stream_events import (
    ExecutionStreamEvent,
    navigation_event,
    extraction_event,
    signal_event,
    status_event
)


@dataclass
class ExecutionStreamConfig:
    """Configuration for execution stream output."""
    base_dir: Path
    stream_id: str

    @property
    def file_path(self) -> Path:
        return self.base_dir / f"{self.stream_id}.jsonl"


class ExecutionStreamEmitter:
    """
    Append-only emitter for execution stream events.

    Does NOT control execution. Does NOT modify mission behavior.
    """

    def __init__(self, base_dir: Optional[str] = None, stream_id: Optional[str] = None):
        self._base_dir = Path(base_dir or "outputs/execution_streams")
        self._base_dir.mkdir(parents=True, exist_ok=True)
        self._stream_id = stream_id or f"stream_{uuid4().hex}"
        self._config = ExecutionStreamConfig(base_dir=self._base_dir, stream_id=self._stream_id)

    @property
    def stream_id(self) -> str:
        return self._stream_id

    @property
    def file_path(self) -> str:
        return str(self._config.file_path)

    def emit(self, event: ExecutionStreamEvent) -> None:
        """Append an event to the JSONL stream."""
        with self._config.file_path.open("a", encoding="utf-8") as handle:
            handle.write(event.to_json())
            handle.write("\n")
            handle.flush()

    def emit_navigation(
        self,
        mission_id: str,
        url: str,
        action: str,
        detail: Optional[str] = None
    ) -> None:
        """Emit a navigation event."""
        self.emit(navigation_event(
            mission_id=mission_id,
            url=url,
            action=action,
            detail=detail
        ))

    def emit_extraction(
        self,
        mission_id: str,
        target: str,
        items_extracted: int,
        detail: Optional[str] = None
    ) -> None:
        """Emit an extraction event."""
        self.emit(extraction_event(
            mission_id=mission_id,
            target=target,
            items_extracted=items_extracted,
            detail=detail
        ))

    def emit_signal(
        self,
        mission_id: str,
        signal_type: str,
        signal_layer: str,
        signal_source: str,
        summary: Optional[str] = None
    ) -> None:
        """Emit a signal event."""
        self.emit(signal_event(
            mission_id=mission_id,
            signal_type=signal_type,
            signal_layer=signal_layer,
            signal_source=signal_source,
            summary=summary
        ))

    def emit_status(
        self,
        mission_id: str,
        status: str,
        reason: Optional[str] = None
    ) -> None:
        """Emit a status event."""
        self.emit(status_event(
            mission_id=mission_id,
            status=status,
            reason=reason
        ))
