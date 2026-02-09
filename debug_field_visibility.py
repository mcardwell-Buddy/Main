#!/usr/bin/env python3
"""Debug why minFilter/maxFilter fields aren't interactable."""

import os
import sys
import time
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent / '.env')

sys.path.insert(0, str(Path(__file__).parent))

from backend.mployer_scraper import MployerScraper

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
    print("\n[1] Logging in...")
    scraper.login_to_mployer()
    print("[OK] Logged in")
    
    # Navigate to search page
    print("\n[2] Navigating to search page...")
    scraper.driver.get("https://portal.mployeradvisor.com/catalyst/employer")
    time.sleep(3)
    
    # Find the minFilter field and inspect its properties
    print("\n[3] Inspecting minFilter field properties...")
    try:
        min_field = scraper.driver.find_element("id", "minFilter")
        
        print(f"    Tag: {min_field.tag_name}")
        print(f"    Display: {min_field.value_of_css_property('display')}")
        print(f"    Visibility: {min_field.value_of_css_property('visibility')}")
        print(f"    Opacity: {min_field.value_of_css_property('opacity')}")
        print(f"    Hidden attr: {min_field.get_attribute('hidden')}")
        print(f"    Disabled attr: {min_field.get_attribute('disabled')}")
        print(f"    Is displayed: {min_field.is_displayed()}")
        print(f"    Is enabled: {min_field.is_enabled()}")
        print(f"    Current value: '{min_field.get_attribute('value')}'")
        print(f"    Parent HTML: {min_field.find_element('xpath', '..').get_attribute('outerHTML')[:200]}")
        
        # Try scrolling the field into view and checking again
        print("\n[4] After scrollIntoView...")
        scraper.driver.execute_script("arguments[0].scrollIntoView(true);", min_field)
        time.sleep(0.5)
        print(f"    Is displayed: {min_field.is_displayed()}")
        print(f"    Is enabled: {min_field.is_enabled()}")
        
        # Try using JavaScript to check if field is hidden
        print("\n[5] JavaScript visibility check...")
        is_visible = scraper.driver.execute_script(
            "return arguments[0].offsetParent !== null;", 
            min_field
        )
        print(f"    offsetParent !== null: {is_visible}")
        
        # Check if there's a parent that's hidden
        print("\n[6] Checking parent elements...")
        parent = min_field
        level = 0
        while parent and level < 5:
            try:
                parent = parent.find_element("xpath", "..")
                display = parent.value_of_css_property('display')
                visibility = parent.value_of_css_property('visibility')
                print(f"    Level {level+1} ({parent.tag_name}): display={display}, visibility={visibility}")
                level += 1
            except:
                break
        
        # Try alternative approach: Find any input with placeholder "Min"
        print("\n[7] Finding inputs with placeholder 'Min'...")
        inputs_with_min = scraper.driver.find_elements("xpath", "//input[@placeholder='Min']")
        print(f"    Found {len(inputs_with_min)} input(s) with placeholder='Min'")
        if inputs_with_min:
            alt_field = inputs_with_min[0]
            print(f"    ID: {alt_field.get_attribute('id')}")
            print(f"    Name: {alt_field.get_attribute('name')}")
            print(f"    Is displayed: {alt_field.is_displayed()}")
            print(f"    Is enabled: {alt_field.is_enabled()}")
        
        # Try finding the Enrolled Employees section button/header
        print("\n[8] Finding 'Enrolled Employees' section header...")
        try:
            header = scraper.driver.find_element("xpath", "//*[contains(text(), 'Enrolled Employees')]")
            print(f"    Found: {header.tag_name}")
            print(f"    Text: {header.text[:50]}")
            print(f"    Is displayed: {header.is_displayed()}")
            # Try clicking it
            scraper.driver.execute_script("arguments[0].click();", header)
            print("    Clicked header")
            time.sleep(1)
            # Check minFilter again
            print(f"    After click, minFilter is_displayed: {min_field.is_displayed()}")
            print(f"    After click, minFilter is_enabled: {min_field.is_enabled()}")
        except Exception as e:
            print(f"    Error: {e}")
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
    
finally:
    print("\n[9] Closing browser...")
    scraper.driver.quit()
