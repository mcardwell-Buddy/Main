#!/usr/bin/env python3
"""Check the actual size/bounds of the minFilter field."""

import os
import sys
import time
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent / '.env')

sys.path.insert(0, str(Path(__file__).parent))

from backend.mployer_scraper import MployerScraper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

username = os.getenv("MPLOYER_USERNAME")
password = os.getenv("MPLOYER_PASSWORD")

if not username or not password:
    logger.error("Set MPLOYER_USERNAME and MPLOYER_PASSWORD in .env")
    sys.exit(1)

# Initialize scraper
scraper = MployerScraper(username, password, headless=False)
scraper.initialize_browser()

try:
    # Login
    print("\n[1] Logging in...")
    scraper.login_to_mployer()
    
    # Navigate
    print("[2] Navigating...")
    scraper.driver.get("https://portal.mployeradvisor.com/catalyst/employer")
    time.sleep(3)
    
    # Get minFilter field
    min_field = scraper.driver.find_element("id", "minFilter")
    
    # Get bounding rect
    print("\n[3] Field bounds and size...")
    rect = min_field.rect
    print(f"    x: {rect['x']}")
    print(f"    y: {rect['y']}")
    print(f"    width: {rect['width']}")
    print(f"    height: {rect['height']}")
    
    # Get actual rendered dimensions via JavaScript
    print("\n[4] JavaScript-checked dimensions...")
    info = scraper.driver.execute_script("""
    const elem = arguments[0];
    const rect = elem.getBoundingClientRect();
    const style = window.getComputedStyle(elem);
    return {
        clientWidth: elem.clientWidth,
        clientHeight: elem.clientHeight,
        offsetWidth: elem.offsetWidth,
        offsetHeight: elem.offsetHeight,
        boundingRect: {x: rect.x, y: rect.y, width: rect.width, height: rect.height},
        display: style.display,
        visibility: style.visibility,
        opacity: style.opacity,
        pointerEvents: style.pointerEvents,
        position: style.position
    };
    """, min_field)
    
    for key, value in info.items():
        if isinstance(value, dict):
            print(f"    {key}:")
            for k, v in value.items():
                print(f"      {k}: {v}")
        else:
            print(f"    {key}: {value}")
    
    # Try to interact using executeScript instead
    print("\n[5] Testing interaction via executeScript...")
    try:
        # Method 1: Simple value set
        scraper.driver.execute_script("arguments[0].value = '10';", min_field)
        val = min_field.get_attribute('value')
        print(f"    After execute_script setValue: value = '{val}'")
        
        # Method 2: Trigger input event
        scraper.driver.execute_script("""
        arguments[0].focus();
        arguments[0].value = '10';
        arguments[0].dispatchEvent(new Event('input', {bubbles: true}));
        arguments[0].dispatchEvent(new Event('change', {bubbles: true}));
        """, min_field)
        val = min_field.get_attribute('value')
        print(f"    After full JS method: value = '{val}'")
        
        print("\n[OK] JavaScript-based field interaction works!")
        
    except Exception as e:
        print(f"    [FAIL] {e}")
    
finally:
    scraper.driver.quit()
