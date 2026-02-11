# 🧪 COMPREHENSIVE TESTING PLAN

## Overview

After completing all 10 phases of the Buddy System integration, this comprehensive testing plan must be executed to validate the entire system working together as a unified whole.

**Timeline:** 2-3 weeks (run in parallel with Phase 10 final touches)
**Scope:** Unit tests → Integration tests → End-to-end scenarios → Performance benchmarks

---

## Testing Phases Checklist

### ✅ Phase 1: Progress Tracking

**Unit Tests:**
- [ ] MissionProgressTracker initialization
- [ ] start_step() → progress_percent calculation
- [ ] complete_step() → event emission
- [ ] fail_step() → error state
- [ ] get_progress_percent() → returns 0-100
- [ ] get_elapsed_seconds() → time calculation
- [ ] Callback registration & invocation

**Integration Tests:**
- [ ] Progress events flow to streaming_events
- [ ] Firestore persistence of progress_tracker
- [ ] ETA calculation accuracy (±2 seconds)
- [ ] Progress visible in BuddyWhiteboard > Live Agents
- [ ] Dashboard updates every 5 seconds (or <100ms via WebSocket)

**End-to-End Scenarios:**
- [ ] Single mission execution: 0% → 100% progress tracking
- [ ] Concurrent missions: 5+ simultaneous with separate progress bars
- [ ] Mission failure: Progress stops at failure step
- [ ] Client reconnect: Progress persists across browser refresh
- [ ] Long mission (>60s): Progress tracking stability

**Performance Benchmarks:**
- [ ] Progress update latency: <200ms from execution_service → dashboard
- [ ] Firestore query time: <100ms for get_mission_progress()
- [ ] Memory usage: <5MB per concurrent mission tracked
- [ ] Database size: <1KB per mission's progress_tracker document

---

### ✅ Phase 2: Mission Modification

**Unit Tests:**
- [ ] mission_updater validates objective changes
- [ ] Validates scope domain changes
- [ ] Validates constraint updates
- [ ] Rejects invalid parameters
- [ ] Preserves mission metadata during update

**Integration Tests:**
- [ ] PUT /missions/{id}/update endpoint works
- [ ] Updated mission returned with changed fields highlighted
- [ ] Only "proposed" or "clarification_needed" missions can be updated
- [ ] Interaction orchestrator routes "modify mission" intent
- [ ] Updated mission can be re-approved

**End-to-End Scenarios:**
- [ ] User modifies objective → clarification flow → updated proposal
- [ ] User changes allowed_domains → validation → accepted/rejected
- [ ] User modifies priority → propagates to tool selection
- [ ] Multiple modifications in sequence → all applied correctly
- [ ] Modification rejected due to invalid parameter → error message

**Performance Benchmarks:**
- [ ] Modification validation: <50ms
- [ ] Database update: <100ms
- [ ] Return new proposal: <200ms total

---

### ✅ Phase 3: Feedback Loop

**Unit Tests:**
- [ ] tool_selector queries feedback_manager
- [ ] feedback_manager.get_tool_adjustment() returns multiplier
- [ ] Confidence calculation: base × (1 + feedback_factor)
- [ ] Tool exclusion for rejected tools
- [ ] Tool boost for approved tools (+0.15)

**Integration Tests:**
- [ ] Feedback stored in feedback_manager.state
- [ ] Tool confidence changes reflected in next selection
- [ ] User correction persists across missions
- [ ] Feedback constraints applied hardly (exclusion)
- [ ] Feedback multipliers applied softly (confidence boost/penalty)

**End-to-End Scenarios:**
- [ ] User rejects web_search → next mission avoids web_search
- [ ] User approves web_extract → next similar mission prefers it
- [ ] Multiple feedback samples → confidence converges on user preference
- [ ] Feedback across different user intents → tool adjustment scoped correctly
- [ ] Feedback reversal (was bad, now good) → system adapts

**Performance Benchmarks:**
- [ ] Feedback query in tool selection: <50ms
- [ ] Multiplier calculation: <10ms
- [ ] Single feedback store: <100ms to database

---

### ✅ Phase 4: Satisfaction Survey

**Unit Tests:**
- [ ] SurveyResponse creation & validation
- [ ] Survey response storage in Firebase
- [ ] survey_id → mission_id linkage
- [ ] Rating conversion: 1-10 → learning signal

**Integration Tests:**
- [ ] POST /missions/{id}/survey endpoint receives response
- [ ] Survey modal displays after mission completion
- [ ] Survey auto-dismiss after 10 seconds
- [ ] Learning emitter consumes survey data
- [ ] Tool confidence updates based on rating

**End-to-End Scenarios:**
- [ ] Mission completes → survey modal appears → user rates 8 → confidence boosted
- [ ] User ignores survey → auto-dismissed after 10s
- [ ] Rating 1-5 → confidence penalty (-0.1)
- [ ] Rating 6-7 → neutral (no confidence change)
- [ ] Rating 8-10 → confidence boost (+0.05)
- [ ] 20+ survey samples → confidence converges to user satisfaction

**Performance Benchmarks:**
- [ ] Survey modal render: <200ms
- [ ] Survey submission: <100ms
- [ ] Learning signal update: <100ms

---

### ✅ Phase 5: Investment Logic

**Unit Tests:**
- [ ] investment_core.evaluate_candidate() calculates ROI
- [ ] ROI = (benefit - cost) / cost
- [ ] Ranking by ROI works correctly
- [ ] Confidence & ROI weighted correctly (0.6 conf + 0.4 ROI)

**Integration Tests:**
- [ ] tool_selector calls investment_core.rank_by_roi()
- [ ] Final tool selection uses weighted score
- [ ] Tool selection logged with ROI values
- [ ] ROI updates after each mission execution

**End-to-End Scenarios:**
- [ ] web_search: ROI=0.92 (cheap, fast) vs web_extract: ROI=0.45 (expensive)
  → web_search selected despite lower base confidence
- [ ] 100 executions tracked → ROI estimates improve
- [ ] Tool costs increase → tool_selector avoids it for cheaper alternatives
- [ ] Time estimates decrease → tool_selector prefers faster tools

**Performance Benchmarks:**
- [ ] ROI ranking of 5 candidates: <50ms
- [ ] Weighted score calculation: <10ms
- [ ] Single ROI update: <100ms

---

### ✅ Phase 6: WebSocket Streaming

**Unit Tests:**
- [ ] WebSocket endpoint creation
- [ ] Client connection/disconnection handling
- [ ] Event serialization to JSON
- [ ] Message broadcast to all connected clients
- [ ] Reconnection with event replay

**Integration Tests:**
- [ ] ws://localhost:8000/ws/{user_id} endpoint works
- [ ] Progress events streamed in real-time
- [ ] Mission completion events streamed
- [ ] Artifact created events streamed
- [ ] WebSocket falls back to polling on connection failure

**End-to-End Scenarios:**
- [ ] Client connects → receives live progress updates <100ms latency
- [ ] Client disconnects & reconnects → missed events replayed
- [ ] 5 concurrent clients → all receive same progress updates
- [ ] Network interruption → fallback to HTTP polling
- [ ] Network recovers → resume WebSocket streaming
- [ ] 10+ messages per second → no bottleneck

**Performance Benchmarks:**
- [ ] Progress message latency: <50ms
- [ ] WebSocket overhead: <5% additional bandwidth
- [ ] Memory per connection: <100KB
- [ ] Max sustained throughput: 1000 messages/sec

---

### ✅ Phase 7: Artifact Preview Generation

**Unit Tests:**
- [ ] HTML generation for web extracts
- [ ] Syntax highlighting for code blocks
- [ ] Chart detection in numeric data
- [ ] Chart.js JSON generation
- [ ] XSS prevention in HTML sanitization

**Integration Tests:**
- [ ] artifact_preview_generator creates HTML previews
- [ ] Preview displays in artifact panel
- [ ] Charts render inline without external calls
- [ ] Chart export to PNG/SVG works

**End-to-End Scenarios:**
- [ ] Web extract → sections rendered as styled cards
- [ ] Search results → show thumbnails + snippet preview
- [ ] Calculation → formatted equation + result box with highlighting
- [ ] Numeric data → detect and auto-generate chart
- [ ] Code blocks → syntax highlight with proper indentation
- [ ] Large artifacts (>1MB) → preview generation still <500ms

**Performance Benchmarks:**
- [ ] HTML preview generation: <200ms
- [ ] Chart rendering: <300ms
- [ ] Memory for large preview: <10MB
- [ ] Artifact panel load: <400ms total

---

### ✅ Phase 8: Phase25 Router Integration

**Unit Tests:**
- [ ] interaction_orchestrator classifies "autonomous_goal" intent
- [ ] Routing decision: single-step vs multi-step
- [ ] phase25_orchestrator returns standard ResponseEnvelope
- [ ] Mission schema mapping works

**Integration Tests:**
- [ ] Multi-step objectives detected correctly
- [ ] Routed to phase25_orchestrator successfully
- [ ] phase25 missions stored in missions collection
- [ ] Response envelope format unified

**End-to-End Scenarios:**
- [ ] Single-step objective → ExecutionService path
- [ ] Multi-step autonomous goal → phase25_orchestrator path
- [ ] Both return standard ResponseEnvelope format
- [ ] phase25 missions visible in dashboard
- [ ] Mixed single+multi missions can run concurrently

**Performance Benchmarks:**
- [ ] Intent classification: <100ms
- [ ] Routing decision: <10ms
- [ ] Response envelope generation: <50ms

---

### ✅ Phase 9: Task Scheduler

**Unit Tests:**
- [ ] cloud_task_scheduler initialization
- [ ] schedule_mission() with trigger_time parameter
- [ ] Recurrence options: 'none', 'daily', 'weekly'
- [ ] Cancellation: DELETE /missions/{id}/schedule
- [ ] Job execution at trigger time

**Integration Tests:**
- [ ] POST /missions/{id}/schedule endpoint works
- [ ] APScheduler registers job correctly
- [ ] Job triggers execution_service.execute_mission() at time
- [ ] Recurring missions execute on schedule
- [ ] Cancellation removes job from scheduler

**End-to-End Scenarios:**
- [ ] Schedule mission for tomorrow 9am → executes at 9am
- [ ] Schedule daily mission → executes every day at same time
- [ ] Cancel scheduled mission → stops executing
- [ ] Reschedule mission → new time takes effect
- [ ] 10+ concurrent scheduled missions → all execute on time

**Performance Benchmarks:**
- [ ] Schedule operation: <100ms
- [ ] Job registration: <50ms
- [ ] Precision: ±2 seconds for trigger time
- [ ] Memory per scheduled job: <1KB

---

### ✅ Phase 10: Recipe System

**Unit Tests:**
- [ ] RecipeTemplate dataclass creation
- [ ] Recipe storage in Firebase recipes collection
- [ ] Recipe retrieval by recipe_id
- [ ] Mission auto-population from recipe params
- [ ] Success rate calculation

**Integration Tests:**
- [ ] GET /recipes endpoint lists all recipes
- [ ] POST /missions/from-recipe/{recipe_id} clones recipe
- [ ] Auto-filled mission params validate correctly
- [ ] Recipe usage tracked in database

**End-to-End Scenarios:**
- [ ] User selects "Find job postings" recipe
  → Mission auto-filled with objective, scope, constraints
- [ ] User customizes recipe params → cloned mission updates
- [ ] Recipe success rate shown: "92% success rate"
- [ ] 25% of new missions use recipes (adoption metric)
- [ ] Recipe personalization: "Most used by you: 'Research Company'"

**Performance Benchmarks:**
- [ ] Recipe list retrieval: <100ms
- [ ] Mission clone from recipe: <200ms
- [ ] Recipe suggestion: <50ms
- [ ] Storage per recipe: <500 bytes

---

## Master Test Execution Timeline

### Week 1: Unit Testing
- Day 1-2: Phase 1-3 unit tests
- Day 3-4: Phase 4-7 unit tests
- Day 5: Phase 8-10 unit tests

### Week 2: Integration Testing
- Day 6-7: Phase 1-5 integration tests
- Day 8-9: Phase 6-10 integration tests
- Day 10: Cross-phase integration (Phase 1→2→3 flow)

### Week 3: End-to-End & Performance
- Day 11-12: Scenario testing (happy paths)
- Day 13-14: Failure scenario testing
- Day 15: Performance benchmarking & load testing

---

## Test Scenarios: Critical Paths

### Scenario 1: Complete Mission Flow (Single User)

```
1. User sends chat message: "Find job postings in tech"
   └─ Progress: 0%

2. Interaction orchestrator classifies intent
   └─ Progress: 10%

3. ExecutionService starts
   └─ Progress: 15%

4. Tool selection (uses investment_core ROI + feedback adjustments)
   └─ Progress: 40%

5. Tool executes (web_search for job postings)
   └─ Progress: 65%

6. Artifact created and previewed
   └─ Progress: 85%

7. Learning signal emitted
   └─ Progress: 95%

8. Survey modal appears → user rates outcome
   └─ Progress: 100%

9. Tool confidence updated based on rating
   └─ Ready for next mission

Assertions:
- Progress visible in real-time (dashboard)
- Firebase shows mission execution_record
- WebSocket delivered updates <100ms latency
- Tool confidence reflected in next tool selection
- Survey response stored correctly
```

### Scenario 2: Concurrent Missions (5 Simultaneous)

```
User 1: "Search Python tutorials" → web_search (progress: 0-100%)
User 2: "Extract text from NYT" → web_extract (progress: 0-100%)
User 3: "Calculate mortgage" → calculate (progress: 0-100%)
User 4: "Schedule daily research" → task_scheduler (progress: 0-100%)
User 5: "Find company info + create proposal" → phase25 (progress: 0-100%)

Assertions:
- Each progress bar updates independently
- No cross-talk between missions
- Total system time <30 seconds (all 5 complete)
- Memory usage <50MB total
- Firebase writes don't collide
```

### Scenario 3: Mission Modification Flow

```
1. User sends objective: "Find jobs" (ambiguous)
   → Interaction orchestrator detects clarification_needed
   └─ Status: clarification_needed

2. System returns clarification response
   → "What types of jobs? What locations?"
   └─ User responds: "Software engineer roles in SF"

3. User sends modification: PUT /missions/{id}/update
   {
     "objective": "Find software engineer roles in San Francisco"
   }
   └─ Status: proposed (for re-approval)

4. System validates new objective
   → Valid, constraints met
   └─ Returns updated proposal

5. User approves updated mission
   └─ Status: approved

6. Execution proceeds with updated objective
   → Tool selection optimized for new objective
   └─ Progress: 0-100%

Assertions:
- Modification accepted only in correct states
- Updated mission returned with changes highlighted
- New tool selection better matches updated objective
- Learning signals reflect update
```

### Scenario 4: Feedback Loop Learning

```
Mission 1: Objective: "Search for X"
           Tool: web_search
           User feedback: "Not relevant" (rating: 3)
           Confidence before: 0.85
           Confidence after: 0.75 (penalty -0.1)

Mission 2: Objective: "Find more about X"
           Tool: web_search (considered; confidence: 0.75)
           Alternative: web_extract (confidence: 0.80)
           Selected: web_extract
           User feedback: "Perfect!" (rating: 9)
           web_extract confidence: 0.80 + 0.05 = 0.85

Mission 3: Objective: "Deep research on X"
           Tool: web_extract (confidence: 0.85)
           Selected: web_extract
           User feedback: "Good" (rating: 7)
           web_extract confidence: 0.85 (neutral feedback)

Assertions:
- Feedback multipliers applied correctly
- Tool confidence converges to actual usefulness
- Tool selection improves over time
- Feedback constrains tool pool appropriately
```

### Scenario 5: WebSocket vs Polling Fallback

```
Part A: WebSocket Connected
  User opens BuddyWhiteboard
  → Connects to ws://localhost:8000/ws/{user_id}
  → Mission starts, progress updates stream
  → Latency: 45ms average
  → Updates arrive as they happen

Part B: WebSocket Connection Fails
  Network interruption (simulate with DevTools)
  → Dashboard falls back to HTTP polling every 5 seconds
  → Status indicator: "Polling 🟡" (instead of "Live 🟢")
  → User still sees progress, just delayed

Part C: WebSocket Reconnects
  Network restored
  → Client re-establishes WebSocket
  → Missed events replayed
  → Dashboard resumes live updates
  → Status indicator: "Live 🟢" again

Assertions:
- WebSocket latency <100ms
- Polling fallback transparent to user
- Event replay ensures no data loss
- Reconnection automatic & seamless
```

### Scenario 6: Phase25 Multi-Agent (Autonomous Goals)

```
User: "I need to find job postings, extract requirements, 
       and compare them across 3 companies"

Interaction Orchestrator:
  ├─ Detects: multi-step, autonomous goal
  └─ Routes to: phase25_orchestrator

Phase25 Orchestrator:
  ├─ Break down into sub-missions:
  │  ├─ Mission 1: web_search (tech job postings)
  │  ├─ Mission 2: web_extract (extract reqs from postings)
  │  └─ Mission 3: calculate (compare requirements)
  ├─ Execute in sequence (with dependencies)
  └─ Aggregate results

Dashboard:
  ├─ Shows compound mission progress
  ├─ Lists 3 sub-missions in Task Pipeline
  └─ Final artifact contains aggregated data

Assertions:
- Autonomous goal routed correctly
- Sub-missions execute in dependency order
- Progress tracked at both compound & sub-mission levels
- Final response in standard ResponseEnvelope format
```

---

## Failure Scenarios to Test

### Failure 1: Mission Rejected During Execution

```
Precondition: Mission in "approved" state
Action: Budget limit exceeded during tool execution
Expected: progress_tracker.fail_step() → mission_stop event → "failed" status
Assertion: User sees failure in dashboard, artifact NOT created
```

### Failure 2: Tool Selection Failed

```
Precondition: LLM intent classification unavailable
Action: execute_mission() → _classify_intent() → timeout
Expected: fall back to default intent, continue or fail gracefully
Assertion: Mission either executes with default intent or fails clearly
```

### Failure 3: Firestore Persistence Fails

```
Precondition: Firestore write quota exceeded
Action: execute_mission() → mission_store.save_progress() → Exception
Expected: Log error, fallback to in-memory only, continue execution
Assertion: Mission completes even if persistence fails, non-blocking error
```

### Failure 4: WebSocket Connection Lost During Progress

```
Precondition: WebSocket connected, mission executing
Action: Network disconnect between progress event
Expected: Client detects disconnect, switches to polling, reconnects
Assertion: No progress data lost, seamless fallback
```

### Failure 5: Concurrent Modification Conflict

```
Precondition: Mission in "proposed" state
Action: 2 users simultaneously PUT /missions/{id}/update
Expected: First wins, second gets conflict error
Assertion: Mission updated once, no race condition
```

---

## Performance & Load Testing

### Load Test 1: Concurrent Mission Execution

```
Setup: Start 20 concurrent missions
Measure:
  - Total execution time
  - Peak memory usage
  - Database query latency
  - Progress update latency
  - Error rate

Target Benchmarks:
  ✓ All 20 complete in <5 minutes
  ✓ Memory <200MB
  ✓ Query latency <200ms (p95)
  ✓ Progress update latency <150ms (p99)
  ✓ Error rate <0.1%
```

### Load Test 2: High-Frequency Progress Updates

```
Setup: Single mission with rapid progress updates (every 100ms)
Measure:
  - Dashboard responsiveness
  - Firestore write rate
  - WebSocket message throughput
  - CPU usage

Target Benchmarks:
  ✓ Dashboard smooth animation (>30 FPS)
  ✓ Firestore writes: <1000/sec (avoid quota issues)
  ✓ WebSocket: <500 msg/sec per client
  ✓ CPU growth linear with mission count
```

### Load Test 3: Feedback Loop at Scale

```
Setup: 1000 missions with feedback, tool selection optimization
Measure:
  - Tool confidence convergence rate
  - Tool selection accuracy improvement
  - Learning emitter throughput
  - Database growth rate

Target Benchmarks:
  ✓ Confidence converges in <50 sample missions
  ✓ Tool accuracy improves 10%+ after feedback
  ✓ Learning throughput: 100 signals/sec
  ✓ Database growth: <1MB/1000 missions
```

---

## Sign-Off Criteria

✅ **All tests passing:**
- [ ] Unit tests: 95%+ pass rate, 0 critical failures
- [ ] Integration tests: 100% pass rate
- [ ] End-to-end scenarios: All 6 critical paths successful
- [ ] Failure scenarios: All handled gracefully
- [ ] Performance benchmarks: All targets met
- [ ] Load tests: All stress limits verified

✅ **Documentation complete:**
- [ ] Test results documented
- [ ] Performance metrics recorded
- [ ] Known issues tracked (if any)
- [ ] Improvement recommendations listed

✅ **Ready for production:**
- [ ] All 10 phases integrated & tested
- [ ] No critical bugs identified
- [ ] Performance acceptable for production load
- [ ] Comprehensive test suite available for regression testing

---

## Test Automation & Tools

### Recommended Testing Stack

```
Unit Tests: pytest (Python)
  └─ test_mission_progress_tracker.py
  └─ test_mission_updater.py
  └─ test_feedback_manager.py
  └─ ... etc

Integration Tests: pytest + fixtures
  └─ test_progress_to_firebase.py
  └─ test_execution_service_integration.py
  └─ test_phase_dependencies.py

E2E Tests: Selenium/Cypress (JavaScript)
  └─ spec/dashboard_progress_tracking.spec.js
  └─ spec/mission_modification.spec.js
  └─ spec/websocket_streaming.spec.js

Load Testing: Locust (Python)
  └─ locustfile.py

Performance: ApacheBench / wrk
  └─ Benchmark critical endpoints
```

---

## Next Steps

1. After all 10 phases are implemented
2. Follow this comprehensive testing plan sequentially
3. Document results in [TEST_RESULTS.md](TEST_RESULTS.md) (to be created)
4. Address any identified issues
5. Deploy to production with confidence

🚀 **Ready to test!**

