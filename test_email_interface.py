import os
import unittest
from unittest import mock
from pathlib import Path
import tempfile
from email.message import EmailMessage

from Back_End.interfaces.email_interface import EmailInterface


class TestEmailInterface(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temp_dir.name)

        os.environ["BUDDY_EMAIL_ADDRESS"] = "buddy@example.com"
        os.environ["BUDDY_EMAIL_IMAP_HOST"] = "imap.mail.yahoo.com"
        os.environ["BUDDY_EMAIL_IMAP_PORT"] = "993"
        os.environ["BUDDY_EMAIL_SMTP_HOST"] = "smtp.mail.yahoo.com"
        os.environ["BUDDY_EMAIL_SMTP_PORT"] = "587"
        os.environ["BUDDY_EMAIL_APP_PASSWORD"] = "app-password"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    @mock.patch("imaplib.IMAP4_SSL")
    def test_fetch_unread_emails(self, mock_imap):
        msg = EmailMessage()
        msg["Subject"] = "Test Subject"
        msg["From"] = "sender@example.com"
        msg["To"] = "buddy@example.com"
        msg["Message-ID"] = "<msg-1>"
        msg.set_content("Hello Buddy")

        instance = mock_imap.return_value.__enter__.return_value
        instance.login.return_value = ("OK", [])
        instance.select.return_value = ("OK", [])
        instance.search.return_value = ("OK", [b"1"])
        instance.fetch.return_value = ("OK", [(b"1", msg.as_bytes())])

        interface = EmailInterface(output_dir=self.output_dir)
        events = interface.fetch_unread_emails()

        self.assertEqual(len(events), 1)
        event = events[0]
        self.assertEqual(event["event_type"], "email_received")
        self.assertEqual(event["subject"], "Test Subject")
        self.assertEqual(event["from"], "sender@example.com")

    @mock.patch("smtplib.SMTP")
    def test_send_email_requires_approval(self, mock_smtp):
        interface = EmailInterface(output_dir=self.output_dir)
        sent = interface.send_email("to@example.com", "Hello", "Body", approval_flag=False)
        self.assertFalse(sent)
        mock_smtp.assert_not_called()

    @mock.patch("smtplib.SMTP")
    def test_send_email_with_approval(self, mock_smtp):
        smtp_instance = mock_smtp.return_value.__enter__.return_value
        smtp_instance.sendmail.return_value = {}

        interface = EmailInterface(output_dir=self.output_dir)
        sent = interface.send_email("to@example.com", "Hello", "Body", approval_flag=True)
        self.assertTrue(sent)
        mock_smtp.assert_called_once()


if __name__ == "__main__":
    unittest.main()

