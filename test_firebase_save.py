"""
Test if Firebase saving actually works by creating a test session
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from Back_End.conversation.session_store import get_conversation_store
import time

print("=" * 80)
print("TEST: Create Session and Verify Firebase Save")
print("=" * 80)

store = get_conversation_store()

# Create a test session
test_session_id = f"test_{int(time.time() * 1000)}"
print(f"\n1. Creating test session: {test_session_id}")

try:
    session = store.get_or_create(
        session_id=test_session_id,
        source='chat_ui',
        external_user_id='test_user'
    )
    print(f"   ✅ Session created in memory")
    print(f"   - ID: {session.session_id}")
    print(f"   - Source: {session.source}")
except Exception as e:
    print(f"   ❌ Failed to create: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Check if it's in memory
print(f"\n2. Checking backend memory:")
if test_session_id in store._sessions:
    print(f"   ✅ Found in memory")
else:
    print(f"   ❌ NOT in memory")

# Check if Firebase save was attempted
print(f"\n3. Checking Firebase state:")
print(f"   Firebase enabled: {store._firebase_enabled}")
print(f"   DB client: {store._db is not None}")

# Wait a moment for Firebase write
print(f"\n4. Waiting 2 seconds for Firebase write...")
time.sleep(2)

# Query Firebase directly
if store._firebase_enabled and store._db:
    try:
        doc = store._collection.document(test_session_id).get()
        if doc.exists:
            print(f"   ✅ FOUND in Firebase!")
            data = doc.to_dict()
            print(f"   - session_id: {data.get('session_id')}")
            print(f"   - source: {data.get('source')}")
        else:
            print(f"   ❌ NOT FOUND in Firebase")
            print(f"   Session was created in memory but not saved to Firebase!")
            
            # Check all documents
            print(f"\n   Checking all documents in collection:")
            all_docs = list(store._collection.stream())
            print(f"   Total documents: {len(all_docs)}")
            for d in all_docs[:5]:
                print(f"   - {d.id}")
    except Exception as e:
        print(f"   ❌ Error querying Firebase: {e}")
        import traceback
        traceback.print_exc()

# Clean up - delete test session
print(f"\n5. Cleanup:")
try:
    if store._firebase_enabled and store._db:
        store._collection.document(test_session_id).delete()
        print(f"   ✅ Test session deleted from Firebase")
    if test_session_id in store._sessions:
        del store._sessions[test_session_id]
        print(f"   ✅ Test session deleted from memory")
except Exception as e:
    print(f"   ⚠️  Cleanup error: {e}")

print("\n" + "=" * 80)
print("DIAGNOSIS")
print("=" * 80)
print("""
If test session was:
- ✅ Created in memory
- ✅ Found in Firebase
  → Firebase save is working!
  → Problem is elsewhere (frontend? API?)

If test session was:
- ✅ Created in memory
- ❌ NOT in Firebase
  → _save_to_firebase() is failing silently
  → Check Firebase credentials/permissions
""")

