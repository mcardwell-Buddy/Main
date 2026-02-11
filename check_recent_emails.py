"""Check recent emails to find MFA sender"""
import os
import sys
from pathlib import Path

# Load .env
env_path = Path('.env')
for line in env_path.read_text().splitlines():
    if not line or line.strip().startswith('#') or '=' not in line:
        continue
    k, v = line.split('=', 1)
    os.environ.setdefault(k.strip(), v.strip())

from Back_End.msgraph_email import MSGraphEmailClient

print('Checking recent emails to find MFA sender...\n')

client = MSGraphEmailClient()
token = client._get_access_token()

if token:
    import requests
    from datetime import datetime, timedelta
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Get last 10 emails
    cutoff_time = (datetime.utcnow() - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    user_endpoint = f"{client.graph_endpoint}/me/messages"
    params = {
        "$filter": f"receivedDateTime ge {cutoff_time}",
        "$orderby": "receivedDateTime DESC",
        "$top": 10,
        "$select": "subject,from,receivedDateTime,bodyPreview"
    }
    
    response = requests.get(user_endpoint, headers=headers, params=params)
    
    if response.status_code == 200:
        messages = response.json().get("value", [])
        print(f"Found {len(messages)} recent email(s):\n")
        
        for i, msg in enumerate(messages, 1):
            sender = msg.get("from", {}).get("emailAddress", {})
            sender_name = sender.get("name", "Unknown")
            sender_email = sender.get("address", "Unknown")
            subject = msg.get("subject", "No subject")
            preview = msg.get("bodyPreview", "")[:100]
            received = msg.get("receivedDateTime", "")
            
            print(f"{i}. From: {sender_name} <{sender_email}>")
            print(f"   Subject: {subject}")
            print(f"   Received: {received}")
            print(f"   Preview: {preview}...")
            print()
    else:
        print(f"Error: {response.status_code} - {response.text}")
else:
    print("Failed to authenticate")

