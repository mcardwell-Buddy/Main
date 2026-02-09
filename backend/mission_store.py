"""Mission store with Firebase-only persistence.

Replaces outputs/phase25/missions.jsonl with Firebase collection 'missions'.
Single source of truth for all mission lifecycle events.
"""
from __future__ import annotations

import threading
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

# Firebase imports for persistence
try:
    from firebase_admin import firestore
    from backend.config import Config
    import firebase_admin
    from firebase_admin import credentials
    FIREBASE_AVAILABLE = Config.FIREBASE_ENABLED
except ImportError:
    FIREBASE_AVAILABLE = False
    logger.warning("Firebase not available - mission persistence disabled")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Mission:
    """Mission data model."""
    mission_id: str
    event_type: str  # 'mission_proposed', 'mission_approved', 'mission_executed', etc.
    status: str  # 'proposed', 'approved', 'completed', 'failed', etc.
    objective: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    scope: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=_now_iso)
    
    # Execution fields (populated after execution)
    tool_used: Optional[str] = None
    tool_confidence: Optional[float] = None
    intent: Optional[str] = None
    execution_result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Firebase storage."""
        data = {
            "mission_id": self.mission_id,
            "event_type": self.event_type,
            "status": self.status,
            "objective": self.objective,
            "metadata": self.metadata,
            "scope": self.scope,
            "timestamp": self.timestamp,
        }
        
        # Add execution fields if present
        if self.tool_used:
            data["tool_used"] = self.tool_used
        if self.tool_confidence is not None:
            data["tool_confidence"] = self.tool_confidence
        if self.intent:
            data["intent"] = self.intent
        if self.execution_result is not None:
            data["execution_result"] = self.execution_result
        if self.error:
            data["error"] = self.error
            
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Mission:
        """Create Mission from dictionary."""
        return cls(
            mission_id=data["mission_id"],
            event_type=data["event_type"],
            status=data["status"],
            objective=data.get("objective", {}),
            metadata=data.get("metadata", {}),
            scope=data.get("scope", {}),
            timestamp=data.get("timestamp", _now_iso()),
            tool_used=data.get("tool_used"),
            tool_confidence=data.get("tool_confidence"),
            intent=data.get("intent"),
            execution_result=data.get("execution_result"),
            error=data.get("error"),
        )


class MissionStore:
    """Thread-safe store for missions with Firebase-only persistence.
    
    Replaces local .jsonl files with Firebase collection 'missions'.
    Each mission can have multiple events (proposed → approved → executed).
    Events are stored as subcollection under mission_id document.
    """

    def __init__(self) -> None:
        self._missions: Dict[str, List[Mission]] = {}  # mission_id → list of events
        self._lock = threading.RLock()
        
        # Initialize Firebase client
        self._firebase_enabled = FIREBASE_AVAILABLE
        self._db = None
        if self._firebase_enabled:
            try:
                # Initialize firebase_admin if not already initialized
                if not firebase_admin._apps:
                    cred_path = Config.FIREBASE_CREDENTIALS_PATH
                    if cred_path:
                        cred = credentials.Certificate(cred_path)
                        firebase_admin.initialize_app(cred)
                    else:
                        raise RuntimeError("FIREBASE_CREDENTIALS_PATH not set")
                
                self._db = firestore.client()
                self._collection = self._db.collection('missions')
                self._load_from_firebase()
                logger.info("MissionStore initialized with Firebase persistence")
            except Exception as e:
                logger.error(f"Failed to initialize Firebase for missions: {e}")
                self._firebase_enabled = False
        else:
            logger.warning("MissionStore initialized WITHOUT Firebase persistence")
    
    def _load_from_firebase(self) -> None:
        """Load all existing missions from Firebase on startup."""
        if not self._firebase_enabled or not self._db:
            return
        
        try:
            # Load all mission documents
            docs = self._collection.stream()
            loaded_count = 0
            for doc in docs:
                mission_id = doc.id
                # Load events subcollection
                events_ref = self._collection.document(mission_id).collection('events')
                events_docs = events_ref.order_by('timestamp').stream()
                
                events = []
                for event_doc in events_docs:
                    event_data = event_doc.to_dict()
                    event_data['mission_id'] = mission_id  # Ensure mission_id is set
                    mission = Mission.from_dict(event_data)
                    events.append(mission)
                
                if events:
                    self._missions[mission_id] = events
                    loaded_count += 1
            
            logger.info(f"Loaded {loaded_count} missions from Firebase")
        except Exception as e:
            logger.error(f"Failed to load missions from Firebase: {e}")
    
    def _save_to_firebase(self, mission: Mission) -> None:
        """Save a mission event to Firebase."""
        if not self._firebase_enabled or not self._db:
            logger.warning(f"Firebase disabled - mission {mission.mission_id} NOT persisted")
            return
        
        try:
            # Store event in subcollection: missions/{mission_id}/events/{event_id}
            event_id = f"{mission.event_type}_{mission.timestamp}"
            event_ref = self._collection.document(mission.mission_id).collection('events').document(event_id)
            event_ref.set(mission.to_dict())
            
            # Also update the parent document with current status
            mission_ref = self._collection.document(mission.mission_id)
            mission_ref.set({
                'mission_id': mission.mission_id,
                'current_status': mission.status,
                'last_updated': mission.timestamp,
                'event_type': mission.event_type,
            }, merge=True)
            
            logger.debug(f"Saved mission {mission.mission_id} event to Firebase: {mission.event_type}")
        except Exception as e:
            logger.error(f"Failed to save mission {mission.mission_id} to Firebase: {e}")
    
    def write_mission_event(self, mission: Mission) -> None:
        """Write a mission event (proposed, approved, executed, etc.)."""
        with self._lock:
            if mission.mission_id not in self._missions:
                self._missions[mission.mission_id] = []
            
            self._missions[mission.mission_id].append(mission)
            self._save_to_firebase(mission)
            logger.info(f"Mission event written: {mission.mission_id} → {mission.event_type} → {mission.status}")
    
    def get_mission_events(self, mission_id: str) -> List[Mission]:
        """Get all events for a mission."""
        with self._lock:
            return self._missions.get(mission_id, [])
    
    def get_current_status(self, mission_id: str) -> Optional[str]:
        """Get current status of a mission (most recent event)."""
        with self._lock:
            events = self._missions.get(mission_id, [])
            if not events:
                return None
            return events[-1].status
    
    def find_mission(self, mission_id: str) -> Optional[Mission]:
        """Find most recent event for a mission."""
        with self._lock:
            events = self._missions.get(mission_id, [])
            if not events:
                return None
            return events[-1]
    
    def count_execution_records(self, mission_id: str) -> int:
        """Count how many times a mission has been executed."""
        with self._lock:
            events = self._missions.get(mission_id, [])
            return sum(1 for e in events if e.event_type == 'mission_executed')
    
    def list_missions(
        self,
        status: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Mission]:
        """List missions, optionally filtered by status."""
        with self._lock:
            # Get most recent event for each mission
            missions = []
            for mission_id, events in self._missions.items():
                if events:
                    latest = events[-1]
                    if status is None or latest.status == status:
                        missions.append(latest)
            
            # Sort by timestamp descending (most recent first)
            missions.sort(key=lambda m: m.timestamp, reverse=True)
            
            if limit:
                missions = missions[:limit]
            
            return missions
    
    def get_all_events(self) -> List[Mission]:
        """Get all mission events across all missions (for migration/debugging)."""
        with self._lock:
            all_events = []
            for events in self._missions.values():
                all_events.extend(events)
            return sorted(all_events, key=lambda e: e.timestamp)


# Singleton instance
_store: Optional[MissionStore] = None


def get_mission_store() -> MissionStore:
    """Get singleton MissionStore instance."""
    global _store
    if _store is None:
        _store = MissionStore()
    return _store
