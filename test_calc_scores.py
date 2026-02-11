from Back_End.tool_registry import tool_registry
from Back_End.tools import register_foundational_tools, register_code_awareness_tools
from Back_End.additional_tools import register_additional_tools
from Back_End.tool_performance import tracker

register_foundational_tools(tool_registry)
register_additional_tools(tool_registry)
register_code_awareness_tools(tool_registry)

goal = 'What is 100-10?'
domain = '_global'

# Check pattern scores
from Back_End.tool_selector import tool_selector
pattern_scores = tool_selector.analyze_goal(goal)
print(f"Pattern scores: {pattern_scores}")

# Check performance scores
perf_scores = {}
for tool_name in tool_registry.tools.keys():
    perf_scores[tool_name] = tracker.get_usefulness_score(tool_name, domain)
print(f"Performance scores: {perf_scores}")

# Calculate final scores
final_scores = {}
for tool_name in tool_registry.tools.keys():
    pattern_conf = pattern_scores.get(tool_name, 0.0)
    perf_conf = perf_scores.get(tool_name, 0.5)
    final_scores[tool_name] = (pattern_conf * 0.8) + (perf_conf * 0.2)

print(f"Final scores: {final_scores}")
print(f"Max score: {max(final_scores.values())}")
print(f"Threshold: 0.15")

