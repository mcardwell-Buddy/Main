"""
Demo Buddy's Vision System
Demonstrates vision capabilities on any website
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from backend.buddys_vision import BuddysVision


def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}\n")


def demo_buddys_vision():
    print_section("BUDDY'S VISION SYSTEM - DEMO")

    print("[*] Creating Chrome WebDriver...")
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        vision = BuddysVision(driver=driver)
        print("[OK] Buddy's Vision Online!\n")

        test_url = "https://example.com"
        print_section("STEP 1: BUDDY INSPECTS A WEBSITE")
        print(f"[*] Buddy is looking at: {test_url}")
        print("    (Analyzing DOM structure, elements, patterns)\n")

        inspection = vision.see_website(test_url)
        print("[OK] Buddy completed the inspection!\n")

        print("WHAT BUDDY FOUND:")
        print(f"   - Title: {inspection.get('title', 'N/A')}")
        print(f"   - URL: {inspection.get('url', 'N/A')}")
        print(f"   - Total elements: {len(inspection.get('all_elements', []))}")
        print(f"   - Forms: {len(inspection.get('forms', []))}")
        print(f"   - Buttons: {len(inspection.get('buttons', []))}")
        print(f"   - Input fields: {len(inspection.get('inputs', []))}")
        print(f"   - Links: {len(inspection.get('links', []))}")
        print(f"   - Selects/Dropdowns: {len(inspection.get('selects', []))}")

    except Exception as e:
        print(f"[ERR] Demo failed: {e}")
        import traceback

        traceback.print_exc()
    finally:
        print("[*] Closing browser...")
        driver.quit()
        print("[OK] Browser closed")


if __name__ == "__main__":
    demo_buddys_vision()
