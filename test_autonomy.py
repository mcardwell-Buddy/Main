#!/usr/bin/env python3
"""
Test autonomy manager structures and guardrails.
"""

import sys
sys.path.insert(0, '.')

from Back_End.autonomy_manager import AutonomyManager
from Back_End.memory import memory


def _clear_memory_safe():
    try:
        if hasattr(memory, 'data'):
            memory.data.clear()
    except Exception:
        pass


def test_autonomy_basics():
    print("\n=== Testing Autonomy Basics ===\n")
    _clear_memory_safe()
    mgr = AutonomyManager()
    assert mgr.get_current_level() == 1
    assert mgr.can_tool_execute_at_level("web_search", 1) is True
    print("✓ Autonomy basics passed")


def test_escalation_flow():
    print("\n=== Testing Escalation Flow ===\n")
    _clear_memory_safe()
    mgr = AutonomyManager()
    can, reason, metrics = mgr.evaluate_escalation(2)
    assert can is False
    assert "successful sessions" in reason.lower()

    request = mgr.request_escalation(2, "Testing escalation")
    assert request["status"] == "pending_human_review"

    decision = mgr.approve_escalation(request["id"], approved=False, human_comment="Not yet")
    assert decision["type"] == "autonomy_escalation_denied"

    pending = mgr.list_requests(status="pending_human_review")
    assert len(pending) == 0
    print("✓ Escalation flow passed")


if __name__ == '__main__':
    print("=" * 60)
    print("AUTONOMY TEST SUITE")
    print("=" * 60)

    test_autonomy_basics()
    test_escalation_flow()

    print("\n" + "=" * 60)
    print("✓ All autonomy tests completed!")
    print("=" * 60)

