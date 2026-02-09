"""Quick config test."""
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
                key, value = line.split('=', 1)
                os.environ[key] = value

from backend.interfaces.telegram_interface import TelegramInterface
from backend.interfaces.email_interface import EmailInterface

telegram = TelegramInterface()
email = EmailInterface()

print("Telegram config loaded:", bool(telegram.config.bot_token and telegram.config.allowed_user_id))
print("Email config loaded:", bool(email.creds.address and email.creds.app_password))
