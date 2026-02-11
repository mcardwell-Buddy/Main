"""Test script for local-first storage."""
import sys
sys.path.insert(0, '.')

from Back_End.mission_store import get_mission_store, Mission
import time

print("\n" + "="*60)
print("🧪 TESTING LOCAL-FIRST STORAGE")
print("="*60)

# Get store
store = get_mission_store()
print(f"\n📦 Storage mode: {store._storage_mode}")

# Create test mission
mission_id = f'test_local_{int(time.time())}'
mission = Mission(
    mission_id=mission_id,
    event_type='mission_proposed',
    status='proposed',
    objective={'test': 'local storage', 'purpose': 'verify SQLite writes'}
)

# Write mission
print(f"\n✍️  Writing test mission: {mission_id}")
store.write_mission_event(mission)
print("✅ Mission written successfully")

# Verify write
print(f"\n🔍 Verifying write...")
events = store.get_mission_events(mission.mission_id)
print(f"✅ Found {len(events)} event(s) for mission {mission.mission_id}")

# Show local storage stats
if store._local_store:
    stats = store._local_store.get_stats()
    print(f"\n📊 Local Storage Statistics:")
    print(f"   Database: {store._local_store.db_path}")
    print(f"   Total events: {stats['total_events']}")
    print(f"   Unsynced events: {stats['unsynced_events']}")
    print(f"   Unique missions: {stats['unique_missions']}")
    print(f"   Database size: {stats['database_size_mb']} MB")
    
    # Check if database file exists
    if store._local_store.db_path.exists():
        print(f"\n✅ SQLite database exists at: {store._local_store.db_path}")
    else:
        print(f"\n❌ SQLite database NOT found at: {store._local_store.db_path}")
else:
    print(f"\n⚠️  Not using local storage (mode: {store._storage_mode})")

print("\n" + "="*60)
print("✅ TEST COMPLETED")
print("="*60 + "\n")
