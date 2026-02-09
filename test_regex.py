import re

goal = 'What is 100-10?'

# Try different regex patterns
patterns = [
    r'(\d+[\s]*[+\-*/][\s]*\d+)',
    r'(\d+[-+*/]\d+)',
    r'(\d+\s*[-+*/]\s*\d+)',
    r'\d+\s*[-+*/]\s*\d+'
]

for p in patterns:
    m = re.search(p, goal)
    result = m.group(0) if m else "NO MATCH"
    print(f"Pattern: {p}")
    print(f"Result: {result}\n")
