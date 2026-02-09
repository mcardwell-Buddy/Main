# Phase 3: Integration Risks & Next Steps

## Identified Risks

### 1. Server Auto-Reload (DEV ONLY)
**Impact**: Medium  
**Probability**: High  
**Mitigation**: 
- FastAPI auto-reload in dev will trigger when files change
- Need to wait ~3 seconds for reload to complete
- **Action**: Restart server manually if needed
- Production: Use `uvicorn` without `--reload` flag

### 2. Whiteboard JSONL Write Latency
**Impact**: Low  
**Probability**: Medium  
**Mitigation**:
- Mission state written to JSONL during execution
- Reading immediately after mission_spawn may return empty/partial state
- `/api/whiteboard/{mission_id}` returns 404 if not in JSONL yet
- **Action**: UI should show "Loading..." or retry with exponential backoff
- **Expected**: < 100ms in normal conditions

### 3. Missing Frontend Error Handling
**Impact**: Low  
**Probability**: Low  
**Mitigation**:
- New endpoint could fail or timeout
- Current UI has try/catch but shows raw error
- **Action**: Add user-friendly error messages
  ```javascript
  catch (error) {
    addMessage(`⚠️ Couldn't create mission: ${error.message}. Try again?`, 'agent');
  }
  ```

### 4. Envelope Deserialization
**Impact**: Low  
**Probability**: Very Low  
**Mitigation**:
- UI expects specific JSON structure from ResponseEnvelope
- If backend returns unexpected format, UI will crash
- **Action**: Add validation
  ```javascript
  if (!envelope.envelope?.missions_spawned) {
    envelope.envelope.missions_spawned = [];
  }
  ```

### 5. Old Code Still Active
**Impact**: Low  
**Probability**: High  
**Mitigation**:
- Other parts of backend may still call `/reasoning/execute`
- Creates duplicate execution paths
- **Action**: Audit codebase for calls to old endpoints
  - Search: `fetch.*reasoning/execute`
  - Search: `requests.*conversation/message`
  - Replace with calls to `/chat/integrated` where appropriate

---

## Edge Cases & Handling

### Edge Case 1: No Mission Proposed
**Scenario**: User asks clarifying question  
**Current Behavior**: `missions_spawned` will be empty  
**Expected UI Response**: Show primary_text only, no "Proposed Missions" section  
**Status**: ✅ Handled in code

### Edge Case 2: Fast Execution
**Scenario**: Mission completes before UI tries to read whiteboard  
**Current Behavior**: Whiteboard returns final state with status="completed"  
**Expected UI Response**: Show mission as complete with results  
**Status**: ✅ Handled naturally

### Edge Case 3: Slow Network
**Scenario**: Whiteboard read takes > 5 seconds  
**Current Behavior**: UI may timeout or show stale data  
**Expected UI Response**: Retry or show "Syncing..."  
**Status**: ⚠️ Needs UI enhancement

### Edge Case 4: Server Restart During Mission
**Scenario**: Backend crashes while mission executing  
**Current Behavior**: Partial signals in JSONL, mission status unknown  
**Expected UI Response**: Show "Mission state unknown, retrying..."  
**Status**: ⚠️ Needs better error recovery

---

## Performance Implications

### Response Time

| Operation | Expected Time | Constraint |
|-----------|---------------|-----------|
| `/chat/integrated` | 100-500ms | Should be < 1s |
| ChatSessionHandler | 50ms | Should be < 100ms |
| InteractionOrchestrator | 20ms | Should be < 50ms |
| JSONL write | 5ms | Should be < 50ms |
| `/api/whiteboard/{mission_id}` | 10-50ms | Should be < 100ms |

**Total roundtrip**: ~200ms for UI to get mission proposal  
**Then**: ~50ms for UI to read mission state

### Scaling Concerns

- JSONL files will grow (no archival yet)
- No pagination on `/api/whiteboard/goals`
- No caching on whiteboard reads
- **Action for Phase 4**: Add caching, archival, pagination

---

## Known Limitations

1. **Whiteboard reads are synchronous** - Blocks on large JSONL files
2. **No real-time updates** - UI must poll `/api/whiteboard/{mission_id}`
3. **No mission cancellation** - Can't stop a proposed mission once sent
4. **No artifact rendering** - ResponseEnvelope includes artifacts but UI doesn't render them yet
5. **No execution stream consumption** - UI doesn't show live progress

**Phase 4 will address**: Artifacts, rendering, real-time streams

---

## Next Steps (Phase 4+)

### Immediate (Phase 4)
- [ ] Add Artifact Registry (how to store artifacts)
- [ ] Design Presentation Router (how to render artifacts)
- [ ] Add WebSocket updates for real-time mission progress
- [ ] Add polling to UI for mission state updates

### Short-term (Phase 5)
- [ ] Add mission cancellation via PATCH `/api/mission/{mission_id}`
- [ ] Add execution stream consumption (real-time progress in UI)
- [ ] Add mission history/replay
- [ ] Add artifact download/export

### Long-term (Phase 6+)
- [ ] Optimize JSONL with archival/compression
- [ ] Add caching layer for whiteboard reads
- [ ] Add search/filter on goals and missions
- [ ] Add audit trail for all chat/mission interactions

---

## Validation Checklist

Before declaring Phase 3 DONE:

- [x] New endpoint created and callable
- [x] Frontend updated to use new endpoint
- [x] Old endpoints still work (backward compat)
- [x] ResponseEnvelope structure correct
- [x] Whiteboard reads return valid data
- [x] No new schemas or business logic
- [x] No breaking changes
- [x] Constraints verified
- [ ] **PENDING**: Manual testing in UI
- [ ] **PENDING**: Load testing with concurrent users
- [ ] **PENDING**: Edge case testing

---

## Deployment Checklist

When deploying Phase 3 to production:

1. **Backup**
   - [ ] Backup `outputs/phase25/learning_signals.jsonl`
   - [ ] Backup database (if applicable)

2. **Deploy**
   - [ ] Deploy `backend/main.py` changes
   - [ ] Deploy `frontend/src/UnifiedChat.js` changes
   - [ ] Restart backend server
   - [ ] Clear frontend cache
   - [ ] Monitor error logs

3. **Verify**
   - [ ] `/chat/integrated` responds to test request
   - [ ] `/api/whiteboard/goals` returns data
   - [ ] UI loads without console errors
   - [ ] Test message produces mission proposal

4. **Rollback Plan**
   - [ ] If errors: Revert `main.py` and `UnifiedChat.js`
   - [ ] Restart server
   - [ ] UI will fall back to `/conversation/message` (legacy)
   - [ ] Note: Old path doesn't show missions, but system still works

---

## Support

For issues with Phase 3 integration:

1. **Backend won't start**: Check `backend/main.py` syntax (auto-compile test)
2. **Endpoint returns 500**: Check logs for ChatSessionHandler errors
3. **UI shows no missions**: Verify `/chat/integrated` was called (check network tab)
4. **Whiteboard returns 404**: Wait 1-2 seconds, signals may not be written yet
5. **Old endpoints broken**: Check for recursive calls or imports

---

**Status**: ✅ Phase 3 wiring complete  
**Risk Level**: LOW (backward compatible, isolated changes)  
**Ready for Phase 4**: YES

