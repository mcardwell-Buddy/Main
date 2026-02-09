"""
Screenshot and page state capture for embedded browser learning.
Captures both visual screenshots and detailed DOM structure.
"""

import logging
import base64
import json
from io import BytesIO

logger = logging.getLogger(__name__)


def capture_screenshot_as_base64(driver, max_width=1280, max_height=720):
    """
    Capture current browser view as base64-encoded PNG for embedding in UI.
    
    Args:
        driver: Selenium WebDriver instance
        max_width: Target width (scales down if needed)
        max_height: Target height (scales down if needed)
    
    Returns:
        dict with 'base64' and 'size' or None on error
    """
    try:
        # Get full page screenshot
        screenshot = driver.get_screenshot_as_png()
        
        from PIL import Image

        # Open as PIL image
        img = Image.open(BytesIO(screenshot))
        
        # Scale if needed
        if img.width > max_width or img.height > max_height:
            img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
        
        # Convert to base64
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_b64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        return {
            'base64': img_b64,
            'width': img.width,
            'height': img.height,
            'format': 'png'
        }
    except Exception as e:
        logger.error(f"Screenshot capture failed: {e}", exc_info=True)
        return None


def capture_page_state(driver):
    """
    Capture current page URL, title, and simplified DOM for context.
    
    Args:
        driver: Selenium WebDriver instance
    
    Returns:
        dict with page metadata
    """
    try:
        return {
            'url': driver.current_url,
            'title': driver.title,
            'page_source_length': len(driver.page_source),
            'viewport': driver.execute_script(
                "return {width: window.innerWidth, height: window.innerHeight}"
            )
        }
    except Exception as e:
        logger.error(f"Page state capture failed: {e}", exc_info=True)
        return {}


def capture_clickable_elements(driver, limit=50):
    """
    Find all clickable elements on page for overlay display.
    
    Args:
        driver: Selenium WebDriver instance
        limit: Max elements to capture
    
    Returns:
        list of dicts with element info (text, position, tag)
    """
    try:
        from selenium.webdriver.common.by import By

        elements = []
        
        # Find buttons, links, and interactive elements
        selectors = [
            'button', 'a[href]', 'input[type="submit"]',
            'input[type="button"]', '[role="button"]',
            'select', 'textarea'
        ]
        
        for selector in selectors:
            if len(elements) >= limit:
                break
            
            try:
                items = driver.find_elements(By.CSS_SELECTOR, selector)
                for item in items:
                    if len(elements) >= limit:
                        break
                    
                    try:
                        # Get element position and size
                        location = item.location
                        size = item.size
                        
                        # Only include visible elements
                        if size['width'] > 0 and size['height'] > 0:
                            elements.append({
                                'tag': item.tag_name,
                                'text': item.text[:50] if item.text else '',
                                'x': location['x'],
                                'y': location['y'],
                                'width': size['width'],
                                'height': size['height'],
                                'type': item.get_attribute('type') or '',
                                'name': item.get_attribute('name') or '',
                            })
                    except:
                        pass
            except:
                pass
        
        return elements
    except Exception as e:
        logger.error(f"Clickable elements capture failed: {e}", exc_info=True)
        return []


def capture_full_context(driver):
    """
    Capture screenshot + page state + clickable elements.
    
    Args:
        driver: Selenium WebDriver instance
    
    Returns:
        dict with 'screenshot', 'page_state', 'clickables'
    """
    return {
        'screenshot': capture_screenshot_as_base64(driver),
        'page_state': capture_page_state(driver),
        'clickables': capture_clickable_elements(driver)
    }
