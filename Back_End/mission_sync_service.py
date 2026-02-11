"""
Background sync service for syncing local SQLite missions to Firebase.

This service runs in a background thread and periodically syncs unsynced
mission events from the local SQLite database to Firebase Firestore.

Sync Strategy:
- Check for unsynced events every 5 minutes (configurable)
- Batch sync up to 100 events at a time
- Retry failed syncs with exponential backoff
- Log all sync operations for monitoring
"""

import os
import time
import logging
import threading
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path

from Back_End.local_mission_store import get_local_mission_store

# Firebase imports
try:
    from firebase_admin import firestore
    import firebase_admin
    from firebase_admin import credentials
    from Back_End.config import Config
    FIREBASE_AVAILABLE = Config.FIREBASE_ENABLED
except ImportError:
    FIREBASE_AVAILABLE = False
    firestore = None

logger = logging.getLogger(__name__)

class MissionSyncService:
    """Background service for syncing local missions to Firebase."""
    
    def __init__(self, sync_interval_seconds: int = 300, batch_size: int = 100):
        """Initialize sync service.
        
        Args:
            sync_interval_seconds: How often to check for unsynced events (default 5 minutes)
            batch_size: Maximum events to sync per batch (default 100)
        """
        self.sync_interval = sync_interval_seconds
        self.batch_size = batch_size
        self.running = False
        self.thread: threading.Thread = None
        
        self.local_store = get_local_mission_store()
        
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
                logger.info("Firebase client initialized for sync service")
            except Exception as e:
                logger.error(f"Failed to initialize Firebase: {e}")
                self._firebase_enabled = False
        
        # Sync statistics
        self.stats = {
            'total_synced': 0,
            'total_failed': 0,
            'last_sync_time': None,
            'last_sync_count': 0,
            'last_error': None
        }
        
        # Setup logging
        self._setup_logging()
        
        logger.info(f"MissionSyncService initialized (interval: {sync_interval_seconds}s, batch: {batch_size})")
    
    def _setup_logging(self):
        """Setup dedicated log file for sync operations."""
        log_dir = Path("outputs/logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / "mission_sync.log"
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        
        logger.addHandler(file_handler)
    
    def start(self):
        """Start the background sync service."""
        if self.running:
            logger.warning("Sync service already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._sync_loop, daemon=True)
        self.thread.start()
        
        logger.info("✅ Sync service started")
    
    def stop(self):
        """Stop the background sync service."""
        if not self.running:
            return
        
        self.running = False
        if self.thread:
            self.thread.join(timeout=10)
        
        logger.info("Sync service stopped")
    
    def _sync_loop(self):
        """Main sync loop running in background thread."""
        logger.info("Sync loop started")
        
        while self.running:
            try:
                # Perform sync
                self._sync_batch()
                
                # Sleep until next sync interval
                time.sleep(self.sync_interval)
                
            except Exception as e:
                logger.error(f"Error in sync loop: {e}")
                self.stats['last_error'] = str(e)
                time.sleep(60)  # Wait 1 minute before retry on error
    
    def _sync_batch(self):
        """Sync a batch of unsynced events to Firebase."""
        try:
            # Get unsynced events
            unsynced = self.local_store.get_unsynced_events(limit=self.batch_size)
            
            if not unsynced:
                logger.debug("No unsynced events found")
                return
            
            logger.info(f"Syncing {len(unsynced)} events to Firebase...")
            
            synced_row_ids = []
            failed_count = 0
            
            for event in unsynced:
                row_id = event['row_id']
                mission_data = event['data']
                
                # Sync to Firebase with retry logic
                if self._sync_to_firebase(mission_data):
                    synced_row_ids.append(row_id)
                else:
                    failed_count += 1
            
            # Mark synced events
            if synced_row_ids:
                self.local_store.mark_synced(synced_row_ids)
            
            # Update stats
            self.stats['total_synced'] += len(synced_row_ids)
            self.stats['total_failed'] += failed_count
            self.stats['last_sync_time'] = datetime.utcnow().isoformat()
            self.stats['last_sync_count'] = len(synced_row_ids)
            
            if failed_count > 0:
                logger.warning(f"⚠️ Sync completed: {len(synced_row_ids)} synced, {failed_count} failed")
            else:
                logger.info(f"✅ Sync completed: {len(synced_row_ids)} events synced")
                
        except Exception as e:
            logger.error(f"Failed to sync batch: {e}")
            self.stats['last_error'] = str(e)
    
    def _sync_to_firebase(self, mission_data: Dict[str, Any], max_retries: int = 3) -> bool:
        """Sync a single mission event to Firebase with retry logic.
        
        Args:
            mission_data: Mission data to sync
            max_retries: Maximum retry attempts
            
        Returns:
            bool: True if sync successful, False otherwise
        """
        if not self._firebase_enabled or not self._db:
            logger.warning("Firebase not enabled - cannot sync")
            return False
        
        mission_id = mission_data.get('mission_id')
        event_type = mission_data.get('event_type')
        
        for attempt in range(max_retries):
            try:
                # Write to Firebase
                doc_ref = self._db.collection('missions').document(mission_id)
                
                # Store in subcollection 'events' like the original implementation
                events_ref = doc_ref.collection('events')
                events_ref.add({
                    'mission_id': mission_id,
                    'event_type': event_type,
                    'status': mission_data.get('status'),
                    'timestamp': mission_data.get('timestamp'),
                    'data': mission_data,
                    'synced_at': datetime.utcnow().isoformat()
                })
                
                logger.debug(f"✓ Synced: {mission_id} → {event_type}")
                return True
                
            except Exception as e:
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                logger.warning(f"Sync attempt {attempt + 1}/{max_retries} failed for {mission_id}: {e}")
                
                if attempt < max_retries - 1:
                    time.sleep(wait_time)
                else:
                    logger.error(f"❌ All sync attempts failed for {mission_id}")
                    return False
        
        return False
    
    def force_sync(self) -> Dict[str, Any]:
        """Force an immediate sync and return results.
        
        Returns:
            Dictionary with sync results
        """
        logger.info("Force sync requested")
        
        initial_stats = self.stats.copy()
        self._sync_batch()
        
        return {
            'synced': self.stats['total_synced'] - initial_stats['total_synced'],
            'failed': self.stats['total_failed'] - initial_stats['total_failed'],
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get sync service statistics.
        
        Returns:
            Dictionary with sync statistics
        """
        local_stats = self.local_store.get_stats()
        
        return {
            'sync_service': {
                **self.stats,
                'running': self.running,
                'sync_interval_seconds': self.sync_interval,
                'batch_size': self.batch_size
            },
            'local_storage': local_stats
        }


# Singleton instance
_sync_service_instance: MissionSyncService = None

def get_sync_service() -> MissionSyncService:
    """Get singleton instance of MissionSyncService."""
    global _sync_service_instance
    if _sync_service_instance is None:
        _sync_service_instance = MissionSyncService()
    return _sync_service_instance


def start_sync_service():
    """Convenience function to start the sync service."""
    service = get_sync_service()
    service.start()
    return service


def stop_sync_service():
    """Convenience function to stop the sync service."""
    service = get_sync_service()
    service.stop()
