# INVESTIGATION REPORT: Sessions Persisting After Deletion

**Date**: February 8, 2026  
**Issue**: Sessions persist after Firebase deletion, browser history clear, and restarts

---

## ROOT CAUSES IDENTIFIED

### Issue 1: ❌ OLD localStorage Code Still Active

**Location**: `frontend/src/UnifiedChat.js` lines 120-131

**Found Code** (This was NOT removed):
```javascript
// Load sessions from localStorage on mount
useEffect(() => {
  const stored = localStorage.getItem('buddy_sessions');
  if (stored) {
    try {
      setSessions(JSON.parse(stored));
    } catch (e) {
      console.error('Failed to parse stored sessions:', e);
    }
  }
}, []);
```

**Problem**: 
- This is OLD localStorage loading code
- It runs BEFORE the backend loading useEffect (line 154)
- Sessions get loaded from localStorage FIRST
- Then backend loading might merge or get overwritten

**Evidence**: grep found 4 localStorage references, but we only removed 2 useEffect hooks

---

### Issue 2: ✅ Backend In-Memory Cache (Expected Behavior)

**Location**: `backend/conversation/session_store.py` line 96

**How It Works**:
```python
def _load_from_firebase(self) -> None:
    """Load all existing sessions from Firebase on startup."""
    # Loads ALL sessions into self._sessions dict on backend startup
    docs = self._collection.stream()
    for doc in docs:
        # Store in memory
        self._sessions[session.session_id] = session
```

**Investigation Results**:
```
1. Firebase Status: ENABLED
2. Sessions in Backend Memory: 2 sessions
   - 1770608802740: 0 messages, source=chat_ui
   - 1770608803164: 0 messages, source=chat_ui
3. Sessions in Firebase: 2 sessions (same IDs)
4. Analysis: Sessions in both memory and Firebase
```

**Why Sessions Persist After Firebase Deletion**:
1. Backend loads sessions from Firebase on startup → stores in memory
2. You delete sessions from Firebase Console
3. Backend still has sessions in memory (self._sessions dict)
4. GET /conversation/sessions returns from memory, not Firebase
5. Sessions appear to persist

**This is EXPECTED behavior** - backend caches sessions in memory for performance.

---

## THE REAL PROBLEM: localStorage Priority

### Execution Order (WRONG):

```
1. Component mounts
2. useEffect #1 (line 120) runs: Load from localStorage ← RUNS FIRST
3. useEffect #2 (line 154) runs: Load from backend
4. Result: localStorage wins or causes conflict
```

### What Actually Happens:

```
User clears browser → localStorage still has data (not cleared correctly?)
User refreshes → localStorage loads sessions
Backend loading might overwrite, but conflict occurs
```

---

## EVIDENCE

### Grep Results for localStorage:
```
Line 120: // Load sessions from localStorage on mount
Line 122: const stored = localStorage.getItem('buddy_sessions');
Line 571: const injectedContext = localStorage.getItem('whiteboard_context');
Line 573: localStorage.removeItem('whiteboard_context');
```

**Lines 120-131**: OLD code that loads from localStorage  
**Lines 571, 573**: Different feature (whiteboard context) - OK to keep

### Code That Should NOT Be There:
```javascript
// Line 120-131 - THIS IS THE CULPRIT
useEffect(() => {
  const stored = localStorage.getItem('buddy_sessions');
  if (stored) {
    try {
      setSessions(JSON.parse(stored));
    } catch (e) {
      console.error('Failed to parse stored sessions:', e);
    }
  }
}, []);
```

---

## WHY OUR FIX DIDN'T WORK

When we removed localStorage code, we looked at lines 173-189 and removed those useEffect hooks.

**BUT** we missed the LOADING useEffect at lines 120-131 which is EARLIER in the file.

This loading code runs FIRST on component mount, before the backend loading code.

---

## TIMELINE OF WHAT HAPPENED

### Original Fix (What We Did):
1. ✅ Removed localStorage.setItem() at line 179 (saving sessions)
2. ✅ Removed localStorage.setItem() at line 187 (saving active session)
3. ✅ Added backend loading useEffect at line 154
4. ❌ MISSED: localStorage.getItem() at line 122 (loading sessions)

### Result:
- Sessions stop being SAVED to localStorage (good!)
- But OLD sessions still LOADED from localStorage (bad!)
- Old localStorage data persists and takes priority

---

## PROOF

### Test Scenario:
1. User had sessions in localStorage BEFORE fix was applied
2. We removed the SAVE code but not the LOAD code
3. Old sessions still in localStorage from before
4. On component mount: loads old sessions from localStorage (line 122)
5. Backend loading (line 154) may run later but doesn't clear the old data

### Why Browser Clear "Didn't Work":
- User may not have cleared localStorage specifically
- Or localStorage cleared but backend cache still had sessions
- Frontend loads from backend → sessions reappear
- Backend saves to Firebase → sessions back in Firebase
- Next load: localStorage has them again

---

## THE FIX NEEDED

### Remove Lines 120-131:
```javascript
// DELETE THIS ENTIRE useEffect:
// Load sessions from localStorage on mount
useEffect(() => {
  const stored = localStorage.getItem('buddy_sessions');
  if (stored) {
    try {
      setSessions(JSON.parse(stored));
    } catch (e) {
      console.error('Failed to parse stored sessions:', e);
    }
  }
}, []);
```

### Why This Fixes It:
- No localStorage loading on mount
- Only backend loading happens (line 154)
- Backend is single source of truth
- Delete from Firebase → restart backend → sessions gone
- No localStorage interference

---

## BACKEND CACHE BEHAVIOR (Separate Issue)

### Expected Behavior:
- Backend loads from Firebase on startup
- Sessions cached in memory for performance
- Deleting from Firebase doesn't invalidate cache
- Must restart backend to reload from Firebase

### This is CORRECT:
- Caching improves performance
- Backend is the source of truth
- Don't need to query Firebase on every API call

### To Clear Backend Cache:
1. Delete sessions from Firebase Console
2. Restart backend server
3. Backend reloads (empty) from Firebase

---

## USER CONFUSION EXPLAINED

### What User Experienced:
1. Applied our fix
2. Sessions still appeared
3. Deleted from Firebase
4. Sessions STILL appeared
5. Cleared browser history
6. Sessions STILL appeared
7. Restarted backend and frontend
8. Sessions STILL appeared

### Why This Happened:
1. OLD localStorage still has sessions (from before fix)
2. Line 122 loads from localStorage on mount
3. Backend also has sessions in cache
4. Two sources feeding the UI with stale data
5. Even after Firebase deletion, both caches remain

### The Fix Will Resolve:
- Remove line 122: No localStorage loading
- Restart backend: Clears backend cache
- Hard refresh: Loads only from backend
- Backend loads from (empty) Firebase
- Sessions finally gone

---

## ACTION REQUIRED

**Single Change Needed**: Remove lines 120-131 in frontend/src/UnifiedChat.js

**After Change**:
1. Restart frontend
2. Restart backend (to clear backend cache)
3. Hard refresh browser
4. Should load from backend/Firebase only
5. No localStorage interference

---

## VERIFICATION STEPS

After fix is applied:

1. **Open browser DevTools → Application → Local Storage**
   - Check if 'buddy_sessions' exists
   - Should be empty or not exist

2. **Create new session**
   - Should call backend API
   - Should appear in Firebase immediately
   - Should NOT be in localStorage

3. **Delete from Firebase**
   - Restart backend server
   - Hard refresh browser
   - Session should be GONE

4. **Clear browser history**
   - Sessions should reload from backend/Firebase
   - Should persist correctly

---

## SUMMARY

**Problem**: localStorage loading code (line 122) was NOT removed  
**Impact**: Old sessions persist from localStorage, even after Firebase deletion  
**Fix**: Remove lines 120-131 (localStorage loading useEffect)  
**Result**: Backend/Firebase becomes true source of truth

**Backend cache is NORMAL** - just restart backend to reload from Firebase.
