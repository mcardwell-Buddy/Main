#!/usr/bin/env python3
"""Quick test of tool selection fix"""

import sys
sys.path.insert(0, '.')

from backend.tool_selector import ToolSelector

ts = ToolSelector()

test_goals = [
    "What is the current time?",
    "Get current time",
    "Show me today's date",
    "Calculate 5 + 10",
]

print("Testing tool selection:")
print("=" * 60)

for goal in test_goals:
    scores = ts.analyze_goal(goal)
    top_tools = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
    
    print(f"\nGoal: {goal}")
    print(f"Top 3 tools:")
    for tool, score in top_tools:
        if score > 0:
            print(f"  {tool}: {score:.2f}")
    
    # Simulate actual selection
    tool_name, tool_input, confidence = ts.select_tool(goal, context={'domain': '_global'})
    print(f"Selected: {tool_name} (confidence: {confidence:.2f})")

print("\n" + "=" * 60)
