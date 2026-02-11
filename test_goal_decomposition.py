#!/usr/bin/env python3
"""
Test goal decomposition and composite goal execution.
"""

import sys
sys.path.insert(0, '.')

from Back_End.goal_decomposer import goal_decomposer
from Back_End.composite_agent import execute_goal
from Back_End.config import Config
from Back_End.memory import memory


def _clear_memory_safe():
    try:
        if hasattr(memory, 'data'):
            memory.data.clear()
    except Exception:
        pass


def test_classification_atomic():
    print("\n=== Testing Atomic Classification ===\n")
    goal = "Summarize latest AI news"
    classification = goal_decomposer.classify_goal(goal)
    assert classification["is_composite"] is False
    assert classification["total_subgoals"] == 0
    print("✓ Atomic classification passed")


def test_classification_composite():
    print("\n=== Testing Composite Classification ===\n")
    goal = "Design and launch a marketing campaign"
    classification = goal_decomposer.classify_goal(goal)
    assert classification["is_composite"] is True
    assert 1 <= classification["total_subgoals"] <= 4
    print(f"✓ Composite classification passed ({classification['total_subgoals']} subgoals)")


def test_decomposition_constraints():
    print("\n=== Testing Decomposition Constraints ===\n")
    goal = "Compare marketing and crypto growth"
    subgoals = goal_decomposer.decompose(goal)
    assert len(subgoals) <= 4
    assert all(sg.get("goal") for sg in subgoals)
    print(f"✓ Decomposition constraints passed ({len(subgoals)} subgoals)")


def test_execute_atomic():
    print("\n=== Testing Atomic Execution ===\n")
    _clear_memory_safe()
    goal = "Check latest technology trends"
    result = execute_goal(goal)
    assert result["goal_type"] == "atomic"
    assert result["goal"] == goal
    assert 0 <= result["final_confidence"] <= 1.0
    assert result["total_steps"] <= Config.MAX_AGENT_STEPS
    print(f"✓ Atomic execution passed ({result['total_steps']} steps)")


def test_execute_composite():
    print("\n=== Testing Composite Execution ===\n")
    _clear_memory_safe()
    goal = "Plan and then analyze a product launch"
    result = execute_goal(goal)
    assert result["goal_type"] == "composite"
    assert result["original_goal"] == goal
    assert 1 <= result["total_subgoals"] <= 4
    assert len(result["subgoal_results"]) == result["total_subgoals"]
    assert 0 <= result["final_confidence"] <= 1.0
    assert result["total_steps"] >= result["total_subgoals"]
    print(f"✓ Composite execution passed ({result['total_subgoals']} subgoals)")


if __name__ == '__main__':
    print("=" * 60)
    print("GOAL DECOMPOSITION TEST SUITE")
    print("=" * 60)

    test_classification_atomic()
    test_classification_composite()
    test_decomposition_constraints()
    test_execute_atomic()
    test_execute_composite()

    print("\n" + "=" * 60)
    print("✓ All goal decomposition tests completed!")
    print("=" * 60)

