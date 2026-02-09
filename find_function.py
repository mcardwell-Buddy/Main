with open(r'c:\Users\micha\Buddy\backend\interaction_orchestrator.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find start and end of function
start = None
end = None
for i, line in enumerate(lines):
    if '_handle_approval_bridge' in line and start is None:
        start = i
    if start is not None and i > start and line.strip().startswith('def '):
        end = i
        break

print(f'Function starts at line {start} and ends at line {end}')
print(f'Lines {start} to {end-1}')
