#!/usr/bin/env python3
"""
Test human feedback injection and application.
"""

import sys
sys.path.insert(0, '.')

from backend.feedback_manager import feedback_manager
from backend.memory import memory


def _clear_memory_safe():
    try:
        if hasattr(memory, 'data'):
            memory.data.clear()
    except Exception:
        pass


def test_feedback_penalty():
    print("\n=== Testing Feedback Penalty ===\n")
    _clear_memory_safe()
    feedback_manager.submit_feedback(
        goal_pattern="marketing campaign",
        tool="web_search",
        domain="marketing",
        verdict="negative",
        reason="Too generic",
        action="penalize",
        impact={"tool_adjustment": 0.5, "penalty_duration": "permanent", "hard_constraint": None},
    )

    multiplier, constraint, matched = feedback_manager.get_tool_adjustment(
        "Design a marketing campaign", "web_search", "marketing"
    )

    assert multiplier == 0.5
    assert constraint is None
    assert len(matched) >= 1
    print("✓ Feedback penalty applied")


def test_feedback_constraint():
    print("\n=== Testing Feedback Constraint ===\n")
    _clear_memory_safe()
    feedback_manager.submit_feedback(
        goal_pattern="marketing campaign",
        tool="web_search",
        domain="marketing",
        verdict="negative",
        reason="Disallowed",
        action="constraint",
        impact={"tool_adjustment": 0.0, "penalty_duration": "permanent", "hard_constraint": "never_use_for_marketing"},
    )

    multiplier, constraint, matched = feedback_manager.get_tool_adjustment(
        "Design a marketing campaign", "web_search", "marketing"
    )

    assert multiplier == 0.0
    assert constraint == "never_use_for_marketing"
    assert len(matched) >= 1
    print("✓ Feedback constraint applied")


if __name__ == '__main__':
    print("=" * 60)
    print("HUMAN FEEDBACK TEST SUITE")
    print("=" * 60)

    test_feedback_penalty()
    test_feedback_constraint()

    print("\n" + "=" * 60)
    print("✓ All feedback tests completed!")
    print("=" * 60)
