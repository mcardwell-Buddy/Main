#!/usr/bin/env python3
"""
Test tool selection for extraction vs calculate
"""
import logging
logging.basicConfig(level=logging.DEBUG)

# Import and register tools FIRST
from backend.tool_registry import tool_registry
from backend.tools import register_foundational_tools, register_code_awareness_tools
from backend.additional_tools import register_additional_tools
from backend.extended_tools import register_extended_tools
from backend.web_scraper import register_scraping_tools
from backend.web_tools import register_web_tools

register_foundational_tools(tool_registry)
register_additional_tools(tool_registry)
register_code_awareness_tools(tool_registry)
register_extended_tools(tool_registry)
register_scraping_tools(tool_registry)
register_web_tools(tool_registry)

from backend.tool_selector import tool_selector

print("=" * 80)
print("TEST: Tool Selection for Extraction vs Calculate")
print("=" * 80)

test_cases = [
    ("Extract financial data from earnings reports", "Should select web_extract or web_search, NOT calculate"),
    ("Extract data from example.com", "Should select web_extract or web_navigate, NOT calculate"),
    ("Pull text content from webpage", "Should select web_extract, NOT calculate"),
    ("Scrape data and parse it", "Should select web_extract, NOT calculate"),
    ("Get market data from financial website", "Should select web_search or web_extract, NOT calculate"),
    ("Calculate 100 + 50", "Should select calculate"),
    ("What is 25 * 4?", "Should select calculate"),
    ("Extract the price from the page", "Should select web_extract, NOT calculate"),
]

print("\n")
for query, expected_behavior in test_cases:
    print(f"Query: {query}")
    print(f"Expected: {expected_behavior}")
    
    # Get tool scores
    scores = tool_selector.analyze_goal(query)
    
    # Get selected tool
    tool_name, tool_input, confidence = tool_selector.select_tool(query)
    
    print(f"Selected Tool: {tool_name} (confidence: {confidence:.2f})")
    
    # Show top 3 tools
    top_tools = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
    print("Top candidates:")
    for tool, score in top_tools:
        print(f"  - {tool}: {score:.2f}")
    
    # Check if it's wrong
    if query.lower().startswith(("extract", "pull", "scrape", "get")) or "extract" in query.lower() or "scrape" in query.lower():
        if tool_name == "calculate":
            print("[FAIL] Should not use calculate for extraction!")
        else:
            print("[PASS] Correct: Using web tool for extraction")
    elif ("+" in query or "-" in query or "*" in query or "/" in query or "calculate" in query.lower() or "what is" in query.lower() and any(c.isdigit() for c in query)):
        if tool_name == "calculate":
            print("[PASS] Correct: Using calculate for math")
        else:
            print("[FAIL] Should use calculate for math!")
    
    print()

print("=" * 80)
print("TEST COMPLETE")
print("=" * 80)
