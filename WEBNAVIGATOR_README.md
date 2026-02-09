# WebNavigatorAgent - Pagination Implementation

**Phase 1 Steps 1 & 2 Complete**  
**Last Updated:** February 6, 2026

---

## Example Pagination Metadata

### Single Page Run (max_pages=1)

```json
{
  "status": "COMPLETED",
  "data": {
    "page_title": "Example Domain",
    "page_url": "https://example.com",
    "page_type": "directory",
    "items": [
      {
        "name": "More information...",
        "url": "https://www.iana.org/domains/example",
        "category": ""
      }
    ],
    "structure": {
      "forms_count": 0,
      "buttons_count": 0,
      "inputs_count": 0,
      "links_count": 1
    }
  },
  "metadata": {
    "execution_id": "nav_1738850123.456",
    "duration_ms": 3250,
    "items_extracted": 1,
    "url": "https://example.com",
    "page_type": "directory",
    "execution_mode": "DRY_RUN",
    "pages_visited": 1,
    "pagination_detected": false,
    "pagination_method": null,
    "pagination_stopped_reason": "single_page_mode"
  }
}
```

### Multi-Page Run (max_pages=3, No Pagination Found)

```json
{
  "status": "COMPLETED",
  "data": {
    "page_title": "Example Domain",
    "page_url": "https://example.com",
    "page_type": "directory",
    "items": [
      {
        "name": "More information...",
        "url": "https://www.iana.org/domains/example",
        "category": ""
      }
    ],
    "structure": {
      "total_items": 1,
      "pages_extracted": 1
    }
  },
  "metadata": {
    "execution_id": "nav_1738850456.789",
    "duration_ms": 3420,
    "items_extracted": 1,
    "url": "https://example.com",
    "page_type": "directory",
    "execution_mode": "DRY_RUN",
    "pages_visited": 1,
    "pagination_detected": true,
    "pagination_method": null,
    "pagination_stopped_reason": "no_next"
  }
}
```

### Multi-Page Run (max_pages=3, Pagination Success)

**Hypothetical example from a paginated site:**

```json
{
  "status": "COMPLETED",
  "data": {
    "page_title": "Product Directory - Page 3",
    "page_url": "https://example-directory.com/?page=3",
    "page_type": "directory",
    "items": [
      {"name": "Product A", "url": "https://example-directory.com/product-a", "category": "electronics"},
      {"name": "Product B", "url": "https://example-directory.com/product-b", "category": "electronics"},
      {"name": "Product C", "url": "https://example-directory.com/product-c", "category": "tools"},
      {"name": "Product D", "url": "https://example-directory.com/product-d", "category": "tools"},
      {"name": "Product E", "url": "https://example-directory.com/product-e", "category": "home"},
      {"name": "Product F", "url": "https://example-directory.com/product-f", "category": "home"},
      {"name": "Product G", "url": "https://example-directory.com/product-g", "category": "garden"},
      {"name": "Product H", "url": "https://example-directory.com/product-h", "category": "garden"}
    ],
    "structure": {
      "total_items": 45,
      "pages_extracted": 3
    }
  },
  "metadata": {
    "execution_id": "nav_1738851000.123",
    "duration_ms": 12840,
    "items_extracted": 45,
    "url": "https://example-directory.com",
    "page_type": "directory",
    "execution_mode": "DRY_RUN",
    "pages_visited": 3,
    "pagination_detected": true,
    "pagination_method": "text_match",
    "pagination_stopped_reason": "max_pages"
  }
}
```

---

## Complete Updated Agent Code

### File: `backend/agents/web_navigator_agent.py`

```python
"""
WebNavigatorAgent - Phase 1 Steps 1 & 2

A wrapper agent that exposes existing Selenium tooling (BuddysVisionCore + BuddysArms)
through a standardized agent interface with bounded pagination support.

NO NEW SELENIUM LOGIC. This is an adapter + pagination module.
"""

import time
import logging
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager

from backend.buddys_vision_core import BuddysVisionCore
from backend.buddys_arms import BuddysArms
from backend.phase25_orchestrator import Phase25Orchestrator

logger = logging.getLogger(__name__)


class WebNavigatorAgent:
    """
    Agent wrapper for web navigation and extraction with pagination support.
    
    Wraps existing Selenium tooling (BuddysVisionCore + BuddysArms) without
    adding new behavior. This is an adapter layer for agent-style invocation.
    
    Phase 1 Step 1: Basic navigation and extraction wrapper
    Phase 1 Step 2: Bounded pagination traversal (max_pages enforcement)
    """
    
    def __init__(self, headless: bool = True, orchestrator: Optional[Phase25Orchestrator] = None):
        """
        Initialize the agent.
        
        Args:
            headless: Run browser in headless mode
            orchestrator: Optional Phase25Orchestrator for logging (creates new one if None)
        """
        self.headless = headless
        self.orchestrator = orchestrator or Phase25Orchestrator()
        self.driver = None
        self.vision_core = None
        self.arms = None
        
    def _initialize_browser(self) -> None:
        """Initialize Chrome browser using existing pattern from mployer_scraper"""
        if self.driver is not None:
            return  # Already initialized
            
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless")
        
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        try:
            # Use cached ChromeDriver if available
            chromedriver_path = Path.home() / ".wdm" / "drivers" / "chromedriver" / "win64" / "144.0.7559.133" / "chromedriver-win32" / "chromedriver.exe"
            
            if chromedriver_path.exists():
                logger.info("Using cached ChromeDriver")
                service = Service(str(chromedriver_path))
            else:
                logger.info("Using webdriver-manager to install ChromeDriver")
                service = Service(ChromeDriverManager().install())
            
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Initialize existing Selenium wrappers
            self.vision_core = BuddysVisionCore(self.driver, timeout=10)
            self.arms = BuddysArms(self.driver, self.vision_core, timeout=15)
            
            logger.info("✓ Browser and Selenium wrappers initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize browser: {e}")
            raise
    
    def _close_browser(self) -> None:
        """Close the browser"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Browser closed")
            except Exception as e:
                logger.warning(f"Error closing browser: {e}")
            finally:
                self.driver = None
                self.vision_core = None
                self.arms = None
    
    def run(self, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single navigation + extraction run using existing Selenium tooling.
        
        Input Contract:
        {
            "target_url": "https://example.com",
            "page_type": "directory | listings | jobs | catalog",
            "expected_fields": ["name", "url", "category", "location"],
            "max_pages": 3,
            "execution_mode": "MOCK | DRY_RUN"
        }
        
        Returns:
        {
            "status": "COMPLETED | FAILED",
            "data": {...},
            "metadata": {
                "duration_ms": 1234,
                "items_extracted": 10,
                "pages_visited": 3,
                "pagination_detected": true,
                "pagination_method": "text_match",
                "pagination_stopped_reason": "max_pages",
                "execution_id": "..."
            },
            "error": "..." (if failed)
        }
        """
        start_time = time.time()
        execution_id = f"nav_{datetime.now().timestamp()}"
        
        # Extract input parameters
        target_url = input_payload.get("target_url")
        page_type = input_payload.get("page_type", "unknown")
        expected_fields = input_payload.get("expected_fields", [])
        max_pages = input_payload.get("max_pages", 1)
        execution_mode = input_payload.get("execution_mode", "DRY_RUN")
        
        if not target_url:
            return self._build_error_response(
                execution_id=execution_id,
                error="target_url is required",
                start_time=start_time
            )
        
        logger.info(f"[WebNavigatorAgent] Starting navigation to {target_url}")
        logger.info(f"  Page type: {page_type}")
        logger.info(f"  Expected fields: {expected_fields}")
        logger.info(f"  Execution mode: {execution_mode}")
        logger.info(f"  Max pages: {max_pages}")
        
        try:
            # Initialize browser
            self._initialize_browser()
            
            # Navigate to target URL using existing BuddysArms
            logger.info(f"Navigating to {target_url}...")
            self.arms.navigate(target_url)
            
            # Use pagination-aware extraction if max_pages > 1
            if max_pages > 1:
                logger.info("Multi-page extraction enabled")
                extracted_data, pagination_metadata = self._paginate_and_extract(
                    expected_fields=expected_fields,
                    page_type=page_type,
                    max_pages=max_pages
                )
            else:
                logger.info("Single-page extraction (max_pages=1)")
                # Single page extraction (existing logic)
                inspection_data = self.vision_core.inspect_website(
                    url=self.driver.current_url,
                    expand_interactive=True,
                    max_scrolls=4
                )
                
                extracted_data = self._extract_data_from_inspection(
                    inspection_data=inspection_data,
                    expected_fields=expected_fields,
                    page_type=page_type
                )
                
                pagination_metadata = {
                    "pages_visited": 1,
                    "pagination_detected": False,
                    "pagination_method": None,
                    "pagination_stopped_reason": "single_page_mode"
                }
            
            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Log execution using existing orchestrator
            self.orchestrator.log_execution(
                task_id=execution_id,
                tool_name="web_navigator_agent",
                action_type="navigate_and_extract",
                status="COMPLETED",
                data={
                    "url": target_url,
                    "page_type": page_type,
                    "items_extracted": len(extracted_data.get("items", [])),
                    "fields_found": list(extracted_data.keys()),
                    "pages_visited": pagination_metadata.get("pages_visited", 1),
                    "pagination_detected": pagination_metadata.get("pagination_detected", False)
                },
                duration_ms=duration_ms
            )
            
            # Build response
            response = {
                "status": "COMPLETED",
                "data": extracted_data,
                "metadata": {
                    "execution_id": execution_id,
                    "duration_ms": duration_ms,
                    "items_extracted": len(extracted_data.get("items", [])),
                    "url": target_url,
                    "page_type": page_type,
                    "execution_mode": execution_mode,
                    **pagination_metadata  # Include pagination metadata
                }
            }
            
            logger.info(f"✓ Navigation completed: {len(extracted_data.get('items', []))} items extracted across {pagination_metadata['pages_visited']} page(s)")
            
            return response
            
        except Exception as e:
            logger.error(f"Navigation failed: {e}", exc_info=True)
            return self._build_error_response(
                execution_id=execution_id,
                error=str(e),
                start_time=start_time
            )
        
        finally:
            # Clean up browser
            self._close_browser()
    
    def _extract_data_from_inspection(
        self, 
        inspection_data: Dict[str, Any],
        expected_fields: List[str],
        page_type: str
    ) -> Dict[str, Any]:
        """
        Extract structured data from BuddysVisionCore inspection results.
        
        Uses ONLY existing extraction logic - no new patterns.
        """
        extracted = {
            "page_title": inspection_data.get("page_title", ""),
            "page_url": inspection_data.get("page_url", ""),
            "page_type": page_type,
            "items": [],
            "structure": {
                "forms_count": len(inspection_data.get("forms", [])),
                "buttons_count": len(inspection_data.get("buttons", [])),
                "inputs_count": len(inspection_data.get("inputs", [])),
                "links_count": len(inspection_data.get("links", []))
            }
        }
        
        # Extract items from links (simplest extraction pattern)
        # This uses existing link data from BuddysVisionCore
        links = inspection_data.get("links", [])
        
        for link in links[:50]:  # Limit to first 50 links
            item = {}
            
            # Map expected fields to available data
            if "name" in expected_fields:
                item["name"] = link.get("text", "").strip()
            
            if "url" in expected_fields:
                item["url"] = link.get("href", "")
            
            if "category" in expected_fields:
                # Use class name as proxy for category
                item["category"] = link.get("class", "").split()[0] if link.get("class") else ""
            
            if "location" in expected_fields:
                # Not available in basic link extraction
                item["location"] = ""
            
            # Only add non-empty items
            if item.get("name") or item.get("url"):
                extracted["items"].append(item)
        
        logger.info(f"Extracted {len(extracted['items'])} items from inspection")
        
        return extracted
    
    def _detect_pagination(self) -> Optional[Tuple[WebElement, str]]:
        """
        Detect pagination control on current page.
        
        Returns:
            Tuple of (element, method) if found, None otherwise
            method: "rel_next" | "aria_label" | "text_match" | "page_number"
        """
        try:
            # Strategy 1: <a rel="next">
            try:
                next_link = self.driver.find_element(By.CSS_SELECTOR, "a[rel='next']")
                if next_link.is_displayed() and next_link.is_enabled():
                    logger.info("Pagination detected: rel='next' link")
                    return (next_link, "rel_next")
            except NoSuchElementException:
                pass
            
            # Strategy 2: aria-label containing "next" (case-insensitive)
            try:
                next_elements = self.driver.find_elements(By.XPATH, 
                    "//*[contains(translate(@aria-label, 'NEXT', 'next'), 'next') and (self::a or self::button)]")
                for elem in next_elements:
                    if elem.is_displayed() and elem.is_enabled():
                        logger.info(f"Pagination detected: aria-label='{elem.get_attribute('aria-label')}'")
                        return (elem, "aria_label")
            except NoSuchElementException:
                pass
            
            # Strategy 3: Visible text matches common "next" patterns
            next_patterns = ["Next", "next", "NEXT", ">", "→", "More", "more", "Next Page", "next page"]
            for pattern in next_patterns:
                try:
                    # Try buttons first
                    buttons = self.driver.find_elements(By.TAG_NAME, "button")
                    for btn in buttons:
                        if btn.text.strip() == pattern and btn.is_displayed() and btn.is_enabled():
                            logger.info(f"Pagination detected: button text='{pattern}'")
                            return (btn, "text_match")
                    
                    # Try links
                    links = self.driver.find_elements(By.TAG_NAME, "a")
                    for link in links:
                        if link.text.strip() == pattern and link.is_displayed() and link.is_enabled():
                            logger.info(f"Pagination detected: link text='{pattern}'")
                            return (link, "text_match")
                except (NoSuchElementException, StaleElementReferenceException):
                    continue
            
            # Strategy 4: Page-number controls (find highest unvisited number)
            try:
                # Look for numeric pagination links
                page_links = self.driver.find_elements(By.XPATH, 
                    "//a[string(number(text())) != 'NaN' and self::a]")
                
                if page_links:
                    # Get current page (look for active/selected class)
                    current_page = 1
                    for link in page_links:
                        classes = link.get_attribute("class") or ""
                        if "active" in classes.lower() or "current" in classes.lower() or "selected" in classes.lower():
                            try:
                                current_page = int(link.text.strip())
                            except ValueError:
                                pass
                    
                    # Find next page number
                    next_page = current_page + 1
                    for link in page_links:
                        try:
                            page_num = int(link.text.strip())
                            if page_num == next_page and link.is_displayed() and link.is_enabled():
                                logger.info(f"Pagination detected: page number {next_page}")
                                return (link, "page_number")
                        except ValueError:
                            continue
            except (NoSuchElementException, StaleElementReferenceException):
                pass
            
            logger.info("No pagination control detected")
            return None
            
        except Exception as e:
            logger.warning(f"Error detecting pagination: {e}")
            return None
    
    def _go_to_next_page(self, element: WebElement) -> bool:
        """
        Click pagination element and verify navigation occurred.
        
        Returns:
            True if navigation successful, False otherwise
        """
        try:
            # Record current state
            current_url = self.driver.current_url
            current_content_hash = self._get_page_content_hash()
            
            # Scroll element into view
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.5)
            
            # Click using existing retry logic pattern from BuddysArms
            clicked = False
            for attempt in range(3):
                try:
                    element.click()
                    clicked = True
                    break
                except Exception:
                    try:
                        self.driver.execute_script("arguments[0].click();", element)
                        clicked = True
                        break
                    except Exception:
                        if attempt < 2:
                            time.sleep(0.5)
            
            if not clicked:
                logger.warning("Failed to click pagination element")
                return False
            
            # Wait for page change
            time.sleep(2)
            
            # Verify navigation occurred
            new_url = self.driver.current_url
            new_content_hash = self._get_page_content_hash()
            
            if new_url != current_url:
                logger.info(f"Navigation successful: URL changed to {new_url}")
                return True
            
            if new_content_hash != current_content_hash:
                logger.info("Navigation successful: Content changed")
                return True
            
            logger.warning("Navigation failed: No URL or content change detected")
            return False
            
        except Exception as e:
            logger.error(f"Error navigating to next page: {e}")
            return False
    
    def _get_page_content_hash(self) -> str:
        """Get hash of page content for duplicate detection"""
        try:
            # Use page title + first 1000 chars of body text as content signature
            title = self.driver.title or ""
            body = self.driver.find_element(By.TAG_NAME, "body").text[:1000]
            content = f"{title}|{body}"
            return hashlib.md5(content.encode()).hexdigest()
        except Exception:
            return ""
    
    def _paginate_and_extract(
        self,
        expected_fields: List[str],
        page_type: str,
        max_pages: int
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Extract data across multiple pages with pagination.
        
        Returns:
            Tuple of (extracted_data, pagination_metadata)
        """
        all_items = []
        pages_visited = 0
        pagination_detected = False
        pagination_method = None
        stopped_reason = None
        seen_urls = set()  # For deduplication
        seen_content_hashes = set()
        
        logger.info(f"Starting pagination: max_pages={max_pages}")
        
        while pages_visited < max_pages:
            pages_visited += 1
            logger.info(f"Extracting from page {pages_visited}/{max_pages}")
            
            # Check for duplicate content
            current_hash = self._get_page_content_hash()
            if current_hash in seen_content_hashes:
                logger.info("Duplicate page content detected, stopping")
                stopped_reason = "duplicate"
                break
            seen_content_hashes.add(current_hash)
            
            # Extract data from current page using existing logic
            try:
                inspection_data = self.vision_core.inspect_website(
                    url=self.driver.current_url,
                    expand_interactive=True,
                    max_scrolls=4
                )
                
                page_data = self._extract_data_from_inspection(
                    inspection_data=inspection_data,
                    expected_fields=expected_fields,
                    page_type=page_type
                )
                
                # Add items with deduplication by URL
                for item in page_data.get("items", []):
                    item_url = item.get("url", "")
                    if item_url and item_url not in seen_urls:
                        all_items.append(item)
                        seen_urls.add(item_url)
                    elif not item_url:
                        # No URL to dedupe by, add anyway
                        all_items.append(item)
                
                logger.info(f"Extracted {len(page_data.get('items', []))} items from page {pages_visited} (total: {len(all_items)})")
                
            except Exception as e:
                logger.error(f"Error extracting from page {pages_visited}: {e}")
                stopped_reason = "extraction_error"
                break
            
            # Check if we've reached max_pages
            if pages_visited >= max_pages:
                logger.info("Reached max_pages limit")
                stopped_reason = "max_pages"
                break
            
            # Detect pagination control
            pagination_result = self._detect_pagination()
            
            if pagination_result is None:
                logger.info("No pagination control found, stopping")
                stopped_reason = "no_next"
                break
            
            element, method = pagination_result
            pagination_detected = True
            pagination_method = method
            
            # Try to navigate to next page
            if not self._go_to_next_page(element):
                logger.info("Failed to navigate to next page, stopping")
                stopped_reason = "navigation_failed"
                break
            
            # Small delay between pages
            time.sleep(1)
        
        # Build aggregated data
        extracted_data = {
            "page_title": self.driver.title,
            "page_url": self.driver.current_url,
            "page_type": page_type,
            "items": all_items,
            "structure": {
                "total_items": len(all_items),
                "pages_extracted": pages_visited
            }
        }
        
        pagination_metadata = {
            "pages_visited": pages_visited,
            "pagination_detected": pagination_detected,
            "pagination_method": pagination_method,
            "pagination_stopped_reason": stopped_reason or "completed"
        }
        
        logger.info(f"Pagination complete: {pages_visited} pages, {len(all_items)} items, stopped: {stopped_reason}")
        
        return extracted_data, pagination_metadata
    
    def _build_error_response(
        self,
        execution_id: str,
        error: str,
        start_time: float
    ) -> Dict[str, Any]:
        """Build error response and log to orchestrator"""
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Log failure
        self.orchestrator.log_execution(
            task_id=execution_id,
            tool_name="web_navigator_agent",
            action_type="navigate_and_extract",
            status="FAILED",
            data={"error": error},
            duration_ms=duration_ms
        )
        
        return {
            "status": "FAILED",
            "error": error,
            "metadata": {
                "execution_id": execution_id,
                "duration_ms": duration_ms
            }
        }
```

---

## Key Pagination Features

### Detection Strategies (Priority Order)

1. **`rel_next`** — HTML5 standard `<a rel="next">`
2. **`aria_label`** — ARIA accessibility with "next" in label
3. **`text_match`** — Common text patterns: "Next", ">", "→", "More"
4. **`page_number`** — Numeric page links (1, 2, 3...)

### Stop Conditions

- `max_pages` — Page limit reached
- `no_next` — No pagination control found
- `duplicate` — Same content hash detected
- `navigation_failed` — Click didn't change page
- `extraction_error` — Data extraction failed
- `single_page_mode` — max_pages set to 1

### Deduplication

- **By URL:** Items with same URL deduplicated
- **By Content Hash:** Page content hashed to prevent loops

---

## Usage Examples

### Basic Single Page

```python
from backend.agents import WebNavigatorAgent

agent = WebNavigatorAgent(headless=True)

result = agent.run({
    "target_url": "https://example.com",
    "page_type": "directory",
    "expected_fields": ["name", "url"],
    "max_pages": 1,
    "execution_mode": "DRY_RUN"
})

print(f"Items: {result['metadata']['items_extracted']}")
print(f"Pages: {result['metadata']['pages_visited']}")
```

### Multi-Page with Pagination

```python
result = agent.run({
    "target_url": "https://paginated-site.com/directory",
    "page_type": "directory",
    "expected_fields": ["name", "url", "category"],
    "max_pages": 5,
    "execution_mode": "DRY_RUN"
})

metadata = result['metadata']
print(f"Items extracted: {metadata['items_extracted']}")
print(f"Pages visited: {metadata['pages_visited']}")
print(f"Pagination method: {metadata['pagination_method']}")
print(f"Stop reason: {metadata['pagination_stopped_reason']}")
```

---

## Log File Entry Example

**Location:** `backend/outputs/phase25/tool_execution_log.jsonl`

```json
{
  "execution_id": "nav_1738851000.123",
  "tool_name": "web_navigator_agent",
  "timestamp": "2026-02-06T15:30:00.123456Z",
  "duration_ms": 12840,
  "status": "COMPLETED",
  "action_type": "navigate_and_extract",
  "data_extracted": {
    "url": "https://example-directory.com",
    "page_type": "directory",
    "items_extracted": 45,
    "fields_found": ["page_title", "page_url", "items", "structure"],
    "pages_visited": 3,
    "pagination_detected": true
  },
  "execution_mode": "LIVE"
}
```

---

## What Was NOT Changed

**Core Selenium Files (Unchanged):**
- ❌ `buddys_vision_core.py` — NOT modified
- ❌ `buddys_arms.py` — NOT modified
- ❌ `phase25_orchestrator.py` — NOT modified

**Only Modified:**
- ✅ `backend/agents/web_navigator_agent.py` — Extended with pagination

---

**Documentation Version:** 1.0  
**Last Updated:** February 6, 2026  
**Status:** Steps 1 & 2 Complete ✅
