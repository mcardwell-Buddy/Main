"""
Page Inspector - Automatically analyze and report page elements
"""
import logging
from typing import List, Dict
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

logger = logging.getLogger(__name__)


def inspect_page_elements(driver: WebDriver) -> Dict:
    """
    Analyze current page and report all important elements (including hidden ones).
    
    Args:
        driver: Selenium WebDriver instance
        
    Returns:
        Dictionary with categorized element information
    """
    report = {
        "url": driver.current_url,
        "title": driver.title,
        "inputs": [],
        "buttons": [],
        "links": [],
        "selects": [],
        "labels": [],
        "headings": [],
        "all_text": []
    }
    
    try:
        # Find ALL input fields (including hidden ones)
        inputs = driver.find_elements(By.TAG_NAME, "input")
        for inp in inputs:
            try:
                is_displayed = inp.is_displayed()
            except:
                is_displayed = False
            try:
                is_enabled = inp.is_enabled()
            except:
                is_enabled = False
            
            # Include all inputs with meaningful attributes
            if inp.get_attribute("id") or inp.get_attribute("name") or inp.get_attribute("placeholder"):
                report["inputs"].append({
                    "type": inp.get_attribute("type"),
                    "id": inp.get_attribute("id"),
                    "name": inp.get_attribute("name"),
                    "class": inp.get_attribute("class"),
                    "placeholder": inp.get_attribute("placeholder"),
                    "value": inp.get_attribute("value"),
                    "visible": is_displayed,
                    "enabled": is_enabled,
                })
        
        # Find all buttons (including hidden ones)
        buttons = driver.find_elements(By.TAG_NAME, "button")
        for btn in buttons:
            if btn.text.strip():
                try:
                    is_displayed = btn.is_displayed()
                except:
                    is_displayed = False
                report["buttons"].append({
                    "text": btn.text.strip(),
                    "type": btn.get_attribute("type"),
                    "class": btn.get_attribute("class"),
                    "visible": is_displayed,
                })
        
        # Find all links
        links = driver.find_elements(By.TAG_NAME, "a")
        for link in links[:30]:
            if link.text.strip():
                try:
                    is_displayed = link.is_displayed()
                except:
                    is_displayed = False
                report["links"].append({
                    "text": link.text.strip(),
                    "href": link.get_attribute("href"),
                    "visible": is_displayed,
                })
        
        # Find all select/dropdown fields
        selects = driver.find_elements(By.TAG_NAME, "select")
        for sel in selects:
            report["selects"].append({
                "id": sel.get_attribute("id"),
                "name": sel.get_attribute("name"),
                "class": sel.get_attribute("class"),
            })
        
        # Find all labels (including hidden ones)
        labels = driver.find_elements(By.TAG_NAME, "label")
        for label in labels:
            if label.text.strip():
                try:
                    is_displayed = label.is_displayed()
                except:
                    is_displayed = False
                report["labels"].append({
                    "text": label.text.strip(),
                    "for": label.get_attribute("for"),
                    "visible": is_displayed,
                })
        
        # Find all headings
        for tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            headings = driver.find_elements(By.TAG_NAME, tag)
            for h in headings:
                if h.text.strip():
                    try:
                        is_displayed = h.is_displayed()
                    except:
                        is_displayed = False
                    report["headings"].append({
                        "level": tag,
                        "text": h.text.strip(),
                        "visible": is_displayed,
                    })
        
        # Find all divs with text that might be section headers or field names
        divs = driver.find_elements(By.TAG_NAME, "div")
        for div in divs:
            text = div.text.strip()
            # Look for divs with specific text patterns that might be field labels
            if text and len(text) < 100 and not text.startswith("function"):
                # Check if this div contains common filter words
                if any(word in text.lower() for word in ["employer", "name", "min", "max", "rating", "industry", "location", "broker", "carrier", "state", "city", "zip"]):
                    try:
                        is_displayed = div.is_displayed()
                    except:
                        is_displayed = False
                    report["all_text"].append({
                        "text": text,
                        "tag": "div",
                        "visible": is_displayed,
                        "class": div.get_attribute("class"),
                    })
        
        # Also get spans with text
        spans = driver.find_elements(By.TAG_NAME, "span")
        for span in spans[:100]:  # Limit to first 100
            text = span.text.strip()
            if text and len(text) < 80:
                if any(word in text.lower() for word in ["employer", "name", "min", "max", "rating", "industry", "location", "broker", "carrier", "state", "city", "zip", "search", "filter", "include", "exclude"]):
                    try:
                        is_displayed = span.is_displayed()
                    except:
                        is_displayed = False
                    report["all_text"].append({
                        "text": text,
                        "tag": "span",
                        "visible": is_displayed,
                        "class": span.get_attribute("class"),
                    })
        
    except Exception as e:
        logger.error(f"Error inspecting page: {e}")
    
    return report


def print_inspection_report(report: Dict):
    """Print a formatted inspection report"""
    print("\n" + "=" * 80)
    print("PAGE INSPECTION REPORT")
    print("=" * 80)
    print(f"URL: {report['url']}")
    print(f"Title: {report['title']}")
    
    if report["headings"]:
        print(f"\n📋 HEADINGS ({len(report['headings'])}):")
        for h in report["headings"][:15]:
            vis = "✓" if h.get('visible', True) else "✗"
            print(f"  [{vis}] [{h['level'].upper()}] {h['text']}")
    
    if report["all_text"]:
        print(f"\n📝 FILTER SECTIONS & FIELD NAMES ({len(report['all_text'])}):")
        # Group by visibility
        visible_items = [item for item in report["all_text"] if item.get('visible', True)]
        hidden_items = [item for item in report["all_text"] if not item.get('visible', True)]
        
        if visible_items:
            print("  VISIBLE:")
            for item in visible_items[:30]:
                print(f"    • {item['text']}")
        
        if hidden_items:
            print("  HIDDEN/COLLAPSED:")
            for item in hidden_items[:20]:
                print(f"    • {item['text']}")
    
    if report["labels"]:
        print(f"\n🏷️  LABELS ({len(report['labels'])}):")
        visible_labels = [l for l in report["labels"] if l.get('visible', True)]
        for label in visible_labels[:20]:
            print(f"  • {label['text']}")
    
    if report["inputs"]:
        print(f"\n📝 INPUT FIELDS ({len(report['inputs'])}):")
        visible_inputs = [i for i in report["inputs"] if i.get('visible', True)]
        hidden_inputs = [i for i in report["inputs"] if not i.get('visible', True)]
        
        if visible_inputs:
            print("  VISIBLE:")
            for inp in visible_inputs[:15]:
                id_str = f"id='{inp['id']}'" if inp['id'] else ""
                name_str = f"name='{inp['name']}'" if inp['name'] else ""
                placeholder_str = f"placeholder='{inp['placeholder']}'" if inp['placeholder'] else ""
                attrs = ", ".join(filter(None, [id_str, name_str, placeholder_str]))
                print(f"    {inp['type']}: {attrs}")
        
        if hidden_inputs:
            print("  HIDDEN/NOT VISIBLE:")
            for inp in hidden_inputs[:15]:
                id_str = f"id='{inp['id']}'" if inp['id'] else ""
                name_str = f"name='{inp['name']}'" if inp['name'] else ""
                placeholder_str = f"placeholder='{inp['placeholder']}'" if inp['placeholder'] else ""
                attrs = ", ".join(filter(None, [id_str, name_str, placeholder_str]))
                print(f"    {inp['type']}: {attrs}")
    
    if report["buttons"]:
        print(f"\n🔘 BUTTONS ({len(report['buttons'])}):")
        for btn in report["buttons"][:20]:
            vis = "✓" if btn.get('visible', True) else "✗"
            print(f"  [{vis}] {btn['text']}")
    
    print("=" * 80)


def find_field_by_label(driver: WebDriver, label_text: str) -> List:
    """
    Find input fields associated with a specific label text.
    
    Args:
        driver: Selenium WebDriver instance
        label_text: Text to search for in labels (case-insensitive)
        
    Returns:
        List of matching input elements
    """
    matches = []
    
    try:
        # Find labels containing the text
        labels = driver.find_elements(By.XPATH, f"//label[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{label_text.lower()}')]")
        
        for label in labels:
            # Try to find associated input via 'for' attribute
            for_attr = label.get_attribute("for")
            if for_attr:
                try:
                    inp = driver.find_element(By.ID, for_attr)
                    matches.append(inp)
                except:
                    pass
            
            # Also try to find input as sibling or child
            try:
                nearby_inputs = label.find_elements(By.XPATH, ".//following-sibling::input | .//input")
                matches.extend(nearby_inputs)
            except:
                pass
        
    except Exception as e:
        logger.debug(f"Error finding field by label: {e}")
    
    return matches


def find_field_by_placeholder(driver: WebDriver, placeholder_text: str) -> List:
    """Find input fields by placeholder text"""
    try:
        return driver.find_elements(By.XPATH, f"//input[contains(@placeholder, '{placeholder_text}')]")
    except:
        return []

