"""Test pattern specificity"""
import re

# Learning query patterns
learning_query_patterns = [
    r'\b(what do you know about|tell me what you know|what have you learned about)\b',
    r'\b(how much do you know|what\'s your understanding of|explain your knowledge of)\b',
]

# Store knowledge patterns  
store_knowledge_patterns = [
    r'\b(learn about|study|research and remember)\b',
    r'\b(teach yourself|find out about and remember|memorize)\b',
]

test_goals = [
    ("learn about Python", "store_knowledge"),
    ("what do you know about Python?", "learning_query"),
    ("what is Python?", "none"),
    ("study machine learning", "store_knowledge"),
    ("teach yourself Docker", "store_knowledge"),
]

print("Pattern Matching Test:")
print("="*60)

for goal, expected in test_goals:
    lq_match = any(re.search(p, goal, re.IGNORECASE) for p in learning_query_patterns)
    sk_match = any(re.search(p, goal, re.IGNORECASE) for p in store_knowledge_patterns)
    
    result = "learning_query" if lq_match else ("store_knowledge" if sk_match else "none")
    status = "✓" if result == expected else "✗"
    
    print(f"{status} '{goal}'")
    print(f"   Expected: {expected}, Got: {result}")
    print(f"   LQ match: {lq_match}, SK match: {sk_match}")
    print()

