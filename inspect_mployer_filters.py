#!/usr/bin/env python3
"""
Mployer Filter Inspector & Mapper
Uses DevTools to scan and map all available filters on the Mployer employer search page.
Creates a mapping that Buddy can use to fill filters intelligently.
"""

import os
import sys
import json
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

sys.path.insert(0, str(Path(__file__).parent.parent))


def inspect_mployer_filters():
    """
    Connect to Mployer and deeply inspect the filter structure
    """
    
    print("\n" + "="*70)
    print("MPLOYER FILTER INSPECTOR & MAPPER")
    print("="*70)
    
    username = os.getenv('MPLOYER_USERNAME')
    password = os.getenv('MPLOYER_PASSWORD')
    
    if not username or not password:
        print("❌ Missing credentials")
        return None
    
    from Back_End.mployer_scraper import MployerScraper
    
    # Create scraper
    scraper = MployerScraper(username, password, headless=False)
    scraper.initialize_browser()
    
    try:
        print("\n1️⃣  LOGGING IN...")
        if not scraper.login_to_mployer():
            print("❌ Login failed")
            return None
        
        print("\n2️⃣  NAVIGATING TO EMPLOYER SEARCH...")
        scraper.driver.get("https://portal.mployeradvisor.com/catalyst/employer")
        time.sleep(3)
        
        print("\n3️⃣  SCANNING PAGE FOR ALL FILTERS...")
        print("-" * 70)
        
        # Run comprehensive inspection script
        filter_map = scraper.driver.execute_script("""
        const filterMap = {
            timestamp: new Date().toISOString(),
            page_url: window.location.href,
            page_title: document.title,
            filters: [],
            form_data: {
                all_inputs: [],
                all_selects: [],
                all_buttons: []
            }
        };
        
        // ===== 1. FIND ALL INPUT FIELDS =====
        console.log("Scanning for input fields...");
        const inputs = document.querySelectorAll('input');
        console.log("Found " + inputs.length + " input elements");
        
        inputs.forEach((input, idx) => {
            const info = {
                index: idx,
                type: input.type,
                id: input.id,
                name: input.name,
                placeholder: input.placeholder,
                value: input.value,
                class: input.className,
                aria_label: input.getAttribute('aria-label'),
                aria_placeholder: input.getAttribute('aria-placeholder'),
                min: input.getAttribute('min'),
                max: input.getAttribute('max'),
                data_attrs: {}
            };
            
            // Capture all data-* attributes
            Array.from(input.attributes).forEach(attr => {
                if (attr.name.startsWith('data-')) {
                    info.data_attrs[attr.name] = attr.value;
                }
            });
            
            filterMap.form_data.all_inputs.push(info);
            
            // Try to infer what this field is for
            const searchTerms = (input.placeholder + ' ' + input.name + ' ' + input.getAttribute('aria-label') || '').toLowerCase();
            
            if (searchTerms.includes('employee') || searchTerms.includes('count') || searchTerms.includes('size')) {
                filterMap.filters.push({
                    type: 'EMPLOYEE_COUNT',
                    subtype: searchTerms.includes('min') ? 'min' : (searchTerms.includes('max') ? 'max' : 'unknown'),
                    element_type: 'input',
                    input_type: input.type,
                    selector_id: input.id ? '#' + input.id : null,
                    selector_name: input.name ? 'input[name="' + input.name + '"]' : null,
                    xpath: null,
                    placeholder: input.placeholder,
                    aria_label: input.getAttribute('aria-label'),
                    action: 'type_number'
                });
            }
            else if (searchTerms.includes('name') || searchTerms.includes('company')) {
                filterMap.filters.push({
                    type: 'COMPANY_NAME',
                    element_type: 'input',
                    selector_id: input.id ? '#' + input.id : null,
                    selector_name: input.name ? 'input[name="' + input.name + '"]' : null,
                    placeholder: input.placeholder,
                    action: 'type_text'
                });
            }
            else if (searchTerms.includes('location') || searchTerms.includes('city') || searchTerms.includes('state')) {
                filterMap.filters.push({
                    type: searchTerms.includes('city') ? 'CITY' : (searchTerms.includes('state') ? 'STATE' : 'LOCATION'),
                    element_type: 'input',
                    selector_id: input.id ? '#' + input.id : null,
                    selector_name: input.name ? 'input[name="' + input.name + '"]' : null,
                    placeholder: input.placeholder,
                    action: 'type_text'
                });
            }
            else if (searchTerms.includes('industry')) {
                filterMap.filters.push({
                    type: 'INDUSTRY',
                    element_type: 'input',
                    selector_id: input.id ? '#' + input.id : null,
                    selector_name: input.name ? 'input[name="' + input.name + '"]' : null,
                    placeholder: input.placeholder,
                    action: 'type_text_and_select'
                });
            }
            else if (searchTerms.includes('revenue')) {
                filterMap.filters.push({
                    type: 'REVENUE',
                    subtype: searchTerms.includes('min') ? 'min' : (searchTerms.includes('max') ? 'max' : 'unknown'),
                    element_type: 'input',
                    selector_id: input.id ? '#' + input.id : null,
                    selector_name: input.name ? 'input[name="' + input.name + '"]' : null,
                    action: 'type_number'
                });
            }
        });
        
        // ===== 2. FIND ALL SELECT DROPDOWNS =====
        console.log("Scanning for select dropdowns...");
        const selects = document.querySelectorAll('select');
        console.log("Found " + selects.length + " select elements");
        
        selects.forEach((select, idx) => {
            const info = {
                index: idx,
                id: select.id,
                name: select.name,
                class: select.className,
                options: []
            };
            
            Array.from(select.options).forEach(opt => {
                info.options.push({
                    value: opt.value,
                    text: opt.text
                });
            });
            
            filterMap.form_data.all_selects.push(info);
        });
        
        // ===== 3. FIND ALL BUTTONS =====
        console.log("Scanning for buttons...");
        const buttons = document.querySelectorAll('button');
        console.log("Found " + buttons.length + " button elements");
        
        buttons.forEach((btn, idx) => {
            const text = btn.innerText.substring(0, 50);
            const info = {
                index: idx,
                text: text,
                id: btn.id,
                class: btn.className,
                type: btn.type,
                disabled: btn.disabled,
                is_visible: btn.offsetHeight > 0
            };
            
            filterMap.form_data.all_buttons.push(info);
            
            // Try to identify filter-related buttons
            if (text.toLowerCase().includes('apply') || text.toLowerCase().includes('filter') || text.toLowerCase().includes('search')) {
                filterMap.filters.push({
                    type: 'ACTION_BUTTON',
                    action: text.toLowerCase().includes('apply') ? 'apply_filters' : 'search',
                    selector_text: text,
                    id: btn.id,
                    element_type: 'button'
                });
            }
        });
        
        // ===== 4. SCAN FOR CUSTOM FILTER COMPONENTS =====
        console.log("Scanning for custom filter components...");
        
        // Look for common filter container patterns
        const filterContainers = document.querySelectorAll('[class*="filter"], [class*="Filter"], [class*="sidebar"], [class*="Sidebar"], [role="region"]');
        console.log("Found " + filterContainers.length + " filter container elements");
        
        filterMap.form_data.filter_containers = filterContainers.length;
        
        // ===== 5. ANALYZE PAGE STRUCTURE =====
        console.log("Analyzing page structure...");
        filterMap.page_structure = {
            has_form: document.querySelector('form') !== null,
            form_count: document.querySelectorAll('form').length,
            form_ids: Array.from(document.querySelectorAll('form')).map(f => f.id || 'unnamed'),
            has_fieldsets: document.querySelector('fieldset') !== null,
            fieldset_count: document.querySelectorAll('fieldset').length
        };
        
        console.log("Inspection complete!");
        return filterMap;
        """)
        
        # Print detailed results
        print(f"\n✅ INSPECTION COMPLETE")
        print(f"Found {len(filter_map.get('filters', []))} filters detected\n")
        
        # Show detected filters
        print("DETECTED FILTERS:")
        print("-" * 70)
        for idx, filt in enumerate(filter_map.get('filters', []), 1):
            filter_type = filt.get('type', 'UNKNOWN')
            action = filt.get('action', '?')
            
            if filter_type == 'ACTION_BUTTON':
                print(f"{idx}. {filter_type:20} | Action: {filt.get('action', '?')}")
            elif filt.get('subtype'):
                print(f"{idx}. {filter_type:20} ({filt.get('subtype'):5}) | {filt.get('placeholder', 'ID: ' + (filt.get('selector_id') or '?'))}")
            else:
                print(f"{idx}. {filter_type:20} | {filt.get('placeholder', 'ID: ' + (filt.get('selector_id') or '?'))}")
        
        # Show all inputs found
        print(f"\n\nALL INPUT FIELDS ({len(filter_map['form_data']['all_inputs'])}):")
        print("-" * 70)
        for idx, inp in enumerate(filter_map['form_data']['all_inputs'], 1):
            name = inp.get('name') or inp.get('id') or inp.get('placeholder') or f"input_{idx}"
            inp_type = inp.get('type', 'text')
            placeholder = inp.get('placeholder', '')
            aria_label = inp.get('aria_label', '')
            
            print(f"{idx:3}. Type={inp_type:8} | Name: {name:30} | Placeholder: {placeholder:25} | Label: {aria_label}")
        
        # Show all buttons found
        print(f"\n\nALL BUTTONS ({len(filter_map['form_data']['all_buttons'])}):")
        print("-" * 70)
        for idx, btn in enumerate(filter_map['form_data']['all_buttons'][:15], 1):  # Show first 15
            text = btn.get('text', '')[:40]
            visible = "✓" if btn.get('is_visible') else "✗"
            print(f"{idx:3}. {visible} {text:45} (type={btn.get('type', '?')})")
        
        # Save mapping
        print(f"\n\nPAGE STRUCTURE:")
        print("-" * 70)
        structure = filter_map['page_structure']
        print(f"  Has form: {structure['has_form']}")
        print(f"  Form count: {structure['form_count']}")
        print(f"  Fieldsets: {structure['fieldset_count']}")
        
        # Save to file
        output_file = Path(__file__).parent / "mployer_filter_map.json"
        with open(output_file, 'w') as f:
            json.dump(filter_map, f, indent=2)
        
        print(f"\n\n✅ FILTER MAP SAVED")
        print("="*70)
        print(f"Saved to: {output_file}")
        print(f"\nYou can now use this mapping to fill filters!")
        print("\nKeep the browser window open to test filter filling...")
        
        # Keep browser open for manual inspection
        input("\nPress Enter to keep browser open for inspection, or close it...")
        
        return filter_map
    
    finally:
        print("\nClosing browser...")
        scraper.close()


if __name__ == "__main__":
    filter_map = inspect_mployer_filters()

