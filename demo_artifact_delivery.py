"""
Demo: Buddy's Artifact Delivery System (No OAuth Required)

This demo shows how the natural language parsing and delivery orchestration work
WITHOUT actually sending emails or uploading to OneDrive (which require OAuth setup).

Perfect for understanding the flow before configuring OAuth credentials.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.artifact_delivery_flow import DeliveryIntentParser, ArtifactDeliveryOrchestrator


def demo_natural_language_parsing():
    """Demo: How Buddy understands user responses"""
    print("\n" + "="*70)
    print("🧠 DEMO: Natural Language Understanding")
    print("="*70)
    
    parser = DeliveryIntentParser()
    
    test_responses = [
        "yes please email it",
        "save to onedrive please",
        "both would be great",
        "send via email and also save to cloud",
        "no thanks, I'll get it later",
        "email it with a note saying this is the final version",
        "sure, onedrive is fine",
    ]
    
    print("\n📝 How Buddy interprets different user responses:\n")
    
    for response in test_responses:
        print(f"💬 User: '{response}'")
        
        intent = parser.parse_delivery_intent(response)
        
        print(f"   🤖 Buddy understands:")
        print(f"      • Wants delivery: {intent['wants_delivery']}")
        print(f"      • Email: {'✅ Yes' if intent['email'] else '❌ No'}")
        print(f"      • OneDrive: {'✅ Yes' if intent['onedrive'] else '❌ No'}")
        if intent['custom_message']:
            print(f"      • Custom message: \"{intent['custom_message']}\"")
        print(f"      • Confidence: {intent['confidence']*100:.0f}%")
        print()


def demo_delivery_offer():
    """Demo: What Buddy shows users after task completion"""
    print("\n" + "="*70)
    print("📦 DEMO: Delivery Offer After Task Completion")
    print("="*70)
    
    # Create test artifacts
    test_dir = Path("data/demo_artifacts")
    test_dir.mkdir(parents=True, exist_ok=True)
    
    test_files = [
        test_dir / "hello_world.py",
        test_dir / "readme.md",
        test_dir / "config.json"
    ]
    
    for file in test_files:
        with open(file, 'w') as f:
            f.write(f"Demo content for {file.name}")
    
    print("\n✅ Buddy just completed a task and created:")
    for file in test_files:
        print(f"   📄 {file.name}")
    
    # Create delivery offer
    orchestrator = ArtifactDeliveryOrchestrator()
    offer = orchestrator.offer_delivery(
        mission_id="demo_mission_001",
        artifacts=[str(f) for f in test_files],
        user_email="user@example.com"
    )
    
    print("\n" + "-"*70)
    print("🎯 Buddy presents this offer to you:")
    print("-"*70)
    print(offer["message"])
    print("-"*70)


def demo_full_workflow():
    """Demo: Complete workflow from offer to delivery"""
    print("\n" + "="*70)
    print("🎭 DEMO: Complete Delivery Workflow")
    print("="*70)
    
    # Setup
    orchestrator = ArtifactDeliveryOrchestrator()
    test_dir = Path("data/demo_artifacts")
    test_dir.mkdir(parents=True, exist_ok=True)
    
    test_file = test_dir / "awesome_script.py"
    with open(test_file, 'w') as f:
        f.write("print('Hello from Buddy!')")
    
    # Step 1: Task completes
    print("\n📋 STEP 1: Task Completes")
    print("   Buddy executed your request and created: awesome_script.py")
    
    # Step 2: Offer delivery
    print("\n📋 STEP 2: Buddy Offers Delivery")
    offer = orchestrator.offer_delivery(
        mission_id="demo_workflow",
        artifacts=[str(test_file)],
        user_email="user@example.com"
    )
    print(f"\n{offer['message']}\n")
    
    # Step 3: User responds
    print("📋 STEP 3: You Respond")
    user_response = "yes email it with a note saying this is version 2.0"
    print(f"   💬 You: '{user_response}'")
    
    # Step 4: Parse intent
    print("\n📋 STEP 4: Buddy Understands Your Intent")
    intent = orchestrator.intent_parser.parse_delivery_intent(user_response)
    print(f"   🤖 Parsed:")
    print(f"      • Wants delivery: ✅ Yes")
    print(f"      • Method: 📧 Email")
    print(f"      • Custom message: \"{intent['custom_message']}\"")
    
    # Step 5: Simulated delivery (no actual send without OAuth)
    print("\n📋 STEP 5: Buddy Would Execute Delivery")
    print("   (Simulated - requires OAuth configuration for actual delivery)")
    print("\n   Would send:")
    print(f"      To: user@example.com")
    print(f"      Subject: Buddy Built: awesome_script.py")
    print(f"      Body: {intent['custom_message']}")
    print(f"      Attachment: awesome_script.py")
    
    # Step 6: Confirmation
    print("\n📋 STEP 6: Buddy Confirms")
    print("   ✅ Email sent successfully!")
    print("   📧 Check your inbox for awesome_script.py")


def demo_email_comprehension():
    """Demo: How Buddy understands incoming emails"""
    print("\n" + "="*70)
    print("📧 DEMO: Email Comprehension")
    print("="*70)
    
    from backend.email_client import get_comprehension_engine
    
    engine = get_comprehension_engine()
    
    # Mock incoming email
    mock_email = {
        "from": "boss@company.com",
        "to": "buddy@yahoo.com",
        "subject": "URGENT: Need report by EOD",
        "date": "Mon, 10 Feb 2026 14:30:00",
        "body": """Hi Buddy,

Can you please create a sales report for Q4 2025? I need it by end of day today.

Include:
- Total revenue
- Top 5 customers
- Month-over-month growth

This is urgent for tomorrow's board meeting.

Thanks!
"""
    }
    
    print("\n📬 Incoming Email:")
    print(f"   From: {mock_email['from']}")
    print(f"   Subject: {mock_email['subject']}")
    print(f"   Date: {mock_email['date']}")
    print(f"\n   Body:\n{mock_email['body']}")
    
    print("\n🤖 Buddy's Comprehension:")
    comprehension = engine.comprehend_email(mock_email)
    
    print(f"\n   📌 Intent:")
    print(f"      {comprehension['intent']}")
    
    print(f"\n   📝 Action Items:")
    for item in comprehension['action_items']:
        print(f"      • {item}")
    
    print(f"\n   ⏰ Urgency: {comprehension['urgency']}")
    print(f"   😊 Sentiment: {comprehension['sentiment']}")
    
    if comprehension['questions']:
        print(f"\n   ❓ Questions Asked:")
        for q in comprehension['questions']:
            print(f"      • {q}")
    
    print(f"\n   💡 Suggested Response:")
    print(f"      {comprehension['suggested_response']}")


def main():
    """Run all demos"""
    print("\n" + "="*70)
    print("🎬 BUDDY ARTIFACT DELIVERY SYSTEM - INTERACTIVE DEMO")
    print("="*70)
    print("\nThis demo shows how Buddy's artifact delivery system works")
    print("WITHOUT requiring OAuth configuration.")
    print("\nYou'll see:")
    print("  1. Natural language understanding")
    print("  2. Delivery offer presentation")
    print("  3. Complete workflow simulation")
    print("  4. Email comprehension capabilities")
    
    input("\nPress Enter to start the demo...")
    
    # Run demos
    demo_natural_language_parsing()
    input("\nPress Enter to continue...")
    
    demo_delivery_offer()
    input("\nPress Enter to continue...")
    
    demo_full_workflow()
    input("\nPress Enter to continue...")
    
    demo_email_comprehension()
    
    # Summary
    print("\n" + "="*70)
    print("🎉 DEMO COMPLETE!")
    print("="*70)
    print("\n✅ You've seen how Buddy:")
    print("   • Understands natural language responses")
    print("   • Presents delivery offers professionally")
    print("   • Executes complete delivery workflows")
    print("   • Comprehends incoming email content")
    
    print("\n📝 Next Steps:")
    print("   1. Read ARTIFACT_DELIVERY_SETUP.md for OAuth configuration")
    print("   2. Set up Yahoo email credentials")
    print("   3. Set up Microsoft OneDrive credentials")
    print("   4. Run OAuth authorization flows")
    print("   5. Test with real emails and uploads!")
    
    print("\n📚 Documentation:")
    print("   • ARTIFACT_DELIVERY_IMPLEMENTATION.md - Full details")
    print("   • ARTIFACT_DELIVERY_SETUP.md - Setup guide")
    print("   • ARTIFACT_DELIVERY_QUICK_REFERENCE.md - Quick commands")
    
    print("\n🚀 Ready to configure OAuth? See ARTIFACT_DELIVERY_SETUP.md")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
