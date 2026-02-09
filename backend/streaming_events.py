"""
Execution Streaming Events Schema
Observability-only event stream tied to mission_id
NO control commands, NO autonomy
"""

from enum import Enum
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Any, Optional
import json


class StreamingEventType(Enum):
    """Event types for mission execution"""
    
    # Mission lifecycle
    MISSION_START = "mission_start"
    MISSION_PROGRESS = "mission_progress"
    MISSION_STOP = "mission_stop"
    
    # Execution steps
    SELECTOR_ATTEMPT = "selector_attempt"
    INTENT_DECISION = "intent_decision"

    # Execution instrumentation
    EXECUTION_STEP = "execution_step"
    TOOL_INVOKED = "tool_invoked"
    TOOL_RESULT = "tool_result"
    ARTIFACT_PREVIEW = "artifact_preview"
    
    # Status changes
    MISSION_STATUS_CHANGE = "mission_status_change"


class SelectorAttemptStatus(Enum):
    """Selector attempt outcomes"""
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"


class IntentDecisionType(Enum):
    """Intent decision types"""
    NAVIGATE = "navigate"
    EXTRACT = "extract"
    ANALYZE = "analyze"
    SYNTHESIZE = "synthesize"
    WAIT = "wait"
    OTHER = "other"


class MissionStatus(Enum):
    """Mission status values"""
    QUEUED = "queued"
    STARTED = "started"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class StreamingEvent:
    """Base streaming event structure"""
    mission_id: str
    event_type: StreamingEventType
    timestamp: datetime
    sequence_number: int
    data: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "mission_id": self.mission_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "sequence_number": self.sequence_number,
            "data": self.data,
        }
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())


@dataclass
class MissionStartEvent(StreamingEvent):
    """Mission start event"""
    
    @staticmethod
    def create(
        mission_id: str,
        objective: str,
        sequence_number: int,
        timestamp: Optional[datetime] = None,
    ) -> "MissionStartEvent":
        """Create a mission start event"""
        return MissionStartEvent(
            mission_id=mission_id,
            event_type=StreamingEventType.MISSION_START,
            timestamp=timestamp or datetime.utcnow(),
            sequence_number=sequence_number,
            data={
                "objective": objective,
                "started_at": (timestamp or datetime.utcnow()).isoformat(),
            },
        )


@dataclass
class MissionProgressEvent(StreamingEvent):
    """Mission progress event"""
    
    @staticmethod
    def create(
        mission_id: str,
        progress_percent: int,
        current_step: str,
        sequence_number: int,
        timestamp: Optional[datetime] = None,
    ) -> "MissionProgressEvent":
        """Create a mission progress event"""
        return MissionProgressEvent(
            mission_id=mission_id,
            event_type=StreamingEventType.MISSION_PROGRESS,
            timestamp=timestamp or datetime.utcnow(),
            sequence_number=sequence_number,
            data={
                "progress_percent": progress_percent,
                "current_step": current_step,
                "updated_at": (timestamp or datetime.utcnow()).isoformat(),
            },
        )


@dataclass
class MissionStopEvent(StreamingEvent):
    """Mission stop event"""
    
    @staticmethod
    def create(
        mission_id: str,
        reason: str,
        final_status: MissionStatus,
        sequence_number: int,
        timestamp: Optional[datetime] = None,
    ) -> "MissionStopEvent":
        """Create a mission stop event"""
        return MissionStopEvent(
            mission_id=mission_id,
            event_type=StreamingEventType.MISSION_STOP,
            timestamp=timestamp or datetime.utcnow(),
            sequence_number=sequence_number,
            data={
                "reason": reason,
                "final_status": final_status.value,
                "stopped_at": (timestamp or datetime.utcnow()).isoformat(),
            },
        )


@dataclass
class SelectorAttemptEvent(StreamingEvent):
    """Selector attempt event (observability only)"""
    
    @staticmethod
    def create(
        mission_id: str,
        selector_id: str,
        selector_description: str,
        status: SelectorAttemptStatus,
        sequence_number: int,
        details: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ) -> "SelectorAttemptEvent":
        """Create a selector attempt event"""
        return SelectorAttemptEvent(
            mission_id=mission_id,
            event_type=StreamingEventType.SELECTOR_ATTEMPT,
            timestamp=timestamp or datetime.utcnow(),
            sequence_number=sequence_number,
            data={
                "selector_id": selector_id,
                "selector_description": selector_description,
                "status": status.value,
                "details": details or {},
                "attempted_at": (timestamp or datetime.utcnow()).isoformat(),
            },
        )


@dataclass
class IntentDecisionEvent(StreamingEvent):
    """Intent decision event (observability only)"""
    
    @staticmethod
    def create(
        mission_id: str,
        intent_type: IntentDecisionType,
        reasoning: str,
        sequence_number: int,
        parameters: Optional[Dict[str, Any]] = None,
        confidence: Optional[float] = None,
        timestamp: Optional[datetime] = None,
    ) -> "IntentDecisionEvent":
        """Create an intent decision event"""
        return IntentDecisionEvent(
            mission_id=mission_id,
            event_type=StreamingEventType.INTENT_DECISION,
            timestamp=timestamp or datetime.utcnow(),
            sequence_number=sequence_number,
            data={
                "intent_type": intent_type.value,
                "reasoning": reasoning,
                "parameters": parameters or {},
                "confidence": confidence,
                "decided_at": (timestamp or datetime.utcnow()).isoformat(),
            },
        )


@dataclass
class MissionStatusChangeEvent(StreamingEvent):
    """Mission status change event"""
    
    @staticmethod
    def create(
        mission_id: str,
        old_status: MissionStatus,
        new_status: MissionStatus,
        reason: str,
        sequence_number: int,
        timestamp: Optional[datetime] = None,
    ) -> "MissionStatusChangeEvent":
        """Create a mission status change event"""
        return MissionStatusChangeEvent(
            mission_id=mission_id,
            event_type=StreamingEventType.MISSION_STATUS_CHANGE,
            timestamp=timestamp or datetime.utcnow(),
            sequence_number=sequence_number,
            data={
                "old_status": old_status.value,
                "new_status": new_status.value,
                "reason": reason,
                "changed_at": (timestamp or datetime.utcnow()).isoformat(),
            },
        )


class StreamingEventEmitter:
    """Emits streaming events (observability only)"""
    
    def __init__(self):
        """Initialize emitter"""
        self.event_listeners: Dict[str, List[callable]] = {}
        self.mission_sequences: Dict[str, int] = {}
        self.event_buffer: Dict[str, List[StreamingEvent]] = {}  # Buffer for late subscribers
        self.buffer_size = 100  # Keep last 100 events per mission
    
    def subscribe(self, mission_id: str, callback: callable) -> None:
        """Subscribe to events for a mission and replay buffered events"""
        if mission_id not in self.event_listeners:
            self.event_listeners[mission_id] = []
        self.event_listeners[mission_id].append(callback)
        
        # IMPORTANT: Replay buffered events to the new subscriber
        # This ensures WebSocket clients that connect late still see prior events
        if mission_id in self.event_buffer:
            print(f"[EVENT BUFFER] Replaying {len(self.event_buffer[mission_id])} buffered events for mission {mission_id}")
            for buffered_event in self.event_buffer[mission_id]:
                try:
                    callback(buffered_event)
                except Exception as e:
                    print(f"Error replaying buffered event to subscriber: {e}")
    
    def unsubscribe(self, mission_id: str, callback: callable) -> None:
        """Unsubscribe from events for a mission"""
        if mission_id in self.event_listeners:
            self.event_listeners[mission_id].remove(callback)
    
    def emit(self, event: StreamingEvent) -> None:
        """Emit an event to all listeners and buffer it for late subscribers"""
        mission_id = event.mission_id
        
        # Track sequence numbers per mission
        if mission_id not in self.mission_sequences:
            self.mission_sequences[mission_id] = 0
        self.mission_sequences[mission_id] += 1
        event.sequence_number = self.mission_sequences[mission_id]
        
        # Buffer the event (for late subscribers)
        if mission_id not in self.event_buffer:
            self.event_buffer[mission_id] = []
        self.event_buffer[mission_id].append(event)
        # Keep buffer size limited
        if len(self.event_buffer[mission_id]) > self.buffer_size:
            self.event_buffer[mission_id].pop(0)
        
        # Notify all listeners (one-way broadcast, no response expected)
        if mission_id in self.event_listeners:
            for callback in self.event_listeners[mission_id]:
                try:
                    callback(event)
                except Exception as e:
                    # Listener errors don't affect other listeners
                    print(f"Listener error for {mission_id}: {e}")
    
    def emit_mission_start(
        self,
        mission_id: str,
        objective: str,
    ) -> None:
        """Emit mission start event"""
        event = MissionStartEvent.create(
            mission_id=mission_id,
            objective=objective,
            sequence_number=0,  # Will be overridden
        )
        self.emit(event)
    
    def emit_mission_progress(
        self,
        mission_id: str,
        progress_percent: int,
        current_step: str,
    ) -> None:
        """Emit mission progress event"""
        event = MissionProgressEvent.create(
            mission_id=mission_id,
            progress_percent=progress_percent,
            current_step=current_step,
            sequence_number=0,  # Will be overridden
        )
        self.emit(event)
    
    def emit_mission_stop(
        self,
        mission_id: str,
        reason: str,
        final_status: MissionStatus,
    ) -> None:
        """Emit mission stop event"""
        event = MissionStopEvent.create(
            mission_id=mission_id,
            reason=reason,
            final_status=final_status,
            sequence_number=0,  # Will be overridden
        )
        self.emit(event)
    
    def emit_selector_attempt(
        self,
        mission_id: str,
        selector_id: str,
        selector_description: str,
        status: SelectorAttemptStatus,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Emit selector attempt event (observability only)"""
        event = SelectorAttemptEvent.create(
            mission_id=mission_id,
            selector_id=selector_id,
            selector_description=selector_description,
            status=status,
            sequence_number=0,  # Will be overridden
            details=details,
        )
        self.emit(event)
    
    def emit_intent_decision(
        self,
        mission_id: str,
        intent_type: IntentDecisionType,
        reasoning: str,
        parameters: Optional[Dict[str, Any]] = None,
        confidence: Optional[float] = None,
    ) -> None:
        """Emit intent decision event (observability only)"""
        event = IntentDecisionEvent.create(
            mission_id=mission_id,
            intent_type=intent_type,
            reasoning=reasoning,
            sequence_number=0,  # Will be overridden
            parameters=parameters,
            confidence=confidence,
        )
        self.emit(event)

    def emit_execution_step(
        self,
        mission_id: str,
        step_name: str,
        step_status: str,
        step_index: Optional[int] = None,
        total_steps: Optional[int] = None,
        progress_percent: Optional[int] = None,
        message: Optional[str] = None,
    ) -> None:
        """Emit execution step event (observability only)."""
        event = StreamingEvent(
            mission_id=mission_id,
            event_type=StreamingEventType.EXECUTION_STEP,
            timestamp=datetime.utcnow(),
            sequence_number=0,  # Will be overridden
            data={
                "step_name": step_name,
                "step_status": step_status,
                "step_index": step_index,
                "total_steps": total_steps,
                "progress_percent": progress_percent,
                "message": message,
                "updated_at": datetime.utcnow().isoformat(),
            },
        )
        self.emit(event)

    def emit_tool_invoked(
        self,
        mission_id: str,
        tool_name: str,
        tool_input: Any,
        message: Optional[str] = None,
    ) -> None:
        """Emit tool invocation event (observability only)."""
        event = StreamingEvent(
            mission_id=mission_id,
            event_type=StreamingEventType.TOOL_INVOKED,
            timestamp=datetime.utcnow(),
            sequence_number=0,  # Will be overridden
            data={
                "tool_name": tool_name,
                "tool_input": tool_input,
                "message": message,
                "invoked_at": datetime.utcnow().isoformat(),
            },
        )
        self.emit(event)

    def emit_tool_result(
        self,
        mission_id: str,
        tool_name: str,
        success: bool,
        summary: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Emit tool result event (observability only)."""
        event = StreamingEvent(
            mission_id=mission_id,
            event_type=StreamingEventType.TOOL_RESULT,
            timestamp=datetime.utcnow(),
            sequence_number=0,  # Will be overridden
            data={
                "tool_name": tool_name,
                "success": success,
                "summary": summary,
                "details": details or {},
                "completed_at": datetime.utcnow().isoformat(),
            },
        )
        self.emit(event)

    def emit_artifact_preview(
        self,
        mission_id: str,
        artifact_type: str,
        preview: Dict[str, Any],
        message: Optional[str] = None,
    ) -> None:
        """Emit artifact preview event (observability only)."""
        event = StreamingEvent(
            mission_id=mission_id,
            event_type=StreamingEventType.ARTIFACT_PREVIEW,
            timestamp=datetime.utcnow(),
            sequence_number=0,  # Will be overridden
            data={
                "artifact_type": artifact_type,
                "preview": preview,
                "message": message,
                "created_at": datetime.utcnow().isoformat(),
            },
        )
        self.emit(event)
    
    def emit_mission_status_change(
        self,
        mission_id: str,
        old_status: MissionStatus,
        new_status: MissionStatus,
        reason: str,
    ) -> None:
        """Emit mission status change event"""
        event = MissionStatusChangeEvent.create(
            mission_id=mission_id,
            old_status=old_status,
            new_status=new_status,
            reason=reason,
            sequence_number=0,  # Will be overridden
        )
        self.emit(event)


# Global emitter instance
_global_emitter: Optional[StreamingEventEmitter] = None


def get_event_emitter() -> StreamingEventEmitter:
    """Get or create global event emitter"""
    global _global_emitter
    if _global_emitter is None:
        _global_emitter = StreamingEventEmitter()
    return _global_emitter
