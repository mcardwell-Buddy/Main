# Phase 3A.2 Quick Reference: Using Session Context

## New Capabilities

Buddy now understands pronouns, supports repeat commands, and remembers context within sessions.

---

## Example Conversation Flow

### 1. Initial Mission with Full Details
```
User: "Extract the email addresses from linkedin.com"
→ Buddy creates mission: extract(emails, linkedin.com)
```

### 2. Follow-up Using Pronoun Reference
```
User: "Extract the phone numbers from there"
→ Buddy resolves "there" to linkedin.com (from prior mission)
→ Creates mission: extract(phone numbers, linkedin.com)
```

### 3. Repeat Command
```
User: "Do it again"
→ Buddy repeats the last mission exactly
→ Creates mission: extract(phone numbers, linkedin.com)
```

### 4. Repeat with Modified Constraint
```
User: "Extract the top 5 emails from linkedin.com"
→ Buddy creates mission: extract(emails, linkedin.com, count=5)

User: "Do it again"
→ Buddy repeats with same fields + constraint
→ Creates mission: extract(emails, linkedin.com, count=5)
```

---

## What Gets Remembered (Session Context)

For each session, Buddy remembers:

1. **Recent URLs** (up to 10)
   - From successful missions
   - Enables "Extract from there" resolution

2. **Recent Action Objects** (up to 10)
   - What was extracted (emails, names, titles, etc.)
   - Enables pronoun resolution ("Extract it from...")

3. **Recent Intents** (up to 10)
   - Type of last mission (extract, navigate, search)
   - Used for repeat commands

4. **Last READY Mission**
   - Full fields: intent, object, target, URL, constraints
   - Used for "Do it again" command

---

## Safety Guarantees

### What Context CANNOT Do

❌ **Cannot invent missing fields**
- "Extract from there" without prior extract mission → INCOMPLETE

❌ **Cannot bypass readiness validation**
- "Navigate somewhere" (no explicit "there") → blocked, even if context has URL

❌ **Cannot create missions on its own**
- Context can only fill gaps, never create missions from nothing

❌ **Cannot resolve ambiguous references**
- "Go there" with 2+ URLs in context → asks for clarification

### What Context CAN Do

✅ **Resolve unambiguous pronouns**
- "Extract from there" with exactly 1 URL → resolved

✅ **Support repeat commands**
- "Do it again" with prior READY mission → creates identical mission

✅ **Fill in constraints**
- "Do it again" preserves count, format, duration, etc.

✅ **Enable follow-ups**
- Can chain missions: extract → extract → navigate → search

---

## Pronoun Keywords Recognized

### For "there" / "here" (source URL)
- "from there"
- "go there"
- "from here"
- "from the same site"

### For "it" / "that" (action object)
- "Extract it"
- "Get that"
- "Extract from it"
- "Do that again"

### For Repeat Commands
- "Do it again"
- "Repeat that"
- "Try again"
- "Repeat"
- "Again"

---

## When Context Resolution Fails (Expected Behavior)

### Scenario 1: No Prior Mission
```
User: "Do it again"
(No prior mission in session context)

Result: INCOMPLETE
Response: "I'm missing some required details before I can do that."
```

### Scenario 2: Ambiguous Reference
```
User: "Extract from example.com"
(Prior missions to linkedin.com AND github.com)

Result: INCOMPLETE
Response: "I'm missing some required details before I can do that."
```

### Scenario 3: Message Doesn't Trigger Pronoun Detection
```
User: "Navigate somewhere"
(Context has URLs, but "somewhere" ≠ pronoun keyword)

Result: INCOMPLETE (missing source_url)
Response: "I'm missing some required details before I can do that."
```

---

## Testing Session Context

### Run All Tests
```bash
cd c:\Users\micha\Buddy
python -m pytest backend/tests/test_session_context_safety.py -v
```

### Run Regression Guard (Phase 3A.1)
```bash
python -m pytest backend/tests/test_action_readiness_engine.py backend/tests/test_action_readiness_gate.py backend/tests/test_readiness_sole_gate.py -v
```

### Run Complete Suite
```bash
python -m pytest backend/tests/test_action_readiness_engine.py backend/tests/test_action_readiness_gate.py backend/tests/test_readiness_sole_gate.py backend/tests/test_session_context_safety.py -v
```

**Expected**: 36/36 PASSED ✅

---

## Implementation Details

### SessionContext Dataclass
```python
from backend.session_context import SessionContext, SessionContextManager

# Create a session context manager
manager = SessionContextManager()

# Get or create context for a session
ctx = manager.get_or_create(session_id="user_session_123")

# Add a READY mission to context
ctx.set_last_ready_mission({
    'intent': 'extract',
    'action_object': 'emails',
    'action_target': 'linkedin.com',
    'source_url': 'https://linkedin.com',
    'constraints': {'count': 5}
})

# Try to resolve "there" to a URL
url = ctx.resolve_source_url()  # Returns URL if exactly 1 in history, else None

# Check if "Do it again" is possible
if ctx.can_repeat_last_mission():
    fields = ctx.get_repeated_mission_fields()
    # Use fields to create new mission with same parameters
```

### ActionReadinessEngine with Context
```python
from backend.action_readiness_engine import ActionReadinessEngine
from backend.session_context import SessionContextManager

engine = ActionReadinessEngine()
manager = SessionContextManager()
ctx = manager.get_or_create(session_id)

result = engine.validate(
    user_message="Extract from there",
    intent="extract",
    context_obj=ctx  # NEW: Pass session context
)

if result.decision == ReadinessDecision.READY:
    # Use result.source_url (may have been resolved from context)
    print(f"Ready to extract from: {result.source_url}")
```

---

## Architecture Diagram

```
┌─ User Message ─────────────────────────────────┐
│                                               │
│   "Extract the emails from there"             │
└─────────────────────┬─────────────────────────┘
                      │
                      ▼
        ┌─────────────────────────┐
        │ Interaction Orchestrator │
        └────────┬────────────────┘
                 │
    ┌────────────┴────────────┐
    ▼                         ▼
[Detect Intent]      [Get Session Context]
intent="extract"     ctx = manager.get_or_create(session_id)
    │                        │
    └────────────┬───────────┘
                 ▼
      ┌──────────────────────────┐
      │ ActionReadinessEngine    │
      │  .validate(...)          │
      │  - Extract fields        │
      │  - Try context resolution│
      │  - Check completeness    │
      └────┬─────────────────────┘
           │
       ┌───┴──────────────────────┐
       │                          │
    READY                      INCOMPLETE
       │                          │
       ▼                          ▼
  Create Mission          Ask for Clarification
  Update Context          No mission created
```

---

## Troubleshooting

### Q: "Do it again" creates mission but with wrong fields
**A**: Confirm the prior mission was READY (not INCOMPLETE). Context only remembers READY missions.

### Q: "Extract from there" still asks for source URL
**A**: Check that session context has at least one URL from a prior mission. If ambiguous (2+ URLs), needs clarification.

### Q: Context resolves URL when I don't want it to
**A**: Avoid pronouns like "there" or "from there". Say the full URL instead: "Extract from github.com".

### Q: Session context persists across sessions
**A**: Normal - SessionContext is per-session. New session_id = fresh context. When orchestrator is destroyed, all context cleared.

---

## Performance Notes

- **Memory**: ~1KB per session (stores ~30 URLs/objects max)
- **Lookup**: O(1) for context retrieval, O(n) for ambiguity check (n ≤ 10)
- **No I/O**: Context is in-memory, no database/disk access

---

**Documentation Version**: 1.0  
**Phase**: 3A.2  
**Last Updated**: 2026-02-08
