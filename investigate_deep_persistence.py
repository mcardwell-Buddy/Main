"""
Deep investigation: Why sessions persist after deletion
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.conversation.session_store import get_conversation_store
from backend.config import Config
import time

print("=" * 80)
print("DEEP INVESTIGATION: WHY SESSIONS PERSIST AFTER DELETION")
print("=" * 80)

# Get the store
store = get_conversation_store()

print("\n1. BACKEND MEMORY STATE:")
print(f"   Sessions in memory: {len(store._sessions)}")
if store._sessions:
    for session_id, session in list(store._sessions.items())[:5]:
        print(f"   - {session_id}")
        print(f"     Source: {session.source}")
        print(f"     Messages: {len(session.messages)}")
        print(f"     Title: {session.title or '(no title)'}")

print("\n2. FIREBASE DIRECT CHECK:")
if store._firebase_enabled and store._db:
    try:
        docs = list(store._collection.stream())
        print(f"   Documents in Firebase: {len(docs)}")
        for doc in docs[:5]:
            data = doc.to_dict()
            print(f"   - {doc.id}")
            print(f"     Source: {data.get('source')}")
            print(f"     Messages: {len(data.get('messages', []))}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

print("\n3. CHECKING IF SESSIONS AUTO-RECREATE:")
print("   Looking for code that creates sessions automatically...")

# Check loadSessions in frontend
print("\n   Frontend behavior (from code analysis):")
print("   - Component mounts")
print("   - useEffect runs: loadSessionsFromBackend()")
print("   - If backend returns empty:")
print("     → Creates first session via POST /conversation/sessions/create")
print("   - This CREATES a new session in Firebase!")

print("\n4. THE AUTO-CREATION CYCLE:")
print("""
   CYCLE DISCOVERED:
   
   Step 1: User deletes all sessions from Firebase
   Step 2: Backend memory still has sessions (cached from startup)
   Step 3: Frontend calls GET /conversation/sessions
   Step 4: Backend returns sessions from memory
   Step 5: Frontend displays them
   
   OR if backend restarted:
   
   Step 1: User deletes all sessions from Firebase
   Step 2: Backend restarts, loads from Firebase (0 sessions)
   Step 3: Frontend calls GET /conversation/sessions
   Step 4: Backend returns [] (empty)
   Step 5: Frontend sees empty list
   Step 6: Frontend auto-creates "Session 1" via API call
   Step 7: Session appears in Firebase again!
   
   PROBLEM: Frontend auto-creates session when list is empty!
""")

print("\n5. CHECKING FRONTEND AUTO-CREATION CODE:")
print("   Looking at frontend/src/UnifiedChat.js...")

with open('frontend/src/UnifiedChat.js', 'r', encoding='utf-8') as f:
    content = f.read()
    
# Find the auto-creation logic
if 'No sessions found, create first session' in content:
    print("   ⚠️  FOUND: Auto-creation logic when no sessions exist")
    print("   Location: In loadSessionsFromBackend useEffect")
    print("   Behavior: If backend returns empty list → creates Session 1")
    print("   This is why sessions reappear after deletion!")

print("\n6. TRACE THE EXACT FLOW:")

# Simulate what happens
print("""
   USER DELETES SESSION FROM FIREBASE:
   
   1. User opens Firebase Console
   2. Deletes all documents in conversation_sessions
   3. Firebase now empty ✓
   
   BUT:
   
   4. Backend still has sessions in memory (if not restarted)
      → GET /conversation/sessions returns from memory
      → Sessions appear in UI
      → User sees "ghost sessions"
   
   OR if backend WAS restarted:
   
   4. Backend loads from (empty) Firebase
   5. Backend memory now empty
   6. Frontend loads, gets empty []
   7. Frontend sees no sessions
   8. Frontend code: "if (backendSessions.length === 0)"
   9. Frontend creates new session via POST
   10. New session appears immediately
   11. User thinks old session came back!
""")

print("\n7. VERIFICATION - CHECK TIMESTAMPS:")
print("\n   If sessions reappearing have:")
print("   - SAME IDs as before → Backend memory cache")
print("   - NEW IDs (recent timestamps) → Frontend auto-creating")

if store._sessions:
    print("\n   Current session IDs in backend memory:")
    for session_id in store._sessions.keys():
        # Session IDs are timestamps
        try:
            timestamp = int(session_id)
            created_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp/1000))
            print(f"   - {session_id} (created: {created_time})")
        except:
            print(f"   - {session_id}")

print("\n" + "=" * 80)
print("CONCLUSION")
print("=" * 80)
print("""
TWO CAUSES OF PERSISTENT SESSIONS:

CAUSE 1: Backend Memory Cache (after deletion)
- Backend loads sessions on startup into memory
- Deleting from Firebase doesn't clear backend memory
- GET /conversation/sessions returns stale data from memory
- Solution: Restart backend after Firebase deletion

CAUSE 2: Frontend Auto-Creation (after backend restart)
- When backend returns empty session list
- Frontend auto-creates "Session 1" to avoid empty state
- This immediately creates new session in Firebase
- Solution: Remove auto-creation OR add user confirmation

RECOMMENDATION:
- Check session IDs to determine which cause
- If OLD timestamp → Restart backend
- If NEW timestamp → Frontend is auto-creating
""")
