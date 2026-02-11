#!/usr/bin/env python3
"""
Interactive session manager for Mployer automation.
Keeps browser open and allows running multiple commands sequentially.
"""

import os
import sys
import json
import time
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from Back_End.mployer_scraper import MployerScraper
from Back_End.page_inspector import inspect_page_elements

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class InteractiveSession:
    """Interactive session for running multiple Mployer operations"""
    
    def __init__(self):
        self.scraper = None
        self.username = os.getenv("MPLOYER_USERNAME", "")
        self.password = os.getenv("MPLOYER_PASSWORD", "")
    
    def start_session(self):
        """Initialize the session with a browser"""
        if not self.username or not self.password:
            logger.error("MPLOYER_USERNAME or MPLOYER_PASSWORD not set in .env")
            return False
        
        logger.info("Starting interactive session...")
        self.scraper = MployerScraper(self.username, self.password, headless=False)
        self.scraper.initialize_browser()
        return True
    
    def navigate_to_employer_search(self):
        """Navigate to employer search page"""
        logger.info("Navigating to Employer Search page...")
        try:
            self.scraper.login_to_mployer()
            self.scraper.driver.get("https://portal.mployeradvisor.com/catalyst/employer")
            time.sleep(3)
            logger.info("✓ Navigated to Employer Search")
            return True
        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            return False
    
    def inspect_page(self):
        """Inspect page and report elements"""
        logger.info("\n=== PAGE INSPECTION ===")
        try:
            elements = inspect_page_elements(self.scraper.driver)
            
            # Print key element types
            print("\n📋 PAGE ANALYSIS:")
            print(f"  URL: {elements.get('url', 'Unknown')}")
            print(f"  Title: {elements.get('title', 'Unknown')}")
            
            # Print input fields
            if elements.get('inputs'):
                print(f"\n📝 INPUT FIELDS ({len(elements['inputs'])} found):")
                for field in elements['inputs'][:10]:  # Show first 10
                    visible = "✓" if field.get('visible') else "✗"
                    name = field.get('name') or field.get('placeholder') or field.get('id') or 'Unknown'
                    print(f"  {visible} {name} (type: {field.get('type', 'text')})")
            
            # Print buttons
            if elements.get('buttons'):
                print(f"\n🔘 BUTTONS ({len(elements['buttons'])} found):")
                for button in elements['buttons']:
                    visible = "✓" if button.get('visible') else "✗"
                    text = button.get('text', 'No text')
                    print(f"  {visible} {text}")
            
            logger.info("✓ Page inspection complete")
            return True
        except Exception as e:
            logger.error(f"Inspection failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def run_employer_search(self):
        """Run employer search with filters"""
        logger.info("\n=== EMPLOYER SEARCH ===")
        
        # Get filter criteria from user
        try:
            min_employees = input("Min employees (default 10): ").strip() or "10"
            max_employees = input("Max employees (default 500): ").strip() or "500"
            
            min_employees = int(min_employees)
            max_employees = int(max_employees)
            
            logger.info(f"Searching for employers: {min_employees}-{max_employees} employees")
            
            employers = self.scraper.search_employers(
                employees_min=min_employees,
                employees_max=max_employees
            )
            
            logger.info(f"✓ Found {len(employers)} employers")
            
            if employers:
                print("\n📊 SEARCH RESULTS:")
                for i, emp in enumerate(employers[:10], 1):  # Show first 10
                    print(f"\n{i}. {emp.get('name', 'N/A')}")
                    print(f"   Employees: {emp.get('employees', 'N/A')}")
                    print(f"   Location: {emp.get('location', 'N/A')}")
                    print(f"   Industry: {emp.get('industry', 'N/A')}")
                
                if len(employers) > 10:
                    print(f"\n... and {len(employers) - 10} more employers")
            
            return employers
        except ValueError:
            logger.error("Invalid input - please enter numbers")
            return []
        except Exception as e:
            logger.error(f"Search failed: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def take_screenshot(self):
        """Take a screenshot of the current page"""
        try:
            timestamp = int(time.time())
            filename = f"mployer_screenshot_{timestamp}.png"
            self.scraper.driver.save_screenshot(filename)
            logger.info(f"✓ Screenshot saved: {filename}")
            return True
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            return False
    
    def get_current_url(self):
        """Get current page URL"""
        try:
            url = self.scraper.driver.current_url
            logger.info(f"Current URL: {url}")
            return url
        except Exception as e:
            logger.error(f"Failed to get URL: {e}")
            return None
    
    def navigate_to_url(self):
        """Navigate to custom URL"""
        try:
            url = input("Enter URL to navigate to: ").strip()
            if url:
                self.scraper.driver.get(url)
                time.sleep(2)
                logger.info(f"✓ Navigated to {url}")
        except Exception as e:
            logger.error(f"Navigation failed: {e}")
    
    def show_menu(self):
        """Show available commands"""
        print("\n" + "="*50)
        print("INTERACTIVE MPLOYER SESSION")
        print("="*50)
        print("Commands:")
        print("  1 - Navigate to Employer Search")
        print("  2 - Inspect Page Elements")
        print("  3 - Run Employer Search")
        print("  4 - Take Screenshot")
        print("  5 - Show Current URL")
        print("  6 - Navigate to Custom URL")
        print("  q - Quit (closes browser)")
        print("="*50)
    
    def run(self):
        """Run the interactive session"""
        if not self.start_session():
            return
        
        try:
            while True:
                self.show_menu()
                command = input("\nEnter command: ").strip().lower()
                
                if command == "1":
                    self.navigate_to_employer_search()
                elif command == "2":
                    self.inspect_page()
                elif command == "3":
                    self.run_employer_search()
                elif command == "4":
                    self.take_screenshot()
                elif command == "5":
                    self.get_current_url()
                elif command == "6":
                    self.navigate_to_url()
                elif command == "q":
                    logger.info("Closing browser...")
                    self.scraper.driver.quit()
                    logger.info("Session ended.")
                    break
                else:
                    logger.warning("Unknown command")
        except KeyboardInterrupt:
            logger.info("\nSession interrupted by user")
            self.scraper.driver.quit()
        except Exception as e:
            logger.error(f"Session error: {e}")
            import traceback
            traceback.print_exc()
            if self.scraper:
                self.scraper.driver.quit()

if __name__ == "__main__":
    session = InteractiveSession()
    session.run()

