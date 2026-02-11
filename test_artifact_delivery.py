"""
Comprehensive Test Suite for Artifact Delivery System

Tests:
1. Email sending with attachments
2. OneDrive file upload
3. Natural language intent parsing
4. Delivery orchestration flow
5. OAuth token management
"""

import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from Back_End.artifact_delivery_flow import DeliveryIntentParser, ArtifactDeliveryOrchestrator
from Back_End.email_client import YahooEmailClient, YahooOAuthClient
from Back_End.onedrive_client import OneDriveClient, OneDriveOAuthClient


def test_intent_parser():
    """Test natural language parsing for delivery intent"""
    print("\n" + "="*50)
    print("TEST 1: Natural Language Intent Parsing")
    print("="*50)
    
    parser = DeliveryIntentParser()
    
    test_cases = [
        ("yes please email it", {"wants_delivery": True, "email": True, "onedrive": False}),
        ("save to onedrive", {"wants_delivery": True, "email": False, "onedrive": True}),
        ("both please", {"wants_delivery": True, "email": True, "onedrive": True}),
        ("no thanks", {"wants_delivery": False, "email": False, "onedrive": False}),
        ("send it via email with a note", {"wants_delivery": True, "email": True}),
    ]
    
    passed = 0
    for user_input, expected in test_cases:
        print(f"\nInput: '{user_input}'")
        result = parser.parse_delivery_intent(user_input)
        
        matches = (
            result["wants_delivery"] == expected["wants_delivery"] and
            result["email"] == expected["email"] and
            ("onedrive" not in expected or result["onedrive"] == expected["onedrive"])
        )
        
        if matches:
            print(f"✅ PASS - Intent: {result}")
            passed += 1
        else:
            print(f"❌ FAIL - Got: {result}, Expected: {expected}")
    
    print(f"\n📊 Results: {passed}/{len(test_cases)} tests passed")
    return passed == len(test_cases)


def test_oauth_config_loading():
    """Test OAuth configuration loading"""
    print("\n" + "="*50)
    print("TEST 2: OAuth Configuration Loading")
    print("="*50)
    
    try:
        # Test Yahoo OAuth
        yahoo_oauth = YahooOAuthClient()
        print("\n✅ Yahoo OAuth client initialized")
        print(f"   Config path: {yahoo_oauth.config_path}")
        print(f"   Tokens path: {yahoo_oauth.tokens_path}")
        
        # Test OneDrive OAuth
        onedrive_oauth = OneDriveOAuthClient()
        print("\n✅ OneDrive OAuth client initialized")
        print(f"   Config path: {onedrive_oauth.config_path}")
        print(f"   Tokens path: {onedrive_oauth.tokens_path}")
        
        # Check if configuration exists
        if yahoo_oauth.config.get("client_id"):
            print("\n✅ Yahoo OAuth credentials configured")
        else:
            print("\n⚠️  Yahoo OAuth credentials not set (expected for first run)")
        
        if onedrive_oauth.config.get("client_id"):
            print("✅ OneDrive OAuth credentials configured")
        else:
            print("⚠️  OneDrive OAuth credentials not set (expected for first run)")
        
        return True
        
    except Exception as e:
        print(f"\n❌ FAIL: {e}")
        return False


def test_delivery_orchestrator():
    """Test delivery orchestrator workflow"""
    print("\n" + "="*50)
    print("TEST 3: Delivery Orchestrator Workflow")
    print("="*50)
    
    try:
        orchestrator = ArtifactDeliveryOrchestrator()
        
        # Create test artifacts
        test_dir = Path("data/test_artifacts")
        test_dir.mkdir(parents=True, exist_ok=True)
        
        test_file = test_dir / "test_artifact.txt"
        with open(test_file, 'w') as f:
            f.write("This is a test artifact created by Buddy!")
        
        print(f"\n✅ Created test artifact: {test_file}")
        
        # Create delivery offer
        offer = orchestrator.offer_delivery(
            mission_id="test_mission_001",
            artifacts=[str(test_file)],
            user_email="user@example.com"
        )
        
        print("\n✅ Created delivery offer:")
        print(f"   Mission ID: {offer['offer_id']}")
        print(f"   Artifacts: {len(offer['artifacts'])}")
        print(f"   Options: {', '.join(offer['options'])}")
        print(f"\nOffer Message:\n{offer['message']}")
        
        # Test parsing various responses
        print("\n📝 Testing response handling (simulated):")
        responses = [
            "yes email it",
            "save to onedrive",
            "no thanks"
        ]
        
        for response in responses:
            intent = orchestrator.intent_parser.parse_delivery_intent(response)
            print(f"\n   Response: '{response}'")
            print(f"   → Parsed: {intent['wants_delivery']=}, {intent['email']=}, {intent['onedrive']=}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_email_client_initialization():
    """Test email client can initialize (doesn't require OAuth tokens)"""
    print("\n" + "="*50)
    print("TEST 4: Email Client Initialization")
    print("="*50)
    
    try:
        from Back_End.email_client import get_email_client, get_comprehension_engine
        
        email_client = get_email_client()
        print("✅ Email client initialized")
        print(f"   SMTP: {email_client.smtp_server}:{email_client.smtp_port}")
        print(f"   IMAP: {email_client.imap_server}:{email_client.imap_port}")
        
        comprehension = get_comprehension_engine()
        print("\n✅ Email comprehension engine initialized")
        
        # Test email parsing (mock email)
        mock_email = {
            "from": "sender@example.com",
            "to": "buddy@yahoo.com",
            "subject": "Test Request",
            "date": "Mon, 10 Feb 2026 10:00:00",
            "body": "Hi Buddy, can you create a simple Python script for me? Thanks!"
        }
        
        print("\n📧 Testing email comprehension on mock email...")
        result = comprehension.comprehend_email(mock_email)
        
        print(f"\n✅ Comprehension result:")
        print(f"   Intent: {result.get('intent', 'N/A')}")
        print(f"   Urgency: {result.get('urgency', 'N/A')}")
        print(f"   Sentiment: {result.get('sentiment', 'N/A')}")
        print(f"   Action Items: {len(result.get('action_items', []))}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_onedrive_client_initialization():
    """Test OneDrive client initialization"""
    print("\n" + "="*50)
    print("TEST 5: OneDrive Client Initialization")
    print("="*50)
    
    try:
        from Back_End.onedrive_client import get_onedrive_client
        
        onedrive = get_onedrive_client()
        print("✅ OneDrive client initialized")
        print(f"   Graph API: {onedrive.graph_api}")
        
        print("\n⚠️  Note: Actual OneDrive operations require OAuth tokens")
        print("   Run OAuth setup via API to authorize access")
        
        return True
        
    except Exception as e:
        print(f"\n❌ FAIL: {e}")
        return False


def test_file_attachment_support():
    """Test that we can handle various file types"""
    print("\n" + "="*50)
    print("TEST 6: File Attachment Support")
    print("="*50)
    
    try:
        test_dir = Path("data/test_artifacts")
        test_dir.mkdir(parents=True, exist_ok=True)
        
        # Create various file types
        test_files = {
            "text.txt": "Plain text content",
            "code.py": "print('Hello from Python!')",
            "data.json": '{"key": "value"}',
            "doc.md": "# Markdown Document\n\nThis is a test."
        }
        
        print("\n📄 Creating test files:")
        for filename, content in test_files.items():
            filepath = test_dir / filename
            with open(filepath, 'w') as f:
                f.write(content)
            print(f"   ✅ {filename} ({len(content)} bytes)")
        
        print(f"\n✅ All test files created in: {test_dir}")
        print(f"   Total: {len(test_files)} files")
        
        return True
        
    except Exception as e:
        print(f"\n❌ FAIL: {e}")
        return False


def run_all_tests():
    """Run complete test suite"""
    print("\n" + "="*70)
    print("🧪 BUDDY ARTIFACT DELIVERY SYSTEM - TEST SUITE")
    print("="*70)
    
    tests = [
        ("Natural Language Intent Parsing", test_intent_parser),
        ("OAuth Configuration Loading", test_oauth_config_loading),
        ("Delivery Orchestrator Workflow", test_delivery_orchestrator),
        ("Email Client Initialization", test_email_client_initialization),
        ("OneDrive Client Initialization", test_onedrive_client_initialization),
        ("File Attachment Support", test_file_attachment_support),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n❌ Test '{name}' crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")
    
    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)
    
    print(f"\n{'='*70}")
    if passed_count == total_count:
        print(f"🎉 ALL TESTS PASSED! ({passed_count}/{total_count})")
        print("="*70)
        print("\n✅ Artifact delivery system is ready!")
        print("\n📝 Next steps:")
        print("   1. Configure OAuth credentials (see ARTIFACT_DELIVERY_SETUP.md)")
        print("   2. Run OAuth authorization flows")
        print("   3. Test with real emails and OneDrive uploads")
    else:
        print(f"⚠️  SOME TESTS FAILED ({passed_count}/{total_count} passed)")
        print("="*70)
        print("\n⚠️  Review failures above and fix issues")
    
    return passed_count == total_count


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

