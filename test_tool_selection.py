from Back_End.tool_selector import tool_selector
from Back_End.tool_registry import tool_registry
from Back_End.tools import register_foundational_tools
from Back_End.additional_tools import register_additional_tools

# Register tools first!
register_foundational_tools(tool_registry)
register_additional_tools(tool_registry)

print("=== Testing Tool Selection for Web Extract ===\n")

test_goal = "Extract all data and content from https://example.com"

print(f"Goal: '{test_goal}'")
print()

# Test intent classification
from Back_End.execution_service import ExecutionService
es = ExecutionService()
intent = es._classify_intent(test_goal)
print(f"Intent Classification: {intent}")
print()

# Get pattern scores
scores = tool_selector.analyze_goal(test_goal)
print("Pattern Scores (top 5):")
for tool, score in sorted(scores.items(), key=lambda x: x[1], reverse=True)[:5]:
    print(f"  {tool}: {score:.2f}")

print()

# Get the actual selected tool
tool_name, tool_input, confidence = tool_selector.select_tool(test_goal)
print(f"Selected tool: {tool_name}")
print(f"Tool input: '{tool_input}'")
print(f"Confidence: {confidence:.2f}")
print()

# Check tool validation
from Back_End.execution_service import INTENT_TOOL_RULES
print(f"Allowed tools for '{intent}' intent: {INTENT_TOOL_RULES.get(intent, [])}")
print(f"Is '{tool_name}' allowed? {tool_name in INTENT_TOOL_RULES.get(intent, [])}")

print("5. Confidence Scoring - Only acts when confident enough")

