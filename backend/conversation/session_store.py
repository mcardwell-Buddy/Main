"""Conversation session store shared across channels.

Provides a single conversation model for chat UI and Telegram.
"""
from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

# Firebase imports for persistence
try:
    from firebase_admin import firestore
    from backend.config import Config
    FIREBASE_AVAILABLE = Config.FIREBASE_ENABLED
except ImportError:
    FIREBASE_AVAILABLE = False


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ConversationMessage:
    message_id: str
    role: str  # "user" | "assistant"
    text: str
    timestamp: str
    source: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_id": self.message_id,
            "role": self.role,
            "text": self.text,
            "timestamp": self.timestamp,
            "source": self.source,
        }


@dataclass
class ConversationSession:
    session_id: str
    source: str
    external_user_id: Optional[str] = None
    messages: List[ConversationMessage] = field(default_factory=list)
    linked_goals: List[str] = field(default_factory=list)
    title: str = ""
    archived: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "source": self.source,
            "external_user_id": self.external_user_id,
            "messages": [m.to_dict() for m in self.messages],
            "linked_goals": list(self.linked_goals),
            "title": self.title,
            "archived": self.archived,
        }


class ConversationStore:
    """Thread-safe store for conversation sessions with Firebase persistence."""

    def __init__(self) -> None:
        self._sessions: Dict[str, ConversationSession] = {}
        self._lock = threading.RLock()
        
        # Initialize Firebase client if available
        self._firebase_enabled = FIREBASE_AVAILABLE
        self._db = None
        if self._firebase_enabled:
            try:
                import firebase_admin
                from firebase_admin import credentials
                
                # Initialize firebase_admin if not already initialized
                if not firebase_admin._apps:
                    cred_path = Config.FIREBASE_CREDENTIALS_PATH
                    if cred_path:
                        cred = credentials.Certificate(cred_path)
                        firebase_admin.initialize_app(cred)
                    else:
                        raise RuntimeError("FIREBASE_CREDENTIALS_PATH not set")
                
                self._db = firestore.client()
                self._collection = self._db.collection('conversation_sessions')
                self._load_from_firebase()
            except Exception as e:
                print(f"Warning: Failed to initialize Firebase for sessions: {e}")
                self._firebase_enabled = False
    
    def _load_from_firebase(self) -> None:
        """Load all existing sessions from Firebase on startup."""
        if not self._firebase_enabled or not self._db:
            return
        
        try:
            docs = self._collection.stream()
            for doc in docs:
                data = doc.to_dict()
                session = ConversationSession(
                    session_id=data['session_id'],
                    source=data['source'],
                    external_user_id=data.get('external_user_id'),
                    messages=[
                        ConversationMessage(**msg) for msg in data.get('messages', [])
                    ],
                    linked_goals=data.get('linked_goals', []),
                    title=data.get('title', ''),
                    archived=data.get('archived', False),
                )
                self._sessions[session.session_id] = session
            print(f"Loaded {len(self._sessions)} conversation sessions from Firebase")
        except Exception as e:
            print(f"Warning: Failed to load sessions from Firebase: {e}")
    
    def _save_to_firebase(self, session: ConversationSession) -> None:
        """Save a session to Firebase (non-blocking, fire-and-forget)."""
        if not self._firebase_enabled or not self._db:
            return
        
        try:
            self._collection.document(session.session_id).set(session.to_dict())
        except Exception as e:
            print(f"Warning: Failed to save session {session.session_id} to Firebase: {e}")

    def list_sessions(self) -> List[ConversationSession]:
        with self._lock:
            return list(self._sessions.values())

    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        with self._lock:
            return self._sessions.get(session_id)

    def get_or_create(self, session_id: str, source: str, external_user_id: Optional[str]) -> ConversationSession:
        with self._lock:
            if session_id in self._sessions:
                return self._sessions[session_id]
            session = ConversationSession(
                session_id=session_id,
                source=source,
                external_user_id=external_user_id,
            )
            self._sessions[session_id] = session
            self._save_to_firebase(session)
            return session

    def append_message(self, session_id: str, role: str, text: str, source: str) -> ConversationMessage:
        with self._lock:
            session = self._sessions[session_id]
            message = ConversationMessage(
                message_id=f"msg_{len(session.messages) + 1}",
                role=role,
                text=text,
                timestamp=_now_iso(),
                source=source,
            )
            session.messages.append(message)
            self._save_to_firebase(session)
            return message

    def link_goal(self, session_id: str, goal_id: str) -> None:
        with self._lock:
            session = self._sessions[session_id]
            if goal_id not in session.linked_goals:
                session.linked_goals.append(goal_id)
                self._save_to_firebase(session)
    
    def update_session(self, session_id: str, title: Optional[str] = None, archived: Optional[bool] = None) -> bool:
        """Update session metadata (title, archived status)."""
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return False
            if title is not None:
                session.title = title
            if archived is not None:
                session.archived = archived
            self._save_to_firebase(session)
            return True
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session from memory and Firebase."""
        with self._lock:
            if session_id not in self._sessions:
                return False
            del self._sessions[session_id]
            
            # Delete from Firebase
            if self._firebase_enabled and self._db:
                try:
                    self._collection.document(session_id).delete()
                except Exception as e:
                    print(f"Warning: Failed to delete session {session_id} from Firebase: {e}")
            return True


_store: Optional[ConversationStore] = None


def get_conversation_store() -> ConversationStore:
    global _store
    if _store is None:
        _store = ConversationStore()
    return _store
