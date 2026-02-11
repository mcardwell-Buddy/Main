"""Test Mployer login with automatic MFA"""
import os
import sys
from pathlib import Path

# Load .env
env_path = Path('.env')
for line in env_path.read_text().splitlines():
    if not line or line.strip().startswith('#') or '=' not in line:
        continue
    k, v = line.split('=', 1)
    os.environ.setdefault(k.strip(), v.strip())

# Test Mployer login
from Back_End.mployer_scraper import MployerScraper
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')

username = os.getenv("MPLOYER_USERNAME")
password = os.getenv("MPLOYER_PASSWORD")

print(f"\nTesting Mployer login for: {username}")
print("=" * 60)

scraper = MployerScraper(username, password, headless=False)
scraper.initialize_browser()

success = scraper.login_to_mployer()

if success:
    print("\n" + "=" * 60)
    print("✓ LOGIN SUCCESSFUL!")
    print("=" * 60)
    
    # Navigate to employer search
    print("\nNavigating to Employer Search...")
    try:
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.common.by import By
        import time
        
        # Navigate directly to employer search page
        scraper.driver.get("https://portal.mployeradvisor.com/catalyst/employer")
        print("✓ Navigated to Employer Search page")
        
        # Wait for page to load
        time.sleep(3)
        
        print(f"\nCurrent URL: {scraper.driver.current_url}")
        print(f"Page Title: {scraper.driver.title}")
        
        print("\n" + "=" * 60)
        print("Analyzing search fields and their labels...")
        print("=" * 60)
        
        # Find all autocomplete inputs
        autocomplete_inputs = scraper.driver.find_elements(By.CSS_SELECTOR, "input.rz-autocomplete-input")
        print(f"\nFound {len(autocomplete_inputs)} autocomplete fields:")
        for i, inp in enumerate(autocomplete_inputs, 1):
            placeholder = inp.get_attribute("placeholder")
            # Try to find nearby label
            try:
                parent = inp.find_element(By.XPATH, "./ancestor::div[contains(@class, 'rz-autocomplete') or contains(@class, 'form-group') or contains(@class, 'field')]")
                label = parent.find_element(By.XPATH, "./preceding-sibling::label | ./preceding-sibling::div//label | ./ancestor::*//label")
                label_text = label.text
            except:
                try:
                    # Look for any nearby text
                    parent = inp.find_element(By.XPATH, "./ancestor::div[1]")
                    label_text = parent.text.split('\n')[0] if parent.text else "No label"
                except:
                    label_text = "No label found"
            
            print(f"  {i}. Placeholder: '{placeholder}', Nearby text: '{label_text[:50]}'")
        
        # Find min/max filters
        print(f"\nNumber range filters:")
        min_filter = scraper.driver.find_element(By.ID, "minFilter")
        max_filter = scraper.driver.find_element(By.ID, "maxFilter")
        print(f"  - Min field: ID='minFilter', Placeholder='{min_filter.get_attribute('placeholder')}'")
        print(f"  - Max field: ID='maxFilter', Placeholder='{max_filter.get_attribute('placeholder')}'")
        
        # Find Apply Filters button
        try:
            apply_btn = scraper.driver.find_element(By.XPATH, "//span[contains(text(), 'Apply Filters')]")
            print(f"\n✓ Found 'Apply Filters' button")
        except:
            print(f"\n✗ 'Apply Filters' button not found")
        
        # Get all visible text on the page to understand field labels
        print("\n" + "=" * 60)
        print("Visible labels and headings on page:")
        print("=" * 60)
        
        # Look for common label patterns
        labels = scraper.driver.find_elements(By.TAG_NAME, "label")
        for label in labels[:20]:
            if label.text.strip():
                print(f"  - {label.text.strip()}")
        
        # Look for headings
        for tag in ['h1', 'h2', 'h3', 'h4']:
            headings = scraper.driver.find_elements(By.TAG_NAME, tag)
            for h in headings:
                if h.text.strip():
                    print(f"  - [{tag.upper()}] {h.text.strip()}")
        
        print("\n" + "=" * 60)
        print("Ready to implement search functionality!")
        print("=" * 60)
        print("\nLook at the browser to identify which field is for what...")
        input("\nPress Enter to close browser and exit...")
        
    except Exception as e:
        print(f"\n✗ Error during navigation: {e}")
        print(f"Current URL: {scraper.driver.current_url}")
        import traceback
        traceback.print_exc()
        print("\nTaking screenshot for debugging...")
        scraper.driver.save_screenshot("employer_search_error.png")
        print("Screenshot saved to employer_search_error.png")
        input("\nPress Enter to close browser and exit...")
else:
    print("\n" + "=" * 60)
    print("✗ LOGIN FAILED")
    print("=" * 60)
    input("\nPress Enter to close browser and exit...")

if scraper.driver:
    scraper.driver.quit()

