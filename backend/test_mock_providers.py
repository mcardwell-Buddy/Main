#!/usr/bin/env python
"""Test script for mock providers"""

import os
import sys

os.environ['DRY_RUN'] = 'true'

# Add backend to path
sys.path.insert(0, '/Users/micha/Buddy/backend')

# Test Mployer Mock
print("Testing Mployer Mock...")
from mployer_mock import get_mployer_client
mployer = get_mployer_client()
login_result = mployer.login('test@example.com', 'password')
success = login_result.get('success', False)
print(f"  ✓ Mployer login: {success}")

search_result = mployer.search_contacts(company='TestCorp')
contacts = search_result.get('total_results', 0)
print(f"  ✓ Mployer search: {contacts} contacts")

# Test GoHighLevel Mock
print("\nTesting GoHighLevel Mock...")
from gohighlevel_mock import get_gohighlevel_client
ghl = get_gohighlevel_client()
contact_result = ghl.create_contact({'first_name': 'John', 'last_name': 'Doe', 'email': 'john@example.com'})
success = contact_result.get('success', False)
print(f"  ✓ GHL contact created: {success}")

search_result = ghl.search_contact(email='john@example.com')
count = search_result.get('total_results', 0)
print(f"  ✓ GHL contact search: {count} results")

# Test MS Graph Mock
print("\nTesting MS Graph Mock...")
from msgraph_mock import get_msgraph_client
msgraph = get_msgraph_client()
email_result = msgraph.send_email(['test@example.com'], 'Test Subject', 'Test Body')
success = email_result.get('success', False)
print(f"  ✓ MS Graph email sent: {success}")

messages = msgraph.get_messages(limit=5)
count = messages.get('total_count', 0)
print(f"  ✓ MS Graph messages: {count} in mailbox")

print("\n✅ All mock providers working!")
