# Buddy Phase 2 - Communications Interfaces

**Status:** Interface adapters only (no decision-making or learning logic)

This document covers setup and usage for:
- Yahoo Email (IMAP read, SMTP send with approval gate)
- Telegram Bot (incoming/outgoing messages)

---

## Environment Variables

### Yahoo Email
Set these before running Buddy:

```
BUDDY_EMAIL_ADDRESS=your_address@yahoo.com
BUDDY_EMAIL_IMAP_HOST=imap.mail.yahoo.com
BUDDY_EMAIL_IMAP_PORT=993
BUDDY_EMAIL_SMTP_HOST=smtp.mail.yahoo.com
BUDDY_EMAIL_SMTP_PORT=587
BUDDY_EMAIL_APP_PASSWORD=your_app_password
```

> Use a Yahoo **App Password** (not your main account password).

### Telegram
```
BUDDY_TELEGRAM_BOT_TOKEN=123456789:ABCDEF-your-bot-token
BUDDY_TELEGRAM_ALLOWED_USER_ID=123456789
```

> The allowed user is the only user whose messages will be processed.

---

## Email Interface

**Module:** [backend/interfaces/email_interface.py](backend/interfaces/email_interface.py)

### Capabilities
- Read unread emails via IMAP
- Normalize into Buddy events
- Send emails via SMTP **only with explicit approval flag**
- Log all events to JSONL

### Event Schema
```
{
  "event_type": "email_received | email_sent",
  "message_id": "...",
  "from": "...",
  "to": "...",
  "subject": "...",
  "timestamp": "...",
  "body_preview": "...",
  "attachments": false,
  "source": "yahoo_mail"
}
```

### Output Log
```
backend/outputs/phase25/email_events.jsonl
```

### Usage Example
```python
from backend.interfaces.email_interface import EmailInterface

email = EmailInterface()

# Read unread emails
events = email.fetch_unread_emails()

# Send email (requires approval flag)
sent = email.send_email(
    to_address="someone@example.com",
    subject="Hello",
    body="Hi from Buddy",
    approval_flag=True
)
```

**Safety**: If `approval_flag=False`, sending is blocked.

---

## Telegram Interface

**Module:** [backend/interfaces/telegram_interface.py](backend/interfaces/telegram_interface.py)

### Capabilities
- Accept messages only from allowed user
- Normalize into Buddy conversation events
- Send outbound messages
- Log all events to JSONL

### Event Schema
```
{
  "event_type": "telegram_message",
  "direction": "incoming | outgoing",
  "user_id": "...",
  "timestamp": "...",
  "text": "...",
  "source": "telegram"
}
```

### Output Log
```
backend/outputs/phase25/telegram_events.jsonl
```

### Usage Example
```python
from backend.interfaces.telegram_interface import TelegramInterface

telegram = TelegramInterface()

# Handle an incoming update (dict from Telegram webhook or getUpdates)
event = telegram.handle_update(update)

# Send an outbound message
telegram.send_message(user_id="123456789", text="Hello from Buddy")
```

---

## Testing

### Email Interface Tests
```
python test_email_interface.py
```

### Telegram Interface Tests
```
python test_telegram_interface.py
```

### Event Bridge Tests
```
python test_event_bridge.py
```

Tests use mocks (no real network access required).

---

## Validation (Live Smoke Tests)

### Email Validation
```
python backend/validation/validate_email_interface.py
```

**Expected output (example):**
```
Starting Yahoo email validation (read-only).
Emails fetched: 2
  1) Subject line one
  2) Subject line two
```

### Telegram Validation (Polling)
```
python backend/validation/validate_telegram_interface.py
```

**Expected output (example):**
```
Starting Telegram polling. Press CTRL+C to stop.
```

#### Manual Telegram Test
1) Send a message to your bot from the **allowed user**.
2) Buddy will reply: **"Buddy received your message and is online."**
3) Stop the script with CTRL+C.

---

## Integration Rules (Respected)

- ✅ No changes to WebNavigatorAgent
- ✅ No changes to BuddysVisionCore
- ✅ No changes to BuddysArms
- ✅ No changes to Phase25Orchestrator
- ✅ No learning or decision-making logic
- ✅ Interface adapters only
- ✅ Events emitted to JSONL for Buddy Core to consume later
- ✅ No automatic email sending (approval required)
- ✅ Telegram messages accepted only from allowed user

---

## Notes

- Errors are caught and logged; interfaces will not crash Buddy.
- Sending email is **disabled by default** and requires explicit approval.
- Telegram messages are accepted only from `BUDDY_TELEGRAM_ALLOWED_USER_ID`.
- Validation scripts are **read-only** and safe to run in production.
