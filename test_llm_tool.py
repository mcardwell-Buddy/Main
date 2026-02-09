"""Test LLM tool selection"""
from backend.llm_client import llm_client
from backend.tool_registry import tool_registry

print(f"LLM Enabled: {llm_client.enabled}")
print()

if llm_client.enabled:
    # Prepare tools list
    available_tools = []
    for tool_name, tool_info in tool_registry.tools.items():
        available_tools.append({
            'name': tool_name,
            'description': tool_info.get('description', ''),
            'domain': '_global'
        })
    
    # Test different goal types
    test_goals = [
        "learn about Python decorators",
        "what do you know about Python?",
        "what is quantum computing?",
    ]
    
    for goal in test_goals:
        print(f"Goal: '{goal}'")
        result = llm_client.select_tool(goal, available_tools)
        if result:
            print(f"  Tool: {result.get('tool')}")
            print(f"  Confidence: {result.get('confidence')}")
            print(f"  Reasoning: {result.get('reasoning')}")
        else:
            print("  No result")
        print()
else:
    print("LLM not enabled - skipping test")
