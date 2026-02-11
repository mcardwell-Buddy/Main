#!/usr/bin/env python
"""Quick test of NavigationIntentEngine standalone"""

import sys
import os
os.chdir(r'C:\Users\micha\Buddy')
sys.path.insert(0, r'C:\Users\micha\Buddy')

from Back_End.agents.navigation_intent_engine import NavigationIntentEngine

print("Testing NavigationIntentEngine...")

# Mock page context
mock_context = {
    "links": [
        {"text": "Browse All Companies", "href": "/directory", "aria_label": None, "class": ""},
        {"text": "Next Page", "href": "/page/2", "aria_label": "Next page", "class": "pagination"},
        {"text": "Login", "href": "/login", "aria_label": None, "class": "nav-link"},
        {"text": "Company Listings", "href": "/companies", "aria_label": None, "class": "main-nav"},
        {"text": "Facebook", "href": "https://facebook.com", "aria_label": None, "class": "social"},
    ]
}

# Test intent engine
engine = NavigationIntentEngine(
    goal_description="Find small business listings",
    page_context=mock_context,
    current_url="https://example.com"
)

print(f"Goal keywords: {engine.goal_keywords}")

# Rank candidates
candidates = engine.rank_navigation_candidates()

print(f"\nFound {len(candidates)} candidates:")
for idx, c in enumerate(candidates[:5], 1):
    print(f"  #{idx}: [{c['score']}] {c['text']} → {c['href']}")
    print(f"       Signals: {', '.join(c['signals'])}")

# Test signal emission
top = candidates[0] if candidates else None
signal = engine.emit_intent_signal(top)

print(f"\nIntent Signal:")
print(f"  Goal: {signal['goal']}")
print(f"  Confidence: {signal['confidence']}")
if signal['top_candidate']:
    print(f"  Top: {signal['top_candidate']['text']} (score: {signal['top_candidate']['score']})")

print("\n✅ NavigationIntentEngine working!")

