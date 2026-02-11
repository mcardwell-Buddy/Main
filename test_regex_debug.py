#!/usr/bin/env python
import re

goal = "Extract 'services' from https://www.cardwellassociates.com"

# First check - looking for quoted selectors
match1 = re.search(r'["\']([#.]?[\w-]+(?:\s+[\w-]+)*)["\']', goal)
print(f"First regex (quoted selectors): {match1}")
if match1:
    print(f"  Matched: {match1.group(1)}")

# Second check - extract content type
content_match = re.search(r'extract\s+["\']?(\w+(?:\s+\w+)?)["\']?', goal, re.IGNORECASE)
print(f"\nSecond regex (content type): {content_match}")
if content_match:
    print(f"  Matched: {content_match.group(1)}")
    content_type = content_match.group(1).lower()
    selector_map = {
        'services': '.services, .service-list, section[class*="service"], ul.services li, .offering',
        'prices': '.price, .pricing, [class*="price"], .cost',
    }
    print(f"  Content type: {content_type}")
    print(f"  In selector_map: {content_type in selector_map}")
    if content_type in selector_map:
        print(f"  Returning: {selector_map[content_type]}")

