"""Email validation runner with .env loader."""
import sys
import os
from pathlib import Path

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
from backend.interfaces.email_interface import EmailInterface

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

logger.info("Starting Yahoo email validation (read-only).")
try:
    email = EmailInterface()
    events = email.fetch_unread_emails()
    logger.info("Emails fetched: %d", len(events))
    for idx, event in enumerate(events, 1):
        subject = event.get("subject", "")
        logger.info("  %d) %s", idx, subject)
except Exception as exc:
    logger.warning("Email validation failed: %s", exc)
