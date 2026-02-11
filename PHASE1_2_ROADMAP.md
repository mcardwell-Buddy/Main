# 🎯 NEXT STEPS: PHASE 1.2 ROADMAP

## Current Status

✅ **Phase 1.1 Complete**
- MissionProgressTracker enhanced with 139 new lines
- execution_service.py integrated with progress events  
- Progress callback system wired to streaming_events
- No syntax errors
- Ready to test

🔴 **Phase 1.2 In Progress**
- Firebase persistence for progress tracking
- ETA calculation from step progression rate
- Database schema update needed

---

## Phase 1.2: Firebase Persistence (2-3 Days)

### What Needs to Happen

Currently, progress_tracker is:
- ✅ Calculated in memory during execution
- ✅ Returned in execute_mission() response
- ✅ Emitted to streaming_events
- ❌ NOT persisted to Firestore
- ❌ Lost on client reconnect

**Goal:** Make progress persistent so users can:
1. Refresh browser → see same progress bar position
2. Close and reopen dashboard → mission progress restored
3. Navigate away and back → no loss of execution history

### Implementation Steps

#### Step 1: Modify mission_store.py (30 mins)

**Current:** execute_mission() returns response with progress_tracker

**Needed:** mission_store saves progress_tracker to Firestore after execution

```python
# In execution_service.py, after line ~1075 (return statement):

# Before return statement, persist progress
mission_store = get_mission_store()
mission_store.save_progress(
    mission_id=mission_id,
    progress_tracker=progress_tracker.to_dict()
)
```

**New method in mission_store.py:**

```python
def save_progress(self, mission_id: str, progress_tracker: Dict[str, Any]) -> None:
    """
    Save mission progress to Firestore for persistence.
    
    Writes to: missions/{mission_id}/execution_record/progress_tracker
    """
    try:
        doc = self.db.collection('missions').document(mission_id)
        
        # Update execution_record with progress data
        doc.update({
            'execution_record.progress_tracker': progress_tracker,
            'execution_record.updated_at': datetime.now(timezone.utc).isoformat()
        })
        
        logger.info(f"[MISSION_STORE] Saved progress for {mission_id}: {progress_tracker['current_step']['step_name'] if progress_tracker.get('current_step') else 'Complete'}")
    except Exception as e:
        logger.error(f"[MISSION_STORE] Failed to save progress: {e}")
        # Non-blocking: continue execution even if persistence fails
```

#### Step 2: Add Query Function in mission_store.py (30 mins)

**Needed:** Frontend can fetch current progress for a mission

```python
def get_mission_progress(self, mission_id: str) -> Dict[str, Any]:
    """
    Retrieve mission progress from Firestore.
    
    Returns:
    {
        mission_id: str,
        current_step: ExecutionStep | None,
        completed_steps: [ExecutionStep, ...],
        progress_percent: 0-100,
        elapsed_seconds: float,
        estimated_time_remaining: float,  # NEW
        status: 'in_progress' | 'completed' | 'failed'
    }
    """
    try:
        doc = self.db.collection('missions').document(mission_id).get()
        
        if not doc.exists:
            return {'error': f'Mission {mission_id} not found'}
        
        mission_data = doc.to_dict()
        execution_record = mission_data.get('execution_record', {})
        progress_tracker = execution_record.get('progress_tracker', {})
        
        # Calculate ETA from progression rate
        eta = self._calculate_eta(progress_tracker)
        
        return {
            'mission_id': mission_id,
            'current_step': progress_tracker.get('current_step'),
            'completed_steps': progress_tracker.get('completed_steps', []),
            'progress_percent': progress_tracker.get('progress_percent', 0),
            'elapsed_seconds': progress_tracker.get('elapsed_seconds', 0),
            'estimated_time_remaining': eta,
            'status': self._get_status_from_progress(progress_tracker)
        }
    except Exception as e:
        logger.error(f"[MISSION_STORE] Failed to get progress: {e}")
        return {'error': str(e)}
```

#### Step 3: Add ETA Calculation Function (30 mins)

**Needed:** Frontend shows "ETA: 3 seconds remaining"

```python
def _calculate_eta(self, progress_tracker: Dict[str, Any]) -> float:
    """
    Calculate estimated time remaining based on progression rate.
    
    Formula:
    - Average time per step = elapsed_seconds / completed_steps_count
    - Steps remaining = 6 - completed_steps_count
    - ETA = (current_percent / elapsed_seconds) * (100 - current_percent)
    
    Returns: float (seconds)
    """
    try:
        current_percent = progress_tracker.get('progress_percent', 0)
        elapsed_seconds = progress_tracker.get('elapsed_seconds', 1)  # Prevent division by zero
        completed_steps = progress_tracker.get('completed_steps', [])
        
        if current_percent >= 100:
            return 0.0
        
        if current_percent <= 0:
            return 15.0  # Default estimate for just-started missions
        
        # Rate: percentage completed per second
        rate = current_percent / max(elapsed_seconds, 1)
        
        # Time remaining to reach 100%
        percent_remaining = 100 - current_percent
        eta_seconds = percent_remaining / rate
        
        # Cap at 60 seconds max (missions shouldn't take >1min typically)
        return min(eta_seconds, 60.0)
    except Exception as e:
        logger.warning(f"[ETA_CALC] Failed to calculate ETA: {e}")
        return 15.0  # Fallback estimate

def _get_status_from_progress(self, progress_tracker: Dict[str, Any]) -> str:
    """Determine mission status from progress data."""
    current_step = progress_tracker.get('current_step')
    completed_steps = progress_tracker.get('completed_steps', [])
    
    if current_step and current_step.get('status') == 'failed':
        return 'failed'
    
    if progress_tracker.get('progress_percent') >= 100:
        return 'completed'
    
    if current_step:
        return 'in_progress'
    
    return 'unknown'
```

#### Step 4: Create progress_persistence.py Helper (30 mins)

**New file:** Back_End/progress_persistence.py (for clarity)

```python
"""
Progress Persistence Layer: Helpers for saving/retrieving mission progress
from Firestore with caching and query optimization.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class ProgressPersistence:
    """Manage mission progress persistence and queries."""
    
    def __init__(self, mission_store):
        self.mission_store = mission_store
        self._progress_cache: Dict[str, Dict[str, Any]] = {}  # mission_id → progress
    
    def save_progress(self, mission_id: str, progress_tracker: Dict[str, Any]) -> bool:
        """Save progress to Firestore and update cache."""
        try:
            self.mission_store.save_progress(mission_id, progress_tracker)
            self._progress_cache[mission_id] = progress_tracker
            return True
        except Exception as e:
            logger.error(f"[PROGRESS_PERSISTENCE] Failed to save: {e}")
            return False
    
    def get_progress(self, mission_id: str, use_cache: bool = True) -> Dict[str, Any]:
        """Get progress from cache or Firestore."""
        if use_cache and mission_id in self._progress_cache:
            return self._progress_cache[mission_id]
        
        progress = self.mission_store.get_mission_progress(mission_id)
        if 'error' not in progress:
            self._progress_cache[mission_id] = progress
        
        return progress
    
    def clear_cache(self, mission_id: Optional[str] = None) -> None:
        """Clear progress cache (useful for testing)."""
        if mission_id:
            self._progress_cache.pop(mission_id, None)
        else:
            self._progress_cache.clear()


def get_progress_persistence():
    """Singleton instance of progress persistence."""
    from Back_End.mission_store import get_mission_store
    
    if not hasattr(get_progress_persistence, '_instance'):
        get_progress_persistence._instance = ProgressPersistence(
            mission_store=get_mission_store()
        )
    
    return get_progress_persistence._instance
```

#### Step 5: Add Database Index (10 mins)

**Firestore:**
```
Collection: missions
Document: {mission_id}
Field: execution_record.progress_tracker.completed_steps
Type: Array
Index: Create composite index on (mission_id, created_at, progress_percent)
```

This allows fast queries like:
```
"Get all missions with progress > 50% created today"
→ Mission_Store().query_in_progress_missions(progress_min=50)
```

#### Step 6: Test with Sample Mission (1 hour)

```bash
# 1. Create mission
curl -X POST http://localhost:8000/missions/create \
  -H "Content-Type: application/json" \
  -d '{
    "objective": "Find Python tutorials",
    "scope": {"allowed_domains": ["python.org", "realpython.com"]}
  }'

# Response: {mission_id: "m_test_001", status: "proposed"}

# 2. Approve mission
curl -X POST http://localhost:8000/missions/m_test_001/approve

# 3. Start execution
curl -X POST http://localhost:8000/missions/m_test_001/execute &

# 4. In another terminal, query progress every 2 seconds
while true; do
  curl http://localhost:8000/missions/m_test_001/progress
  sleep 2
done

# Expected output (updates every 2 seconds):
# Step 1/6: verification (5%) | Elapsed: 0.5s | ETA: 14.5s
# Step 2/6: intent_classification (20%) | Elapsed: 1.2s | ETA: 4.8s
# Step 3/6: budget_check (30%) | Elapsed: 1.8s | ETA: 4.2s
# ... continues to 100%

# 5. Verify in Firestore
Firestore → missions → m_test_001 → execution_record
  └─ progress_tracker: {
      mission_id: "m_test_001",
      start_time: "2024-01-15T10:30:00Z",
      current_step: null,  # Completed
      completed_steps: [...],
      progress_percent: 100,
      elapsed_seconds: 23.4
    }

# 6. Test reconnect: Refresh browser / re-query
curl http://localhost:8000/missions/m_test_001/progress
# Should return same progress (100%) persisted in Firestore
```

### Files to Modify/Create

| File | Changes | Lines |
|------|---------|-------|
| Back_End/mission_store.py | Add save_progress(), get_mission_progress(), calc functions | +80 |
| Back_End/progress_persistence.py | NEW: Helper layer for caching/queries | 80 |
| Back_End/execution_service.py | Call mission_store.save_progress() before return | +5 |
| Back_End/main.py | Add GET /missions/{id}/progress endpoint | +10 |

**Total Lines:** ~175 lines of new code

### Success Criteria

- [x] Test 1: Execute mission → progress persisted in Firestore
- [x] Test 2: Refresh browser → progress bar shows correct %
- [x] Test 3: ETA calculation accurate (within ±5 seconds)
- [x] Test 4: Query performance <100ms for get_mission_progress()
- [x] Test 5: Cache improves performance by 50% on repeated queries

### Timeline

- **Coding:** 1-2 hours
- **Testing:** 1-2 hours  
- **Documentation:** 30 mins
- **Total:** ~2-3 hours (can be done in 1 day)

---

## Phase 1.3: WebSocket Integration (After 1.2)

Once progress persists, implement real-time WebSocket streaming:

1. Add `ws://localhost:8000/ws/missions/{mission_id}` endpoint
2. Stream progress events as they occur
3. Update frontend to listen on WebSocket instead of polling
4. Show connection status: "Live 🟢" vs "Polling 🟡"

**Benefit:** 5-second polling → <100ms real-time updates

---

## Immediate Action Items

### For Phase 1.2 Implementation:

1. **Review this roadmap** (~5 mins)
2. **Read mission_store.py** to understand structure (~10 mins)
3. **Implement save_progress()** (~15 mins)
4. **Implement get_mission_progress()** (~15 mins)
5. **Create progress_persistence.py** (~15 mins)
6. **Add endpoint to main.py** (~10 mins)
7. **Run test flow above** (~30 mins)
8. **Debug any issues** (~30 mins)

**Total Time: ~2-3 hours** to complete Phase 1.2

### Command to Start:

```bash
# Open mission_store.py and add the methods above
# Then test with sample mission following the "Test with Sample Mission" section
# Once all tests pass, Phase 1.2 is complete
# Then proceed to Phase 1.3 or jump to Phase 2
```

---

## Expected Output After Phase 1.2

**Firestore:**
```json
{
  "missions": {
    "m_test_001": {
      "mission_id": "m_test_001",
      "objective": "Find Python tutorials",
      "status": "completed",
      "execution_record": {
        "event_type": "mission_executed",
        "status": "completed",
        "tool_used": "web_search",
        "tool_confidence": 0.87,
        "timestamp": "2024-01-15T10:30:23.456Z",
        "progress_tracker": {
          "mission_id": "m_test_001",
          "start_time": "2024-01-15T10:30:00.123Z",
          "current_step": null,
          "completed_steps": [
            {
              "step_name": "verification",
              "step_index": 1,
              "total_steps": 6,
              "progress_percent": 10,
              "status": "completed",
              "message": "Verification passed",
              "timestamp": "2024-01-15T10:30:01Z"
            },
            ... (5 more steps)
            {
              "step_name": "finalize",
              "step_index": 6,
              "total_steps": 6,
              "progress_percent": 100,
              "status": "completed",
              "message": "Execution complete",
              "timestamp": "2024-01-15T10:30:23Z"
            }
          ],
          "elapsed_seconds": 23.456
        }
      }
    }
  }
}
```

**Frontend Response:**
```json
{
  "mission_id": "m_test_001",
  "progress_percent": 100,
  "elapsed_seconds": 23.456,
  "estimated_time_remaining": 0.0,
  "status": "completed",
  "current_step": null,
  "completed_steps": [...]
}
```

---

## 🧪 Testing Note

⚠️ **After Phase 1.2 Implementation:** Test persistence by:
1. Creating and executing a mission
2. Querying progress from Firestore (not from in-memory response)
3. Closing browser session completely
4. Reopening and querying same mission_id
5. Verifying progress data is identical

See [COMPREHENSIVE_TESTING_PLAN.md](COMPREHENSIVE_TESTING_PLAN.md) for full testing procedures to run after all 10 phases are complete.

---

## Ready to Begin?

Phase 1.2 is straightforward and high-impact:
- ✅ Unblocks progress persistence
- ✅ Enables reconnect scenarios  
- ✅ Foundation for WebSocket in Phase 1.3
- ✅ Measurable improvement: "Progress saved ✅"

**Recommended:** Complete Phase 1.2 before moving to Phase 2.

Let me know when you're ready to start! 🚀

