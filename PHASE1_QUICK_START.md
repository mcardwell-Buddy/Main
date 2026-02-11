# Phase 1: Local Agent Foundation - Quick Start

## 🎯 Goal
Create basic local agent that can start, poll Firebase, and stop cleanly.

**Timeline:** 3-4 days  
**Status:** ✅ READY TO TEST

---

## 📦 What Was Created

### **1. Main Agent** - `Back_End/buddy_local_agent.py`
The core daemon that:
- Initializes Firebase and SQLite
- Runs a polling loop
- Updates heartbeat every 30 seconds
- Handles graceful shutdown (Ctrl+C)
- Logs everything to file and console

**Key Classes:**
- `BuddyLocalAgent` - Main agent daemon

**Key Methods:**
- `initialize()` - Set up Firebase & database
- `start()` - Start the daemon
- `stop()` - Clean graceful shutdown
- `_update_heartbeat()` - Send heart beat to Firebase
- `_main_loop()` - Main polling loop
- `get_status()` - Get current status

### **2. Configuration** - `config/buddy_local_config.yaml`
All agent settings in one place:
- Poll interval, heartbeat interval
- Browser limits (adjust based on Phase 0)
- Resource thresholds
- Timeouts and retry limits
- Database cleanup schedules

### **3. Config Manager** - `Back_End/config_manager.py`
Singleton pattern for configuration access:
```python
from config_manager import get_config

max_browsers = get_config('max_browsers')  # Get value
log_level = get_config('log_level')        # Get another
```

### **4. Startup Script** - `scripts/start_agent.py`
Easy way to start the agent:
```powershell
python scripts/start_agent.py --start
```

### **5. Tests** - `test_phase1.py`
Unit tests for foundation:
```powershell
python test_phase1.py
```

---

## ✅ Testing Phase 1

### **Test 1: Basic Agent Initialization**
```powershell
cd C:\Users\micha\Buddy
python test_phase1.py
```

Expected output:
```
test_agent_initialization ... ok
test_agent_id_persistence ... ok
test_config_manager ... ok
test_success_rate_calculation ... ok
...

Ran 8 tests in 0.234s
OK
```

### **Test 2: Agent Status Check**
```powershell
python Back_End/buddy_local_agent.py --status
```

Expected output:
```
======================================================================
📊 BUDDY LOCAL AGENT STATUS
======================================================================
agent_id             : local-MICHAEL-LAPTOP-12345678
status               : OFFLINE
uptime               : None
tasks_processed      : 0
tasks_failed         : 0
success_rate         : 100.0
start_time           : None
current_time         : 2026-02-11T15:30:45.123456
======================================================================
```

### **Test 3: Start Agent (30 seconds)**
```powershell
python Back_End/buddy_local_agent.py --start
```

Expected output:
```
======================================================================
🚀 STARTING BUDDY LOCAL AGENT
======================================================================

Initializing Buddy Local Agent (ID: local-MICHAEL-LAPTOP-12345678)
✅ Firebase initialized
✅ SQLite initialized
✅ Firebase connection verified
Agent ID: local-MICHAEL-LAPTOP-12345678
Start time: 2026-02-11 15:32:10
Version: 1.0.0
Status: READY

Starting main loop...
  Poll interval: 5s
  Heartbeat interval: 30s

✅ Heartbeat updated (uptime: 30s, processed: 0)
✅ Heartbeat updated (uptime: 60s, processed: 0)
✅ Heartbeat updated (uptime: 90s, processed: 0)

[Press Ctrl+C to stop...]
```

Then press `Ctrl+C`:
```
📍 Signal received. Initiating graceful shutdown...

======================================================================
🛑 STOPPING BUDDY LOCAL AGENT
======================================================================

✅ Database closed
Uptime: 0:01:35
Tasks processed: 0
Tasks failed: 0
Success rate: 100.0%
Status: OFFLINE
======================================================================
```

---

## 📊 What to Verify

### **Firebase Connection**
Check that heartbeats are being written to Firebase:

```javascript
// In Firebase Console:
// Go to: Firestore Database > agents > {agent_id} > heartbeat > current
// Should see a document with:
{
  "agent_id": "local-MICHAEL-LAPTOP-12345678",
  "status": "ONLINE",
  "last_heartbeat": "2026-02-11T15:32:40.123Z",
  "uptime_seconds": 150,
  "tasks_processed": 0,
  "updated_at": "2026-02-11T15:32:40.123Z"
}
```

### **SQLite Database**
Check that database was created:

```powershell
# Check file exists
ls local_data/

# Should see:
# Mode   LastWriteTime      Length Name
# ----   -------            ------ ----
# -a---  2/11/2026  3:32 PM  49152 buddy_local.db
# -a---  2/11/2026  3:32 PM  32768 buddy_local.db-shm
# -a---  2/11/2026  3:32 PM   2048 buddy_local.db-wal
```

### **Logs**
Check that logs are being written:

```powershell
tail -f logs/buddy_local.log
```

Should show heartbeat updates every 30 seconds.

---

## 🔑 Key Concepts (Phase 1)

### **Agent ID**
Unique identifier for your local agent:
- Format: `local-{hostname}-{random_8_hex}`
- Persisted in: `config/agent_id.txt`
- Identifies this specific installation

### **Heartbeat**
"I'm alive" signal to Firebase every 30 seconds:
- Location: `/agents/{agent_id}/heartbeat/current`
- Contains: status, uptime, tasks processed
- Used by task router to detect online agents

### **SQLite Database**
Local storage for task queue and results:
- Location: `local_data/buddy_local.db`
- Tables created: tasks_queue, results_buffer, agent_metrics
- Enables offline operation and buffering

### **Configuration**
Single source of truth for settings:
- File: `config/buddy_local_config.yaml`
- Loaded on startup
- Can be updated without restarting

### **Logging**
Comprehensive event tracking:
- File: `logs/buddy_local.log`
- Console: Real-time status
- Level: DEBUG by default (adjust in config)

---

## 📋 Phase 1 Checklist

Before moving to Phase 2, verify:

- [ ] Agent can start without errors
- [ ] Heartbeats appear in Firebase
- [ ] SQLite database created
- [ ] Logs being written
- [ ] Agent shuts down gracefully (Ctrl+C)
- [ ] All unit tests pass
- [ ] Agent ID persists (restart and verify same ID)
- [ ] Status command works

---

## 🛠️ Configuration Adjustments

Based on Phase 0 results (40 browsers, 141 MB/browser):

### Update `config/buddy_local_config.yaml`:

```yaml
# Your laptop has 19.7 GB RAM
# Recommendation: Set to 20-25 browsers (70% RAM usage)
max_browsers: 25  # Conservative starting point

# Can increase to 30, 50, or higher later
# but 25 is safe while testing other features
```

---

## 🚀 Next Steps

Once Phase 1 is confirmed working:

1. Move to Phase 2: Resource Monitoring
2. Add RAM/CPU tracking (psutil)
3. Implement auto-throttling
4. Build resource dashboard

---

## 💡 Tips

### **Debugging**
- Set `log_level: DEBUG` in config for verbose output
- Check `logs/buddy_local.log` for full details
- Use `--status` to check current state

### **Firebase**
- If connection fails, check `.env` file has `FIREBASE_SERVICE_ACCOUNT`
- Test: `echo $env:FIREBASE_SERVICE_ACCOUNT`

### **SQLite**
- To inspect database: `sqlite3 local_data/buddy_local.db`
- List tables: `.tables`
- View schema: `.schema`

### **Keep Running**
- Agent can run 24/7 in background
- Windows: Use Task Scheduler to auto-start
- Monitor via heartbeats in Firebase

---

## ❓ Troubleshooting

### Error: "ModuleNotFoundError: No module named 'firebase_admin'"
```powershell
pip install firebase-admin
```

### Error: "FIREBASE_SERVICE_ACCOUNT not found"
Check `.env` file:
```powershell
cat .env | grep FIREBASE_SERVICE_ACCOUNT
```

If missing, add it:
```
FIREBASE_SERVICE_ACCOUNT=/path/to/service-account.json
```

### Error: "Database is locked"
Agent already running on another terminal/process
```powershell
# Stop other instances
taskkill /F /IM python.exe

# Or check what's running
Get-Process python
```

### Agent starts but no heartbeats in Firebase
1. Check Firebase connection: `python Back_End/buddy_local_agent.py --status`
2. Check logs: `tail -f logs/buddy_local.log`
3. Verify service account has write permissions

---

## 📈 What's Next

Phase 1 is the foundation. Now we'll build on it:

- **Phase 2:** Add resource monitoring (RAM/CPU)
- **Phase 3:** Build browser pool (manage 20+ Chrome instances)
- **Phase 4:** Execute actual tasks
- **Phase 5:** Local database sync
- **Phase 6:** Firebase result sync
- ...and more!

Each phase builds on Phase 1's foundation.

---

**Ready?** Run the tests and start the agent! Let me know how it goes! 🚀

**Document Version:** 1.0  
**Created:** February 11, 2026  
**Status:** Ready to Execute
