"""Live smoke test for Yahoo Email interface (read-only)."""

import logging
from typing import List

from Back_End.interfaces.email_interface import EmailInterface

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def _print_summary(events: List[dict]) -> None:
    logger.info("Emails fetched: %d", len(events))
    for idx, event in enumerate(events, 1):
        subject = event.get("subject", "")
        logger.info("  %d) %s", idx, subject)


def main() -> None:
    logger.info("Starting Yahoo email validation (read-only).")
    try:
        email = EmailInterface()
        events = email.fetch_unread_emails()
        _print_summary(events)
    except Exception as exc:
        logger.warning("Email validation failed: %s", exc)


if __name__ == "__main__":
    main()

