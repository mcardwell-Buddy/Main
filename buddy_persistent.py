#!/usr/bin/env python3
"""
BUDDY PERSISTENT SESSION
=========================
Keep browser window OPEN - DO NOT CLOSE between tests
Uses developer inspection data to understand page structure
"""

import os
import sys
import time
import json
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

load_dotenv(Path(__file__).parent / '.env')
sys.path.insert(0, str(Path(__file__).parent))

from Back_End.mployer_scraper import MployerScraper
from selenium.webdriver.common.by import By

username = os.getenv("MPLOYER_USERNAME")
password = os.getenv("MPLOYER_PASSWORD")

if not username or not password:
    print("ERROR: Set MPLOYER_USERNAME and MPLOYER_PASSWORD in .env")
    sys.exit(1)

print("\n" + "="*90)
print("BUDDY PERSISTENT SESSION - Browser window will STAY OPEN")
print("="*90)
print("\nInitializing...\n")

# Initialize scraper (do NOT close browser in this session)
scraper = MployerScraper(username, password, headless=False)
scraper.initialize_browser()

try:
    # LOGIN
    print("[LOGIN] Logging in to Mployer (using saved cookies if available)...")
    if not scraper.login_to_mployer():
        print("[FAIL] Login failed - exiting")
        sys.exit(1)
    print("[OK] Logged in successfully\n")
    
    # NAVIGATE
    print("[NAVIGATE] Going to Employer Search page...")
    scraper.driver.get("https://portal.mployeradvisor.com/catalyst/employer")
    time.sleep(3)
    print("[OK] On Employer Search page\n")
    
    # INSPECTION - Read all page elements like developer tools would
    print("[INSPECT] Reading page structure from developer inspection...")
    inspection = scraper.inspect_page_elements()
    
    print(f"  Found {inspection['counts']['total_inputs']} input fields")
    print(f"  Found {inspection['counts']['total_buttons']} buttons")
    print(f"  Found {inspection['counts']['total_tables']} tables")
    print(f"  Current employer count: {inspection['page_state']['employer_count']}")
    
    # Save inspection data for reference
    scraper.save_inspection_to_file(inspection, "page_inspection.json")
    print("  Inspection saved to page_inspection.json\n")
    
    # Show filter fields found
    print("[FILTER FIELDS] Available filters:")
    filter_inputs = [inp for inp in inspection['inputs'] if inp['is_filter_field']]
    for inp in filter_inputs[:10]:
        status = "VISIBLE" if inp['is_visible'] else "HIDDEN"
        print(f"  - {inp['id'] or inp['name']:20} = '{inp['value']}' [{status}]")
    
    print("\n" + "="*90)
    print("INTERACTIVE MODE - Browser is OPEN. Commands:")
    print("="*90)
    print("  help              - Show all commands")
    print("  inspect           - Refresh inspection data")
    print("  filters           - Show available filters")
    print("  set-min <value>   - Set minimum employees filter")
    print("  set-max <value>   - Set maximum employees filter")
    print("  apply             - Click 'Apply Filters' button")
    print("  count             - Show current employer count")
    print("  extract           - Extract employer results")
    print("  state <name>      - Set state filter (e.g., Maryland)")
    print("  clear             - Clear all filters")
    print("  quit              - Close browser and exit")
    print("="*90)
    
    session_start = datetime.now()
    
    # INTERACTIVE LOOP - Keep browser open
    while True:
        cmd = input("\n[buddy]> ").strip().lower()
        
        if not cmd:
            continue
        
        # ===== QUIT =====
        if cmd == "quit":
            response = input("Close browser and exit? (yes/no): ").strip().lower()
            if response in ['yes', 'y']:
                break
            else:
                print("[OK] Staying in session")
                continue
        
        # ===== HELP =====
        elif cmd == "help":
            print("\nAvailable commands:")
            print("  help              - Show this help")
            print("  inspect           - Read page structure again")
            print("  filters           - List all filter fields found")
            print("  set-min <N>       - Set min employees to N")
            print("  set-max <N>       - Set max employees to N")
            print("  apply             - Click Apply Filters button")
            print("  count             - Show current employer count on page")
            print("  extract           - Extract and show employer results")
            print("  state <name>      - Set state filter")
            print("  clear             - Clear all filters")
            print("  page              - Show current page info")
            print("  quit              - Exit (closes browser)")
        
        # ===== INSPECT =====
        elif cmd == "inspect":
            print("[REFRESHING] Reading page structure...")
            inspection = scraper.inspect_page_elements()
            scraper.save_inspection_to_file(inspection, "page_inspection.json")
            print(f"  {inspection['counts']['total_inputs']} inputs")
            print(f"  {inspection['counts']['total_buttons']} buttons")
            print(f"  Employer count: {inspection['page_state']['employer_count']}")
        
        # ===== FILTERS =====
        elif cmd == "filters":
            filter_inputs = [inp for inp in inspection['inputs'] if inp['is_filter_field']]
            print(f"\nFound {len(filter_inputs)} filter fields:")
            for inp in filter_inputs:
                status = "[V]" if inp['is_visible'] else "[H]"
                print(f"  {status} {inp['id'] or inp['name']:20s} = {inp['value']}")
        
        # ===== SET MIN =====
        elif cmd.startswith("set-min "):
            value = cmd.split(" ", 1)[1].strip()
            print(f"[SET] Setting minFilter to {value}...")
            try:
                scraper.driver.execute_script(f"""
                const field = document.getElementById('minFilter');
                if (field) {{
                    field.value = '{value}';
                    field.dispatchEvent(new Event('input', {{bubbles: true}}));
                    field.dispatchEvent(new Event('change', {{bubbles: true}}));
                }}
                """)
                print(f"  [OK] Set to {value}")
            except Exception as e:
                print(f"  [ERROR] {e}")
        
        # ===== SET MAX =====
        elif cmd.startswith("set-max "):
            value = cmd.split(" ", 1)[1].strip()
            print(f"[SET] Setting maxFilter to {value}...")
            try:
                scraper.driver.execute_script(f"""
                const field = document.getElementById('maxFilter');
                if (field) {{
                    field.value = '{value}';
                    field.dispatchEvent(new Event('input', {{bubbles: true}}));
                    field.dispatchEvent(new Event('change', {{bubbles: true}}));
                }}
                """)
                print(f"  [OK] Set to {value}")
            except Exception as e:
                print(f"  [ERROR] {e}")
        
        # ===== APPLY =====
        elif cmd == "apply":
            print("[APPLY] Clicking 'Apply Filters' button...")
            try:
                from selenium.webdriver.common.by import By
                apply_btn = scraper.driver.find_element(By.XPATH, "//button[contains(text(), 'Apply Filters')]")
                scraper.driver.execute_script("arguments[0].click();", apply_btn)
                print("[OK] Clicked Apply Filters")
                time.sleep(3)
                # Get new count
                inspection = scraper.inspect_page_elements()
                print(f"  New employer count: {inspection['page_state']['employer_count']}")
            except Exception as e:
                print(f"  [ERROR] {e}")
        
        # ===== COUNT =====
        elif cmd == "count":
            inspection = scraper.inspect_page_elements()
            print(f"Current employer count: {inspection['page_state']['employer_count']}")
        
        # ===== EXTRACT =====
        elif cmd == "extract":
            print("[EXTRACT] Extracting employer results...")
            results = scraper._extract_employer_results()
            print(f"Extracted {len(results)} employers")
            if results:
                print("\nFirst 5 results:")
                for i, emp in enumerate(results[:5], 1):
                    print(f"  {i}. {emp.get('name', 'N/A')}")
                    if emp.get('employees'):
                        print(f"     Employees: {emp.get('employees')}")
                    if emp.get('location'):
                        print(f"     Location: {emp.get('location')}")
        
        # ===== COUNT SHORTCUT =====
        elif cmd == "page":
            print(f"Current URL: {scraper.driver.current_url}")
            print(f"Page title: {scraper.driver.title}")
            body = scraper.driver.find_element(By.TAG_NAME, "body")
            for line in body.text.split('\n'):
                if "employers found" in line:
                    print(f"Results: {line.strip()}")
                    break
        
        # ===== STATE FILTER =====
        elif cmd.startswith("state "):
            state = cmd.split(" ", 1)[1].strip()
            print(f"[STATE] Setting state filter to {state}...")
            print("  (This would need state field selector - check inspection.json)")
        
        # ===== CLEAR =====
        elif cmd == "clear":
            print("[CLEAR] Clearing filters...")
            try:
                clear_btn = scraper.driver.find_element(By.XPATH, "//button[contains(text(), 'Clear')]")
                scraper.driver.execute_script("arguments[0].click();", clear_btn)
                print("[OK] Cleared filters")
                time.sleep(2)
            except Exception as e:
                print(f"  [NO CLEAR BUTTON] {e}")
        
        else:
            print(f"Unknown command: '{cmd}' (type 'help' for commands)")
    
    print("\n[CLOSING] Browser closing...")
    
except Exception as e:
    print(f"\n[ERROR] {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    input("\nPress Enter to close browser...")

finally:
    elapsed = datetime.now() - session_start
    print(f"\nSession duration: {elapsed}")
    print("Closing browser...")
    scraper.driver.quit()
    print("[OK] Browser closed. Goodbye!")

