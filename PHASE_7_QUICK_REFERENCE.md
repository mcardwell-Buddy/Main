# Phase 7: Quick Reference & Integration Guide

## Files Created

```
backend/
├── capability_boundary.py           (280 lines)
├── delegation_evaluator.py          (320 lines)
├── delegation_signal_emitter.py     (180 lines)
├── delegation_whiteboard_panel.py   (280 lines)
└── test_phase7_delegation.py        (380+ lines)

PHASE_7_COMPLETE.md                 (Comprehensive docs)
PHASE_7_QUICK_REFERENCE.md          (This file)
```

---

## 5-Minute Integration

### Step 1: Import Components

```python
from backend.capability_boundary import CapabilityBoundaryModel, ExecutionClass
from backend.delegation_evaluator import DelegationEvaluator
from backend.delegation_signal_emitter import DelegationSignalEmitter
from backend.delegation_whiteboard_panel import DelegationWhiteboardPanel
```

### Step 2: Create Evaluator

```python
evaluator = DelegationEvaluator()
```

### Step 3: Evaluate Task

```python
decision = evaluator.evaluate("Your task description here")
```

### Step 4: Check Results

```python
print(f"Execution: {decision.execution_class.value}")
print(f"Blocked: {decision.is_blocked}")
print(f"Effort: {decision.estimated_human_effort} minutes")
```

### Step 5: Emit Signal (Optional)

```python
emitter = DelegationSignalEmitter()
signal = emitter.emit_delegation_signal(task_description)
```

### Step 6: Render Panel (Optional)

```python
panel = DelegationWhiteboardPanel()
print(panel.evaluate_and_render(task_description))
```

---

## Classification Quick Lookup

### AI_EXECUTABLE Keywords
```
extract, parse, analyze, process, aggregate, validate, check, 
monitor, log, automate, batch, generate, format, export, import
```

### HUMAN_REQUIRED Keywords
```
approve, review, authorize, contact, sign off, creative, design,
physical, manual, negotiate, communicate, legal, policy
```

### COLLABORATIVE Keywords
```
coordinate, collaborate, handoff, escalate, refine, iterate,
checkpoint, user reviews, reviews and, phased, staged
```

---

## Decision Classes

| Class | Meaning | Blocked? | Human Actions? | Examples |
|-------|---------|----------|-----------------|----------|
| AI_EXECUTABLE | Fully automated | No | No | Extract, parse, validate |
| HUMAN_REQUIRED | Needs human | Often | Yes | Approve, authorize, contact |
| COLLABORATIVE | Both contribute | Maybe | Yes | Review, then execute |

---

## Common Patterns

### Fully Automated (AI_EXECUTABLE)
```
"Extract all records from database"
"Parse JSON and categorize by status"
"Validate email addresses in bulk"
```

### Human Required (HUMAN_REQUIRED)
```
"Review the results and approve"
"Contact the manager and get feedback"
"Sign off on the compliance documentation"
```

### Collaborative (COLLABORATIVE)
```
"Extract records, user reviews and approves"
"Buddy processes data, user validates results"
"AI prepares data, human makes final decision"
```

---

## API Reference

### CapabilityBoundaryModel

```python
model = CapabilityBoundaryModel()

# Classify a task
result = model.classify(task_description: str) -> CapabilityBoundary
# Fields: execution_class, reasoning, confidence, key_indicators

# From dict (mission, goal, etc.)
result = model.classify_from_dict(task_dict: Dict) -> CapabilityBoundary
```

### DelegationEvaluator

```python
evaluator = DelegationEvaluator()

# Evaluate task
decision = evaluator.evaluate(task_description: str) -> DelegationDecision

# From dict
decision = evaluator.evaluate_from_dict(task_dict: Dict) -> DelegationDecision

# Get summary
summary = evaluator.get_handoff_summary(decision) -> str
quick = evaluator.get_quick_summary(decision) -> str
```

### DelegationSignalEmitter

```python
emitter = DelegationSignalEmitter(stream_dir="/path/to/streams")

# Emit signal
signal = emitter.emit_delegation_signal(
    task_description: str,
    mission_id: Optional[str]
) -> DelegationSignal

# From dict
signal = emitter.emit_delegation_signal_from_dict(
    task_dict: Dict,
    mission_id: Optional[str]
) -> DelegationSignal

# Get signals
latest = emitter.get_latest_signal(stream_file: str) -> DelegationSignal
all_signals = emitter.get_signals_from_file(stream_file: str) -> List
```

### DelegationWhiteboardPanel

```python
panel = DelegationWhiteboardPanel()

# Evaluate and render
output = panel.evaluate_and_render(task_description: str) -> str

# Just render (with pre-set decision)
panel.set_delegation_decision(decision: DelegationDecision)
output = panel.render() -> str

# Summaries
quick = panel.render_quick_summary() -> str
full = panel.render_full_summary() -> str
```

---

## Decision Output Structure

```python
DelegationDecision(
    execution_class=ExecutionClass.COLLABORATIVE,
    rationale="String explaining the decision",
    required_human_actions=[
        HumanAction("action name", "description", 15, blocking=False),
        HumanAction("approval needed", "description", 10, blocking=True),
    ],
    estimated_human_effort=25,  # minutes
    is_blocked=True,            # waiting on human?
    blocking_reason="Needs approval before proceeding",
    conditions=["Requires formal approval", "Time-dependent"],
    confidence=0.85
)
```

---

## Signal Format (JSONL)

```json
{
  "signal_type": "delegation_decision",
  "signal_layer": "governance",
  "signal_source": "delegation_engine",
  "payload": {
    "execution_class": "COLLABORATIVE",
    "rationale": "Requires human review and approval",
    "required_human_actions": ["review results", "provide approval"],
    "estimated_human_effort": 25,
    "is_blocked": true,
    "blocking_reason": "Awaiting human approval",
    "conditions": ["Requires formal approval"]
  },
  "mission_id": "mission_123",
  "created_at": "2026-02-07T15:30:45Z"
}
```

---

## Testing

Run validation suite:
```bash
cd c:\Users\micha\Buddy
python backend/test_phase7_delegation.py
```

Expected output:
```
[OK] Capability Boundary Classification
[OK] Delegation Evaluator
[OK] Signal Emission
[OK] Whiteboard Panel
[OK] Constraints Verification
[OK] Full Integration

TOTAL: 6/6 test suites passed
ALL TESTS PASSED - PHASE 7 READY FOR PRODUCTION
```

---

## Integration Checklist

- [ ] Import Phase 7 modules
- [ ] Create DelegationEvaluator instance
- [ ] Evaluate mission/goal before execution
- [ ] Check `is_blocked` before proceeding
- [ ] Display panel in Whiteboard UI
- [ ] Emit signal to audit stream
- [ ] Use decision for operator visibility
- [ ] Test with Phase 8 Operator Controls

---

## Constraints (DO NOT violate)

❌ **DO NOT** modify mission data
❌ **DO NOT** create missions automatically
❌ **DO NOT** trigger execution
❌ **DO NOT** add autonomy
❌ **DO NOT** retry or loop
❌ **DO NOT** mutate decisions (immutable dataclasses)
❌ **DO NOT** assume task defaults

✅ **DO** read task descriptions
✅ **DO** emit signals
✅ **DO** render panels
✅ **DO** provide summaries
✅ **DO** keep audit trail

---

## Next Phase: Phase 8

Phase 8 will integrate with Operator Controls to:
- Show delegation decisions in control panel
- Get operator approval/direction
- Execute based on delegation class + operator decision
- Provide audit trail of all decisions

---

**Phase 7 Ready for Production** ✅
