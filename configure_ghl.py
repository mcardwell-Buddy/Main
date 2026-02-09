"""
Quick script to configure GoHighLevel with your API token
"""

import requests
import json

# Your GHL credentials
GHL_API_TOKEN = "pit-2a219967-29e8-4ea7-97ce-ea515b04e90a"  # Replace with your actual token
GHL_LOCATION_ID = "YOUR_LOCATION_ID"   # Optional, replace if you have one

# Configure Buddy
response = requests.post(
    "http://localhost:8000/ghl/configure",
    json={
        "api_token": GHL_API_TOKEN,
        "location_id": GHL_LOCATION_ID if GHL_LOCATION_ID != "YOUR_LOCATION_ID" else None
    }
)

print("Configuration Response:")
print(json.dumps(response.json(), indent=2))

# Check status
status = requests.get("http://localhost:8000/ghl/status")
print("\nStatus Check:")
print(json.dumps(status.json(), indent=2))

if status.json().get("configured"):
    print("\n✅ GoHighLevel is configured and ready!")
    print("\nYou can now ask Buddy things like:")
    print('  - "Find HR managers at tech companies and add to my CRM"')
    print('  - "Add John Smith from Acme Corp to GoHighLevel"')
    print('  - "Search my CRM for contacts at TechCorp"')
else:
    print("\n❌ Configuration failed. Check your API token.")
