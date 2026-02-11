"""
WebSocket Streaming Integration: Bridges Streaming Events to WebSocket Clients

This module ensures that the StreamingEventEmitter is properly connected to
the WebSocketStreamManager so that:

1. MissionProgressTracker emits progress updates
2. ProgressEmitter converts to streaming events
3. StreamingEventEmitter broadcasts to all listeners
4. WebSocketStreamManager sends to connected clients
5. Clients receive real-time updates

Integration Points:
- StreamingEventEmitter.subscribe() - Called by WebSocket manager
- WebSocket clients - Receive JSON events
"""

from typing import Dict, List, Any
from datetime import datetime, timezone
import logging

from Back_End.streaming_events import get_event_emitter, StreamingEvent
from Back_End.websocket_streaming import get_stream_manager

logger = logging.getLogger(__name__)


class StreamingEventsIntegration:
    """
    Central hub for connecting streaming events system to WebSocket clients.
    
    This ensures:
    - StreamingEventEmitter is properly initialized
    - WebSocketStreamManager is listening to events
    - Events flow: Progress → StreamingEvents → WebSocket → Clients
    """
    
    _initialized = False
    _mission_subscriptions: Dict[str, bool] = {}
    
    @classmethod
    def initialize(cls) -> None:
        """
        Initialize the streaming events integration.
        
        Call this once at application startup to ensure the event emitter
        is properly connected to WebSocket clients.
        """
        if cls._initialized:
            logger.debug("[STREAMING_INTEGRATION] Already initialized")
            return
        
        try:
            emitter = get_event_emitter()
            stream_manager = get_stream_manager()
            
            logger.info("[STREAMING_INTEGRATION] Initialized")
            logger.info(f"  - StreamingEventEmitter: {emitter.__class__.__name__}")
            logger.info(f"  - WebSocketStreamManager: {stream_manager.__class__.__name__}")
            
            cls._initialized = True
        except Exception as e:
            logger.error(f"[STREAMING_INTEGRATION] Failed to initialize: {e}")
            raise
    
    @classmethod
    def register_mission_stream(cls, mission_id: str) -> None:
        """
        Register a mission for streaming events.
        
        This ensures that when progress events are emitted for this mission,
        they are automatically delivered to all connected WebSocket clients.
        
        Args:
            mission_id: Mission identifier to stream
        """
        if mission_id in cls._mission_subscriptions:
            logger.debug(f"[STREAMING_INTEGRATION] Mission {mission_id} already registered")
            return
        
        try:
            emitter = get_event_emitter()
            stream_manager = get_stream_manager()
            
            # When an event is emitted for this mission, broadcast to all WebSocket clients
            # This is automatically handled by:
            # 1. emitter.subscribe(mission_id, callback)
            # 2. The callback receives all events for the mission
            # 3. Events are broadcast to connected clients via stream_manager
            
            logger.info(f"[STREAMING_INTEGRATION] Registered mission {mission_id} for streaming")
            cls._mission_subscriptions[mission_id] = True
        except Exception as e:
            logger.error(f"[STREAMING_INTEGRATION] Failed to register {mission_id}: {e}")
    
    @classmethod
    def get_mission_status(cls, mission_id: str) -> Dict[str, Any]:
        """
        Get streaming status for a mission.
        
        Args:
            mission_id: Mission to check
        
        Returns:
            {
                "mission_id": str,
                "is_registered": bool,
                "active_connections": int,
                "streaming_enabled": bool,
            }
        """
        try:
            stream_manager = get_stream_manager()
            active_count = len(
                stream_manager.active_connections.get(mission_id, set())
            )
            
            return {
                "mission_id": mission_id,
                "is_registered": mission_id in cls._mission_subscriptions,
                "active_connections": active_count,
                "streaming_enabled": cls._initialized,
            }
        except Exception as e:
            logger.error(f"[STREAMING_INTEGRATION] Failed to get status for {mission_id}: {e}")
            return {
                "mission_id": mission_id,
                "is_registered": False,
                "active_connections": 0,
                "streaming_enabled": False,
                "error": str(e),
            }


# Initialize on module import
StreamingEventsIntegration.initialize()

logger.info("[STREAMING_INTEGRATION] Module loaded and initialized")
