"""Debug email connection."""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Load .env
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                try:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
                except:
                    pass

print("Email address:", os.getenv("BUDDY_EMAIL_ADDRESS"))
print("IMAP host:", os.getenv("BUDDY_EMAIL_IMAP_HOST"))
print("IMAP port:", os.getenv("BUDDY_EMAIL_IMAP_PORT"))
print("App password set:", bool(os.getenv("BUDDY_EMAIL_APP_PASSWORD")))
print("App password length:", len(os.getenv("BUDDY_EMAIL_APP_PASSWORD", "")))

# Try connection
import imaplib
try:
    print("\nAttempting IMAP connection...")
    imap = imaplib.IMAP4_SSL(
        os.getenv("BUDDY_EMAIL_IMAP_HOST"),
        int(os.getenv("BUDDY_EMAIL_IMAP_PORT"))
    )
    print("Connection established, attempting login...")
    imap.login(
        os.getenv("BUDDY_EMAIL_ADDRESS"),
        os.getenv("BUDDY_EMAIL_APP_PASSWORD")
    )
    print("✓ Login successful!")
    imap.logout()
except Exception as e:
    print("✗ Connection/Login failed:", e)

