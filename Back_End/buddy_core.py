"""Buddy Core message entry point.

Telegram and other channels should call this function to obtain a response.
This module owns conversation memory and response generation logic.
"""
from __future__ import annotations

import uuid
from typing import Dict, Any, Optional

from Back_End.conversation.session_store import get_conversation_store


def _build_session_id(source: str, external_user_id: Optional[str]) -> str:
    if source == "telegram" and external_user_id:
        return f"telegram_{external_user_id}"
    return f"session_{uuid.uuid4().hex[:8]}"


def handle_user_message(
    source: str,
    text: str,
    session_id: Optional[str] = None,
    external_user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Handle user input from an external channel and return response text.

    This is a temporary placeholder implementation for validation.
    """
    store = get_conversation_store()
    session_id = session_id or _build_session_id(source, external_user_id)
    session = store.get_or_create(session_id=session_id, source=source, external_user_id=external_user_id)

    store.append_message(session.session_id, role="user", text=text, source=source)

    source_label = source.strip().title() if source else "Unknown"
    response_text = f"Buddy heard you via {source_label}: {text}"

    store.append_message(session.session_id, role="assistant", text=response_text, source="buddy_core")

    return {
        "session_id": session.session_id,
        "response": response_text,
        "linked_goals": list(session.linked_goals),
    }


def list_conversation_sessions() -> list[dict]:
    """Return all sessions in summary form."""
    store = get_conversation_store()
    sessions = []
    for session in store.list_sessions():
        sessions.append({
            "session_id": session.session_id,
            "source": session.source,
            "external_user_id": session.external_user_id,
            "message_count": len(session.messages),
            "linked_goals": list(session.linked_goals),
            "last_message_at": session.messages[-1].timestamp if session.messages else None,
            "title": session.title,
            "archived": session.archived,
        })
    return sessions


def get_conversation_session(session_id: str) -> Optional[dict]:
    """Return a full session with messages."""
    store = get_conversation_store()
    session = store.get_session(session_id)
    if not session:
        return None
    return session.to_dict()


def update_conversation_session(session_id: str, title: Optional[str] = None, archived: Optional[bool] = None) -> bool:
    """Update session metadata."""
    store = get_conversation_store()
    return store.update_session(session_id, title=title, archived=archived)


def delete_conversation_session(session_id: str) -> bool:
    """Delete a session."""
    store = get_conversation_store()
    return store.delete_session(session_id)

