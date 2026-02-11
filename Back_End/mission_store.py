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
    from Back_End.config import Config
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
    
    def save_progress(self, mission_id: str, progress_tracker: Dict[str, Any]) -> None:
        """
        Save mission progress to Firestore for persistence.
        
        Writes to: missions/{mission_id}/execution_record/progress_tracker
        """
        if not self._firebase_enabled or not self._db:
            logger.warning(f"Firebase disabled - progress for {mission_id} NOT persisted")
            return
        
        try:
            doc = self._collection.document(mission_id)
            
            # Update execution_record with progress data
            doc.update({
                'execution_record.progress_tracker': progress_tracker,
                'execution_record.progress_updated_at': datetime.now(timezone.utc).isoformat()
            })
            
            current_step = progress_tracker.get('current_step', {})
            step_name = current_step.get('step_name') if current_step else 'Complete'
            logger.info(f"[MISSION_STORE] Saved progress for {mission_id}: {step_name}")
        except Exception as e:
            logger.error(f"[MISSION_STORE] Failed to save progress: {e}")
    
    def get_mission_progress(self, mission_id: str) -> Dict[str, Any]:
        """
        Retrieve mission progress from Firestore.
        
        Returns:
        {
            mission_id: str,
            current_step: ExecutionStep | None,
            completed_steps: [ExecutionStep, ...],
            progress_percent: 0-100,
            elapsed_seconds: float,
            estimated_time_remaining: float,
            status: 'in_progress' | 'completed' | 'failed'
        }
        """
        if not self._firebase_enabled or not self._db:
            logger.warning(f"Firebase disabled - cannot retrieve progress for {mission_id}")
            return {'error': 'Firebase not available'}
        
        try:
            doc = self._collection.document(mission_id).get()
            
            if not doc.exists:
                return {'error': f'Mission {mission_id} not found'}
            
            mission_data = doc.to_dict()
            execution_record = mission_data.get('execution_record', {})
            progress_tracker = execution_record.get('progress_tracker', {})
            
            # Calculate ETA from progression rate
            eta = self._calculate_eta(progress_tracker)
            
            return {
                'mission_id': mission_id,
                'current_step': progress_tracker.get('current_step'),
                'completed_steps': progress_tracker.get('completed_steps', []),
                'progress_percent': progress_tracker.get('progress_percent', 0),
                'elapsed_seconds': progress_tracker.get('elapsed_seconds', 0),
                'estimated_time_remaining': eta,
                'status': self._get_status_from_progress(progress_tracker)
            }
        except Exception as e:
            logger.error(f"[MISSION_STORE] Failed to get progress: {e}")
            return {'error': str(e)}
    
    def _calculate_eta(self, progress_tracker: Dict[str, Any]) -> float:
        """
        Calculate estimated time remaining based on progression rate.
        
        Formula:
        - Rate: percentage completed per second
        - ETA = (percent_remaining / rate)
        
        Returns: float (seconds)
        """
        try:
            current_percent = progress_tracker.get('progress_percent', 0)
            elapsed_seconds = progress_tracker.get('elapsed_seconds', 1)
            
            if current_percent >= 100:
                return 0.0
            
            if current_percent <= 0:
                return 15.0  # Default estimate for just-started missions
            
            # Prevent division by zero
            elapsed_seconds = max(elapsed_seconds, 0.1)
            
            # Rate: percentage completed per second
            rate = current_percent / elapsed_seconds
            
            if rate <= 0:
                return 15.0  # Fallback if no progress
            
            # Time remaining to reach 100%
            percent_remaining = 100 - current_percent
            eta_seconds = percent_remaining / rate
            
            # Cap at 60 seconds max (missions shouldn't take >1min typically)
            return min(eta_seconds, 60.0)
        except Exception as e:
            logger.warning(f"[ETA_CALC] Failed to calculate ETA: {e}")
            return 15.0  # Fallback estimate
    
    def _get_status_from_progress(self, progress_tracker: Dict[str, Any]) -> str:
        """Determine mission status from progress data."""
        try:
            current_step = progress_tracker.get('current_step')
            
            if current_step and current_step.get('status') == 'failed':
                return 'failed'
            
            if progress_tracker.get('progress_percent', 0) >= 100:
                return 'completed'
            
            if current_step:
                return 'in_progress'
            
            return 'unknown'
        except Exception as e:
            logger.warning(f"[STATUS] Failed to get status: {e}")
            return 'unknown'
    
    def save_mission_update(self, update: Any) -> None:
        """
        Save mission update/clarification to Firestore.
        
        Writes to: missions/{mission_id}/updates/{update_id}
        """
        if not self._firebase_enabled or not self._db:
            logger.warning(f"Firebase disabled - update for {update.mission_id} NOT persisted")
            return
        
        try:
            mission_id = update.mission_id
            update_id = f"{update.update_type}_{update.timestamp}"
            
            updates_ref = self._collection.document(mission_id).collection('updates').document(update_id)
            updates_ref.set(update.to_dict())
            
            # Update parent document with update count
            mission_ref = self._collection.document(mission_id)
            mission_ref.set({
                'mission_id': mission_id,
                'last_update_at': update.timestamp,
            }, merge=True)
            
            logger.info(f"[MISSION_STORE] Saved update for {mission_id}: {update.update_type}")
        except Exception as e:
            logger.error(f"[MISSION_STORE] Failed to save update: {e}")
    
    def get_mission_updates(self, mission_id: str) -> List[Any]:
        """
        Retrieve all updates for a mission.
        
        Returns:
            List of MissionUpdate objects
        """
        if not self._firebase_enabled or not self._db:
            logger.warning(f"Firebase disabled - cannot retrieve updates for {mission_id}")
            return []
        
        try:
            from Back_End.mission_updater import MissionUpdate
            
            updates_ref = self._collection.document(mission_id).collection('updates')
            updates_docs = updates_ref.order_by('timestamp').stream()
            
            updates = []
            for doc in updates_docs:
                update_data = doc.to_dict()
                # Reconstruct MissionUpdate object
                update = MissionUpdate(
                    mission_id=update_data['mission_id'],
                    update_type=update_data['update_type'],
                    update_data=update_data['update_data'],
                    reason=update_data.get('reason')
                )
                update.timestamp = update_data['timestamp']  # Restore original timestamp
                updates.append(update)
            
            logger.debug(f"[MISSION_STORE] Retrieved {len(updates)} updates for {mission_id}")
            return updates
        except Exception as e:
            logger.error(f"[MISSION_STORE] Failed to get updates: {e}")
            return []
    
    def save_mission_feedback(self, feedback: Any) -> None:
        """
        Save mission feedback to Firestore.
        
        PHASE 3: Tracks outcomes for tool selection learning
        
        Writes to: missions/{mission_id}/feedback/{mission_id}
        """
        if not self._firebase_enabled or not self._db:
            logger.warning(f"Firebase disabled - feedback for {feedback.mission_id} NOT persisted")
            return
        
        try:
            mission_id = feedback.mission_id
            
            feedback_ref = self._collection.document(mission_id).collection('feedback').document(mission_id)
            feedback_ref.set(feedback.to_dict())
            
            # Update parent document
            mission_ref = self._collection.document(mission_id)
            mission_ref.set({
                'mission_id': mission_id,
                'feedback_recorded': True,
                'feedback_timestamp': feedback.timestamp
            }, merge=True)
            
            logger.info(f"[MISSION_STORE] Saved feedback for {mission_id}: {feedback.tool_used}")
        except Exception as e:
            logger.error(f"[MISSION_STORE] Failed to save feedback: {e}")
    
    def get_mission_feedbacks(
        self,
        tool: Optional[str] = None,
        mission_type: Optional[str] = None,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Retrieve mission feedbacks matching criteria.
        
        PHASE 3: For tool selection learning.
        
        Args:
            tool: Filter by tool name (optional)
            mission_type: Filter by mission type (optional)
            days: Only return feedback from last N days
        
        Returns:
            List of feedback dictionaries
        """
        if not self._firebase_enabled or not self._db:
            logger.warning("Firebase disabled - cannot retrieve feedbacks")
            return []
        
        try:
            from datetime import timedelta
            
            cutoff_time = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
            feedbacks = []
            
            # Query all missions for feedback documents
            missions_ref = self._collection.stream()
            
            for mission_doc in missions_ref:
                mission_id = mission_doc.id
                feedback_ref = self._collection.document(mission_id).collection('feedback')
                
                # Query feedback documents
                query = feedback_ref.where('timestamp', '>=', cutoff_time)
                
                for feedback_doc in query.stream():
                    feedback_data = feedback_doc.to_dict()
                    
                    # Apply filters
                    if tool and feedback_data.get('tool_used') != tool:
                        continue
                    if mission_type and feedback_data.get('mission_type') != mission_type:
                        continue
                    
                    feedbacks.append(feedback_data)
            
            logger.debug(f"[MISSION_STORE] Retrieved {len(feedbacks)} feedbacks")
            return feedbacks
        
        except Exception as e:
            logger.error(f"[MISSION_STORE] Failed to get feedbacks: {e}")
            return []
    
    def save_mission_survey(self, survey: Any) -> None:
        """
        Save mission completion survey to Firestore.
        
        PHASE 4: Tracks user satisfaction after mission completion
        
        Writes to: missions/{mission_id}/survey/{mission_id}
        """
        if not self._firebase_enabled or not self._db:
            logger.warning(f"Firebase disabled - survey for {survey.mission_id} NOT persisted")
            return
        
        try:
            mission_id = survey.mission_id
            
            survey_ref = self._collection.document(mission_id).collection('survey').document(mission_id)
            survey_ref.set(survey.to_dict())
            
            # Update parent document
            mission_ref = self._collection.document(mission_id)
            mission_ref.set({
                'mission_id': mission_id,
                'survey_completed': True,
                'survey_timestamp': survey.timestamp,
                'survey_score': survey.get_average_score()
            }, merge=True)
            
            logger.info(f"[MISSION_STORE] Saved survey for {mission_id}: score={survey.get_average_score():.1f}")
        except Exception as e:
            logger.error(f"[MISSION_STORE] Failed to save survey: {e}")
    
    def get_mission_survey(self, mission_id: str) -> Optional[Any]:
        """
        Retrieve mission survey response, if completed.
        
        Returns:
            MissionSurvey object, or None if not completed
        """
        if not self._firebase_enabled or not self._db:
            logger.warning(f"Firebase disabled - cannot retrieve survey for {mission_id}")
            return None
        
        try:
            from Back_End.survey_collector import MissionSurvey
            
            survey_ref = self._collection.document(mission_id).collection('survey').document(mission_id)
            doc = survey_ref.get()
            
            if not doc.exists:
                return None
            
            survey_data = doc.to_dict()
            
            survey = MissionSurvey(
                mission_id=survey_data['mission_id'],
                result_quality_score=survey_data['result_quality_score'],
                execution_speed_score=survey_data['execution_speed_score'],
                tool_appropriateness_score=survey_data['tool_appropriateness_score'],
                overall_satisfaction_score=survey_data['overall_satisfaction_score'],
                would_use_again=survey_data['would_use_again'],
                improvement_suggestions=survey_data.get('improvement_suggestions'),
                additional_notes=survey_data.get('additional_notes')
            )
            survey.timestamp = survey_data['timestamp']
            
            return survey
        except Exception as e:
            logger.error(f"[MISSION_STORE] Failed to get survey: {e}")
            return None
    
    def get_all_mission_surveys(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve all mission surveys for analytics.
        
        PHASE 4: For survey summary statistics
        
        Returns:
            List of survey response dictionaries
        """
        if not self._firebase_enabled or not self._db:
            logger.warning("Firebase disabled - cannot retrieve surveys")
            return []
        
        try:
            surveys = []
            missions_ref = self._collection.stream()
            
            for mission_doc in missions_ref:
                mission_id = mission_doc.id
                survey_ref = self._collection.document(mission_id).collection('survey').document(mission_id)
                doc = survey_ref.get()
                
                if doc.exists:
                    surveys.append(doc.to_dict())
                    if len(surveys) >= limit:
                        break
            
            logger.debug(f"[MISSION_STORE] Retrieved {len(surveys)} surveys")
            return surveys
        except Exception as e:
            logger.error(f"[MISSION_STORE] Failed to get surveys: {e}")
            return []
    
    def get_tool_costs(
        self,
        tool: str,
        mission_type: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Retrieve cost metrics for a tool across missions.
        
        PHASE 5: For investment/ROI calculations
        
        Args:
            tool: Tool name
            mission_type: Optional filter by mission type
            days: Only include data from last N days
        
        Returns:
        {
            'tool': 'web_search',
            'mission_type': 'tutorial_search',
            'total_cost': 15.50,
            'execution_count': 31,
            'avg_cost': 0.50,
            'avg_satisfaction': 4.2,
            'cost_distribution': [...percentiles...]
        }
        """
        if not self._firebase_enabled or not self._db:
            logger.warning(f"Firebase disabled - cannot retrieve costs for {tool}")
            return {'total_cost': 0, 'execution_count': 0, 'avg_cost': 0}
        
        try:
            from datetime import timedelta
            
            cutoff_time = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
            costs = []
            satisfactions = []
            
            # Query feedback documents for cost information
            missions_ref = self._collection.stream()
            
            for mission_doc in missions_ref:
                mission_id = mission_doc.id
                feedback_ref = self._collection.document(mission_id).collection('feedback').document(mission_id)
                doc = feedback_ref.get()
                
                if doc.exists:
                    doc_data = doc.to_dict()
                    
                    if doc_data.get('tool_used') != tool:
                        continue
                    if mission_type and doc_data.get('mission_type') != mission_type:
                        continue
                    if doc_data.get('timestamp', '') < cutoff_time:
                        continue
                    
                    # Note: For now, we estimate cost from execution time
                    # In real system, would pull from actual cost tracking
                    exec_time = doc_data.get('execution_time_seconds', 0)
                    estimated_cost = max(0.01, exec_time * 0.1)  # $0.10 per second estimate
                    
                    costs.append(estimated_cost)
                    if doc_data.get('user_satisfaction'):
                        satisfactions.append(doc_data['user_satisfaction'])
            
            if not costs:
                return {
                    'tool': tool,
                    'mission_type': mission_type or '_all',
                    'total_cost': 0,
                    'execution_count': 0,
                    'avg_cost': 0,
                    'avg_satisfaction': None
                }
            
            return {
                'tool': tool,
                'mission_type': mission_type or '_all',
                'total_cost': sum(costs),
                'execution_count': len(costs),
                'avg_cost': sum(costs) / len(costs),
                'avg_satisfaction': sum(satisfactions) / len(satisfactions) if satisfactions else None
            }
        except Exception as e:
            logger.error(f"[MISSION_STORE] Failed to get tool costs: {e}")
            return {'total_cost': 0, 'execution_count': 0, 'avg_cost': 0}


# Singleton instance
_store: Optional[MissionStore] = None


def get_mission_store() -> MissionStore:
    """Get singleton MissionStore instance."""
    global _store
    if _store is None:
        _store = MissionStore()
    return _store

