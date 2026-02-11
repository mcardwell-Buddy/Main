# 🗺️ BUDDY SYSTEM INTEGRATION ARCHITECTURE DIAGRAMS

## Phase 1: Progress Tracking Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                       MISSION EXECUTION FLOW                        │
└─────────────────────────────────────────────────────────────────────┘

    execute_mission(mission_id)
            │
            ├─► Initialize MissionProgressTracker
            │        ├─► mission_id
            │        ├─► start_time = now()
            │        ├─► completed_steps = []
            │        └─► Register callback(emit_progress) → streaming_events
            │
            ├─► STEP 1: Verification (5%)
            │        ├─ progress_tracker.start_step(...)
            │        ├─ Load mission from Firestore
            │        ├─ Verify status == "approved"
            │        ├─ Check idempotency
            │        └─ progress_tracker.complete_step() OR fail_step()
            │             │
            │             └─► Callback: emit_progress("step_completed", {...})
            │                  │
            │                  └─► streaming_events.emit_execution_step()
            │                       ├─ Firestore: missions/{id}/execution_record
            │                       ├─ WebSocket: broadcast to clients
            │                       └─ Logger: audit trail
            │
            ├─► STEP 2: Intent Classification (20%)
            │        ├─ progress_tracker.start_step(...)
            │        ├─ LLM classify intent
            │        ├─ Map to decision type
            │        └─ progress_tracker.complete_step()
            │
            ├─► STEP 3: Budget Check (30%)
            │        ├─ progress_tracker.start_step(...)
            │        ├─ Estimate costs
            │        ├─ Query budget_enforcer
            │        ├─ FAIL? → progress_tracker.fail_step() → return error
            │        └─ PASS? → progress_tracker.complete_step()
            │
            ├─► STEP 4: Tool Selection (40%)
            │        ├─ progress_tracker.start_step(...)
            │        ├─ Check pre-selected tool (from planning phase)
            │        ├─ Fallback: tool_selector.select_tool()
            │        ├─ Validate tool for intent
            │        └─ progress_tracker.complete_step()
            │
            ├─► STEP 5: Tool Execution (65%)
            │        ├─ progress_tracker.start_step(...)
            │        ├─ [If web_extract: pre-navigate to URL]
            │        ├─ tool_registry.call(tool_name, tool_input)
            │        ├─ Parse execution_result
            │        └─ progress_tracker.complete_step() OR fail_step()
            │
            ├─► STEP 6: Artifact Creation (85%)
            │        ├─ Build artifact object
            │        ├─ artifact_writer.write_artifact()
            │        ├─ artifact_preview_generator.generate_preview()
            │        └─ emitter.emit_artifact_preview()
            │
            ├─► STEP 7: Finalize (100%)
            │        ├─ progress_tracker.start_step("finalize")
            │        ├─ Emit learning signal
            │        ├─ Run mission evaluation
            │        ├─ Track actual costs
            │        ├─ progress_tracker.complete_step()
            │        └─ emitter.emit_mission_stop()
            │
            └─► Return {
                    success: bool,
                    mission_id: str,
                    status: 'completed' | 'failed',
                    tool_used: str,
                    artifact_reference: dict,
                    progress_tracker: {
                        mission_id,
                        start_time,
                        current_step: ExecutionStep | None,
                        completed_steps: [ExecutionStep, ...],
                        elapsed_seconds: float
                    }
                }
```

---

## Progress Event Propagation

```
┌─────────────────────────────────────────────────────────────────────┐
│                    EVENT PROPAGATION CHAIN                          │
└─────────────────────────────────────────────────────────────────────┘

    execution_service.py
            │
            ├─► progress_tracker.complete_step()
            │        │
            │        └─► _emit_progress("step_completed", step_data)
            │                │
            │                └─► For each registered callback:
            │                     callback("step_completed", {...})
            │
            └─► callback: emit_progress()
                    │
                    └─► streaming_events.emit_execution_step(
                            mission_id,
                            step_name,
                            step_status,
                            progress_percent,
                            message
                        )
                            │
                            ├─► Firestore
                            │   └─ missions
                            │       └─ {mission_id}
                            │           └─ execution_record
                            │               └─ progress_tracker
                            │                   ├─ current_step
                            │                   ├─ completed_steps[i]
                            │                   ├─ start_time
                            │                   └─ elapsed_seconds
                            │
                            ├─► WebSocket Broadaster
                            │   └─ ws://localhost:8000/ws/{user_id}
                            │       └─ Clients receive real-time update
                            │
                            ├─► Event Emitter Queue
                            │   └─ streaming_events_log table
                            │       └─ Audit trail of all steps
                            │
                            └─► Logger
                                └─ [PROGRESS_TRACKER] Step X: {name} ({percent}%)
```

---

## Phase 1 System Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                       COMPLETE PHASE 1 SYSTEM                            │
└──────────────────────────────────────────────────────────────────────────┘

┌─ BACKEND ─────────────────────────────────┐
│                                            │
│  execution_service.py                     │
│    ├─ Initialize MissionProgressTracker   │
│    ├─ Call progress_tracker.start_step()  │
│    ├─ [Execute step]                      │
│    ├─ Call progress_tracker.complete_step│
│    ├─ Register callback to emit events    │
│    └─ Return progress_tracker in response │
│                                            │
│  mission_progress_tracker.py              │
│    ├─ ExecutionStep (dataclass)           │
│    │   ├─ step_name: str                  │
│    │   ├─ step_index: int                 │
│    │   ├─ total_steps: int                │
│    │   ├─ progress_percent: int           │
│    │   ├─ status: "started"|"completed"| │
│    │   │            "failed"              │
│    │   ├─ message: str                    │
│    │   └─ timestamp: ISO8601              │
│    │                                      │
│    ├─ MissionProgressTracker (dataclass)  │
│    │   ├─ mission_id: str                 │
│    │   ├─ start_time: ISO8601             │
│    │   ├─ current_step: ExecutionStep     │
│    │   ├─ completed_steps: [ExecutionStep]│
│    │   ├─ progress_callbacks: [Callable]  │
│    │   ├─ start_step()                    │
│    │   ├─ complete_step()                 │
│    │   ├─ fail_step()                     │
│    │   ├─ register_callback()             │
│    │   ├─ _emit_progress()                │
│    │   ├─ get_progress_percent() → 0-100  │
│    │   └─ get_elapsed_seconds() → float   │
│    │                                      │
│    └─ Legacy methods (backward compat)    │
│        ├─ total_items_collected           │
│        ├─ pages_since_last_increase       │
│        └─ update() method                 │
│                                            │
│  streaming_events.py                      │
│    └─ emit_execution_step() ← receives    │
│       progress updates via callback       │
│                                            │
├─ FIREBASE (Firestore) ────────────────────┤
│                                            │
│  missions/{mission_id}/execution_record   │
│    ├─ event_type: "mission_executed"      │
│    ├─ mission_id: str                     │
│    ├─ status: "completed"|"failed"        │
│    ├─ tool_used: str                      │
│    ├─ tool_confidence: float              │
│    ├─ timestamp: ISO8601                  │
│    ├─ execution_result: {...}             │
│    ├─ progress_tracker: {           [1.2] │
│    │   ├─ mission_id                      │
│    │   ├─ start_time                      │
│    │   ├─ current_step                    │
│    │   ├─ completed_steps                 │
│    │   └─ elapsed_seconds                 │
│    │ }                                    │
│    └─ artifact_reference: {...}           │
│                                            │
├─ FRONTEND ────────────────────────────────┤
│                                            │
│  BuddyWhiteboard.js                       │
│    ├─ State: analyticsData                │
│    │   └─ agents: {                       │
│    │       mission_id,                    │
│    │       status,                        │
│    │       progress_percent,              │
│    │       current_step,                  │
│    │       elapsed_seconds,               │
│    │       tool_used                      │
│    │     }                                │
│    │                                      │
│    ├─ Live Agents Section                 │
│    │   ├─ Progress bar (0-100%)           │
│    │   ├─ Message: "Step: {name} ({%})"   │
│    │   ├─ Elapsed: "{seconds}s"           │
│    │   └─ Status badge                    │
│    │                                      │
│    ├─ Task Pipeline Section               │
│    │   └─ Last 5 missions                 │
│    │       ├─ Tool name                   │
│    │       ├─ Progress %                  │
│    │       └─ Timestamp                   │
│    │                                      │
│    └─ useEffect(() => {                   │
│        fetch('/api/analytics/all')        │
│        Update state                       │
│      }, 5000) [Polling every 5s]          │
│                                            │
│  whiteboard_metrics.py                    │
│    └─ collect_analytics_dashboard()       │
│        ├─ _collect_agents_data()          │
│        │   ├─ Query agents collection     │
│        │   ├─ Get latest execution_record │
│        │   └─ Return {agent, progress, %} │
│        │                                  │
│        ├─ _collect_task_pipeline()        │
│        │   ├─ Query last 24h missions     │
│        │   └─ Return [{status, tool, %}]  │
│        │                                  │
│        └─ Return aggregated data to /api  │
│            └─ responses to /analytics/all │
│                                            │
└────────────────────────────────────────────┘
```

---

## Step Progress Percentage Breakdown

```
┌─────────────────────────────────────────────────────────────┐
│          EXECUTION PROGRESS PERCENTAGE TIMELINE             │
└─────────────────────────────────────────────────────────────┘

    0% ─────────────────────────────────────────────────────── 100%
    │                                                          │
    ├─► 5% Verification Started
    │   ├─ Load mission
    │   └─ Verify "approved"
    │
    ├─► 10% Verification Complete
    │
    ├─► 20% Intent Classification Started
    │   ├─ Classify objective
    │   └─ Map to tool category
    │
    ├─► 30% Intent Complete
    │   ├─ Budget Check Started
    │   └─ Calculate costs
    │
    ├─► 40% Budget Complete
    │   ├─ Tool Selection Started
    │   ├─ Check candidates
    │   └─ Select best match
    │
    ├─► 55% Tool Selected
    │   ├─ Tool Execution Started
    │   ├─ [Pre-nav for web_extract]
    │   └─ Executing tool_registry.call()
    │
    ├─► 80% Tool Execution Complete
    │   ├─ Artifact Creation Started
    │   ├─ Build artifact
    │   └─ Write to storage
    │
    ├─► 90% Artifact Created
    │   ├─ Finalize Started
    │   ├─ Emit learning signal
    │   └─ Track costs
    │
    └─► 100% Execution Complete
        ├─ Return result
        └─ Emit mission_stop

    Duration: Typically 5-30 seconds
    Goal: <5 seconds for most tools
```

---

## All 10 Phases Integration Dependency Graph

```
┌───────────────────────────────────────────────────────────────────────┐
│                    PHASE DEPENDENCY DIAGRAM                           │
└───────────────────────────────────────────────────────────────────────┘

                            ┌─────────────┐
                            │   PHASE 1   │
                            │ PROGRESS {} │ ✅ DONE
                            └──────┬──────┘
                                   │ (provides progress signal)
                    ┌──────────────┼──────────────┐
                    │              │              │
           ┌────────▼────────┐    │    ┌─────────▼──────┐
           │    PHASE 2      │    │    │    PHASE 3     │
           │   MISSION       │    │    │  FEEDBACK →    │
           │   UPDATE        │    │    │  TOOL RANK     │
           └────────┬────────┘    │    └─────────┬──────┘
                    │             │              │
                    └─────┬───────┴──────────────┘
                          │ (both provide learning signals)
                          │
                    ┌─────▼──────────┐
                    │    PHASE 4     │
                    │   SURVEY       │
                    │   COLLECTOR    │
                    └─────┬──────────┘
                          │ (satisfaction scores)
                          │
                    ┌─────▼──────────┐
                    │    PHASE 5     │
                    │  INVESTMENT    │
                    │   LOGIC        │
                    └─────┬──────────┘
                          │ (ROI scores)
                          │
       ┌──────────────────┼──────────────────┐
       │                  │                  │
   ┌───▼────┐     ┌───────▼────┐     ┌──────▼───┐
   │PHASE 6 │     │  PHASE 7   │     │ PHASE 8  │
   │WebSocket    │ ARTIFACTS  │     │ PHASE25  │
   │STREAM  │     │  PREVIEW   │     │ ROUTER   │
   └────┬───┘     └────┬───────┘     └──────┬───┘
        │              │                    │
        └──────────────┼────────────────────┘
                       │ (live data + routes)
                       │
       ┌───────────────┼───────────────┐
       │               │               │
   ┌───▼────┐     ┌────▼───┐      ┌───▼────┐
   │PHASE 9 │     │PHASE10 │      │ READY  │
   │SCHEDULER    │RECIPES │      │COMPLETE│
   │CLOUD   │     │SYSTEM  │      │SYSTEM  │
   └────────┘     └────────┘      └────────┘
```

---

## Testing Phase 1.1: End-to-End Flow

```
┌────────────────────────────────────────────────────────────────┐
│                  TEST FLOW FOR PHASE 1.1                       │
└────────────────────────────────────────────────────────────────┘

1. Create Test Mission
   curl -X POST http://localhost:8000/missions/create \
        -H "Content-Type: application/json" \
        -d '{"objective": "search for python tutorials"}'
   
   → Returns: {mission_id: "m_abc123", status: "proposed"}

2. Approve Mission (via /chat/integrated or direct API)
   curl -X POST http://localhost:8000/missions/m_abc123/approve
   
   → Returns: {status: "approved"}

3. Execute Mission (Triggers Progress Tracking)
   curl -X POST http://localhost:8000/missions/m_abc123/execute
   
   Watch console for:
   ✓ [PROGRESS_TRACKER] Step 1/6: verification (5%)
   ✓ [PROGRESS_TRACKER] Completed: verification (10%)
   ✓ [PROGRESS_TRACKER] Step 2/6: intent_classification (20%)
   ✓ [PROGRESS_TRACKER] Completed: intent_classification (30%)
   ... (continues to 100%)
   
   → Returns: {
       success: true,
       mission_id: "m_abc123",
       status: "completed",
       progress_tracker: {
         mission_id: "m_abc123",
         start_time: "2024-01-15T10:30:45.123Z",
         completed_steps: [
           {step_name: "verification", ..., progress_percent: 10},
           {step_name: "intent_classification", ..., progress_percent: 30},
           ...
           {step_name: "finalize", ..., progress_percent: 100}
         ]
       }
     }

4. View Progress in Dashboard
   Open: http://localhost:3000/api/whiteboard
   
   → Live Agents Section shows:
      "Mission m_abc123: COMPLETED 100% | Executed with web_search (23s)"
   
   → Task Pipeline shows:
      "web_search - COMPLETED - 100% - 10:30:45"

5. Query Firebase (Phase 1.2)
   Firestore:
   missions/m_abc123/execution_record
   └─ progress_tracker: {...}     [Persisted here ⏳]
```

---

## Error Handling Flow

```
┌────────────────────────────────────────────────────────────────┐
│          PROGRESS TRACKING ON FAILURE SCENARIOS               │
└────────────────────────────────────────────────────────────────┘

Scenario 1: Mission Not Found
  progress_tracker.start_step("verification", 1, 6, 5%, "...")
  progress_tracker.fail_step("Mission not found")
    ├─ _emit_progress("step_failed", {...status: "failed"})
    └─ streaming_events.emit_execution_step(..., step_status="failed")
  return {success: false, error: "Mission not found"}

Scenario 2: Budget Exceeded
  progress_tracker.start_step("budget_check", 3, 6, 30%, "...")
  progress_tracker.fail_step("Budget exceeded: $5.23 > $5.00 limit")
    ├─ _emit_progress("step_failed", {...})
    └─ streaming_events.emit_execution_step(..., step_status="failed")
  return {success: false, error: "Budget exceeded"}

Scenario 3: Tool Selection Failed
  progress_tracker.start_step("tool_selection", 4, 6, 40%, "...")
  progress_tracker.fail_step("Tool selection failed: confidence 0.12 < 0.15")
    ├─ _emit_progress("step_failed", {...})
    └─ streaming_events.emit_execution_step(..., step_status="failed")
  return {success: false, error: "Tool selection failed"}

Scenario 4: Tool Execution Error
  progress_tracker.start_step("tool_execution", 5, 6, 65%, "...")
  [tool_registry.call() raises Exception]
  progress_tracker.fail_step("Tool execution failed: Connection timeout")
    ├─ _emit_progress("step_failed", {...})
    └─ streaming_events.emit_execution_step(..., step_status="failed")
  return {success: false, error: "Tool execution failed"}

Scenario 5: Success
  [All steps complete]
  progress_tracker.complete_step("Execution complete")
    ├─ _emit_progress("step_completed", {...})
    └─ streaming_events.emit_execution_step(..., step_status="completed")
  return {success: true, artifact_reference: {...}, progress_tracker: {...}}

Progress Update Broadcast (regardless of success/failure):
  1. Firestore: missions/{id}/execution_record.progress_tracker = {...}
  2. WebSocket: Client receives progress update
  3. Logger: [PROGRESS_TRACKER] audit trail
  4. Dashboard: Updates progress bar accordingly
```

---

## Success Criteria Checklist

```
✅ Phase 1.1: Progress Tracking in execution_service
  ├─ [✓] MissionProgressTracker class created
  ├─ [✓] ExecutionStep dataclass implemented
  ├─ [✓] Callback registration system working
  ├─ [✓] progress_tracker.start_step() emits events
  ├─ [✓] progress_tracker.complete_step() emits events
  ├─ [✓] progress_tracker.fail_step() emits events
  ├─ [✓] Percent calculations (5% → 100%)
  ├─ [✓] Return value includes progress_tracker
  ├─ [✓] No syntax errors in modified files
  └─ [✓] Backwards compatible with legacy methods

⏳ Phase 1.2: Firebase Persistence
  ├─ [ ] progress_tracker persisted in Firestore
  ├─ [ ] Query function: get_mission_progress()
  ├─ [ ] ETA calculation implemented
  ├─ [ ] Database index created
  └─ [ ] Tested on 5+ sample missions

⏳ Phase 1.3: WebSocket Integration
  ├─ [ ] WebSocket endpoint created
  ├─ [ ] Progress events streamed to clients
  ├─ [ ] Dashboard connects to WebSocket
  ├─ [ ] Fallback to polling if WebSocket fails
  └─ [ ] <200ms latency verified

✅ Overall Phase 1 Goal: Real-time progress visibility
  └─ [✓] Progress visible in BuddyWhiteboard Live Agents
  └─ [⏳] Persisted in Firebase (Phase 1.2)
  └─ [⏳] Streamed via WebSocket (Phase 1.3)
```

