"""Smoke test to verify web tools are now registered"""

from Back_End.agent import *

print("=" * 60)
print("TOOL REGISTRATION VERIFICATION")
print("=" * 60)

print("\nRegistered tools after fix:")
for name in sorted(tool_registry.tools.keys()):
    print(f"  - {name}")

print("\n" + "=" * 60)
print("WEB TOOLS STATUS")
print("=" * 60)

critical_tools = ['web_navigate', 'web_extract', 'web_click', 'calculate']
for tool in critical_tools:
    status = "✅ REGISTERED" if tool in tool_registry.tools else "❌ MISSING"
    print(f"  {tool:20s} {status}")

print("\n" + "=" * 60)
print("TOOL COUNT")
print("=" * 60)
print(f"  Total registered tools: {len(tool_registry.tools)}")

# Test actual execution
print("\n" + "=" * 60)
print("SMOKE TEST: Calculate")
print("=" * 60)
result = tool_registry.call('calculate', '2+2')
print(f"  Input: '2+2'")
print(f"  Result: {result}")

print("\n" + "=" * 60)
print("SMOKE TEST: Web Navigate")
print("=" * 60)
result = tool_registry.call('web_navigate', 'https://example.com')
print(f"  Input: 'https://example.com'")
print(f"  Result keys: {list(result.keys())}")
if 'error' in result:
    print(f"  Error: {result['error']}")
elif 'message' in result:
    print(f"  Message: {result['message']}")
print(f"  Success: {'error' not in result or 'dry' in str(result).lower()}")

print("\n" + "=" * 60)
print("VERIFICATION COMPLETE")
print("=" * 60)

