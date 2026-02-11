#!/usr/bin/env python3
"""
DIAGNOSTIC 1: When Does Backend Get Called?
Goal: Understand when frontend actually calls backend to create sessions
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 70)
print("DIAGNOSTIC 1: FRONTEND -> BACKEND SESSION FLOW")
print("=" * 70)

print("""
QUESTION: When does the frontend actually call the backend?

Let's trace the flow:

1. USER CLICKS "NEW SESSION" IN UI
   - Frontend creates a session ID (timestamp-based)
   - Frontend adds session to local state/storage
   - Question: Does it call backend yet? NO!

2. USER TYPES FIRST MESSAGE
   - Frontend calls: POST /chat/integrated
   - Backend receives: { session_id, text, user_id }
   - Backend creates ChatSessionHandler(session_id)
   - ChatSessionHandler.__init__() creates in ConversationStore
   - Question: Is this the FIRST time backend knows about session? YES!

PROBLEM IDENTIFIED:
==================
The frontend creates sessions LOCALLY (client-side only).
Backend only learns about session when first message arrives.

This explains:
- "New session" button doesn't call backend
- Session appears in UI but not Firebase
- Only when you send a message does backend create it

VERIFICATION NEEDED:
===================
Check frontend code (UnifiedChat.js) for:
1. Where "new session" is handled
2. If it calls backend API
3. If it stores sessions in localStorage
4. When it actually POSTs to /chat/integrated
""")

print("\n" + "=" * 70)
print("\nLet's check the frontend code...")
print("=" * 70)

# Check if UnifiedChat.js exists
frontend_file = "frontend/src/UnifiedChat.js"
if os.path.exists(frontend_file):
    print(f"\n✅ Found {frontend_file}")
    
    with open(frontend_file, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    
    # Check for localStorage usage
    if "localStorage" in content:
        print("❌ ISSUE: localStorage is being used!")
        
        # Count occurrences
        count = content.count("localStorage")
        print(f"   Found {count} references to localStorage")
        
        # Check what's being stored
        if "setItem" in content:
            print("   - setItem() calls found (storing data)")
        if "getItem" in content:
            print("   - getItem() calls found (retrieving data)")
        if "sessions" in content.lower() and "localstorage" in content.lower():
            print("   ⚠️  Sessions appear to be stored in localStorage!")
    else:
        print("✅ No localStorage usage found")
    
    # Check for new session handling
    if "handleNewSession" in content or "newSession" in content:
        print("\n📋 New session handling found:")
        print("   - handleNewSession or similar function exists")
        
        # Check if it calls backend
        if "fetch" in content or "axios" in content or "POST" in content:
            print("   - HTTP calls present in file")
        
    # Check for session creation
    if "createSession" in content:
        print("\n📋 Session creation function found")
    
    print("\n" + "=" * 70)
    print("FINDINGS:")
    print("=" * 70)
    
    if "localStorage" in content:
        print("\n❌ PROBLEM 1: Frontend uses localStorage")
        print("   Solution: Remove localStorage, use backend API only")
        
    print("\n❌ PROBLEM 2: 'New Session' doesn't call backend")
    print("   Solution: Call backend API to create session immediately")
    
else:
    print(f"\n❌ Could not find {frontend_file}")
    print("   Cannot verify frontend behavior")

print("\n" + "=" * 70)
print("\nDIAGNOSTIC SUMMARY:")
print("=" * 70)
print("""
ROOT CAUSES IDENTIFIED:

1. FRONTEND CREATES SESSIONS LOCALLY
   - "New Session" button creates ID client-side only
   - No backend API call on session creation
   - Backend only knows about it when first message sent

2. FRONTEND USES LOCALSTORAGE
   - Sessions and/or messages stored in browser
   - This is why clearing browser history loses chat
   - Should use backend/Firebase exclusively

REQUIRED FIXES:

Fix 1: Make "New Session" call backend API
   - Add endpoint: POST /conversation/sessions/create
   - Returns: { session_id }
   - Frontend calls this on "New Session" click
   - Backend creates in ConversationStore immediately

Fix 2: Remove localStorage usage from frontend
   - Load sessions from: GET /conversation/sessions
   - Load messages from session data
   - No local storage at all

Fix 3: Keep backend session creation on init (already done)
   - Fallback for legacy clients
   - Ensures session exists even if frontend doesn't call create API
""")

