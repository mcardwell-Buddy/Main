# WebNavigatorAgent — Complete Documentation (Steps 1-3)

**Status:** Phase 1 Steps 1, 2, and 3 Complete ✅  
**Date:** February 6, 2026  
**Version:** 1.1 (With Learning Signals)

---

## Overview

**WebNavigatorAgent** is a wrapper around existing Selenium tooling (BuddysVisionCore + BuddysArms) that provides:

1. **Step 1:** Clean agent-style interface for navigation + extraction
2. **Step 2:** Bounded pagination traversal with 4 detection strategies
3. **Step 3:** Selector-level learning signal emission (instrumentation only)

**Zero modifications to core Selenium files.**

---

## Example Learning Signals (Actual Format)

### Scenario: 2-Page Site with "Next" Button

#### Single Page Run (max_pages=1)

**Expected:** No pagination detection, no signals emitted

```
[INFO] Single-page extraction (max_pages=1)
✓ Navigation completed: 5 items extracted across 1 page(s)
[AGGREGATE] 0 selectors: 0 success, 0 failed (rate: 0%)
```

---

#### Multi-Page Run (max_pages=3, Page 1→2 Successful)

**Expected:** Selectors attempted → pagination control found → navigation successful

```
[INFO] Extracting from page 1/3
[SIGNAL] css:a[rel='next'] → failure (45ms, 0 retries)
[SIGNAL] aria:aria-label contains 'next' → failure (23ms, 0 retries)
[SIGNAL] text:button:'Next' → failure (67ms, 0 retries)
[SIGNAL] text:a:'Next' → success (89ms, 0 retries)
[INFO] Pagination detected: link text='Next'
[SIGNAL] interaction:pagination_element.click() → success (2145ms, 1 retries)

[INFO] Extracting from page 2/3
[SIGNAL] css:a[rel='next'] → failure (42ms, 0 retries)
[SIGNAL] aria:aria-label contains 'next' → failure (25ms, 0 retries)
[SIGNAL] text:button:'Next' → failure (71ms, 0 retries)
[SIGNAL] text:a:'Next' → failure (82ms, 0 retries)
[INFO] No pagination control found, stopping
```

**Signals Emitted to JSONL:**

```json
{"signal_type": "selector_outcome", "tool_name": "web_navigator_agent", "selector": "a[rel='next']", "selector_type": "css", "page_number": 1, "outcome": "failure", "duration_ms": 45, "retry_count": 0, "confidence": 0.0, "timestamp": "2026-02-06T15:30:00.123456Z"}
{"signal_type": "selector_outcome", "tool_name": "web_navigator_agent", "selector": "aria-label contains 'next'", "selector_type": "aria", "page_number": 1, "outcome": "failure", "duration_ms": 23, "retry_count": 0, "confidence": 0.0, "timestamp": "2026-02-06T15:30:00.168Z"}
{"signal_type": "selector_outcome", "tool_name": "web_navigator_agent", "selector": "button:'Next'", "selector_type": "text", "page_number": 1, "outcome": "failure", "duration_ms": 67, "retry_count": 0, "confidence": 0.0, "timestamp": "2026-02-06T15:30:00.191Z"}
{"signal_type": "selector_outcome", "tool_name": "web_navigator_agent", "selector": "a:'Next'", "selector_type": "text", "page_number": 1, "outcome": "success", "duration_ms": 89, "retry_count": 0, "confidence": 0.0, "timestamp": "2026-02-06T15:30:00.280Z"}
{"signal_type": "selector_outcome", "tool_name": "web_navigator_agent", "selector": "pagination_element.click()", "selector_type": "interaction", "page_number": 1, "outcome": "success", "duration_ms": 2145, "retry_count": 1, "confidence": 0.0, "timestamp": "2026-02-06T15:30:02.425Z"}
{"signal_type": "selector_outcome", "tool_name": "web_navigator_agent", "selector": "a[rel='next']", "selector_type": "css", "page_number": 2, "outcome": "failure", "duration_ms": 42, "retry_count": 0, "confidence": 0.0, "timestamp": "2026-02-06T15:30:02.467Z"}
{"signal_type": "selector_outcome", "tool_name": "web_navigator_agent", "selector": "aria-label contains 'next'", "selector_type": "aria", "page_number": 2, "outcome": "failure", "duration_ms": 25, "retry_count": 0, "confidence": 0.0, "timestamp": "2026-02-06T15:30:02.492Z"}
{"signal_type": "selector_outcome", "tool_name": "web_navigator_agent", "selector": "button:'Next'", "selector_type": "text", "page_number": 2, "outcome": "failure", "duration_ms": 71, "retry_count": 0, "confidence": 0.0, "timestamp": "2026-02-06T15:30:02.563Z"}
{"signal_type": "selector_outcome", "tool_name": "web_navigator_agent", "selector": "a:'Next'", "selector_type": "text", "page_number": 2, "outcome": "failure", "duration_ms": 82, "retry_count": 0, "confidence": 0.0, "timestamp": "2026-02-06T15:30:02.645Z"}
{"signal_type": "selector_aggregate", "tool_name": "web_navigator_agent", "execution_id": "nav_1738851000.123", "total_selectors_attempted": 9, "selectors_succeeded": 2, "selectors_failed": 7, "overall_success_rate": 0.2222, "pagination_signals_count": 5, "pagination_success_rate": 0.4, "total_duration_ms": 3359, "average_duration_ms": 373.2, "total_retries": 1, "average_retries": 0.111, "timestamp": "2026-02-06T15:30:02.767Z"}
```

---

## Response Structure (With Learning Metrics)

```python
{
    "status": "COMPLETED",
    "data": {
        "page_title": "Product Directory - Page 2",
        "page_url": "https://example.com/?page=2",
        "page_type": "directory",
        "items": [
            {"name": "Product A", "url": "https://example.com/prod-a", "category": "electronics"},
            {"name": "Product B", "url": "https://example.com/prod-b", "category": "electronics"},
            # ... more items ...
        ],
        "structure": {
            "total_items": 10,
            "pages_extracted": 2
        }
    },
    "metadata": {
        "execution_id": "nav_1738851000.123",
        "duration_ms": 15240,
        "items_extracted": 10,
        "url": "https://example.com",
        "page_type": "directory",
        "execution_mode": "DRY_RUN",
        
        # === PAGINATION METADATA (Step 2) ===
        "pages_visited": 2,
        "pagination_detected": true,
        "pagination_method": "text_match",
        "pagination_stopped_reason": "no_next",
        
        # === LEARNING METRICS (Step 3) ===
        "selectors_attempted": 9,
        "selectors_succeeded": 2,
        "selector_success_rate": 0.2222
    }
}
```

---

## Complete Agent Code (Steps 1-3)

See [WEBNAVIGATOR_README.md](WEBNAVIGATOR_README.md) for full implementation.

**Key methods:**
- `run(input_payload)` — Main entry point
- `_detect_pagination()` — 4 detection strategies with signals
- `_go_to_next_page(element)` — Navigation with signals
- `_paginate_and_extract()` — Multi-page extraction
- `_emit_selector_signal()` — Emit individual signal
- `_emit_aggregate_signals()` — Emit summary signal
- `_compute_learning_metrics()` — Compute statistics
- `_flush_selector_signals()` — Persist to JSONL

---

## Learning Signal Files

### Individual Selector Signals

**Location:** `backend/outputs/phase25/learning_signals.jsonl`

**Purpose:** Record every selector attempt with outcome and timing

**Example Query:**
```bash
# Show all pagination detection failures
cat learning_signals.jsonl | jq 'select(.signal_type=="selector_outcome" and .outcome=="failure" and (.selector_type=="css" or .selector_type=="aria"))'

# Show selector success rate per page
cat learning_signals.jsonl | jq 'select(.signal_type=="selector_outcome") | {page: .page_number, selector: .selector, outcome: .outcome}'
```

### Aggregate Summary Signal

**Emitted at:** End of `run()` execution

**Contains:**
```python
{
    "signal_type": "selector_aggregate",
    "total_selectors_attempted": 9,
    "selectors_succeeded": 2,
    "overall_success_rate": 0.2222,
    "pagination_success_rate": 0.4,
    "average_duration_ms": 373.2,
    "average_retries": 0.111
}
```

---

## Instrumentation Points

### `_detect_pagination()` — 4 Strategies

| Strategy | Selector | Signal Type | Attempts |
|----------|----------|-------------|----------|
| 1. HTML5 next link | `a[rel='next']` | css | 1 |
| 2. ARIA label | `//*[aria-label contains 'next']` | aria | 1 |
| 3. Text patterns | `button/a with text='Next'` | text | 6+ |
| 4. Page numbers | `a with numeric text` | page_number | 1 |

**Total signals per call:** 4-8 (depends on DOM)

### `_go_to_next_page()` — Navigation

| Signal | Type | Tracked |
|--------|------|---------|
| Click attempt | interaction | ✅ Success/failure |
| Retry count | interaction | ✅ 0-3 attempts |
| URL verification | interaction | ✅ Post-click check |
| Content change | interaction | ✅ MD5 hash comparison |

### Per-Page Context

Each signal includes:
```python
"page_number": 1,  # Current page in pagination loop
"timestamp": "ISO-8601",  # When signal was emitted
"duration_ms": 87,  # How long the operation took
"retry_count": 1  # Number of retry attempts
```

---

## Phase 1 Complete: What We Know

By end of Step 3, WebNavigatorAgent can truthfully report:

✅ **Which selectors were attempted**
```
a[rel='next']
aria-label contains 'next'
button text='Next'
a text='Next'
page number links
```

✅ **Which ones worked**
```
a text='Next' on page 1 → success
pagination_element.click() on page 1 → success
```

✅ **How fast they ran**
```
Average selector detection: 373ms
Average interaction time: 2145ms
```

✅ **Reliability metrics**
```
Overall success rate: 22.2%
Pagination success rate: 40%
```

✅ **Without changing behavior**
```
Same 4 detection strategies
Same priority order
Same retry logic
Same extraction patterns
```

---

## Phase 1 Step 3: NOT Doing (Yet)

❌ No selector ranking (will be Step 4)
❌ No adaptive strategy switching (will be Step 5)
❌ No confidence adjustments (will be Step 6)
❌ No dynamic retries based on history (will be Step 7)
❌ No behavioral changes whatsoever (only measurement)

---

## Next Steps (When Requested)

### Phase 1 Step 4: Selector Ranking
Use learning signals to identify most reliable selectors.

### Phase 1 Step 5: Dynamic Adaptation
Adjust detection order based on success history.

### Phase 1 Step 6: Filter Generalization
Extend learning to filter detection and interaction.

### Phase 1 Step 7: GoHighLevel Integration
Emit signals to external learning system.

---

## Testing Learning Signals

### 1. Single-Page Test
```python
result = agent.run({
    "target_url": "https://example.com",
    "max_pages": 1
})
# Expected: No signals emitted (single page mode)
```

### 2. Multi-Page Test
```python
result = agent.run({
    "target_url": "https://paginated-site.com",
    "max_pages": 3
})
# Expected: 4-8 signals per page + 1 aggregate signal
```

### 3. Verify JSONL
```bash
ls -la backend/outputs/phase25/learning_signals.jsonl
wc -l backend/outputs/phase25/learning_signals.jsonl  # Count signals
tail -5 backend/outputs/phase25/learning_signals.jsonl  # Show last signals
```

### 4. Parse Signals
```bash
# Show all selector outcomes
jq 'select(.signal_type=="selector_outcome")' learning_signals.jsonl

# Show success count
jq -s '[.[] | select(.signal_type=="selector_outcome" and .outcome=="success")] | length' learning_signals.jsonl
```

---

## Files Modified (Step 3)

### `backend/agents/web_navigator_agent.py`
- Added: `_emit_selector_signal()`
- Added: `_emit_aggregate_signals()`
- Added: `_compute_learning_metrics()`
- Added: `_flush_selector_signals()`
- Added: `_persist_learning_signal()`
- Modified: `_detect_pagination()` — Added signal emission
- Modified: `_go_to_next_page()` — Added signal emission
- Modified: `_paginate_and_extract()` — Added page tracking
- Modified: `run()` — Initialize signals, emit at end, include metrics

### `backend/agents/__init__.py`
- Unchanged (already exports WebNavigatorAgent)

### Core Files
- `buddys_vision_core.py` — ✅ UNCHANGED
- `buddys_arms.py` — ✅ UNCHANGED
- `phase25_orchestrator.py` — ✅ UNCHANGED

---

## Documentation Files

| File | Purpose | Status |
|------|---------|--------|
| [SELENIUM_CAPABILITY_AUDIT.md](SELENIUM_CAPABILITY_AUDIT.md) | Phase 1 foundation audit | ✅ Complete |
| [PHASE1_STEP1_COMPLETE.md](PHASE1_STEP1_COMPLETE.md) | Wrapper agent (Step 1) | ✅ Complete |
| [PHASE1_STEP2_COMPLETE.md](PHASE1_STEP2_COMPLETE.md) | Pagination (Step 2) | ✅ Complete |
| [PHASE1_STEP3_COMPLETE.md](PHASE1_STEP3_COMPLETE.md) | Learning signals (Step 3) | ✅ Complete |
| [WEBNAVIGATOR_README.md](WEBNAVIGATOR_README.md) | Full code + examples | ✅ Complete |
| This file | Steps 1-3 combined reference | ✅ Complete |

---

**PHASE 1 · STEPS 1-3 COMPLETE** ✅

