# Firebase Queue Design - Task Routing

## Overview

Firebase Firestore serves as the communication layer between Cloud Run and local agents.

---

## Firebase Structure

```
firestore/
├── agents/
│   └── {agent_id}/
│       ├── heartbeat (document)
│       ├── configuration (document)
│       └── metrics (document)
│
├── tasks/
│   ├── pending/
│   │   └── {task_id} (document)
│   ├── assigned/
│   │   └── {agent_id}/
│   │       └── {task_id} (document)
│   ├── completed/
│   │   └── {task_id} (document)
│   └── failed/
│       └── {task_id} (document)
│
├── results/
│   └── {result_id} (document)
│
├── missions/ (existing)
├── sessions/ (existing)
└── configuration/ (existing)
```

---

## Collection Schemas

### **1. `/agents/{agent_id}/heartbeat`**

**Purpose:** Track agent online status

```javascript
{
  agent_id: "local-laptop-001",
  agent_type: "local",              // 'local' or 'cloud'
  status: "ONLINE",                 // 'ONLINE', 'OFFLINE', 'ERROR', 'RESTARTING'
  last_heartbeat: Timestamp,
  uptime_seconds: 14523,
  
  // Capacity info
  max_browsers: 25,
  active_browsers: 12,
  tasks_in_progress: 12,
  available_slots: 13,
  
  // Resource usage
  ram_used_gb: 10.5,
  ram_total_gb: 16.0,
  ram_percent: 65.6,
  cpu_percent: 42.3,
  
  // Performance
  tasks_completed_today: 127,
  success_rate_today: 98.4,
  average_task_time_ms: 8500,
  
  // Version info
  version: "1.0.0",
  hostname: "MICHAEL-LAPTOP",
  ip_address: "192.168.1.100",
  
  created_at: Timestamp,
  updated_at: Timestamp
}
```

**Update Frequency:** Every 30 seconds  
**Stale Threshold:** 60 seconds (consider offline)

---

### **2. `/agents/{agent_id}/configuration`**

**Purpose:** Agent-specific configuration

```javascript
{
  // Browser settings
  max_browsers: 25,
  browser_launch_timeout_ms: 30000,
  browser_restart_after_tasks: 50,
  enable_headless: false,
  
  // Task settings
  max_concurrent_tasks: 20,
  task_timeout_ms: 120000,
  retry_limit: 3,
  
  // Resource settings
  ram_throttle_threshold: 85,
  ram_warning_threshold: 90,
  cpu_throttle_threshold: 80,
  
  // Sync settings
  sync_interval_seconds: 60,
  batch_size: 50,
  
  // Cache settings
  cache_enabled: true,
  cache_ttl_hours: 24,
  cache_max_size_mb: 500,
  
  updated_at: Timestamp
}
```

---

### **3. `/agents/{agent_id}/metrics`**

**Purpose:** Agent performance metrics (updated hourly)

```javascript
{
  hour: "2026-02-11T15:00:00Z",
  
  tasks_completed: 47,
  tasks_failed: 2,
  success_rate: 95.9,
  
  average_execution_time_ms: 8200,
  min_execution_time_ms: 1200,
  max_execution_time_ms: 45000,
  
  browsers_peak: 20,
  browsers_average: 15,
  
  ram_peak_percent: 78.5,
  ram_average_percent: 62.3,
  
  cpu_peak_percent: 82.1,
  cpu_average_percent: 45.6,
  
  cache_hit_rate: 32.5,
  
  created_at: Timestamp
}
```

---

### **4. `/tasks/pending/{task_id}`**

**Purpose:** Tasks waiting to be assigned

```javascript
{
  task_id: "task_abc123",
  type: "web_navigate",
  params: {
    url: "https://example.com",
    action: "scrape",
    selectors: {...}
  },
  
  priority: "NORMAL",              // 'URGENT', 'NORMAL', 'BATCH'
  
  // Routing preferences
  prefer_local: true,              // Prefer local agent if available
  require_local: false,            // Must use local (don't fallback to cloud)
  timeout_ms: 120000,
  
  // Mission context
  mission_id: "mission_xyz789",
  step_number: 3,
  step_total: 10,
  
  // Metadata
  user_id: "user_123",
  created_by: "cloud_orchestrator",
  created_at: Timestamp,
  expires_at: Timestamp            // Auto-delete if not picked up
}
```

**Lifecycle:**
1. Created by Cloud Run orchestrator
2. Task router assigns to agent
3. Moved to `/tasks/assigned/{agent_id}/{task_id}`
4. Agent processes task
5. Moved to `/tasks/completed/` or `/tasks/failed/`
6. Auto-deleted after 7 days

---

### **5. `/tasks/assigned/{agent_id}/{task_id}`**

**Purpose:** Tasks assigned to specific agent

```javascript
{
  ...all fields from pending task...
  
  assigned_to: "local-laptop-001",
  assigned_at: Timestamp,
  assignment_expires_at: Timestamp,  // If not started, reassign
  
  status: "assigned",                // 'assigned', 'in_progress'
  started_at: Timestamp,
  browser_id: 5
}
```

**Assignment Timeout:** 5 minutes  
If agent doesn't start task within 5 minutes, task is reassigned.

---

### **6. `/tasks/completed/{task_id}`**

**Purpose:** Successfully completed tasks

```javascript
{
  task_id: "task_abc123",
  type: "web_navigate",
  
  status: "completed",
  result_id: "result_xyz789",      // Link to /results/{result_id}
  
  executed_by: "local-laptop-001",
  execution_time_ms: 8500,
  browser_id: 5,
  
  completed_at: Timestamp,
  auto_delete_at: Timestamp        // 7 days after completion
}
```

---

### **7. `/tasks/failed/{task_id}`**

**Purpose:** Failed tasks (for debugging)

```javascript
{
  ...all fields from pending task...
  
  status: "failed",
  error: "TimeoutError: Navigation took longer than 120s",
  error_type: "TimeoutError",
  stack_trace: "...",
  
  executed_by: "local-laptop-001",
  attempts: 3,
  
  failed_at: Timestamp,
  auto_delete_at: Timestamp        // 7 days
}
```

---

### **8. `/results/{result_id}`**

**Purpose:** Task execution results

```javascript
{
  result_id: "result_xyz789",
  task_id: "task_abc123",
  
  success: true,
  data: {
    extracted_items: [...],
    page_title: "Example Domain",
    url: "https://example.com"
  },
  
  execution_time_ms: 8500,
  retries: 0,
  
  // Screenshots & logs
  screenshot_url: "gs://buddy-screenshots/result_xyz789.png",
  log_url: "gs://buddy-logs/result_xyz789.log",
  
  // Metadata
  executed_by: "local-laptop-001",
  browser_id: 5,
  cache_hit: false,
  
  created_at: Timestamp,
  auto_delete_at: Timestamp        // 30 days
}
```

---

## Task Routing Flow

### **Cloud Side (Task Router):**

```javascript
function routeTask(task) {
  // 1. Check for online agents
  const agents = await getOnlineAgents()
  
  if (agents.length === 0) {
    // No agents available, use cloud fallback
    return routeToCloud(task)
  }
  
  // 2. Filter by capability
  const capableAgents = agents.filter(a => 
    canHandle(a, task.type) && 
    a.available_slots > 0
  )
  
  if (capableAgents.length === 0) {
    if (task.require_local) {
      // Queue for later
      return queueForLocal(task)
    } else {
      // Fallback to cloud
      return routeToCloud(task)
    }
  }
  
  // 3. Select best agent (load balancing)
  const agent = selectBestAgent(capableAgents, task)
  
  // 4. Assign task
  await assignTask(agent.agent_id, task)
}

function getOnlineAgents() {
  const now = Date.now()
  const agents = await db.collection('agents')
    .where('status', '==', 'ONLINE')
    .get()
  
  // Filter by heartbeat freshness
  return agents.filter(a => 
    (now - a.last_heartbeat.toMillis()) < 60000  // < 60s old
  )
}

function selectBestAgent(agents, task) {
  // Priority 1: Most available slots
  // Priority 2: Best success rate
  // Priority 3: Lowest response time
  
  return agents.sort((a, b) => {
    if (a.available_slots !== b.available_slots) {
      return b.available_slots - a.available_slots
    }
    return b.success_rate_today - a.success_rate_today
  })[0]
}

async function assignTask(agentId, task) {
  // Move task to assigned
  const assignedPath = `tasks/assigned/${agentId}/${task.task_id}`
  await db.doc(assignedPath).set({
    ...task,
    assigned_to: agentId,
    assigned_at: Timestamp.now(),
    assignment_expires_at: Timestamp.now() + 300000,  // 5 minutes
    status: 'assigned'
  })
  
  // Delete from pending
  await db.doc(`tasks/pending/${task.task_id}`).delete()
}
```

---

### **Local Side (Agent):**

```javascript
function pollForTasks() {
  const agentId = config.agent_id
  
  // Listen for assigned tasks
  db.collection(`tasks/assigned/${agentId}`)
    .where('status', '==', 'assigned')
    .onSnapshot(snapshot => {
      snapshot.docChanges().forEach(change => {
        if (change.type === 'added') {
          const task = change.doc.data()
          executeTask(task)
        }
      })
    })
}

async function executeTask(task) {
  // 1. Update status
  await updateTaskStatus(task.task_id, {
    status: 'in_progress',
    started_at: Timestamp.now()
  })
  
  // 2. Checkout browser
  const browser = await browserPool.checkout()
  
  try {
    // 3. Execute
    const result = await taskExecutor.execute(task, browser)
    
    // 4. Save result
    const resultId = await saveResult(result)
    
    // 5. Move to completed
    await moveToCompleted(task.task_id, resultId)
  
  } catch (error) {
    // Handle failure
    await moveToFailed(task.task_id, error)
  
  } finally {
    // 6. Return browser to pool
    await browserPool.checkin(browser)
  }
}
```

---

## Sync Strategy

### **Download Tasks (Firebase → Local):**
- **Method:** Firestore onSnapshot listener
- **Frequency:** Real-time
- **Filter:** Only tasks assigned to this agent

### **Upload Results (Local → Firebase):**
- **Method:** Batch writes
- **Frequency:** Every 60 seconds
- **Batch Size:** 50 results

```javascript
async function syncResults() {
  const batch = db.batch()
  
  // Get unsynced results from SQLite
  const results = await localDb.getUnsyncedResults(50)
  
  results.forEach(result => {
    const ref = db.collection('results').doc(result.result_id)
    batch.set(ref, result)
  })
  
  await batch.commit()
  
  // Mark as synced in SQLite
  await localDb.markSynced(results.map(r => r.result_id))
}
```

---

## Firestore Indexes

### **Required Composite Indexes:**

```
Collection: agents
Fields: status ASC, last_heartbeat DESC

Collection: tasks/pending
Fields: priority ASC, created_at ASC

Collection: tasks/assigned/{agentId}
Fields: status ASC, assigned_at ASC
```

**Create via Firebase Console:** 
Firestore will prompt you when queries need indexes.

---

## Security Rules

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    
    // Agents: Only agent can write its own data
    match /agents/{agentId} {
      allow read: if true;  // Anyone can read agent status
      allow write: if request.auth.uid == agentId;
    }
    
    // Tasks: Cloud can write, agents can read/update assigned tasks
    match /tasks/{status}/{taskId} {
      allow read: if true;
      allow write: if request.auth.token.admin == true;  // Only cloud
    }
    
    match /tasks/assigned/{agentId}/{taskId} {
      allow read, write: if request.auth.uid == agentId;
    }
    
    // Results: Agents can write, anyone can read
    match /results/{resultId} {
      allow read: if true;
      allow write: if request.auth != null;
    }
  }
}
```

---

## Cost Optimization

### **Firestore Operations:**

**Current (All Cloud):**
- Reads: ~1,000/day (within free tier)
- Writes: ~500/day (within free tier)

**With Local Agent:**
- Reads: ~5,000/day (agent polling, still within free tier)
- Writes: ~1,500/day (heartbeats + results, still free)

**Optimization:**
- Batch writes (50x reduction)
- Cache heartbeats (refresh every 30s instead of 5s)
- Use Firestore listeners (no polling overhead)
- Aggregate metrics (hourly instead of per-task)

**Expected Cost:** $0/month (well within free tier)

---

## Monitoring Queries

### **Get Agent Status:**
```javascript
const agent = await db.doc('agents/local-laptop-001/heartbeat').get()
console.log(`Status: ${agent.status}, Tasks: ${agent.tasks_in_progress}`)
```

### **Get Pending Tasks Count:**
```javascript
const snapshot = await db.collection('tasks/pending').count().get()
console.log(`Pending: ${snapshot.data().count}`)
```

### **Get Agent Performance:**
```javascript
const metrics = await db.doc('agents/local-laptop-001/metrics').get()
console.log(`Success rate: ${metrics.success_rate}%`)
```

---

## Next Steps (Phase 7)

1. Implement task router in Cloud Run
2. Create agent discovery logic
3. Build task assignment system
4. Add fallback routing
5. Test with multiple agents

---

**Document Version:** 1.0  
**Created:** February 11, 2026  
**Status:** Ready for Implementation
