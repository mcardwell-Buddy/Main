#!/usr/bin/env python3
"""Test filter interaction using JavaScript methods instead of standard Selenium."""

import os
import sys
import time
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent / '.env')

sys.path.insert(0, str(Path(__file__).parent))

from Back_End.mployer_scraper import MployerScraper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

username = os.getenv("MPLOYER_USERNAME")
password = os.getenv("MPLOYER_PASSWORD")

if not username or not password:
    logger.error("Set MPLOYER_USERNAME and MPLOYER_PASSWORD in .env")
    sys.exit(1)

# Initialize scraper
scraper = MployerScraper(username, password, headless=False)
scraper.initialize_browser()

try:
    # Login to Mployer
    print("\n[1] Logging in to Mployer...")
    scraper.login_to_mployer()
    print("[OK] Logged in successfully")
    
    # Navigate to search page using search_employers method
    print("\n[2] Navigating to Employer Search...")
    print("     Testing with filters: min=10, max=500")
    
    # Call search_employers which will:
    # 1. Navigate to the search page
    # 2. Expand filter sections
    # 3. Fill in the filter values
    # 4. Click Apply Filters
    # 5. Extract and return results
    results = scraper.search_employers(employees_min=10, employees_max=500)
    
    print("[OK] Search completed")
    print(f"\n[3] Results: Found {len(results)} employers")
    if results:
        print("     First few results:")
        for i, employer in enumerate(results[:3]):
            print(f"     - {employer.get('name', 'Unknown')} ({employer.get('employees', 'N/A')} employees)")
    else:
        print("     No results returned")
    
finally:
    print("\nClosing browser...")
    scraper.driver.quit()

