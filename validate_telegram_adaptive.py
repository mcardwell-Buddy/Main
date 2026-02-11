"""Telegram validation mode - adaptive response testing."""
import sys
import os
from pathlib import Path
import signal
import time
import json
import urllib.request
import logging

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

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

from Back_End.interfaces.telegram_interface import TelegramInterface

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
allowed_user = os.getenv("BUDDY_TELEGRAM_ALLOWED_USER_ID", "")

if not bot_token:
    logger.error("BUDDY_TELEGRAM_BOT_TOKEN not set; exiting.")
    sys.exit(1)

if not allowed_user:
    logger.error("BUDDY_TELEGRAM_ALLOWED_USER_ID not set; exiting.")
    sys.exit(1)

logger.info("=" * 70)
logger.info("TELEGRAM VALIDATION MODE - ADAPTIVE RESPONSE TEST")
logger.info("=" * 70)
logger.info("Bot token: %s", bot_token[:20] + "...")
logger.info("Allowed user ID: %s", allowed_user)
logger.info("")
logger.info("Waiting for messages from allowed user...")
logger.info("Buddy will respond with adaptive lengths per intent:")
logger.info("  - conversation     -> 2-5 sentences, natural & friendly")
logger.info("  - status_request   -> 3-5 sentences, brief summary")
logger.info("  - reflection       -> 3-5 sentences, thoughtful insights")
logger.info("  - exploration      -> 4-6 sentences + follow-up question")
logger.info("  - potential_action -> 2-4 sentences + approval note")
logger.info("")
logger.info("Press CTRL+C to stop.")
logger.info("=" * 70)

offset = None
message_count = 0

while not SHUTDOWN:
    try:
        updates = _get_updates_raw(bot_token, offset=offset, timeout=20)
        for update in updates:
            update_id = update.get("update_id")
            if update_id is not None:
                offset = update_id + 1

            event = telegram.process_update(update)
            if not event:
                # Message from unauthorized user - silently skip
                if update.get("message"):
                    unauthorized_user = str(update["message"].get("from", {}).get("id", "unknown"))
                    logger.warning("Message from unauthorized user %s (ignored)", unauthorized_user)
                continue

            # Authorized message received
            user_id = event.get("user_id")
            text = event.get("text", "")
            message_count += 1

            logger.info("[%d] Inbound: user=%s, text='%s'", message_count, user_id, text)
            logger.info("[%d] Outbound: user=%s, reply sent", message_count, user_id)

    except Exception as exc:
        logger.warning("Polling error: %s", exc)
        time.sleep(2)

logger.info("")
logger.info("=" * 70)
logger.info("Telegram validation stopped.")
logger.info("Total messages processed: %d", message_count)
logger.info("=" * 70)

