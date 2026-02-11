#!/usr/bin/env python
"""
PHASE 1 VALIDATION RUN - Execute WebNavigatorAgent on 5 Real Sites

Objective: Generate real selector-level learning data without code changes
Input: 5 real, publicly accessible websites with pagination
Output: learning_signals.jsonl, tool_execution_log.jsonl, summary report
"""

import time
import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import WebNavigatorAgent
try:
    from Back_End.agents import WebNavigatorAgent
    logger.info("✓ WebNavigatorAgent imported successfully")
except Exception as e:
    logger.error(f"Failed to import WebNavigatorAgent: {e}")
    exit(1)


# Site configurations for validation run
VALIDATION_SITES = [
    {
        "name": "Quotes to Scrape",
        "url": "http://quotes.toscrape.com/",
        "page_type": "listing",
        "expected_fields": ["name", "url"],
        "description": "Quotes with pagination"
    },
    {
        "name": "Books to Scrape",
        "url": "http://books.toscrape.com/",
        "page_type": "catalog",
        "expected_fields": ["name", "url", "category"],
        "description": "Book catalog with pagination"
    },
    {
        "name": "Scrape This Site - Table Tennis Players",
        "url": "http://scrapethissite.com/pages/table-tennis-players/",
        "page_type": "directory",
        "expected_fields": ["name", "url"],
        "description": "Players list with pagination"
    },
    {
        "name": "HackerNews",
        "url": "https://news.ycombinator.com/",
        "page_type": "listing",
        "expected_fields": ["name", "url"],
        "description": "HackerNews with next page button"
    },
    {
        "name": "Lobsters",
        "url": "https://lobste.rs/",
        "page_type": "listing",
        "expected_fields": ["name", "url"],
        "description": "Tech news aggregator with pagination"
    }
]


def run_validation():
    """Execute WebNavigatorAgent against all 5 sites."""
    
    logger.info("=" * 80)
    logger.info("PHASE 1 VALIDATION RUN - WebNavigatorAgent on 5 Real Sites")
    logger.info("=" * 80)
    logger.info(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Total sites to run: {len(VALIDATION_SITES)}")
    logger.info("")
    
    execution_results = []
    
    for idx, site_config in enumerate(VALIDATION_SITES, 1):
        logger.info(f"\n{'='*80}")
        logger.info(f"SITE {idx}/{len(VALIDATION_SITES)}: {site_config['name']}")
        logger.info(f"{'='*80}")
        logger.info(f"URL: {site_config['url']}")
        logger.info(f"Description: {site_config['description']}")
        logger.info(f"Expected fields: {site_config['expected_fields']}")
        
        try:
            # Create fresh agent instance for each site
            agent = WebNavigatorAgent(headless=True)
            
            # Prepare input payload
            input_payload = {
                "target_url": site_config['url'],
                "page_type": site_config['page_type'],
                "expected_fields": site_config['expected_fields'],
                "max_pages": 3,  # Try up to 3 pages per site
                "execution_mode": "DRY_RUN"
            }
            
            logger.info("\n[EXECUTION]")
            logger.info(f"Max pages: {input_payload['max_pages']}")
            logger.info(f"Execution mode: {input_payload['execution_mode']}")
            
            # Execute the agent
            start_time = time.time()
            result = agent.run(input_payload)
            duration = time.time() - start_time
            
            # Log results
            logger.info(f"\n[RESULT]")
            logger.info(f"Status: {result['status']}")
            logger.info(f"Duration: {duration:.2f}s")
            
            if result['status'] == 'COMPLETED':
                metadata = result['metadata']
                logger.info(f"Items extracted: {metadata.get('items_extracted', 0)}")
                logger.info(f"Pages visited: {metadata.get('pages_visited', 0)}")
                logger.info(f"Pagination detected: {metadata.get('pagination_detected', False)}")
                logger.info(f"Pagination method: {metadata.get('pagination_method', 'N/A')}")
                logger.info(f"Pagination stop reason: {metadata.get('pagination_stopped_reason', 'N/A')}")
                logger.info(f"Selectors attempted: {metadata.get('selectors_attempted', 0)}")
                logger.info(f"Selectors succeeded: {metadata.get('selectors_succeeded', 0)}")
                logger.info(f"Selector success rate: {metadata.get('selector_success_rate', 0):.1%}")
                
                execution_results.append({
                    'site_name': site_config['name'],
                    'site_url': site_config['url'],
                    'status': 'COMPLETED',
                    'duration_seconds': duration,
                    'items_extracted': metadata.get('items_extracted', 0),
                    'pages_visited': metadata.get('pages_visited', 0),
                    'pagination_detected': metadata.get('pagination_detected', False),
                    'pagination_method': metadata.get('pagination_method'),
                    'selectors_attempted': metadata.get('selectors_attempted', 0),
                    'selectors_succeeded': metadata.get('selectors_succeeded', 0),
                    'selector_success_rate': metadata.get('selector_success_rate', 0)
                })
            else:
                error = result.get('error', 'Unknown error')
                logger.error(f"Error: {error}")
                execution_results.append({
                    'site_name': site_config['name'],
                    'site_url': site_config['url'],
                    'status': 'FAILED',
                    'duration_seconds': duration,
                    'error': error
                })
        
        except Exception as e:
            logger.error(f"Exception during execution: {e}", exc_info=True)
            execution_results.append({
                'site_name': site_config['name'],
                'site_url': site_config['url'],
                'status': 'EXCEPTION',
                'error': str(e)
            })
        
        # Small delay between sites to avoid overwhelming servers
        if idx < len(VALIDATION_SITES):
            logger.info("\n[DELAY] Waiting 2 seconds before next site...")
            time.sleep(2)
    
    # Generate summary report
    logger.info(f"\n\n{'='*80}")
    logger.info("VALIDATION RUN SUMMARY")
    logger.info(f"{'='*80}")
    
    print_summary_report(execution_results)
    
    # Verify output files
    logger.info(f"\n{'='*80}")
    logger.info("OUTPUT FILES VERIFICATION")
    logger.info(f"{'='*80}")
    
    verify_output_files()
    
    logger.info(f"\n{'='*80}")
    logger.info("PHASE 1 VALIDATION RUN COMPLETE")
    logger.info(f"{'='*80}\n")


def print_summary_report(results):
    """Print factual summary of validation run."""
    
    # Count results by status
    completed = sum(1 for r in results if r['status'] == 'COMPLETED')
    failed = sum(1 for r in results if r['status'] == 'FAILED')
    exception = sum(1 for r in results if r['status'] == 'EXCEPTION')
    
    logger.info(f"\nExecution Summary:")
    logger.info(f"  Total sites: {len(results)}")
    logger.info(f"  Completed: {completed}")
    logger.info(f"  Failed: {failed}")
    logger.info(f"  Exceptions: {exception}")
    
    # Aggregate metrics
    total_pages = sum(r.get('pages_visited', 0) for r in results if r['status'] == 'COMPLETED')
    total_items = sum(r.get('items_extracted', 0) for r in results if r['status'] == 'COMPLETED')
    total_selectors = sum(r.get('selectors_attempted', 0) for r in results if r['status'] == 'COMPLETED')
    total_success = sum(r.get('selectors_succeeded', 0) for r in results if r['status'] == 'COMPLETED')
    
    logger.info(f"\nData Collection Results:")
    logger.info(f"  Total pages visited: {total_pages}")
    logger.info(f"  Total items extracted: {total_items}")
    logger.info(f"  Total selector attempts: {total_selectors}")
    logger.info(f"  Total selectors succeeded: {total_success}")
    
    if total_selectors > 0:
        overall_success_rate = total_success / total_selectors
        logger.info(f"  Overall selector success rate: {overall_success_rate:.1%}")
    
    # Pagination methods observed
    pagination_methods = {}
    for r in results:
        if r.get('pagination_detected') and r.get('pagination_method'):
            method = r['pagination_method']
            pagination_methods[method] = pagination_methods.get(method, 0) + 1
    
    if pagination_methods:
        logger.info(f"\nPagination Methods Observed:")
        for method, count in sorted(pagination_methods.items()):
            logger.info(f"  {method}: {count} site(s)")
    
    # Per-site summary
    logger.info(f"\nPer-Site Results:")
    for r in results:
        status = r['status']
        site_name = r['site_name']
        
        if status == 'COMPLETED':
            pages = r.get('pages_visited', 0)
            items = r.get('items_extracted', 0)
            success_rate = r.get('selector_success_rate', 0)
            logger.info(f"  ✓ {site_name}")
            logger.info(f"      Pages: {pages}, Items: {items}, Selector success: {success_rate:.1%}")
        elif status == 'FAILED':
            logger.info(f"  ✗ {site_name}")
            logger.info(f"      Error: {r.get('error', 'Unknown')}")
        else:
            logger.info(f"  ✗ {site_name}")
            logger.info(f"      Exception: {r.get('error', 'Unknown')}")


def verify_output_files():
    """Verify that learning signals and execution logs were written."""
    
    outputs_dir = Path(__file__).parent / "backend" / "outputs" / "phase25"
    
    # Check learning_signals.jsonl
    learning_signals_file = outputs_dir / "learning_signals.jsonl"
    if learning_signals_file.exists():
        signal_count = sum(1 for _ in open(learning_signals_file))
        logger.info(f"✓ learning_signals.jsonl exists ({signal_count} records)")
        
        # Sample first few signals
        with open(learning_signals_file, 'r') as f:
            for i, line in enumerate(f):
                if i < 3:
                    try:
                        signal = json.loads(line)
                        signal_type = signal.get('signal_type', 'unknown')
                        logger.info(f"    Sample {i+1}: {signal_type}")
                    except:
                        pass
                else:
                    break
    else:
        logger.warning(f"⚠ learning_signals.jsonl not found at {learning_signals_file}")
    
    # Check tool_execution_log.jsonl
    execution_log_file = outputs_dir / "tool_execution_log.jsonl"
    if execution_log_file.exists():
        log_count = sum(1 for _ in open(execution_log_file))
        logger.info(f"✓ tool_execution_log.jsonl exists ({log_count} records)")
    else:
        logger.warning(f"⚠ tool_execution_log.jsonl not found at {execution_log_file}")


if __name__ == "__main__":
    try:
        run_validation()
    except KeyboardInterrupt:
        logger.info("\n\nValidation run interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)

