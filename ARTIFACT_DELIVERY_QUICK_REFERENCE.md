# 🚀 Buddy Artifact Delivery - Quick Reference

## 📧 **Send Email with Attachment**

### Python:
```python
from backend.email_client import get_email_client

client = get_email_client()
result = client.send_email(
    to="user@example.com",
    subject="Your Artifact",
    body="Hi! Here's your file.",
    attachments=["path/to/file.py"]
)
```

### API:
```bash
curl -X POST http://localhost:8000/api/email/send \
  -H "Content-Type: application/json" \
  -d '{
    "to": "user@example.com",
    "subject": "Your Artifact",
    "body": "Hi! Here is your file.",
    "attachments": ["path/to/file.py"]
  }'
```

---

## ☁️ **Upload to OneDrive**

### Python:
```python
from backend.onedrive_client import get_onedrive_client

client = get_onedrive_client()
result = client.upload_file(
    file_path="path/to/file.py",
    onedrive_folder="/Buddy Artifacts"
)
print(result["web_url"])  # Share this link
```

### API:
```bash
curl -X POST http://localhost:8000/api/onedrive/upload \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "path/to/file.py",
    "onedrive_folder": "/Buddy Artifacts"
  }'
```

---

## 🎯 **Full Delivery Flow**

### Python:
```python
from backend.artifact_delivery_flow import get_delivery_orchestrator

orchestrator = get_delivery_orchestrator()

# Step 1: Offer delivery
offer = orchestrator.offer_delivery(
    mission_id="mission_123",
    artifacts=["script.py", "readme.md"],
    user_email="user@example.com"
)
print(offer["message"])  # Show to user

# Step 2: Handle user response
result = orchestrator.handle_delivery_response(
    mission_id="mission_123",
    user_response="yes email them"  # Natural language
)
print(result["message"])  # Show confirmation
```

### API:
```bash
# Step 1: Offer
curl -X POST http://localhost:8000/api/artifacts/offer-delivery \
  -H "Content-Type: application/json" \
  -d '{
    "mission_id": "mission_123",
    "artifacts": ["script.py", "readme.md"],
    "user_email": "user@example.com"
  }'

# Step 2: Handle response
curl -X POST http://localhost:8000/api/artifacts/handle-delivery-response \
  -H "Content-Type: application/json" \
  -d '{
    "mission_id": "mission_123",
    "user_response": "yes email them"
  }'
```

---

## 📥 **Fetch & Comprehend Emails**

### Python:
```python
from backend.email_client import get_email_client, get_comprehension_engine

# Fetch emails
client = get_email_client()
emails = client.fetch_emails(unread_only=True, limit=5)

# Comprehend
engine = get_comprehension_engine()
for email in emails:
    comp = engine.comprehend_email(email)
    print(f"From: {email['from']}")
    print(f"Intent: {comp['intent']}")
    print(f"Urgency: {comp['urgency']}")
    print(f"Action Items: {comp['action_items']}")
```

### API:
```bash
# Fetch
curl "http://localhost:8000/api/email/fetch?unread_only=true&limit=5"

# Comprehend
curl -X POST http://localhost:8000/api/email/comprehend \
  -H "Content-Type: application/json" \
  -d '{
    "email": {
      "from": "user@example.com",
      "subject": "Need help",
      "body": "Can you create a script?"
    }
  }'
```

---

## 🔧 **OAuth Setup**

### Get Authorization URLs:
```bash
# Yahoo Email
curl http://localhost:8000/api/email/oauth/setup

# Microsoft OneDrive
curl http://localhost:8000/api/onedrive/oauth/setup
```

### Complete Authorization:
```bash
# Yahoo Email
curl -X POST http://localhost:8000/api/email/oauth/callback \
  -H "Content-Type: application/json" \
  -d '{"code": "YOUR_AUTH_CODE"}'

# Microsoft OneDrive
curl -X POST http://localhost:8000/api/onedrive/oauth/callback \
  -H "Content-Type: application/json" \
  -d '{"code": "YOUR_AUTH_CODE"}'
```

---

## ✅ **Test System**

### Run All Tests:
```bash
python test_artifact_delivery.py
```

**Expected:** 🎉 ALL TESTS PASSED! (6/6)

---

## 💡 **Natural Language Examples**

Users can respond naturally to delivery offers:

| User Says | What Happens |
|-----------|--------------|
| "yes please" | Email sent ✅ |
| "email it" | Email sent ✅ |
| "save to onedrive" | OneDrive upload ✅ |
| "both" | Email + OneDrive ✅ |
| "no thanks" | Nothing sent ❌ |
| "email with note: final version" | Email with custom message ✅ |

---

## 📂 **Configuration Files**

### Yahoo Email:
`data/yahoo_oauth_config.json`
```json
{
  "client_id": "YOUR_YAHOO_CLIENT_ID",
  "client_secret": "YOUR_YAHOO_CLIENT_SECRET",
  "redirect_uri": "http://localhost:8080/oauth/callback",
  "buddy_email": "buddy@yahoo.com"
}
```

### Microsoft OneDrive:
`data/onedrive_oauth_config.json`
```json
{
  "client_id": "YOUR_AZURE_CLIENT_ID",
  "client_secret": "YOUR_AZURE_CLIENT_SECRET",
  "redirect_uri": "http://localhost:8080/oauth/microsoft/callback",
  "scopes": "Files.ReadWrite Files.ReadWrite.All offline_access"
}
```

---

## 🚨 **Troubleshooting**

### "No access token" Error
→ Run OAuth setup and authorization flow

### "Token expired" Error
→ Delete token files and re-authorize OR wait for auto-refresh

### Email doesn't send
→ Check spam folder, verify Yahoo credentials

### OneDrive upload fails
→ Verify API permissions in Azure portal

---

## 📚 **Documentation**

- [ARTIFACT_DELIVERY_IMPLEMENTATION.md](ARTIFACT_DELIVERY_IMPLEMENTATION.md) - Full implementation details
- [ARTIFACT_DELIVERY_SETUP.md](ARTIFACT_DELIVERY_SETUP.md) - Step-by-step setup guide

---

## 🎯 **Common Workflows**

### 1. After Task Completion:
```python
# Buddy creates files
artifacts = ["output.py", "readme.md"]

# Offer delivery
offer = orchestrator.offer_delivery(mission_id, artifacts, user_email)

# User responds
result = orchestrator.handle_delivery_response(mission_id, user_response)
```

### 2. Process Incoming Email:
```python
# Fetch unread
emails = client.fetch_emails(unread_only=True)

# Comprehend and act
for email in emails:
    comp = engine.comprehend_email(email)
    for action in comp['action_items']:
        buddy.create_mission(action)
```

### 3. Batch Upload to OneDrive:
```python
for file in created_files:
    result = onedrive.upload_file(file, "/Buddy Artifacts/project_123")
    print(f"Uploaded: {result['web_url']}")
```

---

**Quick Start:** Run `python test_artifact_delivery.py` to verify setup! 🚀
