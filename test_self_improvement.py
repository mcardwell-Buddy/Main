"""
Test Self-Improvement Engine

Tests the autonomous self-improvement workflow
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.self_improvement_engine import self_improvement_engine
from backend.agent_reasoning import agent_reasoning

print("="*60)
print("TESTING SELF-IMPROVEMENT ENGINE")
print("="*60)

# Test 1: Scan for improvements
print("\n1. Testing codebase scan...")
print("-" * 60)

opportunities = self_improvement_engine.scan_codebase_for_improvements()

print(f"\n✓ Found {len(opportunities)} improvement opportunities:")
for i, opp in enumerate(opportunities[:5], 1):  # Show top 5
    print(f"\n{i}. {opp['file']}")
    print(f"   Priority: {opp['priority']}")
    print(f"   Suggestions:")
    for suggestion in opp['suggestions'][:3]:  # Show first 3 suggestions
        print(f"     - {suggestion}")

# Test 2: Detect self-improvement intent
print("\n\n2. Testing intent detection...")
print("-" * 60)

test_goals = [
    "improve yourself",
    "analyze your own code",
    "what's 2+2",  # Should not detect
    "make yourself better",
]

for goal in test_goals:
    result = agent_reasoning.detect_self_improvement_intent(goal)
    if result:
        print(f"✓ '{goal}' → Detected: {result['action']}")
    else:
        print(f"✗ '{goal}' → Not a self-improvement request")

# Test 3: Test autonomous improvement (with a simple test file)
print("\n\n3. Testing autonomous improvement loop...")
print("-" * 60)

# Create a simple test file
test_file_path = "backend/test_improvement_target.py"
test_content = """
def simple_function(x, y):
    return x + y

if __name__ == "__main__":
    print(simple_function(2, 3))
"""

# Write test file
with open(test_file_path, 'w') as f:
    f.write(test_content)

print(f"Created test file: {test_file_path}")

# Try to improve it
print("\nRunning autonomous improvement (add error handling)...")
result = self_improvement_engine.autonomous_improve_until_tests_pass(
    file_path=test_file_path,
    improvement_description="add error handling"
)

print(f"\n{'='*60}")
print("IMPROVEMENT RESULT:")
print(f"{'='*60}")
print(f"Success: {result.get('success')}")
print(f"Iterations: {result.get('iterations')}")
print(f"Ready for approval: {result.get('ready_for_approval', False)}")

print(f"\nProgress log:")
for log in result.get('progress_log', []):
    print(f"  [{log['iteration']}] {log['message']}")

if result.get('improved_code'):
    print(f"\n{'='*60}")
    print("IMPROVED CODE:")
    print(f"{'='*60}")
    print(result['improved_code'][:500])
    if len(result['improved_code']) > 500:
        print("... (truncated)")

# Cleanup
try:
    os.remove(test_file_path)
    print(f"\n✓ Cleaned up test file")
except:
    pass

print(f"\n{'='*60}")
print("✓ ALL TESTS COMPLETE")
print(f"{'='*60}")
