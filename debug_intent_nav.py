"""Debug test to see navigation flow"""
import logging
from Back_End.agents.web_navigator_agent import WebNavigatorAgent

# Enable debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s:%(name)s:%(message)s'
)

payload = {
    "target_url": "http://quotes.toscrape.com/",
    "goal_description": "Find next page of quotes",
    "page_type": "listing",
    "expected_fields": ["text", "author"],
    "max_pages": 1,
    "execution_mode": "LIVE"
}

print("=== STARTING INTENT ACTION TEST ===")
agent = WebNavigatorAgent()

# Track URL before
initial_url = "http://quotes.toscrape.com/"
print(f"\n[BEFORE] Initial URL: {initial_url}")

result = agent.run(payload)

# Track URL after
if hasattr(agent, 'driver') and agent.driver:
    final_url = agent.driver.current_url
    print(f"\n[AFTER] Final URL: {final_url}")
    print(f"[CHECK] URLs different: {final_url != initial_url}")
    agent.driver.quit()

print("\n[DONE] Test complete")

