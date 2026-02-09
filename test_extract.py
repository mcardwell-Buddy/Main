from backend.tool_selector import tool_selector
import re

goal = 'What is 100-10?'

# Check the prepare_input method
tool_name = 'calculate'

# Look for patterns like "15 + 27" or "calculate 2 * 5"
match = re.search(r'[\d\s\+\-\*\/\(\)\.]+', goal)
if match:
    extracted = match.group(0).strip()
else:
    extracted = goal

print(f"Goal: {goal}")
print(f"Extracted: {extracted}")
print(f"Trying to calculate: {extracted}")

try:
    result = eval(extracted, {"__builtins__": {}}, {})
    print(f"Result: {result}")
except Exception as e:
    print(f"Error: {e}")
