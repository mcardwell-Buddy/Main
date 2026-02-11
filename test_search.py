#!/usr/bin/env python3
"""Quick test of employer search with improved extraction"""

import os
import sys
import time
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from Back_End.mployer_scraper import MployerScraper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

username = os.getenv("MPLOYER_USERNAME")
password = os.getenv("MPLOYER_PASSWORD")

if not username or not password:
    logger.error("Set MPLOYER_USERNAME and MPLOYER_PASSWORD in .env")
    sys.exit(1)

logger.info("Starting test...")
scraper = MployerScraper(username, password, headless=False)
scraper.initialize_browser()

try:
    # Login (will use saved cookies if available)
    logger.info("Logging in...")
    if not scraper.login_to_mployer():
        logger.error("Login failed!")
        sys.exit(1)
    
    logger.info("✓ Login successful!")
    
    # Search with employee range AND location
    logger.info("Running employer search...")
    employers = scraper.search_employers(
        employees_min=10, 
        employees_max=500
        # Note: Skipping state filter for now to focus on employee range filters
    )
    
    logger.info(f"✓ Found {len(employers)} employers")
    
    # Print first 10 results
    if employers:
        print("\n" + "="*80)
        print("SEARCH RESULTS (First 10)")
        print("="*80)
        for i, emp in enumerate(employers[:10], 1):
            print(f"\n{i}. {emp.get('name', 'N/A')}")
            print(f"   Employees: {emp.get('employees', 'N/A')}")
            print(f"   Location: {emp.get('location', 'N/A')}")  
            print(f"   Industry: {emp.get('industry', 'N/A')}")
            if emp.get('raw_text'):
                print(f"   Raw: {emp.get('raw_text')[:100]}...")
    
    logger.info(f"\nTotal employers found: {len(employers)}")
    
except Exception as e:
    logger.error(f"Test failed with error: {e}")
    import traceback
    traceback.print_exc()
    
finally:
    logger.info("Closing browser...")
    try:
        scraper.driver.quit()
    except Exception as e:
        logger.warning(f"Error closing browser: {e}")
        try:
            import subprocess
            subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe'], capture_output=True)
            subprocess.run(['taskkill', '/F', '/IM', 'chromedriver.exe'], capture_output=True)
        except:
            pass

