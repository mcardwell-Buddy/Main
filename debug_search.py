#!/usr/bin/env python3
"""Debug script to see what's actually being extracted from search results"""

import os
import sys
import time
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from Back_End.mployer_scraper import MployerScraper
from selenium.webdriver.common.by import By

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

username = os.getenv("MPLOYER_USERNAME")
password = os.getenv("MPLOYER_PASSWORD")

if not username or not password:
    logger.error("Set MPLOYER_USERNAME and MPLOYER_PASSWORD in .env")
    sys.exit(1)

logger.info("Starting debug test...")
scraper = MployerScraper(username, password, headless=False)
scraper.initialize_browser()

try:
    # Login
    logger.info("Logging in...")
    if not scraper.login_to_mployer():
        logger.error("Login failed!")
        sys.exit(1)
    
    logger.info("✓ Login successful!")
    time.sleep(2)
    
    # Search with employee range and location
    logger.info("Running employer search for Maryland...")
    employers = scraper.search_employers(employees_min=10, employees_max=500, state="Maryland")
    
    logger.info(f"\n{'='*80}")
    logger.info(f"EXTRACTION REPORT: Found {len(employers)} employers")
    logger.info(f"{'='*80}\n")
    
    # Now let's inspect the actual page to see what's there
    logger.info("Inspecting actual page structure...")
    time.sleep(2)
    
    # Try different selectors to find result elements
    selectors_to_try = [
        ("tr", "Table rows"),
        ("[role='row']", "Accessible rows"),
        (".result-row", "Result row class"),
        (".employer-card", "Employer card class"),
        (".employer-result", "Employer result class"),
        ("div[class*='row'][class*='result']", "Div with row+result"),
        ("td", "Table data cells"),
        ("[class*='Result']", "Any class with Result"),
        ("[class*='employer']", "Any class with employer"),
    ]
    
    print("\n" + "="*80)
    print("SELECTOR ANALYSIS")
    print("="*80)
    
    for selector, description in selectors_to_try:
        try:
            elements = scraper.driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                print(f"\n✓ {description:30} ({selector})")
                print(f"  Found: {len(elements)} elements")
                
                # Show first 3 elements' text (truncated)
                for i, elem in enumerate(elements[:3]):
                    text = elem.text[:100].replace('\n', ' | ')
                    print(f"    [{i}] {text}")
                
                if len(elements) > 3:
                    print(f"    ... and {len(elements)-3} more")
        except Exception as e:
            pass
    
    # Now let's check the page title and look for result count indicators
    print("\n" + "="*80)
    print("PAGE STATE")
    print("="*80)
    print(f"Current URL: {scraper.driver.current_url}")
    print(f"Page title: {scraper.driver.title}")
    
    # Look for any text indicating result count
    try:
        body_text = scraper.driver.find_element(By.TAG_NAME, "body").text
        # Look for numbers that might indicate count
        import re
        numbers = re.findall(r'\b(\d+)\s*(?:results?|employers?|match)', body_text, re.IGNORECASE)
        if numbers:
            print(f"Found result count indicators: {numbers}")
    except:
        pass
    
    # Print the extracted employers
    print("\n" + "="*80)
    print("EXTRACTED DATA")
    print("="*80)
    
    if employers:
        for i, emp in enumerate(employers[:5], 1):
            print(f"\n{i}. Name: '{emp.get('name', 'EMPTY')}'")
            print(f"   Employees: {emp.get('employees', 'EMPTY')}")
            print(f"   Location: {emp.get('location', 'EMPTY')}")
            print(f"   Industry: {emp.get('industry', 'EMPTY')}")
            if emp.get('raw_text'):
                raw = emp.get('raw_text', '').replace('\n', ' | ')[:150]
                print(f"   Raw text: {raw}")
        
        if len(employers) > 5:
            print(f"\n... and {len(employers) - 5} more employers")
            # Check if they all have the same issue
            empty_count = sum(1 for e in employers if not e.get('name') or e.get('name') == '')
            print(f"\nEmployers with empty names: {empty_count}/{len(employers)}")
    else:
        print("NO EMPLOYERS EXTRACTED!")
    
    # Take a screenshot of the results page
    logger.info("\nTaking screenshot...")
    scraper.driver.save_screenshot("debug_results_page.png")
    logger.info("Screenshot saved: debug_results_page.png")
    
    # Get page HTML (first 2000 chars)
    print("\n" + "="*80)
    print("PAGE HTML SAMPLE (first 2000 chars)")
    print("="*80)
    html = scraper.driver.page_source[:2000]
    print(html)
    
except Exception as e:
    logger.error(f"Debug test failed with error: {e}")
    import traceback
    traceback.print_exc()
    
finally:
    logger.info("\nClosing browser...")
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

