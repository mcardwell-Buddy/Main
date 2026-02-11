# Whiteboard → Chat Context Handoff System

## Overview

The context handoff system enables intelligent, semantic communication between the Whiteboard and Chat interfaces. When users click "Discuss with Buddy," the system:

1. **Captures context** from the Whiteboard event (rollback, approval, alert, etc.)
2. **Packages it structurally** with metadata about the event type and details
3. **Transmits invisibly** to Chat via localStorage
4. **Buddy auto-responds** with intelligent analysis based on context
5. **No user prompting required** — Buddy already knows what you're talking about

---

## Architecture

### 1. Context Payload Structure

Every whiteboard event generates a structured payload with this format:

```javascript
{
  source: "whiteboard",              // Always "whiteboard"
  event_type: "rollback|approval|alert|learning|execution|opportunity",
  timestamp: "2026-02-06T...",
  summary: "Human-readable 1-line summary",
  context: {
    // Event-specific structured data
    tool: "scraper",
    reason: "Execution failed",
    from_state: "state_1",
    to_state: "state_2",
    // ... more fields depending on event type
  },
  expected_responses: [
    "Explain why the rollback happened",
    "Show me what failed",
    // ... user-friendly follow-up options
  ],
  buddy_prompt: "System instruction for Buddy to generate contextual response"
}
```

### 2. Event Types

#### **Rollback** (`event_type: 'rollback'`)
Triggered when system auto-recovers from failed execution.

**Context Fields:**
- `tool`: Tool that failed
- `reason`: Why it failed
- `from_state`: Failed state
- `to_state`: Recovered state
- `execution_id`: ID of failed execution

**Buddy's Response:** Explains the failure, summarizes the rollback, asks if user wants to retry/investigate/move on.

#### **Approval** (`event_type: 'approval'`)
Triggered when user clicks "Discuss with Buddy" on a hustle candidate.

**Context Fields:**
- `name`: Hustle name
- `description`: Opportunity description
- `risk_level`: low/medium/high
- `estimated_upside`: Revenue potential ($)
- `status`: pending/approved/rejected

**Buddy's Response:** Summarizes the opportunity, highlights key metrics, asks if user wants to approve/reject/analyze further.

#### **Alert** (`event_type: 'alert'`)
Triggered when discussing system alerts or conflicts.

**Context Fields:**
- `title`: Alert title
- `description`: Alert details
- `severity`: Critical/warning/info
- `type`: conflict/rollback/etc.

**Buddy's Response:** Explains the alert's impact, asks if user wants to resolve now or investigate first.

#### **Learning** (`event_type: 'learning'`)
Triggered when confidence changes or learning signals appear.

**Context Fields:**
- `signal_type`: Pattern type detected
- `confidence_score`: 0.0 to 1.0
- `context`: Why confidence changed
- `related_tool`: Tool that triggered signal

**Buddy's Response:** Explains the signal, asks if strategy should adjust based on new confidence level.

#### **Execution** (`event_type: 'execution'`)
Triggered when discussing individual tool executions.

**Context Fields:**
- `tool_name`: What tool executed
- `status`: success/failure/partial
- `duration_ms`: Time taken
- `output`: Execution results

**Buddy's Response:** Summarizes execution, highlights any issues, asks if user wants to review details/retry.

#### **Opportunity** (`event_type: 'opportunity'`)
Triggered when discussing approved income opportunities.

**Context Fields:**
- `name`: Opportunity name
- `potential_revenue`: Estimated revenue ($)
- `automated_tasks`: Number of automated tasks
- `next_actions`: List of recommended next steps

**Buddy's Response:** Reminds user of the opportunity potential, confirms readiness to execute, asks what user wants to do next.

---

## How It Works (Step-by-Step)

### User Clicks "Discuss with Buddy"

```
Whiteboard.js (handleDiscuss function)
↓
1. Event data (rollback, approval, etc.) received
2. generateXxxContext() creates structured payload
3. Payload serialized to JSON
4. Stored in localStorage['whiteboard_context']
5. navigate('/') → moves to Chat
```

### Chat Receives Context

```
UnifiedChat.js (useEffect on activeSessionId)
↓
1. Checks localStorage for 'whiteboard_context'
2. If found:
   a. Parse JSON payload
   b. Verify source === 'whiteboard'
   c. Pass to generateBuddyResponse(context)
   d. Get intelligent response back
   e. addMessage(response, 'agent') → display as Buddy message
   f. Clear localStorage
3. If not found: normal chat mode
```

### Buddy's Auto-Response

```
whiteboardContextGenerator.js (generateBuddyResponse function)
↓
1. Switch on event_type
2. Generate appropriate response based on context data
3. Format with bold summary, key metrics, user-friendly question
4. Return markdown-formatted message
5. Chat displays as agent message (not user input)
```

---

## Code Examples

### Example 1: Approval Alert → Chat

**Whiteboard:**
```javascript
const alert = {
  id: 'hustle-123',
  title: 'GHL Automation',
  riskLevel: 'medium',
  estimatedUpside: 50000,
  status: 'pending',
  context: 'Automate GHL email follow-ups'
};

onClick={() => handleDiscuss(generateApprovalContext(alert))}
```

**Generated Payload:**
```json
{
  "source": "whiteboard",
  "event_type": "approval",
  "summary": "New hustle candidate: \"GHL Automation\" — medium risk, $50,000 upside",
  "context": {
    "name": "GHL Automation",
    "risk_level": "medium",
    "estimated_upside": 50000,
    "description": "Automate GHL email follow-ups"
  },
  "buddy_prompt": "A new hustle candidate is pending approval..."
}
```

**Buddy's Auto-Response:**
```
I see a new hustle has been flagged for approval. **New hustle candidate: 
"GHL Automation" — medium risk, $50,000 upside**

**Key details:**
• Risk Level: medium
• Estimated Upside: $50,000
• Status: pending
• Description: Automate GHL email follow-ups

**Next step:** Do you want to approve this, request more analysis, or reject it?
```

---

### Example 2: Rollback → Chat

**Whiteboard:**
```javascript
const rollback = {
  id: 'rollback-456',
  tool_name: 'scraper',
  failed_state: 'parsing_html',
  recovered_state: 'idle',
  reason: 'Invalid HTML selector'
};

onClick={() => handleDiscuss(generateRollbackContext(rollback))}
```

**Generated Payload:**
```json
{
  "source": "whiteboard",
  "event_type": "rollback",
  "summary": "System rolled back scraper from parsing_html to idle",
  "context": {
    "tool": "scraper",
    "from_state": "parsing_html",
    "to_state": "idle",
    "reason": "Invalid HTML selector"
  }
}
```

**Buddy's Auto-Response:**
```
I see that the system rolled back an execution. **System rolled back 
scraper from parsing_html to idle**

This suggests the scraper tool encountered an issue in the parsing_html 
state. Rolling back to idle keeps the system stable.

**What would you like to do?**
1. Investigate what caused the failure
2. Retry the execution with different parameters
3. Review the tool's recent history
4. Move on to the next task
```

---

## Testing Scenarios

### ✅ Test 1: Approval Alert Flow

1. Navigate to Whiteboard (`http://localhost:3000/whiteboard`)
2. Open Interactions section
3. Find a hustle candidate in "Approval Queue"
4. Click "Discuss with Buddy"
5. **Expected:** Redirected to Chat with Buddy message about the hustle (no user message)
6. **Verify:** Buddy mentions the hustle name, risk level, upside
7. **Verify:** Buddy asks approval/rejection decision

### ✅ Test 2: Rollback Alert Flow

1. In Whiteboard, open Operations section
2. Click on a recent rollback event
3. Click "Discuss with Buddy"
4. **Expected:** Redirected to Chat with contextual Buddy response
5. **Verify:** Buddy explains what tool rolled back and why
6. **Verify:** Buddy offers concrete next steps (retry, investigate, move on)

### ✅ Test 3: System Alert Flow

1. In Whiteboard Interactions, click on a system alert
2. Click "Discuss with Buddy"
3. **Expected:** Redirected to Chat with Buddy message
4. **Verify:** Buddy explains the alert impact and severity
5. **Verify:** Buddy asks if user wants to fix now or investigate

### ✅ Test 4: Confidence Change Flow

1. In Learning section, click on a learning signal
2. Click "Discuss with Buddy"
3. **Expected:** Redirected to Chat with contextual response
4. **Verify:** Buddy explains why confidence changed
5. **Verify:** Buddy asks if strategy should adjust

### ✅ Test 5: Context Persistence

1. Click "Discuss with Buddy" from any Whiteboard event
2. Chat should display Buddy's auto-generated response
3. **Verify:** No user message appears (context is invisible)
4. **Verify:** Buddy's response is relevant to the specific event
5. **Verify:** User can continue natural conversation after

### ✅ Test 6: No Manual Prompting

1. Click "Discuss with Buddy" from Whiteboard
2. **Expected:** Buddy responds immediately, without user typing anything
3. **Verify:** No placeholder waiting for user input
4. **Verify:** User can type follow-up or approve/reject directly
5. **Verify:** Conversation flows naturally

---

## Error Handling

### Scenario: Malformed Context

If localStorage contains invalid JSON:
- `catch` block prevents crash
- Error logged to console
- Chat loads normally in standard mode
- User can chat naturally

### Scenario: Wrong Event Source

If `source !== 'whiteboard'`:
- Context ignored
- Chat loads in standard mode
- User can continue normally

### Scenario: Missing Context Data

If context lacks required fields:
- `generateBuddyResponse()` returns generic response: "I've pulled up some context from the Whiteboard..."
- User can ask clarifying questions
- No errors or crashes

---

## Benefits

✅ **Buddy Already Knows Context** — No need to re-explain the rollback/approval/alert  
✅ **Invisible to User** — Context doesn't clutter chat UI  
✅ **Auto-Intelligent** — Buddy tailors response to event type  
✅ **Structured Data** — Future AI/ML can use event_type for analytics  
✅ **Extensible** — Easy to add new event types (deployment, conflict, etc.)  
✅ **Zero Manual Work** — No user prompting needed  
✅ **Natural Conversation** — Users feel like Buddy is truly integrated  

---

## Future Enhancements

### 1. Rich Context Display

Show context cards inline in chat (sidebar badges showing linked Whiteboard item):
- "Linked to: GHL Automation (Approval Pending)"
- Clickable → returns to Whiteboard at that item

### 2. Multi-Event Bundles

Bundle multiple related events in one context:
```json
{
  "event_type": "bundled",
  "events": [
    { "type": "rollback", "data": {...} },
    { "type": "alert", "data": {...} },
    { "type": "approval", "data": {...} }
  ]
}
```

### 3. Context History

Track which events were discussed in chat:
- Prevent duplicate discussions
- Build conversation timeline
- Show "previously discussed" badges

### 4. Bidirectional Links

When discussing approval in chat, create backlink to Whiteboard:
- Show in chat: "Linked to GHL Automation in Whiteboard"
- Click → opens Whiteboard side-by-side

### 5. Event Filtering

Allow users to filter chat by source:
- Show only "whiteboard-sourced" messages
- Hide standard chat, show only system discussions

---

## Architecture Diagram

```
                        WHITEBOARD SIDE
                        ================
    
    User clicks           Context Generator
    "Discuss"    ←→    whiteboardContextGenerator.js
                            ↓
                    Structured Payload
                    {source, event_type, context, ...}
                            ↓
                    JSON Serialized
                            ↓
                    localStorage['whiteboard_context']
                            ↓
                    navigate('/') → Chat
                    
                    
                        CHAT SIDE
                        =========
                    
                    useEffect on activeSessionId
                            ↓
                    Check localStorage
                            ↓
                    Parse JSON payload
                            ↓
                    generateBuddyResponse(context)
                            ↓
                    addMessage(response, 'agent')
                            ↓
                    Display in Chat UI
                            ↓
                    Clear localStorage
```

---

## Files Modified

- **`whiteboardContextGenerator.js`** — NEW — Context payload generation & Buddy response generation
- **`BuddyWhiteboard.js`** — Updated `handleDiscuss()` to inject structured context
- **`UnifiedChat.js`** — Updated whiteboard intake useEffect to process structured context

---

## Summary

This system transforms context handoff from "here's a random message" to "here's structured context with event metadata and Buddy's intelligent response." Users experience a seamless, context-aware conversation where Buddy already understands what they're discussing before they type.

The key insight: **Context should be invisible, but Buddy's response should be obviously intelligent.**
