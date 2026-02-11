"""
Comprehensive investigation: Why new sessions don't save but old ones persist
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from Back_End.conversation.session_store import get_conversation_store
from Back_End.config import Config

print("=" * 80)
print("COMPREHENSIVE INVESTIGATION: SESSION PERSISTENCE ANOMALY")
print("=" * 80)

# Check 1: What's in Firebase RIGHT NOW
print("\n1. FIREBASE ACTUAL STATE (Direct Query):")
store = get_conversation_store()

if store._firebase_enabled and store._db:
    try:
        docs = list(store._collection.stream())
        print(f"   Total documents in Firebase: {len(docs)}")
        
        if docs:
            print("\n   Session details:")
            for doc in docs:
                data = doc.to_dict()
                print(f"\n   Document ID: {doc.id}")
                print(f"   - session_id: {data.get('session_id')}")
                print(f"   - source: {data.get('source')}")
                print(f"   - messages: {len(data.get('messages', []))}")
                print(f"   - title: {data.get('title', '(no title)')}")
                print(f"   - archived: {data.get('archived', False)}")
        else:
            print("   (empty - no documents)")
    except Exception as e:
        print(f"   ❌ Error querying Firebase: {e}")
        import traceback
        traceback.print_exc()

# Check 2: Backend memory state
print("\n2. BACKEND MEMORY STATE:")
print(f"   Sessions in memory: {len(store._sessions)}")
if store._sessions:
    for session_id in list(store._sessions.keys())[:5]:
        session = store._sessions[session_id]
        print(f"   - {session_id}: {len(session.messages)} msgs, source={session.source}")

# Check 3: Check if _save_to_firebase actually works
print("\n3. TESTING _save_to_firebase() METHOD:")
print(f"   Firebase enabled: {store._firebase_enabled}")
print(f"   DB client exists: {store._db is not None}")
print(f"   Collection: {store._collection.id if store._db else 'N/A'}")

# Check 4: Trace the save path
print("\n4. TRACING SAVE PATH:")
print("   When session is created, does it call _save_to_firebase()?")
print("   Let's check the code flow...")

import inspect
create_method = store.get_or_create
print(f"\n   get_or_create method source location:")
print(f"   File: {inspect.getfile(create_method)}")

# Read the method to see if it saves
source_lines = inspect.getsource(create_method)
if '_save_to_firebase' in source_lines:
    print("   ✅ FOUND: get_or_create() calls _save_to_firebase()")
else:
    print("   ❌ MISSING: get_or_create() does NOT call _save_to_firebase()")
    print("   This would explain why new sessions don't persist!")

# Check 5: Check append_message
print("\n5. CHECKING append_message() METHOD:")
append_method = store.append_message
source_lines = inspect.getsource(append_method)
if '_save_to_firebase' in source_lines:
    print("   ✅ append_message() calls _save_to_firebase()")
else:
    print("   ❌ append_message() does NOT call _save_to_firebase()")

print("\n" + "=" * 80)
print("ANALYSIS")
print("=" * 80)

print("""
HYPOTHESIS 1: get_or_create() doesn't save to Firebase
- When POST /conversation/sessions/create is called
- It calls store.get_or_create()
- If get_or_create() doesn't call _save_to_firebase()
- Session exists in memory but NOT in Firebase
- Frontend sees session (from memory) but Firebase doesn't have it

HYPOTHESIS 2: Old sessions loaded on backend startup
- Backend starts
- Loads sessions from Firebase via _load_from_firebase()
- Those sessions persist in memory
- Even if deleted from Firebase later
- Backend memory cache still has them

HYPOTHESIS 3: Timing issue
- New session created
- Not yet written to Firebase (async/delay)
- User checks Firebase too quickly
- Appears not saved

NEXT: Check the actual get_or_create() implementation
""")

