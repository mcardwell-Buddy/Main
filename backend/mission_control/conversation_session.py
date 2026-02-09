"""
Conversation Session: Tracks conversation context and active goal/program/mission.
Phase 3 Step 2.5: Unifies chat and Telegram inputs with mission structure.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


CONVERSATIONS_FILE = Path("outputs/phase25/conversations.jsonl")


@dataclass
class ConversationSession:
    """Tracks conversation context across chat/Telegram interactions."""
    session_id: str
    source: str  # chat | telegram
    active_goal_id: Optional[str] = None
    active_program_id: Optional[str] = None
    active_mission_id: Optional[str] = None
    last_updated: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "source": self.source,
            "active_goal_id": self.active_goal_id,
            "active_program_id": self.active_program_id,
            "active_mission_id": self.active_mission_id,
            "last_updated": self.last_updated
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> ConversationSession:
        return ConversationSession(
            session_id=data["session_id"],
            source=data["source"],
            active_goal_id=data.get("active_goal_id"),
            active_program_id=data.get("active_program_id"),
            active_mission_id=data.get("active_mission_id"),
            last_updated=data.get("last_updated", "")
        )


class ConversationSessionManager:
    """
    Manages conversation sessions and routing rules.
    Deterministically resolves conversation context.
    """

    def __init__(self, conversations_file: Optional[Path] = None):
        self.conversations_file = conversations_file or CONVERSATIONS_FILE
        self.conversations_file.parent.mkdir(parents=True, exist_ok=True)

    def get_or_create_session(
        self,
        session_id: str,
        source: str = "chat"
    ) -> ConversationSession:
        """
        Get existing session or create new one.
        
        Args:
            session_id: Unique session identifier
            source: chat | telegram
        
        Returns:
            ConversationSession object
        """
        session = self.get_session(session_id)
        if session:
            return session
        
        # Create new session
        session = ConversationSession(
            session_id=session_id,
            source=source,
            last_updated=datetime.now(timezone.utc).isoformat()
        )
        
        self._persist_session(session)
        return session

    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """Retrieve session by ID."""
        sessions = self._load_sessions()
        for session_data in sessions:
            if session_data["session_id"] == session_id:
                return ConversationSession.from_dict(session_data)
        return None

    def update_session_context(
        self,
        session_id: str,
        goal_id: Optional[str] = None,
        program_id: Optional[str] = None,
        mission_id: Optional[str] = None
    ) -> Optional[ConversationSession]:
        """
        Update active context for a session.
        
        Args:
            session_id: Session to update
            goal_id: Active goal (None to clear)
            program_id: Active program (None to clear)
            mission_id: Active mission (None to clear)
        
        Returns:
            Updated ConversationSession
        """
        session = self.get_session(session_id)
        if not session:
            return None
        
        if goal_id is not None:
            session.active_goal_id = goal_id
        if program_id is not None:
            session.active_program_id = program_id
        if mission_id is not None:
            session.active_mission_id = mission_id
        
        session.last_updated = datetime.now(timezone.utc).isoformat()
        self._update_session(session)
        
        return session

    def resolve_context(
        self,
        session_id: str,
        message: str
    ) -> Dict[str, Any]:
        """
        Deterministically resolve conversation context based on message.
        
        Routing Rules:
        - If discussing results → attach to last mission
        - If asking why/what happened → resolve mission → program → goal
        - If asking to explore/find/test → propose new mission under current program
        - If no goal exists → create one only with user confirmation
        
        Args:
            session_id: Current session
            message: User message content
        
        Returns:
            Context dict with routing information
        """
        session = self.get_session(session_id)
        if not session:
            session = self.get_or_create_session(session_id)
        
        message_lower = message.lower()
        
        # Rule 1: Discussing results
        result_keywords = ["result", "found", "collected", "extracted", "opportunity", "opportunities"]
        if any(kw in message_lower for kw in result_keywords):
            return {
                "routing": "results_discussion",
                "attach_to_mission": session.active_mission_id,
                "goal_id": session.active_goal_id,
                "program_id": session.active_program_id,
                "requires_confirmation": False
            }
        
        # Rule 2: Asking why/what happened
        diagnostic_keywords = ["why", "what happened", "failed", "error", "problem", "issue"]
        if any(kw in message_lower for kw in diagnostic_keywords):
            return {
                "routing": "diagnostic",
                "mission_id": session.active_mission_id,
                "program_id": session.active_program_id,
                "goal_id": session.active_goal_id,
                "requires_confirmation": False
            }
        
        # Rule 3: Asking to explore/find/test
        exploration_keywords = ["find", "explore", "test", "search", "collect", "scrape", "get"]
        if any(kw in message_lower for kw in exploration_keywords):
            return {
                "routing": "new_mission_proposal",
                "program_id": session.active_program_id,
                "goal_id": session.active_goal_id,
                "requires_confirmation": True,
                "suggested_action": "propose_mission"
            }
        
        # Rule 4: No clear context
        return {
            "routing": "unclear",
            "goal_id": session.active_goal_id,
            "program_id": session.active_program_id,
            "requires_confirmation": True,
            "suggested_action": "clarify_intent"
        }

    def list_sessions(self, source: Optional[str] = None) -> List[ConversationSession]:
        """List all sessions, optionally filtered by source."""
        sessions = self._load_sessions()
        session_objects = [ConversationSession.from_dict(s) for s in sessions]
        
        if source:
            session_objects = [s for s in session_objects if s.source == source]
        
        return session_objects

    def _load_sessions(self) -> List[Dict[str, Any]]:
        """Load all sessions from file."""
        if not self.conversations_file.exists():
            return []
        
        sessions = []
        with open(self.conversations_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        sessions.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return sessions

    def _persist_session(self, session: ConversationSession) -> None:
        """Append session to file."""
        with open(self.conversations_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(session.to_dict()) + "\n")

    def _update_session(self, session: ConversationSession) -> None:
        """Update existing session in file."""
        sessions = self._load_sessions()
        
        # Find and update
        for i, s in enumerate(sessions):
            if s["session_id"] == session.session_id:
                sessions[i] = session.to_dict()
                break
        
        # Rewrite file
        with open(self.conversations_file, "w", encoding="utf-8") as f:
            for s in sessions:
                f.write(json.dumps(s) + "\n")
