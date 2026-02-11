"""Test Mployer employer search functionality"""
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
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')

username = os.getenv("MPLOYER_USERNAME")
password = os.getenv("MPLOYER_PASSWORD")

print(f"\nMployer Employer Search Test")
print("=" * 60)
print(f"User: {username}")
print("=" * 60)

scraper = MployerScraper(username, password, headless=False)
scraper.initialize_browser()

# Login (will use cookies if available)
success = scraper.login_to_mployer()

if success:
    print("\n✓ Logged in successfully!")
    print("\nStarting employer search...")
    print("-" * 60)
    
    # Test search with basic criteria
    employers = scraper.search_employers(
        employees_min=10,
        employees_max=500,
        city="Baltimore"
    )
    
    print("\n" + "=" * 60)
    print(f"Search complete! Found {len(employers)} employers")
    print("=" * 60)
    
    if employers:
        print("\nFirst 5 results:")
        for i, emp in enumerate(employers[:5], 1):
            print(f"\n{i}. {emp.get('name', 'N/A')}")
            print(f"   Employees: {emp.get('employees', 'N/A')}")
            print(f"   Location: {emp.get('location', 'N/A')}")
    
    print("\n" + "=" * 60)
    print("Browser will stay open for inspection...")
    input("\nPress Enter to close browser and exit...")
else:
    print("\n✗ Login failed")
    input("\nPress Enter to close browser and exit...")

if scraper.driver:
    scraper.driver.quit()

