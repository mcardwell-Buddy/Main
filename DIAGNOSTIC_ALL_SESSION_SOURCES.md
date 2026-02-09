# COMPREHENSIVE SESSION PERSISTENCE DIAGNOSTIC

**Issue**: New sessions don't save to Firebase, old sessions persist despite deletion

---

## ALL POSSIBLE SESSION SOURCES

### 1. Frontend localStorage ❌ (Should be cleared)
**Check**: Browser DevTools → Application → Local Storage → http://localhost:3000
**Look for**: `buddy_sessions`, `buddy_active_session`
**Status**: User claims cleared

### 2. Browser Cache/IndexedDB ❌ (Check these)
**Check**:
- DevTools → Application → Cache Storage
- DevTools → Application → IndexedDB
- DevTools → Application → Session Storage
**Action**: Clear all

### 3. Browser HTTP Cache ❌ (Could cache API responses)
**Check**: Network tab, look for cached responses
**Headers**: `Cache-Control`, `ETag`
**Action**: Hard refresh (Ctrl+Shift+R) or Disable cache in DevTools

### 4. Service Worker ✅ (Not present)
**Status**: No service worker found in code

### 5. Backend Memory Cache ⚠️ (Restarted but...)
**Location**: `backend/conversation/session_store.py` → `self._sessions` dict
**Lifecycle**: Loaded from Firebase on startup
**Issue**: If sessions exist in Firebase when backend starts, they load into memory
**Check**: What's in Firebase BEFORE backend restart?

### 6. Firebase Firestore ⚠️ (Primary source of truth)
**Collection**: `conversation_sessions`
**Issue**: User sees sessions in UI but claims they're not in Firebase
**Possible**: Looking at wrong project/collection?

### 7. Frontend State Persistence ❌ (Check for hidden state)
**Locations**:
- React component state
- URL parameters
- Browser history state

---

## DIAGNOSTIC STEPS

### Step 1: Verify Firebase State
```
1. Open Firebase Console
2. Go to Firestore Database
3. Check conversation_sessions collection
4. Document IDs that exist there
5. Compare with session IDs shown in UI
```

### Step 2: Check Backend Memory
```powershell
# While backend is running, run:
python -c "from backend.conversation.session_store import get_conversation_store; store = get_conversation_store(); print(f'Memory: {list(store._sessions.keys())}')"
```

### Step 3: Check All Browser Storage
```javascript
// In browser console:
console.log('localStorage:', {...localStorage});
console.log('sessionStorage:', {...sessionStorage});

// Check IndexedDB
indexedDB.databases().then(dbs => console.log('IndexedDB:', dbs));

// Check cache
caches.keys().then(keys => console.log('Caches:', keys));
```

### Step 4: Network Tab Analysis
```
1. Open DevTools → Network tab
2. Clear network log
3. Refresh page
4. Look for:
   - GET /conversation/sessions (what does it return?)
   - Any 304 Not Modified responses (cached)
   - Response headers (Cache-Control?)
```

### Step 5: Test New Session Creation
```
1. Click "New Session"
2. Check Network tab:
   - POST /conversation/sessions/create (status?)
   - Response body (session_id?)
3. Check backend logs:
   - [SESSION_CREATE_API] message?
4. Check Firebase Console:
   - New document appears?
5. Check backend memory:
   - Session in memory?
```

---

## HYPOTHESIS: The Real Problem

### Theory 1: Browser HTTP Cache
**Symptoms match exactly**:
- Old sessions persist → Cached GET response
- New sessions don't appear → Cache not invalidated
- Hard refresh "doesn't work" → Cache-Control headers

**Test**:
1. Open DevTools → Network tab
2. Check "Disable cache" checkbox
3. Refresh page
4. Do sessions change?

### Theory 2: Looking at Wrong Firebase Project
**Symptoms**:
- Sessions appear in UI (from actual Firebase)
- User says "not in Firebase" (looking at different project?)

**Test**:
Check FIREBASE_CREDENTIALS_PATH in backend config

### Theory 3: Backend Loads Then Caches
**Flow**:
1. Firebase has 2 old sessions
2. Backend starts → loads 2 sessions into memory
3. User creates new session via UI
4. New session fails to save to Firebase (error swallowed)
5. New session EXISTS in memory but NOT Firebase
6. GET /conversation/sessions returns all 3 from memory
7. User refreshes page
8. Backend still has all 3 in memory
9. UI shows all 3
10. User checks Firebase → only sees 2 old ones

**Test**:
Check backend logs for Firebase save errors

---

## SMOKING GUN CHECK

### Check Frontend Network Requests:

**When page loads**:
```
Request: GET http://localhost:8000/conversation/sessions
Response: [check session IDs here]
Status: 200 or 304?
Cache headers: ?
```

**When clicking "New Session"**:
```
Request: POST http://localhost:8000/conversation/sessions/create
Response: {session_id: ?, status: ?}
Status: 200?
```

**After creating new session, refresh page**:
```
Request: GET http://localhost:8000/conversation/sessions
Response: [does new session appear here?]
```

---

## IMMEDIATE ACTIONS

1. **Open Browser DevTools** → **Network** tab
2. **Check "Disable cache"** checkbox
3. **Clear all** (Application tab → Clear storage → Clear site data)
4. **Restart backend** with logging:
   ```powershell
   python -m uvicorn backend.main:app --reload --port 8000 --log-level debug
   ```
5. **Refresh browser** (Ctrl+Shift+R)
6. **Create new session** and watch:
   - Network tab for API calls
   - Backend terminal for logs
   - Firebase Console for new document

---

## KEY QUESTIONS TO ANSWER

1. **When you create new session, do you see this in Network tab?**
   - POST /conversation/sessions/create → 200 OK?

2. **What does backend log say when creating?**
   - Look for: `[SESSION_CREATE_API] Created session...`

3. **When you refresh, what does GET /conversation/sessions return?**
   - Does it include the new session?
   - Or only old ones?

4. **Have you checked Firebase in the SAME project?**
   - Project ID matches your config?

5. **Are there any errors in browser console?**
   - Red errors?
   - Failed network requests?

---

## MOST LIKELY CAUSE

Based on symptoms (old sessions persist, new don't save), the most likely issue is:

**HTTP CACHE** is caching the GET /conversation/sessions response.

**Fix**: Add Cache-Control headers to backend API or disable browser cache.
