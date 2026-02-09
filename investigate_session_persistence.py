"""
Investigate why sessions persist even after Firebase deletion.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.conversation.session_store import get_conversation_store
from backend.config import Config

print("=" * 70)
print("INVESTIGATION: SESSION PERSISTENCE AFTER DELETION")
print("=" * 70)

# Check 1: Firebase enabled?
print(f"\n1. Firebase Status: {'ENABLED' if Config.FIREBASE_ENABLED else 'DISABLED'}")

# Check 2: What's in backend memory?
store = get_conversation_store()
print(f"\n2. Sessions in Backend Memory (ConversationStore._sessions):")
print(f"   Count: {len(store._sessions)}")

if store._sessions:
    print("\n   Session IDs in memory:")
    for session_id in list(store._sessions.keys())[:5]:  # Show first 5
        session = store._sessions[session_id]
        print(f"   - {session_id}: {len(session.messages)} messages, source={session.source}")

# Check 3: Firebase connection status
print(f"\n3. Firebase Connection:")
print(f"   _firebase_enabled: {store._firebase_enabled}")
print(f"   _db: {store._db is not None}")
if store._db:
    print(f"   _collection: {store._collection.id if hasattr(store._collection, 'id') else 'unknown'}")

# Check 4: Can we query Firebase directly?
if store._firebase_enabled and store._db:
    print(f"\n4. Sessions in Firebase (Direct Query):")
    try:
        docs = store._collection.stream()
        firebase_sessions = []
        for doc in docs:
            firebase_sessions.append(doc.id)
        print(f"   Count: {len(firebase_sessions)}")
        if firebase_sessions:
            print(f"   Session IDs in Firebase:")
            for session_id in firebase_sessions[:5]:  # Show first 5
                print(f"   - {session_id}")
    except Exception as e:
        print(f"   ❌ Error querying Firebase: {e}")

# Check 5: Compare memory vs Firebase
print(f"\n5. Analysis:")
memory_ids = set(store._sessions.keys())
if store._firebase_enabled and store._db:
    try:
        docs = store._collection.stream()
        firebase_ids = set(doc.id for doc in docs)
        
        only_in_memory = memory_ids - firebase_ids
        only_in_firebase = firebase_ids - memory_ids
        
        print(f"   Sessions only in memory: {len(only_in_memory)}")
        if only_in_memory:
            for sid in list(only_in_memory)[:3]:
                print(f"      - {sid}")
        
        print(f"   Sessions only in Firebase: {len(only_in_firebase)}")
        if only_in_firebase:
            for sid in list(only_in_firebase)[:3]:
                print(f"      - {sid}")
        
        print(f"   Sessions in both: {len(memory_ids & firebase_ids)}")
    except Exception as e:
        print(f"   ❌ Could not compare: {e}")

# Check 6: How does backend reload work?
print(f"\n6. Backend Reload Behavior:")
print(f"   ConversationStore._load_from_firebase() is called on __init__()")
print(f"   This happens ONCE when backend starts")
print(f"   If you delete from Firebase AFTER backend starts,")
print(f"   backend still has sessions in memory!")

print("\n" + "=" * 70)
print("CONCLUSION")
print("=" * 70)
print("""
If sessions persist after Firebase deletion:

LIKELY CAUSE: Backend in-memory cache
- ConversationStore loads sessions from Firebase on startup
- Sessions stored in self._sessions dict (in-memory)
- Deleting from Firebase doesn't update backend memory
- Frontend loads from backend API (GET /conversation/sessions)
- Backend returns what's in memory, not what's in Firebase

SOLUTION: Restart backend server to reload from Firebase

ALTERNATIVELY: Need to add cache invalidation logic
""")
