#!/usr/bin/env python
"""Test selector signal persistence"""

from backend.phase25_orchestrator import Phase25Orchestrator
from datetime import datetime, timezone

# Create orchestrator
orch = Phase25Orchestrator()

# Test dict-based signal (Phase 1 selector signals)
selector_signal = {
    'signal_type': 'selector_outcome',
    'tool_name': 'web_navigator_agent',
    'selector': 'a[rel="next"]',
    'selector_type': 'css',
    'page_number': 1,
    'outcome': 'success',
    'duration_ms': 150,
    'retry_count': 0,
    'confidence': 0.0,
    'timestamp': datetime.now(timezone.utc).isoformat()
}

print("Testing dict-based signal...")
orch.log_learning_signal(selector_signal)
print("✓ Dict signal written")

# Test parameter-based signal (Phase 25 meta signals)
print("\nTesting parameter-based signal...")
orch.log_learning_signal(
    signal_data="confidence_increase",
    tool_name="test_tool",
    insight="Test insight",
    confidence=0.95,
    recommended_action="Continue"
)
print("✓ Parameter signal written")

print("\n✓ Both signal formats work!")
