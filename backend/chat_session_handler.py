"""
Chat Session Handler

Integrates chat input with Buddy's execution pipeline.

Flow:
  User Message
       ↓
  [ChatSessionHandler]
       ↓
  [InteractionOrchestrator]
       ↓
  [ResponseEnvelope]
       ↓
  Return to UI

CONSTRAINTS:
- NO UI code
- NO frontend assumptions
- NO logic changes to existing agents
- NO autonomy (missions always status='proposed')

Logging:
- chat_received: Input message logged
- response_generated: Output envelope logged
- mission_spawned: Mission creation logged (if applicable)
- signal_emitted: All signals logged via signal layer
"""

import logging
import json
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from uuid import uuid4

from backend.interaction_orchestrator import orchestrate_message
from backend.response_envelope import ResponseEnvelope
from backend.build_review import BuildReviewRegistry
from backend.economic_scenario import EconomicScenarioRegistry


logger = logging.getLogger(__name__)


@dataclass
class ChatMessage:
    """Incoming chat message with observability trace_id."""
    message_id: str
    user_id: str
    session_id: str
    text: str
    timestamp: str
    trace_id: str  # Unique trace ID for end-to-end observability
    context: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict:
        return {
            'message_id': self.message_id,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'text': self.text,
            'timestamp': self.timestamp,
            'trace_id': self.trace_id,
            'context': self.context
        }


@dataclass
class ChatResponse:
    """Outgoing response envelope with trace_id."""
    response_id: str
    message_id: str
    session_id: str
    trace_id: str  # Propagated from ChatMessage for traceability
    envelope: ResponseEnvelope
    timestamp: str
    
    def to_dict(self) -> Dict:
        return {
            'response_id': self.response_id,
            'message_id': self.message_id,
            'session_id': self.session_id,
            'trace_id': self.trace_id,
            'envelope': self.envelope.to_dict(),
            'timestamp': self.timestamp
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())


class ChatSessionHandler:
    """
    Handles chat message lifecycle.
    
    ONE flow per message:
    1. Receive ChatMessage
    2. Log: chat_received
    3. Call InteractionOrchestrator
    4. Get ResponseEnvelope
    5. Log: response_generated
    6. If missions spawned: log mission_spawned
    7. Return ChatResponse
    
    Mission lifecycle continues independently via signals.
    Whiteboard updates occur via signal emissions only.
    """
    
    def __init__(self, session_id: str, user_id: str = "default"):
        """
        Initialize chat session handler.
        
        Args:
            session_id: Unique session identifier
            user_id: User identifier
        """
        self.session_id = session_id
        self.user_id = user_id
        self.created_at = datetime.utcnow().isoformat()
        self.message_count = 0
        self.mission_count = 0
        
        logger.info(
            f"[CHAT_SESSION] Initialized - session_id={session_id}, "
            f"user_id={user_id}"
        )
    
    def handle_message(
        self,
        message: Union[ChatMessage, str] = None,
        context: Optional[Dict[str, Any]] = None,
        message_id: Optional[str] = None,
        text: Optional[str] = None
    ) -> ChatResponse:
        """
        Handle a single chat message end-to-end.
        
        Supports two calling conventions:
        1. message=ChatMessage(...) - direct ChatMessage object
        2. text="..." - legacy text + context + message_id
        
        Flow:
        1. Validate ChatMessage
        2. Log: chat_received
        3. Call orchestrator
        4. Package response
        5. Log: response_generated + mission_spawned (if applicable)
        6. Return ChatResponse
        
        Args:
            message: ChatMessage object or text string
            context: Optional context (legacy)
            message_id: Optional message ID (legacy)
            text: User message text (legacy parameter name)
            
        Returns:
            ChatResponse with ResponseEnvelope
        """
        # Handle both calling conventions
        if isinstance(message, ChatMessage):
            # New convention: direct ChatMessage object
            chat_msg = message
            required_fields = ['message_id', 'user_id', 'session_id', 'text', 'timestamp']
            for field in required_fields:
                if not hasattr(chat_msg, field):
                    raise ValueError(f"ChatMessage missing required field: {field}")
                if getattr(chat_msg, field) is None:
                    raise ValueError(f"ChatMessage field '{field}' cannot be None")
            message_id = chat_msg.message_id
            text = chat_msg.text
            context = chat_msg.context
            user_id = chat_msg.user_id
        else:
            # Legacy convention: text + optional params
            # 'message' might be text if first positional arg
            if message is not None and isinstance(message, str):
                text = message
            elif text is None:
                raise ValueError("Must provide either ChatMessage object or text string")
            
            # Generate message_id if not provided
            if not message_id:
                message_id = f"msg_{uuid4().hex[:12]}"
            
            user_id = self.user_id
        
        self.message_count += 1
        
        # Step 2: Log chat_received
        logger.info(
            f"[CHAT_RECEIVED] message_id={message_id}, "
            f"user_id={user_id}, text='{text[:50]}...'"
        )
        
        # Step 3: Call InteractionOrchestrator with trace_id
        logger.debug(
            f"[ORCHESTRATE] Calling orchestrator for message {message_id}"
        )
        
        # Extract trace_id from ChatMessage if available
        trace_id = getattr(chat_msg, 'trace_id', None) if isinstance(message, ChatMessage) else None
        
        envelope = orchestrate_message(
            message=text,
            session_id=self.session_id,
            user_id=self.user_id,
            context=context,
            trace_id=trace_id
        )

        # Phase 12.3: Attach build review summaries (read-only)
        try:
            review_registry = BuildReviewRegistry()
            summaries = review_registry.get_latest_reviews_summary()
            if summaries:
                envelope.metadata["build_reviews_summary"] = summaries
        except Exception:
            # Read-only enrichment should not break chat flow
            pass

        # Phase 12.6: Attach economic scenario summary (simulation only)
        try:
            scenario_registry = EconomicScenarioRegistry()
            scenarios = scenario_registry.list_all()
            if scenarios:
                envelope.metadata["economic_scenarios_summary"] = {
                    "label": "SIMULATION - NO MONEY MOVED",
                    "count": len(scenarios),
                    "latest": [s.to_dict() for s in scenarios[-5:]],
                }
        except Exception:
            pass
        
        # Step 4: Package response
        response_id = f"resp_{uuid4().hex[:12]}"
        trace_id = getattr(chat_msg, 'trace_id', None) if isinstance(message, ChatMessage) else None
        response = ChatResponse(
            response_id=response_id,
            message_id=message_id,
            session_id=self.session_id,
            trace_id=trace_id or f"trace_{uuid4().hex[:12]}",
            envelope=envelope,
            timestamp=datetime.utcnow().isoformat()
        )
        
        # Step 5: Log response_generated
        logger.info(
            f"[RESPONSE_GENERATED] response_id={response_id}, "
            f"message_id={message_id}, "
            f"type={envelope.response_type.value}"
        )
        
        # Step 6: Log mission_spawned (if applicable)
        if len(envelope.missions_spawned) > 0:
            for mission in envelope.missions_spawned:
                self.mission_count += 1
                logger.info(
                    f"[MISSION_SPAWNED] mission_id={mission.mission_id}, "
                    f"status={mission.status}, "
                    f"objective={mission.objective_type}"
                )
                logger.debug(
                    f"[MISSION_DETAILS] mission_id={mission.mission_id}, "
                    f"description={mission.objective_description}"
                )
        
        # Step 7: Log signals_emitted (if any)
        if len(envelope.signals_emitted) > 0:
            logger.debug(
                f"[SIGNALS_EMITTED] count={len(envelope.signals_emitted)}"
            )
            for signal in envelope.signals_emitted:
                logger.debug(
                    f"[SIGNAL] type={signal.signal_type}, "
                    f"layer={signal.signal_layer}, "
                    f"source={signal.signal_source}"
                )
        
        return response
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics."""
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'created_at': self.created_at,
            'message_count': self.message_count,
            'mission_count': self.mission_count,
            'uptime_seconds': (
                datetime.utcnow() - 
                datetime.fromisoformat(self.created_at)
            ).total_seconds()
        }
    
    def __repr__(self) -> str:
        stats = self.get_session_stats()
        return (
            f"ChatSessionHandler(session_id={stats['session_id']}, "
            f"messages={stats['message_count']}, "
            f"missions={stats['mission_count']})"
        )


class ChatSessionManager:
    """
    Manages multiple chat sessions.
    
    Tracks active sessions and provides session-level operations.
    """
    
    def __init__(self):
        """Initialize session manager."""
        self.sessions: Dict[str, ChatSessionHandler] = {}
        self.created_at = datetime.utcnow().isoformat()
        
        logger.info("[SESSION_MANAGER] Initialized")
    
    def get_or_create_session(
        self,
        session_id: str,
        user_id: str = "default"
    ) -> ChatSessionHandler:
        """
        Get existing session or create new one.
        
        Args:
            session_id: Session identifier
            user_id: User identifier
            
        Returns:
            ChatSessionHandler (existing or new)
        """
        if session_id not in self.sessions:
            self.sessions[session_id] = ChatSessionHandler(session_id, user_id)
            logger.info(
                f"[SESSION_CREATED] session_id={session_id}, "
                f"user_id={user_id}"
            )
            
            # Also create in ConversationStore for Firebase persistence
            try:
                from backend.conversation.session_store import get_conversation_store
                store = get_conversation_store()
                store.get_or_create(session_id, source='chat_ui', external_user_id=user_id)
                logger.info(f"[SESSION_SYNC] Successfully synced session {session_id} to ConversationStore")
            except Exception as e:
                logger.error(f"[SESSION_SYNC_ERROR] Failed to sync session to ConversationStore: {e}", exc_info=True)
        
        return self.sessions[session_id]
    
    def handle_message(
        self,
        session_id: str,
        text: str,
        user_id: str = "default",
        context: Optional[Dict[str, Any]] = None,
        message_id: Optional[str] = None
    ) -> ChatResponse:
        """
        Handle message in a session (get/create session first).
        
        Args:
            session_id: Session identifier
            text: User message
            user_id: User identifier (used if session doesn't exist)
            context: Optional context
            message_id: Optional message ID
            
        Returns:
            ChatResponse
        """
        session = self.get_or_create_session(session_id, user_id)
        chat_response = session.handle_message(text, context, message_id)
        
        # Sync messages to ConversationStore for Firebase persistence
        try:
            from backend.conversation.session_store import get_conversation_store
            store = get_conversation_store()
            # Add user message to ConversationStore
            store.append_message(session_id, 'user', text, 'chat_ui')
            logger.info(f"[MESSAGE_SYNC] Added user message to session {session_id}")
            # Add assistant response to ConversationStore
            if chat_response and chat_response.envelope and chat_response.envelope.summary:
                store.append_message(session_id, 'assistant', chat_response.envelope.summary, 'chat_ui')
                logger.info(f"[MESSAGE_SYNC] Added assistant message to session {session_id}")
        except Exception as e:
            logger.error(f"[MESSAGE_SYNC_ERROR] Failed to sync messages to ConversationStore: {e}", exc_info=True)
        
        return chat_response
    
    def get_session_stats(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a session."""
        if session_id in self.sessions:
            return self.sessions[session_id].get_session_stats()
        return None
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Get statistics for all sessions."""
        return {
            'manager_created_at': self.created_at,
            'total_sessions': len(self.sessions),
            'sessions': {
                sid: handler.get_session_stats()
                for sid, handler in self.sessions.items()
            }
        }


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

# Global session manager instance
_session_manager = ChatSessionManager()


def handle_chat_message(
    session_id: str,
    text: str,
    user_id: str = "default",
    context: Optional[Dict[str, Any]] = None,
    message_id: Optional[str] = None
) -> ChatResponse:
    """
    Convenience function to handle a chat message.
    
    Args:
        session_id: Session identifier
        text: User message
        user_id: User identifier
        context: Optional context
        message_id: Optional message ID
        
    Returns:
        ChatResponse
    """
    return _session_manager.handle_message(
        session_id, text, user_id, context, message_id
    )


def get_session_stats(session_id: str) -> Optional[Dict[str, Any]]:
    """Get statistics for a session."""
    return _session_manager.get_session_stats(session_id)


def get_all_stats() -> Dict[str, Any]:
    """Get statistics for all sessions."""
    return _session_manager.get_all_stats()
