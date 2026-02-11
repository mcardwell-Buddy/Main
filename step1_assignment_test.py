import sys
import uuid
sys.path.insert(0, '.')
from Back_End.interaction_orchestrator import orchestrate_message

# Trigger a calculation request - try with a more complex expression
session_id = f"session_{uuid.uuid4().hex[:8]}"

# Try different calculation prompts
test_cases = [
    'Calculate 25 * 4',
    'I need to calculate a complex financial formula: (5000 * 1.08^20) + (200 * 12)',
    'Please use the calculate tool for: 123 * 456 / 789'
]

for test_msg in test_cases:
    print(f'\n=== Testing: {test_msg} ===')
    result = orchestrate_message(test_msg, session_id)
    print(f'Response Type: {result.response_type}')
    print(f'Summary (first 100 chars): {result.summary[:100]}...' if len(result.summary) > 100 else f'Summary: {result.summary}')
    print(f'Missions Spawned: {len(result.missions_spawned)}')
    
    if result.missions_spawned:
        mission = result.missions_spawned[0]
        print(f'  MISSION_ID: {mission.get("mission_id")}')
        print(f'  STATUS: {mission.get("status")}')
        print(f'  INTENT: {mission.get("intent")}')
        print(f'  TOOL_SELECTED: {mission.get("tool_selected")}')
        break

