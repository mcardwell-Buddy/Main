from backend.iterative_decomposer import iterative_decomposer
import re

goal = '10 + 5'
print('Goal:', goal)
print('Goal lower:', goal.lower())

# Test math pattern
pattern = r'(?:what\s+is|calculate|compute|solve|times|plus|minus|divided|multiply).*(?:\d|\+|-|\*|\/)'
matches = re.search(pattern, goal.lower(), re.IGNORECASE)
print('Math pattern matches:', bool(matches))

# Test simpler pattern
simple_pattern = r'\d+.*[\+\-\*\/].*\d+'
simple_matches = re.search(simple_pattern, goal.lower())
print('Simple pattern matches:', bool(simple_matches))

result = iterative_decomposer.analyze_goal_complexity(goal)
print('Complexity:', result['complexity'])
print('Category:', result['category'])
