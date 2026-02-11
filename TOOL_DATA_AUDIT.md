# Tool Data Audit Report
**Date:** February 11, 2026  
**Total Tools:** 10 active tools

---

## Executive Summary

**Data Collection Status:** ✅ YES - All tools track usage  
**Data Persistence:** ⚠️ CONDITIONAL - Depends on Firebase enabled  
**Persistence Location:** Firebase Firestore (if enabled) or RAM (if disabled)  
**External API Logging:** ✅ YES - SerpAPI calls are logged with cost tracking

---

## Detailed Tool Audit

### **GROUP 1: Web & Research Tools (tools.py)**

#### 1. **web_search** 
- **Purpose:** Search the web via SerpAPI
- **Data Collected:**
  - Search query
  - Search results (organic results)
  - API usage metrics (searches used)
- **Saved Where:** 
  - ✅ **Tool Performance:** `tool_performance:web_search:_global` (memory/Firebase)
  - ✅ **External API Log:** `external_api_usage.jsonl` (SerpAPI calls with costs)
  - ✅ **Latency:** Running average tracked
- **Retention:** Last 10 calls in history
- **Persistence:** Yes (if Firebase enabled)

#### 2. **web_research**
- **Purpose:** Multi-step intelligent research across engines
- **Data Collected:**
  - Research query
  - Results from multiple search engines
  - Deduplication analysis
  - Confidence scores
- **Saved Where:**
  - ✅ **Tool Performance:** `tool_performance:web_research:_global` (memory/Firebase)
  - ✅ **External API Logs:** Via underlying search calls
  - ✅ **Latency:** Tracked
- **Retention:** Last 10 calls in history
- **Persistence:** Yes (if Firebase enabled)

#### 3. **reflect**
- **Purpose:** Reflect on tool effectiveness and suggest strategy improvements
- **Data Collected:**
  - Effectiveness scores (0.0-1.0)
  - What worked / what didn't
  - Tool feedback (usefulness scores per tool)
  - Strategy adjustments
  - Confidence adjustments
- **Saved Where:**
  - ✅ **Tool Performance:** `tool_performance:reflect:_global`
  - ✅ **Latency:** Running average
- **Retention:** Last 10 calls in history
- **Persistence:** Yes (if Firebase enabled)
- **Note:** Ephemeral analysis - no raw reflection data stored, only metrics

### **GROUP 2: Code Analysis Tools (tools.py)**

#### 4. **repo_index**
- **Purpose:** Analyze repository structure
- **Data Collected:**
  - Directory tree
  - File listing with types
  - File counts by category
  - Repository size metrics
- **Saved Where:**
  - ✅ **Tool Performance:** `tool_performance:repo_index:_global`
  - ✅ **Latency:** Running average
- **Retention:** Last 10 calls in history
- **Persistence:** Yes (if Firebase enabled)
- **Note:** Read-only, no side effects

#### 5. **file_summary**
- **Purpose:** Summarize a Python/JS/TS file
- **Data Collected:**
  - File path analyzed
  - File metadata
  - Code summary (functions, classes, etc.)
  - Complexity metrics
- **Saved Where:**
  - ✅ **Tool Performance:** `tool_performance:file_summary:_global`
  - ✅ **Latency:** Running average
- **Retention:** Last 10 calls in history
- **Persistence:** Yes (if Firebase enabled)
- **Note:** Read-only, no side effects

#### 6. **dependency_map**
- **Purpose:** Show module dependencies
- **Data Collected:**
  - Dependency graph
  - Module relationships
  - Import chains
- **Saved Where:**
  - ✅ **Tool Performance:** `tool_performance:dependency_map:_global`
  - ✅ **Latency:** Running average
- **Retention:** Last 10 calls in history
- **Persistence:** Yes (if Firebase enabled)
- **Note:** Read-only, no side effects

### **GROUP 3: Utility Tools (additional_tools.py)**

#### 7. **calculate**
- **Purpose:** Safely evaluate mathematical expressions
- **Data Collected:**
  - Expression string
  - Calculation result
  - Success/failure status
- **Saved Where:**
  - ✅ **Tool Performance:** `tool_performance:calculate:_global`
  - ✅ **Latency:** Running average
- **Retention:** Last 10 calls in history
- **Persistence:** Yes (if Firebase enabled)
- **Note:** No intermediate calculations stored (stateless)

#### 8. **read_file**
- **Purpose:** Read file contents (read-only, bounded to 100 lines)
- **Data Collected:**
  - File path
  - File content (up to 100 lines)
  - Line count
  - Truncation flag
- **Saved Where:**
  - ✅ **Tool Performance:** `tool_performance:read_file:_global`
  - ✅ **Latency:** Running average
- **Retention:** Last 10 calls in history
- **Persistence:** Yes (if Firebase enabled)
- **Note:** Read-only, no side effects

#### 9. **list_directory**
- **Purpose:** List directory contents
- **Data Collected:**
  - Directory path
  - Item names
  - Item types (file/dir)
  - File sizes
  - Item count
- **Saved Where:**
  - ✅ **Tool Performance:** `tool_performance:list_directory:_global`
  - ✅ **Latency:** Running average
- **Retention:** Last 10 calls in history
- **Persistence:** Yes (if Firebase enabled)
- **Note:** Read-only, no side effects

#### 10. **get_time**
- **Purpose:** Get current date and time
- **Data Collected:**
  - Date (MM/DD/YY)
  - Time (HH:MM AM/PM)
  - ISO format timestamp
  - Unix timestamp
- **Saved Where:**
  - ✅ **Tool Performance:** `tool_performance:get_time:_global`
  - ✅ **Latency:** Running average
- **Retention:** Last 10 calls in history
- **Persistence:** Yes (if Firebase enabled)
- **Note:** Minimal data, stateless

---

## Data Collection Architecture

### **Performance Tracking (Universal)**
Every tool call goes through `tool_registry.call()` which automatically records:

```
tool_performance:NAME:DOMAIN = {
    "tool_name": "...",
    "domain": "_global" or custom domain,
    "total_calls": N,
    "successful_calls": N,
    "failed_calls": N,
    "avg_latency_ms": X.XX,
    "last_used": "ISO timestamp",
    "failure_modes": [...],
    "history": [
        {
            "timestamp": "ISO timestamp",
            "success": bool,
            "latency_ms": X.XX,
            "failure_mode": str or null,
            "context": {args_count, kwargs_count}
        }
        // Last 10 calls only
    ],
    "created_at": "ISO timestamp"
}
```

**Storage:** Memory backend (MockMemory or FirebaseMemory)

### **External API Logging**
Certain tools that call external APIs also log costs:

- **web_search** → SerpAPI usage logged to `external_api_usage.jsonl`
- **web_research** → SerpAPI and other search engine calls logged
- Format: JSONL with timestamp, company, request_type, duration_ms, cost_usd

**Storage:** `Back_End/outputs/logs/external_api_usage.jsonl` (file-based)

---

## Storage Backends Comparison

| Aspect | MockMemory | FirebaseMemory |
|--------|-----------|-----------------|
| **Persistence** | ❌ No (RAM only) | ✅ Yes (Firestore) |
| **Survives Restart** | ❌ Lost on restart | ✅ Retained |
| **Scope** | Single process | Entire project |
| **Query Capability** | Python dict access | Firebase Firestore queries |
| **Collection** | In-memory dict | Firestore collection (configurable) |

**Current Configuration:** Check `Config.FIREBASE_ENABLED`

---

## What Data is NOT Being Saved

⚠️ **Tool Result Data** - The actual outputs of tools are NOT persisted:
- Search results from web_search (just returned in API response)
- File contents from read_file (just returned in API response)
- Code summaries from file_summary (just returned in API response)
- Directory listings from list_directory (just returned in API response)
- Calculation results (just returned in API response)

Only **metadata about tool execution** is saved (times called, success rate, latency).

---

## Audit Findings

### ✅ What's Working Well
1. All tool calls are tracked with latency metrics
2. Failure modes are documented
3. Success rates are calculated per tool per domain
4. External API costs are logged separately
5. Tool performance data persists to Firebase (if enabled)
6. History of last 10 calls retained for debugging

### ⚠️ What Needs Attention
1. **Tool Result Storage Missing:** If we need to keep search results, code analyses, etc., we need to add explicit persistence
2. **External API Logging Narrow:** Only SerpAPI logged; other tools (GoHighLevel, Microsoft Graph, Anthropic) have their own logging
3. **No Cross-Tool Correlation:** Can't easily see which tools were used together or in what sequence without looking at chat history
4. **Memory Growth:** Last 10 result example - history could grow large if tool is called frequently
5. **No TTL on Firestore Data:** Tool performance records accumulate indefinitely

### 🔧 Recommendations
1. Decide if tool **results** should be persisted (not just execution metrics)
2. Standardize external API logging across all tools
3. Add data retention policies (e.g., keep last 30 days only)
4. Create a tool usage analytics dashboard (similar to API Usage dashboard)
5. Add tool chaining/correlation tracking for complex workflows

---

## How to View Tool Data

### In Memory (Development)
```python
from Back_End.memory import memory
all_data = memory.get_all()
tool_stats = [k for k in all_data.keys() if k.startswith('tool_performance')]
```

### In Firebase (Production)
Collection: `app_state_cache` (configurable)  
Document IDs follow pattern: `tool_performance_TOOLNAME__global`

Example Firestore query:
```javascript
db.collection('app_state_cache')
  .where(firebase.firestore.FieldPath.documentId(), '>=', 'tool_performance')
  .where(firebase.firestore.FieldPath.documentId(), '<', 'tool_performancf')
  .get()
```

---

## Audit Completion Date
Generated: 2026-02-11 10:00 UTC  
Audited By: System Analysis  
Status: ✅ Complete - Ready for Review
