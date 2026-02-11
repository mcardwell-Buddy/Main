"""Test intent classification locally."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from Back_End.conversation.intent_classifier import IntentClassifier

classifier = IntentClassifier()

test_messages = [
    "hello buddy",
    "are you online?",
    "this is test message 3",
    "final test",
    "what do you think about this?",
    "can you search for something?",
    "send me an email please",
    "tell me what you believe",
    "what if we tried a different approach?",
    "I think we should try this",
]

print("=" * 70)
print("INTENT CLASSIFICATION TEST")
print("=" * 70)

for msg in test_messages:
    intent = classifier.classify(msg)
    print(f"Message: '{msg}'")
    print(f"Intent: {intent}")
    print(f"Hint: {classifier.get_response_hint(intent)}")
    print()

print("=" * 70)
print("Classification test complete.")
print("=" * 70)

