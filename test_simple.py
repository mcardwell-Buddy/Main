#!/usr/bin/env python3
"""Simple test with direct print statements."""

import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent / '.env')

sys.path.insert(0, str(Path(__file__).parent))

from backend.mployer_scraper import MployerScraper

username = os.getenv("MPLOYER_USERNAME")
password = os.getenv("MPLOYER_PASSWORD")

if not username or not password:
    print("ERROR: Set MPLOYER_USERNAME and MPLOYER_PASSWORD in .env")
    sys.exit(1)

print("\n=== TEST START ===")

# Initialize scraper
scraper = MployerScraper(username, password, headless=False)
scraper.initialize_browser()

try:
    print("[1] Logging in...")
    login_ok = scraper.login_to_mployer()
    if not login_ok:
        print("[1FAIL] Login returned False - MFA likely needed or login failed")
        print("     Please check if a browser window appeared for manual MFA entry")
        sys.exit(1)
    print("[1OK] Logged in successfully")
    
    print("[2] Performing search with employees_min=10, employees_max=500...")
    results = scraper.search_employers(employees_min=10, employees_max=500)
    print(f"[2OK] Search returned {len(results)} results")
    
    # Print page text to see if filters were applied
    time.sleep(2)
    body = scraper.driver.find_element("tag name", "body")
    page_text = body.text[:500]
    
    print("\n[Page content snippet]:")
    print(page_text)
    print("\n[/Page content]")
    
    if results:
        print("\nFirst result:")
        print(results[0])
    else:
        print("\nNo results returned - filters may not have been applied correctly")
    
except Exception as e:
    print(f"[ERROR] {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    
finally:
    print("\n[3] Closing browser...")
    scraper.driver.quit()
    print("[3OK] Test complete")
