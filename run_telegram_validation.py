"""Telegram validation runner with .env loader."""
import sys
import os
from pathlib import Path
import signal
import time
import json
import urllib.request

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

# Run validation
import logging
from backend.interfaces.telegram_interface import TelegramInterface

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

SHUTDOWN = False

def _handle_sigint(_signum, _frame):
    global SHUTDOWN
    SHUTDOWN = True
    logger.info("Shutdown requested. Exiting...")

def _get_updates_raw(bot_token: str, offset, timeout: int = 20):
    params = {"timeout": timeout}
    if offset is not None:
        params["offset"] = offset
    query = "&".join(f"{k}={v}" for k, v in params.items())
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates?{query}"

    with urllib.request.urlopen(url, timeout=timeout + 5) as resp:
        if resp.status != 200:
            return []
        data = json.loads(resp.read().decode("utf-8"))
    return data.get("result", [])

signal.signal(signal.SIGINT, _handle_sigint)

telegram = TelegramInterface()
bot_token = os.getenv("BUDDY_TELEGRAM_BOT_TOKEN", "")

if not bot_token:
    logger.warning("BUDDY_TELEGRAM_BOT_TOKEN not set; exiting.")
    sys.exit(1)

logger.info("Starting Telegram polling. Press CTRL+C to stop.")
logger.info("Send a message from your allowed user to test.")

offset = None
while not SHUTDOWN:
    try:
        updates = _get_updates_raw(bot_token, offset=offset, timeout=20)
        for update in updates:
            update_id = update.get("update_id")
            if update_id is not None:
                offset = update_id + 1

            event = telegram.process_update(update)
            if not event:
                continue

            user_id = event.get("user_id")
            if user_id:
                logger.info("Message received from user %s: %s", user_id, event.get("text", ""))
                logger.info("Reply sent to user %s", user_id)
    except Exception as exc:
        logger.warning("Telegram polling error: %s", exc)
        time.sleep(2)

logger.info("Telegram validation stopped.")
