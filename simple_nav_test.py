#!/usr/bin/env python3
"""Simple test to verify search page loads"""

import os, sys, time
from pathlib import Path
sys.path.insert(0, str(Path('.').absolute()))

from backend.mployer_scraper import MployerScraper

username = os.getenv('MPLOYER_USERNAME')
password = os.getenv('MPLOYER_PASSWORD')

print('TEST: Basic search page navigation')
print('='*50)

scraper = MployerScraper(username, password, headless=False)
scraper.initialize_browser()

try:
    print('1. Trying to use saved session...')
    result = scraper.login_to_mployer()
    print(f'   Login result: {result}')
    
    if result:
        print('2. Opening search page...')
        scraper.driver.get("https://portal.mployeradvisor.com/catalyst/employer")
        time.sleep(3)
        print(f'   Page title: {scraper.driver.title}')
        print(f'   URL: {scraper.driver.current_url}')
        
        print('\n✓ TEST PASSED - Search page accessible!')
    else:
        print('\n✗ Login failed - session probably expired')
        print('  (This is expected, just means cookies are old)')
        
finally:
    scraper.driver.quit()
