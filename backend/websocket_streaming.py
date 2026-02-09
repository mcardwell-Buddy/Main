"""
WebSocket Streaming Endpoint
Real-time event stream for mission execution observability
Observability-only: NO control commands, NO autonomy
"""

from typing import Dict, List, Set
import asyncio
import json
from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from contextlib import asynccontextmanager

from backend.streaming_events import (
    StreamingEvent,
    StreamingEventEmitter,
    get_event_emitter,
)


class WebSocketStreamManager:
    """Manages WebSocket connections for mission event streaming"""
    
    def __init__(self):
        """Initialize stream manager"""
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.emitter = get_event_emitter()
    
    async def connect(self, mission_id: str, websocket: WebSocket) -> None:
        """Accept and track a WebSocket connection for a mission"""
        await websocket.accept()
        
        if mission_id not in self.active_connections:
            self.active_connections[mission_id] = set()
        
        self.active_connections[mission_id].add(websocket)
        
        # Subscribe to events for this mission
        self.emitter.subscribe(
            mission_id,
            lambda event: asyncio.create_task(
                self._broadcast_to_websocket(websocket, event)
            ),
        )
    
    async def disconnect(self, mission_id: str, websocket: WebSocket) -> None:
        """Remove a WebSocket connection"""
        if mission_id in self.active_connections:
            self.active_connections[mission_id].discard(websocket)
            if not self.active_connections[mission_id]:
                del self.active_connections[mission_id]
    
    async def _broadcast_to_websocket(
        self,
        websocket: WebSocket,
        event: StreamingEvent,
    ) -> None:
        """Send event to a single WebSocket client"""
        try:
            print(f"[WebSocket] Sending {event.event_type} event to client")
            await websocket.send_text(event.to_json())
        except Exception as e:
            print(f"[WebSocket] Error sending event: {type(e).__name__}: {e}")
    
    async def broadcast_to_mission(
        self,
        mission_id: str,
        event: StreamingEvent,
    ) -> None:
        """Broadcast event to all WebSocket clients for a mission"""
        if mission_id in self.active_connections:
            for websocket in list(self.active_connections[mission_id]):
                try:
                    await websocket.send_text(event.to_json())
                except Exception as e:
                    print(f"Error broadcasting to mission {mission_id}: {e}")


# Global stream manager
_stream_manager: WebSocketStreamManager = WebSocketStreamManager()


def get_stream_manager() -> WebSocketStreamManager:
    """Get the global WebSocket stream manager"""
    return _stream_manager


# FastAPI router for WebSocket endpoints
router = APIRouter()


@router.websocket("/ws/stream/{mission_id}")
async def websocket_stream_endpoint(mission_id: str, websocket: WebSocket):
    """
    WebSocket endpoint for real-time mission execution events
    
    Connection URL: ws://localhost:8000/ws/stream/{mission_id}
    
    Message Format (server → client):
    ```json
    {
        "mission_id": "mission-abc123",
        "event_type": "selector_attempt",
        "timestamp": "2026-02-07T15:30:45.123456",
        "sequence_number": 5,
        "data": {
            "selector_id": "selector-1",
            "selector_description": "Click on product name",
            "status": "success",
            "details": {...}
        }
    }
    ```
    
    Observability-only:
    - Client RECEIVES events only
    - Client CANNOT send commands
    - Stream is READ-ONLY
    """
    stream_manager = get_stream_manager()
    print(f"[WebSocket] New connection attempt for mission {mission_id}")
    await stream_manager.connect(mission_id, websocket)
    print(f"[WebSocket] Connection accepted for mission {mission_id}")
    
    try:
        # Keep connection open and listening for client disconnect
        # Use a long timeout to allow events to be sent to client without waiting for client input
        while True:
            try:
                # Use timeout to periodically check if client disconnected
                # During timeout, the connection stays open and events can be sent to client
                await asyncio.wait_for(websocket.receive_text(), timeout=60.0)
                # If we get here, client sent something - we ignore it per spec
                print(f"[WebSocket] {mission_id} - Ignoring client message (observability only)")
            except asyncio.TimeoutError:
                # This is normal - just means no message from client for 60 seconds
                # Connection stays open, events can still be sent
                continue
    
    except WebSocketDisconnect:
        print(f"[WebSocket] Client disconnected for mission {mission_id}")
        await stream_manager.disconnect(mission_id, websocket)
    except Exception as e:
        print(f"[WebSocket] Error for mission {mission_id}: {type(e).__name__}: {e}")
        await stream_manager.disconnect(mission_id, websocket)


@router.get("/api/stream-health/{mission_id}")
async def stream_health(mission_id: str) -> Dict:
    """
    Health check for a mission's event stream
    
    Response:
    ```json
    {
        "mission_id": "mission-abc123",
        "active_connections": 2,
        "status": "active",
        "observation_mode": "read-only",
        "control_enabled": false
    }
    ```
    """
    stream_manager = get_stream_manager()
    active_count = len(
        stream_manager.active_connections.get(mission_id, set())
    )
    
    return {
        "mission_id": mission_id,
        "active_connections": active_count,
        "status": "active" if active_count > 0 else "idle",
        "observation_mode": "read-only",
        "control_enabled": False,  # Explicitly false - observability only
    }


# ============================================================================
# Example Usage / Integration Patterns
# ============================================================================

"""
EXAMPLE 1: Emit events during mission execution
================================================================

from backend.streaming_events import (
    get_event_emitter,
    MissionStatus,
    SelectorAttemptStatus,
    IntentDecisionType,
)

emitter = get_event_emitter()

# Mission starts
emitter.emit_mission_start(
    mission_id="mission-abc123",
    objective="Extract competitor pricing"
)

# Status changes during execution
emitter.emit_mission_status_change(
    mission_id="mission-abc123",
    old_status=MissionStatus.QUEUED,
    new_status=MissionStatus.STARTED,
    reason="Execution started"
)

# Selector attempt (observability only)
emitter.emit_selector_attempt(
    mission_id="mission-abc123",
    selector_id="selector-prod-name",
    selector_description="Find product name on page",
    status=SelectorAttemptStatus.SUCCESS,
    details={"found": True, "element_count": 1}
)

# Intent decision (observability only)
emitter.emit_intent_decision(
    mission_id="mission-abc123",
    intent_type=IntentDecisionType.EXTRACT,
    reasoning="Product data found, extracting values",
    parameters={"field": "price", "format": "USD"},
    confidence=0.95
)

# Progress updates
emitter.emit_mission_progress(
    mission_id="mission-abc123",
    progress_percent=50,
    current_step="Extracting pricing data"
)

# Mission completes
emitter.emit_mission_stop(
    mission_id="mission-abc123",
    reason="Completed successfully",
    final_status=MissionStatus.COMPLETED
)


EXAMPLE 2: Client-side WebSocket consumption
================================================================

JavaScript / TypeScript:

const missionId = "mission-abc123";
const ws = new WebSocket(`ws://localhost:8000/ws/stream/${missionId}`);

// Connection established
ws.onopen = () => {
    console.log(`Connected to stream for ${missionId}`);
};

// Receive events
ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    
    // Handle based on event type
    switch (message.event_type) {
        case "mission_start":
            console.log(`Mission started: ${message.data.objective}`);
            break;
        
        case "selector_attempt":
            console.log(
                `Selector attempt [${message.data.selector_id}]: ` +
                `${message.data.status}`
            );
            break;
        
        case "intent_decision":
            console.log(
                `Intent decided: ${message.data.intent_type} ` +
                `(confidence: ${message.data.confidence})`
            );
            break;
        
        case "mission_progress":
            console.log(
                `Progress: ${message.data.progress_percent}% ` +
                `(${message.data.current_step})`
            );
            break;
        
        case "mission_stop":
            console.log(
                `Mission stopped: ${message.data.final_status} ` +
                `(${message.data.reason})`
            );
            break;
    }
};

// Error handling
ws.onerror = (error) => {
    console.error(`WebSocket error: ${error}`);
};

// Disconnection
ws.onclose = () => {
    console.log("Disconnected from stream");
};

// NOTE: Attempting to send commands will be ignored
// (observability-only - no control)
// ws.send(JSON.stringify({command: "pause"})); // ← IGNORED
// ws.send(JSON.stringify({command: "resume"})); // ← IGNORED


EXAMPLE 3: Real-time UI update with event stream
================================================================

Python - Update UI based on streaming events:

async def handle_mission_stream(mission_id: str):
    emitter = get_event_emitter()
    
    def on_event(event: StreamingEvent):
        # Update UI based on event
        update_ui_status(
            mission_id=mission_id,
            event_type=event.event_type.value,
            data=event.data,
            timestamp=event.timestamp
        )
    
    # Subscribe to all events for this mission
    emitter.subscribe(mission_id, on_event)
    
    # Keep alive while mission is running
    await mission_execution_loop(mission_id)
    
    # Unsubscribe when done
    emitter.unsubscribe(mission_id, on_event)


EXAMPLE 4: Event aggregation for live dashboard
================================================================

Pseudo-code for live dashboard:

dashboard_state = {
    "missions": {
        "mission-abc123": {
            "objective": "Extract competitor pricing",
            "status": "in_progress",
            "progress": 50,
            "current_step": "Extracting pricing data",
            "selector_attempts": 12,
            "selector_success_rate": 0.92,
            "intent_decisions": [
                {type: "navigate", confidence: 0.98},
                {type: "extract", confidence: 0.95},
            ],
            "timeline": [
                {seq: 1, event: "mission_start", time: "15:30:45"},
                {seq: 2, event: "selector_attempt", status: "success"},
                {seq: 3, event: "intent_decision", type: "navigate"},
                ...
            ]
        }
    }
}

When event received:
    switch event.type:
        "mission_progress":
            dashboard_state[mission_id].progress = event.data.progress_percent
            dashboard_state[mission_id].current_step = event.data.current_step
            update_ui()
        
        "selector_attempt":
            dashboard_state[mission_id].selector_attempts += 1
            if event.data.status == "success":
                success_count += 1
            dashboard_state[mission_id].selector_success_rate = (
                success_count / dashboard_state[mission_id].selector_attempts
            )
            update_ui()
        
        "intent_decision":
            dashboard_state[mission_id].intent_decisions.append({
                type: event.data.intent_type,
                confidence: event.data.confidence
            })
            update_ui()
        
        "mission_stop":
            dashboard_state[mission_id].status = event.data.final_status
            update_ui()
            close_stream()


EXAMPLE 5: Multi-mission monitoring
================================================================

# Monitor multiple missions with separate streams

missions = ["mission-1", "mission-2", "mission-3"]

async def monitor_missions():
    tasks = [
        asyncio.create_task(connect_and_monitor(mission_id))
        for mission_id in missions
    ]
    await asyncio.gather(*tasks)

async def connect_and_monitor(mission_id: str):
    ws = create_websocket_connection(
        f"ws://localhost:8000/ws/stream/{mission_id}"
    )
    
    async for event in ws:
        # Each mission has independent stream
        # No cross-mission control possible
        # Each event tagged with mission_id for routing
        aggregate_metrics(mission_id, event)
        update_dashboard(mission_id, event)
"""
