"""Email interface for Buddy (Yahoo IMAP/SMTP adapter).

Read-only by default. Sending requires explicit approval flag.
"""

from __future__ import annotations

import imaplib
import json
import logging
import os
import smtplib
from dataclasses import dataclass
from datetime import datetime, timezone
from email import message_from_bytes
from email.message import Message
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)


@dataclass
class EmailCredentials:
    address: str
    imap_host: str
    imap_port: int
    smtp_host: str
    smtp_port: int
    app_password: str


class EmailInterface:
    """Yahoo email adapter (IMAP read, SMTP send with approval gate)."""

    def __init__(self, output_dir: Optional[Path] = None) -> None:
        self.output_dir = output_dir or (Path(__file__).parent.parent / "outputs" / "phase25")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.events_path = self.output_dir / "email_events.jsonl"
        self.creds = self._load_credentials()

    def _load_credentials(self) -> EmailCredentials:
        """Load credentials from environment variables."""
        return EmailCredentials(
            address=os.getenv("BUDDY_EMAIL_ADDRESS", ""),
            imap_host=os.getenv("BUDDY_EMAIL_IMAP_HOST", ""),
            imap_port=int(os.getenv("BUDDY_EMAIL_IMAP_PORT", "0") or 0),
            smtp_host=os.getenv("BUDDY_EMAIL_SMTP_HOST", ""),
            smtp_port=int(os.getenv("BUDDY_EMAIL_SMTP_PORT", "0") or 0),
            app_password=os.getenv("BUDDY_EMAIL_APP_PASSWORD", ""),
        )

    def _log_event(self, event: Dict[str, Any]) -> None:
        """Append event to JSONL log. Never raise."""
        try:
            with self.events_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(event) + "\n")
        except Exception as exc:
            logger.warning("Failed to log email event: %s", exc)

    def _normalize_message(self, msg: Message) -> Dict[str, Any]:
        """Normalize email message to event schema."""
        subject = msg.get("Subject", "")
        from_addr = msg.get("From", "")
        to_addr = msg.get("To", "")
        message_id = msg.get("Message-ID", "")

        timestamp = self._safe_timestamp(msg)
        body_preview, attachments = self._extract_body_preview(msg)

        return {
            "event_type": "email_received",
            "message_id": message_id,
            "from": from_addr,
            "to": to_addr,
            "subject": subject,
            "timestamp": timestamp,
            "body_preview": body_preview,
            "attachments": attachments,
            "source": "yahoo_mail",
        }

    def _safe_timestamp(self, msg: Message) -> str:
        raw_date = msg.get("Date")
        if not raw_date:
            return datetime.now(timezone.utc).isoformat()
        try:
            dt = parsedate_to_datetime(raw_date)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).isoformat()
        except Exception:
            return datetime.now(timezone.utc).isoformat()

    def _extract_body_preview(self, msg: Message) -> tuple[str, bool]:
        """Return text preview and attachments flag."""
        attachments = False
        preview = ""

        if msg.is_multipart():
            for part in msg.walk():
                content_disposition = (part.get("Content-Disposition") or "").lower()
                if "attachment" in content_disposition:
                    attachments = True
                content_type = part.get_content_type()
                if content_type == "text/plain" and not preview:
                    try:
                        payload = part.get_payload(decode=True) or b""
                        preview = payload.decode(part.get_content_charset() or "utf-8", errors="replace").strip()
                    except Exception:
                        preview = ""
        else:
            try:
                payload = msg.get_payload(decode=True) or b""
                preview = payload.decode(msg.get_content_charset() or "utf-8", errors="replace").strip()
            except Exception:
                preview = ""

        return preview[:200], attachments

    def fetch_unread_emails(self) -> List[Dict[str, Any]]:
        """Fetch unread emails via IMAP. Errors are swallowed and logged."""
        events: List[Dict[str, Any]] = []
        if not self._has_imap_config():
            logger.warning("Email IMAP config missing; skipping fetch.")
            return events

        try:
            with imaplib.IMAP4_SSL(self.creds.imap_host, self.creds.imap_port) as imap:
                imap.login(self.creds.address, self.creds.app_password)
                imap.select("INBOX")
                status, data = imap.search(None, "UNSEEN")
                if status != "OK":
                    return events

                message_ids = data[0].split()
                for msg_id in message_ids:
                    status, msg_data = imap.fetch(msg_id, "(RFC822)")
                    if status != "OK" or not msg_data:
                        continue
                    raw = msg_data[0][1]
                    msg = message_from_bytes(raw)
                    event = self._normalize_message(msg)
                    events.append(event)
                    self._log_event(event)
        except Exception as exc:
            logger.warning("IMAP fetch failed: %s", exc)

        return events

    def send_email(
        self,
        to_address: str,
        subject: str,
        body: str,
        approval_flag: bool = False,
    ) -> bool:
        """Send email via SMTP. Requires approval_flag=True."""
        if not approval_flag:
            logger.info("Email send blocked (approval_flag is False).")
            return False
        if not self._has_smtp_config():
            logger.warning("Email SMTP config missing; send aborted.")
            return False

        message = (
            f"From: {self.creds.address}\r\n"
            f"To: {to_address}\r\n"
            f"Subject: {subject}\r\n"
            f"\r\n{body}"
        )

        try:
            with smtplib.SMTP(self.creds.smtp_host, self.creds.smtp_port, timeout=15) as smtp:
                smtp.starttls()
                smtp.login(self.creds.address, self.creds.app_password)
                smtp.sendmail(self.creds.address, [to_address], message)

            event = {
                "event_type": "email_sent",
                "message_id": "",
                "from": self.creds.address,
                "to": to_address,
                "subject": subject,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "body_preview": body[:200],
                "attachments": False,
                "source": "yahoo_mail",
            }
            self._log_event(event)
            return True
        except Exception as exc:
            logger.warning("SMTP send failed: %s", exc)
            return False

    def _has_imap_config(self) -> bool:
        return all([
            self.creds.address,
            self.creds.imap_host,
            self.creds.imap_port,
            self.creds.app_password,
        ])

    def _has_smtp_config(self) -> bool:
        return all([
            self.creds.address,
            self.creds.smtp_host,
            self.creds.smtp_port,
            self.creds.app_password,
        ])
