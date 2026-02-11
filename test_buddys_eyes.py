#!/usr/bin/env python3
"""
BUDDY'S EYES - DEMONSTRATION
Shows how Buddy uses his vision system to understand websites
"""

import os
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from Back_End.mployer_scraper import MployerScraper
from Back_End.buddys_vision import BuddysVision, BuddysVisionTasks


def main():
    print("\n" + "="*70)
    print("👀 BUDDY'S EYES - DEMONSTRATION")
    print("="*70)
    
    username = os.getenv('MPLOYER_USERNAME')
    password = os.getenv('MPLOYER_PASSWORD')
    
    if not username or not password:
        print("❌ Missing MPLOYER_USERNAME or MPLOYER_PASSWORD")
        return
    
    # Initialize Buddy
    print("\n🤖 Initializing Buddy...")
    scraper = MployerScraper(username, password, headless=False)
    scraper.initialize_browser()
    
    try:
        # Buddy logs in
        print("\n📝 Buddy is logging into Mployer...")
        if not scraper.login_to_mployer():
            print("❌ Login failed")
            return
        print("✅ Logged in")
        
        # Give Buddy eyes
        print("\n👀 Giving Buddy eyes...")
        vision = BuddysVision(scraper)
        print("✅ Buddy now has vision!")
        
        # What does Buddy see?
        print("\n" + "="*70)
        print("WHAT BUDDY SEES")
        print("="*70)
        print(f"\n{vision.what_do_you_see()}")
        
        # Buddy looks at the employer search page
        print("\n" + "="*70)
        print("BUDDY IS ANALYZING MPLOYER EMPLOYER SEARCH PAGE")
        print("="*70)
        
        url = "https://portal.mployeradvisor.com/catalyst/employer"
        print(f"\n👀 Buddy is looking at: {url}")
        
        inspection = vision.see_website(url)
        
        # Display what Buddy learned
        print("\n" + "="*70)
        print("WHAT BUDDY LEARNED")
        print("="*70)
        
        print(f"\n📋 Forms Found: {len(inspection.get('forms', []))}")
        for form in inspection.get('forms', [])[:3]:
            print(f"   • Form ID: {form.get('id')} | Action: {form.get('action')} | Fields: {len(form.get('fields', []))}")
        
        print(f"\n🔘 Buttons Found: {len(inspection.get('buttons', []))}")
        for btn in inspection.get('buttons', [])[:5]:
            if btn.get('text').strip():
                print(f"   • {btn.get('text')[:40]} (ID: {btn.get('id')})")
        
        print(f"\n📝 Input Fields Found: {len(inspection.get('inputs', []))}")
        for inp in inspection.get('inputs', [])[:5]:
            label = inp.get('placeholder') or inp.get('name') or f"Input {inp.get('index')}"
            print(f"   • {label} (Type: {inp.get('type')})")
        
        print(f"\n🔗 Links Found: {len(inspection.get('links', []))}")
        for link in inspection.get('links', [])[:3]:
            if link.get('text').strip():
                print(f"   • {link.get('text')[:40]} -> {link.get('href')[:50]}...")
        
        print(f"\n📊 Data Attributes Discovered: {len(inspection.get('data_attributes', {}))}")
        for attr, values in list(inspection.get('data_attributes', {}).items())[:5]:
            print(f"   • {attr}: {len(values)} occurrences")
        
        print(f"\n🔑 Key Selectors Identified:")
        selectors = inspection.get('selectors', {})
        print(f"   • Unique IDs: {len(selectors.get('common_ids', []))}")
        print(f"   • Unique Classes: {len(selectors.get('common_classes', []))}")
        
        # Buddy's memory
        print("\n" + "="*70)
        print("BUDDY'S MEMORY")
        print("="*70)
        
        knowledge_file = Path("buddy_site_knowledge.json")
        if knowledge_file.exists():
            with open(knowledge_file) as f:
                knowledge = json.load(f)
            print(f"\n💾 Buddy remembers {len(knowledge)} websites")
            for domain in list(knowledge.keys())[:5]:
                print(f"   • {domain}")
        
        # Buddy finds elements
        print("\n" + "="*70)
        print("BUDDY FINDING ELEMENTS BY ACTION")
        print("="*70)
        
        actions = ["Apply", "Filter", "Search", "Submit", "Clear"]
        print("\nBuddy looking for elements:")
        for action in actions:
            element = vision.find_element(action)
            if element:
                print(f"   ✓ {action:15} -> Found: {element}")
            else:
                print(f"   ✗ {action:15} -> Not found")
        
        # Create site profile
        print("\n" + "="*70)
        print("BUDDY'S SITE PROFILE")
        print("="*70)
        
        profile = BuddysVisionTasks.create_site_profile(vision.eyes, url)
        print(f"\n📊 Site Profile Summary:")
        print(f"   Title: {profile['summary']['title']}")
        print(f"   Forms: {profile['summary']['forms']}")
        print(f"   Buttons: {profile['summary']['buttons']}")
        print(f"   Inputs: {profile['summary']['inputs']}")
        print(f"   Has Auth: {profile['summary']['has_auth']}")
        
        # Save detailed inspection
        output_file = Path("buddy_inspection_report.json")
        with open(output_file, 'w') as f:
            # Convert to JSON-serializable format
            json.dump(inspection, f, indent=2, default=str)
        print(f"\n✅ Detailed inspection saved to: {output_file}")
        
        # Summary
        print("\n" + "="*70)
        print("✅ BUDDY'S VISION SYSTEM WORKING")
        print("="*70)
        print("""
Buddy can now:
  ✅ See website structure (forms, buttons, inputs, links)
  ✅ Learn site patterns (data attributes, IDs, classes)
  ✅ Understand navigation (menus, breadcrumbs, sections)
  ✅ Find interactive elements (by action names)
  ✅ Remember site knowledge (persistent JSON database)
  ✅ Adapt to site changes (re-inspection capability)
  ✅ Create site profiles (detailed summaries)
  ✅ Compare websites (understand differences)

This is Buddy's vision system - his eyes to understand any website!
        """)
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print("\nClosing browser...")
        scraper.close()
        print("✅ Done")


if __name__ == "__main__":
    main()

