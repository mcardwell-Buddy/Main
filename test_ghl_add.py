"""
Test adding a contact to GoHighLevel
"""

import sys
sys.path.insert(0, 'C:/Users/micha/Buddy')

from Back_End.gohighlevel_client import initialize_ghl
from Back_End.gohighlevel_tools import ghl_add_contact
import json

# Initialize GHL with your token and location
GHL_TOKEN = "pit-2a219967-29e8-4ea7-97ce-ea515b04e90a"
GHL_LOCATION = "Sx0HPSELq34BoxUt5OF9"
initialize_ghl(GHL_TOKEN, GHL_LOCATION)

# Test contact data - simplified for API v2
import time
test_contact = {
    "firstName": "Buddy",
    "lastName": "Test",
    "email": f"buddy.test.{int(time.time())}@example.com",
    "locationId": GHL_LOCATION
}

print("Testing GHL contact creation...")
print(f"Contact: {test_contact['firstName']} {test_contact['lastName']}")
print(f"Email: {test_contact['email']}")
print()

result = ghl_add_contact(json.dumps(test_contact))

print("Result:")
print(json.dumps(result, indent=2))

if result.get("status") == "success":
    print(f"\n✅ SUCCESS! Contact ID: {result.get('contact_id')}")
    print("Check your GoHighLevel CRM to see the new contact!")
else:
    print(f"\n❌ FAILED: {result.get('message', 'Unknown error')}")

