import unittest
import tempfile
from pathlib import Path
import json

from backend.interfaces.event_bridge import EventBridge


class TestEventBridge(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_path = Path(self.temp_dir.name)
        self.email_path = self.base_path / "email_events.jsonl"
        self.telegram_path = self.base_path / "telegram_events.jsonl"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _write_jsonl(self, path: Path, entries: list[dict]) -> None:
        with path.open("w", encoding="utf-8") as f:
            for entry in entries:
                f.write(json.dumps(entry) + "\n")

    def test_load_events_order_preserved(self):
        email_entries = [
            {"event_type": "email_received", "timestamp": "2026-02-06T10:00:00Z"},
            {"event_type": "email_received", "timestamp": "2026-02-06T10:01:00Z"},
        ]
        telegram_entries = [
            {"event_type": "telegram_message", "timestamp": "2026-02-06T10:02:00Z"},
        ]

        self._write_jsonl(self.email_path, email_entries)
        self._write_jsonl(self.telegram_path, telegram_entries)

        bridge = EventBridge(self.email_path, self.telegram_path)
        events = bridge.get_recent_events(limit=10)

        self.assertEqual(len(events), 3)
        self.assertEqual(events[0]["payload"]["event_type"], "email_received")
        self.assertEqual(events[1]["payload"]["event_type"], "email_received")
        self.assertEqual(events[2]["payload"]["event_type"], "telegram_message")

    def test_empty_files_no_crash(self):
        self.email_path.write_text("", encoding="utf-8")
        self.telegram_path.write_text("", encoding="utf-8")

        bridge = EventBridge(self.email_path, self.telegram_path)
        events = bridge.get_recent_events(limit=50)
        self.assertEqual(events, [])

    def test_missing_files_no_crash(self):
        bridge = EventBridge(self.email_path, self.telegram_path)
        events = bridge.get_recent_events(limit=50)
        self.assertEqual(events, [])


if __name__ == "__main__":
    unittest.main()
