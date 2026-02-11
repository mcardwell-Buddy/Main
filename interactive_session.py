"""
Interactive Mployer Session - Keep browser open and run multiple operations
"""
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

from Back_End.mployer_scraper import MployerScraper
from Back_End.page_inspector import inspect_page_elements, print_inspection_report
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')

username = os.getenv("MPLOYER_USERNAME")
password = os.getenv("MPLOYER_PASSWORD")

print("\n" + "=" * 80)
print("MPLOYER INTERACTIVE SESSION")
print("=" * 80)
print(f"User: {username}")
print("Browser will stay open for multiple operations")
print("=" * 80)

# Initialize and login once
scraper = MployerScraper(username, password, headless=False)
scraper.initialize_browser()

success = scraper.login_to_mployer()

if not success:
    print("\n✗ Login failed")
    scraper.driver.quit()
    sys.exit(1)

print("\n✓ Logged in successfully! Session is active.")
print("\n" + "=" * 80)

# Interactive menu
while True:
    print("\nAvailable commands:")
    print("  1. Navigate to Employer Search")
    print("  2. Inspect current page")
    print("  3. Run employer search")
    print("  4. Take screenshot")
    print("  5. Get current URL")
    print("  6. Custom navigation (enter URL)")
    print("  7. Test filters (check if they work)")
    print("  q. Quit and close browser")
    
    choice = input("\nEnter command: ").strip().lower()
    
    if choice == 'q':
        print("\nClosing browser and exiting...")
        scraper.driver.quit()
        break
    
    elif choice == '1':
        print("\nNavigating to Employer Search...")
        scraper.driver.get("https://portal.mployeradvisor.com/catalyst/employer")
        import time
        time.sleep(3)
        print(f"✓ Current URL: {scraper.driver.current_url}")
    
    elif choice == '2':
        print("\nInspecting current page...")
        report = inspect_page_elements(scraper.driver)
        print_inspection_report(report)
    
    elif choice == '3':
        print("\nEmployer Search Configuration:")
        emp_name = input("  Employer name (or press Enter to skip): ").strip()
        min_emp = input("  Min employees (or press Enter to skip): ").strip()
        max_emp = input("  Max employees (or press Enter to skip): ").strip()
        city = input("  City (or press Enter to skip): ").strip()
        state = input("  State (or press Enter to skip): ").strip()
        
        print("\nRunning search...")
        employers = scraper.search_employers(
            employer_name=emp_name if emp_name else None,
            employees_min=int(min_emp) if min_emp else None,
            employees_max=int(max_emp) if max_emp else None,
            city=city if city else None,
            state=state if state else None
        )
        
        print(f"\n✓ Found {len(employers)} employers")
        if employers:
            print("\nFirst 5 results:")
            for i, emp in enumerate(employers[:5], 1):
                print(f"  {i}. {emp}")
    
    elif choice == '4':
        import time
        filename = f"screenshot_{int(time.time())}.png"
        scraper.driver.save_screenshot(filename)
        print(f"✓ Screenshot saved to {filename}")
    
    elif choice == '5':
        print(f"\nCurrent URL: {scraper.driver.current_url}")
        print(f"Page Title: {scraper.driver.title}")
    
    elif choice == '6':
        url = input("Enter URL: ").strip()
        if url:
            print(f"Navigating to {url}...")
            scraper.driver.get(url)
            import time
            time.sleep(2)
            print(f"✓ Current URL: {scraper.driver.current_url}")
    
    elif choice == '7':
        print("\n" + "=" * 80)
        print("COMPREHENSIVE FILTER TEST - URL PARAMETER BASED")
        print("=" * 80)
        from selenium.webdriver.common.by import By
        import time
        
        url_before = scraper.driver.current_url
        print(f"\n[START URL] {url_before}")
        
        # Test 1: Employee Range Filter
        print("\n[TEST 1] Setting Employee Range: min=100, max=750")
        scraper.driver.execute_script('''
        const minField = document.getElementById('minFilter');
        const maxField = document.getElementById('maxFilter');
        if (minField) { minField.value = '100'; minField.dispatchEvent(new Event('input', {bubbles: true})); }
        if (maxField) { maxField.value = '750'; maxField.dispatchEvent(new Event('input', {bubbles: true})); }
        ''')
        time.sleep(0.5)
        
        # Find and click Apply Filters using span selector
        print("[ACTION] Clicking Apply Filters...")
        try:
            apply_btn = scraper.driver.find_element(By.XPATH, "//button[.//span[contains(text(), 'Apply Filters')]]")
            scraper.driver.execute_script('arguments[0].scrollIntoView(true);', apply_btn)
            time.sleep(0.3)
            scraper.driver.execute_script('arguments[0].click();', apply_btn)
            print("  ✓ Apply button clicked!")
            time.sleep(5)
        except Exception as e:
            print(f"  ✗ ERROR: {str(e)[:100]}")
        
        url_after = scraper.driver.current_url
        print(f"\n[RESULT URL] {url_after}")
        
        if url_before != url_after:
            print("✓ URL CHANGED - Filters applied!")
            # Parse URL to show what was applied
            if 'participantsMinFilter' in url_after or 'participantsMaxFilter' in url_after:
                print("  Query parameters in URL:")
                if 'participantsMinFilter' in url_after:
                    print("    • participantsMinFilter found")
                if 'participantsMaxFilter' in url_after:
                    print("    • participantsMaxFilter found")
        else:
            print("✗ URL SAME - Filters not applied")
        
        # Show all filter types available
        print("\n[AVAILABLE FILTERS]")
        interactive = scraper.driver.execute_script('''
        return {
            textInputs: Array.from(document.querySelectorAll('input[type="text"]'))
                .map(i => ({id: i.id, name: i.name, placeholder: i.placeholder}))
                .slice(0, 15),
            checkboxes: Array.from(document.querySelectorAll('input[type="checkbox"]')).length,
            buttons: Array.from(document.querySelectorAll('button'))
                .filter(b => b.textContent.trim() && b.offsetHeight > 0)
                .map(b => b.textContent.trim().substring(0, 30))
                .slice(0, 20)
        };
        ''')
        
        print(f"  Text Input Fields: {len(interactive['textInputs'])}")
        for inp in interactive['textInputs']:
            print(f"    • {inp['id'] or inp['name'] or inp['placeholder']}")
        
        print(f"\n  Checkboxes: {interactive['checkboxes']} (for Yes/No filters)")
        
        print(f"\n  Visible Buttons: {len(interactive['buttons'])}")
        for btn in interactive['buttons']:
            print(f"    • {btn}")
    
    else:
        print("Invalid command. Please try again.")

print("\nSession ended.")

