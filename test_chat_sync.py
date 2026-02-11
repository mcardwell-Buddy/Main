#!/usr/bin/env python
"""
Test to verify chat messages are being synced to Firebase.
"""
import sys
import os
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from Back_End.conversation.session_store import get_conversation_store
from Back_End.config import Config

print("=" * 80)
print("CHAT MESSAGE FIREBASE SYNC TEST")
print("=" * 80)

store = get_conversation_store()
print(f"✓ Store initialized (Firebase enabled: {store._firebase_enabled})")

# Simulate first message
session_id = f"chat_session_{int(datetime.now().timestamp())}"
print(f"\n1. Creating session: {session_id}")

try:
    session = store.get_or_create(session_id, source='chat_ui', external_user_id='user123')
    print(f"   ✓ Session created")
    
    # Add user message
    msg1 = store.append_message(session_id, 'user', 'Hello buddy', 'chat_ui')
    print(f"   ✓ User message added: {msg1.message_id}")
    
    # Add assistant message
    msg2 = store.append_message(session_id, 'assistant', 'Hello! How can I help you?', 'chat_ui')
    print(f"   ✓ Assistant message added: {msg2.message_id}")
    
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Verify in memory
print(f"\n2. Checking in-memory store:")
session_obj = store.get_session(session_id)
if session_obj:
    print(f"   ✓ Session found in memory")
    print(f"     - Messages: {len(session_obj.messages)}")
    for msg in session_obj.messages:
        print(f"       [{msg.role}] {msg.text[:50]}")
else:
    print(f"   ✗ Session not found in memory!")

# Verify in Firebase
print(f"\n3. Checking Firebase:")
if store._db and store._firebase_enabled:
    try:
        doc = store._collection.document(session_id).get()
        if doc.exists:
            data = doc.to_dict()
            print(f"   ✓ Document found in Firebase")
            print(f"     - Session ID: {data.get('session_id')}")
            print(f"     - Messages: {len(data.get('messages', []))}")
            print(f"     - Source: {data.get('source')}")
            
            for i, msg in enumerate(data.get('messages', [])):
                print(f"       [{msg['role']}] {msg['text'][:50]}")
        else:
            print(f"   ✗ Document NOT found in Firebase!")
    except Exception as e:
        print(f"   ✗ Firebase query error: {e}")
        import traceback
        traceback.print_exc()
else:
    print(f"   ✗ Firebase not initialized")

print("\n" + "=" * 80)
print(f"New session ID for testing: {session_id}")
print("=" * 80)

