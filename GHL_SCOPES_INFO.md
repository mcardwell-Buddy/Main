# GoHighLevel API Scopes & Permissions

## Current Token Type
Your token: `pit-2a219967-29e8-4ea7-97ce-ea515b04e90a`

This appears to be a **Personal Integration Token (PIT)**.

## Issue: 401 Unauthorized

The 401 error suggests one of these issues:

### 1. Missing Location ID
GHL API v1 requires BOTH:
- **API Token** (Authorization header)
- **Location ID** (in request body or as a query parameter)

**Solution**: You need to provide your GoHighLevel Location ID.

### 2. Token Scopes
When you created the token, you should have selected scopes like:
- ✅ `contacts.readonly` - Read contacts
- ✅ `contacts.write` - Create/update contacts
- ✅ `opportunities.readonly` - Read opportunities
- ✅ `opportunities.write` - Create/update opportunities
- ✅ `tasks.readonly` - Read tasks
- ✅ `tasks.write` - Create/update tasks
- ✅ `calendars.readonly` - Read calendars
- ✅ `calendars.write` - Create/update calendar events
- ✅ `conversations.readonly` - Read conversations
- ✅ `conversations.write` - Send messages
- ✅ `users.readonly` - Read user info
- ✅ `locations.readonly` - Read location info

## How to Get Your Location ID

1. Log into your GoHighLevel account
2. Go to **Settings** → **Company** or check your account URL
3. Your Location ID is typically visible in the URL or in API settings

## How to Configure with Location ID

Run in PowerShell:

```powershell
$body = @{
    api_token = "pit-2a219967-29e8-4ea7-97ce-ea515b04e90a"
    location_id = "YOUR_LOCATION_ID_HERE"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/ghl/configure" -Method POST -Body $body -ContentType "application/json"
```

## Alternative: Use API v2

GHL API v2 might not require location_id in the same way. We can update the client to use v2 if needed.

## Current Implementation Scopes

Buddy currently supports these GHL operations:
- ✅ Add/update contacts
- ✅ Search contacts
- ✅ Create opportunities (deals)
- ✅ Add tasks
- ✅ Add notes to contacts
- ✅ Bulk import contacts
- ❌ Calendar events (not yet implemented)
- ❌ Conversations/messaging (not yet implemented)
- ❌ Workflows/automation (not yet implemented)

If you granted "all rights," we can implement additional endpoints once the authentication is working.
