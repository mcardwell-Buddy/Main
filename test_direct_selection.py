"""Test tool selection directly with verbose output"""
import logging
logging.basicConfig(level=logging.DEBUG)

# Import and register tools FIRST
from backend.tool_registry import tool_registry
from backend.tools import register_foundational_tools, register_code_awareness_tools
from backend.additional_tools import register_additional_tools

register_foundational_tools(tool_registry)
register_additional_tools(tool_registry)
register_code_awareness_tools(tool_registry)

print(f"Registered tools: {list(tool_registry.tools.keys())}\n")

from backend.tool_selector import tool_selector
from backend.tool_performance import tracker

goal = "What is the current time?"

# Check performance scores
print("Performance scores:")
for tool in ['get_time', 'calculate', 'web_search']:
    score = tracker.get_usefulness_score(tool, '_global')
    print(f"  {tool}: {score:.2f}")

# Test analyze_goal
scores = tool_selector.analyze_goal(goal)
print(f"\nPattern scores for '{goal}':")
for tool, score in sorted(scores.items(), key=lambda x: x[1], reverse=True)[:5]:
    print(f"  {tool}: {score:.2f}")

# Test select_tool
tool_name, tool_input, confidence = tool_selector.select_tool(
    goal,
    context={'domain': '_global', 'step': 0}
)

print(f"\nselect_tool result:")
print(f"  Tool: {tool_name}")
print(f"  Input: {tool_input}")
print(f"  Confidence: {confidence:.2f}")
