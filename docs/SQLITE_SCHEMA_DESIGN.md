# SQLite Schema Design - Local Agent Database

## Overview

The local SQLite database buffers data before Firebase sync, provides caching, and stores temporary execution state.

**Database File:** `local_data/buddy_local.db`

---

## Schema Design

### **Table 1: `tasks_queue`**
Stores pending tasks downloaded from Firebase.

```sql
CREATE TABLE tasks_queue (
    task_id TEXT PRIMARY KEY,
    type TEXT NOT NULL,                    -- 'web_navigate', 'data_processing', etc.
    params TEXT NOT NULL,                  -- JSON string of parameters
    priority TEXT DEFAULT 'NORMAL',        -- 'URGENT', 'NORMAL', 'BATCH'
    status TEXT DEFAULT 'pending',         -- 'pending', 'in_progress', 'completed', 'failed'
    retries INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error TEXT,
    assigned_browser INTEGER,              -- Browser pool index
    INDEX idx_status (status),
    INDEX idx_priority_created (priority, created_at)
);
```

**Purpose:** Local task queue for execution tracking

---

### **Table 2: `results_buffer`**
Stores completed results waiting to sync to Firebase.

```sql
CREATE TABLE results_buffer (
    result_id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    success BOOLEAN NOT NULL,
    data TEXT,                             -- JSON string of result data
    error TEXT,
    execution_time_ms INTEGER,
    screenshot_path TEXT,
    log_path TEXT,
    synced BOOLEAN DEFAULT 0,              -- 0 = not synced, 1 = synced
    sync_attempts INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    synced_at TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks_queue(task_id),
    INDEX idx_synced_created (synced, created_at)
);
```

**Purpose:** Buffer completed results for batch sync

---

### **Table 3: `cache`**
Caches web scraping results to avoid duplicate requests.

```sql
CREATE TABLE cache (
    cache_key TEXT PRIMARY KEY,            -- URL or unique identifier
    data TEXT NOT NULL,                    -- Cached data (JSON)
    data_type TEXT DEFAULT 'html',         -- 'html', 'json', 'text'
    size_bytes INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_expires (expires_at),
    INDEX idx_last_accessed (last_accessed)
);
```

**Purpose:** Reduce duplicate web requests (30-50% cache hit rate expected)

**Cache TTL:**
- Default: 24 hours
- Configurable per cache type
- Auto-cleanup of expired entries

---

### **Table 4: `learning_signals`**
Buffers selector learning signals for batch sync.

```sql
CREATE TABLE learning_signals (
    signal_id TEXT PRIMARY KEY,
    task_id TEXT,
    selector TEXT NOT NULL,
    selector_type TEXT,                    -- 'css', 'xpath', 'id', 'name'
    success BOOLEAN NOT NULL,
    context TEXT,                          -- URL, page title, etc.
    error_message TEXT,
    execution_time_ms INTEGER,
    synced BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    synced_at TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks_queue(task_id),
    INDEX idx_synced_created (synced, created_at)
);
```

**Purpose:** Collect selector performance data for self-healing system

---

### **Table 5: `browser_pool_state`**
Tracks browser health and usage.

```sql
CREATE TABLE browser_pool_state (
    browser_id INTEGER PRIMARY KEY,
    pid INTEGER,                           -- Process ID
    status TEXT DEFAULT 'idle',            -- 'idle', 'busy', 'crashed', 'restarting'
    current_task_id TEXT,
    tasks_completed INTEGER DEFAULT 0,
    launches INTEGER DEFAULT 1,
    memory_mb INTEGER,
    last_health_check TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    restarted_at TIMESTAMP,
    FOREIGN KEY (current_task_id) REFERENCES tasks_queue(task_id)
);
```

**Purpose:** Track browser health for pool management

---

### **Table 6: `sync_log`**
Logs sync operations for debugging.

```sql
CREATE TABLE sync_log (
    sync_id TEXT PRIMARY KEY,
    direction TEXT NOT NULL,               -- 'download' (FB→Local), 'upload' (Local→FB)
    record_type TEXT NOT NULL,             -- 'tasks', 'results', 'learning_signals'
    record_count INTEGER NOT NULL,
    success BOOLEAN NOT NULL,
    error TEXT,
    duration_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_created (created_at)
);
```

**Purpose:** Monitor sync health and performance

---

### **Table 7: `agent_metrics`**
Stores local agent performance metrics.

```sql
CREATE TABLE agent_metrics (
    metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tasks_completed INTEGER DEFAULT 0,
    tasks_failed INTEGER DEFAULT 0,
    average_execution_time_ms INTEGER,
    browsers_active INTEGER,
    ram_used_gb REAL,
    ram_percent REAL,
    cpu_percent REAL,
    cache_hit_rate REAL,
    sync_latency_ms INTEGER
);
```

**Purpose:** Track agent performance over time

---

### **Table 8: `schema_version`**
Tracks database migrations.

```sql
CREATE TABLE schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

-- Initial version
INSERT INTO schema_version (version, description) 
VALUES (1, 'Initial schema with 8 tables');
```

**Purpose:** Database migration management

---

## Indexes Strategy

### **Performance Indexes:**
- `idx_status` on `tasks_queue.status` - Fast pending task queries
- `idx_synced_created` on `results_buffer` - Fast unsynced result queries
- `idx_expires` on `cache.expires_at` - Fast cache cleanup
- `idx_created` on `sync_log` - Fast recent sync queries

### **Index Rationale:**
- Query patterns prioritize: "find pending tasks", "find unsynced results"
- Composite indexes (status + created_at) for sorted results
- Single-column indexes for simple filters

---

## Cleanup Strategy

### **Automatic Cleanup:**
```sql
-- Delete completed tasks older than 7 days
DELETE FROM tasks_queue 
WHERE status = 'completed' 
AND completed_at < datetime('now', '-7 days');

-- Delete synced results older than 7 days
DELETE FROM results_buffer 
WHERE synced = 1 
AND synced_at < datetime('now', '-7 days');

-- Delete expired cache entries
DELETE FROM cache 
WHERE expires_at < datetime('now');

-- Delete old metrics (keep 30 days)
DELETE FROM agent_metrics 
WHERE timestamp < datetime('now', '-30 days');

-- Delete old sync logs (keep 14 days)
DELETE FROM sync_log 
WHERE created_at < datetime('now', '-14 days');

-- Vacuum database weekly
VACUUM;

-- Analyze for query optimization
ANALYZE;
```

**Schedule:** Runs daily at 3 AM local time

---

## Query Patterns

### **Common Operations:**

#### Get Pending Tasks (Priority Order)
```sql
SELECT * FROM tasks_queue
WHERE status = 'pending'
ORDER BY 
    CASE priority
        WHEN 'URGENT' THEN 1
        WHEN 'NORMAL' THEN 2
        WHEN 'BATCH' THEN 3
    END,
    created_at ASC
LIMIT 20;
```

#### Get Unsynced Results
```sql
SELECT * FROM results_buffer
WHERE synced = 0
ORDER BY created_at ASC
LIMIT 50;
```

#### Cache Lookup
```sql
SELECT data FROM cache
WHERE cache_key = ?
AND expires_at > datetime('now')
AND data_type = ?;
```

#### Update Cache Access
```sql
UPDATE cache
SET access_count = access_count + 1,
    last_accessed = datetime('now')
WHERE cache_key = ?;
```

---

## Storage Estimates

### **Expected Database Size:**

**With 1,000 tasks/day:**
- tasks_queue: ~2 MB (7 days retention)
- results_buffer: ~5 MB (7 days retention)
- cache: ~50 MB (1,000 cached pages)
- learning_signals: ~3 MB
- browser_pool_state: < 1 MB
- sync_log: ~2 MB
- agent_metrics: ~1 MB

**Total: ~64 MB/month**

**With 5,000 tasks/day:**
- Total: ~320 MB/month

**Disk Space:** Allocate 1 GB for safety

---

## Concurrency Strategy

### **SQLite Settings:**
```python
# Connection pool settings
conn = sqlite3.connect(
    'buddy_local.db',
    check_same_thread=False,  # Allow multi-threading
    timeout=10.0               # Wait up to 10s for lock
)

# Enable WAL mode (Write-Ahead Logging)
conn.execute('PRAGMA journal_mode=WAL')

# Performance tuning
conn.execute('PRAGMA synchronous=NORMAL')  # Faster writes
conn.execute('PRAGMA cache_size=-64000')   # 64MB cache
conn.execute('PRAGMA temp_store=MEMORY')   # Temp tables in RAM
```

### **Write Strategy:**
- Use transactions for batch writes
- Single writer, multiple readers (SQLite limitation)
- Queue writes if database locked

---

## Migration Strategy

### **Version Control:**
Each schema change gets a new version number.

**Migration Files:**
- `migrations/001_initial.sql` - Initial schema
- `migrations/002_add_priority.sql` - Add priority field
- `migrations/003_add_indexes.sql` - Add performance indexes

**Apply Migrations:**
```python
def apply_migrations(conn):
    current_version = get_current_version(conn)
    migrations = load_migrations()
    
    for migration in migrations:
        if migration.version > current_version:
            conn.executescript(migration.sql)
            conn.execute(
                'INSERT INTO schema_version VALUES (?, ?)',
                (migration.version, migration.description)
            )
```

---

## Backup Strategy

### **Automated Backups:**
- **Frequency:** Daily at 2 AM
- **Location:** `local_data/backups/buddy_local_YYYYMMDD.db`
- **Retention:** Keep 7 days
- **Method:** SQLite `.backup` command

```python
import shutil
from datetime import datetime

def backup_database():
    source = 'local_data/buddy_local.db'
    timestamp = datetime.now().strftime('%Y%m%d')
    dest = f'local_data/backups/buddy_local_{timestamp}.db'
    shutil.copy2(source, dest)
    print(f"Backup created: {dest}")
```

---

## Security Considerations

### **Data Protection:**
- No sensitive credentials stored in SQLite
- Use Firebase for authentication tokens
- Environment variables for secrets
- File permissions: 600 (owner read/write only)

### **Encryption:**
SQLite database is NOT encrypted (local only, low risk).
- If needed: Use SQLCipher extension
- Trade-off: 10-15% performance penalty

---

## Next Steps (Phase 5)

1. Create `local_database.py` with schema
2. Implement migration system
3. Write query helper functions
4. Add cleanup automation
5. Test with 1,000+ records

---

**Document Version:** 1.0  
**Created:** February 11, 2026  
**Status:** Ready for Implementation
