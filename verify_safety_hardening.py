#!/usr/bin/env python
"""Verify safety hardening tags are injected correctly"""

import json
from pathlib import Path
from Back_End.phase25_orchestrator import Phase25Orchestrator
from datetime import datetime, timezone

# Clean output file
output_file = Path("outputs/phase25/learning_signals.jsonl")
output_file.parent.mkdir(parents=True, exist_ok=True)
if output_file.exists():
    output_file.unlink()

orch = Phase25Orchestrator()

print("=" * 60)
print("TESTING SAFETY HARDENING")
print("=" * 60)

# Test 1: Selector signal WITHOUT tags (should be injected)
print("\n[TEST 1] Selector signal without safety tags")
signal_no_tags = {
    'signal_type': 'selector_outcome',
    'tool_name': 'web_navigator_agent',
    'selector': 'a[rel="next"]',
    'outcome': 'success',
    'duration_ms': 120,
    'timestamp': datetime.now(timezone.utc).isoformat()
}
orch.log_learning_signal(signal_no_tags)
print("  ✓ Written")

# Test 2: Selector signal WITH tags (should be preserved)
print("\n[TEST 2] Selector signal with explicit tags")
signal_with_tags = {
    'signal_type': 'selector_outcome',
    'signal_layer': 'custom_layer',
    'signal_source': 'custom_source',
    'selector': 'button.next',
    'outcome': 'failure',
    'duration_ms': 200,
    'timestamp': datetime.now(timezone.utc).isoformat()
}
orch.log_learning_signal(signal_with_tags)
print("  ✓ Written")

# Test 3: Phase25 meta signal (should be unchanged)
print("\n[TEST 3] Phase25 meta signal")
orch.log_learning_signal(
    signal_data="confidence_increase",
    tool_name="test_agent",
    insight="Test Phase25 signal",
    confidence=0.90,
    recommended_action="Continue"
)
print("  ✓ Written")

# Verify results
print("\n" + "=" * 60)
print("VERIFICATION")
print("=" * 60)

with open(output_file, 'r') as f:
    signals = [json.loads(line) for line in f if line.strip()]

print(f"\nTotal signals written: {len(signals)}")

# Check Test 1
print("\n[TEST 1 RESULT]")
s1 = signals[0]
assert s1['signal_type'] == 'selector_outcome', "Wrong signal type"
assert s1['signal_layer'] == 'selector', "❌ signal_layer not injected!"
assert s1['signal_source'] == 'web_navigator', "❌ signal_source not injected!"
print("  ✅ Tags injected: signal_layer='selector', signal_source='web_navigator'")

# Check Test 2
print("\n[TEST 2 RESULT]")
s2 = signals[1]
assert s2['signal_layer'] == 'custom_layer', "❌ Explicit tag overwritten!"
assert s2['signal_source'] == 'custom_source', "❌ Explicit tag overwritten!"
print("  ✅ Explicit tags preserved: signal_layer='custom_layer', signal_source='custom_source'")

# Check Test 3
print("\n[TEST 3 RESULT]")
s3 = signals[2]
assert 'signal_id' in s3, "Missing signal_id"
assert s3['signal_type'] == 'confidence_increase', "Wrong signal type"
assert 'signal_layer' not in s3, "❌ Phase25 signal contaminated!"
assert 'signal_source' not in s3, "❌ Phase25 signal contaminated!"
print("  ✅ Phase25 signal unchanged (no selector tags)")

print("\n" + "=" * 60)
print("✅ ALL TESTS PASSED - SAFETY HARDENING VERIFIED")
print("=" * 60)

