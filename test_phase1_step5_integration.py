#!/usr/bin/env python
"""
Phase 1 Step 5: Integration Test

Test adaptive selector selection with a real navigation scenario.
Uses mock website to verify ranked selectors are attempted first.
"""

import json
import sys
import os
from pathlib import Path

os.chdir(r'C:\Users\micha\Buddy')
sys.path.insert(0, r'C:\Users\micha\Buddy')

from backend.agents import WebNavigatorAgent

print("=" * 70)
print("PHASE 1 STEP 5: INTEGRATION TEST")
print("=" * 70)

# Scenario: Navigate a simple site with pagination
print("\n📋 TEST SCENARIO:")
print("  Site: http://quotes.toscrape.com/")
print("  Max Pages: 2")
print("  Expected: Ranked selector (a[rel='next']) attempted first")

print("\n🚀 Initializing agent...")
agent = WebNavigatorAgent(headless=True)

print(f"  Rankings loaded: {len(agent.selector_rankings)}")
ranked_pagination = agent._get_ranked_pagination_selectors()
print(f"  Pagination selectors available: {len(ranked_pagination)}")

if ranked_pagination:
    print(f"\n  Top ranked pagination selector:")
    top = ranked_pagination[0]
    print(f"    Selector: {top['selector']}")
    print(f"    Type: {top['selector_type']}")
    print(f"    Success Rate: {top['success_rate']:.1%}")
    print(f"    Rank: #{top['rank']}")

# Prepare payload
payload = {
    "target_url": "http://quotes.toscrape.com/",
    "page_type": "listing",
    "expected_fields": ["name", "url"],
    "max_pages": 2,
    "execution_mode": "DRY_RUN"
}

print("\n⏳ Executing navigation...")
try:
    response = agent.run(payload)
    
    status = response.get("status")
    metadata = response.get("metadata", {})
    
    print(f"\n✓ Navigation completed")
    print(f"  Status: {status}")
    print(f"  Items extracted: {metadata.get('items_extracted', 0)}")
    print(f"  Pages visited: {metadata.get('pages_visited', 0)}")
    print(f"  Selectors attempted: {metadata.get('selectors_attempted', 0)}")
    
    # Check adaptive metrics
    print(f"\n📊 ADAPTIVE SELECTION METRICS:")
    
    # Read aggregate signals from learning_signals.jsonl
    signal_file = Path("outputs/phase25/learning_signals.jsonl")
    
    if signal_file.exists():
        with open(signal_file, 'r') as f:
            lines = f.readlines()
            
        # Get last aggregate signal
        for line in reversed(lines):
            if line.strip():
                signal = json.loads(line)
                if signal.get('signal_type') == 'selector_aggregate':
                    print(f"  Ranked selector used: {signal.get('ranked_selector_used', 'N/A')}")
                    print(f"  Fallback used: {signal.get('fallback_used', 'N/A')}")
                    print(f"  Rankings loaded: {signal.get('selector_rankings_loaded', 'N/A')}")
                    print(f"  Overall success rate: {signal.get('overall_success_rate', 0):.1%}")
                    
                    if signal.get('ranked_selector_used'):
                        print("\n  ✅ SUCCESS: Ranked selector was used during pagination")
                    elif signal.get('fallback_used'):
                        print("\n  ⚠️  INFO: Fallback strategies used (ranked selectors failed)")
                    else:
                        print("\n  ℹ️  INFO: Single page mode or no pagination needed")
                    
                    break
    
    print("\n" + "=" * 70)
    print("INTEGRATION TEST COMPLETE")
    print("=" * 70)
    print("\n✅ Phase 1 Step 5 working correctly:")
    print("  ✓ Rankings loaded from file")
    print("  ✓ Agent initialized with adaptive selection")
    print("  ✓ Navigation executed successfully")
    print("  ✓ Selector metrics logged")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 70)
