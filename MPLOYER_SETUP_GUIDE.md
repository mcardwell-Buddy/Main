# Mployer Automation Setup Guide

## Overview
Buddy can automatically search Mployer for contacts matching your criteria and add them to GoHighLevel. This runs on a schedule (daily, weekly, or hourly) completely hands-off.

---

## Step 1: Store Your Mployer Credentials Securely

We support **3 secure methods** to store your login credentials:

### Option A: Environment Variables (Simplest)
1. Create a `.env` file in `C:\Users\micha\Buddy\`
2. Add these lines:
```
MPLOYER_USERNAME=your-mployer-email@example.com
MPLOYER_PASSWORD=your-mployer-password
```
3. Save the file

**Pros:** Easy setup, Buddy loads them automatically
**Cons:** Least secure (check .env is in .gitignore)

### Option B: Windows Credential Manager (Recommended)
Run this setup wizard:
```powershell
cd C:\Users\micha\Buddy
python -c "from backend.credential_manager import CredentialManager; CredentialManager.setup_credentials()"
```

Select **Option 3: Windows Credential Manager**

Your credentials will be:
- ✅ Encrypted by Windows
- ✅ Automatically retrieved by Buddy
- ✅ Never stored in files
- ✅ Accessible only by your Windows account

### Option C: Encrypted Local Storage
Run the setup wizard above and select **Option 2: Encrypted Storage**

Your credentials will be:
- ✅ AES-256 encrypted
- ✅ Stored locally with encryption key in Credential Manager
- ✅ Safe if file is compromised

---

## Step 2: Configure Search Criteria

Create `mployer_config.json` in `C:\Users\micha\Buddy\` or run the interactive setup:

```powershell
cd C:\Users\micha\Buddy
python -c "from backend.mployer_scheduler import interactive_setup; interactive_setup()"
```

**Or manually create `mployer_config.json`:**
```json
{
  "enabled": true,
  "schedule": "daily",
  "run_time": "08:00",
  "job_title": "Head of HR",
  "location": "Baltimore, Maryland",
  "company_size_min": 10,
  "company_size_max": 500,
  "exclude_keywords": ["government", "union", "federal", "military"],
  "max_contacts": 50,
  "workflow_id": null
}
```

**Configuration Options:**
- `schedule`: "daily", "weekly", or "hourly"
- `run_time`: Time in 24-hour format (e.g., "08:00" for 8 AM)
- `job_title`: Target position (e.g., "Head of HR", "CFO", "CEO")
- `location`: Target geography
- `company_size_min/max`: Employee count range
- `exclude_keywords`: Industries/types to filter out
- `max_contacts`: Maximum contacts to collect per run
- `workflow_id`: (Optional) GHL workflow ID to trigger after adding contacts

---

## Step 3: Test the Automation

### Run Once Immediately:
```powershell
cd C:\Users\micha\Buddy
python -c "from backend.mployer_scheduler import MployerScheduler; s = MployerScheduler(); result = s.run_once_now(); print(result)"
```

This will:
1. ✅ Log into your Mployer account
2. ✅ Search for matching contacts
3. ✅ Extract their information
4. ✅ Check if they already exist in GHL
5. ✅ Add new contacts with "Buddy List" tag
6. ✅ Show you the results

### Watch It Run (Not Headless):
If you want to see the browser in action:
1. Edit `backend/mployer_scraper.py` line 49
2. Change `headless: bool = True` to `headless: bool = False`
3. Run the test again

---

## Step 4: Start the Scheduler

### Option A: Run in PowerShell (Foreground)
```powershell
cd C:\Users\micha\Buddy
python -c "from backend.mployer_scheduler import MployerScheduler; s = MployerScheduler(); s.start_scheduler()"
```

This will:
- ✅ Run at your scheduled time
- ✅ Check every minute for scheduled tasks
- ✅ Display logs in real-time
- ⚠️ Must keep terminal open

### Option B: Schedule as Windows Task (Recommended)
This runs Buddy even when you're not logged in.

Create a scheduled task in Windows:
1. Open **Task Scheduler**
2. **Create Basic Task** → Name: "Buddy Mployer Automation"
3. **Trigger**: Daily at 8 AM (or your preferred time)
4. **Action**: Start a program
   - Program: `C:\Users\micha\AppData\Local\Programs\Python\Python311\python.exe`
   - Arguments: `-c "from backend.mployer_scheduler import MployerScheduler; s = MployerScheduler(); s.run_automation()"`
   - Start in: `C:\Users\micha\Buddy`
5. **Finish** → Check "Open the Properties dialog when I click Finish"
6. Set user to your account and enable "Run with highest privileges"
7. Click **OK**

---

## Step 5: Monitor Automation Runs

Buddy creates logs of each run in `C:\Users\micha\Buddy\logs\mployer.log`

View recent runs:
```powershell
Get-Content "C:\Users\micha\Buddy\logs\mployer.log" -Tail 50
```

---

## How It Works in Detail

### Search Flow:
```
1. Load stored Mployer credentials ✓
2. Open Mployer in browser (Chrome) ✓
3. Log in with your credentials ✓
4. Navigate to search page ✓
5. Enter search criteria:
   - Job title: "Head of HR"
   - Location: "Baltimore, Maryland"
   - Company size: 10-500
   - Exclude: government, unions, etc.
6. Extract results from page ✓
7. For each contact found:
   - Parse name, email, phone, address
   - Get LinkedIn URL
   - Check if duplicate in GHL
   - Add if new
8. Tag all as "Buddy List" ✓
9. (Optional) Trigger workflow ✓
10. Report results ✓
```

### Data Safety:
- ✅ No passwords stored in code
- ✅ No credentials in logs
- ✅ Encrypted storage available
- ✅ Windows Credential Manager backed
- ✅ Can be revoked anytime

---

## Troubleshooting

### "Credentials not found"
Run setup:
```powershell
python -c "from backend.credential_manager import CredentialManager; CredentialManager.setup_credentials()"
```

### Mployer Login Fails
1. Test manual login on mployer.com first
2. Check if your password changed
3. Check if 2FA is enabled (may need adjustment)
4. Check if account is locked

### No Contacts Found
1. Test search manually on Mployer
2. Adjust search criteria in config
3. Check exclude_keywords isn't filtering everything
4. Try broader location/title

### Selector Errors in Logs
Mployer may have changed their HTML structure. If you see errors like:
```
Could not locate element: By.ID, "email"
```

This means the HTML selectors need updating. Contact support or update selectors in `mployer_scraper.py` lines with `find_element()`

---

## Next Steps

1. ✅ **Store credentials** (Recommend: Windows Credential Manager)
2. ✅ **Configure search criteria** (your target profile)
3. ✅ **Test once** (run immediately and verify)
4. ✅ **Schedule automation** (Windows Task Scheduler)
5. ✅ **Monitor logs** (check results daily)
6. ✅ **Review in GHL** (see new contacts in "Buddy List")

---

## Questions?

Check logs first:
```powershell
Get-Content "C:\Users\micha\Buddy\logs\mployer.log" -Tail 100
```

Common issues are documented there.
