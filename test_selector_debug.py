#!/usr/bin/env python
from backend.tool_selector import tool_selector

goal = "Extract 'services' from https://www.cardwellassociates.com"
result = tool_selector.prepare_input('web_extract', goal, {})
print(f"Goal: {goal}")
print(f"Result: {result}")
print(f"Expected: .services, .service-list, section[class*=\"service\"], ul.services li, .offering")
