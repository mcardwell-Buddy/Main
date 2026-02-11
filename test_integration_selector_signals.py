#!/usr/bin/env python
"""Integration test: Simulate web_navigator_agent selector signal flow"""

import json
from pathlib import Path
from Back_End.phase25_orchestrator import Phase25Orchestrator
from datetime import datetime, timezone

# Clean output
output_file = Path("outputs/phase25/learning_signals.jsonl")
if output_file.exists():
    output_file.unlink()

print("=" * 70)
print("INTEGRATION TEST: Web Navigator Agent Selector Signal Flow")
print("=" * 70)

# Simulate what web_navigator_agent._emit_selector_signal() creates
def simulate_agent_selector_signal():
    """Simulate exact signal structure from web_navigator_agent"""
    return {
        "signal_type": "selector_outcome",
        "tool_name": "web_navigator_agent",
        "selector": "a[rel='next']",
        "selector_type": "css",
        "page_number": 2,
        "outcome": "success",
        "duration_ms": 145,
        "retry_count": 0,
        "confidence": 0.0,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

# Initialize orchestrator (as done in web_navigator_agent.__init__)
orch = Phase25Orchestrator()

# Emit 3 selector signals (as happens during pagination)
print("\n📊 Emitting 3 selector signals from web_navigator_agent...")
for i in range(1, 4):
    signal = simulate_agent_selector_signal()
    signal['page_number'] = i
    signal['duration_ms'] = 100 + (i * 15)
    orch.log_learning_signal(signal)  # This is what _persist_learning_signal() calls
    print(f"  ✓ Selector signal {i} emitted (page {i})")

# Read back and verify
print("\n🔍 Verifying signals in learning_signals.jsonl...")
with open(output_file, 'r') as f:
    signals = [json.loads(line) for line in f if line.strip()]

print(f"\nTotal signals: {len(signals)}")

all_tagged = True
for idx, sig in enumerate(signals, 1):
    has_layer = 'signal_layer' in sig
    has_source = 'signal_source' in sig
    layer_val = sig.get('signal_layer')
    source_val = sig.get('signal_source')
    
    status = "✅" if (has_layer and has_source) else "❌"
    print(f"\n  Signal {idx}:")
    print(f"    signal_type: {sig.get('signal_type')}")
    print(f"    page_number: {sig.get('page_number')}")
    print(f"    signal_layer: {layer_val} {status}")
    print(f"    signal_source: {source_val} {status}")
    
    if not (has_layer and has_source and layer_val == 'selector' and source_val == 'web_navigator'):
        all_tagged = False

print("\n" + "=" * 70)
if all_tagged:
    print("✅ SUCCESS: All selector signals properly tagged!")
    print("   - signal_layer='selector'")
    print("   - signal_source='web_navigator'")
else:
    print("❌ FAILURE: Some signals missing safety tags")
print("=" * 70)

