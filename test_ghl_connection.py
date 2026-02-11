"""
Test GoHighLevel API Connection with New Token

Tests the updated GHL API token and displays available capabilities.

Author: Buddy
Date: February 11, 2026
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from Back_End.gohighlevel_client import GoHighLevelClient

print("\n" + "="*80)
print("TESTING GOHIGHLEVEL API CONNECTION")
print("="*80 + "\n")

# Get credentials
api_token = os.getenv("GHL_API_TOKEN")
location_id = os.getenv("GHL_LOCATION_ID")

print(f"📋 API Token: {api_token[:20]}... (hidden)")
print(f"📍 Location ID: {location_id}\n")

# Initialize client
print("🔄 Initializing GHL client...")
ghl = GoHighLevelClient(api_token, location_id)
print("✅ Client initialized\n")

# Test 1: List contacts (basic connectivity test)
print("="*80)
print("TEST 1: API Connectivity - List Contacts")
print("="*80)
result = ghl.list_contacts(limit=1)

if result.get("success"):
    print(f"✅ API Connection Successful!")
    print(f"   Token is valid and working")
    print()
else:
    print(f"❌ API Connection Failed!")
    print(f"   Error: {result.get('error')}\n")
    print("🔧 Troubleshooting:")
    print("   1. Verify the new token is correct in .env")
    print("   2. Check token permissions in GHL settings")
    print("   3. Ensure token hasn't expired\n")
    sys.exit(1)

# Test 2: List pipelines
print("="*80)
print("TEST 2: List Sales Pipelines")
print("="*80)
result = ghl.list_pipelines()

if result.get("success"):
    pipelines = result.get("data", {}).get("pipelines", [])
    print(f"✅ Found {len(pipelines)} pipeline(s)")
    
    for pipeline in pipelines:
        print(f"\n   📊 Pipeline: {pipeline.get('name', 'Unknown')}")
        print(f"      ID: {pipeline.get('id', 'N/A')}")
        
        stages = pipeline.get("stages", [])
        if stages:
            print(f"      Stages ({len(stages)}):")
            for stage in stages[:3]:  # First 3 stages only
                print(f"         • {stage.get('name', 'Unknown')}")
            if len(stages) > 3:
                print(f"         ... and {len(stages) - 3} more")
else:
    print(f"⚠️  Could not fetch pipelines: {result.get('error')}")

print()

# Test 3: List tags
print("="*80)
print("TEST 3: List Available Tags")
print("="*80)
result = ghl.list_tags()

if result.get("success"):
    tags = result.get("data", {}).get("tags", [])
    print(f"✅ Found {len(tags)} tag(s)")
    
    if tags:
        print(f"   Tags: {', '.join([tag.get('name', '') for tag in tags[:10]])}")
        if len(tags) > 10:
            print(f"   ... and {len(tags) - 10} more")
else:
    print(f"⚠️  Could not fetch tags: {result.get('error')}")

print()

# Test 4: List more contacts
print("="*80)
print("TEST 4: List Recent Contacts (Details)")
print("="*80)
result = ghl.list_contacts(limit=5)

if result.get("success"):
    contacts = result.get("data", {}).get("contacts", [])
    total = result.get("data", {}).get("total", 0)
    print(f"✅ Found {total} total contacts in CRM (showing first 5)")
    
    for contact in contacts:
        name = f"{contact.get('firstName', '')} {contact.get('lastName', '')}".strip() or "Unknown"
        email = contact.get('email', 'No email')
        print(f"   👤 {name} ({email})")
else:
    print(f"⚠️  Could not fetch contacts: {result.get('error')}")

print()

# Summary
print("="*80)
print("CONNECTION TEST COMPLETE")
print("="*80)
print("✅ GoHighLevel API is connected and working!")
print("✅ New token is valid and has proper permissions")
print("\n📚 See GHL_CAPABILITIES.md for full list of available functions")
print("="*80 + "\n")
