# Phase 25: Operator Guide - How to Use the Three Dashboards

## Quick Start

### Launching the Dashboard Application

```bash
# Navigate to dashboard app directory
cd buddy_phase25/

# Show operations dashboard (default)
python dashboard_app.py operations

# Show learning dashboard
python dashboard_app.py learning

# Show interaction dashboard  
python dashboard_app.py interaction

# Show full help
python dashboard_app.py help
```

## Dashboard 1: Learning Dashboard

### Purpose
**"Is Buddy learning and improving?"**

Shows Buddy's adaptive behavior, learning progress, and tool confidence over time.

### Key Sections

#### 1. Confidence Trajectory
Visual trend chart showing how Buddy's overall confidence has changed:

```
Buddy Confidence Over Time:
1.00 ┤                    ╭─
     │                   │
0.95 ┤                  ╭─
     │                 │
0.90 ┤    ╭───────────│
     │   │
0.85 ┤  │
     ├──────────────────────────────→ Time
     Time:  Day 1    Day 2    Day 3
```

**What to Look For:**
- ⬆️ Rising trend = Buddy is learning and improving
- ➡️ Flat trend = Stable performance (could be ceiling or plateau)
- ⬇️ Falling trend = Performance degradation (investigate why)
- 📊 Sharp drops = Likely triggered by new tool or environment change

**Actions:**
- If trending upward: All good, Buddy is learning
- If plateau: May need new tools or harder tasks
- If declining: Check recent tool additions or phase changes

#### 2. Recent Learning Signals
Table showing recent insights discovered:

```
Signal Type         Tool            Insight
─────────────────────────────────────────────────────────────
TOOL_RELIABILITY    button_click    95% success - high confidence
CONTEXT_AWARENESS   search_page     Improved with wait_time=500ms
TOOL_COMBINATION    click→text_in   Sequence order matters
ERROR_PATTERN       scroll_page     Fails on dynamic content
PERFORMANCE        *                Mean latency decreased 12%
```

**Columns:**
- **Signal Type**: Category of learning (reliability, awareness, combination, pattern, performance)
- **Tool**: Which tool(s) generated this signal
- **Insight**: What was learned
- **Confidence**: How sure Buddy is (0.0-1.0)
- **Timestamp**: When discovered

**Actions:**
- Review high-confidence signals (>0.85) for insights
- Investigate RED signals (confidence <0.5) before acting on them
- Check tool combinations that reduced latency

#### 3. Tool Performance Rankings
Ranked list of tools by Buddy's confidence:

```
Tool              Success Rate   Avg Confidence   Recent Calls
─────────────────────────────────────────────────────────────
1. button_click        98%            0.94          156
2. text_input          96%            0.92          234
3. scroll_page         91%            0.81          89
4. wait_element        95%            0.88          412
5. search_page         88%            0.76          67
```

**How to Use:**
- Prefer tools in top positions (most confident)
- Avoid tools near bottom (less confident)
- If tool suddenly drops: May need retraining or environment change

#### 4. Improvement Chains
Human-readable stories of how Buddy improved:

```
IMPROVEMENT CHAIN #1: Button Click Optimization
├─ FAILURE: Button click failed 15% of time (Day 1)
├─ INVESTIGATION: Phase 16 learning model identified timeout issue
├─ INSIGHT: Added 200ms wait before click improves success 94% → 98%
├─ ACTION TAKEN: Updated tool parameters in Phase 24
└─ RESULT: ✓ Tool reliability improved, Buddy confidence +0.08

IMPROVEMENT CHAIN #2: Context Awareness
├─ FAILURE: Text input failed when page dynamic (Day 2)
├─ INVESTIGATION: Phase 19 meta-learning detected pattern
├─ INSIGHT: Failure always preceded by page scroll events
├─ ACTION TAKEN: Added scroll detection before text_input
└─ RESULT: ✓ Context awareness improved, failures -40%
```

**What to Look For:**
- ✓ RESULT lines with checkmarks = Successful improvements
- ⚠️ Chains with "PENDING" = Buddy found issue but awaiting human approval
- ✗ Chains with multiple FAILURES = May need intervention

### Interpreting Dashboard Health

| Indicator | Meaning | Action |
|-----------|---------|--------|
| 📈 Rising confidence | Buddy is learning | Monitor and celebrate! |
| 📊 Plateau | Buddy needs new challenges | Add new tools or tasks |
| 📉 Declining confidence | Performance issue | Investigate recent changes |
| 🔴 Red signals | Low confidence insight | Review before acting |
| 🟢 Green signals | High confidence insight | Can act with confidence |

## Dashboard 2: Operations Dashboard

### Purpose
**"Is Buddy safe and operating correctly right now?"**

Real-time monitoring of system health, active agents, tool executions, and safety gates.

### Key Sections

#### 1. System Health Report
Overall health status and key metrics:

```
SYSTEM HEALTH REPORT
═════════════════════════════════════════════════════════════
Status: HEALTHY (Score: 92/100)

Health Metrics:
  • Overall Health:       92/100  [████████▒░]
  • Agent Health:         95/100  [█████████░]
  • Tool Reliability:     89/100  [████████░░]
  • Safety Compliance:   100/100  [██████████]
  • Resource Usage:        65%    [██████░░░░]

Recent Anomalies: None detected

Last Updated: 2024-01-15 14:35:22 UTC
```

**What to Look For:**
- **Overall Health 90+**: All systems operational
- **Overall Health 70-89**: Minor issues, monitor closely
- **Overall Health <70**: Alert state, investigate immediately
- **Safety Compliance 100**: Always required
- **Recent Anomalies**: If listed, click to investigate

#### 2. Execution Environment Indicator
Current environment and risk level:

```
Execution Environment: DRY_RUN
Risk Level: LOW ✓
├─ MOCK:     Safe sandbox (learning only)
├─ DRY_RUN:  Current (simulation, no side effects)
├─ LIVE:     Production (full execution, use caution)
└─ LOCKED:   Emergency (system frozen to MOCK)
```

**Environment Guide:**
- 🟢 **MOCK** (Safe Sandbox)
  - Use for: Initial training, experiments
  - Characteristics: No real browser actions, pure simulation
  - Risk: None
  
- 🟡 **DRY_RUN** (Simulation)
  - Use for: Testing, validation before production
  - Characteristics: Real browser but no data modification
  - Risk: Low (read-only operations)
  
- 🔴 **LIVE** (Production)
  - Use for: Real tasks with actual consequences
  - Characteristics: Full execution with side effects
  - Risk: High (verify all safety gates before entering)
  
- ⚫ **LOCKED** (Emergency Freeze)
  - Triggered: By critical safety violations
  - Characteristics: System forced to MOCK, no LIVE/DRY_RUN allowed
  - Recovery: Manual override by admin

**Commands:**
```bash
# Check current environment
python dashboard_app.py status

# Switch environment
python dashboard_app.py environment mock      # Safe mode
python dashboard_app.py environment dry_run   # Simulation
python dashboard_app.py environment live      # Production
```

#### 3. Active Agents Table
Agents currently running:

```
ACTIVE AGENTS (3 operational)
─────────────────────────────────────────────────────────────
Agent ID    Role        Status    Success   Last Activity
─────────────────────────────────────────────────────────────
agent_1     executor    ✓         95%       2024-01-15 14:35:12
agent_2     validator   ✓         98%       2024-01-15 14:35:15
agent_3     learner     ✓         87%       2024-01-15 14:35:10
```

**What to Look For:**
- ✓ Status = Agent operational
- ⚠️ Status = Agent degraded
- ✗ Status = Agent offline

**Success Rate Interpretation:**
- 95%+: Excellent performance
- 85-94%: Good performance
- 70-84%: Monitor, may need intervention
- <70%: Alert, investigate immediately

#### 4. Recent Tool Executions
Last 10 tool executions:

```
RECENT TOOL EXECUTIONS (Last 10)
─────────────────────────────────────────────────────────────
Time             Tool          Status     Confidence  Duration
─────────────────────────────────────────────────────────────
14:35:15 UTC     button_click  ✓          0.94        125ms
14:35:08 UTC     text_input    ✓          0.96        45ms
14:34:52 UTC     scroll_page   ✓          0.82        235ms
14:34:40 UTC     wait_element  ✓          0.89        1200ms
14:34:22 UTC     search_page   ⚠️         0.63        890ms
14:33:45 UTC     button_click  ✓          0.93        132ms
```

**Status Meanings:**
- ✓ = Success
- ⚠️ = Partial success or warning
- ✗ = Failed

**Confidence Scores:**
- 0.90+: High confidence, trust execution
- 0.70-0.89: Moderate confidence, verify result
- <0.70: Low confidence, manual review recommended

#### 5. Safety Gate Decisions
Recent safety approval/rejection decisions:

```
SAFETY GATE DECISIONS (Last 10)
─────────────────────────────────────────────────────────────
Time             Gate Type    Decision  Reason
─────────────────────────────────────────────────────────────
14:35:10 UTC     RATE_LIMIT   ✓ ALLOW   <100 calls/min
14:34:22 UTC     DATA_ACCESS  ✓ ALLOW   Non-sensitive data
14:33:15 UTC     CONSEQUENCE  ⛔ BLOCK   Modifies user data
14:32:40 UTC     TIMEOUT      ✓ ALLOW   <5000ms latency
```

**Gate Types:**
- **RATE_LIMIT**: Too many tool calls? Blocked to prevent resource exhaustion
- **DATA_ACCESS**: Accessing sensitive data? Requires approval
- **CONSEQUENCE**: Will change data? Requires verification
- **TIMEOUT**: Taking too long? Blocked to prevent hangs

**Decisions:**
- ✓ ALLOW: Gate approved execution
- ⛔ BLOCK: Gate rejected execution (safety concern)
- ⚠️ PENDING: Awaiting human approval (check Interaction Dashboard)

### Monitoring Best Practices

**Check Every 5 Minutes:**
1. Overall health score (should stay 85+)
2. Agent status (all should be ✓)
3. Safety gate blocks (should be zero)

**Investigate If:**
- Health drops below 85
- Any agent shows ⚠️ or ✗
- More than 2 recent gate blocks
- Any red ALERT widgets

## Dashboard 3: Interaction Dashboard

### Purpose
**"What does Buddy need from me right now?"**

Chat interface, pending approvals, active tasks, and user feedback.

### Key Sections

#### 1. Chat Interface
Conversation history with Buddy:

```
CHAT HISTORY
─────────────────────────────────────────────────────────────
[14:35:15] USER: "Click the login button"
[14:35:20] BUDDY: "I'll click the login button for you."
[14:35:45] BUDDY: "Login button clicked successfully (0.94 confidence)."
[14:36:00] USER: "Then enter my username"
[14:36:05] BUDDY: "Entering username in the text field..."
[14:36:10] BUDDY: ⚠️ "Username field not found. May be dynamically loaded."
[14:36:10] BUDDY: "Awaiting approval to retry with wait(500ms)."
[14:36:15] USER: "Go ahead"
```

**How to Use:**
- View conversation history with Buddy
- See execution progress in real-time
- Respond to Buddy's clarification requests
- Give approval for uncertain actions

#### 2. Pending Approvals
Actions requiring human sign-off:

```
PENDING APPROVALS (2)
─────────────────────────────────────────────────────────────

APPROVAL #1: [MEDIUM PRIORITY]
├─ Action: Click "Delete Account" button
├─ Reason: Consequence flag - deletes user account
├─ Tool: button_click on selector #delete-account
├─ Confidence: 0.89
├─ Context: User task is "Clean up test accounts"
├─ Recommendation: ✓ APPROVE (matches task intent)
└─ Your Decision: [APPROVE] [REJECT] [GET_MORE_INFO]

APPROVAL #2: [LOW PRIORITY]
├─ Action: Retry scroll_page with longer timeout (3000ms)
├─ Reason: Previous attempt failed, need longer wait
├─ Tool: scroll_page with timeout=3000
├─ Confidence: 0.71
├─ Context: Dynamic page takes time to load
├─ Recommendation: ⚠️ MAYBE (high timeout may cause hangs)
└─ Your Decision: [APPROVE] [REJECT] [GET_MORE_INFO]
```

**Approval Levels:**
- 🔴 **CRITICAL**: High-consequence action (data deletion, system change)
- 🟡 **MEDIUM**: Moderate consequence (retry, different approach)
- 🟢 **LOW**: Minor consequence (just confirm you want this)

**Decision Options:**
- ✓ **APPROVE**: Proceed with action
- ✗ **REJECT**: Don't do this action, try alternative
- ❓ **GET_MORE_INFO**: Ask Buddy for more details before deciding

#### 3. Active Tasks
Currently running or pending tasks:

```
ACTIVE TASKS (3)
─────────────────────────────────────────────────────────────

TASK #1: [IN_PROGRESS] Login to test account
├─ Priority: HIGH
├─ Progress: 3/5 steps complete
├─ Current Step: "Enter password"
├─ Status: Waiting for element visibility
├─ Estimated Time: 2 minutes remaining
├─ Last Update: 2024-01-15 14:35:22 UTC
└─ Actions: [PAUSE] [CANCEL] [MODIFY]

TASK #2: [PENDING_APPROVAL] Submit form with validation
├─ Priority: MEDIUM
├─ Progress: 2/4 steps complete
├─ Next Step: Click submit button (needs approval)
├─ Status: Awaiting human approval
├─ Blocker: Medium-confidence tool on form submission
└─ Actions: [PREVIEW] [APPROVE] [REJECT]

TASK #3: [COMPLETED] Verify account exists
├─ Priority: LOW
├─ Progress: 4/4 steps complete (100%)
├─ Final Result: ✓ Account exists and verified
├─ Completion Time: 1m 23s
└─ Actions: [VIEW_LOG] [RETRY]
```

**Task States:**
- 🟡 **PENDING**: Not started, waiting to be queued
- 🔵 **IN_PROGRESS**: Currently running
- ⏸️ **PAUSED**: Temporarily stopped, can resume
- ⏳ **PENDING_APPROVAL**: Blocked waiting for human approval
- ✓ **COMPLETED**: Finished successfully
- ✗ **FAILED**: Error occurred, can retry
- ⛔ **CANCELLED**: User canceled

**Priority Guide:**
- 🔴 **HIGH**: Critical path, needed immediately
- 🟡 **MEDIUM**: Important but not blocking
- 🟢 **LOW**: Nice to have, can defer

**Actions:**
- **[PAUSE]**: Pause task, can resume later
- **[CANCEL]**: Stop task permanently
- **[MODIFY]**: Edit task parameters
- **[PREVIEW]**: See what will happen before approval
- **[APPROVE]**: Give approval to proceed
- **[REJECT]**: Don't proceed with this step

#### 4. Recent Execution Feedback
Results from completed executions:

```
RECENT EXECUTION FEEDBACK
─────────────────────────────────────────────────────────────

[14:35:10] EXECUTION FEEDBACK: Task "Login" 
├─ Status: ✓ SUCCESS
├─ Actual Behavior: "Clicked login, page redirected to dashboard"
├─ Expected Behavior: "Click login button, should redirect"
├─ Match: ✓ 100% expected
├─ Feedback: "Great! Exactly what I wanted"
└─ Confidence Delta: +0.02 (Buddy learned this works)

[14:34:45] EXECUTION FEEDBACK: Tool "scroll_page"
├─ Status: ⚠️ PARTIAL
├─ Actual Behavior: "Scrolled, but element not visible"
├─ Expected Behavior: "Scroll to make element visible"
├─ Match: ⚠️ 50% expected (element still not visible)
├─ Feedback: "Not quite - element is still hidden"
└─ Confidence Delta: -0.05 (Buddy will try different approach)

[14:33:20] EXECUTION FEEDBACK: Tool "text_input"
├─ Status: ✗ FAILURE  
├─ Actual Behavior: "Text input failed - field locked"
├─ Expected Behavior: "Type text in field"
├─ Match: ✗ 0% expected
├─ Feedback: "That didn't work, the field was locked"
└─ Confidence Delta: -0.08 (Buddy will add unlock step)
```

**Feedback Types:**
- ✓ **SUCCESS**: Execution went exactly as expected
- ⚠️ **PARTIAL**: Partially succeeded, some parts not as expected
- ✗ **FAILURE**: Execution failed completely

**How to Provide Feedback:**
1. **Describe actual behavior**: What actually happened?
2. **Compare to expected**: What should have happened?
3. **Rate confidence**: Should Buddy be more/less confident?
4. **Provide reason**: Why didn't it work?

### Common Interaction Scenarios

#### Scenario 1: Buddy Asks for Clarification
```
BUDDY: "I need to click 'Save' but there are 3 buttons on the page. 
        Which one should I click?"

YOU: "The blue one in the bottom right"

BUDDY: "Got it. I'll click the Save button in the bottom right."
```

#### Scenario 2: Approving a High-Risk Action
```
PENDING APPROVAL:
- Action: Delete user data
- Confidence: 0.85
- Your Decision: [APPROVE] - "Yes, we're testing cleanup"

BUDDY: "Deleting user data as approved."
BUDDY: "Data deletion completed successfully."
```

#### Scenario 3: Rejecting an Uncertain Action
```
PENDING APPROVAL:
- Action: Modify system settings
- Confidence: 0.62 (LOW)
- Your Decision: [REJECT] - "Too risky, find another way"

BUDDY: "Understood, I'll try a different approach instead."
BUDDY: "Using alternative method to accomplish the task..."
```

## Developer Mode

### Purpose
**"Show me all 24 phases and raw data streams"**

Access to complete system internals for debugging and audit.

### Activating Developer Mode
```bash
python dashboard_app.py dev-mode
# Output: ✓ Developer Mode ENABLED
```

### What's Available

```
DEVELOPER MODE - Phase Tabs & Audit Timeline
═════════════════════════════════════════════════════════════

Developer Mode: ACTIVE ✓
Last Accessed: 2024-01-15 14:35:22 UTC

Available Phases:
  - Phase 1:  System Initialization
  - Phase 2:  Approval & Clarification Engine
  - Phase 3:  ... (through Phase 24)
  - Phase 24: Tool Orchestration & Learning
```

### Viewing Phase Details
```bash
# View Phase 16 (Learning) details
python dashboard_app.py phase 16

# Shows:
# - learning_metrics.json (reward models)
# - confidence_updates.jsonl (real-time confidence)
# - tool_learning_summary.json (per-tool learning)
```

### Viewing Audit Timeline
```bash
python dashboard_app.py nav-history 50
# Shows last 50 dashboard navigations with timestamps and reasons
```

## Command Reference

### Navigation
```bash
python dashboard_app.py learning          # Learning Dashboard
python dashboard_app.py operations        # Operations Dashboard  
python dashboard_app.py interaction       # Interaction Dashboard
python dashboard_app.py developer         # Developer Mode
python dashboard_app.py navigate <mode>   # Navigate to mode
```

### Environment Control
```bash
python dashboard_app.py environment mock      # Safe sandbox
python dashboard_app.py environment dry_run   # Simulation
python dashboard_app.py environment live      # Production
python dashboard_app.py environment locked    # Emergency freeze
```

### Export & Audit
```bash
python dashboard_app.py export-state backup.json         # Save state
python dashboard_app.py export-audit audit_2024_01_15.json  # Export audit trail
python dashboard_app.py nav-history 20                   # Last 20 navigations
python dashboard_app.py env-history 20                   # Last 20 env changes
```

### System Info
```bash
python dashboard_app.py status             # Current status
python dashboard_app.py help               # Show help
```

## Troubleshooting

### Dashboard Not Updating
```bash
# Force refresh
python dashboard_app.py operations
# Try Developer Mode
python dashboard_app.py dev-mode
# Check phase outputs exist
ls outputs/phase*/*.json
```

### Pending Approval Stuck
```bash
# Check Interaction Dashboard
python dashboard_app.py interaction
# Manually approve or reject
# If really stuck: export state and reset
python dashboard_app.py export-state stuck_state.json
```

### Performance Issues
```bash
# Check system health
python dashboard_app.py operations
# Look for Resource Usage %
# If >80%, may need to pause tasks
python dashboard_app.py status
```

## Performance Summary

| Task | Typical Time | Max Time |
|------|----------|----------|
| Load Learning Dashboard | ~150ms | 500ms |
| Load Operations Dashboard | ~100ms | 300ms |
| Load Interaction Dashboard | ~50ms | 200ms |
| Navigate between dashboards | <100ms | <500ms |
| Export state | <500ms | 2s |
| Export audit trail | <200ms | 1s |

## Success Metrics

### Healthy System Indicators
- ✓ Learning Dashboard: Confidence trending up
- ✓ Operations Dashboard: Health 90+, 0 blocks
- ✓ Interaction Dashboard: Few pending approvals
- ✓ Execution time: Consistent <2s per tool

### Warning Signs
- ⚠️ Learning: Confidence plateaued >2 days
- ⚠️ Operations: Health <80, frequent anomalies
- ⚠️ Interaction: >5 pending approvals, stuck tasks
- ⚠️ Execution: Tool calls >5s average

### Critical Issues
- 🔴 Learning: Confidence declining daily
- 🔴 Operations: Health <70, safety blocks
- 🔴 Interaction: Tasks failing repeatedly
- 🔴 Execution: Tools failing >20% of time
