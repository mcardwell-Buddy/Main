#!/usr/bin/env python3
"""
BUDDY'S VISION SYSTEM
High-level interface for web inspection and learning (INSPECTION ONLY).

Vision is responsible for:
  ✓ Inspecting websites
  ✓ Extracting DOM structure
  ✓ Finding elements by action
  ✓ Remembering site patterns
  
Vision is NOT responsible for:
  ✗ Executing actions (clicks, fills, navigation)
  ✗ Those are Legs/Arms responsibility
  ✗ Never calls Arms or Legs directly
"""

from Back_End.buddys_vision_core import BuddysVisionCore
from Back_End.profile_manager import load_profile


class BuddysVision:
    """
    Vision subsystem - INSPECTION ONLY.
    
    Gives Buddy the ability to inspect websites and extract information.
    Does NOT execute any actions - returns recommendations only.
    """
    
    def __init__(self, scraper=None, driver=None):
        """Initialize vision with a scraper instance or Selenium driver"""
        if scraper is None and driver is None:
            raise ValueError("Provide either scraper or driver")
        self.scraper = scraper
        self.driver = driver or getattr(scraper, "driver", None)
        if self.driver is None:
            raise ValueError("Scraper must expose .driver or pass driver explicitly")
        # Vision core for inspection only
        self.core = BuddysVisionCore(self.driver)
    
    def see_website(self, url: str, expand_interactive: bool = True) -> dict:
        """Buddy looks at a website and learns its structure"""
        print(f"\n[VISION] LOOKING AT: {url}")
        return self.core.inspect_website(url, expand_interactive=expand_interactive)
    
    def remember_site(self, url: str, expand_interactive: bool = True) -> None:
        """Buddy memorizes a site's structure"""
        self.see_website(url, expand_interactive=expand_interactive)
    
    def understand_site(self, url: str, expand_interactive: bool = True) -> dict:
        """Get full understanding of a site's structure"""
        return self.see_website(url, expand_interactive=expand_interactive)
    
    def find_element(self, action: str) -> str:
        """Buddy asks 'where is the element to [action]'"""
        return self.core.find_element_for_action(action)
    
    def remember_about_site(self, domain: str) -> dict:
        """Buddy recalls what he knows about a site"""
        return self.core.get_knowledge_about_site(domain)
    
    def what_do_you_see(self) -> str:
        """Buddy describes what he currently sees"""
        title = self.driver.title
        url = self.driver.current_url
        return f"I see a page titled '{title}' at {url}"
    
    def analyze_and_learn(self, url: str) -> dict:
        """Comprehensive analysis and learning"""
        print(f"\n[VISION] ANALYZING AND LEARNING FROM: {url}")
        inspection = self.see_website(url)
        print(f"\n[OK] BUDDY HAS LEARNED ABOUT: {url}")
        return inspection

    def autofill_signup_form(self, profile: dict = None, submit: bool = False) -> dict:
        """
        INSPECT signup form and return the structure.
        
        Note: The actual filling is done by Arms/Legs, not Vision.
        Vision only inspects and reports what it finds.
        
        Args:
            profile: User profile for analysis (not used for actual filling)
            submit: Not used - Vision never submits forms
            
        Returns:
            Form structure and metadata for Arms to use when filling
        """
        if profile is None:
            profile = load_profile()
        # Vision only inspects the form structure
        return self.core.inspect_forms_on_page()


# Quick reference for common vision tasks
class BuddysVisionTasks:
    """Common vision-based tasks Buddy can perform"""
    
    @staticmethod
    def create_site_profile(core: BuddysVisionCore, url: str) -> dict:
        """Create a complete profile of a website"""
        inspection = core.inspect_website(url)
        
        profile = {
            "site": url,
            "summary": {
                "title": inspection.get('page_title'),
                "forms": len(inspection.get('forms', [])),
                "buttons": len(inspection.get('buttons', [])),
                "inputs": len(inspection.get('inputs', [])),
                "has_auth": inspection.get('auth_elements', {}).get('has_login', False),
            },
            "key_selectors": {},
            "interactions": []
        }
        
        # Identify key selectors
        for btn in inspection.get('buttons', [])[:5]:
            if btn.get('id'):
                profile['key_selectors'][btn.get('text', f"Button {btn['index']}")] = f"#{btn['id']}"
        
        return profile
    
    @staticmethod
    def compare_sites(core: BuddysVisionCore, url1: str, url2: str) -> dict:
        """Compare two websites to understand their differences"""
        site1 = core.inspect_website(url1)
        site2 = core.inspect_website(url2)
        
        comparison = {
            "site1": url1,
            "site2": url2,
            "differences": {
                "forms_diff": len(site1.get('forms', [])) - len(site2.get('forms', [])),
                "buttons_diff": len(site1.get('buttons', [])) - len(site2.get('buttons', [])),
                "auth_approaches": {
                    "site1": site1.get('auth_elements', {}),
                    "site2": site2.get('auth_elements', {})
                }
            }
        }
        
        return comparison


# Integration example
def buddy_learn_mployer(scraper):
    """Example: Buddy learns the Mployer site structure"""
    vision = BuddysVision(scraper)
    
    print("\n[VISION] LEARNING MPLOYER STRUCTURE")
    print("="*70)
    
    # Navigate and inspect
    vision.remember_site("https://portal.mployeradvisor.com/catalyst/employer")
    
    print("\n[OK] BUDDY NOW UNDERSTANDS MPLOYER")
    return vision


if __name__ == "__main__":
    print("Buddy's Vision System Ready")
    print("This module provides comprehensive site inspection capabilities")

