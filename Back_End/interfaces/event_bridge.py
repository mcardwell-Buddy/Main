"""Read-only event bridge for email and Telegram events."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class EventBridge:
    """Loads recent events from email and telegram JSONL logs."""

    def __init__(
        self,
        email_events_path: Optional[Path] = None,
        telegram_events_path: Optional[Path] = None,
    ) -> None:
        base_dir = Path(__file__).parent.parent / "outputs" / "phase25"
        self.email_events_path = email_events_path or (base_dir / "email_events.jsonl")
        self.telegram_events_path = telegram_events_path or (base_dir / "telegram_events.jsonl")

    def get_recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Load recent events from both sources (read-only)."""
        events: List[Dict[str, Any]] = []

        events.extend(self._load_events(self.email_events_path, source="email"))
        events.extend(self._load_events(self.telegram_events_path, source="telegram"))

        if limit <= 0:
            return []
        return events[-limit:]

    def _load_events(self, path: Path, source: str) -> List[Dict[str, Any]]:
        if not path.exists():
            return []

        output: List[Dict[str, Any]] = []
        try:
            with path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        raw = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    event = {
                        "source": source,
                        "event_type": raw.get("event_type", ""),
                        "timestamp": raw.get("timestamp", self._now_iso()),
                        "payload": raw,
                    }
                    output.append(event)
        except Exception as exc:
            logger.warning("Failed to read events from %s: %s", path, exc)

        return output

    def _now_iso(self) -> str:
        return datetime.utcnow().isoformat() + "Z"

