import os
import unittest
from unittest import mock
from pathlib import Path
import tempfile
import json

from Back_End.interfaces.telegram_interface import TelegramInterface


class TestTelegramInterface(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temp_dir.name)

        os.environ["BUDDY_TELEGRAM_BOT_TOKEN"] = "test-token"
        os.environ["BUDDY_TELEGRAM_ALLOWED_USER_ID"] = "12345"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_handle_update_allowed_user(self):
        interface = TelegramInterface(output_dir=self.output_dir)
        update = {
            "message": {
                "from": {"id": 12345},
                "text": "Hello",
            }
        }

        event = interface.handle_update(update)
        self.assertIsNotNone(event)
        self.assertEqual(event["direction"], "incoming")
        self.assertEqual(event["user_id"], "12345")
        self.assertEqual(event["text"], "Hello")

    def test_handle_update_blocked_user(self):
        interface = TelegramInterface(output_dir=self.output_dir)
        update = {
            "message": {
                "from": {"id": 99999},
                "text": "Hello",
            }
        }

        event = interface.handle_update(update)
        self.assertIsNone(event)

    @mock.patch("urllib.request.urlopen")
    def test_send_message(self, mock_urlopen):
        response = mock.MagicMock()
        response.status = 200
        response.read.return_value = json.dumps({"ok": True}).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = response

        interface = TelegramInterface(output_dir=self.output_dir)
        sent = interface.send_message("12345", "Hi")
        self.assertTrue(sent)


if __name__ == "__main__":
    unittest.main()

