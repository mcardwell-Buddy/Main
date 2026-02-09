# 🚀 Firebase Deployment Setup - Complete Instructions

**Status:** ✅ Configuration files ready  
**Date:** February 9, 2026

---

## 📋 **What We've Set Up**

- ✅ `.gitignore` - Excludes unnecessary files
- ✅ `firebase.json` - Firebase hosting config
- ✅ `.gcloudignore` - Cloud deployment config
- ✅ `Dockerfile` - Container configuration
- ✅ This guide!

---

## 🚀 **Step 1: Install Git (If Not Already Installed)**

### **Windows:**

1. Go to: https://git-scm.com/download/win
2. Download and run the installer
3. Use all default options
4. **Restart PowerShell** after installation

Verify installation:
```powershell
git --version
```

Should show: `git version 2.x.x...`

---

## 📦 **Step 2: Install Firebase CLI**

```powershell
# Install Node.js first if you don't have it
# Download from: https://nodejs.org/

# Then install Firebase CLI
npm install -g firebase-tools
```

Verify:
```powershell
firebase --version
```

---

## 🔐 **Step 3: Login to Firebase**

```powershell
firebase login
```

This opens a browser → Click "Allow" → Closes automatically

---

## 📝 **Step 4: Set Up Git Repository**

```powershell
cd C:\Users\micha\Buddy

# Configure Git user for this repo
git config user.email "buddy@example.com"
git config user.name "Buddy Agent"

# Add all files
git add .

# Create first commit
git commit -m "Initial Buddy commit with email and cloud features"

# Check status
git status
```

You should see: `nothing to commit, working tree clean`

---

## 🔗 **Step 5: Connect to Your Firebase Project**

```powershell
# List your Firebase projects
firebase list

# Connect to your project (replace PROJECT_ID with your actual ID)
firebase use YOUR_PROJECT_ID

# Example: firebase use buddy-agent-123abc
```

You'll see a `.firebaserc` file created (already in .gitignore)

---

## ☁️ **Step 6: Deploy to Firebase App Hosting**

### **Option A: Via Firebase Console (Easiest)**

1. Go to: https://console.firebase.google.com/
2. Select your project
3. **Left menu → Build → App Hosting**
4. **Create an App / Connect Repository**
5. **Connect GitHub**
   - Authorize Firebase
   - Select your Buddy repository
   - Select `main` branch
6. **Click Deploy**

Firebase auto-deploys on every Git push!

### **Option B: Deploy from Local (Fastest for Testing)**

```powershell
cd C:\Users\micha\Buddy

# Deploy to Firebase
firebase deploy

# Or deploy only hosting
firebase deploy --only hosting
```

---

## 🎯 **Step 7: Get Your HTTPS URL**

After deployment, you'll see:

```
Hosting URL: https://buddy-agent-abc123.web.app
```

---

## 🛠️ **Step 8: Update Yahoo OAuth Config**

Update: `data/yahoo_oauth_config.json`

```json
{
  "client_id": "YOUR_YAHOO_CLIENT_ID",
  "client_secret": "YOUR_YAHOO_CLIENT_SECRET",
  "redirect_uri": "https://buddy-agent-abc123.web.app/oauth/callback",
  "buddy_email": "buddy@yahoo.com"
}
```

Replace `buddy-agent-abc123` with **your actual Firebase URL**

---

## ✅ **Step 9: Test OAuth Flow**

```powershell
# Once deployed, test the OAuth setup endpoint
curl https://your-firebase-url.web.app/api/email/oauth/setup

# Should return an authorization_url
```

---

## 📊 **Deployment Checklist**

- [ ] Git installed and working
- [ ] Firebase CLI installed (`firebase --version`)
- [ ] Logged into Firebase (`firebase login`)
- [ ] Repository initialized (`git status` works)
- [ ] Files committed (`git log` shows commits)
- [ ] Firebase project connected (`firebase use PROJECT_ID`)
- [ ] App Hosting enabled in Firebase Console
- [ ] Deployed to Firebase (see HTTPS URL)
- [ ] Yahoo OAuth config updated with HTTPS URL
- [ ] OAuth endpoint responds

---

## 🚀 **After Deployment**

Your Buddy now:
- ✅ Has a public HTTPS URL
- ✅ Can send/receive emails
- ✅ Can upload to OneDrive
- ✅ Can deliver artifacts
- ✅ Auto-deploys on Git commits

---

## 📝 **Expected Folder Structure After Setup**

```
Buddy/
├── .git/                    (created by git init)
├── .gitignore              (already present)
├── .firebaserc              (created by firebase use)
├── .gcloudignore           (we created)
├── firebase.json           (we created)
├── Dockerfile              (we created)
├── requirements.txt        
├── backend/
│   ├── main.py
│   ├── email_client.py
│   ├── onedrive_client.py
│   └── ... (other files)
├── data/                   (ignored by git)
└── README.md
```

---

## 🐛 **Troubleshooting**

### **"Git not found"**
→ Install Git from https://git-scm.com/

### **"firebase: command not found"**
→ Install Firebase CLI: `npm install -g firebase-tools`

### **"Not logged in to Firebase"**
→ Run: `firebase login`

### **"Could not find Cloud Build API"**
→ Go to: https://console.cloud.google.com/ → Enable Cloud Build API

### **Email doesn't send from deployed Buddy**
→ Make sure `data/yahoo_tokens.json` exists
→ Re-run OAuth authorization flow
→ Check that token file permissions are correct

---

## 🎉 **Next Steps**

1. **Install Git** (if needed)
2. **Install Firebase CLI** (if needed)  
3. **Follow Steps 3-6** above
4. **Get your HTTPS URL**
5. **Update Yahoo OAuth config** with HTTPS URL
6. **Test with curl or browser**

---

## 💬 **Need Help?**

When you get stuck on a step:
1. Note which step failed
2. Share the error message
3. I can help debug!

**Most common issue:** Git not installed → Just install Git and retry!

---

## 🎯 **Summary**

Everything is ready:
- ✅ Configuration files created
- ✅ Buddy code ready
- ✅ Just need to: Install Git → Commit → Deploy

**Total time:** ~10 minutes!

Let me know once you've installed Git and I'll walk you through the rest! 🚀
