"""
Progress Persistence Layer: Helpers for saving/retrieving mission progress
from Firestore with caching and query optimization.
"""

from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ProgressPersistence:
    """Manage mission progress persistence and queries."""
    
    def __init__(self, mission_store):
        self.mission_store = mission_store
        self._progress_cache: Dict[str, Dict[str, Any]] = {}  # mission_id → progress
    
    def save_progress(self, mission_id: str, progress_tracker: Dict[str, Any]) -> bool:
        """Save progress to Firestore and update cache."""
        try:
            self.mission_store.save_progress(mission_id, progress_tracker)
            self._progress_cache[mission_id] = progress_tracker
            logger.debug(f"[PROGRESS_CACHE] Saved {mission_id} to Firestore and cache")
            return True
        except Exception as e:
            logger.error(f"[PROGRESS_PERSISTENCE] Failed to save: {e}")
            return False
    
    def get_progress(self, mission_id: str, use_cache: bool = True) -> Dict[str, Any]:
        """Get progress from cache or Firestore."""
        if use_cache and mission_id in self._progress_cache:
            logger.debug(f"[PROGRESS_CACHE] Cache hit for {mission_id}")
            return self._progress_cache[mission_id]
        
        logger.debug(f"[PROGRESS_CACHE] Cache miss for {mission_id}, querying Firestore")
        progress = self.mission_store.get_mission_progress(mission_id)
        if 'error' not in progress:
            self._progress_cache[mission_id] = progress
        
        return progress
    
    def clear_cache(self, mission_id: Optional[str] = None) -> None:
        """Clear progress cache (useful for testing)."""
        if mission_id:
            self._progress_cache.pop(mission_id, None)
            logger.debug(f"[PROGRESS_CACHE] Cleared cache for {mission_id}")
        else:
            self._progress_cache.clear()
            logger.debug("[PROGRESS_CACHE] Cleared entire cache")


def get_progress_persistence():
    """Singleton instance of progress persistence."""
    from Back_End.mission_store import get_mission_store
    
    if not hasattr(get_progress_persistence, '_instance'):
        get_progress_persistence._instance = ProgressPersistence(
            mission_store=get_mission_store()
        )
    
    return get_progress_persistence._instance
