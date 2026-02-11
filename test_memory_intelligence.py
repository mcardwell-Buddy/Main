from Back_End.memory_manager import memory_manager

# Test importance calculation
print("=== Testing Importance Calculation ===\n")

# Low importance reflection (neutral effectiveness)
low_reflection = {
    'effectiveness_score': 0.5,
    'confidence_adjustment': 0.0,
    'strategy_adjustment': 'Try again',
    'tool_feedback': {}
}
importance = memory_manager.calculate_importance('reflection', low_reflection)
print(f"Low importance reflection: {importance:.2f}")
print(f"Should save? {memory_manager.should_save('reflection', low_reflection)}\n")

# High importance reflection (good effectiveness, strategy, confidence boost)
high_reflection = {
    'effectiveness_score': 0.85,
    'confidence_adjustment': 0.15,
    'strategy_adjustment': 'Web search was very effective. Continue using targeted queries for technical topics.',
    'tool_feedback': {
        'web_search': {'usefulness': 0.9}
    }
}
importance = memory_manager.calculate_importance('reflection', high_reflection)
print(f"High importance reflection: {importance:.2f}")
print(f"Should save? {memory_manager.should_save('reflection', high_reflection)}\n")

# Critical failure (tool failed, low usefulness)
failure_reflection = {
    'effectiveness_score': 0.2,
    'confidence_adjustment': -0.15,
    'strategy_adjustment': 'This tool consistently fails. Avoid using it for this task type.',
    'tool_feedback': {
        'calculate': {'usefulness': 0.1, 'notes': 'Syntax errors'}
    }
}
importance = memory_manager.calculate_importance('reflection', failure_reflection)
print(f"Failure reflection: {importance:.2f}")
print(f"Should save? {memory_manager.should_save('reflection', failure_reflection)}\n")

# Error observation (always important)
error_obs = {'error': 'Tool timeout'}
importance = memory_manager.calculate_importance('observation', error_obs)
print(f"Error observation: {importance:.2f}")
print(f"Should save? {memory_manager.should_save('observation', error_obs)}\n")

# Goal completion (always important)
completion = {'goal': 'test', 'steps_taken': 5, 'final_confidence': 0.8}
importance = memory_manager.calculate_importance('goal_completion', completion)
print(f"Goal completion: {importance:.2f}")
print(f"Should save? {memory_manager.should_save('goal_completion', completion)}\n")

print("=== Summary ===")
print("The agent now:")
print("- Calculates importance scores (0.0 to 1.0) for every piece of data")
print("- Only saves to Firebase if importance >= 0.6 (configurable)")
print("- Always saves: failures, high effectiveness, goal completions")
print("- Skips: neutral reflections, low-value observations")
print("- Enriches saved data with importance metadata and timestamps")

