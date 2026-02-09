# Human Energy Model - Phase 6 Step 2

## Overview

The Human Energy Model estimates human effort cost and rest constraints for tasks. It provides deterministic, heuristic-based classification without relying on LLM inference.

**Key Purpose**: Enable Buddy to understand human effort requirements and rest awareness for task recommendations.

**Design**: Observational only - no scheduling automation, no reminders, no enforcement.

## Effort Levels

| Level | Definition | Time Range | Examples |
|-------|-----------|-----------|----------|
| **LOW** | Reply, approve, skim | < 5 min | Email reply, approve order, quick review |
| **MEDIUM** | Review doc, make decision | 5-30 min | Document review, decision-making, code review |
| **HIGH** | Calls, meetings, physical | > 30 min | Phone calls, meetings, site visits |

## Classification Heuristics

### Keyword-Based Scoring

**LOW Effort Keywords** (68 total):
- Actions: reply, respond, acknowledge, approve, reject, accept, decline, confirm
- Characteristics: quick, brief, fast, short, skim, glance
- Examples: quick review, email reply, simple choice

**MEDIUM Effort Keywords** (92 total):
- Actions: review, analyze, evaluate, assess, decide, recommend
- Characteristics: document, discussion, moderate, feedback
- Examples: document review, code review, decision making, research

**HIGH Effort Keywords** (109 total):
- Actions: call, meeting, presentation, interview, training
- Characteristics: travel, physical, extensive, comprehensive
- Examples: phone call, team meeting, site visit, workshop

### Pattern-Based Scoring

**MEDIUM Patterns** (9 regex rules):
- `read.*document` (1.5 pts)
- `review.*document` (1.5 pts)
- `make.*decision` (2.0 pts)
- `discuss.*with` (1.5 pts)
- `write.*email` (1.5 pts)
- And 4 more...

**HIGH Patterns** (14 regex rules):
- `attend.*meeting` (3.0 pts)
- `conduct.*meeting` (3.0 pts)
- `phone.*call` (3.0 pts)
- `video.*call` (3.0 pts)
- `presentation` (3.0 pts)
- And 9 more...

### Scoring Algorithm

1. **Keyword Matching**: 0.5 points per keyword match
2. **Pattern Matching**: 1.0-3.0 points per regex match
3. **Confidence Calculation**: `primary_score / total_score`
4. **Effort Level**: Highest-scoring category wins

## Rest Awareness

### Rest Window Configuration

```python
model = HumanEnergyModel(max_continuous_minutes=120.0)  # Default: 2 hours
```

### Rest Status Thresholds

| Condition | Threshold | Status |
|-----------|-----------|--------|
| **OK** | < 85% of limit | No warning |
| **NEAR_LIMIT** | 85-100% of limit | Soft warning |
| **EXCEEDED** | > 100% of limit | Hard warning |

### Rest Calculation

```
projected_effort = cumulative_minutes + task_estimated_minutes

if projected_effort > max_continuous_minutes * 1.2:
    status = "EXCEEDS_LIMIT"
elif projected_effort > max_continuous_minutes * 0.85:
    status = "NEAR_LIMIT"
else:
    status = "OK"
```

**Key Point**: Soft warnings only - observational, no enforcement.

## API

### Main Class: `HumanEnergyModel`

```python
from human_energy_model import HumanEnergyModel

model = HumanEnergyModel(max_continuous_minutes=120.0)

# Estimate human cost
estimate = model.estimate_human_cost(
    task_description="Review quarterly report",
    current_cumulative_minutes=30.0
)

print(estimate.effort_level)           # EffortLevel.MEDIUM
print(estimate.estimated_minutes)      # 15.0
print(estimate.min_minutes)            # 5.0
print(estimate.max_minutes)            # 30.0
print(estimate.evidence_keywords)      # ['review']
print(estimate.rest_warning)           # False
print(estimate.rest_recommendation)    # "OK"
```

### Convenience Function

```python
from human_energy_model import estimate_human_cost

result = estimate_human_cost("Reply to email")
# Returns: HumanEnergyEstimate
```

### Result Structure: `HumanEnergyEstimate`

```python
@dataclass
class HumanEnergyEstimate:
    task_description: str            # Original task
    effort_level: EffortLevel        # LOW, MEDIUM, HIGH
    estimated_minutes: float         # Point estimate (mid-range)
    min_minutes: float               # Optimistic (min-range)
    max_minutes: float               # Pessimistic (max-range)
    evidence_keywords: List[str]     # Keywords that influenced classification
    reasoning: str                   # Human-readable explanation
    rest_warning: bool               # Whether exceeds window
    rest_recommendation: str         # "OK", "NEAR_LIMIT", "EXCEEDS_LIMIT"
    session_id: str                  # For tracking
    timestamp: str                   # ISO 8601 timestamp
```

### Rest Status Method

```python
model.cumulative_effort_minutes = 85.0
status = model.get_rest_status()

# Returns:
{
    "cumulative_minutes": 85.0,
    "max_continuous_minutes": 120.0,
    "remaining_minutes": 35.0,
    "status": "OK"
}
```

## Learning Signals

Every estimation emits a learning signal for observability:

```json
{
  "signal_type": "human_effort_estimated",
  "signal_layer": "cognition",
  "signal_source": "human_energy_model",
  "timestamp": "2026-02-07T16:49:06.055039",
  "session_id": "3a6b436b-a298-40ae-a383-54514333ca69",
  "data": {
    "task_description": "Review quarterly report",
    "effort_level": "MEDIUM",
    "estimated_minutes": 15.0,
    "min_minutes": 5.0,
    "max_minutes": 30.0,
    "evidence_keywords": ["review"],
    "rest_warning": false,
    "rest_recommendation": "OK",
    "reasoning": "MEDIUM effort (80% confidence). Estimated 15 minutes..."
  }
}
```

## Examples

### Example 1: Low Effort Task

```python
model = HumanEnergyModel()
result = model.estimate_human_cost("Reply to customer email")

# Output:
# effort_level: LOW
# estimated_minutes: 3.0 (range: 1.0-5.0)
# evidence_keywords: ['email', 'reply']
# rest_warning: False
# rest_recommendation: "OK"
```

### Example 2: Medium Effort Task

```python
result = model.estimate_human_cost("Review the quarterly report document")

# Output:
# effort_level: MEDIUM
# estimated_minutes: 15.0 (range: 5.0-30.0)
# evidence_keywords: ['review']
# rest_warning: False
```

### Example 3: High Effort Task

```python
result = model.estimate_human_cost("Attend team planning meeting")

# Output:
# effort_level: HIGH
# estimated_minutes: 60.0 (range: 30.0-120.0)
# evidence_keywords: ['meeting', 'plan', 'attend']
# rest_warning: False
```

### Example 4: Rest Warning

```python
result = model.estimate_human_cost(
    "Attend long meeting",
    current_cumulative_minutes=110.0  # Already at 110 minutes
)

# Output:
# effort_level: HIGH
# estimated_minutes: 60.0
# rest_warning: True
# rest_recommendation: "EXCEEDS_LIMIT"
```

### Example 5: Duration Modifiers

```python
# With "quick" modifier - reduces estimate
quick = model.estimate_human_cost("Quick review of document")
# estimated_minutes: ~10.5 (reduced from 15)

# With "extensive" modifier - increases estimate
extensive = model.estimate_human_cost("Extensive analysis of data")
# estimated_minutes: ~22.5 (increased from 15)
```

## Integration Points

### With Operator Controls

Operator can see effort estimates when reviewing tasks:
- LOW effort: Auto-safe delegation
- MEDIUM effort: Worth reviewing
- HIGH effort: Requires explicit approval

### With Streaming Events

Effort estimates included in execution streaming:
```python
{
  "mission_id": "m123",
  "event_type": "task_estimate",
  "data": {
    "effort_level": "MEDIUM",
    "estimated_minutes": 15.0,
    "rest_warning": false
  }
}
```

### With Capability Boundary Model

Combined classification:
- Capability: DIGITAL/PHYSICAL/HYBRID
- Effort: LOW/MEDIUM/HIGH
- Decision: Which human should handle + when?

## Implementation Details

### Determinism

All classifications are deterministic (same input → same output):
- Keyword matching uses exact substring search (case-insensitive)
- Patterns use regex (consistent across calls)
- Confidence calculation is deterministic math
- No randomization, no LLM inference

### Performance

- Classification: O(n) where n = task description length
- Keyword matching: O(k) where k = keyword set size (~260 total)
- Pattern matching: O(p) where p = pattern count (23 total)
- Typical execution: < 1ms per classification

### Memory Usage

- Model instance: ~50KB (keyword sets + patterns)
- Per estimate: ~2KB
- No persistent state beyond session_id

## Files

| File | Purpose | Lines |
|------|---------|-------|
| `human_energy_model.py` | Core model implementation | 550+ |
| `test_human_energy_model.py` | Comprehensive unit tests (32 tests) | 450+ |
| `HUMAN_ENERGY_MODEL.md` | This documentation | 400+ |

## Unit Tests

All 32 tests passing:

**Test Coverage**:
- LOW effort classification (3 tests)
- MEDIUM effort classification (3 tests)
- HIGH effort classification (3 tests)
- Rest constraints (3 tests)
- Time estimates (2 tests)
- Duration modifiers (2 tests)
- Signal structure (3 tests)
- Edge cases (4 tests)
- Confidence scores (2 tests)
- Rest status (2 tests)
- Convenience function (1 test)
- Determinism (2 tests)
- Session tracking (2 tests)

**Test Execution**:
```bash
$ pytest test_human_energy_model.py -v
============================= 32 passed in 0.37s ==============================
```

## Constraints

### What This Model DOES

✅ Classify tasks by human effort level (LOW/MEDIUM/HIGH)  
✅ Estimate time ranges for tasks  
✅ Track cumulative effort within a window  
✅ Provide soft warnings when approaching limits  
✅ Emit learning signals for observability  
✅ Support deterministic classification (no LLM)  

### What This Model DOES NOT DO

❌ Schedule tasks  
❌ Send reminders  
❌ Enforce rest constraints  
❌ Make autonomous decisions  
❌ Modify task execution  
❌ Use machine learning  
❌ Collect historical data  

## Future Extensions

### Potential Enhancements (Not Currently Implemented)

1. **Effort Adjustment**: Based on task complexity/priority
2. **Cumulative Tracking**: Historical effort patterns
3. **User Profiles**: Different rest windows per person
4. **Recovery Prediction**: Estimated recovery time after high-effort tasks
5. **Effort Trends**: Weekly/monthly effort analysis

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-07 | Initial release (Phase 6 Step 2) |

## Status

**Production Ready**: Yes

**All Constraints Met**:
- ✅ No execution changes
- ✅ No scheduling automation
- ✅ No reminders
- ✅ Observational only
- ✅ Deterministic classification
- ✅ Learning signals emitted
- ✅ 32/32 unit tests passing

