"""Test Microsoft Graph email retrieval"""
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

# Test Microsoft Graph
from backend.msgraph_email import MSGraphEmailClient

print('Testing Microsoft Graph API connection...')
print(f'Client ID: {os.getenv("MSGRAPH_CLIENT_ID")}')
print(f'Tenant ID: {os.getenv("MSGRAPH_TENANT_ID")}')
print(f'Email: {os.getenv("EMAIL_IMAP_USER")}')
print()

client = MSGraphEmailClient()
print('Attempting to get access token...')
token = client._get_access_token()

if token:
    print('✓ Successfully authenticated with Microsoft Graph!')
    print(f'Token length: {len(token)} characters')
    print()
    print('Testing email retrieval (looking for recent emails)...')
    code = client.get_mfa_code(from_sender='', max_wait=10)  # Empty sender to get any recent email
    if code:
        print(f'Found code: {code}')
    else:
        print('No matching emails found (this is expected if no recent MFA emails)')
else:
    print('✗ Failed to authenticate')
    print('Check your credentials in .env file')
