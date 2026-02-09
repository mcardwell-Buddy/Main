#!/usr/bin/env python3
"""Debug: Show filter elements on page and test clicking them"""

import os, sys, time
from pathlib import Path
sys.path.insert(0, str(Path('.').absolute()))

from backend.mployer_scraper import MployerScraper
from selenium.webdriver.common.by import By

username = os.getenv('MPLOYER_USERNAME')
password = os.getenv('MPLOYER_PASSWORD')

print("\n" + "="*60)
print("FILTER ELEMENT DETECTION TEST")
print("="*60)

scraper = MployerScraper(username, password, headless=False)
scraper.initialize_browser()

try:
    # Login
    print("\n[1] Logging in...")
    if not scraper.login_to_mployer():
        print("Login failed")
        sys.exit(1)
    print("✓ Logged in")
    
    # Navigate to search
    print("\n[2] Opening search page...")
    scraper.driver.get("https://portal.mployeradvisor.com/catalyst/employer")
    time.sleep(3)
    
    # Look for all clickable elements
    print("\n[3] Searching for filter section headers...")
    
    # Find all elements with text
    all_elements = scraper.driver.find_elements(By.XPATH, "//*[contains(text(), 'Employee') or contains(text(), 'Enrolled')]")
    print(f"Found {len(all_elements)} elements mentioning 'Employee/Enrolled':")
    for i, elem in enumerate(all_elements[:5]):
        text = elem.text[:50]
        try:
            tag = elem.tag_name
            classes = elem.get_attribute('class')
            print(f"  {i+1}. <{tag} class='{classes}'> {text}")
        except:
            pass
    
    # Find input fields
    print("\n[4] Searching for input fields...")
    inputs = scraper.driver.find_elements(By.TAG_NAME, "input")
    print(f"Found {len(inputs)} input fields:")
    for i, inp in enumerate(inputs[:10]):
        input_id = inp.get_attribute('id')
        input_name = inp.get_attribute('name')
        input_placeholder = inp.get_attribute('placeholder')
        input_type = inp.get_attribute('type')
        print(f"  {i+1}. id='{input_id}' name='{input_name}' type='{input_type}' placeholder='{input_placeholder}'")
    
    # Try to manually click and fill min/max fields
    print("\n[5] Attempting to fill min/max employee fields...")
    try:
        min_field = scraper.driver.find_element(By.ID, "minFilter")
        print(f"✓ Found minFilter field")
        min_field.clear()
        min_field.send_keys("10")
        print(f"✓ Set minFilter to 10")
    except Exception as e:
        print(f"✗ Could not fill minFilter: {e}")
    
    try:
        max_field = scraper.driver.find_element(By.ID, "maxFilter")
        print(f"✓ Found maxFilter field")
        max_field.clear()
        max_field.send_keys("500")
        print(f"✓ Set maxFilter to 500")
    except Exception as e:
        print(f"✗ Could not fill maxFilter: {e}")
    
    # Look for Apply Filters button
    print("\n[6] Looking for Apply Filters button...")
    buttons = scraper.driver.find_elements(By.XPATH, "//*[contains(text(), 'Apply')]")
    print(f"Found {len(buttons)} elements with 'Apply' text:")
    for i, btn in enumerate(buttons[:3]):
        text = btn.text
        print(f"  {i+1}. {text}")
    
    print("\n✓ DEBUG COMPLETE - Check the open browser window for current state")
    print("Press Ctrl+C to close...")
    
    # Keep browser open
    while True:
        time.sleep(1)
    
finally:
    try:
        scraper.driver.quit()
    except:
        pass
