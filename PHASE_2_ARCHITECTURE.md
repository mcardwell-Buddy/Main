# Phase 2 Architecture Overview

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    HTTP CLIENT / USER                            │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                    POST /reasoning/execute
                      {"goal": "..."}
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│           PHASE 2: PRE-VALIDATION SYSTEM                         │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ 1. Non-empty text validation                             │   │
│  │ 2. Length bounds check (10-500 chars)                    │   │
│  │ 3. Tool availability verification                        │   │
│  │ 4. Grammar/syntax check                                  │   │
│  │ 5. Dangerous command detection                           │   │
│  │ 6. Context completeness check                            │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│  Output: PreValidationResult                                      │
│  - validation_status: passed | failed                            │
│  - failures: List[ValidationCheck]                               │
│  - total_confidence_delta: float (adjustment)                    │
│  - suggested_questions: List[str]                                │
└──────────────────────┬──────────────────────────────────────────┘
                       │ (passed)
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│        PHASE 1: AGENT REASONING (Existing System)                │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Goal decomposition                                       │   │
│  │ Tool selection                                           │   │
│  │ Argument generation                                      │   │
│  │ Reasoning summary                                        │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│  Output: ReasoningResult                                          │
│  - success: bool                                                  │
│  - reasoning_summary: str                                         │
│  - tools_used: List[ToolCall]                                     │
│  - understanding: dict                                            │
│  - goals_met: bool                                                │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│     PHASE 2: GRADED CONFIDENCE CALCULATION                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Calculate 4 confidence factors:                          │   │
│  │                                                          │   │
│  │ 1. Goal Understanding (30%)      [from reasoning]        │   │
│  │    - How clear is intent? [0.0-1.0]                     │   │
│  │                                                          │   │
│  │ 2. Tool Availability (30%)        [from tools_used]      │   │
│  │    - Are all tools available? [0.0-1.0]                 │   │
│  │                                                          │   │
│  │ 3. Context Richness (20%)         [from session]         │   │
│  │    - Is sufficient context available? [0.0-1.0]         │   │
│  │                                                          │   │
│  │ 4. Tool Confidence (20%)          [from tool metadata]   │   │
│  │    - Are tools deterministic? [0.0-1.0]                 │   │
│  │                                                          │   │
│  │ Final: confidence = sum(factor × weight)                 │   │
│  │        confidence ∈ [0.0, 1.0]  (continuous)            │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│  Output: float [0.0, 1.0]                                         │
│  - 0.00-0.30: Very low (almost impossible)                       │
│  - 0.30-0.55: Low (needs clarification)                          │
│  - 0.55-0.85: Medium (needs approval)                            │
│  - 0.85-1.00: High (auto-execute)                                │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│      PHASE 2: APPROVAL GATES DECISION LOGIC                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Route execution based on confidence:                     │   │
│  │                                                          │   │
│  │ IF confidence >= 0.85:                                  │   │
│  │   ├─► ExecutionPath.HIGH_CONFIDENCE                    │   │
│  │   └─► Execute tools immediately                         │   │
│  │       (No approval needed)                              │   │
│  │                                                          │   │
│  │ ELIF confidence >= 0.55:                                │   │
│  │   ├─► ExecutionPath.APPROVED                           │   │
│  │   └─► Generate ApprovalRequest                          │   │
│  │       (Wait for user/Soul approval)                    │   │
│  │                                                          │   │
│  │ ELSE (confidence < 0.55):                               │   │
│  │   ├─► ExecutionPath.CLARIFICATION                      │   │
│  │   └─► Generate ClarificationRequest                     │   │
│  │       (Ask for clarification)                           │   │
│  │                                                          │   │
│  │ ELSE IF any errors in reasoning:                        │   │
│  │   └─► ExecutionPath.REJECTED                           │   │
│  │       (Don't execute)                                   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│  Output: ApprovalDecision                                         │
│  - execution_path: ExecutionPath enum                            │
│  - approval_request: ApprovalRequest (if needed)                 │
│  - clarification_request: ClarificationRequest (if needed)       │
└──────────────────────┬──────────────────────────────────────────┘
                       │
          ┌────────────┼────────────┬──────────────┐
          │            │            │              │
          ▼            ▼            ▼              ▼
    HIGH_CONF      APPROVED    CLARIFICATION   REJECTED
       PATH         PATH           PATH          PATH
        │            │              │             │
        │            │              │             │
        ▼            ▼              ▼             ▼
   EXECUTE       SEND TO         GENERATE      RETURN
   TOOLS      SOUL SYSTEM       QUESTIONS      ERROR
        │            │              │             │
        │            ▼              │             │
        │    ┌──────────────────┐   │             │
        │    │ Soul Callback:   │   │             │
        │    │ /approval/       │   │             │
        │    │ respond/{id}     │   │             │
        │    └──────────────────┘   │             │
        │            │              │             │
        │            │              ▼             │
        │            │         RETURN TO        │
        │            │         CLIENT:          │
        │            │    clarification_       │
        │            │    request_id           │
        │            │                         │
        │            ▼                         │
        │    (WAIT FOR APPROVAL)              │
        │            │                         │
        │            ▼                         │
        │    Client responds via              │
        │    POST /approval/respond/{id}      │
        │            │                         │
        │            ▼                         │
        │    If approved: Execute tools       │
        │    If denied: Return error          │
        │            │                         │
        └────────────┴─────────────┬───────────┘
                                   │
                                   ▼
        ┌──────────────────────────────────────┐
        │  PHASE 2: SOUL INTEGRATION CALLBACKS  │
        │  ┌────────────────────────────────┐  │
        │  │ Log to Soul System:            │  │
        │  │  - Approval requests           │  │
        │  │  - Clarification requests      │  │
        │  │  - Execution decisions         │  │
        │  │  - Tool execution results      │  │
        │  │  - Approval decisions          │  │
        │  │  - Timeout events              │  │
        │  └────────────────────────────────┘  │
        │                                      │
        │  Soul manages:                       │
        │  - Conversation context              │
        │  - Approval workflow state           │
        │  - Clarification response tracking   │
        │  - Audit trail                       │
        └──────────────────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────────┐
        │  HTTP RESPONSE (Always 200 OK)      │
        │  ┌────────────────────────────────┐  │
        │  │ {                              │  │
        │  │   "success": bool,             │  │
        │  │   "result": {                  │  │
        │  │     "reasoning_summary": str,  │  │
        │  │     "tool_results": list,      │  │
        │  │     "tools_used": list,        │  │
        │  │     "understanding": dict,     │  │
        │  │     "confidence": float        │  │
        │  │   },                           │  │
        │  │   "approval_state": str,       │  │
        │  │   "soul_request_id": str,      │  │
        │  │   "execution_path": str,       │  │
        │  │   "timestamp": str             │  │
        │  │ }                              │  │
        │  └────────────────────────────────┘  │
        └──────────────────────────────────────┘
```

## Data Flow: High Confidence Case

```
User Goal: "Click the submit button"
         │
         ▼
[Pre-Validation] ─→ PASSED ✓
         │
         ▼
[Agent Reasoning] ─→ tool: button_clicker, success: true
         │
         ▼
[Confidence Calc] ─→ 0.95 (HIGH ✓)
         │
         ▼
[Approval Gates] ─→ ExecutionPath.HIGH_CONFIDENCE
         │
         ▼
[Execute Tools] ─→ Button clicked, DOM updated
         │
         ▼
HTTP 200:
{
  "success": true,
  "result": {
    "reasoning_summary": "Clicked submit button",
    "tool_results": [{"success": true}],
    "tools_used": ["button_clicker"],
    "understanding": {"action": "click", "target": "submit button"},
    "confidence": 0.95
  },
  "approval_state": "none",
  "execution_path": "high_confidence",
  "timestamp": "2026-02-05T10:30:45Z"
}
```

## Data Flow: Medium Confidence Case

```
User Goal: "Fill in the form"
         │
         ▼
[Pre-Validation] ─→ PASSED ✓
         │
         ▼
[Agent Reasoning] ─→ tools: [form_filler, input_finder], success: true
         │
         ▼
[Confidence Calc] ─→ 0.70 (MEDIUM ✓)
         │
         ▼
[Approval Gates] ─→ ExecutionPath.APPROVED
                ─→ ApprovalRequest created
         │
         ▼
[Soul Integration] ─→ Log to Soul system
                   ─→ Return request_id: "req-abc123"
         │
         ▼
HTTP 200:
{
  "success": true,
  "result": {
    "reasoning_summary": "Will fill in form with available tools",
    "tool_results": [],
    "tools_used": ["form_filler", "input_finder"],
    "understanding": {"action": "fill", "target": "form"},
    "confidence": 0.70
  },
  "approval_state": "awaiting_approval",
  "execution_path": "approved",
  "soul_request_id": "req-abc123",
  "timestamp": "2026-02-05T10:30:45Z"
}

         ▼
[User/Soul Decision]
         │
         ├─→ Approved
         │   │
         │   ▼
         │ [Execute Tools] ─→ Form filled
         │   │
         │   ▼
         │ HTTP 200:
         │ {
         │   "success": true,
         │   "approval_state": "approved",
         │   "result": {"tool_results": [...]}
         │ }
         │
         └─→ Rejected
             │
             ▼
           HTTP 200:
           {
             "success": false,
             "approval_state": "denied",
             "error": "User rejected execution"
           }
```

## Data Flow: Low Confidence Case

```
User Goal: "Help me"
         │
         ▼
[Pre-Validation] ─→ PASSED (vague but valid) ✓
         │
         ▼
[Agent Reasoning] ─→ confidence factors low, success: false
         │
         ▼
[Confidence Calc] ─→ 0.35 (LOW ✗)
         │
         ▼
[Approval Gates] ─→ ExecutionPath.CLARIFICATION
                ─→ ClarificationRequest created
         │
         ▼
[ClarificationGen] ─→ "What do you need help with?
                       1. Finding an element
                       2. Filling a form
                       3. Clicking a button
                       4. Extracting data"
         │
         ▼
[Soul Integration] ─→ Log to Soul system
                   ─→ Return request_id: "clar-xyz789"
         │
         ▼
HTTP 200:
{
  "success": false,
  "result": {
    "reasoning_summary": "Goal too ambiguous, clarification needed",
    "tool_results": [],
    "tools_used": [],
    "understanding": {"error": "ambiguous goal"},
    "confidence": 0.35
  },
  "approval_state": "none",
  "execution_path": "clarification",
  "soul_request_id": "clar-xyz789",
  "suggested_questions": [
    "What do you need help with?",
    "Please specify: action (click/fill/find), target (element/form/data)"
  ],
  "timestamp": "2026-02-05T10:30:45Z"
}

         ▼
[User Clarification]
         │
         ├─→ "Click the submit button"
         │   │
         │   ▼
         │ [Retry /reasoning/execute] ─→ Confidence: 0.95
         │                               Execution: IMMEDIATE
         │
         └─→ No response
             │
             ▼
           [Timeout after 5 min]
           HTTP 200:
           {
             "success": false,
             "approval_state": "timeout",
             "error": "Clarification timeout"
           }
```

## Module Dependency Graph

```
┌────────────────────┐
│ phase2_confidence  │
│  (standalone)      │
└────────────────────┘
    ▲           ▲
    │           │
    │           └─────────────────┐
    │                             │
    │                             ▼
┌────────────────────┐    ┌──────────────────┐
│ phase2_            │    │ phase2_          │
│ prevalidation      │    │ approval_gates   │
│  (depends on       │    │  (depends on     │
│   confidence)      │    │   confidence)    │
└────────────────────┘    └──────────────────┘
    │                             │
    │                             │
    └──────────────┬──────────────┘
                   │
                   ▼
       ┌──────────────────────┐
       │ phase2_              │
       │ clarification        │
       │  (standalone)        │
       └──────────────────────┘
                   │
                   │
    ┌──────────────┼──────────────┐
    │              │              │
    ▼              ▼              ▼
┌──────────┐  ┌────────────┐  ┌──────────────┐
│ phase2_  │  │ phase2_    │  │ phase2_      │
│ soul_    │  │ response_  │  │ (main.py)    │
│ integration│  │ schema     │  │ (endpoint)   │
└──────────┘  └────────────┘  └──────────────┘
```

## Phase 2 vs Phase 1 Comparison

### Phase 1 (Original)
```
Goal → Agent Reasoning → Tools → Results
         │
         └─→ Bimodal confidence (0 or 1)
         └─→ No approval workflow
         └─→ Execute if success=true
         └─→ No clarification
```

### Phase 2 (Enhanced)
```
Goal → Pre-Validation ─→ Agent Reasoning ─→ Graded Confidence
         │ (catch issues early)    │            │ (0.0-1.0)
         │                         │            │
         └─────────────────────────┴────────────┤
                                                ▼
                                    Approval Gates Decision
                                          │
                        ┌─────────────────┼─────────────────┐
                        │                 │                 │
                   ≥0.85: AUTO       0.55-0.85:          <0.55:
                   EXECUTE           REQUEST            REQUEST
                        │            APPROVAL            CLARIFICATION
                        │                 │                 │
                        ▼                 ▼                 ▼
                    Execute           Wait for          Ask User/Soul
                    Tools         User/Soul Approval    for Clarification
                        │                 │                 │
                        └─────────────────┼─────────────────┘
                                          │
                                          ▼
                                    Response with:
                                   - confidence (0.0-1.0)
                                   - execution_path
                                   - approval_state
                                   - soul_request_id
```

## Confidence Score Distribution (Expected)

```
Frequency
    │
    │
    │    ╱╲
    │   ╱  ╲
    │  ╱    ╲
    │ ╱      ╲     ╱╲
    │╱        ╲   ╱  ╲
    ├─────────┼──────────────────────
    │         │           ╱╲
    │         │          ╱  ╲
    │         │         ╱    ╲
    │         │        ╱      ╲
    └─────────┼───────────────────────▶
    0.0      0.5      1.0       Confidence

Phase 1 (bimodal):  Two peaks at 0.0 and 1.0
Phase 2 (continuous): Smooth distribution 0.0-1.0
```

## Decision Thresholds

```
Confidence [0.0 ──────────────────────────────────────── 1.0]
           │                                             │
           │                                             │
    0.0    0.2    0.4    0.55   0.7    0.85    0.95   1.0
    │      │      │      │      │      │       │      │
    └──────┴──────┴──────┴──────┴──────┴───────┴──────┘
                     │              │              │
              CLARIFICATION      APPROVAL      AUTO-EXECUTE
              REQUEST            GATE          (immediate)
              (Ambiguous)     (Medium Conf)    (High Conf)
```

## Error Handling Flow

```
HTTP Request
    │
    ▼
Try:
├─ Pre-Validation
│  ├─ Fail ─→ Return error (validation_failed)
│  │
│  └─ Pass ─→ Continue
│
├─ Agent Reasoning
│  ├─ Error ─→ Return error (reasoning_failed)
│  │
│  └─ Success ─→ Continue
│
├─ Confidence Calculation
│  ├─ Error ─→ Return error (confidence_calc_failed)
│  │
│  └─ Success ─→ Continue
│
├─ Approval Gates Decision
│  ├─ Error ─→ Return error (approval_gate_failed)
│  │
│  └─ Success ─→ Route by execution path
│
├─ [HIGH_CONFIDENCE or APPROVED or CLARIFICATION]
│  ├─ Error ─→ Return error (execution_failed)
│  │
│  └─ Success ─→ Continue
│
└─ Response Building
   ├─ Error ─→ Return error (response_build_failed)
   │
   └─ Success ─→ Return HTTP 200 with response

Catch-All: Always return HTTP 200 OK
          (Never return HTTP 5xx)
```

## Feature Flag Hierarchy

```
PHASE2_ENABLED (master switch)
    │
    ├─→ PHASE2_PRE_VALIDATION_ENABLED
    │   └─→ Run 6 validation checks before reasoning
    │
    ├─→ PHASE2_GRADED_CONFIDENCE_ENABLED
    │   └─→ Calculate continuous confidence [0.0-1.0]
    │       Otherwise: use Phase 1 (bimodal 0/1)
    │
    ├─→ PHASE2_APPROVAL_GATES_ENABLED
    │   └─→ Route by confidence thresholds
    │       Otherwise: execute if success=true
    │
    ├─→ PHASE2_CLARIFICATION_ENABLED
    │   └─→ Generate clarification questions for low confidence
    │       Otherwise: only approve/reject
    │
    └─→ (Each flag is independent)

If PHASE2_ENABLED=False:
    ├─ All Phase 2 systems disabled
    ├─ Fall back to Phase 1 behavior
    └─ Return Phase 1 response schema
```

---

This architecture ensures:
✓ Clear data flow through all systems
✓ Independent feature flags for selective rollout
✓ Continuous confidence distribution (not bimodal)
✓ Three execution paths (auto-execute, approval, clarification)
✓ Complete Soul system integration
✓ Backward compatibility with Phase 1
✓ Safe fallback to Phase 1 if Phase 2 disabled
