from Back_End.tool_registry import tool_registry

print("Registered tools:")
print(f"Count: {len(tool_registry.tools)}")
for name in tool_registry.tools.keys():
    print(f"  - {name}")

