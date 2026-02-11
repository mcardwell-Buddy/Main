# Phase 2: Resource Monitoring - Quick Start

## 🎯 Goal
Monitor system resources and prevent laptop crashes.

**Timeline:** 2-3 days  
**Status:** ✅ READY TO BUILD

---

## 📦 What We'll Build

A **ResourceMonitor** class that:
- Tracks RAM usage in real-time
- Monitors CPU usage
- Calculates safe browser count
- Auto-throttles when approaching limits
- Sends alerts when needed
- Shows real-time dashboard

---

## 🧪 Preview of Phase 2

### **You'll Be Able To Do:**

```python
from resource_monitor import ResourceMonitor

# Create monitor
monitor = ResourceMonitor()

# Get safe browser count (based on YOUR laptop)
safe_count = monitor.get_safe_browser_count()
print(f"Safe to run: {safe_count} browsers")
# Output: "Safe to run: 25 browsers"

# Get real-time status
status = monitor.get_system_status()
print(status)
# Output:
# {
#   'ram_used_gb': 10.5,
#   'ram_total_gb': 19.7,
#   'ram_percent': 53.3,
#   'cpu_percent': 42.1,
#   'browser_count_safe': 25,
#   'throttling': False
# }

# Check if approaching limit
if monitor.is_approaching_limit():
    print("Slowing down task acceptance...")
```

---

## 📊 Phase 2 Architecture

```
┌──────────────────────────────────┐
│   ResourceMonitor Class          │
├──────────────────────────────────┤
│                                  │
│  ├─ psutil integration          │
│  ├─ RAM tracking                │
│  ├─ CPU monitoring              │
│  ├─ Safe browser calculation    │
│  ├─ Threshold detection         │
│  └─ Alert system                │
│                                  │
└──────────────────────────────────┘
         ↓
    Store in SQLite
    BuddyLocalAgent
         ↓
    Used by Phase 3
    (Browser Pool)
```

---

## 🛠️ Phase 2 Components

### **1. ResourceMonitor Class**
Main monitoring class with:
- `__init__()` - Initialize with thresholds
- `get_system_status()` - Current RAM/CPU/browser count
- `get_safe_browser_count()` - How many browsers can run
- `is_approaching_limit()` - Check if near thresholds
- `should_throttle()` - Should we pause new tasks?
- `get_alerts()` - Any issues to report?
- `update_metrics()` - Store in database
- `start_monitoring()` - Optional background thread

### **2. Django/Flask Dashboard** (optional for Phase 2)
Beautiful web UI showing:
- Real-time RAM/CPU graphs
- Browser utilization
- Throttling status
- Historical data

### **3. Alert System**
Notifications when:
- RAM > 85% (warning)
- RAM > 90% (alert)
- CPU > 80% (warning)
- Expected to grow to

### **4. SQLite Integration**
Store metrics in `agent_metrics` table for:
- Historical tracking
- Performance analysis
- Trend detection

---

## 📝 What Phase 2 Will Create

```
Back_End/
├── resource_monitor.py          (NEW - 300 lines)
│   └── ResourceMonitor class
│   └── Metrics storage
│   └── Threshold logic
│
└── (Optional for Phase 2)
    └── dashboard.py             (NEW - 200 lines if included)
        └── Flask web app
        └── Real-time metrics
        └── Historical graphs

config/
└── buddy_local_config.yaml      (MODIFIED)
    └── New thresholds
    └── New limits

local_data/
└── buddy_local.db               (MODIFIED)
    └── agent_metrics table used
```

---

## ⚙️ Configuration for Phase 2

These will be in `buddy_local_config.yaml`:

```yaml
# Resource Thresholds
ram_warning_threshold_percent: 85
ram_shutdown_threshold_percent: 90
cpu_warning_threshold_percent: 80

# Browser Calculation
# Based on YOUR Phase 0 results: 19.7 GB, 40 browsers max
max_browsers_safe: 25              # 70% RAM usage
max_browsers_comfortable: 30       # 80% RAM usage
max_browsers_aggressive: 50        # 85% RAM usage (risky)

# Throttling
throttle_at_ram_percent: 75
pause_new_tasks_at_ram_percent: 85
emergency_stop_at_ram_percent: 95

# Monitoring
monitor_interval_seconds: 10
history_retention_hours: 24
```

---

## 🧪 Phase 2 Test Plan

After you build it:

### **Test 1: Normal Operation**
```python
monitor = ResourceMonitor()
status = monitor.get_system_status()
assert status['ram_percent'] < 80  # Should be under 80%
assert status['browser_count_safe'] == 25
```

### **Test 2: Safe Browser Count**
```python
# Should match your laptop capacity (from Phase 0)
safe_count = monitor.get_safe_browser_count()
assert 20 <= safe_count <= 30  # For 16-20 GB laptop
```

### **Test 3: Throttling Detection**
```python
# Run something to use RAM, then check
if monitor.is_approaching_limit():
    print("Throttling detected")
```

### **Test 4: Historical Data**
```python
# Run monitor for 1 hour
# Check that metrics are being stored
metrics = monitor.get_historical_metrics(hours=1)
assert len(metrics) >= 6  # At least 6 data points (10s interval)
```

---

## 💡 Expected Behavior

### **Phase 0 Results (Your Laptop)**
```
RAM: 19.7 GB
CPU: 12 cores
Max browsers: 40 (at 85% RAM)
Recommendation: 25 browsers (70% RAM)
```

### **Phase 2 Will Calculate**
```python
available_ram = 19.7 * 1024 * 0.7  # 13.79 GB at 70%
ram_per_browser = 141  # MB (from Phase 0)
safe_browsers = int(13.79 * 1024 / 141)
# Result: ~99 browsers (but we cap at 25 for safety)
```

---

## 🔗 Integration with Phase 1

Phase 2 integrates with Phase 1's agent:

```python
# In buddy_local_agent.py
from resource_monitor import ResourceMonitor

class BuddyLocalAgent:
    def __init__(self):
        # ... existing code ...
        self.resource_monitor = ResourceMonitor()
    
    def _main_loop(self):
        while self.running:
            # Check resources before polling tasks
            if self.resource_monitor.should_throttle():
                time.sleep(10)  # Back off
                continue
            
            # Update metrics
            self.resource_monitor.update_metrics()
            
            # ... rest of polling ...
```

---

## 🎯 Phase 2 Success Criteria

When Phase 2 is complete:

- [ ] ResourceMonitor class working
- [ ] Accurate RAM/CPU tracking
- [ ] Safe browser count calculated
- [ ] Throttling works correctly
- [ ] Alerts trigger at thresholds
- [ ] Metrics stored in SQLite
- [ ] Tests pass (manual and unit)
- [ ] Optional: Dashboard functional

---

## 🚀 Ready to Start Phase 2?

When ready, I'll create:

1. **`Back_End/resource_monitor.py`** - Full implementation
2. **Updated `buddy_local_agent.py`** - Integration
3. **Updated tests** - New unit tests for monitoring
4. **`PHASE2_DETAILED_GUIDE.md`** - Implementation details
5. **Optional dashboard** - Web UI for monitoring

---

## 📋 Phase 2 Prerequisites

Before starting Phase 2, verify:

- [ ] Phase 1 complete and working
- [ ] `local_data/buddy_local.db` created
- [ ] Agent can start/stop
- [ ] Tests pass

Already done? **Ready for Phase 2!** 🚀

---

## 🎯 Why Phase 2 Matters

**Resource monitoring is critical** for safety:

1. **Prevents Crashes**: Know before you hit the limit
2. **Protects Your Laptop**: Auto-throttles if needed
3. **Optimal Performance**: Runs max browsers without strain
4. **Historical Data**: Understand your system over time
5. **Smart Scaling**: Adjusts dynamically as load changes

Without Phase 2, you could accidentally crash your laptop by launching too many browsers.

**With Phase 2**, the agent self-regulates and keeps your system healthy.

---

## 💰 Impact

Phase 2 enables Phase 3-5:

- **Phase 3** needs resource info to manage browser pool
- **Phase 4** needs to know when to pause tasks
- **Phase 5** needs metrics for optimization

It's foundational for everything that follows.

---

## ⏱️ Timeline

- **Day 1:** Build ResourceMonitor class (100%)
- **Day 2:** Integration with BuddyLocalAgent
- **Day 3:** Testing and refinement

Then ready for Phase 3!

---

**Ready?** Just say "Let's do Phase 2!" and I'll build it all! 🚀

---

**Document Version:** 1.0  
**Date:** February 11, 2026  
**Status:** Ready for Implementation
