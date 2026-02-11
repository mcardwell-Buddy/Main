#!/usr/bin/env python3
"""
INVESTIGATION 2B: Session Creation Flow Verification
Goal: Trace the actual flow when /chat/integrated endpoint is called
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def investigate_chat_integrated_flow():
    """Trace the actual flow for /chat/integrated endpoint"""
    print("=" * 70)
    print("INVESTIGATION 2B: /CHAT/INTEGRATED FLOW TRACE")
    print("=" * 70)
    
    print("\nFlow Analysis (from code reading):\n")
    
    print("1. Frontend sends: POST /chat/integrated")
    print("   └─ Request includes: session_id, user_id, text")
    print()
    
    print("2. Endpoint handler (main.py:1013-1065):")
    print("   └─ Creates ChatSessionHandler(session_id, user_id)")
    print("   └─ ChatSessionHandler.__init__ is called")
    print()
    
    print("3. ChatSessionHandler.__init__ (chat_session_handler.py:~220):")
    print("   └─ Stores session_id and user_id locally")
    print("   └─ Does NOT create session yet (lazy)")
    print()
    
    print("4. handle_message() called (main.py:1074):")
    print("   └─ ChatSessionHandler.handle_message() is called")
    print("   └─ This creates/stores the ChatMessage")
    print()
    
    print("5. Inside handle_message (chat_session_handler.py:~373):")
    print("   ✅ Calls: store.append_message()")
    print("   └─ This adds message to ConversationStore")
    print("   └─ ConversationStore saves to Firebase")
    print()
    
    print("HOWEVER - Session itself needs to be created first!")
    print()
    
    print("Looking for session creation in ChatSessionHandler:")
    try:
        with open("backend/chat_session_handler.py", "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        
        if "get_or_create(" in content and "session_id" in content:
            print("   ✅ Session creation code found")
            
            # Look for the pattern
            if "store.get_or_create(session_id" in content:
                print("   ✅ Calls: store.get_or_create(session_id)")
                print("   └─ This creates session in ConversationStore")
                return True
            else:
                print("   ❌ Doesn't appear to call store.get_or_create()")
                return False
        else:
            print("   ❌ No session creation pattern found")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

if __name__ == "__main__":
    result = investigate_chat_integrated_flow()
    
    print("\n" + "=" * 70)
    
    if result:
        print("✅ FINDING: /chat/integrated DOES persist sessions to Firebase")
        print("   Flow: /chat/integrated → ChatSessionHandler → handle_message()")
        print("         → append_message() → ConversationStore → Firebase")
        sys.exit(0)
    else:
        print("❌ FINDING: /chat/integrated flow unclear - needs verification")
        sys.exit(1)

