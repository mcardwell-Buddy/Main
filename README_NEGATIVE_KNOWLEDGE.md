# Negative Knowledge Registry ✅ COMPLETE

## Summary

Implemented a read-only observational system that captures what Buddy should NOT do again by learning from failure patterns. The registry analyzes historical learning signals to identify and persist negative knowledge without ever blocking execution or using LLMs.

## What Was Built

### 1. NegativeKnowledgeRegistry (`backend/learning/negative_knowledge_registry.py`)
- **460 lines** of deterministic pattern detection logic
- Analyzes mission failures, selector failures, and ambiguity patterns
- Persists to `outputs/phase25/negative_knowledge.jsonl`
- Zero autonomy, zero LLM usage, purely observational

### 2. Whiteboard Integration (`backend/whiteboard/mission_whiteboard.py`)
- Added "what_buddy_avoids" section
- Displays summary statistics by pattern type
- Shows high-confidence patterns (≥0.7)
- Read-only display, never affects execution

### 3. Validation Tests
- **9 comprehensive tests** covering all functionality
- **✅ ALL TESTS PASSING (9/9)**
- Real-world test with actual learning_signals.jsonl
- Confirms deterministic, non-blocking behavior

## Constraints Compliance

✅ **NO Autonomy** - Registry never blocks execution or makes decisions  
✅ **NO Blocking** - Purely observational, runs alongside normal operation  
✅ **NO Selenium Changes** - No modifications to browser automation  
✅ **NO LLM Usage** - Deterministic pattern detection using thresholds  
✅ **Observational Only** - Learns from existing signals  
✅ **Analytical Only** - Surfaces insights, never triggers actions  

## Pattern Types Detected

### 1. Mission Failures
**Captured from:** `mission_failed`, `mission_status_update` signals  
**Example:**
```json
{
  "pattern_type": "mission",
  "pattern_signature": "83b832f47b541ae0",
  "reason": "Mission failed: no_progress",
  "evidence": ["mission-id-123"],
  "confidence": 0.70,
  "occurrence_count": 2
}
```

### 2. Selector Failures
**Captured from:** `selector_outcome` signals with `outcome: "failure"`  
**Criteria:** Selector must fail at least 2 times  
**Example:**
```json
{
  "pattern_type": "selector",
  "pattern_signature": "ef0f99c78ba84d86",
  "reason": "Selector consistently fails (failed 2 times)",
  "evidence": ["timestamp1", "timestamp2"],
  "confidence": 0.70,
  "occurrence_count": 1
}
```

### 3. Goal Ambiguity (Future)
**Captured from:** `mission_ambiguous` signals  
**Purpose:** Track goals that produce unclear results

### 4. Excessive Cost (Future)
**Captured from:** `excessive_cost` signals  
**Purpose:** Identify expensive, low-value patterns

### 5. Opportunity Failures (Future)
**Purpose:** Track non-converting opportunity types

### 6. Program Failures (Future)
**Purpose:** Track failed program patterns

## How It Works

### Pattern Detection Flow
```
learning_signals.jsonl
         ↓
NegativeKnowledgeRegistry.process_learning_signals()
         ↓
Analyze by signal type:
  • mission_failed → Mission pattern
  • selector_outcome (failure) → Selector pattern
  • mission_ambiguous → Goal pattern
  • excessive_cost → Cost pattern
         ↓
Generate deterministic signature (SHA-256 hash)
         ↓
Check if pattern exists:
  • If yes: Increment occurrence_count, increase confidence
  • If no: Create new entry with initial confidence
         ↓
Persist to negative_knowledge.jsonl
         ↓
Surface via whiteboard "what_buddy_avoids"
```

### Confidence Scoring
- **Initial confidence:** 0.5-0.8 depending on pattern type
- **Increment per observation:** +0.1
- **Maximum:** 1.0 (capped)
- **High confidence threshold:** ≥0.7

### Signature Generation
Deterministic hashing ensures same pattern → same signature:
```python
signature_input = f"{pattern_type}::{json.dumps(components, sort_keys=True)}"
signature = hashlib.sha256(signature_input.encode()).hexdigest()[:16]
```

## Data Model

### NegativeKnowledgeEntry
```python
@dataclass
class NegativeKnowledgeEntry:
    pattern_type: str          # "mission" | "selector" | "goal" | "opportunity" | "program" | "site"
    pattern_signature: str     # 16-char hex hash for deduplication
    reason: str                # Human-readable explanation
    evidence: List[str]        # Signal IDs supporting this pattern
    confidence: float          # 0.0-1.0 strength of evidence
    first_observed: str        # ISO timestamp
    last_observed: str         # ISO timestamp
    occurrence_count: int      # Number of times observed
```

### Persistence Format (JSONL)
```jsonl
{"pattern_type": "mission", "pattern_signature": "83b832f47b541ae0", "reason": "Mission failed: no_progress", "evidence": ["0035d374-2f36-499f-afba-10a2fd3d47e9"], "confidence": 0.6, "first_observed": "2026-02-07T16:00:37.846580+00:00", "last_observed": "2026-02-07T16:00:37.846580+00:00", "occurrence_count": 1}
```

## Whiteboard Output

### "what_buddy_avoids" Section
```json
{
  "what_buddy_avoids": {
    "summary": {
      "mission": {
        "pattern_count": 1,
        "total_occurrences": 2,
        "avg_confidence": 0.70,
        "high_confidence_count": 1
      },
      "selector": {
        "pattern_count": 1,
        "total_occurrences": 1,
        "avg_confidence": 0.70,
        "high_confidence_count": 1
      }
    },
    "high_confidence_patterns": {
      "mission": [
        {
          "reason": "Mission failed: no_progress",
          "confidence": 0.70,
          "occurrences": 2,
          "first_seen": "2026-02-07T16:00:37.846580+00:00",
          "last_seen": "2026-02-07T16:00:37.848578+00:00"
        }
      ],
      "selector": [
        {
          "reason": "Selector consistently fails (failed 2 times)",
          "confidence": 0.70,
          "occurrences": 1,
          "first_seen": "2026-02-07T16:00:37.851089+00:00",
          "last_seen": "2026-02-07T16:00:37.851089+00:00"
        }
      ]
    },
    "total_patterns": 2
  }
}
```

## API Reference

### NegativeKnowledgeRegistry Methods

#### `__init__(outputs_dir: str = "outputs/phase25")`
Initialize registry and load existing patterns from disk.

#### `add_pattern(pattern_type, pattern_components, reason, evidence_signal_ids, confidence=0.5)`
Add or update a negative knowledge pattern.
- **Returns:** `NegativeKnowledgeEntry`

#### `analyze_mission_failure(mission_signal: Dict[str, Any])`
Analyze a mission_failed signal for negative patterns.
- **Returns:** `Optional[NegativeKnowledgeEntry]`

#### `analyze_selector_failures(selector_signals: List[Dict[str, Any]])`
Batch analyze selector_outcome signals for failing selectors.
- **Returns:** `List[NegativeKnowledgeEntry]`

#### `process_learning_signals(max_signals: Optional[int] = None)`
Process learning_signals.jsonl to extract all patterns.
- **Returns:** `Dict[str, int]` (statistics)

#### `get_all_patterns()`
Get all patterns in the registry.
- **Returns:** `List[NegativeKnowledgeEntry]`

#### `get_patterns_by_type(pattern_type: str)`
Filter patterns by type.
- **Returns:** `List[NegativeKnowledgeEntry]`

#### `get_high_confidence_patterns(min_confidence: float = 0.7)`
Get patterns above confidence threshold.
- **Returns:** `List[NegativeKnowledgeEntry]`

#### `get_summary_by_type()`
Get statistics grouped by pattern type.
- **Returns:** `Dict[str, Dict[str, Any]]`

### Utility Functions

#### `get_negative_knowledge_for_whiteboard(outputs_dir: str = "outputs/phase25")`
Get negative knowledge formatted for whiteboard display.
- **Returns:** `Dict[str, Any]`

## Usage Examples

### Process Real Signals
```python
from backend.learning.negative_knowledge_registry import NegativeKnowledgeRegistry

registry = NegativeKnowledgeRegistry(outputs_dir="outputs/phase25")
stats = registry.process_learning_signals()

print(f"Processed {stats['processed']} signals")
print(f"Detected {stats['patterns_detected']} patterns")
```

### Query Patterns
```python
# Get all mission failure patterns
mission_patterns = registry.get_patterns_by_type("mission")

# Get high-confidence patterns only
high_conf = registry.get_high_confidence_patterns(min_confidence=0.8)

# Get summary statistics
summary = registry.get_summary_by_type()
print(f"Mission patterns: {summary['mission']['pattern_count']}")
```

### View in Whiteboard
```python
from backend.whiteboard.mission_whiteboard import get_mission_whiteboard

whiteboard = get_mission_whiteboard("mission-id-here")
avoids = whiteboard["what_buddy_avoids"]

print(f"Total patterns: {avoids['total_patterns']}")
for ptype, patterns in avoids["high_confidence_patterns"].items():
    print(f"{ptype}: {len(patterns)} patterns")
```

## Validation Results

### Test Suite (9 Tests)
```
✅ Test 1: Pattern Creation - PASSED
✅ Test 2: Selector Failure Analysis - PASSED
✅ Test 3: Mission Failure Analysis - PASSED
✅ Test 4: Persistence and Loading - PASSED
✅ Test 5: Confidence Scoring - PASSED
✅ Test 6: Pattern Filtering - PASSED
✅ Test 7: Real Signal Processing - PASSED
✅ Test 8: Whiteboard Integration - PASSED
✅ Test 9: Summary Statistics - PASSED
```

### Real-World Test Results
Processing actual `learning_signals.jsonl`:
- **Signals processed:** 64
- **Mission failures detected:** 2
- **Selector failures detected:** 1
- **Patterns created:** 2 unique patterns
- **File created:** `outputs/phase25/negative_knowledge.jsonl`

### Whiteboard Integration Test
```
✅ Whiteboard retrieved successfully
✅ "what_buddy_avoids" section present
✅ Summary statistics accurate
✅ High confidence patterns displayed
✅ No execution impact
```

## Files Modified/Created

**Created:**
- [backend/learning/negative_knowledge_registry.py](backend/learning/negative_knowledge_registry.py) (460 lines)
- [test_negative_knowledge.py](test_negative_knowledge.py) (458 lines)
- [test_negative_knowledge_realworld.py](test_negative_knowledge_realworld.py) (114 lines)
- [test_whiteboard_negative_knowledge.py](test_whiteboard_negative_knowledge.py) (73 lines)
- `outputs/phase25/negative_knowledge.jsonl` (auto-generated)

**Modified:**
- [backend/whiteboard/mission_whiteboard.py](backend/whiteboard/mission_whiteboard.py) (+30 lines)
  - Added import: `get_negative_knowledge_for_whiteboard`
  - Added helper: `_negative_knowledge_summary()`
  - Added field: `"what_buddy_avoids"` to whiteboard output

## Real-World Example

### Input Signals
From `learning_signals.jsonl`:
```jsonl
{"signal_type": "selector_outcome", "selector": ".page-next", "outcome": "failure", "timestamp": "2026-02-06T21:56:16.078622+00:00"}
{"signal_type": "selector_outcome", "selector": ".page-next", "outcome": "failure", "timestamp": "2026-02-06T21:56:16.078622+00:00"}
{"signal_type": "mission_failed", "mission_id": "0035d374-2f36-499f-afba-10a2fd3d47e9", "reason": "no_progress"}
```

### Registry Output
`negative_knowledge.jsonl`:
```jsonl
{"pattern_type": "selector", "pattern_signature": "ef0f99c78ba84d86", "reason": "Selector consistently fails (failed 2 times)", "evidence": ["2026-02-06T21:56:16.078622+00:00", "2026-02-06T21:56:16.078622+00:00"], "confidence": 0.7, "first_observed": "2026-02-07T16:00:37.851089+00:00", "last_observed": "2026-02-07T16:00:37.851089+00:00", "occurrence_count": 1}
{"pattern_type": "mission", "pattern_signature": "83b832f47b541ae0", "reason": "Mission failed: no_progress", "evidence": ["0035d374-2f36-499f-afba-10a2fd3d47e9"], "confidence": 0.7, "first_observed": "2026-02-07T16:00:37.846580+00:00", "last_observed": "2026-02-07T16:00:37.848578+00:00", "occurrence_count": 2}
```

### Whiteboard Display
```
📋 WHAT BUDDY AVOIDS
Total patterns tracked: 2

⚠️  High confidence patterns:
   MISSION:
      • Mission failed: no_progress
        Confidence: 0.70
        Occurrences: 2
   
   SELECTOR:
      • Selector consistently fails (failed 2 times)
        Confidence: 0.70
        Occurrences: 1
```

## Use Cases

### 1. Mission Post-Mortem Analysis
**Problem:** Why do certain missions keep failing?  
**Solution:** Check negative knowledge registry for repeated failure patterns

### 2. Selector Debugging
**Problem:** Which selectors are unreliable?  
**Solution:** Query selector patterns with high occurrence counts

### 3. Goal Refinement
**Problem:** Are there goal formulations that consistently fail?  
**Solution:** Review goal/mission patterns to identify problematic objectives

### 4. Cost Optimization
**Problem:** Which patterns have high cost/low value?  
**Solution:** Future: excessive_cost patterns will identify expensive operations

### 5. Human-in-the-Loop Insights
**Problem:** Need to explain to humans what Buddy is learning  
**Solution:** "what_buddy_avoids" section provides clear, confidence-scored insights

## Design Principles

### 1. Zero Execution Impact
- Registry runs alongside normal operation
- Never blocks or delays mission execution
- Graceful degradation if registry unavailable

### 2. Deterministic Detection
- No LLMs, no randomness
- Same inputs always produce same patterns
- Confidence scoring is formula-based

### 3. Evidence-Based Learning
- Every pattern backed by signal IDs
- Confidence increases with repeated observations
- Patterns emerge from data, not assumptions

### 4. Persistent Memory
- JSONL format for append-only durability
- Registry survives restarts
- Historical patterns accumulate over time

### 5. Human-Readable Output
- Natural language reasons
- Confidence scores (0.0-1.0)
- Occurrence counts
- Temporal tracking (first/last seen)

## Future Enhancements

Potential additions (outside current scope):
- **Auto-selector pruning:** Suggest removing consistently failing selectors
- **Mission template warnings:** Flag goal formulations with high failure rates
- **Cost-benefit analysis:** Compare pattern cost vs. success rate
- **Pattern trend detection:** Identify patterns getting worse over time
- **Anomaly detection:** Flag new failure patterns not seen before
- **Pattern decay:** Reduce confidence for old patterns if not observed recently

## Metrics

- **Total Lines of Code:** 1,105
- **Core Module:** 460 lines
- **Test Coverage:** 9 tests
- **Test Pass Rate:** 100%
- **Pattern Types:** 6 (mission, selector, goal, opportunity, program, site)
- **Confidence Range:** 0.0-1.0
- **High Confidence Threshold:** ≥0.7
- **Signature Length:** 16 hex characters
- **Persistence Format:** JSONL (append-only)

## Running Tests

### Validation Test Suite
```bash
python test_negative_knowledge.py
```
Runs 9 comprehensive tests covering:
- Pattern creation and signature generation
- Selector failure detection
- Mission failure analysis
- Persistence and loading
- Confidence scoring
- Pattern filtering
- Real signal processing
- Whiteboard integration
- Summary statistics

### Real-World Test
```bash
python test_negative_knowledge_realworld.py
```
Processes actual `learning_signals.jsonl` and displays:
- Processing statistics
- Patterns by type
- High confidence patterns
- Summary statistics
- Whiteboard preview

### Whiteboard Integration Test
```bash
python test_whiteboard_negative_knowledge.py
```
Verifies:
- Whiteboard contains "what_buddy_avoids"
- Summary statistics are accurate
- High confidence patterns are displayed
- No execution impact

---

**Status:** ✅ COMPLETE AND VALIDATED  
**Ready for:** Production use  
**Date:** February 7, 2026  
**Constraints Met:** All (NO autonomy, NO blocking, NO Selenium, NO LLM, observational only)
