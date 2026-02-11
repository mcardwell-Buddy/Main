#!/usr/bin/env python3
"""
INVESTIGATION 2: Session Creation from All Entry Points
Goal: Verify all session creation paths use ConversationStore
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pathlib import Path
import re

def find_all_session_creation_paths():
    """Find and analyze all session creation entry points"""
    print("=" * 70)
    print("INVESTIGATION 2: SESSION CREATION FROM ALL ENTRY POINTS")
    print("=" * 70)
    
    # Critical files that handle incoming messages
    entry_points = {
        "backend/main.py": {
            "endpoint": "/chat/integrated",
            "expected": "Should use ChatSessionHandler (which syncs to ConversationStore)"
        },
        "backend/chat_session_handler.py": {
            "endpoint": "ChatSessionHandler.__init__ / ChatSessionManager.get_or_create",
            "expected": "Should directly sync to ConversationStore"
        },
        "backend/interaction_orchestrator.py": {
            "endpoint": "process_message() entry point",
            "expected": "Should use ConversationStore if creating sessions"
        },
    }
    
    print("\nAnalyzing entry points:\n")
    
    results = {}
    
    for file_path, info in entry_points.items():
        if not Path(file_path).exists():
            print(f"❌ {file_path}: FILE NOT FOUND")
            results[file_path] = "ERROR"
            continue
        
        print(f"\n📄 {file_path}")
        print(f"   Entry: {info['endpoint']}")
        print(f"   Expected: {info['expected']}")
        
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            
            # Check for ConversationStore usage
            has_store = "ConversationStore" in content or "get_conversation_store" in content
            has_sync = "store.get_or_create" in content or "append_message" in content
            
            if has_store:
                print(f"   ✅ Uses ConversationStore")
                if has_sync:
                    print(f"   ✅ Calls store.get_or_create() or append_message()")
                    results[file_path] = "COMPLETE"
                else:
                    print(f"   ⚠️  Imports ConversationStore but unclear if used")
                    results[file_path] = "PARTIAL"
            else:
                print(f"   ❌ Does NOT use ConversationStore")
                results[file_path] = "MISSING"
                
                # Check if it creates sessions at all
                if "session_id" in content or "Session(" in content:
                    print(f"   ⚠️  BUT: File creates sessions without persisting")
                
        except Exception as e:
            print(f"   ❌ Error reading file: {e}")
            results[file_path] = "ERROR"
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY:\n")
    
    complete = sum(1 for v in results.values() if v == "COMPLETE")
    partial = sum(1 for v in results.values() if v == "PARTIAL")
    missing = sum(1 for v in results.values() if v == "MISSING")
    errors = sum(1 for v in results.values() if v == "ERROR")
    total = len(results)
    
    print(f"Complete (uses ConversationStore):   {complete}/{total}")
    print(f"Partial (unclear usage):             {partial}/{total}")
    print(f"Missing (NO ConversationStore):      {missing}/{total}")
    print(f"Errors:                              {errors}/{total}")
    
    # Details
    print(f"\nDetailed Results:")
    for file_path, status in results.items():
        status_symbol = "✅" if status == "COMPLETE" else "⚠️ " if status == "PARTIAL" else "❌" if status == "MISSING" else "❌"
        print(f"  {status_symbol} {file_path}: {status}")
    
    print("\n" + "=" * 70)
    
    if complete == total:
        print("✅ ALL ENTRY POINTS USE CONVERSATIONSTORE")
        return True
    elif complete + partial >= total - 1:
        print("⚠️  MOSTLY OK - Some uncertainty")
        return None
    else:
        print("❌ GAPS FOUND - Some paths bypass ConversationStore")
        return False

if __name__ == "__main__":
    result = find_all_session_creation_paths()
    
    if result is True:
        print("\nFINDING: All session creation paths persist to Firebase")
        sys.exit(0)
    elif result is None:
        print("\nFINDING: Mostly good, needs verification")
        sys.exit(0)
    else:
        print("\nFINDING: Session persistence gaps exist - needs fixes")
        sys.exit(1)

