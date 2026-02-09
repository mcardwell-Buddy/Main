#!/usr/bin/env python
"""Generate comprehensive test data for selector ranking"""

import json
from pathlib import Path
from datetime import datetime, timezone

# Clear existing test signals
output_file = Path("outputs/phase25/learning_signals.jsonl")
output_file.parent.mkdir(parents=True, exist_ok=True)
if output_file.exists():
    output_file.unlink()

# Generate diverse selector signals
test_signals = [
    # Selector 1: a[rel='next'] - Perfect performance
    {"signal_type": "selector_outcome", "signal_layer": "selector", "signal_source": "web_navigator",
     "selector": "a[rel='next']", "selector_type": "css", "page_number": 1, "outcome": "success",
     "duration_ms": 120, "retry_count": 0, "timestamp": datetime.now(timezone.utc).isoformat()},
    {"signal_type": "selector_outcome", "signal_layer": "selector", "signal_source": "web_navigator",
     "selector": "a[rel='next']", "selector_type": "css", "page_number": 2, "outcome": "success",
     "duration_ms": 135, "retry_count": 0, "timestamp": datetime.now(timezone.utc).isoformat()},
    {"signal_type": "selector_outcome", "signal_layer": "selector", "signal_source": "web_navigator",
     "selector": "a[rel='next']", "selector_type": "css", "page_number": 3, "outcome": "success",
     "duration_ms": 125, "retry_count": 0, "timestamp": datetime.now(timezone.utc).isoformat()},
    
    # Selector 2: .next-button - High success with retries
    {"signal_type": "selector_outcome", "signal_layer": "selector", "signal_source": "web_navigator",
     "selector": ".next-button", "selector_type": "css", "page_number": 1, "outcome": "success",
     "duration_ms": 200, "retry_count": 1, "timestamp": datetime.now(timezone.utc).isoformat()},
    {"signal_type": "selector_outcome", "signal_layer": "selector", "signal_source": "web_navigator",
     "selector": ".next-button", "selector_type": "css", "page_number": 2, "outcome": "success",
     "duration_ms": 180, "retry_count": 0, "timestamp": datetime.now(timezone.utc).isoformat()},
    {"signal_type": "selector_outcome", "signal_layer": "selector", "signal_source": "web_navigator",
     "selector": ".next-button", "selector_type": "css", "page_number": 3, "outcome": "success",
     "duration_ms": 190, "retry_count": 1, "timestamp": datetime.now(timezone.utc).isoformat()},
    {"signal_type": "selector_outcome", "signal_layer": "selector", "signal_source": "web_navigator",
     "selector": ".next-button", "selector_type": "css", "page_number": 4, "outcome": "success",
     "duration_ms": 195, "retry_count": 0, "timestamp": datetime.now(timezone.utc).isoformat()},
    
    # Selector 3: //a[contains(text(),'Next')] - XPath with some failures
    {"signal_type": "selector_outcome", "signal_layer": "selector", "signal_source": "web_navigator",
     "selector": "//a[contains(text(),'Next')]", "selector_type": "xpath", "page_number": 1, "outcome": "success",
     "duration_ms": 250, "retry_count": 0, "timestamp": datetime.now(timezone.utc).isoformat()},
    {"signal_type": "selector_outcome", "signal_layer": "selector", "signal_source": "web_navigator",
     "selector": "//a[contains(text(),'Next')]", "selector_type": "xpath", "page_number": 2, "outcome": "failure",
     "duration_ms": 300, "retry_count": 2, "timestamp": datetime.now(timezone.utc).isoformat()},
    {"signal_type": "selector_outcome", "signal_layer": "selector", "signal_source": "web_navigator",
     "selector": "//a[contains(text(),'Next')]", "selector_type": "xpath", "page_number": 3, "outcome": "success",
     "duration_ms": 240, "retry_count": 1, "timestamp": datetime.now(timezone.utc).isoformat()},
    {"signal_type": "selector_outcome", "signal_layer": "selector", "signal_source": "web_navigator",
     "selector": "//a[contains(text(),'Next')]", "selector_type": "xpath", "page_number": 4, "outcome": "success",
     "duration_ms": 260, "retry_count": 0, "timestamp": datetime.now(timezone.utc).isoformat()},
    
    # Selector 4: #pagination-next - Slow but reliable
    {"signal_type": "selector_outcome", "signal_layer": "selector", "signal_source": "web_navigator",
     "selector": "#pagination-next", "selector_type": "css", "page_number": 1, "outcome": "success",
     "duration_ms": 400, "retry_count": 0, "timestamp": datetime.now(timezone.utc).isoformat()},
    {"signal_type": "selector_outcome", "signal_layer": "selector", "signal_source": "web_navigator",
     "selector": "#pagination-next", "selector_type": "css", "page_number": 2, "outcome": "success",
     "duration_ms": 420, "retry_count": 0, "timestamp": datetime.now(timezone.utc).isoformat()},
    
    # Selector 5: .page-next - Poor performance
    {"signal_type": "selector_outcome", "signal_layer": "selector", "signal_source": "web_navigator",
     "selector": ".page-next", "selector_type": "css", "page_number": 1, "outcome": "failure",
     "duration_ms": 500, "retry_count": 3, "timestamp": datetime.now(timezone.utc).isoformat()},
    {"signal_type": "selector_outcome", "signal_layer": "selector", "signal_source": "web_navigator",
     "selector": ".page-next", "selector_type": "css", "page_number": 2, "outcome": "success",
     "duration_ms": 450, "retry_count": 2, "timestamp": datetime.now(timezone.utc).isoformat()},
    {"signal_type": "selector_outcome", "signal_layer": "selector", "signal_source": "web_navigator",
     "selector": ".page-next", "selector_type": "css", "page_number": 3, "outcome": "failure",
     "duration_ms": 480, "retry_count": 3, "timestamp": datetime.now(timezone.utc).isoformat()},
    
    # Add some Phase25 meta signals (should be ignored)
    {"signal_id": "sig_test_001", "signal_type": "confidence_increase", "tool_name": "test_tool",
     "insight": "Test insight", "confidence": 0.9, "recommended_action": "Continue",
     "timestamp": datetime.now(timezone.utc).isoformat()},
    {"signal_id": "sig_test_002", "signal_type": "efficiency_gain", "tool_name": "test_tool",
     "insight": "Another insight", "confidence": 0.85, "recommended_action": "Continue",
     "timestamp": datetime.now(timezone.utc).isoformat()},
]

# Write signals
with open(output_file, 'w') as f:
    for signal in test_signals:
        f.write(json.dumps(signal) + '\n')

print(f"✓ Generated {len(test_signals)} test signals")
print(f"  - {sum(1 for s in test_signals if s.get('signal_layer') == 'selector')} selector signals")
print(f"  - {sum(1 for s in test_signals if 'signal_id' in s)} Phase25 meta signals")
print(f"\nWritten to: {output_file}")
