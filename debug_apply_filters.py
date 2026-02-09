#!/usr/bin/env python3
"""Debug script to check if filters are actually being set."""

import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / '.env')

sys.path.insert(0, str(Path(__file__).parent))

from backend.mployer_scraper import MployerScraper

username = os.getenv("MPLOYER_USERNAME")
password = os.getenv("MPLOYER_PASSWORD")

if not username or not password:
    print("ERROR: Set MPLOYER_USERNAME and MPLOYER_PASSWORD in .env")
    sys.exit(1)

print("\n=== DEBUG FILTER APPLICATION ===\n")

scraper = MployerScraper(username, password, headless=False)
scraper.initialize_browser()

try:
    print("[1] Logging in...")
    if not scraper.login_to_mployer():
        print("[FAIL] Login failed")
        sys.exit(1)
    print("[OK] Logged in")
    
    # Navigate to search page
    print("\n[2] Navigating to search page...")
    scraper.driver.get("https://portal.mployeradvisor.com/catalyst/employer")
    time.sleep(3)
    print("[OK] On search page")
    
    # Check initial state - get the employer count text
    print("\n[3] Initial state - checking employer count...")
    try:
        body = scraper.driver.find_element("tag name", "body")
        text = body.text
        for line in text.split('\n'):
            if "employers found" in line:
                print(f"    Initial: {line.strip()}")
                break
    except:
        print("    Could not find employer count")
    
    # Set employee range using JavaScript directly (like the code does)
    print("\n[4] Setting employee range (10-500) via JavaScript...")
    scraper.driver.execute_script("""
    const minField = document.getElementById('minFilter');
    if (minField) {
        minField.focus();
        minField.value = '10';
        minField.dispatchEvent(new Event('input', {bubbles: true}));
        minField.dispatchEvent(new Event('change', {bubbles: true}));
        console.log('Set minFilter to 10');
    }
    const maxField = document.getElementById('maxFilter');
    if (maxField) {
        maxField.focus();
        maxField.value = '500';
        maxField.dispatchEvent(new Event('input', {bubbles: true}));
        maxField.dispatchEvent(new Event('change', {bubbles: true}));
        console.log('Set maxFilter to 500');
    }
    """)
    time.sleep(1)
    
    # Verify the values were set
    min_val = scraper.driver.execute_script("return document.getElementById('minFilter').value")
    max_val = scraper.driver.execute_script("return document.getElementById('maxFilter').value")
    print(f"    minFilter value: '{min_val}'")
    print(f"    maxFilter value: '{max_val}'")
    
    # Find and click Apply Filters button
    print("\n[5] Finding Apply Filters button...")
    try:
        buttons = scraper.driver.find_elements("tag name", "button")
        print(f"    Found {len(buttons)} buttons total")
        
        for i, btn in enumerate(buttons):
            text = btn.text.strip()
            if "apply" in text.lower() and "filter" in text.lower():
                print(f"    Button {i}: '{text}' (is_enabled: {btn.is_enabled()})")
    except Exception as e:
        print(f"    Error finding buttons: {e}")
    
    # Try clicking Apply Filters
    print("\n[6] Clicking Apply Filters button...")
    try:
        apply_btn = scraper.driver.find_element("xpath", "//button[contains(., 'Apply Filters')]")
        print(f"    Found button, clicking...")
        scraper.driver.execute_script("arguments[0].click();", apply_btn)
        print("    [OK] Clicked Apply Filters")
        time.sleep(3)
    except Exception as e:
        print(f"    [FAIL] {e}")
    
    # Check final state
    print("\n[7] Final state - checking employer count...")
    try:
        body = scraper.driver.find_element("tag name", "body")
        text = body.text
        for line in text.split('\n'):
            if "employers found" in line:
                print(f"    Final: {line.strip()}")
                break
    except:
        print("    Could not find employer count")
    
except Exception as e:
    print(f"[ERROR] {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    
finally:
    print("\n[8] Closing...")
    scraper.driver.quit()
    print("[OK] Done")
