"""Live smoke test for Telegram interface (polling + ACK reply)."""

import json
import logging
import os
import signal
import time
import urllib.request

from Back_End.interfaces.telegram_interface import TelegramInterface

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

SHUTDOWN = False


def _handle_sigint(_signum, _frame):
    global SHUTDOWN
    SHUTDOWN = True
    logger.info("Shutdown requested. Exiting...")


def _get_updates_raw(bot_token: str, offset: int | None, timeout: int = 20):
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


def main() -> None:
    signal.signal(signal.SIGINT, _handle_sigint)

    telegram = TelegramInterface()
    bot_token = os.getenv("BUDDY_TELEGRAM_BOT_TOKEN", "")

    if not bot_token:
        logger.warning("BUDDY_TELEGRAM_BOT_TOKEN not set; exiting.")
        return

    logger.info("Starting Telegram polling. Press CTRL+C to stop.")

    offset = None
    while not SHUTDOWN:
        try:
            updates = _get_updates_raw(bot_token, offset=offset, timeout=20)
            for update in updates:
                update_id = update.get("update_id")
                if update_id is not None:
                    offset = update_id + 1

                event = telegram.handle_update(update)
                if not event:
                    continue

                user_id = event.get("user_id")
                if user_id:
                    telegram.send_message(
                        user_id=user_id,
                        text="Buddy received your message and is online.",
                    )
        except Exception as exc:
            logger.warning("Telegram polling error: %s", exc)
            time.sleep(2)

    logger.info("Telegram validation stopped.")


if __name__ == "__main__":
    main()

