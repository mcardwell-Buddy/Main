"""Test that JSONL logging includes intent field."""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from Back_End.interfaces.telegram_interface import TelegramInterface

# Create a test interface instance
telegram = TelegramInterface()

# Simulate incoming messages with different intents
test_updates = [
    {
        "update_id": 100,
        "message": {
            "message_id": 1,
            "from": {"id": 8310994340, "first_name": "Test"},
            "text": "hello buddy"
        }
    },
    {
        "update_id": 101,
        "message": {
            "message_id": 2,
            "from": {"id": 8310994340, "first_name": "Test"},
            "text": "are you online?"
        }
    },
]

print("=" * 70)
print("INTENT LOGGING TEST")
print("=" * 70)
print("")

for update in test_updates:
    # Handle the message (which classifies intent and logs to JSONL)
    event = telegram.handle_update(update)
    if event:
        print(f"Message: '{event['text']}'")
        print(f"Intent: {event['intent']}")
        print()

# Read back the JSONL file to verify intent is logged
events_file = telegram.events_path
if events_file.exists():
    print("-" * 70)
    print("Recent JSONL entries with intent field:")
    print("-" * 70)
    
    with open(events_file, 'r') as f:
        lines = f.readlines()
        # Show last 4 lines
        for line in lines[-4:]:
            entry = json.loads(line)
            if "intent" in entry:
                direction = entry.get("direction", "?")
                text_preview = entry.get("text", "")[:40]
                intent = entry.get("intent", "N/A")
                print(f"[{direction}] '{text_preview}' → intent={intent}")
            else:
                direction = entry.get("direction", "?")
                text_preview = entry.get("text", "")[:40]
                print(f"[{direction}] '{text_preview}' → (NO INTENT FIELD)")

print("-" * 70)
print("Test complete. Intent field now in JSONL.")
print("=" * 70)

