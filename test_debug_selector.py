from backend.tool_selector import tool_selector
from backend.tool_registry import tool_registry

goal = "search for best practices"

# Step-by-step debug
print(f"Goal: {goal}\n")

# 1. Pattern scores
pattern_scores = tool_selector.analyze_goal(goal)
print("1. Pattern Scores:")
for tool, score in sorted(pattern_scores.items(), key=lambda x: x[1], reverse=True):
    if score > 0:
        print(f"   {tool}: {score:.2f}")

# 2. Performance scores
print("\n2. Performance Scores:")
for tool_name in list(tool_registry.tools.keys())[:3]:
    perf = tool_selector.get_tool_usefulness(tool_name)
    print(f"   {tool_name}: {perf:.2f}")

# 3. Combined scores
print("\n3. Combined Scores (80% pattern + 20% performance):")
for tool_name in list(tool_registry.tools.keys())[:3]:
    pattern = pattern_scores.get(tool_name, 0.0)
    perf = tool_selector.get_tool_usefulness(tool_name)
    combined = (pattern * 0.8) + (perf * 0.2)
    print(f"   {tool_name}: ({pattern:.2f} * 0.8) + ({perf:.2f} * 0.2) = {combined:.2f}")

# 4. Final selection
tool_name, tool_input, confidence = tool_selector.select_tool(goal)
print(f"\n4. Final Selection:")
print(f"   Tool: {tool_name}")
print(f"   Input: {tool_input}")
print(f"   Confidence: {confidence:.2f}")
