================================================================================
📋 PHASE 2 DESIGN DOCUMENT - SOUL INTEGRATION & APPROVAL GATES
================================================================================

Status: DESIGN PHASE (Approval Required Before Implementation)
Baseline: Phase 1 Stabilization Complete, Synthetic Observation Metrics Ready
Autonomy: Level 1 Suggest-Only (maintained until Phase 2 gates operational)
Code Status: No production changes during design phase

================================================================================
TABLE OF CONTENTS
================================================================================

1. Phase 2 Overview & Objectives
2. Soul Integration Architecture
3. Approval Gates System Design
4. Graded Confidence System Design
5. Clarification Handling Mechanism
6. Pre-Validation for Failure-Injected Scenarios
7. Integration Points & Data Flow
8. Isolation & Safety Constraints
9. Testing & Rollout Strategy
10. Implementation Roadmap

================================================================================
1. PHASE 2 OVERVIEW & OBJECTIVES
================================================================================

Phase 2 Goal: Enable user approval workflows and nuanced confidence reasoning
while maintaining Level 1 suggest-only autonomy until all safety gates are active.

Objectives:
  A) Integrate Soul system for approval request validation
  B) Implement approval gates before tool execution
  C) Introduce graded confidence (0.0-1.0 continuous) for nuanced decisions
  D) Add clarification handling for ambiguous goals
  E) Implement pre-validation to reduce failure-injected risk

Key Constraint: All new systems must be isolated, testable, and deactivatable.

Synthetic Observation Findings to Address:
  • Confidence is currently bimodal (0.0 or 0.70) - Phase 2 adds grading
  • Ambiguous goals are rejected silently - Phase 2 adds clarification questions
  • Failure-injected goals have 22% immediate reject - Phase 2 adds pre-validation
  • No approval workflow - Phase 2 adds Soul-based approval gates
  • Tool selection is accurate - Phase 2 maintains existing accuracy

================================================================================
2. SOUL INTEGRATION ARCHITECTURE
================================================================================

Purpose: Soul is the user-facing approval and memory system that validates
approval requests, maintains conversation context, and tracks approval history.

Integration Points:
  a) Approval request validation (before tool execution)
  b) Clarification question validation (for ambiguous goals)
  c) Context/memory retrieval (for conversation history)
  d) Approval decision storage (for audit trail)

High-Level Architecture:

┌─────────────────────────────────────────────────────────────────┐
│                    /reasoning/execute (Level 1)                 │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 1. Pre-Validation (NEW - Phase 2)                       │   │
│  │    - Check goal feasibility (before reasoning)          │   │
│  │    - Detect ambiguous goals early                       │   │
│  │    - Detect failure-injected scenarios                  │   │
│  │    - Return clear rejection or proceed                  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                         ↓                                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 2. Agent Reasoning (EXISTING - Phase 1)                 │   │
│  │    - Generate reasoning, confidence, tool list          │   │
│  │    - Confidence now: 0.0-1.0 continuous (Phase 2)       │   │
│  │    - Generate clarification questions if ambiguous      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                         ↓                                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 3. Approval Gates (NEW - Phase 2)                       │   │
│  │    IF confidence >= approval_threshold:                 │   │
│  │       → Execute tools (Level 1 → Level 2)              │   │
│  │    ELSE IF approval_required=true:                      │   │
│  │       → Ask Soul for approval (via callback)            │   │
│  │    ELSE:                                                │   │
│  │       → Return reasoning without execution              │   │
│  └─────────────────────────────────────────────────────────┘   │
│                         ↓                                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 4. Execution or Return (MODIFIED - Phase 2)             │   │
│  │    IF approval_granted OR high_confidence:              │   │
│  │       → Execute tools                                   │   │
│  │    ELSE:                                                │   │
│  │       → Return suggestion + approval request to Soul    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                         ↓                                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 5. Response to Caller (MODIFIED - Phase 2)              │   │
│  │    Always return:                                       │   │
│  │    {success, result, approval_state, soul_request_id}   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│ INVARIANT: Tool execution requires (high_confidence OR          │
│            approval_granted) to transition from Level 1→2       │
└─────────────────────────────────────────────────────────────────┘

                              ↓
                     ┌────────────────┐
                     │  Soul System   │
                     │  (Approval)    │
                     │  (Memory)      │
                     │  (Context)     │
                     └────────────────┘
                         (Manages:)
                    • Approval requests
                    • Approval history
                    • Conversation context
                    • Clarification state

Soul Integration Points (Callback Pattern):
  1. soul.validate_approval_request(approval_request: dict) → bool
     Purpose: Check if approval request is valid and actionable
     Input: {goal, confidence, tools_proposed, reasoning_summary}
     Output: {approved: bool, feedback: str}

  2. soul.validate_clarification(question: str, context: dict) → bool
     Purpose: Check if clarification question is appropriate and useful
     Input: {question, original_goal, ambiguity_reason}
     Output: {valid: bool, feedback: str}

  3. soul.get_conversation_context(session_id: str) → dict
     Purpose: Retrieve prior conversation history for graded confidence
     Output: {prior_goals: [], prior_approvals: [], context_summary: str}

  4. soul.store_approval_decision(decision: dict) → bool
     Purpose: Record approval decision for audit trail
     Input: {goal, confidence, decision, approval_time, approver}
     Output: {stored: bool, decision_id: str}

Phase 1 Phase 2 Comparison:
  Phase 1: /reasoning/execute → HTTP 200/500 (suggest only, no Soul)
  Phase 2: /reasoning/execute → HTTP 200 with approval_state field
           + optional Soul callback to request user approval
           + graded confidence (0.0-1.0) for nuanced gates

================================================================================
3. APPROVAL GATES SYSTEM DESIGN
================================================================================

Purpose: Implement decision gates that determine whether to execute tools
or request user approval before proceeding.

Gate Logic:

┌──────────────────────────────────────────────────────────┐
│ Given: confidence (0.0-1.0), approval_required (bool)    │
├──────────────────────────────────────────────────────────┤
│ GATE 1: High Confidence Path (Fast Execution)            │
│  IF confidence >= 0.85:                                  │
│     → Execute tools immediately                          │
│     → Return success/failure results                     │
│     INVARIANT: Tool execution requires no approval       │
│                                                          │
│ GATE 2: Medium Confidence Path (Suggest + Request)       │
│  IF 0.55 <= confidence < 0.85:                           │
│     → Generate approval request                          │
│     → Send to Soul system via callback                   │
│     → Return "awaiting_approval" state                   │
│     → Tool execution BLOCKED until approved              │
│     INVARIANT: Tool execution requires approval          │
│                                                          │
│ GATE 3: Low Confidence Path (Clarification or Reject)    │
│  IF confidence < 0.55:                                   │
│     → IF ambiguous goal detected:                        │
│        → Generate clarification questions                │
│        → Send to Soul system                             │
│        → Return "clarification_needed" state             │
│     → ELSE (failure-injected):                           │
│        → Generate error explanation                      │
│        → Return "execution_impossible" state             │
│     INVARIANT: No tool execution on low confidence       │
└──────────────────────────────────────────────────────────┘

Gate Thresholds (Tunable, Defaults):
  • High Confidence: >= 0.85 (auto-execute, no approval needed)
  • Medium Confidence: 0.55-0.85 (request approval, wait for yes/no)
  • Low Confidence: < 0.55 (clarify if possible, else reject)

Approval Request Structure:
```python
ApprovalRequest = {
    "request_id": "uuid",
    "goal": "original user goal",
    "confidence": 0.72,  # Why we're asking (not 100% sure)
    "reasoning_summary": "Agent believes...",
    "tools_proposed": ["tool_a", "tool_b"],
    "tool_descriptions": {"tool_a": "...", "tool_b": "..."},
    "risks": ["risk_1", "risk_2"],  # Known issues
    "alternatives": ["alt_1", "alt_2"],  # Other approaches
    "time_limit": 300,  # Seconds to wait for approval
    "approval_callback_url": "/approval/respond/{request_id}",
}
```

Approval Response:
```python
ApprovalResponse = {
    "request_id": "matching request_id",
    "approved": True,  # or False
    "feedback": "Go ahead, this looks right",  # or "Stop, don't do this"
    "timestamp": "2026-02-05T14:30:00Z",
    "approver": "user_id",
    "conditions": ["don't modify anything critical"],  # optional
}
```

Timeout Handling:
  • Approval requests timeout after 300 seconds (5 minutes)
  • If no response: Return "approval_timeout" state
  • User can retry goal or provide new direction
  • No automatic fallback (require explicit user action)

Isolation & Safety:
  ✓ Approval gates are independent from Phase 1 reasoning
  ✓ Tool execution only happens if (confidence >= 0.85) OR (approval_granted)
  ✓ No tool execution without one of these conditions
  ✓ Soul callbacks are non-blocking (approval happens asynchronously)
  ✓ All approval decisions are audited (stored in Soul)

================================================================================
4. GRADED CONFIDENCE SYSTEM DESIGN
================================================================================

Purpose: Move from bimodal (0.0 or 0.70) to continuous (0.0-1.0) confidence
to enable nuanced approval gates and decision-making.

Current State (Phase 1):
  • Bimodal distribution (30 runs at 0.0, 470 runs at 0.70)
  • Binary decision (accept or reject)
  • No intermediate uncertainty (0.2, 0.4, 0.6)
  • Confidence = (goal_understood AND tools_available)

Target State (Phase 2):
  • Continuous distribution (0.0-1.0 across full range)
  • Graded decision (commit, approve, clarify, reject)
  • Intermediate uncertainty (0.3-0.7 represents "needs approval")
  • Confidence = (goal_understood * tools_available * context_richness * tool_confidence)

Confidence Factors (Weighted):

Factor 1: Goal Understanding (30% weight)
  • 1.0: Clear, specific, unambiguous goal
  • 0.8: Clear intent, minor ambiguity
  • 0.5: Partially ambiguous, multiple interpretations
  • 0.2: Very vague, unclear what user wants
  • 0.0: Impossible to understand

Goal Clarity Signals:
  • Action verb present (e.g., "click", "find", "analyze"): +0.1
  • Target element specified (e.g., "the button on line 5"): +0.1
  • Context provided (e.g., "in the modal dialog"): +0.1
  • Expected outcome stated (e.g., "should return true"): +0.1
  • No contradictions (e.g., "help me" vs "don't help"): +0.1

Factor 2: Tool Availability (30% weight)
  • 1.0: All required tools available, no missing dependencies
  • 0.8: 1-2 tools available, alternative paths exist
  • 0.5: Tools available but limited, may need substitution
  • 0.2: Tools partially available, significant workarounds needed
  • 0.0: Required tools missing, cannot proceed

Tool Availability Signals:
  • Each required tool exists: +0.15 per tool
  • Tool has required capabilities: +0.15 per capability
  • Tool is working/healthy: +0.05 per tool

Factor 3: Context Richness (20% weight)
  • 1.0: Full context (conversation history, prior goals, shared state)
  • 0.8: Good context (1-2 prior goals, some shared state)
  • 0.5: Basic context (this is first goal, minimal state)
  • 0.2: Limited context (no prior history, unclear starting state)
  • 0.0: No context (isolated goal, no reference)

Context Richness Signals:
  • Prior conversation history available: +0.1
  • Session state available: +0.05
  • User preferences known: +0.05
  • Same tool used recently: +0.05

Factor 4: Tool Confidence (20% weight)
  • 1.0: All tools are deterministic, guaranteed to work
  • 0.8: Most tools deterministic, 1 may have side effects
  • 0.5: Mix of deterministic and uncertain tools
  • 0.2: Most tools have uncertainty or side effects
  • 0.0: Tools are very uncertain or dangerous

Tool Confidence Signals:
  • Tool is deterministic (read-only): +0.1 per tool
  • Tool is idempotent: +0.05 per tool
  • Tool has error handling: +0.05 per tool

Confidence Calculation:
```python
confidence = (
    goal_understanding * 0.30 +
    tool_availability * 0.30 +
    context_richness * 0.20 +
    tool_confidence * 0.20
)
```

Example Scenarios:

Scenario 1: Atomic Goal (Clear, Tools Available)
  • Goal Understanding: 1.0 (very clear: "click button #submit")
  • Tool Availability: 1.0 (all tools present)
  • Context Richness: 0.5 (first goal, no history)
  • Tool Confidence: 1.0 (deterministic tools)
  • Final: (1.0*0.3) + (1.0*0.3) + (0.5*0.2) + (1.0*0.2) = 0.90
  • Action: HIGH CONFIDENCE → Execute immediately

Scenario 2: Ambiguous Goal (Unclear, Tools Unavailable)
  • Goal Understanding: 0.2 (vague: "help me")
  • Tool Availability: 0.0 (no target tool)
  • Context Richness: 0.3 (no prior history)
  • Tool Confidence: 0.5 (uncertain what tool to use)
  • Final: (0.2*0.3) + (0.0*0.3) + (0.3*0.2) + (0.5*0.2) = 0.16
  • Action: LOW CONFIDENCE → Clarify or reject

Scenario 3: Medium Confidence (Clear but Missing Context)
  • Goal Understanding: 0.9 (clear: "refactor this function")
  • Tool Availability: 0.8 (tools available, limited options)
  • Context Richness: 0.4 (code not provided)
  • Tool Confidence: 0.7 (tools may have edge cases)
  • Final: (0.9*0.3) + (0.8*0.3) + (0.4*0.2) + (0.7*0.2) = 0.73
  • Action: MEDIUM CONFIDENCE → Request approval before executing

Implementation Notes:
  • Confidence calculation is deterministic (same goal → same confidence)
  • Confidence is calculated per goal, not accumulated
  • Confidence factors are tunable (weights can be adjusted)
  • New factors can be added (e.g., user_trust_level, execution_cost)

Phase 1 vs Phase 2 Comparison:
  Phase 1: confidence = 0.0 or 0.70 (bimodal, binary)
  Phase 2: confidence = 0.0-1.0 (continuous, graded)
  Benefit: Enables nuanced approval gates and learning

================================================================================
5. CLARIFICATION HANDLING MECHANISM
================================================================================

Purpose: For ambiguous goals (confidence < 0.55), generate clarification
questions that help user provide more context, enabling re-evaluation.

Clarification Flow:

┌────────────────────────────────────────────────────────┐
│ 1. Detect Ambiguous Goal                               │
│    • Confidence < 0.55 AND goal_understanding < 0.3   │
│    • Examples: "help me", "fix this", "make it work" │
└────────────────────────────────────────────────────────┘
                         ↓
┌────────────────────────────────────────────────────────┐
│ 2. Generate Clarification Questions                    │
│    • Identify missing information                      │
│    • Ask targeted, actionable questions                │
│    • Validate questions with Soul system               │
└────────────────────────────────────────────────────────┘
                         ↓
┌────────────────────────────────────────────────────────┐
│ 3. Send to Soul System                                 │
│    • soul.validate_clarification(questions)            │
│    • Store in conversation context                     │
│    • Wait for user response (300s timeout)             │
└────────────────────────────────────────────────────────┘
                         ↓
┌────────────────────────────────────────────────────────┐
│ 4. Process User Response                               │
│    • Update goal with clarified context                │
│    • Re-calculate confidence with new information      │
│    • If confidence >= 0.55: proceed with approval gate │
│    • Else: ask more questions or reject                │
└────────────────────────────────────────────────────────┘
                         ↓
┌────────────────────────────────────────────────────────┐
│ 5. Execute or Return (as per approval gates)           │
│    • Apply standard approval gate logic                │
│    • Execute if confidence high or approved            │
└────────────────────────────────────────────────────────┘

Clarification Question Generation:

Pattern 1: Action Identification
  Original Goal: "Help me get this done."
  Missing: Specific action
  Question: "What specific action do you want me to perform?
             (e.g., click a button, analyze code, generate text)"

Pattern 2: Target Identification
  Original Goal: "Fix this."
  Missing: What to fix
  Question: "What should I fix? (e.g., the button on the left,
             the error message, the calculation)"

Pattern 3: Context Identification
  Original Goal: "Complete the task."
  Missing: Which task, in what context
  Question: "Which task? Please provide the context or code you're
             working with, if applicable."

Pattern 4: Success Criteria
  Original Goal: "Make it work."
  Missing: How to know if it works
  Question: "How will I know if it's working correctly?
             (e.g., button should be clickable, error should disappear)"

Pattern 5: Constraints
  Original Goal: "Get me set up."
  Missing: Constraints or preferences
  Question: "Are there any constraints or preferences?
             (e.g., use this library, don't modify this file)"

Question Validation (Soul Integration):

Before sending clarification questions to user, validate with Soul:

```python
clarification_request = {
    "original_goal": "help me",
    "ambiguity_reason": "goal_understanding too low",
    "questions": [
        {
            "question": "What action do you want?",
            "pattern": "action_identification",
            "required": True,
        },
        {
            "question": "What context should I use?",
            "pattern": "context_identification",
            "required": False,
        }
    ],
}

soul.validate_clarification(clarification_request) → {
    "valid": True,
    "approved_questions": [0, 1],
    "feedback": "Both questions are appropriate.",
}
```

Response Processing:

User provides clarification:
```python
clarification_response = {
    "request_id": "clarification_123",
    "answers": [
        {"question_index": 0, "answer": "click the submit button"},
        {"question_index": 1, "answer": "button is in the bottom right"},
    ],
}
```

Updated goal becomes:
```
Original: "Help me get this done."
Updated: "Click the submit button that is in the bottom right."
```

Re-evaluate confidence with updated goal (usually increases).

Isolation & Safety:
  ✓ Clarification is pre-execution (no tool risk)
  ✓ Questions are validated by Soul before sending
  ✓ Questions timeout after 300 seconds
  ✓ No automatic retry (user must explicitly provide clarification)
  ✓ All clarifications are stored in conversation history

================================================================================
6. PRE-VALIDATION FOR FAILURE-INJECTED SCENARIOS
================================================================================

Purpose: Detect impossible or risky goals before attempting reasoning,
reducing wasted computation and clearer error messages.

Problem Statement (From Synthetic Observation):
  • 139 failure-injected scenarios executed
  • 22% had confidence 0.0 (rejected early)
  • 78% had confidence 0.70 (attempted before failing)
  • Goal: Improve early detection to >80% pre-validation catch rate

Pre-Validation Checks:

Check 1: Required Tool Availability
  Description: Verify all required tools exist and are accessible
  Pattern: If goal mentions "tool_X", check if tool_X is registered
  Example Goal: "Use the ImageEditor tool to crop this image"
  Detection: Extract tool names from goal, check availability
  Action on Failure:
    • confidence -= 0.3 (tool missing is major risk)
    • Generate error: "Tool 'ImageEditor' is not available"

Check 2: Element Existence (Frontend Goals)
  Description: For UI goals, verify target elements can be found
  Pattern: "click the button", "find the text input"
  Detection: Parse goal for UI element names, check UI schema
  Action on Failure:
    • confidence -= 0.2 (element missing)
    • Generate suggestion: "Button not found; did you mean 'Submit'?"

Check 3: Context Availability
  Description: Verify required context is available (code, data, etc.)
  Pattern: "Refactor this function", "Analyze this dataset"
  Detection: Check if context is in goal or prior history
  Action on Failure:
    • confidence -= 0.2 (context missing)
    • Generate clarification: "Please provide the code you want refactored"

Check 4: Contradiction Detection
  Description: Detect contradictory goals
  Pattern: "Click button X and do NOT click button Y" (conflicting)
  Detection: Parse goal for logical contradictions
  Action on Failure:
    • confidence -= 0.3 (contradiction)
    • Generate error: "Goal contains contradictory instructions"

Check 5: Scope Validation
  Description: Verify goal is within system scope
  Pattern: "Launch a rocket" (not a software task)
  Detection: Check goal against system capabilities
  Action on Failure:
    • confidence -= 0.4 (out of scope)
    • Generate suggestion: "This task is outside my capabilities"

Check 6: Complexity Warning
  Description: Flag overly complex goals that may fail
  Pattern: Multi-step with 5+ tools required
  Detection: Count required tools and steps
  Action on Warning:
    • confidence -= 0.1 (complexity concern)
    • Generate message: "This is complex; may need approval"

Pre-Validation Response:

If any check fails significantly (confidence drops to <0.55):
```python
{
    "validation_status": "pre_validation_failed",
    "checks_passed": 4,
    "checks_failed": 2,
    "failures": [
        {
            "check": "required_tool_availability",
            "severity": "high",
            "message": "Tool 'Compiler' is not available",
            "confidence_delta": -0.3,
        },
        {
            "check": "context_availability",
            "severity": "medium",
            "message": "Code context not provided",
            "confidence_delta": -0.2,
        }
    ],
    "final_confidence": 0.25,
    "recommendation": "clarify_or_provide_context",
    "suggested_questions": [
        "Can you provide the code you want to compile?",
        "Do you want to use a different compiler/tool?",
    ],
}
```

Expected Improvement:
  • Before Pre-Validation: 78% of failure-injected reach 0.70 confidence
  • After Pre-Validation: ~85%+ caught at pre-validation (confidence <0.55)
  • Benefit: Clearer error messages, faster feedback, reduced wasted reasoning

Implementation Strategy:
  1. Add validate_goal() function to /reasoning/execute
  2. Run before agent reasoning (early exit if severe failures)
  3. Confidence reduced based on check failures
  4. Return pre_validation_failed state (with clarification options)
  5. User can provide context and retry

Isolation & Safety:
  ✓ Pre-validation is read-only (no side effects)
  ✓ Runs before reasoning (fast, cheap to fail)
  ✓ All failures generate clarification suggestions
  ✓ No tool execution after pre-validation failure
  ✓ Confidence is automatically adjusted

================================================================================
7. INTEGRATION POINTS & DATA FLOW
================================================================================

Architecture: Five Distinct Systems Integrated at /reasoning/execute

┌──────────────────────────────────────────────────────────────────┐
│                        /reasoning/execute                         │
│                      (Orchestration Point)                        │
│                                                                   │
│  INPUT: {goal, session_id, context, approval_required}           │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ SYSTEM 1: Pre-Validation (NEW)                              │ │
│  │  • Check tool availability                                  │ │
│  │  • Check element existence                                  │ │
│  │  • Check context availability                               │ │
│  │  • Detect contradictions                                    │ │
│  │  → Output: validation_status, confidence_adjustments        │ │
│  │ ┌─── If validation FAILS (confidence < 0.55) ───────┐      │ │
│  │ │ → Return "pre_validation_failed" state             │      │ │
│  │ │ → Send clarification questions to Soul             │      │ │
│  │ │ → END (don't proceed to reasoning)                 │      │ │
│  │ └────────────────────────────────────────────────────┘      │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                         ↓                                         │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ SYSTEM 2: Agent Reasoning (EXISTING - Phase 1)              │ │
│  │  • Parse goal                                               │ │
│  │  • Select tools                                             │ │
│  │  • Generate reasoning                                       │ │
│  │  • Calculate graded confidence (NEW - Phase 2)              │ │
│  │  → Output: reasoning_summary, tools_proposed, confidence    │ │
│  │ ┌─── If ambiguous (confidence < 0.55) ───────┐             │ │
│  │ │ → Generate clarification questions          │             │ │
│  │ │ → Ask Soul to validate questions            │             │ │
│  │ │ → Return "clarification_needed" state       │             │ │
│  │ └────────────────────────────────────────────┘             │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                         ↓                                         │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ SYSTEM 3: Approval Gates (NEW - Phase 2)                    │ │
│  │  Decide: Execute now, request approval, or reject?          │ │
│  │  ┌─── IF confidence >= 0.85 ───────────────────┐            │ │
│  │  │ → Execute tools immediately (HIGH_CONFIDENCE) │           │ │
│  │  │ → No approval needed                         │           │ │
│  │  └─────────────────────────────────────────────┘            │ │
│  │  ┌─── IF 0.55 <= confidence < 0.85 ──────────┐              │ │
│  │  │ → Generate approval request                │              │ │
│  │  │ → Send to Soul system (callback)           │              │ │
│  │  │ → Return "awaiting_approval" state         │              │ │
│  │  │ → Tool execution BLOCKED                   │              │ │
│  │  └────────────────────────────────────────────┘              │ │
│  │  ┌─── IF confidence < 0.55 ───────────────────┐              │ │
│  │  │ → Return suggestion (no execution)          │              │ │
│  │  │ → No approval requested                    │              │ │
│  │  │ → Return "low_confidence" state            │              │ │
│  │  └────────────────────────────────────────────┘              │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                         ↓                                         │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ SYSTEM 4: Tool Execution (MODIFIED - Phase 2)               │ │
│  │  Only executes if: (confidence >= 0.85) OR (approval_granted) │
│  │  • Execute tools in order                                   │ │
│  │  • Collect results                                          │ │
│  │  • Store in tool_results array                              │ │
│  │  → Output: tool_results, success flag                       │ │
│  │ ┌─── Safety Invariant ──────────────────────────────────┐   │ │
│  │ │ Tool execution REQUIRES one of:                       │   │ │
│  │ │   (A) confidence >= 0.85, OR                         │   │ │
│  │ │   (B) approval_granted = True                        │   │ │
│  │ │ If neither → Do not execute, return suggestion       │   │ │
│  │ └───────────────────────────────────────────────────────┘   │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                         ↓                                         │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ SYSTEM 5: Soul Integration (NEW - Phase 2)                  │ │
│  │  • Callbacks: approval validation, clarification validation │ │
│  │  • Storage: approval decisions, conversation history        │ │
│  │  • Retrieval: context, prior goals, user preferences        │ │
│  │  → Output: approval decision, context, feedback             │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                         ↓                                         │
│  OUTPUT: {                                                       │
│    success: bool,          # Did tool execution succeed?        │
│    result: {               # Reasoning and results               │
│      reasoning_summary,                                         │
│      tool_results,                                              │
│      tools_used,                                                │
│      understanding,                                             │
│      confidence,            # NEW: Graded 0.0-1.0              │
│    },                                                           │
│    approval_state: "none" | "awaiting_approval" | "approved",   │
│    soul_request_id: "uuid or null",                             │
│    execution_path: "high_confidence" | "approved" | "suggested" │
│  }                                                              │
└──────────────────────────────────────────────────────────────────┘

Data Flow Diagram:

User Goal
   │
   ├─→ [Pre-Validation] → Fails? → [Return: pre_validation_failed]
   │                         │
   │                         └─→ [Clarification Questions]
   │                                   │
   │                                   └─→ Soul System
   │
   └─→ [Agent Reasoning] → Confidence calc
                                  │
                                  ├─→ If < 0.55: [Return: low_confidence]
                                  │
                                  └─→ If >= 0.55: [Approval Gates]
                                         │
                                         ├─→ If >= 0.85: [Execute Tools] → [Return: success/failure]
                                         │
                                         └─→ If 0.55-0.85: [Request Approval]
                                                │
                                                └─→ Soul System
                                                      │
                                                      ├─→ Approved? → [Execute Tools] → [Return: success/failure]
                                                      │
                                                      └─→ Denied/Timeout? → [Return: approval_denied]

Integration Points Summary:

1. Pre-Validation → Confidence Adjustment
   • Failures reduce confidence
   • High failures trigger early return

2. Agent Reasoning → Approval Gates
   • Confidence output determines gate logic
   • Tool list determines approval request content

3. Approval Gates → Soul System
   • Generate approval request
   • Send via callback (non-blocking)
   • Wait for decision (async)

4. Approval Decision → Tool Execution
   • approval_granted=True enables execution
   • Tracks approval_state for response

5. Tool Execution → Response
   • Tool results are collected
   • success flag reflects execution outcome
   • execution_path tracks decision path

Phase 1 → Phase 2 Changes Summary:

Phase 1 Components Retained:
  ✓ /reasoning/execute endpoint structure
  ✓ agent_reasoning logic and tool selection
  ✓ tool_results collection
  ✓ HTTP 200 responses
  ✓ response schema (extended with new fields)

Phase 2 New Components:
  ✓ Pre-validation system (6 checks)
  ✓ Graded confidence (0.0-1.0 continuous)
  ✓ Approval gates (3 paths: execute, request, clarify)
  ✓ Clarification handling (question generation + validation)
  ✓ Soul integration (callbacks, storage, retrieval)

No Breaking Changes:
  ✓ Existing callers still get HTTP 200 responses
  ✓ New fields added (not required for backward compatibility)
  ✓ Old confidence values still available (as part of calculation)
  ✓ Tool execution still works (just with additional gates)

================================================================================
8. ISOLATION & SAFETY CONSTRAINTS
================================================================================

Constraint 1: Gradual Activation
  • Phase 2 systems must be independently toggleable
  • Can disable approval gates without breaking pre-validation
  • Can disable pre-validation without breaking reasoning
  • Feature flags: pre_validation_enabled, approval_gates_enabled, clarification_enabled

Constraint 2: Asymmetric Fallback
  • If Soul system is unavailable: approval requests time out, no execution
  • If pre-validation fails: return immediately, no reasoning
  • If approval gates are unavailable: execute on high confidence, request on medium
  • Never fall back to "just execute" without approval if gates are expected

Constraint 3: No Autonomy Escalation
  • Approval gates do NOT change autonomy level of tool execution
  • If execution is approved: still Level 2 (requires approval), not Level 3+
  • Phase 2 does not introduce autonomous execution
  • User approval is explicit pre-requisite for execution

Constraint 4: Schema Invariants (Phase 1 Preserved)
  • All responses must include: success, result, tool_results, tools_used, confidence
  • confidence must be float in [0.0, 1.0]
  • tool_results and tools_used must have matching lengths
  • No partial responses or truncated results

Constraint 5: No Tool State Contamination
  • Tools should not be executed for validation purposes
  • Pre-validation checks do not invoke tools
  • Clarification does not invoke tools
  • Only "Execute Tools" phase invokes tools
  • Failed validation ≠ tool failure

Constraint 6: Audit Trail
  • All approval decisions must be stored in Soul
  • All clarification questions and answers must be logged
  • All pre-validation checks must be recorded
  • Enable post-hoc analysis and user transparency

Constraint 7: User Agency
  • Approval decisions cannot be overridden by system
  • Clarification can be skipped by user (retry with same goal)
  • Approval timeout does not auto-approve or auto-deny
  • Users always have explicit control

Implementation Checkpoints:

Before Phase 2 Launch:
  ☐ All new systems are feature-flagged and can be disabled
  ☐ No breaking changes to existing /reasoning/execute callers
  ☐ Soul integration is properly documented (contract/interface)
  ☐ Approval gates have clear decision logic (no ambiguity)
  ☐ Confidence calculation is deterministic and reproducible
  ☐ Pre-validation checks do not invoke tools
  ☐ Clarification questions are validated by Soul
  ☐ All audit trails are persistent and queryable

================================================================================
9. TESTING & ROLLOUT STRATEGY
================================================================================

Phase 2 Testing Approach:

Stage 1: Unit Testing (Per System)
  • Test pre-validation checks independently
  • Test confidence calculation with sample goals
  • Test approval gates logic (high/medium/low paths)
  • Test clarification question generation
  • Expected: 100% code coverage per system

Stage 2: Integration Testing (System Combinations)
  • Test pre-validation → reasoning flow
  • Test reasoning → approval gates flow
  • Test approval gates → execution flow
  • Test Soul integration (callbacks, storage)
  • Expected: All integration paths covered

Stage 3: End-to-End Testing (Synthetic Harness v2)
  • Create Phase 2 synthetic harness
  • Use same 500 synthetic scenarios from Phase 1
  • Add assertions for approval gates and graded confidence
  • Measure: confidence distribution, approval request rate, execution rate
  • Expected: >80% pre-validation catch, confidence range 0.0-1.0

Stage 4: Regression Testing (Phase 1 Comparison)
  • Run 500 synthetic scenarios with Phase 2
  • Compare results to Phase 1 synthetic observation
  • Verify no regressions in tool selection accuracy
  • Verify all phase 1 schema invariants still hold
  • Expected: Same tool accuracy, new confidence distribution

Stage 5: User Acceptance Testing (Controlled Rollout)
  • Enable Phase 2 for subset of users (5%)
  • Monitor approval request rate, timeout rate, execution rate
  • Collect feedback on clarification questions
  • Verify Soul integration is responsive
  • Expected: <5% approval request timeout, >90% user satisfaction

Rollout Stages:

Stage A: Internal Testing (This Team)
  • Deploy to staging environment
  • Run full test suite (unit → integration → synthetic)
  • Verify all safety constraints
  • Timeline: 1-2 weeks

Stage B: Beta Testing (Early Users)
  • Deploy to 5% of production users
  • Monitor metrics: approval requests, timeouts, execution rate
  • Collect feedback: UX, clarity, performance
  • Timeline: 1-2 weeks

Stage C: Full Rollout
  • Deploy to 100% of users
  • Keep Phase 1 fallback active (can disable Phase 2 if issues)
  • Monitor metrics: engagement, approval rate, success rate
  • Timeline: 1 week

Rollback Procedure:
  • If approval timeout > 10%: disable approval gates, keep pre-validation
  • If pre-validation too aggressive: disable pre-validation, keep gates
  • If Soul callbacks slow: increase timeout, add caching
  • If confidence too low: tune weights in calculation
  • Full rollback: disable all Phase 2, revert to Phase 1

Testing Metrics:

Pre-Validation Effectiveness:
  • Target: >80% failure-injected goals caught at pre-validation
  • Measurement: early_exit_count / failure_injected_count
  • Phase 1 baseline: 22% (139 failure-injected runs)
  • Phase 2 target: 85% (expected 118 of 139 caught early)

Confidence Distribution:
  • Target: Full range 0.0-1.0, not bimodal
  • Measurement: std_dev(confidence) > 0.2
  • Phase 1 baseline: 0.26 std dev (bimodal)
  • Phase 2 target: 0.35+ std dev (continuous distribution)

Approval Request Rate:
  • Target: 15-25% of goals require approval (0.55-0.85 confidence)
  • Measurement: approval_requests / total_goals
  • Acceptable range: 10-30% (too low = gates too loose, too high = too strict)

Approval Timeout Rate:
  • Target: <5% of approval requests timeout
  • Measurement: timeout_count / approval_request_count
  • If > 10%: increase timeout from 300s to 600s

Soul Integration Latency:
  • Target: <100ms for approval validation callback
  • Measurement: avg_callback_latency
  • If > 200ms: implement caching or async batching

Clarification Question Quality:
  • Target: >80% of users find clarifications helpful
  • Measurement: user_feedback_score
  • Metric: "Did clarifications help you provide better context?"

Tool Selection Accuracy (Regression Test):
  • Target: 0% mis-selection (same as Phase 1)
  • Measurement: tool_results/tools_used mismatch count
  • Phase 1 baseline: 0 mismatches in 500 runs
  • Phase 2 target: 0 mismatches (no regression)

================================================================================
10. IMPLEMENTATION ROADMAP
================================================================================

Timeline: 4-6 weeks (design → test → rollout)

Week 1: Foundation
  ☐ Create graded confidence system module
  ☐ Create pre-validation system module
  ☐ Create approval gates module
  ☐ Stub Soul integration (mock responses)
  ☐ Unit tests for all three modules
  ☐ Feature flags for enable/disable

Week 2: Integration
  ☐ Integrate pre-validation into /reasoning/execute
  ☐ Integrate approval gates into /reasoning/execute
  ☐ Integrate Soul callbacks (non-blocking)
  ☐ Modify response schema to include new fields
  ☐ Integration tests (pre-val → reasoning → gates → execution)
  ☐ Update API documentation

Week 3: Clarification
  ☐ Create clarification question generation module
  ☐ Integrate clarification into reasoning path
  ☐ Implement Soul validation for clarifications
  ☐ Handle clarification responses and re-evaluation
  ☐ Unit and integration tests
  ☐ Test all clarification patterns

Week 4: Testing
  ☐ Create synthetic harness v2 (Phase 2 specific tests)
  ☐ Run 500 synthetic scenarios from Phase 1
  ☐ Compare results: confidence distribution, pre-val catch rate
  ☐ Regression testing (tool selection accuracy)
  ☐ Performance testing (latency, throughput)
  ☐ Load testing (100+ concurrent requests)

Week 5: Refinement
  ☐ Tune confidence weights based on testing
  ☐ Adjust approval gate thresholds (0.85, 0.55)
  ☐ Adjust Soul timeout (300s vs 600s)
  ☐ Optimize Soul integration (batching, caching)
  ☐ User feedback integration
  ☐ Documentation finalization

Week 6: Rollout
  ☐ Internal testing (team validation)
  ☐ Beta rollout (5% of users)
  ☐ Monitor metrics (approval rate, timeout rate)
  ☐ Full rollout (100% of users)
  ☐ Metrics dashboard setup
  ☐ Rollback procedure ready-to-execute

Approval Gates Before Implementation:

Design Review (This Document):
  ☐ Approval: Architecture correct and safe?
  ☐ Approval: Integration points clear?
  ☐ Approval: Safety constraints satisfied?
  ☐ Approval: Testing strategy adequate?
  ☐ Approval: Rollout plan realistic?

Risk Assessment:
  ☐ Risk: Soul system not responsive → Mitigation: timeout + fallback
  ☐ Risk: Confidence too low → Mitigation: tunable weights
  ☐ Risk: Too many approval requests → Mitigation: gate thresholds
  ☐ Risk: Regression in tool selection → Mitigation: regression tests
  ☐ Risk: Breaking changes to API → Mitigation: backward compatibility

Go/No-Go Criteria for Implementation:
  ✓ Design review approved
  ✓ No blockers or critical risks
  ✓ All integration points documented
  ✓ Testing strategy ready
  ✓ Rollback procedure validated
  ✓ Safety constraints verified

================================================================================
APPENDIX: PHASE 2 GLOSSARY
================================================================================

Approval Gate: Decision point that determines if tools will be executed
based on confidence level and user approval.

Approval Request: Structured message sent to Soul system asking user to
approve execution of a goal.

Approval State: Current status of approval workflow (none, awaiting_approval,
approved, denied, timeout).

Clarity Signal: Indicator that goal understanding is high (e.g., action verb,
target specified).

Clarification: Process of asking user questions to resolve ambiguity and
provide missing context.

Confidence (Graded): Continuous score (0.0-1.0) representing agent's belief
that it can successfully complete a goal.

Confidence Factor: One of the four components used to calculate graded
confidence (goal_understanding, tool_availability, context_richness,
tool_confidence).

Execution Path: Route taken through approval gates (high_confidence,
approved, suggested).

Failure-Injected: Synthetic goal that requires non-existent tools or
missing context, designed to fail.

Goal Understanding: Clarity of user intent and what specific action is
desired (0.0-1.0 factor).

Pre-Validation: Early checks performed on goal before reasoning to detect
impossible tasks.

Pre-Validation Failed: Goal does not pass pre-validation checks and should
be clarified before proceeding.

Schema Invariant: Guaranteed property of API response (e.g., confidence
must be float in [0, 1]).

Soul System: User-facing approval and memory system that validates requests,
tracks decisions, and maintains context.

Tool Availability: Whether required tools exist and are accessible
(0.0-1.0 factor).

Tool Confidence: Whether selected tools are deterministic and safe
(0.0-1.0 factor).

================================================================================
PHASE 2 DESIGN COMPLETE
================================================================================

Status: Ready for Review and Approval

Next Steps:
  1. Review this design document
  2. Identify concerns or improvements
  3. Approve or request revisions
  4. Upon approval, proceed with implementation roadmap (Week 1-6)

Document Version: 1.0
Date: February 5, 2026
Classification: Internal Design (not production code)
