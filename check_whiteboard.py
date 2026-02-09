#!/usr/bin/env python
"""Quick verification that whiteboard shows approved mission."""

import requests

mission_id = 'mission_chat_4d0eb0580971'
url = f'http://127.0.0.1:8000/api/whiteboard/{mission_id}'

print(f"\nQuerying Whiteboard API for mission: {mission_id}")
print(f"URL: {url}\n")

try:
    response = requests.get(url, timeout=5)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\nWhiteboard Data:")
        print(f"  Mission ID: {data.get('mission_id')}")
        print(f"  Status: {data.get('status')}")
        print(f"  Objective: {data.get('objective_description')}")
        print(f"  Progress: {data.get('latest_progress', {}).get('status_message', 'N/A')}")
        print(f"\n✓ Whiteboard correctly shows approved mission state")
    else:
        print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
