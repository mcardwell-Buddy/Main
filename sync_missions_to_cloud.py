#!/usr/bin/env python3
"""
Manual mission sync script - Force sync local SQLite missions to Firebase.

Usage:
    python sync_missions_to_cloud.py              # Sync all unsynced events
    python sync_missions_to_cloud.py --full       # Force full sync of all events
    python sync_missions_to_cloud.py --dry-run    # Show what would be synced
    python sync_missions_to_cloud.py --stats      # Show storage statistics
"""

import argparse
import sys
import logging
from pathlib import Path
from typing import Dict, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add Back_End to path
sys.path.insert(0, str(Path(__file__).parent))

from Back_End.local_mission_store import get_local_mission_store
from Back_End.mission_sync_service import get_sync_service

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


def show_stats():
    """Show storage statistics."""
    print("\n" + "="*60)
    print("📊 MISSION STORAGE STATISTICS")
    print("="*60)
    
    local_store = get_local_mission_store()
    stats = local_store.get_stats()
    
    print(f"\n📁 Local Storage (SQLite):")
    print(f"   Database: {local_store.db_path}")
    print(f"   Size: {stats['database_size_mb']} MB ({stats['database_size_bytes']:,} bytes)")
    print(f"   Total Events: {stats['total_events']}")
    print(f"   Unique Missions: {stats['unique_missions']}")
    print(f"   Unsynced Events: {stats['unsynced_events']}")
    
    if stats['unsynced_events'] > 0:
        print(f"\n⚠️  {stats['unsynced_events']} events need syncing to Firebase")
    else:
        print(f"\n✅ All events synced to Firebase")
    
    print("\n" + "="*60 + "\n")


def dry_run():
    """Show what would be synced without actually syncing."""
    print("\n" + "="*60)
    print("🔍 DRY RUN - Preview of events to sync")
    print("="*60)
    
    local_store = get_local_mission_store()
    unsynced = local_store.get_unsynced_events(limit=1000)
    
    if not unsynced:
        print("\n✅ No unsynced events found")
        print("="*60 + "\n")
        return
    
    print(f"\nFound {len(unsynced)} unsynced events:\n")
    
    # Group by mission_id
    by_mission: Dict[str, list] = {}
    for event in unsynced:
        mission_data = event['data']
        mission_id = mission_data.get('mission_id', 'unknown')
        if mission_id not in by_mission:
            by_mission[mission_id] = []
        by_mission[mission_id].append(mission_data)
    
    # Display summary
    for i, (mission_id, events) in enumerate(by_mission.items(), 1):
        print(f"{i}. Mission: {mission_id}")
        print(f"   Events: {len(events)}")
        for event in events:
            event_type = event.get('event_type', 'unknown')
            status = event.get('status', 'unknown')
            timestamp = event.get('timestamp', 'unknown')
            print(f"     - {event_type} → {status} ({timestamp})")
        print()
    
    print("="*60)
    print(f"Total: {len(unsynced)} events across {len(by_mission)} missions")
    print("="*60 + "\n")


def sync_all_unsynced():
    """Sync all unsynced events to Firebase."""
    print("\n" + "="*60)
    print("🔄 SYNCING UNSYNCED EVENTS TO FIREBASE")
    print("="*60)
    
    sync_service = get_sync_service()
    
    # Force immediate sync
    result = sync_service.force_sync()
    
    print(f"\n✅ Sync completed:")
    print(f"   Synced: {result['synced']} events")
    print(f"   Failed: {result['failed']} events")
    print(f"   Timestamp: {result['timestamp']}")
    
    if result['failed'] > 0:
        print(f"\n⚠️  {result['failed']} events failed to sync")
        print(f"   Check logs at: outputs/logs/mission_sync.log")
    
    print("\n" + "="*60 + "\n")


def full_sync():
    """Force full sync of all events (including already synced ones)."""
    print("\n" + "="*60)
    print("🔄 FULL SYNC - Syncing ALL events to Firebase")
    print("="*60)
    print("\n⚠️  WARNING: This will re-sync already synced events")
    print("This is useful for recovery or migration scenarios\n")
    
    response = input("Continue? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("Aborted.")
        return
    
    local_store = get_local_mission_store()
    firebase = get_firebase_db()
    
    # Get all missions
    all_mission_ids = local_store.list_missions()
    
    print(f"\nFound {len(all_mission_ids)} missions to sync...")
    
    synced_count = 0
    failed_count = 0
    
    for i, mission_id in enumerate(all_mission_ids, 1):
        print(f"\nSyncing mission {i}/{len(all_mission_ids)}: {mission_id}")
        
        events = local_store.get_mission_events(mission_id)
        
        for event in events:
            try:
                # Write to Firebase
                doc_ref = firebase.collection('missions').document(mission_id)
                event_id = f"{event.get('event_type')}_{event.get('timestamp')}"
                event_ref = doc_ref.collection('events').document(event_id)
                event_ref.set(event)
                
                synced_count += 1
                print(f"  ✓ {event.get('event_type')}")
                
            except Exception as e:
                logger.error(f"Failed to sync event: {e}")
                failed_count += 1
    
    print("\n" + "="*60)
    print(f"✅ Full sync completed:")
    print(f"   Synced: {synced_count} events")
    print(f"   Failed: {failed_count} events")
    print("="*60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description='Manual mission sync script - Sync local SQLite to Firebase',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                # Sync all unsynced events
  %(prog)s --stats        # Show storage statistics
  %(prog)s --dry-run      # Preview what would be synced
  %(prog)s --full         # Force full sync (including already synced)
        """
    )
    
    parser.add_argument('--stats', action='store_true',
                        help='Show storage statistics')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be synced without actually syncing')
    parser.add_argument('--full', action='store_true',
                        help='Force full sync of all events (including already synced)')
    
    args = parser.parse_args()
    
    try:
        if args.stats:
            show_stats()
        elif args.dry_run:
            dry_run()
        elif args.full:
            full_sync()
        else:
            # Default: sync unsynced events
            sync_all_unsynced()
            
    except KeyboardInterrupt:
        print("\n\n❌ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
