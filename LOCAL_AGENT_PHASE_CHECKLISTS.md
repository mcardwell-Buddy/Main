# ✅ Buddy Local Agent - Phase Checklists

## Quick Reference: Check off tasks as you build each phase

---

## 📋 PHASE 0: Preparation & Planning

**Goal:** Understand current system and plan implementation  
**Timeline:** 1-2 days  
**Critical:** Yes (sets foundation for everything)

### Tasks:
- [ ] Measure current Cloud Run costs (last 30 days)
  - Monthly average: $______
  - Peak day cost: $______
  - CPU usage: _____%
  - Memory usage: _____%

- [ ] Document Firebase current usage
  - Reads/day: ______
  - Writes/day: ______
  - Storage GB: ______
  - Current cost: $______/month

- [ ] Test local browser capacity
  - Launch 5 browsers: ⏱️ ____ seconds
  - Launch 10 browsers: ⏱️ ____ seconds  
  - Launch 20 browsers: ⏱️ ____ seconds (crashed? Y/N: ___)
  - Launch 30 browsers: ⏱️ ____ seconds (crashed? Y/N: ___)
  - **Safe maximum:** ____ browsers

- [ ] Check laptop specs
  - RAM: ____ GB
  - CPU: ____ cores
  - OS: Windows ____ / Mac ____ / Linux ____
  - Python version: ______

- [ ] Inventory existing tools
  - Total tools: ____
  - Web nav tools: ____
  - API tools: ____
  - Heavy resource tools: ____

- [ ] Design Firebase task queue
  - Queue path: `/tasks/pending/`
  - Task structure documented: ✅
  - Agent heartbeat path: `/agents/{agent_id}/heartbeat`

- [ ] Design SQLite schema
  - Tables identified: ____
  - Relationships mapped: ✅
  - Migration strategy: ✅

- [ ] Create test plan
  - Unit tests: ____ planned
  - Integration tests: ____ planned
  - Load tests: ____ planned

- [ ] Back up current system
  - Code backed up: ✅
  - Firebase exported: ✅
  - .env saved securely: ✅

### Deliverables:
- [ ] `PHASE0_BASELINE_REPORT.md` created
- [ ] `FIREBASE_SCHEMA_CURRENT.md` created
- [ ] `SQLITE_SCHEMA_DESIGN.md` created
- [ ] `TEST_PLAN.md` created

### Success Criteria:
✅ Know exact current costs  
✅ Know exact laptop capacity  
✅ Have complete schema designs  
✅ Have backed up everything  

---

## 📋 PHASE 1: Local Agent Foundation

**Goal:** Basic agent that can start, poll Firebase, and stop  
**Timeline:** 3-4 days  
**Critical:** Yes (foundation for all other phases)

### Tasks:
- [ ] Create `buddy_local_agent.py`
  - Main entry point created
  - Command-line args (--start, --stop, --status)
  - Agent runs as daemon

- [ ] Firebase authentication
  - Service account JSON downloaded
  - Firebase Admin SDK initialized
  - Authentication tested: ✅

- [ ] Task poller
  - Polls every ____ seconds (recommend 5)
  - Reads from Firebase path: ______
  - Handles empty queue gracefully
  - Logs polling activity

- [ ] SQLite setup
  - Database file: `buddy_local.db`
  - Initial schema applied
  - Connection handling (with pooling)

- [ ] Logging system
  - Log file: `logs/buddy_local.log`
  - Log rotation (daily/weekly)
  - Log levels (DEBUG, INFO, WARNING, ERROR)
  - Console output (pretty formatting)

- [ ] Agent heartbeat
  - Updates Firebase every ____ seconds (recommend 30)
  - Path: `/agents/{agent_id}/heartbeat`
  - Includes: timestamp, status, tasks_processed

- [ ] Graceful shutdown
  - Handles Ctrl+C
  - Finishes current task before stopping
  - Cleans up resources
  - Updates status to OFFLINE

- [ ] Configuration file
  - `config/buddy_local_config.yaml` created
  - Contains: Firebase path, poll interval, log settings
  - Loaded on startup

- [ ] Test polling
  - Agent starts: ✅
  - Agent polls Firebase: ✅
  - Agent logs "No tasks": ✅
  - Agent stops cleanly: ✅

### Code Files Created:
- [ ] `Back_End/buddy_local_agent.py` (main)
- [ ] `config/buddy_local_config.yaml`
- [ ] `local_data/buddy_local.db` (auto-created)

### Testing:
```bash
# Test 1: Start agent
python Back_End/buddy_local_agent.py --start
Expected: Agent starts, shows "Connected to Firebase"

# Test 2: Check status
python Back_End/buddy_local_agent.py --status
Expected: Shows ONLINE, uptime, tasks processed

# Test 3: Stop agent
python Back_End/buddy_local_agent.py --stop
Expected: Stops gracefully, shows summary
```

### Success Criteria:
✅ Agent starts and runs without errors  
✅ Polls Firebase successfully  
✅ SQLite database created  
✅ Logs are readable  
✅ Stops cleanly on Ctrl+C  
✅ Firebase shows agent ONLINE  

---

## 📋 PHASE 2: Resource Monitoring

**Goal:** Prevent laptop from crashing  
**Timeline:** 2-3 days  
**Critical:** Yes (safety system)

### Tasks:
- [ ] Install `psutil` library
  - `pip install psutil`
  - Test import: ✅

- [ ] Create `ResourceMonitor` class
  - File: `Back_End/resource_monitor.py`
  - Tracks RAM, CPU, disk

- [ ] RAM usage tracking
  - Get total RAM: ____ GB
  - Get available RAM: ____ GB
  - Calculate percentage used
  - Update every ____ seconds (recommend 10)

- [ ] CPU usage tracking
  - Get CPU percentage (per core)
  - Average across all cores
  - Detect high sustained usage

- [ ] Calculate safe browser count
  - Formula: `(available_RAM * 0.8) / 400MB`
  - Current safe count: ____
  - Updates dynamically

- [ ] Resource thresholds
  - 80% RAM: Slow down (stop launching new browsers)
  - 85% RAM: Throttle (pause non-urgent tasks)
  - 90% RAM: Alert (send warning)
  - 95% RAM: Emergency stop

- [ ] Real-time dashboard
  - Shows: RAM, CPU, browsers, tasks
  - Updates every ____ seconds
  - Uses `rich` library for pretty output

- [ ] Auto-throttling
  - Detects when approaching limits
  - Pauses new task acceptance
  - Completes current tasks first

- [ ] System warnings
  - Console warnings at 90%
  - Log warnings at 85%
  - Firebase alert at 95%

- [ ] Stress test
  - Launch browsers until 80% RAM
  - Verify auto-throttle works
  - Verify system stays stable

### Code Files Created:
- [ ] `Back_End/resource_monitor.py`

### Testing:
```python
# Test 1: Basic monitoring
from resource_monitor import ResourceMonitor
monitor = ResourceMonitor()
print(monitor.get_system_status())

# Test 2: Safe browser count
safe_count = monitor.get_safe_browser_count()
print(f"Safe to run: {safe_count} browsers")

# Test 3: Stress test
# Launch browsers until auto-throttle kicks in
```

### Success Criteria:
✅ Tracks RAM/CPU accurately  
✅ Calculates safe browser count  
✅ Throttles at 85% RAM  
✅ Alerts at 90% RAM  
✅ Never crashes laptop  
✅ Dashboard shows real-time stats  

---

## 📋 PHASE 3: Browser Pool Manager

**Goal:** Manage 20-30 Chrome instances efficiently  
**Timeline:** 5-7 days  
**Critical:** Yes (core capability)

### Tasks:
- [ ] Create `BrowserPoolManager` class
  - File: `Back_End/browser_pool_manager.py`
  - Manages pool of Chrome browsers

- [ ] Optimized Chrome options
  - Headless mode: Yes/No (recommend No for debugging)
  - Disable images: ✅ (saves 40% bandwidth)
  - Disable CSS: Optional
  - Window size: 1280x720 (smaller = less RAM)
  - Other optimizations: ________________

- [ ] Browser launch
  - Uses Selenium WebDriver
  - ChromeDriver path: ______
  - Launch time: ____ seconds per browser
  - Memory per browser: ____ MB

- [ ] Browser pool initialization
  - Pre-launch ____ browsers (recommend 5)
  - Warm browsers (load about:blank)
  - Store in pool (list/queue)

- [ ] Browser checkout/checkin
  - Checkout: Get available browser from pool
  - Checkin: Return browser to pool
  - Clear cookies/cache between tasks
  - Reset state

- [ ] Browser health checks
  - Ping browser every ____ seconds (recommend 30)
  - Check if responsive
  - Restart if hung

- [ ] Automatic restart on crash
  - Detect crash (WebDriver exception)
  - Remove from pool
  - Launch replacement
  - Log incident

- [ ] Browser cleanup
  - Close tabs
  - Clear cookies/cache
  - Release memory

- [ ] Session management
  - Track tasks per browser
  - Restart after ____ tasks (recommend 50)
  - Prevent memory leaks

- [ ] Parallel execution
  - Execute tasks across multiple browsers
  - Thread pool executor
  - Max threads: ____ (recommend browser count)

- [ ] Pool scaling
  - Grow pool when needed
  - Shrink pool when idle
  - Min browsers: ____ (recommend 3)
  - Max browsers: ____ (from ResourceMonitor)

- [ ] Test with varying loads
  - 1 browser: ✅
  - 5 browsers: ✅
  - 10 browsers: ✅
  - 20 browsers: ✅
  - Maximum browsers: ✅

- [ ] Memory leak detection
  - Run for 1 hour
  - Monitor memory growth
  - Restart browsers if leaking

### Code Files Created:
- [ ] `Back_End/browser_pool_manager.py`

### Testing:
```python
# Test 1: Pool initialization
pool = BrowserPoolManager(max_browsers=10)
pool.initialize()
assert len(pool.browsers) == 5  # Pre-launched

# Test 2: Checkout/checkin
browser = pool.checkout()
# Use browser
pool.checkin(browser)

# Test 3: Parallel execution
tasks = [task1, task2, ..., task20]
results = pool.execute_batch(tasks)
assert len(results) == 20

# Test 4: Stress test
# Run 100 tasks through pool
# Verify no crashes, no memory leaks
```

### Success Criteria:
✅ Can launch 20+ browsers  
✅ Pool management works correctly  
✅ Health checks detect failures  
✅ Auto-restart on crash works  
✅ Parallel execution successful  
✅ No memory leaks in 1-hour test  
✅ Graceful scaling up/down  

---

## 📋 PHASE 4: Task Execution Engine

**Goal:** Actually run web navigation tasks  
**Timeline:** 5-7 days  
**Critical:** Yes (does the work)

### Tasks:
- [ ] Create `TaskExecutor` class
  - File: `Back_End/task_executor.py`
  - Executes different task types

- [ ] Integration with WebNavigatorAgent
  - Import existing WebNavigatorAgent
  - Wrap in TaskExecutor interface
  - Pass browser from pool

- [ ] Task type handlers
  - `web_navigate`: Scraping, automation
  - `data_processing`: Local computation
  - `email_send`: Email tasks
  - Other: ________________

- [ ] Result formatting
  - Standardize result structure
  - Include: success, data, error, duration
  - Validate before returning

- [ ] Error handling
  - Catch all exceptions
  - Log errors with context
  - Return partial results if possible

- [ ] Retry logic
  - Retry failed tasks ____ times (recommend 3)
  - Exponential backoff: 5s, 15s, 45s
  - Different browser on retry

- [ ] Task timeout
  - Default timeout: ____ seconds (recommend 120)
  - Configurable per task
  - Kill browser if exceeded

- [ ] Partial result saving
  - Save progress periodically
  - Store in SQLite
  - Resume if task fails

- [ ] Screenshot capture
  - On success: Optional
  - On failure: Always
  - Store in: `local_data/screenshots/`

- [ ] Execution logging
  - Detailed trace of actions
  - Include: URLs visited, elements found, data extracted
  - Store in: `logs/execution/`

- [ ] Test with real tasks
  - Task 1: Scrape website: ✅
  - Task 2: Fill form: ✅
  - Task 3: Extract data: ✅
  - Task 4: Navigate multi-page: ✅

### Code Files Created:
- [ ] `Back_End/task_executor.py`

### Testing:
```python
# Test 1: Simple navigation
task = {"type": "web_navigate", "url": "https://example.com"}
result = executor.execute(task)
assert result["success"] == True

# Test 2: Failed task (retry)
task = {"type": "web_navigate", "url": "https://invalid.url"}
result = executor.execute(task)
assert result["retries"] == 3

# Test 3: Timeout
task = {"type": "web_navigate", "url": "...", "timeout": 5}
# Should timeout and return error

# Test 4: Screenshots
# Verify screenshot saved on failure
```

### Success Criteria:
✅ Successfully executes web nav tasks  
✅ Integrates with WebNavigatorAgent  
✅ Handles errors gracefully  
✅ Retry logic works  
✅ Timeouts work  
✅ Screenshots captured  
✅ Execution logs detailed  

---

## 📋 PHASE 5: Local Database & Buffering

**Goal:** Store data locally before Firebase sync  
**Timeline:** 3-4 days  
**Critical:** Yes (prevents data loss)

### Tasks:
- [ ] Complete SQLite schema
  - Tables: tasks, results, cache, learning_signals
  - Indexes for performance
  - Foreign keys for integrity

- [ ] Database migration system
  - Track schema version
  - Apply migrations automatically
  - Rollback if needed

- [ ] Task queue table
  - Stores: pending tasks from Firebase
  - Fields: task_id, type, params, status, created_at
  - Index on: status, created_at

- [ ] Results buffer table
  - Stores: completed results (not synced yet)
  - Fields: result_id, task_id, data, synced, created_at
  - Index on: synced, created_at

- [ ] Cache table
  - Stores: previously scraped URLs
  - Fields: url, data, expires_at
  - Avoid re-scraping same URLs
  - TTL: ____ hours (recommend 24)

- [ ] Learning signals buffer
  - Stores: selector success/failures
  - Fields: selector, success, context, created_at
  - Batch sync to Firebase

- [ ] Database cleanup
  - Purge old data (> 30 days)
  - Vacuum database weekly
  - Optimize indexes

- [ ] Query helpers
  - `get_pending_tasks()`
  - `save_result()`
  - `mark_synced()`
  - `get_cached(url)`

- [ ] Transaction safety
  - Use transactions for writes
  - Ensure atomicity
  - No partial writes

- [ ] Load test
  - Insert 1000 tasks: ✅
  - Query performance: < 10ms
  - No corruption

### Code Files Created:
- [ ] `Back_End/local_database.py`
- [ ] `Back_End/migrations/001_initial.sql`

### Testing:
```python
# Test 1: Insert tasks
db.insert_task({"type": "web_navigate", ...})
assert db.count_tasks() == 1

# Test 2: Save result
db.save_result(result_id, data)
assert db.get_result(result_id) == data

# Test 3: Cache lookup
cached = db.get_cached("https://example.com")
if cached and not cached.expired:
    # Use cached data

# Test 4: Transaction rollback
# Simulate error mid-transaction
# Verify no partial data saved
```

### Success Criteria:
✅ Schema complete and efficient  
✅ Migration system works  
✅ All CRUD operations work  
✅ Query performance < 10ms  
✅ No data corruption  
✅ Cleanup automation works  
✅ Handles 1000+ writes  

---

## 📋 PHASE 6: Firebase Sync Engine

**Goal:** Bidirectional sync between local and cloud  
**Timeline:** 5-7 days  
**Critical:** Yes (connects local to cloud)

### Tasks:
- [ ] Create `SyncEngine` class
  - File: `Back_End/sync_engine.py`
  - Handles all sync operations

- [ ] Firebase batch write
  - Batch size: ____ items (recommend 50)
  - Uses Firebase batch API
  - Handles rate limits

- [ ] Task download (Firebase → SQLite)
  - Poll for new tasks
  - Download to local database
  - Mark as pending_local

- [ ] Result upload (SQLite → Firebase)
  - Get unsynced results
  - Upload in batches
  - Mark as synced

- [ ] Conflict resolution
  - Timestamp-based (last write wins)
  - Or: Keep both versions
  - Log conflicts

- [ ] Sync scheduling
  - Sync every ____ seconds (recommend 60)
  - Can trigger manual sync
  - Adaptive interval (faster when busy)

- [ ] Retry logic
  - Retry failed syncs
  - Exponential backoff
  - Max retries: ____

- [ ] Sync prioritization
  - Urgent results sync immediately
  - Batch results sync every minute
  - Learning signals sync hourly

- [ ] Sync metrics
  - Track: items synced, bandwidth, latency
  - Log to SQLite
  - Display in dashboard

- [ ] Incremental sync
  - Only sync changed data
  - Use checksums/hashes
  - Reduces bandwidth 80-90%

- [ ] Offline mode test
  - Disconnect WiFi
  - Run 50 tasks
  - Reconnect WiFi
  - Verify auto-sync: ✅

- [ ] Network interruption test
  - Interrupt during sync
  - Verify retry works
  - Verify no data loss

### Code Files Created:
- [ ] `Back_End/sync_engine.py`

### Testing:
```python
# Test 1: Basic sync
sync.download_tasks()  # Firebase → Local
sync.upload_results()  # Local → Firebase

# Test 2: Batch upload
results = [result1, result2, ..., result50]
sync.upload_batch(results)
assert all synced

# Test 3: Offline mode
wifi.disconnect()
# Run tasks locally
wifi.connect()
sync.auto_sync()
# Verify all results in Firebase

# Test 4: Conflict resolution
# Modify same data on cloud and local
# Trigger sync
# Verify conflict handled correctly
```

### Success Criteria:
✅ Downloads tasks from Firebase  
✅ Uploads results to Firebase  
✅ Batch operations work  
✅ Offline mode works  
✅ Network interruption recovery  
✅ No data loss ever  
✅ Sync latency < 60 seconds  

---

## 📋 PHASE 7: Task Router (Cloud Side)

**Goal:** Route tasks to local vs cloud intelligently  
**Timeline:** 3-4 days  
**Critical:** Yes (orchestration)

### Tasks:
- [ ] Create `TaskRouter` class
  - File: `Back_End/task_router.py`
  - Runs in Cloud Run backend

- [ ] Agent discovery
  - Check Firebase for online agents
  - Path: `/agents/*/heartbeat`
  - Consider agent online if heartbeat < 60s old

- [ ] Routing logic decision tree
  - If web_navigate + local agent online → Local
  - If web_navigate + local agent offline → Cloud (fallback)
  - If API call → Cloud (always)
  - If urgent → Cloud (faster)
  - If batch → Local (cheaper)

- [ ] Task assignment
  - Write task to Firebase queue
  - Path: `/tasks/pending/{agent_id}/{task_id}`
  - Include: task_id, type, params, priority

- [ ] Load balancing
  - If multiple agents online
  - Distribute tasks evenly
  - Consider agent load (tasks in progress)

- [ ] Fallback logic
  - If local unavailable → Queue for cloud
  - If timeout waiting for local → Execute on cloud
  - Notify user: "Running on cloud (local unavailable)"

- [ ] Priority routing
  - Priority levels: URGENT, NORMAL, BATCH
  - URGENT → Always cloud (fastest)
  - NORMAL → Local preferred
  - BATCH → Local only (wait if needed)

- [ ] Routing metrics
  - Track: local_count, cloud_count, fallback_count
  - Store in Firebase
  - Display in dashboard

- [ ] Test routing scenarios
  - Scenario 1: Local ONLINE → Routes to local ✅
  - Scenario 2: Local OFFLINE → Routes to cloud ✅
  - Scenario 3: Multiple agents → Load balanced ✅
  - Scenario 4: URGENT task → Routes to cloud ✅

### Code Files Created:
- [ ] `Back_End/task_router.py`

### Testing:
```python
# Test 1: Local available
router = TaskRouter()
agent = router.find_available_agent("web_navigate")
assert agent.location == "local"

# Test 2: Local unavailable
# Stop local agent
agent = router.find_available_agent("web_navigate")
assert agent.location == "cloud"

# Test 3: Load balancing
# Start 2 local agents
tasks = [task1, task2, ..., task10]
assigned = router.assign_batch(tasks)
# Verify distributed across both agents
```

### Success Criteria:
✅ Discovers online agents  
✅ Routes correctly based on task type  
✅ Fallback to cloud works  
✅ Load balancing works  
✅ Priority routing works  
✅ Metrics tracked accurately  

---

## 📋 PHASE 8: Recipe System

**Goal:** Pre-built workflows for common tasks  
**Timeline:** 5-7 days  
**Critical:** Nice to have (huge time saver)

### Tasks:
- [ ] Design recipe JSON format
  - Structure: name, description, steps, parameters
  - Step types: navigate, click, fill, extract, wait
  - Example recipe documented

- [ ] Create `RecipeExecutor` class
  - File: `Back_End/recipe_executor.py`
  - Loads and executes recipes

- [ ] Recipe library structure
  - Folder: `recipes/`
  - Subfolders: ghl/, linkedin/, email/, general/
  - Naming: `verb_noun.json` (e.g., `create_page.json`)

- [ ] Recipe #1: GHL landing page
  - File: `recipes/ghl/create_landing_page.json`
  - Steps: Login → Sites → Create → Add sections → Publish
  - Tested: ✅

- [ ] Recipe #2: LinkedIn post
  - File: `recipes/linkedin/create_post.json`
  - Steps: Login → Start post → Write text → Upload image → Publish
  - Tested: ✅

- [ ] Recipe #3: Email sending
  - File: `recipes/email/send_gmail.json`
  - Steps: Login → Compose → Recipients → Write → Send
  - Tested: ✅

- [ ] Recipe #4: Web scraping
  - File: `recipes/general/scrape_directory.json`
  - Steps: Navigate → Extract list → Paginate → Aggregate
  - Tested: ✅

- [ ] Recipe #5: Form submission
  - File: `recipes/general/submit_form.json`
  - Steps: Navigate → Fill fields → Solve captcha → Submit
  - Tested: ✅

- [ ] Parameter substitution
  - Replace {variable_name} in recipe
  - Validate required parameters
  - Provide defaults for optional

- [ ] Recipe validation
  - Check JSON syntax
  - Validate step types
  - Verify parameters exist

- [ ] Testing framework
  - Test each recipe with sample data
  - Verify steps execute correctly
  - Check result format

- [ ] Recipe documentation
  - File: `RECIPE_AUTHORING_GUIDE.md`
  - Examples for each step type
  - Best practices

### Code Files Created:
- [ ] `Back_End/recipe_executor.py`
- [ ] `recipes/ghl/create_landing_page.json`
- [ ] `recipes/linkedin/create_post.json`
- [ ] `recipes/email/send_gmail.json`
- [ ] `recipes/general/scrape_directory.json`
- [ ] `recipes/general/submit_form.json`
- [ ] `RECIPE_AUTHORING_GUIDE.md`

### Testing:
```python
# Test 1: Load recipe
recipe = RecipeExecutor.load("ghl/create_landing_page")
assert recipe.name == "Create GHL Landing Page"

# Test 2: Execute recipe
params = {"page_name": "Test Page", "hero_text": "Welcome"}
result = recipe.execute(params)
assert result["success"] == True

# Test 3: Parameter validation
params = {}  # Missing required
try:
    recipe.execute(params)
    assert False  # Should raise error
except ValueError:
    assert True  # Expected

# Test 4: All recipes
# Execute each recipe with test data
# Verify all work
```

### Success Criteria:
✅ Recipe format documented  
✅ 5+ recipes working  
✅ Parameter substitution works  
✅ Validation catches errors  
✅ Testing framework functional  
✅ Documentation complete  

---

## 📋 PHASE 9: Tool Selector Enhancement

**Goal:** Prefer web_navigate when local available  
**Timeline:** 2-3 days  
**Critical:** Yes (activates cost savings)

### Tasks:
- [ ] Audit current tool selector
  - File: `Back_End/tool_selector.py`
  - Understand ranking algorithm
  - Document current logic

- [ ] Add local agent availability check
  - Query Firebase for agent heartbeat
  - Cache result (1 minute TTL)
  - Function: `is_local_agent_available()`

- [ ] Boost web_navigate confidence
  - If local available: +20% confidence
  - If local unavailable: No change
  - Only for tasks that CAN use web nav

- [ ] Update cost estimates
  - web_navigate (local): $0.00
  - web_navigate (cloud): $0.015
  - Affects tool ranking

- [ ] Modify ranking algorithm
  - Prefer web_navigate when:
    - Local agent available
    - Task is web-suitable
    - Confidence > 40%

- [ ] Add "web_nav_first" mode flag
  - Config: `web_nav_first: true`
  - When enabled: Always prefer web nav
  - Override other considerations

- [ ] Update tool selector tests
  - Test: web nav chosen when local available
  - Test: API chosen when web nav not suitable
  - Test: Fallback when local unavailable

- [ ] Integration test
  - Real task: "Find HR managers"
  - Before: Uses serp_search ($0.20)
  - After: Uses web_navigate ($0.00)
  - Verify savings

### Code Files Modified:
- [ ] `Back_End/tool_selector.py`

### Testing:
```python
# Test 1: Local available
# Task: Web scraping
tools = selector.select_tools(task)
assert tools[0].name == "web_navigate"

# Test 2: Local unavailable
# Stop local agent
tools = selector.select_tools(task)
assert tools[0].name == "serp_search"  # Fallback

# Test 3: API task (always cloud)
task = "Get GHL contacts"
tools = selector.select_tools(task)
assert tools[0].name == "ghl_list_contacts"

# Test 4: Web nav first mode
config["web_nav_first"] = True
tools = selector.select_tools(task)
assert tools[0].name == "web_navigate"
```

### Success Criteria:
✅ Detects local agent availability  
✅ Boosts web nav confidence  
✅ Cost estimates updated  
✅ Ranking algorithm works  
✅ Tests pass  
✅ Actual cost savings verified  

---

## 📋 PHASE 10: Integration & End-to-End Testing

**Goal:** Everything works together seamlessly  
**Timeline:** 5-7 days  
**Critical:** Yes (finds bugs)

### Tasks:

#### Integration Tests:
- [ ] Test 1: Mission planning → Local execution
  - User asks: "Find 10 HR managers"
  - Mission planned with web nav
  - Task routed to local agent
  - Agent executes successfully
  - Results synced to Firebase
  - User sees results

- [ ] Test 2: Multi-step mission
  - Mission with 10 steps
  - Mix of local and cloud tasks
  - All steps execute in order
  - Results aggregated correctly

- [ ] Test 3: 20 parallel browsers
  - Queue 20 tasks simultaneously
  - All execute in parallel
  - No crashes
  - All results correct

- [ ] Test 4: Fallback when local offline
  - Stop local agent
  - User asks question
  - Task routes to cloud
  - Completes successfully
  - User notified about fallback

- [ ] Test 5: Local agent restart mid-mission
  - Start long mission (20 tasks)
  - Restart agent after task 10
  - Agent resumes from task 11
  - All tasks complete

- [ ] Test 6: Network interruption
  - Disconnect WiFi mid-execution
  - Tasks buffer locally
  - Reconnect WiFi
  - Auto-sync completes
  - No data loss

- [ ] Test 7: Laptop sleep/wake
  - Start mission
  - Sleep laptop (close lid)
  - Wake laptop
  - Agent resumes
  - Mission completes

- [ ] Test 8: 100 tasks queued
  - Queue 100 web scraping tasks
  - Local agent processes all
  - Tracks progress
  - All complete successfully

- [ ] Test 9: Stress test (max browsers)
  - Run at max browser capacity
  - Monitor RAM/CPU
  - Verify auto-throttle works
  - Verify stability

- [ ] Test 10: Performance benchmark
  - Same task: Before (cloud) vs After (local)
  - Measure: Time, cost, success rate
  - Verify improvements

#### Load Tests:
- [ ] 24-hour continuous operation
  - Run agent for 24 hours
  - Process tasks regularly
  - Monitor stability
  - Check resource usage
  - Verify no memory leaks

- [ ] 48-hour memory leak test
  - Run agent for 48 hours
  - Monitor memory growth
  - Acceptable growth: < 100 MB/day
  - Restart if exceeds threshold

#### Cost Validation:
- [ ] Track actual costs for 1 week
  - Count local tasks: ____
  - Count cloud tasks: ____
  - Calculate savings: $____
  - Compare to baseline: ____%

### Test Results:
```
Test 1: Mission planning → Local execution     [✅ PASS]
Test 2: Multi-step mission                     [✅ PASS]
Test 3: 20 parallel browsers                   [✅ PASS]
Test 4: Fallback when local offline            [✅ PASS]
Test 5: Local agent restart mid-mission        [✅ PASS]
Test 6: Network interruption                   [✅ PASS]
Test 7: Laptop sleep/wake                      [✅ PASS]
Test 8: 100 tasks queued                       [✅ PASS]
Test 9: Stress test (max browsers)             [✅ PASS]
Test 10: Performance benchmark                 [✅ PASS]

Load Test 1: 24-hour operation                 [✅ PASS]
Load Test 2: 48-hour memory leak               [✅ PASS]

Cost Validation: $____ saved/week              [✅ VERIFIED]
```

### Success Criteria:
✅ All integration tests pass  
✅ All load tests pass  
✅ Cost savings verified  
✅ Performance improved  
✅ No critical bugs found  
✅ System stable for 48 hours  

---

## 📋 PHASE 11: Monitoring & Observability

**Goal:** Know what's happening at all times  
**Timeline:** 3-4 days  
**Critical:** Nice to have (operational excellence)

### Tasks:
- [ ] Create monitoring dashboard (web UI)
  - File: `Back_End/monitoring_dashboard.py`
  - Flask web app on http://localhost:5000

- [ ] Real-time metrics display
  - Agent status: ONLINE/OFFLINE/ERROR
  - Uptime: Hours and minutes
  - Tasks today: Count
  - Success rate: Percentage
  - Active browsers: Current / Max
  - RAM usage: Current / Total
  - CPU usage: Percentage
  - Cost saved: Today / This month

- [ ] Alert system
  - Email alerts: Via email_send_work
  - Telegram notifications: Via Telegram bot
  - Alert triggers:
    - Agent offline > 5 minutes
    - RAM > 90%
    - Success rate < 90%
    - Task failed 3+ times

- [ ] Health checks
  - Agent alive check
  - Browser pool health
  - Firebase connection
  - SQLite connection
  - Disk space check

- [ ] Performance graphs
  - Tasks per hour (last 24 hours)
  - Success rate trend (last 7 days)
  - RAM usage over time
  - Cost savings over time
  - Browser utilization

- [ ] Cost tracking dashboard
  - Local tasks count & cost ($0.00)
  - Cloud tasks count & cost
  - Total saved today
  - Total saved this month
  - Projected monthly savings

- [ ] Log aggregation
  - Central log viewer
  - Search logs by: date, level, keyword
  - Filter by: agent, task, error
  - Export logs (CSV, JSON)

- [ ] Automated reports
  - Daily summary email
  - Weekly performance report
  - Monthly cost analysis
  - Generate automatically

- [ ] Crash detection
  - Detect agent crash
  - Attempt auto-restart
  - Alert if restart fails
  - Log crash details

- [ ] Test monitoring
  - Simulate agent offline: Alert triggered ✅
  - Simulate high RAM: Alert triggered ✅
  - Dashboard displays correct data ✅
  - Graphs update in real-time ✅

### Code Files Created:
- [ ] `Back_End/monitoring_dashboard.py`
- [ ] `Back_End/alert_manager.py`
- [ ] `Back_End/report_generator.py`
- [ ] `templates/dashboard.html`

### Testing:
```bash
# Test 1: Start dashboard
python Back_End/monitoring_dashboard.py
# Open http://localhost:5000
# Verify displays correct data

# Test 2: Alert system
# Trigger alert condition (stop agent)
# Wait 5 minutes
# Verify alert received

# Test 3: Reports
python Back_End/report_generator.py --daily
# Verify report generated and emailed
```

### Success Criteria:
✅ Dashboard accessible and functional  
✅ Real-time metrics accurate  
✅ Alerts trigger correctly  
✅ Health checks work  
✅ Graphs display trends  
✅ Reports generate automatically  
✅ Log viewer functional  
✅ Crash detection works  

---

## 📋 PHASE 12: Documentation & User Guide

**Goal:** Easy to use and maintain  
**Timeline:** 2-3 days  
**Critical:** Yes (sustainability)

### Tasks:
- [ ] Installation guide
  - File: `docs/LOCAL_AGENT_INSTALLATION.md`
  - System requirements
  - Step-by-step install (Windows/Mac/Linux)
  - Troubleshooting common issues
  - Verification steps

- [ ] Quick start guide
  - File: `docs/LOCAL_AGENT_QUICK_START.md`
  - 5-minute setup
  - Start agent
  - Run first task
  - View results

- [ ] Configuration reference
  - File: `docs/LOCAL_AGENT_CONFIGURATION.md`
  - All config options explained
  - Default values
  - Recommended settings
  - Advanced tuning

- [ ] Troubleshooting guide
  - File: `docs/LOCAL_AGENT_TROUBLESHOOTING.md`
  - Common issues and solutions
  - Error messages explained
  - How to get help
  - Logs location

- [ ] Recipe authoring guide
  - File: `docs/RECIPE_AUTHORING_GUIDE.md`
  - Recipe format explained
  - Step types reference
  - Parameter system
  - Testing recipes
  - Best practices

- [ ] Architecture documentation
  - File: `docs/LOCAL_AGENT_ARCHITECTURE.md`
  - Component diagram
  - Data flow
  - Firebase structure
  - SQLite schema
  - For future reference

- [ ] Maintenance guide
  - File: `docs/LOCAL_AGENT_MAINTENANCE.md`
  - Update procedure
  - Backup strategy
  - Database cleanup
  - Log rotation
  - ChromeDriver updates

- [ ] FAQ document
  - File: `docs/LOCAL_AGENT_FAQ.md`
  - 20+ common questions
  - Clear, concise answers
  - Links to relevant docs

- [ ] Video tutorial (optional)
  - 10-minute walkthrough
  - Installation to first task
  - Upload to YouTube (private)
  - Link from README

- [ ] Cheat sheet
  - File: `docs/LOCAL_AGENT_CHEATSHEET.md`
  - Common commands
  - Quick reference
  - Troubleshooting checklist
  - Emergency procedures

### Documentation Checklist:
- [ ] All code commented
- [ ] All functions have docstrings
- [ ] README.md updated
- [ ] Examples provided
- [ ] Screenshots included
- [ ] Links working
- [ ] Spelling/grammar checked
- [ ] Tested by fresh user

### Success Criteria:
✅ Installation guide complete  
✅ Quick start works (5 minutes)  
✅ Configuration well-documented  
✅ Troubleshooting covers common issues  
✅ Recipe guide with examples  
✅ Architecture documented  
✅ Maintenance procedures clear  
✅ FAQ answers 20+ questions  
✅ Cheat sheet useful  

---

## 📋 PHASE 13: Production Rollout

**Goal:** Deploy safely to production  
**Timeline:** 7-14 days (gradual rollout)  
**Critical:** Yes (go-live)

### Week 1: Preparation
- [ ] Create rollout plan
  - File: `ROLLOUT_PLAN.md`
  - Gradual deployment strategy
  - Rollback procedures
  - Success criteria

- [ ] Production Firebase setup
  - Use production Firebase project
  - Or: Separate collection in existing
  - Export/import data if needed

- [ ] Deploy task router
  - Update Cloud Run backend
  - Deploy new `task_router.py`
  - Test cloud deployment

- [ ] Install local agent on your laptop
  - Follow installation guide
  - Configure for production
  - Test basic functionality

- [ ] Configure auto-start
  - Windows: Task Scheduler
  - Mac: launchd
  - Linux: systemd
  - Agent starts on boot

- [ ] Run in parallel with old system
  - Keep old system operational
  - Route 10% to new system
  - Monitor both systems

### Week 2: Gradual Rollout
- [ ] Day 1-2: 10% of tasks → Local
  - Monitor for issues
  - Compare results quality
  - Track cost savings

- [ ] Day 3-4: 30% of tasks → Local
  - Increase if Day 1-2 stable
  - Continue monitoring

- [ ] Day 5-6: 60% of tasks → Local
  - Ramp up significantly
  - Watch for issues

- [ ] Day 7: 90% of tasks → Local
  - Near-full migration
  - Keep 10% on cloud for safety

### Ongoing Monitoring:
- [ ] Task success rates (target: > 95%)
- [ ] Response times (target: < 5 seconds)
- [ ] Cost savings (target: > 80%)
- [ ] System stability (target: 99% uptime)
- [ ] User satisfaction (no complaints)

### Rollback Procedure (if needed):
- [ ] Stop local agent
- [ ] Disable task router
- [ ] Route all tasks to cloud
- [ ] Investigate issues
- [ ] Fix and retry

### Final Switchover:
- [ ] 100% hybrid mode (local preferred)
- [ ] Deprecate old cloud-only code paths
- [ ] Update documentation
- [ ] Celebrate savings! 🎉

### Success Criteria:
✅ Local agent stable in production  
✅ Task success rate > 95%  
✅ Cost savings > 80%  
✅ No critical issues  
✅ User experience improved  
✅ Auto-start working  
✅ Monitoring operational  

---

## 📋 PHASE 14: Optimization & Polish

**Goal:** Fine-tune everything  
**Timeline:** Ongoing  
**Critical:** Nice to have (continuous improvement)

### Performance Optimization:
- [ ] Profile browser memory usage
  - Use Chrome DevTools
  - Identify memory leaks
  - Fix inefficiencies

- [ ] Optimize Chrome launch time
  - Pre-warm browsers
  - Cache profiles
  - Current: ____ seconds → Target: ____ seconds

- [ ] Tune sync intervals
  - Test: 30s, 60s, 120s, 300s
  - Find sweet spot (latency vs efficiency)
  - Adaptive intervals based on load

- [ ] Improve recipe performance
  - Cache common pages
  - Optimize selectors
  - Reduce wait times

- [ ] Add caching for repeated scraping
  - Cache TTL: ____ hours
  - Cache hit rate: ____%
  - Bandwidth saved: ____%

- [ ] Implement smart browser reuse
  - Keep logged-in sessions
  - Reuse for same-domain tasks
  - Session lifetime: ____ minutes

### Analytics & Insights:
- [ ] Build analytics dashboard
  - Most common tasks
  - Performance trends
  - Cost breakdown by task type
  - Recommendations for improvement

- [ ] Add ML-based resource prediction
  - Predict browser count needed
  - Predict RAM usage
  - Pre-scale proactively

- [ ] Create performance benchmarks
  - Standardized test suite
  - Track improvements over time
  - Compare to baselines

### Continuous Improvement:
- [ ] Weekly performance reviews
  - Check metrics
  - Identify bottlenecks
  - Plan improvements

- [ ] Monthly optimization sprints
  - Pick top 3 issues
  - Fix and measure
  - Deploy improvements

- [ ] User feedback loop
  - Collect feedback
  - Prioritize features
  - Implement most requested

### Success Criteria:
✅ Browser launch < 2 seconds  
✅ Cache hit rate > 30%  
✅ Sync latency < 30 seconds  
✅ Resource prediction accurate  
✅ Performance improving monthly  
✅ User satisfaction high  

---

## 🎯 Final Checklist: System Complete

Before considering the system "done":

### Functionality:
- [x] Agent starts/stops cleanly
- [ ] Executes tasks successfully
- [ ] Syncs results to Firebase
- [ ] Falls back to cloud when offline
- [ ] Handles errors gracefully
- [ ] Recovers from crashes
- [ ] Scales to 20+ browsers
- [ ] Respects resource limits

### Reliability:
- [ ] Runs for 24 hours without issues
- [ ] Survives laptop sleep/wake
- [ ] Handles network interruptions
- [ ] No memory leaks (48-hour test)
- [ ] Auto-restarts on crash

### Performance:
- [ ] Task latency < 5 seconds
- [ ] Sync latency < 60 seconds
- [ ] 95%+ success rate
- [ ] Saves 80%+ on costs

### Usability:
- [ ] Install in < 10 minutes
- [ ] Start with single command
- [ ] Dashboard shows status
- [ ] Logs are readable
- [ ] Alerts work

### Documentation:
- [ ] Installation guide complete
- [ ] Quick start guide tested
- [ ] Troubleshooting covers common issues
- [ ] Code is commented
- [ ] Architecture documented

### Production:
- [ ] Running in production
- [ ] Stable for 1 week
- [ ] Cost savings verified
- [ ] User satisfied
- [ ] Monitoring operational

---

## 🎉 Completion!

When ALL checkboxes above are checked:

**YOU DID IT!** 🚀

You now have:
- ✅ Local agent running 20-30 browsers
- ✅ 80-90% cost reduction ($2,000-3,400/year saved)
- ✅ Universal web nav capability (no API limits)
- ✅ Stable, reliable, self-healing system
- ✅ Beautiful monitoring dashboard
- ✅ Complete documentation

**Next:** Enjoy the savings and build cool stuff! 😊

---

**Document Version:** 1.0  
**Created:** February 11, 2026  
**Purpose:** Phase-by-phase checklist for implementation
