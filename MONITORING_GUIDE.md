# Phase 2 Continuous Monitoring Guide

## Overview

The Phase 2 continuous monitoring system automatically runs synthetic tests at regular intervals and tracks metrics over time, alerting you if any metric falls outside expected ranges.

## Quick Start

### Option 1: Default Settings (10 min intervals, 10 cycles)
```bash
python phase2_continuous_monitor.py
```

### Option 2: Custom Settings
```bash
python phase2_continuous_monitor.py --interval 15 --max-runs 20
```

### Option 3: Quick Test (1 min intervals, 5 cycles)
```bash
python phase2_continuous_monitor.py --interval 1 --max-runs 5
```

## What It Does

1. **Runs Synthetic Tests**: Executes `phase2_synthetic_harness.py` every N minutes
2. **Collects Metrics**: Tracks confidence, pre-validation, approval rates, latency
3. **Detects Anomalies**: Alerts if metrics fall outside expected ranges
4. **Tracks Trends**: Shows how metrics change over time
5. **Saves History**: Stores results in `phase2_monitoring_history.json`

## Metrics Monitored

| Metric | Target Range | Alert Condition |
|--------|-------------|-----------------|
| **Confidence σ** | >0.20 | If <0.20 (bimodal) |
| **Pre-Val Catch** | >80% | If <80% |
| **Approval Rate** | 10-30% | If <10% or >30% |
| **Latency** | <50ms | If >50ms per goal |

## Example Output

```
================================================================================
TEST CYCLE: 2026-02-05 12:00:00
================================================================================
Running synthetic tests...

Results:
  Goals Tested: 500
  Elapsed Time: 0.20s
  Latency: 0.40ms/goal

  Confidence σ: 0.314 ✅
  Pre-Val Catch: 100.0% ✅
  Approval Rate: 8.0% ⚠️
  Clarification: 2.0%

  ANOMALIES DETECTED:
    ⚠️  Approval rate too low: 8.0% < 10.0%

================================================================================
TREND SUMMARY (Last 3 cycles)
================================================================================

Metric Trends:
  confidence_std_dev:
    📈 Current: 0.314, Avg: 0.318, Range: [0.310, 0.325]
  pre_validation_catch_rate:
    ➡️ Current: 100.0, Avg: 100.0, Range: [100.0, 100.0]
  approval_rate:
    📉 Current: 8.0, Avg: 8.5, Range: [8.0, 9.2]

  Total Anomalies: 3
  ⚠️  3 anomalies detected - review required

💾 History saved to: phase2_monitoring_history.json

⏳ Waiting 10 minutes until next cycle...
   Next cycle at: 12:10:00
```

## Stopping the Monitor

Press `Ctrl+C` to stop monitoring. The system will save the history before exiting.

## Reviewing History

The monitoring history is saved in `phase2_monitoring_history.json`. You can review it with:

```bash
python -c "import json; print(json.dumps(json.load(open('phase2_monitoring_history.json')), indent=2))"
```

## Recommended Usage

### During Staging (Week 1)
```bash
# Run every 15 minutes, unlimited cycles
python phase2_continuous_monitor.py --interval 15 --max-runs 999
```

### During Production Validation
```bash
# Run every 30 minutes, 48 cycles (24 hours)
python phase2_continuous_monitor.py --interval 30 --max-runs 48
```

### Quick Sanity Check
```bash
# Run every 1 minute, 5 cycles (5 minutes total)
python phase2_continuous_monitor.py --interval 1 --max-runs 5
```

## Alert Response Guide

### ⚠️  Confidence σ Too Low (<0.20)
**Cause**: Confidence distribution is bimodal (not graded)  
**Action**: 
1. Check confidence calculation weights
2. Verify ConfidenceFactors are being calculated correctly
3. Review goal diversity in test harness

### ⚠️  Pre-Val Catch Rate Low (<80%)
**Cause**: Pre-validation not catching failure-injected goals  
**Action**:
1. Check pre-validation logic
2. Verify failure-injected goals are sufficiently "bad"
3. Review pre-validation thresholds

### ⚠️  Approval Rate Out of Range (<10% or >30%)
**Cause**: Confidence thresholds may need tuning  
**Action**:
1. If <10%: Lower HIGH_CONFIDENCE_THRESHOLD (e.g., 0.85 → 0.80)
2. If >30%: Raise MEDIUM_CONFIDENCE_THRESHOLD (e.g., 0.55 → 0.60)
3. Review goal distribution in test harness

### ⚠️  Latency Too High (>50ms)
**Cause**: Performance degradation  
**Action**:
1. Check system load (CPU, memory)
2. Profile pre-validation and confidence calculation
3. Look for I/O bottlenecks

## Files Generated

- `phase2_monitoring_history.json` - Complete history of all test cycles
- `phase2_test_report.json` - Latest synthetic test report (overwritten each cycle)

## Tips

1. **Long-term monitoring**: Use `screen` or `tmux` to keep monitor running in background
2. **Alert integration**: Pipe output to monitoring system (e.g., Datadog, Prometheus)
3. **Custom thresholds**: Edit `self.thresholds` in `Phase2ContinuousMonitor.__init__`
4. **Historical analysis**: Parse `phase2_monitoring_history.json` for trends

## Troubleshooting

### Monitor Crashes
Check `phase2_monitoring_history.json` for last successful cycle. Resume monitoring.

### Test Harness Fails
Monitor will log error and continue to next cycle. Check synthetic harness independently.

### Out of Disk Space
Monitor saves history each cycle. Ensure sufficient disk space (each cycle ~500KB).

---

**For questions or issues, refer to**: [PHASE2_STAGING_EXECUTIVE_SUMMARY.md](PHASE2_STAGING_EXECUTIVE_SUMMARY.md)
