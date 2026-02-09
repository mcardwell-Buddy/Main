"""Test MFA code retrieval from email"""
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

from backend.msgraph_email import get_mfa_code_from_msgraph

print('Testing MFA code retrieval from Microsoft Graph...\n')

code = get_mfa_code_from_msgraph(from_sender="mployeradvisor", max_wait=10)

if code:
    print(f"✓ Successfully retrieved MFA code: {code}")
else:
    print("✗ Could not find MFA code in recent emails")
