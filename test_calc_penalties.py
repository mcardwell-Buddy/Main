from Back_End.memory_manager import memory_manager
from Back_End.feedback_manager import feedback_manager

goal = 'What is 100-10?'
domain = '_global'

# Check learnings
learnings = memory_manager.summarize_learnings(goal, domain=domain)
print(f"Memory learnings: {learnings}")

# Check feedback
for tool in ['calculate', 'web_search', 'get_time']:
    mult, constraint, matched = feedback_manager.get_tool_adjustment(goal, tool, domain)
    if matched:
        print(f"{tool}: multiplier={mult}, constraint={constraint}")

