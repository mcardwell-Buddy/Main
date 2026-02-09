# Phase 3B: Quick Reference Guide

## What Changed?

**Before Phase 3B**: Generic messages
```
"I'm missing some required details. Can you provide more information?"
"What would you like me to help with?"
```

**After Phase 3B**: Targeted messages
```
"I know what to extract, but where? Should I use:
• linkedin.com
• A different website?"

"I can do that — what exactly would you like me to extract?
For example:
• Extract titles
• Extract emails
• Extract services"
```

---

## 8 Clarification Types

When Buddy can't act, it uses one of these 8 message types:

### 1. MISSING_OBJECT
**When**: User specifies action + source, but not what to extract/search-for

**Example**: "Extract from linkedin.com"
```
I can do that — what exactly would you like me to extract?

For example:
• Extract titles
• Extract emails
• Extract services
```

### 2. MISSING_TARGET
**When**: User specifies action + object, but source URL ambiguous or missing

**Example**: "Extract the emails" (with prior context linkedin.com)
```
I know what to extract, but where? Should I use:
• linkedin.com
• A different website?
```

### 3. MISSING_TARGET_NO_CONTEXT
**When**: User specifies action + object, no prior context

**Example**: "Extract the emails"
```
I know what to extract, but need a website or URL?
```

### 4. AMBIGUOUS_REFERENCE
**When**: User mentions something like "there", "it", "that" without clarity

**Example**: "Extract from there"
```
When you say 'there', what are you referring to?
```

### 5. MULTI_INTENT
**When**: User requests multiple actions in unclear order

**Example**: "Extract from linkedin and then search"
```
Should I:
1) Navigate to linkedin.com
2) Then extract emails?
```

### 6. TOO_VAGUE
**When**: User uses vague terms like "stuff", "things", "data"

**Example**: "Search for stuff on google"
```
I need more detail. What kind of information?
For example:
• Search for people
• Search for articles
• Search for datasets
```

### 7. INTENT_AMBIGUOUS
**When**: Core action is unclear (extract vs search vs navigate?)

**Example**: "Get me developers"
```
Search for developers OR extract from a specific site?
```

### 8. CONSTRAINT_UNCLEAR
**When**: User specifies action/source, but how to limit results is unclear

**Example**: "Extract all emails from linkedin"
```
How should I limit results?
• Top 5
• Summary (with counts)
• Full list
```

---

## Code Integration Points

### For Adding New Messages
**File**: `backend/clarification_templates.py`

```python
CLARIFICATION_TEMPLATES = {
    ClarificationType.MY_NEW_TYPE: "New message template with {placeholder}",
    # ...
}
```

### For Detecting New Patterns
**File**: `backend/action_readiness_engine.py` → `_determine_clarification_type()`

```python
def _determine_clarification_type(self, message_lower, candidate, missing_fields):
    # Add your detection logic here
    if "your condition" in message_lower:
        return ClarificationType.MY_NEW_TYPE
```

### For Using in Tests
**File**: `backend/tests/test_*.py`

```python
# Use orchestrator cache for session persistence
from test_clarification_ux_invariants import get_or_create_orchestrator, clear_orchestrator_cache

def test_my_feature():
    clear_orchestrator_cache()
    orchestrator = get_or_create_orchestrator("session_1")
    response = orchestrator.process_message("user input")
    assert "expected" in response.summary.lower()
```

---

## Testing Pattern (Phase 3B)

All tests follow this pattern:

```python
def test_invariant_X():
    """UX INVARIANT X: [Description]"""
    clear_orchestrator_cache()
    clear_missions_log()
    
    # Send message that should trigger clarification
    response = run_message("incomplete request")
    
    # Verify no mission created
    assert len(response.missions_spawned) == 0
    assert count_missions() == 0
    
    # Verify correct clarification given
    assert "expected phrase" in response.summary.lower()
    assert "forbidden phrase" not in response.summary.lower()
    
    print("✓ Invariant X verified")
```

---

## Regression Checks

Phase 3B has **zero regressions**. All Phase 3A tests still pass:

```bash
# Phase 3A.1: Sole Mission Gate (6 tests)
pytest backend/tests/test_readiness_sole_gate.py -v

# Phase 3A.2: Session Context (10 tests)
pytest backend/tests/test_session_context_safety.py -v

# Phase 3B: Clarification UX (11 tests)
pytest backend/tests/test_clarification_ux_invariants.py -v

# All together
pytest backend/tests/test_*.py -v
# Result: 27/27 PASSED
```

---

## Safety Invariants

These are protected by tests:

1. **Never Vague** - No generic phrases like "provide more details"
2. **Always Actionable** - Every clarification includes examples or context
3. **No Missions** - Clarifications never create missions
4. **READY Unchanged** - Complete inputs still create missions as before
5. **No Auto-Resolve** - Ambiguous refs ask, don't guess

Plus Phase 3A.1+3A.2 invariants:
- Sole mission gate still enforced
- Session context still safe
- Repeat command still works
- No new unsafe paths

---

## Common Patterns

### User gives too little info
```
User: "Extract from linkedin"
Buddy: "I know what to extract, but where? Should I use: • linkedin.com • Different site?"
Message Type: MISSING_TARGET
```

### User gives vague info
```
User: "Search for stuff"
Buddy: "I need more detail. What kind of information?"
Message Type: TOO_VAGUE
```

### User mentions something ambiguous
```
User: "Extract from there"
Buddy: "When you say 'there', what are you referring to?"
Message Type: AMBIGUOUS_REFERENCE
```

### User wants multiple things
```
User: "Navigate and extract"
Buddy: "Should I: 1) Navigate 2) Then extract?"
Message Type: MULTI_INTENT
```

### User is unclear about action
```
User: "Get me developers"
Buddy: "Search for developers OR extract from a specific site?"
Message Type: INTENT_AMBIGUOUS
```

---

## Performance Notes

- All clarification detection happens in ActionReadinessEngine (already called)
- Template rendering is O(1) - simple string replacement
- No additional database queries
- No additional network calls
- Zero performance regression vs Phase 3A

---

## Migration Checklist

- [x] Old generic messages removed
- [x] All 8 new message types implemented
- [x] Template system in place
- [x] Orchestrator integrated
- [x] All tests passing
- [x] Documentation complete
- [x] Zero regressions confirmed

Ready to ship! 🚀
