"""
Mission Updater: Handle mid-execution mission modifications.

Allows users to clarify, update scope, or refine objectives during 
mission execution without restarting.

Examples:
- Add clarifications: "Also search for recent tutorials (2024+)"
- Update scope: "Exclude academic papers, only blogs"
- Refine objective: "Focus on beginner-friendly resources"
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class MissionUpdate:
    """Represents a single update/clarification to a mission."""
    
    def __init__(
        self,
        mission_id: str,
        update_type: str,  # 'clarification', 'scope_change', 'objective_refinement', 'metadata_update'
        update_data: Dict[str, Any],
        reason: Optional[str] = None
    ):
        self.mission_id = mission_id
        self.update_type = update_type
        self.update_data = update_data
        self.reason = reason
        self.timestamp = datetime.now(timezone.utc).isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'mission_id': self.mission_id,
            'update_type': self.update_type,
            'update_data': self.update_data,
            'reason': self.reason,
            'timestamp': self.timestamp
        }


class MissionUpdater:
    """
    Service for updating missions during execution.
    
    Tracks all updates in Firestore for audit/learning purposes.
    Updates are non-blocking: execution continues regardless.
    """
    
    def __init__(self, mission_store):
        self.mission_store = mission_store
        self._update_cache: Dict[str, List[MissionUpdate]] = {}  # mission_id → updates
    
    def add_clarification(
        self,
        mission_id: str,
        clarification: str,
        reason: Optional[str] = None
    ) -> bool:
        """
        Add clarification to mission during execution.
        
        Example:
            updater.add_clarification(
                "m_001",
                "Only include tutorials from 2024 onwards",
                reason="User wants most recent content"
            )
        
        Args:
            mission_id: Mission to clarify
            clarification: Text of clarification
            reason: Why this clarification was added
        
        Returns:
            True if successful, False otherwise
        """
        try:
            update = MissionUpdate(
                mission_id=mission_id,
                update_type='clarification',
                update_data={'text': clarification},
                reason=reason
            )
            return self._save_update(update)
        except Exception as e:
            logger.error(f"Failed to add clarification: {e}")
            return False
    
    def update_scope(
        self,
        mission_id: str,
        scope_changes: Dict[str, Any],
        reason: Optional[str] = None
    ) -> bool:
        """
        Update scope constraints during execution.
        
        Example:
            updater.update_scope(
                "m_001",
                {
                    'allowed_domains': ['python.org', 'realpython.com'],
                    'blocked_domains': ['pastebin.com'],
                    'max_results': 5
                },
                reason="Narrow search to trusted sources"
            )
        
        Args:
            mission_id: Mission to update
            scope_changes: Dict of scope changes
            reason: Why scope changed
        
        Returns:
            True if successful, False otherwise
        """
        try:
            update = MissionUpdate(
                mission_id=mission_id,
                update_type='scope_change',
                update_data=scope_changes,
                reason=reason
            )
            return self._save_update(update)
        except Exception as e:
            logger.error(f"Failed to update scope: {e}")
            return False
    
    def refine_objective(
        self,
        mission_id: str,
        refinement: str,
        reason: Optional[str] = None
    ) -> bool:
        """
        Refine mission objective during execution.
        
        Example:
            updater.refine_objective(
                "m_001",
                "Focus on beginner-friendly tutorials that cover basics",
                reason="User clarified target audience"
            )
        
        Args:
            mission_id: Mission to refine
            refinement: Refined objective text
            reason: Why objective was refined
        
        Returns:
            True if successful, False otherwise
        """
        try:
            update = MissionUpdate(
                mission_id=mission_id,
                update_type='objective_refinement',
                update_data={'refined_objective': refinement},
                reason=reason
            )
            return self._save_update(update)
        except Exception as e:
            logger.error(f"Failed to refine objective: {e}")
            return False
    
    def update_metadata(
        self,
        mission_id: str,
        metadata_updates: Dict[str, Any],
        reason: Optional[str] = None
    ) -> bool:
        """
        Update metadata fields during execution.
        
        Example:
            updater.update_metadata(
                "m_001",
                {
                    'priority': 'high',
                    'user_notes': 'Customer specifically requested this',
                    'deadline': '2026-02-12'
                },
                reason="Updated priority based on user feedback"
            )
        
        Args:
            mission_id: Mission to update
            metadata_updates: Dict of metadata changes
            reason: Why metadata changed
        
        Returns:
            True if successful, False otherwise
        """
        try:
            update = MissionUpdate(
                mission_id=mission_id,
                update_type='metadata_update',
                update_data=metadata_updates,
                reason=reason
            )
            return self._save_update(update)
        except Exception as e:
            logger.error(f"Failed to update metadata: {e}")
            return False
    
    def _save_update(self, update: MissionUpdate) -> bool:
        """Save update to Firestore and cache."""
        try:
            # Save to Firestore updates subcollection
            self.mission_store.save_mission_update(update)
            
            # Update cache
            if update.mission_id not in self._update_cache:
                self._update_cache[update.mission_id] = []
            self._update_cache[update.mission_id].append(update)
            
            logger.info(
                f"[MISSION_UPDATE] {update.mission_id}: {update.update_type} "
                f"(reason: {update.reason})"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to save update: {e}")
            return False
    
    def get_mission_updates(self, mission_id: str) -> List[MissionUpdate]:
        """Get all updates for a mission."""
        if mission_id in self._update_cache:
            return self._update_cache[mission_id]
        
        # Load from Firestore if not in cache
        try:
            updates = self.mission_store.get_mission_updates(mission_id)
            self._update_cache[mission_id] = updates
            return updates
        except Exception as e:
            logger.error(f"Failed to get updates: {e}")
            return []
    
    def get_mission_update_summary(self, mission_id: str) -> Dict[str, Any]:
        """
        Get summary of all updates to a mission.
        
        Returns:
        {
            'mission_id': str,
            'total_updates': int,
            'clarifications': [str, ...],
            'scope_changes': [Dict, ...],
            'objective_refinements': [str, ...],
            'metadata_updates': [Dict, ...],
            'last_update': ISO timestamp
        }
        """
        updates = self.get_mission_updates(mission_id)
        
        summary = {
            'mission_id': mission_id,
            'total_updates': len(updates),
            'clarifications': [],
            'scope_changes': [],
            'objective_refinements': [],
            'metadata_updates': [],
            'last_update': None
        }
        
        for update in updates:
            if update.update_type == 'clarification':
                summary['clarifications'].append({
                    'text': update.update_data.get('text'),
                    'reason': update.reason,
                    'timestamp': update.timestamp
                })
            elif update.update_type == 'scope_change':
                summary['scope_changes'].append({
                    'changes': update.update_data,
                    'reason': update.reason,
                    'timestamp': update.timestamp
                })
            elif update.update_type == 'objective_refinement':
                summary['objective_refinements'].append({
                    'refinement': update.update_data.get('refined_objective'),
                    'reason': update.reason,
                    'timestamp': update.timestamp
                })
            elif update.update_type == 'metadata_update':
                summary['metadata_updates'].append({
                    'updates': update.update_data,
                    'reason': update.reason,
                    'timestamp': update.timestamp
                })
            
            # Track most recent update
            if not summary['last_update'] or update.timestamp > summary['last_update']:
                summary['last_update'] = update.timestamp
        
        return summary


def get_mission_updater():
    """Get singleton MissionUpdater instance."""
    from Back_End.mission_store import get_mission_store
    
    if not hasattr(get_mission_updater, '_instance'):
        get_mission_updater._instance = MissionUpdater(
            mission_store=get_mission_store()
        )
    
    return get_mission_updater._instance
