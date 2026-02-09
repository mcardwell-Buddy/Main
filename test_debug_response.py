#!/usr/bin/env python3
"""
Debug: See what response we get from interaction orchestrator
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from backend.interaction_orchestrator import InteractionOrchestrator

orchestrator = InteractionOrchestrator()
session_id = "test_debug"
user_id = "test_user"

message = "Search https://techcrunch.com for the latest AI news and write a summary"
print(f"Sending message: {message}\n")

response = orchestrator.process_message(
    message=message,
    session_id=session_id,
    user_id=user_id
)

print("Full Response:")
print(json.dumps(response.to_dict(), indent=2, default=str))
