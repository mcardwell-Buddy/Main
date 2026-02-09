# Capability Boundary Model

**Phase 6 Step 1: Deterministic Task Classification**

**Status**: ✅ **COMPLETE - ALL 15 TESTS PASSED**

---

## Objective

Create a deterministic system that classifies tasks as:
- **DIGITAL** (Buddy-executable)
- **PHYSICAL** (User-required)
- **HYBRID** (handoff or approval required)

**Key Constraints**:
- ✅ No LLM usage (keyword + heuristic-based)
- ✅ No execution changes
- ✅ No new autonomy
- ✅ Read-only classification only
- ✅ Learning signals emitted on every classification

---

## Architecture

### Classification Algorithm

**Three-layer scoring**:

```
Task Description
    ↓
1. Keyword Scoring
   ├── Match against DIGITAL_KEYWORDS
   ├── Match against PHYSICAL_KEYWORDS
   ├── Match against HYBRID_KEYWORDS
   └── Each keyword match = +0.5 points
    ↓
2. Action Pattern Scoring
   ├── Match against DIGITAL_ACTIONS (regex patterns)
   ├── Match against PHYSICAL_ACTIONS (regex patterns)
   └── Each pattern match = +1.0 points
    ↓
3. Confidence Calculation
   ├── Total Score = Digital + Physical + Hybrid
   ├── Confidence = Primary Score / Total Score
   ├── If ambiguous (scores close) → HYBRID
   └── Confidence range: 0.0 to 1.0
    ↓
Result: (Capability, Confidence, Evidence)
```

---

## Keywords

### DIGITAL Keywords (60+ keywords)

**Web/Browse**:
- browse, web, search, google, website, url, link, page, view, read

**Forms**:
- form, submit, fill, input, field, checkbox, select, button, click, type

**Data Processing**:
- extract, parse, scrape, copy, paste, download, upload, process, analyze

**Email**:
- email, send, mail, message, compose, reply, forward, attachment

**API/Database**:
- api, rest, json, request, response, database, query, sql, record

**Code/Automation**:
- code, script, run, execute, automate, program, logic

### PHYSICAL Keywords (45+ keywords)

**Communication**:
- call, phone, dial, voice, speak, talk, conversation, meeting

**In-Person**:
- visit, go, travel, meet, in-person, location, office, store, warehouse

**Legal/Signing**:
- sign, signature, document, contract, legal, notary, authorize

**Logistics**:
- ship, mail, deliver, pickup, parcel, package, carrier, freight

**Inspection**:
- inspect, examine, look, check, verify, observe, physical, tangible

### HYBRID Keywords (10+ keywords)

**Handoff/Approval**:
- handoff, approval, authorization, wait, review, decision, notify, escalate

---

## Heuristics

### DIGITAL Examples

```
✅ "Send email to customer with pricing information"
   Evidence: [email, send]
   Confidence: 0.95
   Reasoning: Strong digital keywords, email action pattern

✅ "Navigate to competitor website and extract pricing data from the table"
   Evidence: [website, extract, data]
   Confidence: 0.97
   Reasoning: Multiple digital keywords + web scraping pattern

✅ "Fill out the contact form with company details and submit"
   Evidence: [form, submit, fill]
   Confidence: 0.96
   Reasoning: Form submission keywords + action patterns
```

### PHYSICAL Examples

```
✅ "Ship the package via fedex to the customer address"
   Evidence: [ship, package]
   Confidence: 0.97
   Reasoning: Strong physical logistics keywords

✅ "Sign the contract and send it back to legal"
   Evidence: [sign, contract]
   Confidence: 0.71
   Reasoning: Physical signing keyword + legal context

✅ "Call the customer support team to discuss the contract terms"
   Evidence: [call, team]
   Confidence: 0.77
   Reasoning: Phone communication keyword + conversation pattern
```

### HYBRID Examples

```
❓ "Review and approve the customer request"
   Evidence: [approval]
   Confidence: 0.60
   Reasoning: Ambiguous - could be digital (email review) or manual (in-person approval)

❓ "Extract data from website and handoff to processing team for approval"
   Evidence: [extract, handoff, approval]
   Confidence: 0.33
   Reasoning: Mixed signals - digital extraction + hybrid handoff requirement
```

---

## Classification Result

### Structure

```python
@dataclass
class ClassificationResult:
    task_description: str
    capability: Capability  # DIGITAL | PHYSICAL | HYBRID
    confidence: float       # 0.0 to 1.0
    evidence_keywords: List[str]  # Keywords that matched
    reasoning: str          # Human-readable explanation
    classified_at: datetime # UTC timestamp
```

### Example

```json
{
    "task_description": "Send email to customer with pricing information",
    "capability": "digital",
    "confidence": 0.952,
    "evidence_keywords": ["email", "send"],
    "reasoning": "Classified as DIGITAL based on digital keywords (score: 1.0), digital action patterns (score: 1.0). Evidence: email, send",
    "classified_at": "2026-02-07T20:15:30.123456"
}
```

---

## Learning Signals

### Signal Structure

Each classification emits a learning signal to `learning_signals.jsonl`:

```json
{
    "signal_type": "capability_classified",
    "signal_layer": "cognition",
    "signal_source": "capability_model",
    "timestamp": "2026-02-07T20:15:30.123456",
    "data": {
        "task_description": "Send email to customer with pricing information",
        "capability": "digital",
        "confidence": 0.952,
        "evidence_keywords": ["email", "send"],
        "reasoning": "Classified as DIGITAL based on digital keywords...",
        "classified_at": "2026-02-07T20:15:30.123456"
    }
}
```

### Signal Log Format

**Append-only JSONL** (one JSON object per line):
- Each line is a complete JSON object
- Never modified after creation
- Queryable and analyzable

### Statistics Available

```python
writer = LearningSignalWriter("learning_signals.jsonl")

stats = writer.get_statistics()
# Returns:
# {
#     "total_signals": 100,
#     "digital_count": 60,
#     "physical_count": 25,
#     "hybrid_count": 15,
#     "avg_confidence": 0.78,
#     "digital_percentage": 60.0,
#     "physical_percentage": 25.0,
#     "hybrid_percentage": 15.0
# }
```

---

## API Usage

### Basic Classification

```python
from backend.capability_boundary_model import classify_task, Capability

# Classify a task
result = classify_task("Send email to customer with invoice")

# Check capability
if result.capability == Capability.DIGITAL:
    print("Buddy can execute this task")
elif result.capability == Capability.PHYSICAL:
    print("User interaction required")
else:  # HYBRID
    print("Handoff or approval needed")

# Access details
print(f"Confidence: {result.confidence}")
print(f"Evidence: {result.evidence_keywords}")
print(f"Reasoning: {result.reasoning}")
```

### With Signal Logging

```python
from backend.capability_boundary_model import classify_task
from backend.learning_signal_writer import LearningSignalWriter

model = CapabilityBoundaryModel()
writer = LearningSignalWriter("learning_signals.jsonl")

# Classify task
result = model.classify_task("Extract data from website")

# Emit learning signal
writer.emit_classification_signal(result)

# Read all signals
signals = writer.read_signals()
for signal in signals:
    print(f"{signal['data']['capability']}: {signal['data']['task_description']}")
```

### In Mission Execution Flow

```python
# During mission initialization
from backend.capability_boundary_model import classify_task

mission_objective = "Extract competitor pricing and send email to team"
classification = classify_task(mission_objective)

if classification.capability == Capability.DIGITAL:
    # Execute mission autonomously
    execute_mission_autonomously(mission_objective)

elif classification.capability == Capability.PHYSICAL:
    # Route to user
    alert_user("Task requires human action: " + mission_objective)

else:  # HYBRID
    # Route for approval
    route_for_approval(mission_objective, classification)
```

---

## Unit Tests (15 Total)

All tests passed with exit code 0.

### Tests 1-3: DIGITAL Classification

| Test | Task | Result | Confidence |
|------|------|--------|-----------|
| 1 | "Send email to customer with pricing information" | DIGITAL | 0.952 |
| 2 | "Navigate to competitor website and extract pricing data" | DIGITAL | 0.972 |
| 3 | "Fill out the contact form and submit" | DIGITAL | 0.962 |

### Tests 4-6: PHYSICAL Classification

| Test | Task | Result | Confidence |
|------|------|--------|-----------|
| 4 | "Ship the package via fedex" | PHYSICAL | 0.972 |
| 5 | "Sign the contract and send back" | PHYSICAL | 0.714 |
| 6 | "Call the customer support team" | PHYSICAL | 0.769 |

### Tests 7-8: HYBRID Classification

| Test | Task | Result | Confidence |
|------|------|--------|-----------|
| 7 | "Review and approve the customer request" | HYBRID | 0.600 |
| 8 | "Extract data and handoff for approval" | HYBRID | 0.333 |

### Tests 9-11: Learning Signals

| Test | Purpose | Result |
|------|---------|--------|
| 9 | Emit and verify single signal | 1 signal created |
| 10 | Accumulate multiple signals | 3 signals accumulated |
| 11 | Calculate statistics | Digital: 2, Physical: 1, Hybrid: 0 |

### Tests 12-15: Edge Cases

| Test | Scenario | Result |
|------|----------|--------|
| 12 | Empty task description | HYBRID (confidence 0.5) |
| 13 | Complex multi-step task | DIGITAL or HYBRID |
| 14 | High-confidence digital | DIGITAL (confidence > 0.7) |
| 15 | Global convenience function | Works correctly |

---

## Files

| File | Purpose | Lines |
|------|---------|-------|
| [backend/capability_boundary_model.py](backend/capability_boundary_model.py) | Classification engine, keyword/pattern matching | 450+ |
| [backend/learning_signal_writer.py](backend/learning_signal_writer.py) | Signal emission and logging | 110+ |
| [backend/test_capability_boundary_model.py](backend/test_capability_boundary_model.py) | 15 unit tests | 350+ |

---

## Output Files

Signal logs created during testing:
- `signals_test9.jsonl` - 1 signal
- `signals_test10.jsonl` - 3 signals
- `signals_test11.jsonl` - 3 signals

Each file contains properly formatted JSONL with complete signal metadata.

---

## Implementation Notes

### No LLM Usage

✅ Pure keyword matching (no ML/LLM)  
✅ Deterministic regex patterns  
✅ Confidence from score ratios  
✅ Same input → Same output (idempotent)

### No Execution Changes

✅ Read-only classification  
✅ No side effects on mission execution  
✅ Signals are observational only  
✅ Can integrate into existing workflows

### No New Autonomy

✅ Classification only (no decision-making)  
✅ Signals inform but don't control  
✅ User retains control (PHYSICAL/HYBRID routes)  
✅ No automatic task promotion

### Learning Signals

✅ Emitted on every classification  
✅ Append-only JSONL format  
✅ Queryable by capability, confidence, time  
✅ No privacy/security concerns (observational)

---

## Integration Points

### With Operator Controls

```
Task Classification
    ↓
If DIGITAL → Can auto-execute (no approval needed)
If PHYSICAL → Route to user (manual required)
If HYBRID → Route to operator controls (approval required)
```

### With Streaming Events

```
classify_task(objective)
    ↓
emit_classification_signal()
    ↓
Streaming event: capability_classified
    ├── capability: "digital" | "physical" | "hybrid"
    ├── confidence: 0.95
    └── evidence: [keywords]
```

### With ResponseEnvelope

```
Task classified as DIGITAL
    ↓
Mission execution initiated
    ↓
ResponseEnvelope created with:
    ├── capabilities_used: ["digital"]
    ├── classification_confidence: 0.95
    └── signals_emitted: [capability_classified_signal]
```

---

## Next Steps (Phase 6)

✅ Step 1: Capability Boundary Model (COMPLETE)

**Future Steps**:
- Step 2: Skill Registry (what Buddy can do)
- Step 3: Task Router (task → skill mapping)
- Step 4: Execution Planner (multi-step task decomposition)
- Step 5: Safety Validator (can this task be executed safely?)

---

## Status: ✅ COMPLETE

- ✅ `Capability` enum defined (DIGITAL, PHYSICAL, HYBRID)
- ✅ `classify_task()` function implemented (keyword + pattern heuristics)
- ✅ Confidence scoring (0.0 to 1.0)
- ✅ Evidence keyword tracking
- ✅ Learning signals emitted (signal_type: capability_classified)
- ✅ JSONL signal logging (append-only)
- ✅ 15 unit tests (all passing)
- ✅ Statistics generation
- ✅ No LLM usage
- ✅ No execution changes
- ✅ No new autonomy
- ✅ Read-only classification only

