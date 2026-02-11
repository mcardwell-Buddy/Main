"""
Session Context Manager

Lightweight, in-memory session state for pronouns, carryover, and follow-ups.

STRICT INVARIANTS:
- Session context can ONLY fill gaps when unambiguous
- Session context CANNOT create missions
- Session context CANNOT bypass readiness
- Session context MUST NOT invent data

Flow:
1. Readiness validation happens FIRST (with context read-only)
2. If READY, context is updated with mission fields
3. If INCOMPLETE, context is NOT updated
4. Future requests can use context to resolve ambiguities
"""

from __future__ import annotations

from dataclasses import dataclass, field
from collections import deque
from typing import Optional, Deque, Dict, Any, List, TYPE_CHECKING

from Back_End.action_readiness_engine import ClarificationType

if TYPE_CHECKING:
    from Back_End.interaction_orchestrator import IntentType


@dataclass
class PendingClarification:
    clarification_type: ClarificationType
    missing_field: str
    intent: "IntentType"
    options: Optional[List[str]]


@dataclass
class SessionContext:
    """
    Minimal session state for readiness-safe follow-ups.
    
    No persistence. No side effects. Read-only during validation.
    """
    session_id: str
    
    # Deque for chronological tracking (most recent last)
    recent_source_urls: Deque[str] = field(default_factory=lambda: deque(maxlen=3))
    recent_action_objects: Deque[str] = field(default_factory=lambda: deque(maxlen=3))
    recent_intents: Deque[str] = field(default_factory=lambda: deque(maxlen=3))
    
    # Last READY mission (for "do it again")
    last_ready_mission: Optional[Dict[str, Any]] = None
    
    # Pending mission awaiting approval
    pending_mission: Optional[Dict[str, Any]] = None

    # Pending clarification awaiting user resolution
    pending_clarification: Optional[PendingClarification] = None
    pending_clarification_message: Optional[str] = None
    
    # Last executed mission result (for artifact follow-ups)
    last_execution_artifact: Optional[Dict[str, Any]] = None

    # Lightweight multi-step snapshots (read-only logging)
    step_snapshots: Deque[Dict[str, Any]] = field(default_factory=lambda: deque(maxlen=100))
    
    def add_source_url(self, url: str) -> None:
        """Record a validated source URL."""
        if url and url not in self.recent_source_urls:
            self.recent_source_urls.append(url)
    
    def add_action_object(self, obj: str) -> None:
        """Record a validated action object."""
        if obj and obj not in self.recent_action_objects:
            self.recent_action_objects.append(obj)
    
    def add_intent(self, intent: str) -> None:
        """Record a validated intent."""
        if intent and intent not in self.recent_intents:
            self.recent_intents.append(intent)
    
    def resolve_source_url(self) -> Optional[str]:
        """
        Resolve "there", "the same site", etc. to most recent URL.
        
        SAFE: Only succeeds if exactly one URL in history.
        """
        if len(self.recent_source_urls) == 1:
            return self.recent_source_urls[-1]
        if len(self.recent_source_urls) > 1:
            # Ambiguous: multiple URLs in history
            return None
        return None
    
    def resolve_action_object(self) -> Optional[str]:
        """
        Resolve "it", "that", "those" to most recent action object.
        
        SAFE: Only succeeds if exactly one object in history.
        """
        if len(self.recent_action_objects) == 1:
            return self.recent_action_objects[-1]
        if len(self.recent_action_objects) > 1:
            # Ambiguous: multiple objects in history
            return None
        return None
    
    def can_repeat_last_mission(self) -> bool:
        """
        Check if "do it again" is unambiguous.
        
        SAFE: Only true if exactly one READY mission in session.
        """
        return self.last_ready_mission is not None
    
    def get_repeated_mission_fields(self) -> Optional[Dict[str, Any]]:
        """
        Get fields for repeating last READY mission.
        
        SAFE: Returns None if no prior READY mission.
        """
        if not self.last_ready_mission:
            return None
        
        # Return copy to prevent external mutation
        return dict(self.last_ready_mission)
    
    def set_last_ready_mission(self, readiness_result: Dict[str, Any]) -> None:
        """
        Update context with validated READY mission fields.
        
        Called ONLY after ActionReadinessEngine confirms READY.
        
        Args:
            readiness_result: dict with intent, action_object, action_target, source_url, constraints
        """
        if not readiness_result:
            return
        
        self.last_ready_mission = dict(readiness_result)
        
        # Also update history for future context resolution
        if readiness_result.get('source_url'):
            self.add_source_url(readiness_result['source_url'])
        if readiness_result.get('action_object'):
            self.add_action_object(readiness_result['action_object'])
        if readiness_result.get('intent'):
            self.add_intent(readiness_result['intent'])
    
    def set_pending_mission(self, mission_draft: Dict[str, Any]) -> None:
        """
        Register a READY mission as pending approval.
        
        Called ONLY after ActionReadinessEngine confirms READY and mission is created.
        
        Args:
            mission_draft: Full mission draft dict with mission_id, objective, etc.
        """
        if not mission_draft:
            return
        # Pending approval and clarification are mutually exclusive
        self.clear_pending_clarification()
        self.pending_mission = dict(mission_draft)

    def set_pending_clarification(self, clarification: PendingClarification, original_message: str) -> None:
        """
        Register a pending clarification for resolution.

        Called ONLY when ActionReadinessEngine returns INCOMPLETE.

        Args:
            clarification: PendingClarification metadata
            original_message: The original user message that triggered clarification
        """
        if not clarification:
            return

        # Pending approval and clarification are mutually exclusive
        self.clear_pending_mission()
        self.pending_clarification = clarification
        self.pending_clarification_message = original_message

    def get_pending_clarification(self) -> Optional[PendingClarification]:
        """Get the pending clarification awaiting resolution."""
        return self.pending_clarification

    def get_pending_clarification_message(self) -> Optional[str]:
        """Get the original message that triggered the pending clarification."""
        return self.pending_clarification_message

    def clear_pending_clarification(self) -> None:
        """Clear the pending clarification after resolution or replacement."""
        self.pending_clarification = None
        self.pending_clarification_message = None
    
    def get_pending_mission(self) -> Optional[Dict[str, Any]]:
        """
        Get the pending mission awaiting approval.
        
        Returns:
            Mission draft dict or None if no mission pending
        """
        if not self.pending_mission:
            return None
        
        return dict(self.pending_mission)
    
    def clear_pending_mission(self) -> None:
        """
        Clear the pending mission after approval/rejection.
        
        Called after approval is processed or mission expires.
        """
        self.pending_mission = None
    
    def set_last_execution_artifact(self, artifact: Dict[str, Any]) -> None:
        """
        Record the artifact from a successfully executed mission.
        
        Called ONLY after mission execution completes.
        Used for read-only artifact follow-up answers.
        
        Args:
            artifact: Execution result dict (read-only copy stored)
        """
        if not artifact:
            return
        self.last_execution_artifact = dict(artifact)

    def add_step_snapshot(self, snapshot: Dict[str, Any]) -> None:
        """
        Record a lightweight step snapshot for multi-step analysis.

        Read-only: does not affect routing or mission logic.
        """
        if not snapshot:
            return
        self.step_snapshots.append(dict(snapshot))
    
    def get_last_execution_artifact(self) -> Optional[Dict[str, Any]]:
        """
        Get the most recent executed mission's artifact.
        
        READ-ONLY. Used to answer follow-up questions.
        Returns:
            Artifact dict or None if no execution exists
        """
        if not self.last_execution_artifact:
            return None
        return dict(self.last_execution_artifact)
    
    def get_last_executed_mission(self) -> Optional[Dict[str, Any]]:
        """
        Get info about the last executed mission (for context).
        
        READ-ONLY. Returns combination of last_ready_mission and artifact.
        
        Returns:
            Mission dict with metadata or None
        """
        if not self.last_ready_mission:
            return None
        return dict(self.last_ready_mission)
    
    def clear(self) -> None:
        """Clear all session context (on session expiry)."""
        self.recent_source_urls.clear()
        self.recent_action_objects.clear()
        self.recent_intents.clear()
        self.last_ready_mission = None
        self.pending_mission = None
        self.pending_clarification = None
        self.pending_clarification_message = None
        self.last_execution_artifact = None
        self.step_snapshots.clear()


class SessionContextManager:
    """
    Memory-only manager for per-session contexts.
    
    One context per session_id. Lifetime: session active only.
    """
    
    def __init__(self):
        self._contexts: Dict[str, SessionContext] = {}
    
    def get_or_create(self, session_id: str) -> SessionContext:
        """Get existing context or create new one."""
        if session_id not in self._contexts:
            self._contexts[session_id] = SessionContext(session_id=session_id)
        return self._contexts[session_id]
    
    def clear_session(self, session_id: str) -> None:
        """Clear context when session expires."""
        if session_id in self._contexts:
            del self._contexts[session_id]
    
    def get_all_sessions(self) -> Dict[str, SessionContext]:
        """For testing/debugging only."""
        return dict(self._contexts)

