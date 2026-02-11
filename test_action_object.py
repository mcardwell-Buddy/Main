#!/usr/bin/env python
"""
Test action_object extraction.
"""
import re

message = "can you visit cardwellassociates.com and provide some information about this company?"
message_lower = message.lower()
intent = "extract"

print(f"Testing message: {message}")
print(f"Intent: {intent}")
print(f"Message lower: {message_lower}\n")

# Check our fallback conditions
print("Checking fallback conditions:")
print(f"1. 'description' in message: {'description' in message_lower}")
print(f"2. 'summary' in message: {'summary' in message_lower}")
print(f"3. 'overview' in message: {'overview' in message_lower}")
print(f"4. 'explain' in message: {'explain' in message_lower}")
print(f"5. 'tell me about' in message: {'tell me about' in message_lower}")

print(f"\n6. 'visit' in message: {'visit' in message_lower}")
print(f"7. 'check' in message: {'check' in message_lower}")
print(f"8. 'look at' in message: {'look at' in message_lower}")
print(f"9. 'view' in message: {'view' in message_lower}")
print(f"10. 'provide' in message: {'provide' in message_lower}")
print(f"11. 'provide information' in message: {'provide information' in message_lower}")

# Now simulate the extraction
action_object = None
if intent == "extract":
    # Try "extract X from Y"
    match = re.search(r"extract\s+(?:the\s+)?([\w\s]+?)\s+from", message_lower)
    if match:
        action_object = match.group(1).strip()
        print(f"\n✓ Pattern 'extract X from Y' matched: {action_object}")
    
    # Try "get X from Y" or "get the X from Y"
    if not action_object:
        match = re.search(r"get\s+(?:the\s+)?([\w\s]+?)\s+from", message_lower)
        if match:
            action_object = match.group(1).strip()
            print(f"✓ Pattern 'get X from Y' matched: {action_object}")
    
    # Try "collect X from Y" or "pull X from Y"
    if not action_object:
        match = re.search(r"(?:collect|pull|grab|retrieve)\s+(?:the\s+)?([\w\s]+?)\s+from", message_lower)
        if match:
            action_object = match.group(1).strip()
            print(f"✓ Pattern 'collect/pull/grab/retrieve X from Y' matched: {action_object}")
    
    # Fallback: if asking for description/summary, extract that
    if not action_object:
        if any(word in message_lower for word in ["description", "summary", "overview", "explain", "tell me about"]):
            action_object = "description"
            print(f"✓ Fallback 'description' matched: {action_object}")
    
    # Fallback: generic extraction
    if not action_object:
        if any(word in message_lower for word in ["visit", "check", "look at", "view", "provide", "provide information"]):
            action_object = "information"
            print(f"✓ Fallback 'information' matched: {action_object}")

if action_object:
    print(f"\n✓ FINAL ACTION_OBJECT: '{action_object}'")
else:
    print(f"\n✗ NO ACTION_OBJECT FOUND")

