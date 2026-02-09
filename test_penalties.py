"""Test penalties and adjustments"""
from backend.tool_selector import tool_selector
from backend.memory_manager import memory_manager
from backend.feedback_manager import feedback_manager

goal = "What is the current time?"
domain = "_global"

# Check memory learnings
learnings = memory_manager.summarize_learnings(goal, domain=domain)
print("Memory learnings:")
print(f"  tools_to_avoid: {learnings.get('tools_to_avoid', [])}")

# Check feedback adjustments
for tool in ['get_time', 'calculate', 'web_search']:
    multiplier, constraint, matched = feedback_manager.get_tool_adjustment(goal, tool, domain)
    if matched:
        print(f"  {tool}: multiplier={multiplier}, constraint={constraint}")
