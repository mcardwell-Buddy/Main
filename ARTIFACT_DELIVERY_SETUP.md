# Artifact Delivery System - Complete Setup Guide

**Date:** February 9, 2026  
**Status:** Ready for Configuration  

---

## 🎯 **Overview**

Buddy can now:
- ✉️ **Send emails** with artifact attachments
- ☁️ **Upload to OneDrive** with shared folder access
- 🧠 **Comprehend emails** using LLM intelligence
- 💬 **Understand natural language** responses
- 📦 **Deliver artifacts** via email or cloud storage

---

## 📋 **Prerequisites**

1. **Yahoo Email Account** for Buddy
   - Create at: https://mail.yahoo.com/
   - Example: `buddy.agent@yahoo.com`

2. **Microsoft Account** (for OneDrive)
   - Can be any Microsoft account
   - Buddy will authenticate with his Yahoo email

3. **API Access**
   - Yahoo Developer App
   - Microsoft Azure App Registration

---

## 🔧 **Setup Steps**

### **PART 1: Yahoo Email OAuth Setup**

#### Step 1: Create Yahoo Developer App

1. Go to: https://developer.yahoo.com/apps/
2. Click **"Create an App"**
3. Fill in details:
   - **Application Name**: `Buddy Email Client`
   - **Application Type**: `Web Application`
   - **Description**: `Email client for Buddy AI Agent`
   - **Redirect URI**: `http://localhost:8080/oauth/callback`
   - **API Permissions**: Select **Mail** (Read/Write)

4. Click **Create App**
5. Copy **Client ID** and **Client Secret**

#### Step 2: Configure Buddy's Email Credentials

Create file: `data/yahoo_oauth_config.json`

```json
{
  "client_id": "YOUR_YAHOO_CLIENT_ID",
  "client_secret": "YOUR_YAHOO_CLIENT_SECRET",
  "redirect_uri": "http://localhost:8080/oauth/callback",
  "buddy_email": "buddy.agent@yahoo.com"
}
```

**OR** set environment variables:

```powershell
$env:YAHOO_CLIENT_ID = "YOUR_CLIENT_ID"
$env:YAHOO_CLIENT_SECRET = "YOUR_CLIENT_SECRET"
$env:BUDDY_YAHOO_EMAIL = "buddy.agent@yahoo.com"
```

#### Step 3: Authorize Yahoo Email Access

**Option A: Via API (Recommended)**

1. Start Buddy server: `python backend/main.py`

2. Get authorization URL:
   ```bash
   curl http://localhost:8000/api/email/oauth/setup
   ```

3. Open the returned `authorization_url` in browser

4. Log in with Buddy's Yahoo account and approve access

5. Copy the `code` from callback URL (looks like: `?code=XXXXX`)

6. Complete authorization:
   ```bash
   curl -X POST http://localhost:8000/api/email/oauth/callback \
     -H "Content-Type: application/json" \
     -d '{"code": "PASTE_CODE_HERE"}'
   ```

**Option B: Via Python Script**

```python
from backend.email_client import YahooOAuthClient

oauth = YahooOAuthClient()

# Get URL
print(f"Open this URL: {oauth.get_authorization_url()}")

# After authorizing, paste code
code = input("Enter authorization code: ")
tokens = oauth.exchange_code_for_tokens(code)

print(f"✅ Email configured! Expires: {tokens['expires_at']}")
```

---

### **PART 2: Microsoft OneDrive OAuth Setup**

#### Step 1: Create Azure App Registration

1. Go to: https://portal.azure.com/
2. Navigate to: **Azure Active Directory** → **App registrations**
3. Click **"New registration"**
4. Fill in:
   - **Name**: `Buddy Cloud Storage`
   - **Supported account types**: `Accounts in any organizational directory and personal Microsoft accounts`
   - **Redirect URI**: `Web` → `http://localhost:8080/oauth/microsoft/callback`

5. Click **Register**

6. On Overview page, copy **Application (client) ID**

7. Go to **Certificates & secrets**
   - Click **New client secret**
   - Description: `Buddy OneDrive Access`
   - Expires: `24 months`
   - Click **Add**
   - **COPY THE SECRET VALUE IMMEDIATELY** (won't show again)

8. Go to **API permissions**
   - Click **Add a permission**
   - Select **Microsoft Graph**
   - Select **Delegated permissions**
   - Add:
     - `Files.ReadWrite` (read/write user's files)
     - `Files.ReadWrite.All` (access shared files)
     - `offline_access` (refresh tokens)
   - Click **Add permissions**
   - Click **Grant admin consent** (if you're admin)

#### Step 2: Configure OneDrive Credentials

Create file: `data/onedrive_oauth_config.json`

```json
{
  "client_id": "YOUR_AZURE_APP_CLIENT_ID",
  "client_secret": "YOUR_AZURE_APP_CLIENT_SECRET",
  "redirect_uri": "http://localhost:8080/oauth/microsoft/callback",
  "scopes": "Files.ReadWrite Files.ReadWrite.All offline_access"
}
```

**OR** set environment variables:

```powershell
$env:MICROSOFT_CLIENT_ID = "YOUR_CLIENT_ID"
$env:MICROSOFT_CLIENT_SECRET = "YOUR_CLIENT_SECRET"
```

#### Step 3: Authorize OneDrive Access

**Option A: Via API**

1. Get authorization URL:
   ```bash
   curl http://localhost:8000/api/onedrive/oauth/setup
   ```

2. Open the `authorization_url` in browser

3. **Important**: Log in with YOUR Microsoft account (where you want Buddy to save files)

4. Approve the permissions

5. Copy the `code` from callback URL

6. Complete authorization:
   ```bash
   curl -X POST http://localhost:8000/api/onedrive/oauth/callback \
     -H "Content-Type: application/json" \
     -d '{"code": "PASTE_CODE_HERE"}'
   ```

**Option B: Via Python Script**

```python
from backend.onedrive_client import OneDriveOAuthClient

oauth = OneDriveOAuthClient()

print(f"Open this URL: {oauth.get_authorization_url()}")

code = input("Enter authorization code: ")
tokens = oauth.exchange_code_for_tokens(code)

print(f"✅ OneDrive configured! Expires: {tokens['expires_at']}")
```

---

## 🚀 **Usage Examples**

### **1. Send Email with Attachment**

```python
from backend.email_client import get_email_client

email_client = get_email_client()

result = email_client.send_email(
    to="user@example.com",
    subject="Your Buddy-Built Artifact",
    body="Hi! Here's the file you requested.",
    attachments=["path/to/artifact.py"]
)

print(f"Email sent: {result['success']}")
```

**Via API:**

```bash
curl -X POST http://localhost:8000/api/email/send \
  -H "Content-Type: application/json" \
  -d '{
    "to": "user@example.com",
    "subject": "Test Email",
    "body": "Hello from Buddy!",
    "attachments": ["data/test.txt"]
  }'
```

### **2. Upload to OneDrive**

```python
from backend.onedrive_client import get_onedrive_client

onedrive = get_onedrive_client()

result = onedrive.upload_file(
    file_path="path/to/artifact.py",
    onedrive_folder="/Buddy Artifacts"
)

print(f"Uploaded: {result['web_url']}")
```

**Via API:**

```bash
curl -X POST http://localhost:8000/api/onedrive/upload \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "data/test.txt",
    "onedrive_folder": "/Buddy Artifacts"
  }'
```

### **3. Full Delivery Flow (Natural Language)**

After Buddy completes a task:

```python
from backend.artifact_delivery_flow import get_delivery_orchestrator

orchestrator = get_delivery_orchestrator()

# Offer delivery
offer = orchestrator.offer_delivery(
    mission_id="mission_123",
    artifacts=["output.py", "readme.md"],
    user_email="user@example.com"
)

print(offer["message"])  # Shows offer to user

# User responds: "yes email them both"
result = orchestrator.handle_delivery_response(
    mission_id="mission_123",
    user_response="yes email them both"
)

print(result["message"])  # Confirmation message
```

### **4. Fetch and Comprehend Emails**

```python
from backend.email_client import get_email_client, get_comprehension_engine

# Fetch recent emails
email_client = get_email_client()
emails = email_client.fetch_emails(unread_only=True, limit=5)

# Comprehend each email
engine = get_comprehension_engine()
for email in emails:
    comprehension = engine.comprehend_email(email)
    
    print(f"From: {email['from']}")
    print(f"Intent: {comprehension['intent']}")
    print(f"Urgency: {comprehension['urgency']}")
    print(f"Action Items: {comprehension['action_items']}")
    print("---")
```

**Via API:**

```bash
# Fetch emails
curl "http://localhost:8000/api/email/fetch?unread_only=true&limit=5"

# Comprehend specific email
curl -X POST http://localhost:8000/api/email/comprehend \
  -H "Content-Type: application/json" \
  -d '{
    "email": {
      "from": "user@example.com",
      "subject": "Help needed",
      "body": "Can you create a script for me?"
    }
  }'
```

---

## 🔄 **Integrated Workflow**

### **How It Works in Buddy's Execution Flow:**

1. **User approves a mission** → Buddy executes and creates artifacts

2. **After completion**, Buddy calls:
   ```python
   orchestrator.offer_delivery(
       mission_id=mission.id,
       artifacts=created_files,
       user_email=user.email
   )
   ```

3. **User sees offer**:
   ```
   🎉 Task Complete!
   
   I've built script.py for you.
   
   Would you like me to send it to you?
   Options: Email, OneDrive, Both
   
   Just reply naturally!
   ```

4. **User responds**: `"yes email it with a note saying this is version 2"`

5. **Buddy parses intent**:
   ```json
   {
     "wants_delivery": true,
     "email": true,
     "onedrive": false,
     "custom_message": "this is version 2"
   }
   ```

6. **Buddy sends email** with attachment and custom message

7. **User receives notification**: `✅ Email sent successfully!`

---

## 🎨 **Natural Language Examples**

Buddy understands various ways users express delivery preferences:

| **User Says**                          | **Buddy Understands**                |
|----------------------------------------|--------------------------------------|
| "yes please"                           | Email ✅                             |
| "email it"                             | Email ✅                             |
| "save to onedrive"                     | OneDrive ✅                          |
| "both"                                 | Email ✅ + OneDrive ✅               |
| "send via email and save to cloud"    | Email ✅ + OneDrive ✅               |
| "no thanks"                            | Decline ❌                           |
| "not right now"                        | Decline ❌                           |
| "email with note: final version"      | Email ✅ + custom message            |

---

## 📊 **Testing**

Run the comprehensive test suite:

```powershell
python test_artifact_delivery.py
```

**Tests include:**
- ✅ Natural language intent parsing
- ✅ OAuth configuration loading
- ✅ Delivery orchestrator workflow
- ✅ Email client initialization
- ✅ OneDrive client initialization
- ✅ File attachment support

**Expected output:**
```
🎉 ALL TESTS PASSED! (6/6)

✅ Artifact delivery system is ready!
```

---

## 🔐 **Security Notes**

1. **OAuth Tokens**: Stored securely in `data/` directory
   - `yahoo_tokens.json` (email)
   - `onedrive_tokens.json` (cloud storage)
   - Add `data/` to `.gitignore` to prevent committing secrets

2. **Token Refresh**: Automatic refresh when tokens expire

3. **Scopes**:
   - Yahoo: `mail-r` (read), `mail-w` (write)
   - Microsoft: `Files.ReadWrite`, `Files.ReadWrite.All`

4. **Redirect URIs**: Only `localhost` for development
   - For production, use HTTPS endpoints

---

## 🐛 **Troubleshooting**

### **"No access token" Error**

**Problem**: OAuth not configured

**Solution**: Complete OAuth authorization flow (see Steps 3 in each section)

### **"Access token expired" Error**

**Problem**: Token expired and refresh failed

**Solution**: 
1. Delete token files: `data/yahoo_tokens.json`, `data/onedrive_tokens.json`
2. Re-run OAuth authorization

### **"Invalid client credentials" Error**

**Problem**: Client ID/Secret incorrect

**Solution**: 
1. Verify credentials in config files
2. Regenerate secret in Yahoo/Azure portal if needed

### **"Permission denied" Error (OneDrive)**

**Problem**: Insufficient API permissions

**Solution**:
1. Go to Azure portal → App → API permissions
2. Ensure `Files.ReadWrite.All` is added
3. Click "Grant admin consent"

### **Email doesn't arrive**

**Problem**: Email in spam or Yahoo SMTP issues

**Solution**:
1. Check spam folder
2. Verify `buddy_email` is correct in config
3. Check Yahoo account is active and can send emails manually

---

## 📝 **API Endpoints Reference**

### **Email Endpoints**

- `GET /api/email/oauth/setup` - Get Yahoo OAuth URL
- `POST /api/email/oauth/callback` - Complete OAuth with code
- `POST /api/email/send` - Send email with attachments
- `GET /api/email/fetch?unread_only=true&limit=10` - Fetch emails
- `POST /api/email/comprehend` - Comprehend email with LLM

### **OneDrive Endpoints**

- `GET /api/onedrive/oauth/setup` - Get Microsoft OAuth URL
- `POST /api/onedrive/oauth/callback` - Complete OAuth with code
- `POST /api/onedrive/upload` - Upload file to OneDrive
- `GET /api/onedrive/list?folder=/` - List files in folder

### **Artifact Delivery Endpoints**

- `POST /api/artifacts/offer-delivery` - Offer delivery after task completion
- `POST /api/artifacts/handle-delivery-response` - Handle user's natural language response

---

## 🎉 **Success!**

Once configured, Buddy will:
- ✅ Automatically offer to send artifacts after completing tasks
- ✅ Understand your natural language responses
- ✅ Send emails with professional formatting
- ✅ Upload to your OneDrive with organized folders
- ✅ Comprehend incoming emails and extract action items
- ✅ Provide delivery confirmations with links

**Buddy is now your personal delivery assistant!** 📬🤖
