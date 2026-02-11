#!/usr/bin/env python3
"""
Recovery script - Rebuild local SQLite database from Firebase.

This script downloads all missions from Firebase Firestore and rebuilds
the local SQLite database. Useful for:
- Recovering from SQLite database corruption
- Setting up local-first mode on a new machine
- Migrating from cloud-direct to local-first mode

Usage:
    python rebuild_local_from_cloud.py              # Rebuild from Firebase
    python rebuild_local_from_cloud.py --backup     # Backup existing DB first
    python rebuild_local_from_cloud.py --validate   # Validate after rebuild
"""

import argparse
import sys
import logging
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add Back_End to path
sys.path.insert(0, str(Path(__file__).parent))

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


def get_firebase_db():
    """Get Firebase firestore client."""
    if not FIREBASE_AVAILABLE:
        raise RuntimeError("Firebase not available")
    
    # Initialize firebase_admin if not already initialized
    if not firebase_admin._apps:
        cred_path = Config.FIREBASE_CREDENTIALS_PATH
        if cred_path:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
        else:
            raise RuntimeError("FIREBASE_CREDENTIALS_PATH not set")
    
    return firestore.client()


def backup_existing_database():
    """Backup existing SQLite database before rebuilding."""
    local_store = get_local_mission_store()
    db_path = local_store.db_path
    
    if not db_path.exists():
        logger.info("No existing database to backup")
        return None
    
    # Create backup filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = db_path.parent / f"buddy_missions_backup_{timestamp}.db"
    
    try:
        shutil.copy2(db_path, backup_path)
        logger.info(f"✅ Backed up database to: {backup_path}")
        return backup_path
    except Exception as e:
        logger.error(f"Failed to backup database: {e}")
        return None


def download_missions_from_firebase() -> List[Dict[str, Any]]:
    """Download all mission events from Firebase.
    
    Returns:
        List of all mission events
    """
    firebase = get_firebase_db()
    
    print("\n" + "="*60)
    print("📥 DOWNLOADING MISSIONS FROM FIREBASE")
    print("="*60)
    
    all_events = []
    
    try:
        # Get all mission documents
        missions_ref = firebase.collection('missions')
        mission_docs = missions_ref.stream()
        
        mission_count = 0
        for mission_doc in mission_docs:
            mission_id = mission_doc.id
            mission_count += 1
            
            print(f"\nDownloading mission {mission_count}: {mission_id}")
            
            # Get all events for this mission
            events_ref = mission_doc.reference.collection('events')
            event_docs = events_ref.order_by('timestamp').stream()
            
            event_count = 0
            for event_doc in event_docs:
                event_data = event_doc.to_dict()
                event_data['mission_id'] = mission_id  # Ensure mission_id is set
                all_events.append(event_data)
                event_count += 1
            
            print(f"  Downloaded {event_count} events")
        
        print("\n" + "="*60)
        print(f"✅ Downloaded {len(all_events)} events from {mission_count} missions")
        print("="*60 + "\n")
        
        return all_events
        
    except Exception as e:
        logger.error(f"Failed to download missions: {e}")
        raise


def rebuild_local_database(events: List[Dict[str, Any]]):
    """Rebuild local SQLite database from downloaded events.
    
    Args:
        events: List of mission event dictionaries
    """
    print("\n" + "="*60)
    print("🔨 REBUILDING LOCAL DATABASE")
    print("="*60)
    
    local_store = get_local_mission_store()
    
    # Delete existing database
    if local_store.db_path.exists():
        local_store.db_path.unlink()
        logger.info(f"Deleted existing database: {local_store.db_path}")
    
    # Re-initialize database (creates fresh schema)
    local_store._init_database()
    
    # Write all events to local store
    success_count = 0
    failed_count = 0
    
    for i, event_data in enumerate(events, 1):
        try:
            # Write to local store, mark as synced since it came from Firebase
            local_store.write_mission_event(event_data)
            
            # Mark as synced (get the row ID and mark it)
            # Since we just wrote it, it's the last row
            with local_store._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE missions SET synced = 1 WHERE id = (SELECT MAX(id) FROM missions)")
                conn.commit()
            
            success_count += 1
            
            if i % 10 == 0:
                print(f"  Progress: {i}/{len(events)} events...")
                
        except Exception as e:
            logger.error(f"Failed to write event {i}: {e}")
            failed_count += 1
    
    print("\n" + "="*60)
    print(f"✅ Database rebuilt:")
    print(f"   Success: {success_count} events")
    print(f"   Failed: {failed_count} events")
    print(f"   Location: {local_store.db_path}")
    print("="*60 + "\n")


def validate_database():
    """Validate the rebuilt database."""
    print("\n" + "="*60)
    print("🔍 VALIDATING DATABASE")
    print("="*60)
    
    local_store = get_local_mission_store()
    stats = local_store.get_stats()
    
    print(f"\n✅ Database Statistics:")
    print(f"   Total Events: {stats['total_events']}")
    print(f"   Unique Missions: {stats['unique_missions']}")
    print(f"   Unsynced Events: {stats['unsynced_events']}")
    print(f"   Database Size: {stats['database_size_mb']} MB")
    
    if stats['unsynced_events'] > 0:
        print(f"\n⚠️  Warning: {stats['unsynced_events']} events marked as unsynced")
        print(f"   This shouldn't happen after rebuild - something may be wrong")
    else:
        print(f"\n✅ All events properly marked as synced")
    
    print("\n" + "="*60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description='Recovery script - Rebuild local SQLite from Firebase',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                # Rebuild database from Firebase
  %(prog)s --backup       # Backup existing DB first
  %(prog)s --validate     # Validate after rebuild
        """
    )
    
    parser.add_argument('--backup', action='store_true',
                        help='Backup existing database before rebuilding')
    parser.add_argument('--validate', action='store_true',
                        help='Validate database after rebuilding')
    parser.add_argument('--no-confirm', action='store_true',
                        help='Skip confirmation prompt (use with caution)')
    
    args = parser.parse_args()
    
    try:
        # Confirm destructive action
        if not args.no_confirm:
            print("\n" + "="*60)
            print("⚠️  WARNING: DESTRUCTIVE OPERATION")
            print("="*60)
            print("\nThis will DELETE your existing local SQLite database")
            print("and rebuild it from Firebase Firestore.")
            print("\nAny unsynced local changes will be LOST!")
            
            if args.backup:
                print("\nA backup will be created first.")
            
            print("\n" + "="*60)
            response = input("\nContinue? (yes/no): ").strip().lower()
            if response not in ['yes', 'y']:
                print("Aborted.")
                return
        
        # Backup if requested
        if args.backup:
            backup_path = backup_existing_database()
            if backup_path:
                print(f"\n✅ Backup created at: {backup_path}")
        
        # Download missions from Firebase
        events = download_missions_from_firebase()
        
        if not events:
            print("\n⚠️  No events found in Firebase - nothing to rebuild")
            return
        
        # Rebuild local database
        rebuild_local_database(events)
        
        # Validate if requested
        if args.validate:
            validate_database()
        
        print("\n✅ Recovery completed successfully!")
        print(f"   You can now use local-first mode with {len(events)} synced events\n")
        
    except KeyboardInterrupt:
        print("\n\n❌ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Recovery failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
