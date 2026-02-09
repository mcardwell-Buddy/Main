#!/usr/bin/env python
"""
PHASE 1 VALIDATION RUN - Execute WebNavigatorAgent on Real Sites
Simplified version focused on data collection.
"""

import sys
import os
import time
import json
import logging
from pathlib import Path

# Set working directory
os.chdir(r'C:\Users\micha\Buddy')
sys.path.insert(0, r'C:\Users\micha\Buddy')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import WebNavigatorAgent
from backend.agents import WebNavigatorAgent

# Site configurations
VALIDATION_SITES = [
    {
        "name": "Quotes to Scrape",
        "url": "http://quotes.toscrape.com/",
        "page_type": "listing",
        "expected_fields": ["name", "url"],
    },
    {
        "name": "Books to Scrape",
        "url": "http://books.toscrape.com/",
        "page_type": "catalog",
        "expected_fields": ["name", "url"],
    },
    {
        "name": "Table Tennis Players",
        "url": "http://scrapethissite.com/pages/table-tennis-players/",
        "page_type": "directory",
        "expected_fields": ["name"],
    },
    {
        "name": "HackerNews",
        "url": "https://news.ycombinator.com/newest",
        "page_type": "news",
        "expected_fields": ["name", "url"],
    },
    {
        "name": "Lobsters",
        "url": "https://lobste.rs/",
        "page_type": "news",
        "expected_fields": ["name", "url"],
    }
]

def run_validation():
    """Execute validation run on all sites."""
    logger.info("=" * 70)
    logger.info("PHASE 1 VALIDATION RUN")
    logger.info("=" * 70)
    
    results = []
    total_start = time.time()
    
    for idx, site in enumerate(VALIDATION_SITES, 1):
        logger.info(f"\n[{idx}/{len(VALIDATION_SITES)}] {site['name']}")
        logger.info(f"  URL: {site['url']}")
        logger.info(f"  Type: {site['page_type']}")
        
        site_start = time.time()
        
        try:
            # Create agent
            agent = WebNavigatorAgent(headless=True)
            
            # Prepare payload
            payload = {
                "target_url": site["url"],
                "page_type": site["page_type"],
                "expected_fields": site["expected_fields"],
                "max_pages": 2,  # Limited pages for validation
                "execution_mode": "DRY_RUN"
            }
            
            # Execute
            logger.info(f"  Executing...")
            response = agent.run(payload)
            
            duration = time.time() - site_start
            
            # Log result
            status = response.get("status")
            metadata = response.get("metadata", {})
            
            logger.info(f"  Status: {status}")
            logger.info(f"  Duration: {duration:.1f}s")
            logger.info(f"  Items extracted: {metadata.get('items_extracted', 0)}")
            logger.info(f"  Pages visited: {metadata.get('pages_visited', 0)}")
            logger.info(f"  Selectors attempted: {metadata.get('selectors_attempted', 0)}")
            logger.info(f"  Selector success rate: {metadata.get('selector_success_rate', 0):.1%}")
            
            results.append({
                "site": site["name"],
                "status": status,
                "duration_s": duration,
                "items_extracted": metadata.get("items_extracted", 0),
                "pages_visited": metadata.get("pages_visited", 0),
                "selectors_attempted": metadata.get("selectors_attempted", 0),
                "selector_success_rate": metadata.get("selector_success_rate", 0),
            })
            
        except Exception as e:
            logger.error(f"  Error: {e}")
            duration = time.time() - site_start
            results.append({
                "site": site["name"],
                "status": "FAILED",
                "error": str(e),
                "duration_s": duration,
            })
    
    # Summary
    total_duration = time.time() - total_start
    
    logger.info("\n" + "=" * 70)
    logger.info("VALIDATION SUMMARY")
    logger.info("=" * 70)
    
    completed = sum(1 for r in results if r["status"] == "COMPLETED")
    failed = sum(1 for r in results if r["status"] == "FAILED")
    
    logger.info(f"Total sites: {len(VALIDATION_SITES)}")
    logger.info(f"Completed: {completed}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Total time: {total_duration:.1f}s")
    
    logger.info("\nDetailed Results:")
    for r in results:
        logger.info(f"  {r['site']}: {r['status']} ({r['duration_s']:.1f}s)")
        if r["status"] == "COMPLETED":
            logger.info(f"    - Items: {r['items_extracted']}, Pages: {r['pages_visited']}")
    
    # Check for output files
    logger.info("\n" + "=" * 70)
    logger.info("OUTPUT FILES")
    logger.info("=" * 70)
    
    outputs_dir = Path("outputs/phase25")
    if outputs_dir.exists():
        signal_file = outputs_dir / "learning_signals.jsonl"
        log_file = outputs_dir / "tool_execution_log.jsonl"
        
        if signal_file.exists():
            signal_count = len([l for l in signal_file.read_text().split('\n') if l.strip()])
            logger.info(f"Learning signals file: {signal_file}")
            logger.info(f"  Signals recorded: {signal_count}")
        
        if log_file.exists():
            log_count = len([l for l in log_file.read_text().split('\n') if l.strip()])
            logger.info(f"Execution log file: {log_file}")
            logger.info(f"  Executions recorded: {log_count}")
    
    logger.info("\nValidation run complete!")
    return results

if __name__ == "__main__":
    try:
        results = run_validation()
        sys.exit(0 if all(r["status"] == "COMPLETED" for r in results) else 1)
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
