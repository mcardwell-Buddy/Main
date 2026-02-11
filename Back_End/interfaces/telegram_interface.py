"""Telegram interface for Buddy (Bot API adapter)."""

from __future__ import annotations

import json
import logging
import os
import time
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List

from Back_End.buddy_core import handle_user_message

logger = logging.getLogger(__name__)


@dataclass
class TelegramConfig:
    bot_token: str
    allowed_user_id: str


class TelegramInterface:
    """Telegram bot adapter for incoming/outgoing message events."""

    def __init__(self, output_dir: Optional[Path] = None) -> None:
        self.output_dir = output_dir or (Path(__file__).parent.parent / "outputs" / "phase25")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.events_path = self.output_dir / "telegram_events.jsonl"
        self.config = self._load_config()

    def _load_config(self) -> TelegramConfig:
        return TelegramConfig(
            bot_token=os.getenv("BUDDY_TELEGRAM_BOT_TOKEN", ""),
            allowed_user_id=os.getenv("BUDDY_TELEGRAM_ALLOWED_USER_ID", ""),
        )

    def _log_event(self, event: Dict[str, Any]) -> None:
        try:
            with self.events_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(event) + "\n")
        except Exception as exc:
            logger.warning("Failed to log telegram event: %s", exc)

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def handle_update(self, update: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Normalize an incoming update into an event. Returns event or None."""
        message = update.get("message") or update.get("edited_message")
        if not message:
            return None

        user_id = str(message.get("from", {}).get("id", ""))
        if not self._is_allowed_user(user_id):
            return None

        text = message.get("text", "")
        timestamp = self._now_iso()

        event = {
            "event_type": "telegram_message",
            "event_category": "conversation",
            "direction": "incoming",
            "user_id": user_id,
            "timestamp": timestamp,
            "text": text,
            "source": "telegram",
        }

        self._log_event(event)
        return event

    def send_message(self, user_id: str, text: str) -> bool:
        """Send a Telegram message to a user. Logs outgoing event."""
        if not self._has_config():
            logger.warning("Telegram config missing; send aborted.")
            return False

        payload = json.dumps({"chat_id": user_id, "text": text}).encode("utf-8")
        url = f"https://api.telegram.org/bot{self.config.bot_token}/sendMessage"

        try:
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                if resp.status != 200:
                    return False
                _ = resp.read()

            event = {
                "event_type": "telegram_message",
                "event_category": "conversation",
                "direction": "outgoing",
                "user_id": str(user_id),
                "timestamp": self._now_iso(),
                "text": text,
                "source": "telegram",
            }
            self._log_event(event)
            return True
        except Exception as exc:
            logger.warning("Telegram send failed: %s", exc)
            return False

    def process_update(self, update: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a Telegram update by forwarding to Buddy Core and sending response.

        Telegram remains a pure I/O adapter: it validates the user, logs the
        inbound message, forwards it to Buddy Core, and sends the response verbatim.
        """
        event = self.handle_update(update)
        if not event:
            return None

        user_id = event.get("user_id")
        text = event.get("text", "")
        response = handle_user_message(
            source="telegram",
            text=text,
            external_user_id=user_id,
        )
        if user_id and response:
            response_text = response.get("response") if isinstance(response, dict) else str(response)
            if response_text:
                self.send_message(user_id=user_id, text=response_text)
        return event

    def poll_updates(self, offset: Optional[int] = None, timeout: int = 15) -> List[Dict[str, Any]]:
        """Fetch updates from Telegram and normalize allowed user messages."""
        if not self._has_config():
            logger.warning("Telegram config missing; poll aborted.")
            return []

        params = {"timeout": timeout}
        if offset is not None:
            params["offset"] = offset

        query = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"https://api.telegram.org/bot{self.config.bot_token}/getUpdates?{query}"

        try:
            with urllib.request.urlopen(url, timeout=timeout + 5) as resp:
                if resp.status != 200:
                    return []
                data = json.loads(resp.read().decode("utf-8"))

            updates = data.get("result", [])
            events: List[Dict[str, Any]] = []
            for update in updates:
                event = self.handle_update(update)
                if event:
                    events.append(event)
            return events
        except Exception as exc:
            logger.warning("Telegram poll failed: %s", exc)
            return []

    def _is_allowed_user(self, user_id: str) -> bool:
        return bool(self.config.allowed_user_id) and user_id == str(self.config.allowed_user_id)

    def _has_config(self) -> bool:
        return bool(self.config.bot_token and self.config.allowed_user_id)

