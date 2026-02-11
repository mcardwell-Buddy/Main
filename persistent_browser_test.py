#!/usr/bin/env python3
"""
Interactive Mployer Search Test - Persistent Browser
Tests filter application and data extraction with a persistent browser window
"""

import os
import sys
import json
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from Back_End.mployer_scraper import MployerScraper

# Global persistent browser
persistent_scraper = None
browser_ready = False


def init_persistent_browser():
    """Initialize persistent browser - reuse across tests"""
    global persistent_scraper, browser_ready
    
    print("\n" + "="*70)
    print("INITIALIZING PERSISTENT BROWSER")
    print("="*70)
    
    username = os.getenv('MPLOYER_USERNAME')
    password = os.getenv('MPLOYER_PASSWORD')
    
    if not username or not password:
        print("❌ ERROR: Missing MPLOYER_USERNAME or MPLOYER_PASSWORD")
        return False
    
    try:
        # Create scraper with visible browser
        persistent_scraper = MployerScraper(username, password, headless=False)
        persistent_scraper.initialize_browser()
        
        # Login
        print("\n📝 LOGGING IN...")
        if persistent_scraper.login_to_mployer():
            print("✅ Logged in successfully")
            browser_ready = True
            print("\n💡 Browser is now persistent - ready for tests")
            print("⏳ Keeping browser open for testing...")
            return True
        else:
            print("❌ Login failed")
            persistent_scraper.close()
            return False
    
    except Exception as e:
        print(f"❌ Failed to initialize browser: {e}")
        return False


def test_filters_and_extraction():
    """Test filter application and employer extraction"""
    global persistent_scraper, browser_ready
    
    if not browser_ready or not persistent_scraper:
        print("❌ Browser not ready. Initialize first.")
        return None
    
    print("\n" + "="*70)
    print("TEST: APPLYING FILTERS & EXTRACTING DATA")
    print("="*70)
    
    try:
        print("\n🔍 STEP 1: NAVIGATE TO SEARCH")
        print("-" * 70)
        persistent_scraper.driver.get("https://portal.mployeradvisor.com/catalyst/employer")
        time.sleep(3)
        print(f"✓ Current URL: {persistent_scraper.driver.current_url}")
        
        print("\n📋 STEP 2: APPLYING FILTERS")
        print("-" * 70)
        
        # Test employee count filter
        print("  Applying employee range: 50-5000...")
        persistent_scraper.driver.execute_script("""
        // Find all number inputs
        const inputs = document.querySelectorAll('input[type="number"]');
        console.log('Found ' + inputs.length + ' number inputs');
        
        let minSet = false, maxSet = false;
        for (let i = 0; i < inputs.length; i++) {
            const input = inputs[i];
            const name = input.name || '';
            const placeholder = input.placeholder || '';
            const label = input.getAttribute('aria-label') || '';
            
            console.log('Input ' + i + ': name="' + name + '" placeholder="' + placeholder + '" aria-label="' + label + '"');
            
            // Try to find min field
            if (!minSet && (name.includes('min') || placeholder.includes('Min') || label.includes('min'))) {
                input.value = '50';
                input.dispatchEvent(new Event('input', {bubbles: true}));
                input.dispatchEvent(new Event('change', {bubbles: true}));
                minSet = true;
                console.log('Set MIN to 50');
            }
            // Try to find max field
            else if (!maxSet && (name.includes('max') || placeholder.includes('Max') || label.includes('max'))) {
                input.value = '5000';
                input.dispatchEvent(new Event('input', {bubbles: true}));
                input.dispatchEvent(new Event('change', {bubbles: true}));
                maxSet = true;
                console.log('Set MAX to 5000');
            }
        }
        """)
        time.sleep(1)
        print("  ✓ Employee filter values set")
        
        # Try to apply filters
        print("\n  Clicking 'Apply Filters' button...")
        try:
            apply_btns = persistent_scraper.driver.find_elements("xpath", 
                "//span[contains(text(), 'Apply')]/ancestor::button | //button[contains(text(), 'Apply')]")
            if apply_btns:
                persistent_scraper.driver.execute_script("arguments[0].click();", apply_btns[0])
                print("  ✓ Apply Filters button clicked")
                time.sleep(5)
            else:
                print("  ⚠️  Apply Filters button not found")
        except Exception as e:
            print(f"  ⚠️  Could not click button: {e}")
        
        print("\n📊 STEP 3: EXTRACTING RESULTS")
        print("-" * 70)
        
        # Analyze page structure
        print("  Analyzing page structure...")
        analysis = persistent_scraper.driver.execute_script("""
        return {
            tables: document.querySelectorAll('table').length,
            rows: document.querySelectorAll('tr').length,
            divs_with_role_row: document.querySelectorAll('[role="row"]').length,
            divs_with_role_cell: document.querySelectorAll('[role="cell"]').length,
            body_text_length: document.body.innerText.length,
            has_results_keyword: document.body.innerText.includes('results') || 
                                 document.body.innerText.includes('Results'),
            page_title: document.title
        };
        """)
        
        print(f"  Tables: {analysis['tables']}")
        print(f"  Table Rows: {analysis['rows']}")
        print(f"  Divs with role='row': {analysis['divs_with_role_row']}")
        print(f"  Divs with role='cell': {analysis['divs_with_role_cell']}")
        print(f"  Page has 'results' keyword: {analysis['has_results_keyword']}")
        print(f"  Page title: {analysis['page_title']}")
        
        # Extract data using existing method
        print("\n  Extracting employer data...")
        employers = persistent_scraper._extract_employer_results()
        
        print(f"\n✅ EXTRACTION COMPLETE")
        print("-" * 70)
        print(f"Found {len(employers)} employers\n")
        
        if employers:
            print("First 5 employers:")
            for i, emp in enumerate(employers[:5], 1):
                print(f"\n  {i}. {emp.get('name', 'UNKNOWN')}")
                for key in ['employees', 'location', 'industry', 'rating']:
                    if emp.get(key):
                        print(f"     {key}: {emp.get(key)}")
        
        # Save results
        output_file = Path(__file__).parent / "test_mployer_results.json"
        with open(output_file, 'w') as f:
            json.dump(employers, f, indent=2)
        print(f"\n✓ Results saved to {output_file}")
        
        return employers
    
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return None


def interactive_test_loop():
    """Keep browser open and allow multiple tests"""
    global persistent_scraper, browser_ready
    
    if not init_persistent_browser():
        print("Failed to initialize persistent browser")
        return
    
    while True:
        print("\n" + "="*70)
        print("PERSISTENT BROWSER TEST MENU")
        print("="*70)
        print("\n1. Test filters & extraction")
        print("2. Run custom search")
        print("3. Inspect page (show structure)")
        print("4. Navigate to page")
        print("5. Close browser & exit")
        print("\nEnter choice (1-5): ", end="")
        
        choice = input().strip()
        
        if choice == "1":
            test_filters_and_extraction()
        
        elif choice == "2":
            print("\nEnter search URL or 'employer' for default: ", end="")
            url = input().strip()
            if url == "employer" or not url:
                url = "https://portal.mployeradvisor.com/catalyst/employer"
            elif not url.startswith("http"):
                url = f"https://portal.mployeradvisor.com/catalyst/{url}"
            
            print(f"Navigating to {url}...")
            persistent_scraper.driver.get(url)
            time.sleep(3)
            print(f"✓ Loaded: {persistent_scraper.driver.title}")
        
        elif choice == "3":
            print("\nInspecting page structure...")
            time.sleep(1)
            test_filters_and_extraction()
        
        elif choice == "4":
            print("\nEnter URL: ", end="")
            url = input().strip()
            if url:
                persistent_scraper.driver.get(url)
                time.sleep(3)
                print(f"✓ Navigated to: {persistent_scraper.driver.title}")
        
        elif choice == "5":
            print("\nClosing browser...")
            persistent_scraper.close()
            print("✓ Browser closed. Goodbye!")
            break
        
        else:
            print("Invalid choice, try again")


if __name__ == "__main__":
    interactive_test_loop()

