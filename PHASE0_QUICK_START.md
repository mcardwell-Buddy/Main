# Phase 0: Preparation & Planning - Quick Start

## 🎯 Goal
Establish baseline and prepare infrastructure before building.

**Timeline:** 1-2 days  
**Status:** ✅ READY TO START

---

## ✅ Checklist

### **Step 1: Test Browser Capacity** (30-45 minutes)

Run the browser capacity test to see how many Chrome instances your laptop can handle.

```powershell
cd C:\Users\micha\Buddy
python scripts/test_browser_capacity.py
```

**What it does:**
- Launches browsers in batches of 5
- Monitors RAM/CPU usage
- Stops at 85% RAM (safety)
- Generates report with recommendations

**Expected Output:**
```
✅ Batch 1: 5 browsers launched (12.3s)
   Total Browsers: 5
   RAM: 4.2 GB (26.3%)
   CPU: 34.5%
   Estimated Safe Max (70%): ~28 browsers
```

**Deliverable:** 
- [ ] `PHASE0_BROWSER_CAPACITY_REPORT.txt` created
- [ ] Know safe maximum: ____ browsers

---

### **Step 2: Analyze Firebase Usage** (10-15 minutes)

Analyze current Firebase Firestore usage to establish cost baseline.

```powershell
python scripts/analyze_firebase_usage.py
```

**What it does:**
- Counts documents in each collection
- Estimates storage size
- Projects monthly operations
- Calculates costs vs free tier

**Expected Output:**
```
📊 FIREBASE USAGE ANALYSIS
Total Documents: 127
Total Storage: 8.45 MB
Reads/month: ~7,620
Writes/month: ~381
✅ Within free tier! Estimated cost: $0/month
```

**Deliverable:**
- [ ] `PHASE0_FIREBASE_USAGE_REPORT.txt` created
- [ ] Current cost baseline: $____ /month

---

### **Step 3: Review Schema Designs** (15-20 minutes)

Review the database designs we'll implement in later phases.

- [ ] Read `docs/SQLITE_SCHEMA_DESIGN.md`
  - 8 tables designed
  - Understand task queue structure
  - Review cleanup strategy

- [ ] Read `docs/FIREBASE_QUEUE_DESIGN.md`
  - Firebase collection structure
  - Task routing flow
  - Sync strategy

**Deliverable:**
- [ ] Understand database architecture
- [ ] Ready to implement in Phase 5-6

---

### **Step 4: Check Laptop Specs** (5 minutes)

Verify your laptop specifications.

```powershell
# Check RAM
wmic memorychip get capacity
# (Sum and divide by 1GB = 1073741824)

# Check CPU
wmic cpu get name, numberofcores, numberoflogicalprocessors

# Check Python version
python --version

# Check Chrome version
(Get-Item "C:\Program Files\Google\Chrome\Application\chrome.exe").VersionInfo.FileVersion
```

**Record:**
- [ ] RAM: ____ GB
- [ ] CPU: ____ cores
- [ ] Python: ______
- [ ] Chrome: ______
- [ ] OS: Windows ____

---

### **Step 5: Backup Current System** (10 minutes)

Safety first! Backup before building.

```powershell
# Export Firebase data (if possible)
# Create git branch
git checkout -b feature/local-agent

# Backup .env
cp .env .env.backup

# Commit current state
git add -A
git commit -m "Checkpoint before Phase 0 - Local Agent implementation"
```

**Deliverable:**
- [ ] Git branch created: `feature/local-agent`
- [ ] `.env` backed up
- [ ] Current code committed

---

### **Step 6: Install Dependencies** (5-10 minutes)

Install new packages needed for local agent.

```powershell
# Activate virtual environment
.venv\Scripts\activate

# Install new packages
pip install psutil rich schedule flask

# Update requirements
pip freeze > requirements.txt
```

**Packages:**
- [x] `psutil` - System monitoring (RAM/CPU)
- [x] `rich` - Beautiful terminal output
- [x] `schedule` - Task scheduling
- [x] `flask` - Monitoring dashboard

**Deliverable:**
- [ ] Dependencies installed
- [ ] `requirements.txt` updated

---

### **Step 7: Create Folders** (2 minutes)

Set up folder structure for local agent.

```powershell
# Create folders
mkdir local_data
mkdir local_data\backups
mkdir local_data\screenshots
mkdir local_data\cache
mkdir config
mkdir logs
mkdir logs\execution

# Create empty config file
New-Item -ItemType File -Path config\buddy_local_config.yaml
```

**Deliverable:**
- [ ] Folder structure created
- [ ] Empty config file ready

---

### **Step 8: Document Baseline** (10-15 minutes)

Create a comprehensive baseline report.

```powershell
# Run this script (creates report)
python scripts/create_baseline_report.py
```

**Or manually create:**

```markdown
# PHASE 0 BASELINE REPORT

Date: February 11, 2026

## Current System

**Cloud Run:**
- Cost: $____ /month (last 30 days)
- CPU: ____ %
- Memory: ____ %
- Requests: ____ /day

**Firebase:**
- Cost: $____ /month
- Reads: ____ /day
- Writes: ____ /day
- Storage: ____ MB

**Tools:**
- Total: ____
- Web nav: ____
- API: ____

## Laptop Capacity

**Specs:**
- RAM: ____ GB
- CPU: ____ cores
- OS: Windows ____

**Browser Capacity:**
- Safe maximum: ____ browsers
- RAM per browser: ____ MB
- Recommended: ____ browsers (70% RAM)

## Goals

**Cost Reduction Target:** 80-90%
- Current: $____ /month
- Target: $____ /month
- Savings: $____ /month

**Performance Target:**
- 20+ parallel browsers
- 95%+ success rate
- < 5s task latency
```

**Deliverable:**
- [ ] `PHASE0_BASELINE_REPORT.md` created

---

## 📋 Phase 0 Completion Checklist

Before moving to Phase 1, verify:

- [ ] Browser capacity tested (know safe maximum)
- [ ] Firebase usage analyzed (know current costs)
- [ ] Database schemas reviewed and understood
- [ ] Laptop specs documented
- [ ] Current system backed up
- [ ] Dependencies installed
- [ ] Folder structure created
- [ ] Baseline report written

**Estimated Time:** 2-3 hours total

---

## 🚀 Next Steps

Once Phase 0 is complete:

1. Review baseline report
2. Confirm goals are realistic
3. Start Phase 1: Local Agent Foundation
4. Build the core polling daemon

---

## 📊 Expected Findings

Based on typical setups:

**Browser Capacity:**
- 8 GB RAM laptop: 10-15 browsers
- 16 GB RAM laptop: 20-30 browsers
- 32 GB RAM laptop: 40-50 browsers

**Firebase Usage:**
- Current: $0-5/month (under free tier)
- Projected: $0-5/month (still under free tier)

**Cloud Run:**
- Current: $10-50/month (varies by usage)
- Projected: $2-10/month (10-20% of current)

---

## ❓ Troubleshooting

### Browser test fails to launch Chrome
```powershell
# Check ChromeDriver is installed
chromedriver --version

# If not, install via selenium-manager (automatic)
# Or download from: https://chromedriver.chromium.org/
```

### Firebase script errors
```powershell
# Check Firebase credentials
echo $env:FIREBASE_SERVICE_ACCOUNT

# If missing, set up application default credentials
gcloud auth application-default login
```

### Permission errors creating folders
```powershell
# Run PowerShell as Administrator
# Or use different location: Documents/BuddyLocal/
```

---

## 💡 Tips

1. **Browser test:** Start with lower batch sizes (3) if laptop is older
2. **Firebase:** If no service account, use app default credentials
3. **Backup:** Push git branch to GitHub for safety
4. **Time:** Take breaks between steps - no rush!

---

**Ready?** Start with Step 1: Test Browser Capacity! 🚀

---

**Document Version:** 1.0  
**Created:** February 11, 2026  
**Status:** Ready to Execute
