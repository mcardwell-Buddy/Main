"""Telegram test - simple."""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Load .env properly
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

print("Bot token set:", bool(os.getenv("BUDDY_TELEGRAM_BOT_TOKEN")))
print("User ID set:", bool(os.getenv("BUDDY_TELEGRAM_ALLOWED_USER_ID")))

if os.getenv("BUDDY_TELEGRAM_BOT_TOKEN"):
    print("Token prefix:", os.getenv("BUDDY_TELEGRAM_BOT_TOKEN")[:20])

