"""
Single focused test for Phase 2 Step 2 verification
"""
import json
import logging
from Back_End.agents.web_navigator_agent import WebNavigatorAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("=" * 80)
print("PHASE 2 STEP 2 VERIFICATION: Intent Action Execution")
print("=" * 80)

payload = {
    "target_url": "http://quotes.toscrape.com/",
    "goal_description": "Find directory of all quotes and authors",
    "page_type": "listing",
    "expected_fields": ["text", "author", "tags"],
    "max_pages": 1,
    "execution_mode": "LIVE"
}

print("\n[TEST] Running web navigation with intent-guided action")
print(f"[TEST] Initial URL: {payload['target_url']}")
print(f"[TEST] Goal: {payload['goal_description']}")

agent = WebNavigatorAgent()
result = agent.run(payload)

print(f"\n[RESULT] Status: {result.get('status')}")
print(f"[RESULT] Items extracted: {result.get('metadata', {}).get('items_extracted', 0)}")

# Get final URL
if hasattr(agent, 'driver') and agent.driver:
    final_url = agent.driver.current_url
    print(f"[RESULT] Final URL: {final_url}")
    
    if final_url != payload['target_url']:
        print("\n[SUCCESS] Intent action EXECUTED - URL changed")
        print(f"[SUCCESS] Navigated from {payload['target_url']}")
        print(f"[SUCCESS]            to {final_url}")
    else:
        print("\n[INFO] Intent action blocked or not triggered")
    
    agent.driver.quit()

# Check signals
signals_file = "outputs/phase25/learning_signals.jsonl"
with open(signals_file, "r", encoding="utf-8") as f:
    lines = f.readlines()
    last_signals = [json.loads(line) for line in lines[-5:] if line.strip()]
    
    print("\n[SIGNALS] Last 3 intent signals:")
    for sig in last_signals[-3:]:
        sig_type = sig.get("signal_type")
        if "intent" in sig_type:
            print(f"  - {sig_type}: {sig.get('goal', 'N/A')[:50]}")
            if sig_type == "intent_action_taken":
                action = sig.get('action', {})
                print(f"    Action: '{action.get('text')}' -> {action.get('href')}")
                print(f"    Confidence: {sig.get('confidence'):.2f}")

print("\n" + "=" * 80)
print("[OK] Phase 2 Step 2 validation complete")
print("=" * 80)

