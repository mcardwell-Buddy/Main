"""
WebNavigatorAgent - Phase 1 Steps 1-3 Complete

A wrapper agent that exposes existing Selenium tooling (BuddysVisionCore + BuddysArms)
through a standardized agent interface with pagination and learning signal instrumentation.

Phase 1 Step 1: Navigation and extraction wrapper
Phase 1 Step 2: Bounded pagination traversal
Phase 1 Step 3: Selector-level learning signal instrumentation
"""

import time
import logging
import hashlib
import json
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from datetime import datetime, timezone

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager

from Back_End.buddys_vision_core import BuddysVisionCore
from Back_End.buddys_arms import BuddysArms
from Back_End.phase25_orchestrator import Phase25Orchestrator

logger = logging.getLogger(__name__)


class WebNavigatorAgent:
    """
    Agent wrapper for web navigation and extraction with pagination and learning signals.
    
    Wraps existing Selenium tooling (BuddysVisionCore + BuddysArms) without
    adding new behavior. Instruments selector attempts for learning signal emission.
    
    Phase 1 Step 1: Basic navigation and extraction wrapper
    Phase 1 Step 2: Bounded pagination traversal (max_pages enforcement)
    Phase 1 Step 3: Selector-level learning signals (instrumentation only)
    """
    
    def __init__(self, headless: bool = True, orchestrator: Optional[Phase25Orchestrator] = None):
        """Initialize the agent."""
        self.headless = headless
        self.orchestrator = orchestrator or Phase25Orchestrator()
        self.driver = None
        self.vision_core = None
        self.arms = None
        
        # Phase 1 Step 3: Learning signal tracking
        self.selector_signals = []
        self.current_page_number = 1
        self.run_start_time = None
        
    def _initialize_browser(self) -> None:
        """Initialize Chrome browser."""
        if self.driver is not None:
            return
            
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        try:
            chromedriver_path = Path.home() / ".wdm" / "drivers" / "chromedriver" / "win64" / "144.0.7559.133" / "chromedriver-win32" / "chromedriver.exe"
            
            if chromedriver_path.exists():
                logger.info("Using cached ChromeDriver")
                service = Service(str(chromedriver_path))
            else:
                logger.info("Using webdriver-manager to install ChromeDriver")
                service = Service(ChromeDriverManager().install())
            
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.vision_core = BuddysVisionCore(self.driver, timeout=10)
            self.arms = BuddysArms(self.driver, self.vision_core, timeout=15)
            
            logger.info("✓ Browser and Selenium wrappers initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize browser: {e}")
            raise
    
    def _close_browser(self) -> None:
        """Close the browser."""
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
    
    # === PHASE 1 STEP 3: LEARNING SIGNAL EMISSION ===
    
    def _emit_selector_signal(
        self,
        selector: str,
        selector_type: str,
        outcome: str,
        duration_ms: int,
        retry_count: int = 0
    ) -> None:
        """Emit a selector-level learning signal."""
        signal = {
            "signal_type": "selector_outcome",
            "tool_name": "web_navigator_agent",
            "selector": selector,
            "selector_type": selector_type,
            "page_number": self.current_page_number,
            "outcome": outcome,
            "duration_ms": duration_ms,
            "retry_count": retry_count,
            "confidence": 0.0,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        self.selector_signals.append(signal)
        logger.debug(f"[SIGNAL] {selector_type}:{selector} → {outcome} ({duration_ms}ms, {retry_count} retries)")
    
    def _emit_aggregate_signals(self, execution_id: str) -> None:
        """Emit aggregate learning signals at end of run."""
        if not self.selector_signals:
            return
        
        successful = sum(1 for s in self.selector_signals if s["outcome"] == "success")
        failed = sum(1 for s in self.selector_signals if s["outcome"] == "failure")
        total = len(self.selector_signals)
        success_rate = successful / total if total > 0 else 0.0
        
        pagination_signals = [s for s in self.selector_signals 
                             if "rel='next'" in s["selector"] or "aria-label" in s["selector"] or "Next" in s["selector"]]
        pagination_successful = sum(1 for s in pagination_signals if s["outcome"] == "success")
        pagination_success_rate = pagination_successful / len(pagination_signals) if pagination_signals else 0.0
        
        total_duration_ms = sum(s["duration_ms"] for s in self.selector_signals)
        avg_duration_ms = total_duration_ms / total if total > 0 else 0
        
        total_retries = sum(s["retry_count"] for s in self.selector_signals)
        avg_retries = total_retries / total if total > 0 else 0
        
        aggregate_signal = {
            "signal_type": "selector_aggregate",
            "tool_name": "web_navigator_agent",
            "execution_id": execution_id,
            "total_selectors_attempted": total,
            "selectors_succeeded": successful,
            "selectors_failed": failed,
            "overall_success_rate": success_rate,
            "pagination_signals_count": len(pagination_signals),
            "pagination_success_rate": pagination_success_rate,
            "total_duration_ms": total_duration_ms,
            "average_duration_ms": avg_duration_ms,
            "total_retries": total_retries,
            "average_retries": avg_retries,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        self._persist_learning_signal(aggregate_signal)
        logger.info(f"[AGGREGATE] {total} selectors: {successful} success, {failed} failed (rate: {success_rate:.1%})")
    
    def _persist_learning_signal(self, signal: Dict[str, Any]) -> None:
        """Persist a learning signal to learning_signals.jsonl."""
        try:
            if hasattr(self.orchestrator, 'log_learning_signal'):
                self.orchestrator.log_learning_signal(signal)
            else:
                outputs_dir = Path(__file__).parent.parent.parent / "outputs" / "phase25"
                outputs_dir.mkdir(parents=True, exist_ok=True)
                signal_file = outputs_dir / "learning_signals.jsonl"
                with open(signal_file, 'a') as f:
                    f.write(json.dumps(signal) + '\n')
        except Exception as e:
            logger.warning(f"Failed to persist learning signal: {e}")
    
    def _compute_learning_metrics(self) -> Dict[str, Any]:
        """Compute aggregate learning metrics from accumulated signals."""
        if not self.selector_signals:
            return {
                "total_attempted": 0,
                "total_succeeded": 0,
                "total_failed": 0,
                "success_rate": 0.0
            }
        
        total = len(self.selector_signals)
        succeeded = sum(1 for s in self.selector_signals if s["outcome"] == "success")
        failed = total - succeeded
        success_rate = succeeded / total if total > 0 else 0.0
        
        return {
            "total_attempted": total,
            "total_succeeded": succeeded,
            "total_failed": failed,
            "success_rate": success_rate
        }
    
    def _flush_selector_signals(self, execution_id: str) -> None:
        """Persist all accumulated selector signals to learning_signals.jsonl."""
        for signal in self.selector_signals:
            self._persist_learning_signal(signal)
        logger.debug(f"Flushed {len(self.selector_signals)} selector signals")
    
    def run(self, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single navigation + extraction run."""
        start_time = time.time()
        execution_id = f"nav_{datetime.now().timestamp()}"
        
        # Phase 1 Step 3: Initialize learning signal tracking
        self.selector_signals = []
        self.current_page_number = 1
        self.run_start_time = start_time
        
        target_url = input_payload.get("target_url")
        page_type = input_payload.get("page_type", "unknown")
        expected_fields = input_payload.get("expected_fields", [])
        max_pages = input_payload.get("max_pages", 1)
        execution_mode = input_payload.get("execution_mode", "DRY_RUN")
        
        if not target_url:
            return self._build_error_response(execution_id=execution_id, error="target_url is required", start_time=start_time)
        
        logger.info(f"[WebNavigatorAgent] Starting navigation to {target_url}")
        logger.info(f"  Max pages: {max_pages}")
        
        try:
            self._initialize_browser()
            logger.info(f"Navigating to {target_url}...")
            self.arms.navigate(target_url)
            
            if max_pages > 1:
                logger.info("Multi-page extraction enabled")
                extracted_data, pagination_metadata = self._paginate_and_extract(
                    expected_fields=expected_fields, page_type=page_type, max_pages=max_pages
                )
            else:
                logger.info("Single-page extraction (max_pages=1)")
                inspection_data = self.vision_core.inspect_website(
                    url=self.driver.current_url, expand_interactive=True, max_scrolls=4
                )
                extracted_data = self._extract_data_from_inspection(
                    inspection_data=inspection_data, expected_fields=expected_fields, page_type=page_type
                )
                pagination_metadata = {
                    "pages_visited": 1,
                    "pagination_detected": False,
                    "pagination_method": None,
                    "pagination_stopped_reason": "single_page_mode"
                }
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Phase 1 Step 3: Emit learning signals
            self._flush_selector_signals(execution_id)
            self._emit_aggregate_signals(execution_id)
            learning_metrics = self._compute_learning_metrics()
            
            self.orchestrator.log_execution(
                task_id=execution_id,
                tool_name="web_navigator_agent",
                action_type="navigate_and_extract",
                status="COMPLETED",
                data={
                    "url": target_url,
                    "items_extracted": len(extracted_data.get("items", [])),
                    "pages_visited": pagination_metadata.get("pages_visited", 1),
                    "selectors_attempted": learning_metrics["total_attempted"],
                    "selector_success_rate": learning_metrics["success_rate"]
                },
                duration_ms=duration_ms
            )
            
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
                    "selectors_attempted": learning_metrics["total_attempted"],
                    "selectors_succeeded": learning_metrics["total_succeeded"],
                    "selector_success_rate": learning_metrics["success_rate"],
                    **pagination_metadata
                }
            }
            
            logger.info(f"✓ Navigation completed: {len(extracted_data.get('items', []))} items, {pagination_metadata['pages_visited']} page(s)")
            return response
            
        except Exception as e:
            logger.error(f"Navigation failed: {e}", exc_info=True)
            return self._build_error_response(execution_id=execution_id, error=str(e), start_time=start_time)
        
        finally:
            self._close_browser()
    
    def _extract_data_from_inspection(
        self, inspection_data: Dict[str, Any], expected_fields: List[str], page_type: str
    ) -> Dict[str, Any]:
        """Extract structured data from BuddysVisionCore inspection results."""
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
        
        links = inspection_data.get("links", [])
        
        for link in links[:50]:
            item = {}
            if "name" in expected_fields:
                item["name"] = link.get("text", "").strip()
            if "url" in expected_fields:
                item["url"] = link.get("href", "")
            if "category" in expected_fields:
                item["category"] = link.get("class", "").split()[0] if link.get("class") else ""
            if "location" in expected_fields:
                item["location"] = ""
            
            if item.get("name") or item.get("url"):
                extracted["items"].append(item)
        
        logger.info(f"Extracted {len(extracted['items'])} items from inspection")
        return extracted
    
    def _detect_pagination(self) -> Optional[Tuple[WebElement, str]]:
        """Detect pagination control on current page."""
        try:
            # Strategy 1: rel="next"
            try:
                attempt_start = time.time()
                next_link = self.driver.find_element(By.CSS_SELECTOR, "a[rel='next']")
                duration = int((time.time() - attempt_start) * 1000)
                if next_link.is_displayed() and next_link.is_enabled():
                    self._emit_selector_signal("a[rel='next']", "css", "success", duration, 0)
                    logger.info("Pagination detected: rel='next' link")
                    return (next_link, "rel_next")
                else:
                    self._emit_selector_signal("a[rel='next']", "css", "failure", duration, 0)
            except NoSuchElementException:
                self._emit_selector_signal("a[rel='next']", "css", "failure", 50, 0)
            
            # Strategy 2: aria-label containing "next"
            try:
                attempt_start = time.time()
                next_elements = self.driver.find_elements(By.XPATH, 
                    "//*[contains(translate(@aria-label, 'NEXT', 'next'), 'next') and (self::a or self::button)]")
                duration = int((time.time() - attempt_start) * 1000)
                for elem in next_elements:
                    if elem.is_displayed() and elem.is_enabled():
                        self._emit_selector_signal("aria-label contains 'next'", "aria", "success", duration, 0)
                        logger.info(f"Pagination detected: aria-label='{elem.get_attribute('aria-label')}'")
                        return (elem, "aria_label")
                if next_elements:
                    self._emit_selector_signal("aria-label contains 'next'", "aria", "failure", duration, 0)
            except NoSuchElementException:
                self._emit_selector_signal("aria-label contains 'next'", "aria", "failure", 50, 0)
            
            # Strategy 3: Text patterns
            next_patterns = ["Next", "next", "NEXT", ">", "→", "More", "more", "Next Page", "next page"]
            for pattern in next_patterns:
                try:
                    attempt_start = time.time()
                    buttons = self.driver.find_elements(By.TAG_NAME, "button")
                    duration = int((time.time() - attempt_start) * 1000)
                    for btn in buttons:
                        if btn.text.strip() == pattern and btn.is_displayed() and btn.is_enabled():
                            self._emit_selector_signal(f"button:'{pattern}'", "text", "success", duration, 0)
                            logger.info(f"Pagination detected: button text='{pattern}'")
                            return (btn, "text_match")
                    
                    links = self.driver.find_elements(By.TAG_NAME, "a")
                    for link in links:
                        if link.text.strip() == pattern and link.is_displayed() and link.is_enabled():
                            self._emit_selector_signal(f"a:'{pattern}'", "text", "success", duration, 0)
                            logger.info(f"Pagination detected: link text='{pattern}'")
                            return (link, "text_match")
                    
                    self._emit_selector_signal(f"text:'{pattern}'", "text", "failure", duration, 0)
                except (NoSuchElementException, StaleElementReferenceException):
                    self._emit_selector_signal(f"text:'{pattern}'", "text", "failure", 50, 0)
            
            # Strategy 4: Page numbers
            try:
                attempt_start = time.time()
                page_links = self.driver.find_elements(By.XPATH, "//a[string(number(text())) != 'NaN' and self::a]")
                duration = int((time.time() - attempt_start) * 1000)
                if page_links:
                    current_page = 1
                    for link in page_links:
                        classes = link.get_attribute("class") or ""
                        if "active" in classes.lower() or "current" in classes.lower():
                            try:
                                current_page = int(link.text.strip())
                            except ValueError:
                                pass
                    
                    next_page = current_page + 1
                    for link in page_links:
                        try:
                            page_num = int(link.text.strip())
                            if page_num == next_page and link.is_displayed() and link.is_enabled():
                                self._emit_selector_signal(f"page_number:{next_page}", "page_number", "success", duration, 0)
                                logger.info(f"Pagination detected: page number {next_page}")
                                return (link, "page_number")
                        except ValueError:
                            pass
                    self._emit_selector_signal("page_number", "page_number", "failure", duration, 0)
            except (NoSuchElementException, StaleElementReferenceException):
                self._emit_selector_signal("page_number", "page_number", "failure", 50, 0)
            
            logger.info("No pagination control detected")
            return None
            
        except Exception as e:
            logger.warning(f"Error detecting pagination: {e}")
            return None
    
    def _go_to_next_page(self, element: WebElement) -> bool:
        """Click pagination element and verify navigation occurred."""
        try:
            nav_start = time.time()
            current_url = self.driver.current_url
            current_content_hash = self._get_page_content_hash()
            
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.5)
            
            clicked = False
            retry_count = 0
            for attempt in range(3):
                try:
                    element.click()
                    clicked = True
                    break
                except Exception:
                    retry_count += 1
                    try:
                        self.driver.execute_script("arguments[0].click();", element)
                        clicked = True
                        break
                    except Exception:
                        if attempt < 2:
                            time.sleep(0.5)
            
            if not clicked:
                nav_duration = int((time.time() - nav_start) * 1000)
                self._emit_selector_signal("pagination_element.click()", "interaction", "failure", nav_duration, retry_count)
                logger.warning("Failed to click pagination element")
                return False
            
            time.sleep(2)
            new_url = self.driver.current_url
            new_content_hash = self._get_page_content_hash()
            nav_duration = int((time.time() - nav_start) * 1000)
            
            if new_url != current_url or new_content_hash != current_content_hash:
                self._emit_selector_signal("pagination_element.click()", "interaction", "success", nav_duration, retry_count)
                logger.info("Navigation successful")
                return True
            
            self._emit_selector_signal("pagination_element.click()", "interaction", "failure", nav_duration, retry_count)
            logger.warning("Navigation failed: No URL or content change detected")
            return False
            
        except Exception as e:
            logger.error(f"Error navigating to next page: {e}")
            return False
    
    def _get_page_content_hash(self) -> str:
        """Get hash of page content for duplicate detection."""
        try:
            title = self.driver.title or ""
            body = self.driver.find_element(By.TAG_NAME, "body").text[:1000]
            content = f"{title}|{body}"
            return hashlib.md5(content.encode()).hexdigest()
        except Exception:
            return ""
    
    def _paginate_and_extract(
        self, expected_fields: List[str], page_type: str, max_pages: int
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Extract data across multiple pages with pagination."""
        all_items = []
        pages_visited = 0
        pagination_detected = False
        pagination_method = None
        stopped_reason = None
        seen_urls = set()
        seen_content_hashes = set()
        
        logger.info(f"Starting pagination: max_pages={max_pages}")
        
        while pages_visited < max_pages:
            pages_visited += 1
            self.current_page_number = pages_visited
            logger.info(f"Extracting from page {pages_visited}/{max_pages}")
            
            current_hash = self._get_page_content_hash()
            if current_hash in seen_content_hashes:
                logger.info("Duplicate page content detected, stopping")
                stopped_reason = "duplicate"
                break
            seen_content_hashes.add(current_hash)
            
            try:
                inspection_data = self.vision_core.inspect_website(
                    url=self.driver.current_url, expand_interactive=True, max_scrolls=4
                )
                page_data = self._extract_data_from_inspection(
                    inspection_data=inspection_data, expected_fields=expected_fields, page_type=page_type
                )
                
                for item in page_data.get("items", []):
                    item_url = item.get("url", "")
                    if item_url and item_url not in seen_urls:
                        all_items.append(item)
                        seen_urls.add(item_url)
                    elif not item_url:
                        all_items.append(item)
                
                logger.info(f"Extracted {len(page_data.get('items', []))} items from page {pages_visited} (total: {len(all_items)})")
                
            except Exception as e:
                logger.error(f"Error extracting from page {pages_visited}: {e}")
                stopped_reason = "extraction_error"
                break
            
            if pages_visited >= max_pages:
                logger.info("Reached max_pages limit")
                stopped_reason = "max_pages"
                break
            
            pagination_result = self._detect_pagination()
            
            if pagination_result is None:
                logger.info("No pagination control found, stopping")
                stopped_reason = "no_next"
                break
            
            element, method = pagination_result
            pagination_detected = True
            pagination_method = method
            
            if not self._go_to_next_page(element):
                logger.info("Failed to navigate to next page, stopping")
                stopped_reason = "navigation_failed"
                break
            
            time.sleep(1)
        
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
    
    def _build_error_response(self, execution_id: str, error: str, start_time: float) -> Dict[str, Any]:
        """Build error response and log to orchestrator."""
        duration_ms = int((time.time() - start_time) * 1000)
        
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

