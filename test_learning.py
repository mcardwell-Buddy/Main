"""Test learning instruction recognition"""
from backend.goal_decomposer import goal_decomposer
from backend.tool_selector import tool_selector

print("="*60)
print("TESTING LEARNING INSTRUCTION RECOGNITION")
print("="*60)

# Test 1: Learning instruction
goal1 = "learn about Python decorators"
print(f"\n1. Goal: '{goal1}'")
classification1 = goal_decomposer.classify_goal(goal1)
tool1 = tool_selector.select_tool(goal1)
print(f"   Composite: {classification1['is_composite']}")
print(f"   Reasoning: {classification1.get('llm_reasoning', 'N/A')}")
print(f"   Tool Selected: {tool1}")
print(f"   ✓ Expected: atomic, store_knowledge")

# Test 2: Introspection query
goal2 = "what do you know about Python?"
print(f"\n2. Goal: '{goal2}'")
classification2 = goal_decomposer.classify_goal(goal2)
tool2 = tool_selector.select_tool(goal2)
print(f"   Composite: {classification2['is_composite']}")
print(f"   Reasoning: {classification2.get('llm_reasoning', 'N/A')}")
print(f"   Tool Selected: {tool2}")
print(f"   ✓ Expected: atomic, learning_query")

# Test 3: Research query (should be web_search)
goal3 = "what is quantum computing?"
print(f"\n3. Goal: '{goal3}'")
tool3 = tool_selector.select_tool(goal3)
print(f"   Tool Selected: {tool3}")
print(f"   ✓ Expected: web_search")

# Test 4: More learning variations
print("\n" + "="*60)
print("LEARNING INSTRUCTION VARIATIONS")
print("="*60)

learning_variations = [
    "study machine learning",
    "research and remember Docker",
    "teach yourself about neural networks",
    "learn everything about TypeScript",
]

for goal in learning_variations:
    tool = tool_selector.select_tool(goal)
    print(f"  '{goal}' -> {tool}")

print("\n" + "="*60)
print("SUMMARY")
print("="*60)
print("Introspection: 'what do you know' -> learning_query (check memory)")
print("Learning: 'learn about' -> store_knowledge (research + save)")
print("Research: 'what is' -> web_search (just research)")
