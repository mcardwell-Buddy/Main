"""
Mission Control: Progress tracking for mission objectives.

This module tracks real-time progress of missions as they execute.
Progress can be tracked by:
- Step completion (verification → intent classification → tool selection → execution)
- Percentage completion (0-100%)
- Milestones (budget check, tool invocation, artifact creation)

Integration: execution_service calls methods on MissionProgressTracker
to report progress, which emits events to Firebase and streaming_events.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Callable

logger = logging.getLogger(__name__)


@dataclass
class ExecutionStep:
    """Represents a single execution step with progress information."""
    step_name: str
    step_index: int
    total_steps: int
    progress_percent: int
    status: str  # "pending", "started", "completed", "failed"
    message: str
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_name": self.step_name,
            "step_index": self.step_index,
            "total_steps": self.total_steps,
            "progress_percent": self.progress_percent,
            "status": self.status,
            "message": self.message,
            "timestamp": self.timestamp
        }


@dataclass
class MissionProgressTracker:
    """
    Tracks mission execution progress from start to completion.
    
    Progress Flow:
    1. Verification (5-10%)
    2. Intent Classification (10-30%)
    3. Budget Check (30-40%)
    4. Tool Selection (40-55%)
    5. Tool Execution (55-80%)
    6. Artifact Creation (80-90%)
    7. Summary & Learning (90-100%)
    
    The tracker calls emitter callbacks at each step to update:
    - Firebase mission record with progress
    - streaming_events for real-time dashboard updates
    - Client-side progress bars
    """
    mission_id: str
    start_time: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    # Track by step
    current_step: Optional[ExecutionStep] = None
    completed_steps: List[ExecutionStep] = field(default_factory=list)
    
    # Legacy: items collected for web extraction missions
    total_items_collected: int = 0
    pages_since_last_increase: int = 0
    last_progress_timestamp: Optional[str] = None
    
    # Callbacks for emitting progress updates
    progress_callbacks: List[Callable[[str, Dict[str, Any]], None]] = field(default_factory=list)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "MissionProgressTracker":
        return MissionProgressTracker(
            mission_id=data.get("mission_id", "unknown"),
            total_items_collected=int(data.get("total_items_collected", 0)),
            pages_since_last_increase=int(data.get("pages_since_last_increase", 0)),
            last_progress_timestamp=data.get("last_progress_timestamp")
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mission_id": self.mission_id,
            "start_time": self.start_time,
            "current_step": self.current_step.to_dict() if self.current_step else None,
            "completed_steps": [s.to_dict() for s in self.completed_steps],
            "total_items_collected": self.total_items_collected,
            "pages_since_last_increase": self.pages_since_last_increase,
            "last_progress_timestamp": self.last_progress_timestamp
        }

    def register_callback(self, callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """Register a callback to be called when progress updates occur."""
        self.progress_callbacks.append(callback)

    def _emit_progress(self, event_type: str, data: Dict[str, Any]) -> None:
        """Emit progress event to all registered callbacks."""
        for callback in self.progress_callbacks:
            try:
                callback(event_type, data)
            except Exception as e:
                logger.error(f"[PROGRESS_TRACKER] Callback failed: {e}")

    def start_step(
        self,
        step_name: str,
        step_index: int,
        total_steps: int,
        progress_percent: int,
        message: str
    ) -> None:
        """Mark the start of an execution step."""
        self.current_step = ExecutionStep(
            step_name=step_name,
            step_index=step_index,
            total_steps=total_steps,
            progress_percent=progress_percent,
            status="started",
            message=message,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        logger.info(f"[PROGRESS_TRACKER] Step {step_index}/{total_steps}: {step_name} ({progress_percent}%)")
        self._emit_progress("step_started", self.current_step.to_dict())

    def complete_step(self, message: Optional[str] = None) -> None:
        """Mark the current step as completed."""
        if self.current_step:
            self.current_step.status = "completed"
            if message:
                self.current_step.message = message
            self.current_step.timestamp = datetime.now(timezone.utc).isoformat()
            self.completed_steps.append(self.current_step)
            logger.info(f"[PROGRESS_TRACKER] Completed: {self.current_step.step_name} ({self.current_step.progress_percent}%)")
            self._emit_progress("step_completed", self.current_step.to_dict())
            self.current_step = None

    def fail_step(self, error_message: str) -> None:
        """Mark the current step as failed."""
        if self.current_step:
            self.current_step.status = "failed"
            self.current_step.message = error_message
            self.current_step.timestamp = datetime.now(timezone.utc).isoformat()
            self.completed_steps.append(self.current_step)
            logger.error(f"[PROGRESS_TRACKER] Failed: {self.current_step.step_name} - {error_message}")
            self._emit_progress("step_failed", self.current_step.to_dict())
            self.current_step = None

    def get_progress_percent(self) -> int:
        """Return current progress percentage (0-100)."""
        if self.current_step:
            return self.current_step.progress_percent
        if self.completed_steps:
            return self.completed_steps[-1].progress_percent
        return 0

    def get_elapsed_seconds(self) -> float:
        """Return seconds elapsed since mission started."""
        start = datetime.fromisoformat(self.start_time)
        elapsed = datetime.now(timezone.utc) - start
        return elapsed.total_seconds()

    # Legacy methods for backward compatibility
    def update(self, items_collected_this_step: int, pages_visited: int) -> None:
        """Legacy: Update items collected (for web extraction missions)."""
        if items_collected_this_step > 0:
            self.total_items_collected += items_collected_this_step
            self.pages_since_last_increase = 0
            self.last_progress_timestamp = datetime.now(timezone.utc).isoformat()
        else:
            self.pages_since_last_increase += max(pages_visited, 1)
            if not self.last_progress_timestamp:
                self.last_progress_timestamp = datetime.now(timezone.utc).isoformat()

