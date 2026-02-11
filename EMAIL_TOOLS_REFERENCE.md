# Email Tools Reference

Buddy now has **two separate email tools** for different purposes:

---

## 🏢 Work Email Tool: `email_send_work`

**Purpose:** Professional business communications for Michael Cardwell at Cardwell Associates

**Email Account:** Michael's Microsoft 365 work email  
**Authentication:** Microsoft Graph API (OAuth)  
**Use Cases:**
- Client communications
- Professional correspondence
- Business reports and updates
- Cardwell Associates official emails

**Example:**
```python
send_work_email(
    to="client@example.com",
    subject="Project Update",
    body="Dear Client, your project milestone has been completed...",
    template="notification",
    name="Client Name",
    title="Project Milestone Complete",
    content="Milestone details here..."
)
```

---

## 🤖 Buddy Personal Email Tool: `email_send_buddy`

**Purpose:** Buddy's operational and personal communications

**Email Account:** buddy.cardwell@yahoo.com (Yahoo Mail)  
**Authentication:** SMTP with app password  
**Use Cases:**
- System notifications
- Operational reports
- Buddy's own communications
- Non-professional emails
- Service integrations
- Daily activity reports

**Example:**
```python
send_buddy_email(
    to="service@example.com",
    subject="Daily Activity Report",
    body="Today's summary...",
    template="report",
    name="System Admin",
    title="Daily Report",
    content="Activity details here..."
)
```

---

## 📋 Common Parameters (Both Tools)

| Parameter | Type | Description |
|-----------|------|-------------|
| `to` | str | Recipient email (comma-separated for multiple) |
| `subject` | str | Email subject line |
| `body` | str | Email body content |
| `attachments` | List[str] | File paths to attach (optional) |
| `cc` | str | CC recipients (optional) |
| `bcc` | str | BCC recipients (optional) |
| `html` | bool | Send as HTML email (default: False) |
| `template` | str | Template name: greeting, notification, report, custom |
| `**template_vars` | dict | Variables for template rendering |

---

## 🎨 Available Templates

### 1. **greeting**
```python
send_buddy_email(
    to="user@example.com",
    template="greeting",
    name="John",
    content="Welcome to the system!"
)
```

### 2. **notification**
```python
send_work_email(
    to="client@example.com",
    template="notification",
    name="Client Name",
    title="Important Update",
    content="Your request has been processed."
)
```

### 3. **report**
```python
send_buddy_email(
    to="admin@example.com",
    template="report",
    name="Admin",
    title="Weekly Summary",
    content="This week's metrics:\n- Tasks: 45\n- Success: 98%"
)
```

### 4. **custom**
```python
send_work_email(
    to="team@example.com",
    template="custom",
    subject="Custom Subject",
    body="Fully custom email body"
)
```

---

## ✅ Decision Guide: Which Tool to Use?

### Use `email_send_work` when:
- ✅ Communicating with clients or business partners
- ✅ Sending professional reports or proposals
- ✅ Official Cardwell Associates correspondence
- ✅ Anything requiring Michael's professional identity

### Use `email_send_buddy` when:
- ✅ System notifications or alerts
- ✅ Internal operational emails
- ✅ Service integrations or API notifications
- ✅ Personal/non-business communications
- ✅ Testing or development emails
- ✅ Buddy's own activity reports

---

## 🔧 Technical Details

### Work Email (Microsoft Graph)
- **Protocol:** HTTPS REST API
- **Authentication:** OAuth 2.0 Client Credentials
- **Permissions:** Mail.Send (Application)
- **Rate Limits:** Microsoft Graph throttling applies
- **Cost:** Included in M365 subscription

### Buddy Email (Yahoo SMTP)
- **Protocol:** SMTP over SSL (Port 465)
- **Authentication:** App Password
- **Credentials:** Stored in `.env` as `BUDDY_EMAIL_APP_PASSWORD`
- **Rate Limits:** Yahoo SMTP limits apply
- **Cost:** Free Yahoo Mail account

---

## 🚨 Important Notes

1. **Never mix contexts** - Don't send Buddy's operational emails from Michael's work account
2. **Security** - Both tools respect credential separation for security
3. **Legacy tool** - `email_send` still exists but is DEPRECATED (defaults to Buddy email)
4. **Attachments** - Both tools support file attachments up to reasonable size limits
5. **HTML Support** - Set `html=True` for rich formatted emails

---

## 📊 Monitoring

Both tools log to:
- **Whiteboard Metrics** - API usage tracking
- **Application Logs** - Detailed send/failure info
- **Return Values** - Success/failure status with timestamps

**Success Response:**
```json
{
    "success": true,
    "message": "Email sent to recipient@example.com",
    "timestamp": "2026-02-11T12:30:00.000000",
    "subject": "Test Subject",
    "recipients": "recipient@example.com",
    "from": "sender@email.com",
    "attachments": 2,
    "duration_ms": 1234.56
}
```

**Failure Response:**
```json
{
    "success": false,
    "error": "Error description here",
    "timestamp": "2026-02-11T12:30:00.000000"
}
```

---

## 🎯 Quick Reference Commands

```python
# Import both tools
from Back_End.tool_email import send_work_email, send_buddy_email

# Professional email
send_work_email(to="client@company.com", subject="...", body="...")

# Operational email
send_buddy_email(to="service@provider.com", subject="...", body="...")

# With template
send_work_email(
    to="client@company.com",
    template="notification",
    name="Client",
    title="Update",
    content="Details..."
)
```

---

**Updated:** February 11, 2026  
**Phase:** Phase 2 - Dual Email System
