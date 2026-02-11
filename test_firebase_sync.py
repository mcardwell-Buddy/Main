#!/usr/bin/env python
"""
Quick test to verify Firebase persistence is working.
"""
import sys
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from Back_End.conversation.session_store import get_conversation_store
from Back_End.config import Config

print("=" * 80)
print("FIREBASE SYNC TEST")
print("=" * 80)

# Check config
print(f"\n1. FIREBASE CONFIG:")
print(f"   FIREBASE_ENABLED: {Config.FIREBASE_ENABLED}")
print(f"   FIREBASE_CREDENTIALS_PATH: {Config.FIREBASE_CREDENTIALS_PATH}")

# Check if credentials file exists
cred_path = Config.FIREBASE_CREDENTIALS_PATH
if cred_path:
    full_path = os.path.join(os.getcwd(), cred_path)
    exists = os.path.exists(full_path)
    print(f"   Credentials file exists: {exists}")
    if exists:
        print(f"   File size: {os.path.getsize(full_path)} bytes")

# Get store
print(f"\n2. GETTING CONVERSATION STORE:")
try:
    store = get_conversation_store()
    print(f"   ✓ Store obtained successfully")
    print(f"   Firebase enabled in store: {store._firebase_enabled}")
    print(f"   Firebase DB initialized: {store._db is not None}")
except Exception as e:
    print(f"   ✗ Failed to get store: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test session creation
print(f"\n3. TESTING SESSION CREATION:")
try:
    test_session_id = "test_session_001"
    session = store.get_or_create(test_session_id, source='test', external_user_id='test_user')
    print(f"   ✓ Session created: {test_session_id}")
    print(f"   Session object: {session}")
except Exception as e:
    print(f"   ✗ Failed to create session: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test message addition
print(f"\n4. TESTING MESSAGE ADDITION:")
try:
    msg = store.append_message(test_session_id, 'user', 'Test message', 'test')
    print(f"   ✓ Message added: {msg.message_id}")
    print(f"   Message: {msg.text}")
except Exception as e:
    print(f"   ✗ Failed to add message: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# List sessions in store
print(f"\n5. CHECKING SESSIONS IN MEMORY:")
try:
    sessions = store.list_sessions()
    print(f"   Sessions in memory: {len(sessions)}")
    for s in sessions:
        print(f"   - {s.session_id}: {len(s.messages)} messages")
except Exception as e:
    print(f"   ✗ Failed to list sessions: {e}")
    import traceback
    traceback.print_exc()

# Try to read from Firebase
print(f"\n6. CHECKING FIREBASE DIRECTLY:")
if store._db and store._firebase_enabled:
    try:
        collection = store._collection
        docs = collection.stream()
        count = 0
        for doc in docs:
            count += 1
            print(f"   ✓ Found document: {doc.id}")
            print(f"     Data keys: {list(doc.to_dict().keys())}")
        print(f"   Total documents in Firebase: {count}")
        
        if count == 0:
            print(f"   ⚠ WARNING: Firebase collection is empty - data not being persisted!")
    except Exception as e:
        print(f"   ✗ Failed to query Firebase: {e}")
        import traceback
        traceback.print_exc()
else:
    print(f"   ✗ Firebase not properly initialized")

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)

