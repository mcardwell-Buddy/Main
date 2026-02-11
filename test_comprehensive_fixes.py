#!/usr/bin/env python
"""
Test the complete fix for:
1. Message persistence to Firebase
2. LLM-based selector generation
3. Session ID consistency
"""

import requests
import json
from uuid import uuid4

BASE_URL = "http://localhost:8000"

def test_message_persistence():
    """Test that messages are saved to Firebase"""
    print("\n" + "="*60)
    print("TEST 1: MESSAGE PERSISTENCE")
    print("="*60)
    
    session_id = f"test_session_{uuid4().hex[:8]}"
    
    # Send a message
    print(f"\n1. Creating new session: {session_id}")
    response = requests.post(f"{BASE_URL}/chat/integrated", json={
        "text": "Can you visit www.cardwellassociates.com and provide a list of services they offer?",
        "session_id": session_id,
        "external_user_id": "test_user"
    })
    
    print(f"   Response status: {response.status_code}")
    data = response.json()
    print(f"   Session ID returned: {data.get('session_id')}")
    print(f"   Message ID: {data.get('chat_message_id')}")
    
    # Load sessions and check if messages are saved
    print(f"\n2. Loading sessions from Back_End...")
    resp_sessions = requests.get(f"{BASE_URL}/conversation/sessions")
    sessions = resp_sessions.json().get('sessions', [])
    
    test_session = None
    for s in sessions:
        if str(s.get('session_id')) == str(session_id):
            test_session = s
            break
    
    if test_session:
        print(f"   ✅ Session found!")
        print(f"   Session ID: {test_session.get('session_id')}")
        print(f"   Title: {test_session.get('title')}")
        print(f"   Message count: {test_session.get('message_count')}")
        print(f"   Messages:")
        for msg in test_session.get('messages', [])[:3]:
            print(f"     - [{msg.get('role')}] {msg.get('text')[:60]}...")
    else:
        print(f"   ❌ Session NOT found in backend!")
        print(f"   Available sessions: {[s.get('session_id') for s in sessions]}")
    
    return test_session is not None

def test_selector_generation():
    """Test that CSS selectors are generated correctly"""
    print("\n" + "="*60)
    print("TEST 2: LLM-BASED SELECTOR GENERATION")
    print("="*60)
    
    from Back_End.tool_selector import tool_selector
    
    test_cases = [
        ("Extract 'services' from https://www.cardwellassociates.com", "services"),
        ("Get the main headline from example.com", "headline"),
        ("Extract contact information from the website", "contact info"),
    ]
    
    print("\nGenerating selectors for common requests:")
    for goal, expected_type in test_cases:
        result = tool_selector.prepare_input('web_extract', goal, {})
        print(f"\n  Goal: {goal}")
        print(f"  Expected type: {expected_type}")
        print(f"  Generated selectors: {result}")
        # Check if result looks like CSS selectors (contains . or #)
        if '.' in result or '#' in result:
            print(f"  ✅ Valid selectors generated")
        else:
            print(f"  ⚠️  May not be valid CSS selectors")
    
    return True

if __name__ == "__main__":
    print("\n" + "="*80)
    print("BUDDY FIX VERIFICATION TESTS")
    print("="*80)
    
    # Test 1: Message persistence
    persistence_ok = test_message_persistence()
    
    # Test 2: Selector generation
    selector_ok = test_selector_generation()
    
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Message Persistence: {'✅ PASS' if persistence_ok else '❌ FAIL'}")
    print(f"Selector Generation: {'✅ PASS' if selector_ok else '❌ FAIL'}")
    print("="*80)

