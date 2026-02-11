#!/usr/bin/env python3
"""Direct test with verbose logging saved to file."""

import os
import sys
import time
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent / '.env')

sys.path.insert(0, str(Path(__file__).parent))

from Back_End.mployer_scraper import MployerScraper

# Set up logging to file
log_file = Path(__file__).parent / 'test_verbose.log'
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

username = os.getenv("MPLOYER_USERNAME")
password = os.getenv("MPLOYER_PASSWORD")

if not username or not password:
    logger.error("Set MPLOYER_USERNAME and MPLOYER_PASSWORD in .env")
    sys.exit(1)

print("\n=== STARTING TEST ===\n")
logger.info("=== STARTING TEST ===")

# Initialize scraper
scraper = MployerScraper(username, password, headless=False)
scraper.initialize_browser()

try:
    logger.info("[1] Logging in...")
    scraper.login_to_mployer()
    logger.info("[1] Login complete")
    
    logger.info("[2] Starting search with employees_min=10, employees_max=500...")
    results = scraper.search_employers(employees_min=10, employees_max=500)
    logger.info(f"[2] Search complete. Got {len(results)} results")
    
    if results:
        logger.info("First 3 results:")
        for r in results[:3]:
            logger.info(f"  - {r}")
    else:
        logger.warning("No results returned!")
        
except Exception as e:
    logger.error(f"Error: {e}", exc_info=True)
    
finally:
    logger.info("[3] Closing...")
    scraper.driver.quit()
    logger.info("[3] Done")

print(f"\n=== LOG SAVED TO {log_file} ===\n")

