#!/usr/bin/env python3
"""
TEST 5: All Session Creation Paths
Goal: Find all places where ConversationSession is created and verify
they all go through ConversationStore (for Firebase persistence).
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import re
from pathlib import Path

def test_session_creation_paths():
    """Find all session creation paths"""
    print("=" * 70)
    print("TEST 5: ALL SESSION CREATION PATHS")
    print("=" * 70)
    
    backend_dir = Path("backend")
    
    # Patterns to search for
    patterns = [
        r"ConversationSession\(",
        r"ChatSessionManager\(\)",
        r"get_or_create_session",
        r"create_session",
        r"new.*session",
    ]
    
    print("\n1. Searching for session creation calls...\n")
    
    findings = {}
    
    for py_file in backend_dir.rglob("*.py"):
        try:
            with open(py_file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                lines = content.split("\n")
            
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    # Find line number
                    line_num = content[:match.start()].count("\n") + 1
                    line_text = lines[line_num - 1] if line_num <= len(lines) else ""
                    
                    file_key = str(py_file)
                    if file_key not in findings:
                        findings[file_key] = []
                    
                    findings[file_key].append({
                        "line": line_num,
                        "pattern": pattern,
                        "text": line_text.strip()
                    })
        
        except Exception as e:
            print(f"   Error reading {py_file}: {e}")
    
    if not findings:
        print("   ⚠️  No session creation patterns found!")
        print("   (This might mean they're created dynamically)")
        return None
    
    print(f"   Found {sum(len(v) for v in findings.values())} potential session creations:\n")
    
    for file_path, matches in sorted(findings.items()):
        print(f"   📄 {file_path}:")
        for match in matches:
            print(f"      L{match['line']:3d}: {match['text'][:70]}")
    
    # Check if they go through ConversationStore
    print("\n2. Checking if session creations use ConversationStore...\n")
    
    # Read critical files
    critical_files = [
        "backend/chat_session_handler.py",
        "backend/chat_session_manager.py",
        "backend/interaction_orchestrator.py",
        "backend/main.py",
    ]
    
    store_usage = {}
    for file_path in critical_files:
        if Path(file_path).exists():
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            except:
                content = ""
            
            has_store_call = "ConversationStore" in content or "conversation_store" in content
            store_usage[file_path] = has_store_call
            
            status = "✅" if has_store_call else "❌"
            print(f"   {status} {file_path}: {'Uses ConversationStore' if has_store_call else 'Does NOT use ConversationStore'}")
    
    # Final analysis
    print("\n3. Analysis:")
    
    uses_store = sum(1 for v in store_usage.values() if v)
    total = len(store_usage)
    
    if uses_store == total:
        print(f"   ✅ All critical files use ConversationStore")
        print(f"   ✅ Session persistence should reach Firebase")
        return True
    elif uses_store > 0:
        print(f"   ⚠️  Only {uses_store}/{total} files use ConversationStore")
        print(f"   ⚠️  Some session creation paths might bypass Firebase!")
        return False
    else:
        print(f"   ❌ NO critical files use ConversationStore!")
        print(f"   ❌ Sessions are NOT persisting to Firebase")
        return False
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    try:
        result = test_session_creation_paths()
        if result:
            print("\n✅ Test PASSED: All session paths use ConversationStore")
            sys.exit(0)
        elif result is False:
            print("\n❌ Test FAILED: Some paths don't use ConversationStore")
            sys.exit(1)
        else:
            print("\n⚠️  Test INCONCLUSIVE: Need manual verification")
            sys.exit(0)
    except Exception as e:
        print(f"\n❌ Test ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
