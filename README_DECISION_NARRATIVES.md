# Deterministic Decision Narratives ✅ COMPLETE

## Summary

Implemented structured "why I did this" explanations for key actions using purely deterministic logic. The system emits decision rationale signals that explain navigation choices, selector selections, and goal evaluations without using LLMs or changing any behavior.

## What Was Built

### 1. DecisionRationaleEmitter (`backend/explainability/decision_rationale.py`)
- **319 lines** of deterministic explanation logic
- 4 explanation methods for different decision types
- Structured rationale with "decision" and "because" fields
- Signal emission for learning_signals.jsonl

### 2. Integration Points (`backend/agents/web_navigator_agent.py`)
- **Intent Action Taken** - Explains why we navigated to a link
- **Selector Execution** - Explains why we chose a specific selector (ranked or fallback)
- Non-blocking, runs alongside existing signals
- No behavioral changes

### 3. Whiteboard Display (`backend/whiteboard/mission_whiteboard.py`)
- Added `decision_trace` section
- Shows most recent decision rationale only
- Includes decision, reasons, action type, timestamp

### 4. Validation Tests (`test_decision_rationale.py`)
- 9 comprehensive tests covering all decision types
- **✅ ALL TESTS PASSING (9/9)**
- Validates deterministic output (no randomness)

## Decision Types Explained

### 1. Intent Action Taken
**When:** Navigating to a ranked link based on goal  
**Example:**
```
Decision: Navigate to: Next →
Because:
  • Highest ranked action (score: 5/20 candidates)
  • Confidence (0.70) exceeds threshold (0.50)
  • Matched signals: text_navigation_keyword, goal_keyword_match:2
  • Keywords from goal found in target
```

### 2. Intent Action Blocked
**When:** Rejecting a navigation action  
**Example:**
```
Decision: Blocked navigation to: Login
Because:
  • Confidence (0.20) below threshold (0.50)
  • No positive signals detected
```

### 3. Selector Execution (Ranked)
**When:** Using a learned selector from rankings  
**Example:**
```
Decision: Execute selector: a[rel='next']
Because:
  • Selected from learned selector rankings
  • Historical success rate: 85.0%
  • CSS selector preferred for performance
  • Pagination context (page 3)
```

### 4. Selector Execution (Fallback)
**When:** Using fallback selector when rankings unavailable  
**Example:**
```
Decision: Execute selector: .next-button
Because:
  • Using fallback selector (ranked selectors unavailable)
  • CSS selector preferred for performance
```

### 5. Goal Evaluation
**When:** Evaluating if mission goal is satisfied  
**Example (Satisfied):**
```
Decision: Goal satisfied
Because:
  • Target reached (50/50 items)
  • High confidence (0.85 >= 0.60)
  • Evidence collected (50 items)
```

**Example (Not Satisfied):**
```
Decision: Goal not satisfied
Because:
  • Zero items collected
  • Low confidence (0.30 < 0.60)
```

## Signal Schema

```json
{
  "signal_type": "decision_rationale",
  "signal_layer": "explainability",
  "signal_source": "decision_engine",
  "mission_id": "unique_mission_id",
  "action_type": "intent_action_taken",
  "rationale": {
    "decision": "Navigate to: Next →",
    "because": [
      "Highest ranked action (score: 5/20 candidates)",
      "Confidence (0.70) exceeds threshold (0.50)",
      "Matched signals: text_navigation_keyword, goal_keyword_match:2"
    ]
  },
  "decision_inputs": {
    "action_text": "Next →",
    "action_href": "https://example.com/page/2",
    "goal": "Find directory of companies",
    "confidence": 0.7,
    "score": 5,
    "total_candidates": 20
  },
  "thresholds_used": {
    "confidence_threshold": 0.5
  },
  "timestamp": "2026-02-07T15:55:06Z"
}
```

## Integration Points

### Intent Actions (web_navigator_agent.py)
```python
# After intent_action_taken signal
emitter = DecisionRationaleEmitter()
rationale = emitter.explain_intent_action_taken(
    action=action,
    goal=goal,
    confidence=confidence,
    score=action.get("score", 0),
    total_candidates=action.get("total_candidates", 1)
)
self._persist_learning_signal(rationale.to_signal(mission_id))
```

### Selector Execution (web_navigator_agent.py)
```python
# After successful selector execution
emitter = DecisionRationaleEmitter()
rationale = emitter.explain_selector_choice(
    selector=selector,
    selector_type=selector_type,
    ranked=True,
    fallback_used=False,
    success_rate=success_rate,
    page_number=page_number
)
self._persist_learning_signal(rationale.to_signal(mission_id))
```

## Whiteboard Output

```json
{
  "decision_trace": {
    "decision": "Execute selector: a[rel='next']",
    "because": [
      "Selected from learned selector rankings",
      "Historical success rate: 85.0%",
      "CSS selector preferred for performance"
    ],
    "action_type": "selector_execution",
    "timestamp": "2026-02-07T15:55:06Z"
  }
}
```

## Validation Results

```
✅ Test 1: Intent Action Taken - PASSED
   - Explains navigation choices with confidence and scoring
   
✅ Test 2: Intent Action Blocked - PASSED
   - Explains why actions were rejected
   
✅ Test 3: Ranked Selector Choice - PASSED
   - Includes success rate and ranking info
   
✅ Test 4: Fallback Selector - PASSED
   - Explains fallback usage clearly
   
✅ Test 5: Goal Satisfied - PASSED
   - Explains positive outcome with evidence
   
✅ Test 6: Goal Not Satisfied - PASSED
   - Explains failure reasons
   
✅ Test 7: Signal Emission - PASSED
   - Always emits (rationales always valuable)
   
✅ Test 8: Signal Structure - PASSED
   - All required fields present
   
✅ Test 9: Deterministic Output - PASSED
   - Same inputs → same explanations (no randomness)
```

## Constraints Compliance

✅ **NO LLM Usage** - Pure heuristic rules and threshold logic  
✅ **NO Autonomy Changes** - Purely explanatory, no decisions  
✅ **NO Behavioral Changes** - Runs alongside existing code  
✅ **Deterministic Only** - Same inputs always produce same outputs  

## How to Use

### Run Validation Tests
```bash
python test_decision_rationale.py
```

### View Decision Trace in Whiteboard
```python
from backend.whiteboard.mission_whiteboard import get_mission_whiteboard

whiteboard = get_mission_whiteboard("mission-id-here")
trace = whiteboard.get("decision_trace")

if trace:
    print(f"Decision: {trace['decision']}")
    print("Because:")
    for reason in trace['because']:
        print(f"  • {reason}")
```

### Query Decision Rationale Signals
```python
import json

with open("outputs/phase25/learning_signals.jsonl", "r") as f:
    for line in f:
        signal = json.loads(line)
        if signal.get("signal_type") == "decision_rationale":
            rationale = signal.get("rationale", {})
            print(f"{rationale['decision']}")
            for reason in rationale['because']:
                print(f"  • {reason}")
```

## Files Modified/Created

**Created:**
- `backend/explainability/decision_rationale.py` (319 lines)
- `test_decision_rationale.py` (380 lines)

**Modified:**
- `backend/agents/web_navigator_agent.py` (+55 lines)
  - Import DecisionRationaleEmitter
  - Added rationale emission for intent actions (2 locations)
  - Added rationale emission for selector choices (2 locations)

- `backend/whiteboard/mission_whiteboard.py` (+18 lines)
  - Added `_decision_trace()` helper
  - Added decision_trace field to whiteboard

## Metrics

- **Total Lines of Code:** 699
- **Test Cases:** 9
- **Test Pass Rate:** 100%
- **Decision Types:** 5 (intent taken, intent blocked, selector ranked, selector fallback, goal eval)
- **Integration Points:** 4

## Real-World Examples

### Navigation Decision
```
Decision: Navigate to: Companies Directory
Because:
  • Highest ranked action (score: 8/15 candidates)
  • Confidence (0.75) exceeds threshold (0.50)
  • Matched signals: url_directory_pattern, goal_keyword_match:2
  • Keywords from goal found in target
```
**Context:** When navigating from homepage to a directory page

### Selector Decision
```
Decision: Execute selector: //a[contains(text(),'Next')]
Because:
  • Selected from learned selector rankings
  • Historical success rate: 92.5%
  • XPath selector for complex matching
  • Pagination context (page 5)
```
**Context:** When paginating through results using learned selectors

### Goal Evaluation
```
Decision: Goal not satisfied
Because:
  • Target not reached (30/50 items)
  • Low confidence (0.45 < 0.60)
```
**Context:** Mission completed but didn't meet target

## Use Cases

### 1. Mission Debugging
**Problem:** Why did mission choose this navigation path?  
**Solution:** Check decision_rationale signals to see ranking scores, confidence, and matched signals

### 2. Selector Learning Analysis
**Problem:** Is selector ranking working?  
**Solution:** Compare ranked vs fallback selector rationales to see learning impact

### 3. Goal Evaluation Transparency
**Problem:** Why was goal marked unsatisfied?  
**Solution:** Review goal evaluation rationale for specific reasons (low confidence, missing items, etc.)

### 4. Human-in-the-Loop Validation
**Problem:** Need to explain mission behavior to humans  
**Solution:** Present decision_trace from whiteboard with clear decision + reasons format

## Future Enhancements

Potential additions (outside current scope):
- Decision history timeline (multiple decisions per mission)
- Decision tree visualization
- Confidence trend analysis
- Decision pattern detection
- Alternative action comparison

---

**Status:** ✅ COMPLETE AND VALIDATED  
**Ready for:** Production use  
**Date:** February 7, 2026  
**Constraints Met:** All (NO LLM, NO autonomy, NO behavior changes, deterministic only)
