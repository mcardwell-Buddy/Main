# Learning Module: Observe-Only Mode - Quick Reference

## Status
✅ **COMPLETE** - Learning signals are being emitted without affecting execution behavior

## Where Learning is Invoked

### Location: `backend/execution_service.py`

**Step 9.5** (Line ~312-330)
- **When:** After successful execution, before return
- **Timing:** Execution complete, result logged
- **Guarantee:** Learning cannot affect outcome

**Step 5.5 Failure Path** (Line ~270-285)
- **When:** After tool validation failure, before return
- **Timing:** Execution decision made, failure logged
- **Guarantee:** Learning cannot change failure

## Sample Learning Record

```json
{
  "signal_type": "execution_outcome",
  "signal_layer": "execution",
  "signal_source": "execution_service",
  "timestamp": "2026-02-08T14:27:04.580991+00:00",
  "data": {
    "mission_id": "test_content_1770560824562",
    "objective": "Calculate 25 * 4",
    "intent": "calculation",
    "tool_used": "calculate",
    "tool_confidence": 0.708,
    "success": true,
    "result_preview": {
      "result": "42",
      "expression": "25*4"
    }
  }
}
```

**File:** `outputs/phase25/execution_learning_signals.jsonl`

## Proof: Execution Behavior Unchanged

### Test Results

```bash
python test_learning_observe_only.py
```

**Output:**
- ✅ PASS: Learning Signal Emission (1 signal per execution)
- ✅ PASS: Execution Invariants with Learning (all 3 pass)
- ✅ PASS: Learning Signal Content (all fields present)

```bash
python test_execution_direct.py
```

**Output:**
- ✅ INVARIANT 1 PASSED: Proposed missions do NOT execute
- ✅ INVARIANT 2 PASSED: Approved missions execute exactly once
- ✅ INVARIANT 3 PASSED: Execution does NOT re-run

## What Learning Does NOT Do

❌ Does NOT read signals  
❌ Does NOT affect tool selection  
❌ Does NOT affect execution decisions  
❌ Does NOT affect approval  
❌ Does NOT retry executions  
❌ Does NOT modify whiteboard  
❌ Does NOT block execution  

## Files Modified

**New:**
- `backend/execution_learning_emitter.py` (~120 lines)
- `test_learning_observe_only.py` (~350 lines)

**Modified:**
- `backend/execution_service.py` (+40 lines)

## Quick Verification

```powershell
# View learning signals
Get-Content outputs\phase25\execution_learning_signals.jsonl | ConvertFrom-Json | Select-Object -First 5

# Count signals
(Get-Content outputs\phase25\execution_learning_signals.jsonl).Count

# Run tests
python test_learning_observe_only.py
python test_execution_direct.py
```

## Next Steps

With learning signals now being emitted:
- Can analyze tool selection accuracy
- Can track confidence vs. success correlation
- Can identify patterns in failures
- Can collect training data for ML models

**Note:** All analysis is future work. Currently write-only, observe-only mode.
