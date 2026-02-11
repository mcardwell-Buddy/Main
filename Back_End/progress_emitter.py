"""
Progress Emitter: Bridge between MissionProgressTracker and StreamingEventEmitter

This module connects the progress tracking callbacks to the streaming events system,
enabling real-time progress updates to WebSocket clients and Firebase.

Integration:
- MissionProgressTracker emits progress updates via callbacks
- ProgressEmitter catches these callbacks
- Converts to StreamingEvent format
- Emits to StreamingEventEmitter for WebSocket broadcast
"""

from typing import Dict, Any, Optional
from datetime import datetime, timezone
import logging

from Back_End.streaming_events import (
    get_event_emitter,
    MissionStatus,
)

logger = logging.getLogger(__name__)


class ProgressEmitter:
    """Bridges MissionProgressTracker progress events to StreamingEventEmitter."""
    
    def __init__(self, mission_id: str):
        """
        Initialize progress emitter for a mission.
        
        Args:
            mission_id: The mission being tracked
        """
        self.mission_id = mission_id
        self.emitter = get_event_emitter()
        self.step_count = 0
    
    def on_progress_update(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Callback for progress tracker updates.
        
        Emitted events:
        - 'step_started': Execution step starting
        - 'step_completed': Execution step completed
        - 'step_failed': Execution step failed
        - 'progress_update': Custom progress update
        
        Args:
            event_type: Type of progress event
            data: Progress event data (from ExecutionStep or custom)
        """
        try:
            if event_type == "step_started":
                self._handle_step_started(data)
            elif event_type == "step_completed":
                self._handle_step_completed(data)
            elif event_type == "step_failed":
                self._handle_step_failed(data)
            elif event_type == "progress_update":
                self._handle_custom_progress(data)
        except Exception as e:
            logger.error(f"[PROGRESS_EMITTER] Callback error for {self.mission_id}: {e}")
    
    def _handle_step_started(self, step_data: Dict[str, Any]) -> None:
        """Handle execution step started event."""
        progress_percent = step_data.get("progress_percent", 0)
        step_name = step_data.get("step_name", "Unknown")
        message = step_data.get("message", "")
        
        # Emit to streaming events for real-time dashboard
        step_description = f"{step_name}: {message}" if message else step_name
        self.emitter.emit_execution_step(
            mission_id=self.mission_id,
            step_name=step_name,
            step_status="started",
            step_index=step_data.get("step_index", self.step_count),
            total_steps=step_data.get("total_steps", 7),
            progress_percent=progress_percent,
            message=f"Starting: {message}"
        )
        
        # Also emit mission progress for simpler clients
        self.emitter.emit_mission_progress(
            mission_id=self.mission_id,
            progress_percent=progress_percent,
            current_step=step_description
        )
        
        logger.info(f"[PROGRESS_EMITTER] Step started: {step_name} ({progress_percent}%)")
    
    def _handle_step_completed(self, step_data: Dict[str, Any]) -> None:
        """Handle execution step completed event."""
        progress_percent = step_data.get("progress_percent", 0)
        step_name = step_data.get("step_name", "Unknown")
        message = step_data.get("message", "")
        
        # Emit step completion to streaming events
        self.emitter.emit_execution_step(
            mission_id=self.mission_id,
            step_name=step_name,
            step_status="completed",
            step_index=step_data.get("step_index", self.step_count),
            total_steps=step_data.get("total_steps", 7),
            progress_percent=progress_percent,
            message=f"Completed: {message}"
        )
        
        # Also emit mission progress
        step_description = f"{step_name}: {message}" if message else step_name
        self.emitter.emit_mission_progress(
            mission_id=self.mission_id,
            progress_percent=progress_percent,
            current_step=step_description
        )
        
        self.step_count += 1
        logger.info(f"[PROGRESS_EMITTER] Step completed: {step_name} ({progress_percent}%)")
    
    def _handle_step_failed(self, step_data: Dict[str, Any]) -> None:
        """Handle execution step failed event."""
        progress_percent = step_data.get("progress_percent", 0)
        step_name = step_data.get("step_name", "Unknown")
        error_message = step_data.get("message", "Unknown error")
        
        # Emit step failure to streaming events
        self.emitter.emit_execution_step(
            mission_id=self.mission_id,
            step_name=step_name,
            step_status="failed",
            step_index=step_data.get("step_index", self.step_count),
            total_steps=step_data.get("total_steps", 7),
            progress_percent=progress_percent,
            message=f"Failed: {error_message}"
        )
        
        # Note: Don't update mission progress on failure - it stays at last good value
        logger.warning(f"[PROGRESS_EMITTER] Step failed: {step_name} - {error_message}")
    
    def _handle_custom_progress(self, data: Dict[str, Any]) -> None:
        """Handle custom progress update."""
        progress_percent = data.get("progress_percent", 0)
        message = data.get("message", "Progress update")
        
        # Emit custom progress to streaming events
        self.emitter.emit_mission_progress(
            mission_id=self.mission_id,
            progress_percent=progress_percent,
            current_step=message
        )
        
        logger.debug(f"[PROGRESS_EMITTER] Custom progress: {message} ({progress_percent}%)")


def register_progress_emitter(
    mission_id: str,
    tracker: 'MissionProgressTracker'
) -> ProgressEmitter:
    """
    Register a progress emitter as a callback on a mission progress tracker.
    
    This wires the progress tracking system to the streaming events system,
    enabling real-time updates to WebSocket clients.
    
    Args:
        mission_id: The mission being executed
        tracker: MissionProgressTracker instance to attach to
    
    Returns:
        ProgressEmitter instance (for testing/inspection)
    
    Example:
        ```python
        tracker = MissionProgressTracker(mission_id="mission-123")
        emitter = register_progress_emitter("mission-123", tracker)
        
        # Now, when tracker.start_step() is called, it automatically
        # emits streaming events via the emitter
        
        tracker.start_step("Tool selection", 4, 7, 40, "Selecting tools...")
        # → emits to StreamingEventEmitter
        # → broadcasts to all WebSocket clients
        ```
    """
    emitter = ProgressEmitter(mission_id)
    tracker.register_callback(emitter.on_progress_update)
    logger.info(f"[PROGRESS_EMITTER] Registered for mission {mission_id}")
    return emitter
