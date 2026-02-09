"""
PHASE 5: WEB TOOLS INTEGRATION
===============================

Safely integrates Buddy's Vision and Arms subsystems into the main agent loop.
Provides tool-level wrappers for web interactions with:
- Dry-run mode for high-risk actions
- Risk level classification
- Session management
- Metrics capture
- Feature flag respect
- Thread safety

NO modifications to Phase 1-4 code - read-only integration pattern.
"""

import os
import time
import logging
import threading
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
from enum import Enum

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Buddy's subsystems (read-only imports)
from backend.buddys_vision import BuddysVision
from backend.buddys_vision_core import BuddysVisionCore
from backend.buddys_arms import BuddysArms
from backend.screenshot_capture import capture_full_context

logger = logging.getLogger(__name__)


# ============================================================================
# RISK CLASSIFICATION
# ============================================================================

class ActionRisk(Enum):
    """Risk levels for web actions"""
    LOW = "low"         # Read-only: inspect, navigate, screenshot
    MEDIUM = "medium"   # Non-permanent: form fill (no submit)
    HIGH = "high"       # Permanent: form submit, delete, purchase


# ============================================================================
# GLOBAL BROWSER SESSION
# ============================================================================

_browser_session = {
    "driver": None,
    "vision": None,
    "arms": None,
    "active": False,
    "created_at": None,
    "lock": threading.RLock()
}


def _is_driver_healthy(driver) -> bool:
    """Return True if the WebDriver session is alive and responsive."""
    if driver is None:
        return False
    try:
        # Access a lightweight property to validate the session
        _ = driver.current_url
        return True
    except Exception as e:
        logger.warning(f"WebDriver health check failed: {e}")
        return False


def _reset_browser_session() -> None:
    """Safely tear down any existing browser session and mark it inactive."""
    global _browser_session
    try:
        driver = _browser_session.get("driver")
        if driver:
            try:
                driver.quit()
            except Exception as e:
                logger.warning(f"Error while quitting stale WebDriver: {e}")
    finally:
        _browser_session.update({
            "driver": None,
            "vision": None,
            "arms": None,
            "active": False,
            "created_at": None
        })


def _get_browser_session() -> Dict[str, Any]:
    """Get or create browser session (thread-safe)"""
    global _browser_session
    
    with _browser_session["lock"]:
        if _browser_session["active"] and _browser_session["driver"]:
            # Ensure the cached driver is still alive
            if _is_driver_healthy(_browser_session["driver"]):
                return _browser_session
            logger.warning("Stale browser session detected; resetting session.")
            _reset_browser_session()

        if _browser_session["active"] and _browser_session["driver"]:
            return _browser_session
        
        # Initialize new session
        logger.info("Initializing browser session...")
        
        try:
            # Chrome options
            chrome_options = Options()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            
            # Check for headless mode from environment
            if os.getenv('WEB_TOOLS_HEADLESS', 'false').lower() == 'true':
                chrome_options.add_argument("--headless")
            
            # Use cached ChromeDriver
            chromedriver_path = Path.home() / ".wdm" / "drivers" / "chromedriver" / "win64" / "144.0.7559.133" / "chromedriver-win32" / "chromedriver.exe"
            
            if chromedriver_path.exists():
                service = Service(str(chromedriver_path))
            else:
                service = Service(ChromeDriverManager().install())
            
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Initialize Vision and Arms
            vision_core = BuddysVisionCore(driver, timeout=10)
            vision = BuddysVision(driver=driver)
            arms = BuddysArms(driver, vision_core, timeout=15)
            
            _browser_session.update({
                "driver": driver,
                "vision": vision,
                "arms": arms,
                "active": True,
                "created_at": datetime.now().isoformat()
            })
            
            logger.info("✓ Browser session initialized")
            return _browser_session
            
        except Exception as e:
            logger.error(f"Failed to initialize browser session: {e}")
            raise


def _check_dry_run(action_risk: ActionRisk) -> bool:
    """Check if action should be dry-run based on risk level and environment"""
    dry_run_mode = os.getenv('WEB_TOOLS_DRY_RUN', 'false').lower() == 'true'
    
    if dry_run_mode:
        return True
    
    # High-risk actions default to dry-run unless explicitly enabled
    if action_risk == ActionRisk.HIGH:
        high_risk_enabled = os.getenv('WEB_TOOLS_ALLOW_HIGH_RISK', 'false').lower() == 'true'
        return not high_risk_enabled
    
    return False


def _log_action(action_name: str, params: Dict, risk: ActionRisk, dry_run: bool, result: Dict):
    """Log action with metrics for Phase 4 integration"""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "action": action_name,
        "parameters": params,
        "risk_level": risk.value,
        "dry_run": dry_run,
        "success": result.get("success", False),
        "execution_time_ms": result.get("execution_time_ms", 0),
        "error": result.get("error")
    }
    
    # Write to metrics file for Phase 4 integration
    metrics_dir = Path("outputs/integration_metrics")
    metrics_dir.mkdir(parents=True, exist_ok=True)
    
    metrics_file = metrics_dir / f"web_actions_{datetime.now().strftime('%Y%m%d')}.jsonl"
    
    import json
    with open(metrics_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(log_entry) + '\n')


# ============================================================================
# WEB INSPECTION TOOLS (LOW RISK - READ ONLY)
# ============================================================================

def web_inspect(url: str) -> Dict[str, Any]:
    """
    Inspect a website and return structured DOM analysis.
    
    Risk Level: LOW (read-only)
    
    Args:
        url: Website URL to inspect
    
    Returns:
        {
            'success': True/False,
            'url': str,
            'inspection': {
                'forms': [...],
                'buttons': [...],
                'inputs': [...],
                'links': [...],
                'structure': {...},
                ...
            },
            'message': str,
            'error': Optional[str]
        }
    """
    start_time = time.time()
    risk = ActionRisk.LOW
    dry_run = _check_dry_run(risk)
    
    try:
        if dry_run:
            result = {
                "success": False,
                "dry_run": True,
                "url": url,
                "message": f"[DRY RUN] Would inspect: {url}",
                "execution_time_ms": 0
            }
        else:
            session = _get_browser_session()
            vision = session["vision"]
            
            # Use Vision to inspect website
            inspection = vision.see_website(url, expand_interactive=True)
            
            execution_time = (time.time() - start_time) * 1000
            
            result = {
                "success": True,
                "url": url,
                "inspection": inspection,
                "message": f"Successfully inspected {url}",
                "execution_time_ms": execution_time
            }
        
        _log_action("web_inspect", {"url": url}, risk, dry_run, result)
        return result
        
    except Exception as e:
        logger.error(f"web_inspect error: {e}")
        execution_time = (time.time() - start_time) * 1000
        result = {
            "success": False,
            "url": url,
            "error": str(e),
            "message": f"Failed to inspect {url}: {e}",
            "execution_time_ms": execution_time
        }
        _log_action("web_inspect", {"url": url}, risk, dry_run, result)
        return result


def web_screenshot() -> Dict[str, Any]:
    """
    Capture screenshot of current page with clickable element overlay.
    
    Risk Level: LOW (read-only)
    
    Returns:
        {
            'success': True/False,
            'screenshot': {'base64': str, 'width': int, 'height': int},
            'page_state': {'url': str, 'title': str, ...},
            'clickables': [{'tag': str, 'text': str, 'x': int, 'y': int, ...}],
            'message': str
        }
    """
    start_time = time.time()
    risk = ActionRisk.LOW
    dry_run = _check_dry_run(risk)
    
    try:
        if dry_run:
            result = {
                "success": False,
                "dry_run": True,
                "message": "[DRY RUN] Would capture screenshot",
                "execution_time_ms": 0
            }
        else:
            session = _get_browser_session()
            driver = session["driver"]
            
            # Capture full context (screenshot + page state + clickables)
            context = capture_full_context(driver)
            
            execution_time = (time.time() - start_time) * 1000
            
            result = {
                "success": True,
                "screenshot": context.get("screenshot"),
                "page_state": context.get("page_state"),
                "clickables": context.get("clickables"),
                "message": "Screenshot captured successfully",
                "execution_time_ms": execution_time
            }
        
        _log_action("web_screenshot", {}, risk, dry_run, result)
        return result
        
    except Exception as e:
        logger.error(f"web_screenshot error: {e}")
        execution_time = (time.time() - start_time) * 1000
        result = {
            "success": False,
            "error": str(e),
            "message": f"Failed to capture screenshot: {e}",
            "execution_time_ms": execution_time
        }
        _log_action("web_screenshot", {}, risk, dry_run, result)
        return result


def web_extract(extraction_hint: str, extract_type: str = "text") -> Dict[str, Any]:
    """
    Extract content from page by semantic understanding.
    Instead of guessing CSS selectors, we scrape the page and use LLM to find the right content.
    
    Risk Level: LOW (read-only)
    
    Args:
        extraction_hint: What to extract (e.g., "services", "contact information", "pricing")
        extract_type: 'text', 'html', 'attributes' (for compatibility)
    
    Returns:
        {
            'success': True/False,
            'extraction_hint': str,
            'content': str,
            'sections': [{'title': str, 'text': str}, ...],
            'count': int,
            'message': str
        }
    """
    start_time = time.time()
    risk = ActionRisk.LOW
    dry_run = _check_dry_run(risk)
    
    try:
        if dry_run:
            result = {
                "success": False,
                "dry_run": True,
                "extraction_hint": extraction_hint,
                "message": f"[DRY RUN] Would extract: {extraction_hint}",
                "execution_time_ms": 0
            }
        else:
            session = _get_browser_session()
            driver = session["driver"]
            
            # Get page HTML
            page_source = driver.page_source
            
            # Parse with BeautifulSoup
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get main content areas (common patterns)
            main_content_selectors = [
                'main', '.main', '#main', '.content', '#content',
                '.container', '.page-content', '.page'
            ]
            
            content_element = soup
            for selector in main_content_selectors:
                elem = soup.select_one(selector)
                if elem:
                    content_element = elem
                    break
            
            # Extract all text
            text = content_element.get_text()
            
            # Extract sections (headings + following text)
            sections = []
            current_section = None
            
            for tag in content_element.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'div', 'section', 'article']):
                if tag.name in ['h1', 'h2', 'h3', 'h4']:
                    title = tag.get_text(strip=True)
                    if current_section and current_section['text'].strip():
                        sections.append(current_section)
                    current_section = {'title': title, 'text': ''}
                elif current_section and tag.name == 'p':
                    text_content = tag.get_text(strip=True)
                    if text_content:
                        current_section['text'] += text_content + '\n'
            
            if current_section and current_section['text'].strip():
                sections.append(current_section)
            
            # Use LLM to find the most relevant sections for the extraction hint
            from backend.llm_client import llm_client
            
            if sections:
                # Build a summary of available sections
                section_summary = "\n".join([f"- {s['title']}: {s['text'][:200]}" for s in sections])
                
                prompt = f"""The user wants to extract: "{extraction_hint}"

Here are the page sections available:
{section_summary}

Which sections are MOST relevant to "{extraction_hint}"? Return a comma-separated list of section titles.
If no sections match, return "NO_MATCH".
Relevant sections:"""
                
                relevant = llm_client.complete(prompt, max_tokens=500, temperature=0.2).strip()
                
                extracted_content = []
                if relevant.lower() != 'no_match':
                    relevant_titles = [t.strip() for t in relevant.split(',')]
                    for section in sections:
                        if section['title'] in relevant_titles:
                            extracted_content.append(section)
                
                # If LLM couldn't find sections, search for the hint in text
                if not extracted_content:
                    hint_lower = extraction_hint.lower()
                    for section in sections:
                        if hint_lower in section['title'].lower() or hint_lower in section['text'][:200].lower():
                            extracted_content.append(section)
                
                # If still nothing, return top 3 largest sections
                if not extracted_content:
                    extracted_content = sorted(sections, key=lambda s: len(s['text']), reverse=True)[:3]
            else:
                # No sections found, return raw text in chunks
                text_clean = text.strip()
                if len(text_clean) > 2000:
                    text_clean = text_clean[:2000]
                
                extracted_content = [{'title': extraction_hint, 'text': text_clean}]
            
            # Format result
            formatted_sections = []
            full_content = ""
            
            for section in extracted_content:
                formatted_sections.append({
                    'title': section.get('title', 'Content'),
                    'text': section.get('text', '')[:1000]
                })
                full_content += f"\n{section.get('title', '')}\n{section.get('text', '')}\n"
            
            execution_time = (time.time() - start_time) * 1000
            
            result = {
                "success": True,
                "extraction_hint": extraction_hint,
                "content": full_content[:3000],
                "sections": formatted_sections,
                "count": len(formatted_sections),
                "message": f"Extracted {len(formatted_sections)} relevant sections for '{extraction_hint}'",
                "execution_time_ms": execution_time
            }
        
        _log_action("web_extract", {"hint": extraction_hint, "type": extract_type}, risk, dry_run, result)
        return result
        
    except Exception as e:
        logger.error(f"web_extract error: {e}")
        execution_time = (time.time() - start_time) * 1000
        result = {
            "success": False,
            "extraction_hint": extraction_hint,
            "error": str(e),
            "message": f"Failed to extract '{extraction_hint}': {e}",
            "execution_time_ms": execution_time
        }
        _log_action("web_extract", {"hint": extraction_hint, "type": extract_type}, risk, dry_run, result)
        return result


# ============================================================================
# WEB NAVIGATION TOOLS (LOW RISK)
# ============================================================================

def web_navigate(url: str) -> Dict[str, Any]:
    """
    Navigate browser to a URL.
    
    Risk Level: LOW (navigation is reversible)
    
    Args:
        url: Target URL
    
    Returns:
        {
            'success': True/False,
            'url': str,
            'final_url': str,
            'title': str,
            'message': str
        }
    """
    start_time = time.time()
    risk = ActionRisk.LOW
    dry_run = _check_dry_run(risk)
    
    def _navigate_once() -> Dict[str, Any]:
        if dry_run:
            return {
                "success": False,
                "dry_run": True,
                "url": url,
                "message": f"[DRY RUN] Would navigate to: {url}",
                "execution_time_ms": 0
            }

        session = _get_browser_session()
        arms = session["arms"]
        driver = session["driver"]

        # Navigate using Arms
        arms.navigate(url)

        # Wait for page load
        time.sleep(1)

        execution_time = (time.time() - start_time) * 1000

        return {
            "success": True,
            "url": url,
            "final_url": driver.current_url,
            "title": driver.title,
            "message": f"Navigated to {url}",
            "execution_time_ms": execution_time
        }

    try:
        result = _navigate_once()
        
        _log_action("web_navigate", {"url": url}, risk, dry_run, result)
        return result
        
    except Exception as e:
        error_text = str(e)
        if ("invalid session id" in error_text.lower() or "disconnected" in error_text.lower()):
            logger.warning("WebDriver session invalid. Resetting and retrying navigation once.")
            _reset_browser_session()
            try:
                result = _navigate_once()
                _log_action("web_navigate", {"url": url}, risk, dry_run, result)
                return result
            except Exception as retry_error:
                logger.error(f"web_navigate retry failed: {retry_error}")
                error_text = str(retry_error)
        logger.error(f"web_navigate error: {e}")
        execution_time = (time.time() - start_time) * 1000
        result = {
            "success": False,
            "url": url,
            "error": error_text,
            "message": f"Failed to navigate to {url}: {error_text}",
            "execution_time_ms": execution_time
        }
        _log_action("web_navigate", {"url": url}, risk, dry_run, result)
        return result


# ============================================================================
# WEB INTERACTION TOOLS (MEDIUM RISK)
# ============================================================================

def web_click(selector_or_text: str, tag: str = "button") -> Dict[str, Any]:
    """
    Click an element by selector or visible text.
    
    Risk Level: MEDIUM (can trigger navigation/actions)
    
    Args:
        selector_or_text: CSS selector or visible text to click
        tag: Element tag if using text matching (default: 'button')
    
    Returns:
        {
            'success': True/False,
            'target': str,
            'message': str
        }
    """
    start_time = time.time()
    risk = ActionRisk.MEDIUM
    dry_run = _check_dry_run(risk)
    
    try:
        if dry_run:
            result = {
                "success": False,
                "dry_run": True,
                "target": selector_or_text,
                "message": f"[DRY RUN] Would click: {selector_or_text}",
                "execution_time_ms": 0
            }
        else:
            session = _get_browser_session()
            arms = session["arms"]
            
            # Try click by text (Arms method)
            success = arms.click_by_text(selector_or_text, tag=tag)
            
            execution_time = (time.time() - start_time) * 1000
            
            if success:
                result = {
                    "success": True,
                    "target": selector_or_text,
                    "message": f"Clicked: {selector_or_text}",
                    "execution_time_ms": execution_time
                }
            else:
                result = {
                    "success": False,
                    "target": selector_or_text,
                    "message": f"Failed to click: {selector_or_text} (element not found or not clickable)",
                    "execution_time_ms": execution_time
                }
        
        _log_action("web_click", {"target": selector_or_text, "tag": tag}, risk, dry_run, result)
        return result
        
    except Exception as e:
        logger.error(f"web_click error: {e}")
        execution_time = (time.time() - start_time) * 1000
        result = {
            "success": False,
            "target": selector_or_text,
            "error": str(e),
            "message": f"Error clicking {selector_or_text}: {e}",
            "execution_time_ms": execution_time
        }
        _log_action("web_click", {"target": selector_or_text, "tag": tag}, risk, dry_run, result)
        return result


def web_fill(field_hint: str, value: str) -> Dict[str, Any]:
    """
    Fill a form field by label/placeholder/name/id hint.
    
    Risk Level: MEDIUM (modifies page state, but no permanent action)
    
    Args:
        field_hint: Text hint to identify field (label, placeholder, name, id)
        value: Value to fill
    
    Returns:
        {
            'success': True/False,
            'field_hint': str,
            'value': str (masked if password),
            'message': str
        }
    """
    start_time = time.time()
    risk = ActionRisk.MEDIUM
    dry_run = _check_dry_run(risk)
    
    try:
        # Mask sensitive values in logs
        is_password = any(word in field_hint.lower() for word in ['password', 'pass', 'pwd', 'secret'])
        logged_value = '***' if is_password else value
        
        if dry_run:
            result = {
                "success": False,
                "dry_run": True,
                "field_hint": field_hint,
                "value": logged_value,
                "message": f"[DRY RUN] Would fill field '{field_hint}' with value",
                "execution_time_ms": 0
            }
        else:
            session = _get_browser_session()
            arms = session["arms"]
            
            # Fill field using Arms
            success = arms.fill_field(field_hint, value)
            
            execution_time = (time.time() - start_time) * 1000
            
            if success:
                result = {
                    "success": True,
                    "field_hint": field_hint,
                    "value": logged_value,
                    "message": f"Filled field: {field_hint}",
                    "execution_time_ms": execution_time
                }
            else:
                result = {
                    "success": False,
                    "field_hint": field_hint,
                    "value": logged_value,
                    "message": f"Failed to fill field: {field_hint} (field not found)",
                    "execution_time_ms": execution_time
                }
        
        _log_action("web_fill", {"field_hint": field_hint, "value": logged_value}, risk, dry_run, result)
        return result
        
    except Exception as e:
        logger.error(f"web_fill error: {e}")
        execution_time = (time.time() - start_time) * 1000
        result = {
            "success": False,
            "field_hint": field_hint,
            "error": str(e),
            "message": f"Error filling field {field_hint}: {e}",
            "execution_time_ms": execution_time
        }
        _log_action("web_fill", {"field_hint": field_hint}, risk, dry_run, result)
        return result


# ============================================================================
# HIGH-RISK TOOLS (PERMANENT ACTIONS)
# ============================================================================

def web_submit_form() -> Dict[str, Any]:
    """
    Submit the first form on the page.
    
    Risk Level: HIGH (permanent action - form submission)
    
    Returns:
        {
            'success': True/False,
            'message': str,
            'warning': str (always includes high-risk warning)
        }
    """
    start_time = time.time()
    risk = ActionRisk.HIGH
    dry_run = _check_dry_run(risk)
    
    # HIGH RISK - always defaults to dry-run unless explicitly enabled
    warning = "⚠️  HIGH RISK ACTION: Form submission is permanent and cannot be undone."
    
    try:
        if dry_run:
            result = {
                "success": False,
                "dry_run": True,
                "message": "[DRY RUN] Would submit form (blocked: high-risk action)",
                "warning": warning,
                "execution_time_ms": 0
            }
        else:
            session = _get_browser_session()
            arms = session["arms"]
            
            # Submit form using Arms
            success = arms.submit_first_form()
            
            execution_time = (time.time() - start_time) * 1000
            
            if success:
                result = {
                    "success": True,
                    "message": "Form submitted successfully",
                    "warning": warning,
                    "execution_time_ms": execution_time
                }
            else:
                result = {
                    "success": False,
                    "message": "Failed to submit form (no form found or submission failed)",
                    "warning": warning,
                    "execution_time_ms": execution_time
                }
        
        _log_action("web_submit_form", {}, risk, dry_run, result)
        return result
        
    except Exception as e:
        logger.error(f"web_submit_form error: {e}")
        execution_time = (time.time() - start_time) * 1000
        result = {
            "success": False,
            "error": str(e),
            "message": f"Error submitting form: {e}",
            "warning": warning,
            "execution_time_ms": execution_time
        }
        _log_action("web_submit_form", {}, risk, dry_run, result)
        return result


# ============================================================================
# SESSION MANAGEMENT TOOLS
# ============================================================================

def web_browser_start() -> Dict[str, Any]:
    """
    Start a persistent browser session.
    
    Returns:
        {
            'success': True/False,
            'session_active': bool,
            'created_at': str,
            'message': str
        }
    """
    try:
        session = _get_browser_session()
        
        return {
            "success": True,
            "session_active": session["active"],
            "created_at": session["created_at"],
            "message": "Browser session active"
        }
        
    except Exception as e:
        logger.error(f"web_browser_start error: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to start browser session: {e}"
        }


def web_browser_stop() -> Dict[str, Any]:
    """
    Stop the persistent browser session and clean up.
    
    Returns:
        {
            'success': True/False,
            'message': str
        }
    """
    global _browser_session
    
    try:
        with _browser_session["lock"]:
            if _browser_session["driver"]:
                _browser_session["driver"].quit()
            
            _browser_session.update({
                "driver": None,
                "vision": None,
                "arms": None,
                "active": False,
                "created_at": None
            })
        
        logger.info("Browser session stopped")
        
        return {
            "success": True,
            "message": "Browser session stopped and cleaned up"
        }
        
    except Exception as e:
        logger.error(f"web_browser_stop error: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Error stopping browser session: {e}"
        }


# ============================================================================
# TOOL REGISTRATION
# ============================================================================

def register_web_tools(tool_registry):
    """
    Register all Vision & Arms tools with the tool registry.
    
    Phase 5 Integration: Connects Vision/Arms to main agent loop.
    """
    
    # Inspection tools (LOW RISK - read-only)
    tool_registry.register(
        'web_inspect',
        web_inspect,
        description='Inspect a website and return structured DOM analysis (forms, buttons, inputs, links, structure). Risk: LOW (read-only).'
    )
    
    tool_registry.register(
        'web_screenshot',
        web_screenshot,
        description='Capture screenshot of current page with clickable element overlay metadata. Risk: LOW (read-only).'
    )
    
    tool_registry.register(
        'web_extract',
        web_extract,
        description='Extract content from page elements by CSS selector (text, HTML, attributes). Risk: LOW (read-only).'
    )
    
    # Navigation tools (LOW RISK)
    tool_registry.register(
        'web_navigate',
        web_navigate,
        description='Navigate browser to a URL. Risk: LOW (reversible action).'
    )
    
    # Interaction tools (MEDIUM RISK)
    tool_registry.register(
        'web_click',
        web_click,
        description='Click an element by selector or visible text. Risk: MEDIUM (can trigger actions). Args: selector_or_text, tag (default: button).'
    )
    
    tool_registry.register(
        'web_fill',
        web_fill,
        description='Fill a form field by label/placeholder/name/id hint. Risk: MEDIUM (modifies page state). Args: field_hint, value.'
    )
    
    # High-risk tools (PERMANENT ACTIONS)
    tool_registry.register(
        'web_submit_form',
        web_submit_form,
        description='Submit the first form on the page. Risk: HIGH (permanent action - defaults to dry-run). Requires WEB_TOOLS_ALLOW_HIGH_RISK=true.'
    )
    
    # Session management
    tool_registry.register(
        'web_browser_start',
        web_browser_start,
        description='Start a persistent browser session for web automation.'
    )
    
    tool_registry.register(
        'web_browser_stop',
        web_browser_stop,
        description='Stop the persistent browser session and clean up resources.'
    )
    
    logger.info("✓ Registered 9 web tools (Vision & Arms integration)")
    logger.info("  - Inspection: web_inspect, web_screenshot, web_extract")
    logger.info("  - Navigation: web_navigate")
    logger.info("  - Interaction: web_click, web_fill")
    logger.info("  - High-Risk: web_submit_form (dry-run by default)")
    logger.info("  - Session: web_browser_start, web_browser_stop")
