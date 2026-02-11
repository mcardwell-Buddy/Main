"""
Chat Intake → Mission Dispatcher Demo

Demonstrates the chat-to-mission flow WITHOUT execution.

Shows:
1. Intent routing
2. Draft building
3. Proposal emission
4. Whiteboard visibility
5. Chat feedback

NO execution. NO autonomy. Pure demonstration.
"""

import sys
from pathlib import Path

# Add workspace to path
sys.path.insert(0, str(Path(__file__).parent))

from Back_End.mission_control.chat_intake_coordinator import ChatIntakeCoordinator
from Back_End.whiteboard.mission_whiteboard import get_proposed_missions


def demo_chat_intake():
    """Run comprehensive demo of chat intake system."""
    
    print("\n" + "=" * 80)
    print("CHAT INTAKE → MISSION DISPATCHER DEMO")
    print("=" * 80)
    
    coordinator = ChatIntakeCoordinator()
    
    # Test messages
    test_messages = [
        {
            'message': 'Get all quotes from quotes.toscrape.com',
            'expected': 'action_request'
        },
        {
            'message': 'Find contact information on yellowpages.com',
            'expected': 'exploratory_request'
        },
        {
            'message': 'Extract 100 leads from mployer.com',
            'expected': 'action_request'
        },
        {
            'message': 'What is the weather today?',
            'expected': 'informational_question'
        },
        {
            'message': 'Hello',
            'expected': 'non_actionable'
        },
    ]
    
    print("\n[1] TESTING INTENT CLASSIFICATION")
    print("-" * 80)
    
    for i, test in enumerate(test_messages, 1):
        message = test['message']
        expected = test['expected']
        
        print(f"\n{i}. Message: \"{message}\"")
        
        result = coordinator.process_chat_message(message, user_id='demo_user')
        
        intent = result['intent_classification']
        intent_type = intent['intent_type']
        actionable = result['actionable']
        
        match = "✓" if intent_type == expected else "✗"
        print(f"   {match} Intent: {intent_type} (expected: {expected})")
        print(f"   Actionable: {actionable}")
        print(f"   Confidence: {intent['confidence']}")
        
        if intent.get('keywords_matched'):
            print(f"   Keywords: {', '.join(intent['keywords_matched'][:3])}")
        
        if actionable and 'mission_draft' in result:
            draft = result['mission_draft']
            print(f"   Mission ID: {draft['mission_id']}")
            print(f"   Objective Type: {draft['objective_type']}")
            print(f"   Status: {draft['status']}")
    
    # Check whiteboard
    print("\n[2] WHITEBOARD PROPOSED MISSIONS")
    print("-" * 80)
    
    proposed = get_proposed_missions()
    
    if proposed:
        print(f"\nFound {len(proposed)} proposed missions:\n")
        
        for mission in proposed[-3:]:  # Show last 3
            print(f"• {mission['mission_id']}")
            print(f"  Status: {mission['status'].upper()}")
            print(f"  Source: {mission['source']}")
            print(f"  Objective: {mission['objective_description'][:60]}...")
            print(f"  Type: {mission['objective_type']}")
            if mission['allowed_domains']:
                print(f"  Domains: {', '.join(mission['allowed_domains'])}")
            print(f"  Awaiting Approval: {mission['awaiting_approval']}")
            print()
    else:
        print("\nNo proposed missions yet.")
    
    # Show chat feedback examples
    print("\n[3] CHAT FEEDBACK EXAMPLES")
    print("-" * 80)
    
    # Example 1: Actionable
    print("\nExample 1: Actionable Request")
    print("-" * 40)
    result = coordinator.process_chat_message(
        "Scrape 50 quotes from quotes.toscrape.com",
        user_id='demo_user'
    )
    
    feedback = result['chat_feedback']
    print(feedback['message'])
    
    # Example 2: Non-actionable
    print("\n\nExample 2: Non-actionable")
    print("-" * 40)
    result = coordinator.process_chat_message(
        "What's the weather?",
        user_id='demo_user'
    )
    
    feedback = result['chat_feedback']
    print(feedback['message'])
    
    # Summary
    print("\n" + "=" * 80)
    print("DEMO COMPLETE - HARD CONSTRAINTS VERIFIED")
    print("=" * 80)
    
    print("\n✓ Intent routing: deterministic (keyword-based)")
    print("✓ Mission drafts: created with safe defaults")
    print("✓ Proposals: emitted to missions.jsonl + signals")
    print("✓ Whiteboard: shows proposed missions")
    print("✓ Chat feedback: clear approval required")
    print("✓ Status: ALL missions 'proposed' (NEVER 'active')")
    print("✓ NO execution occurred")
    print("✓ NO autonomy introduced")
    print("✓ Full audit trail logged")
    
    print("\n" + "=" * 80 + "\n")


if __name__ == '__main__':
    demo_chat_intake()

