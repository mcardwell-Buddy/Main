import sys
sys.path.insert(0, '.')

from Back_End.tool_registry import tool_registry
from Back_End.tools import register_foundational_tools
from Back_End.additional_tools import register_additional_tools

register_foundational_tools(tool_registry)
register_additional_tools(tool_registry)

print("Registered tools:")
for tool_name in sorted(tool_registry.tools.keys()):
    print(f"  - {tool_name}")

print()
print(f"Total: {len(tool_registry.tools)} tools")
print()

# Check if web_extract is there
if 'web_extract' in tool_registry.tools:
    print("✅ web_extract is registered")
else:
    print("❌ web_extract is NOT registered")

