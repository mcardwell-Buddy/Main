"""
Buddy's Arms - Action layer for interacting with websites.
Provides safe, robust interactions based on Buddy's Vision.
"""

from contextlib import contextmanager
from typing import Any, Dict, Optional, Union
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

from Back_End.profile_manager import load_profile


class BuddysArms:
    """Action layer that uses Buddy's Vision to interact with websites safely."""

    def __init__(self, driver, vision_core, timeout=15):
        self.driver = driver
        self.vision_core = vision_core
        self.timeout = timeout
        self.wait = WebDriverWait(driver, timeout)
        self.action_retries = 3

    def navigate(self, url: str) -> None:
        self.driver.get(url)

    def autofill_signup(self, profile: Optional[Dict[str, Any]] = None, submit: bool = False, frame_selector: Optional[Union[str, int]] = None) -> Dict[str, Any]:
        if profile is None:
            profile = load_profile()
        with self._frame_context(frame_selector) as switched:
            if frame_selector is not None and not switched:
                return {"filled": 0, "skipped": 0, "error": "iframe_not_found"}
            return self.vision_core.autofill_signup_form(profile, submit=submit)

    def click_by_text(self, text: str, tag: str = "button", frame_selector: Optional[Union[str, int]] = None) -> bool:
        """Click first visible element containing text."""
        locator = (By.XPATH, f"//{tag}[contains(normalize-space(.), '{text}')]")
        with self._frame_context(frame_selector) as switched:
            if frame_selector is not None and not switched:
                return False
            try:
                el = self.wait.until(EC.element_to_be_clickable(locator))
                return self._click(el)
            except Exception:
                shadow_el = self._find_shadow_element_by_text(text, tag)
                if shadow_el:
                    return self._click(shadow_el)
                return False

    def fill_field(self, field_hint: str, value: str, frame_selector: Optional[Union[str, int]] = None) -> bool:
        """Fill a field by matching label/placeholder/name/id text."""
        with self._frame_context(frame_selector) as switched:
            if frame_selector is not None and not switched:
                return False
            element = self._find_input_by_hint(field_hint)
            if not element:
                return False
            return self._set_value(element, value)

    def set_checkbox(self, field_hint: str, checked: bool = True, frame_selector: Optional[Union[str, int]] = None) -> bool:
        """Set a checkbox by label/name/placeholder/id hint."""
        with self._frame_context(frame_selector) as switched:
            if frame_selector is not None and not switched:
                return False
            element = self._find_input_by_hint(field_hint, input_type="checkbox")
            if not element:
                return False
            return self._set_checked(element, checked)

    def set_toggle(self, field_hint: str, on: bool = True, frame_selector: Optional[Union[str, int]] = None) -> bool:
        """Set a toggle switch (checkbox-like) by hint."""
        with self._frame_context(frame_selector) as switched:
            if frame_selector is not None and not switched:
                return False
            element = self._find_input_by_hint(field_hint, input_type="checkbox")
            if not element:
                element = self._find_toggle_by_hint(field_hint)
            if not element:
                return False
            return self._set_checked(element, on)

    def set_radio(self, field_hint: str, option_text: str, frame_selector: Optional[Union[str, int]] = None) -> bool:
        """Select a radio option by group hint and option text."""
        with self._frame_context(frame_selector) as switched:
            if frame_selector is not None and not switched:
                return False
            option = self._find_radio_option(field_hint, option_text)
            if not option:
                return False
            return self._click(option)

    def select_option(self, field_hint: str, value: str, frame_selector: Optional[Union[str, int]] = None) -> bool:
        """Select an option from a select element by field hint."""
        with self._frame_context(frame_selector) as switched:
            if frame_selector is not None and not switched:
                return False
            element = self._find_select_by_hint(field_hint)
            if not element:
                return False
            return self._select_option(element, value)

    def fill_form(self, data: Dict[str, Any], frame_selector: Optional[Union[str, int]] = None) -> Dict[str, Any]:
        """
        Fill a form using a mapping of field hints to values.
        Booleans will be treated as checkboxes/toggles.
        Dict values with keys: {"select": "..."} or {"radio": "..."}.
        """
        results = {"filled": 0, "skipped": 0}
        with self._frame_context(frame_selector) as switched:
            if frame_selector is not None and not switched:
                return {"filled": 0, "skipped": len(data), "error": "iframe_not_found"}
            for hint, value in data.items():
                ok = False
                if isinstance(value, dict):
                    if "select" in value:
                        ok = self.select_option(hint, str(value["select"]))
                    elif "radio" in value:
                        ok = self.set_radio(hint, str(value["radio"]))
                elif isinstance(value, bool):
                    ok = self.set_checkbox(hint, value)
                else:
                    ok = self.fill_field(hint, str(value))

                if ok:
                    results["filled"] += 1
                else:
                    results["skipped"] += 1
        return results

    def submit_first_form(self, frame_selector: Optional[Union[str, int]] = None) -> bool:
        try:
            with self._frame_context(frame_selector) as switched:
                if frame_selector is not None and not switched:
                    return False
                submit_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
                if submit_buttons:
                    return self._click(submit_buttons[0])
        except Exception:
            return False
        return False

    def _find_input_by_hint(self, hint: str, input_type: Optional[str] = None):
        hint_l = hint.lower()
        selector = "input, textarea" if not input_type else f"input[type='{input_type}']"
        candidates = self.driver.find_elements(By.CSS_SELECTOR, selector)
        for el in candidates:
            try:
                if not el.is_enabled():
                    continue
            except Exception:
                continue
            attrs = " ".join([
                el.get_attribute("name") or "",
                el.get_attribute("id") or "",
                el.get_attribute("placeholder") or "",
                el.get_attribute("aria-label") or "",
                self._label_text(el),
            ]).lower()
            if hint_l in attrs:
                return el

        shadow_el = self._find_shadow_input_by_hint(hint, input_type)
        if shadow_el:
            return shadow_el

        # Fallback: find by associated label text
        if input_type:
            element = self._find_input_by_label_text(hint, input_type)
            if element:
                return element
        return None

    def _find_select_by_hint(self, hint: str):
        hint_l = hint.lower()
        candidates = self.driver.find_elements(By.TAG_NAME, "select")
        for el in candidates:
            attrs = " ".join([
                el.get_attribute("name") or "",
                el.get_attribute("id") or "",
                el.get_attribute("aria-label") or "",
                self._label_text(el),
            ]).lower()
            if hint_l in attrs:
                return el
        shadow_el = self._find_shadow_input_by_hint(hint, "select")
        if shadow_el:
            return shadow_el
        return None

    def _find_toggle_by_hint(self, hint: str):
        """Find toggle-like controls by role or aria attributes."""
        hint_l = hint.lower()
        candidates = self.driver.find_elements(By.CSS_SELECTOR, "[role='switch'], [aria-checked]")
        for el in candidates:
            attrs = " ".join([
                el.get_attribute("name") or "",
                el.get_attribute("id") or "",
                el.get_attribute("aria-label") or "",
                self._label_text(el),
            ]).lower()
            if hint_l in attrs:
                return el
        return None

    def _find_radio_option(self, group_hint: str, option_text: str):
        """Find a radio input by group hint and option label text."""
        try:
            radios = self.driver.find_elements(By.CSS_SELECTOR, "input[type='radio']")
            option_text_l = option_text.lower()
            group_hint_l = group_hint.lower()
            for radio in radios:
                label = self._label_text(radio).lower()
                name = (radio.get_attribute("name") or "").lower()
                if (group_hint_l in name or group_hint_l in label) and option_text_l in label:
                    return radio
        except Exception:
            return None
        return None

    def _set_value(self, element, value: str) -> bool:
        for _ in range(self.action_retries):
            try:
                self.driver.execute_script("arguments[0].focus();", element)
                try:
                    element.clear()
                except Exception:
                    pass
                element.send_keys(value)
                self.driver.execute_script(
                    "arguments[0].dispatchEvent(new Event('input', {bubbles: true}));"
                    "arguments[0].dispatchEvent(new Event('change', {bubbles: true}));",
                    element,
                )
                return True
            except Exception:
                pass
        return False

    def _set_checked(self, element, checked: bool) -> bool:
        try:
            is_checked = element.is_selected()
        except Exception:
            is_checked = False
        if is_checked != checked:
            return self._click(element)
        return True

    def _select_option(self, element, value: str) -> bool:
        try:
            select = Select(element)
            try:
                select.select_by_value(value)
                return True
            except Exception:
                pass
            for opt in element.find_elements(By.TAG_NAME, "option"):
                if value.lower() in (opt.text or "").lower():
                    opt.click()
                    return True
        except Exception:
            return False
        return False

    def _click(self, element) -> bool:
        for _ in range(self.action_retries):
            try:
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            except Exception:
                pass
            try:
                self.wait.until(EC.element_to_be_clickable(element))
            except Exception:
                pass
            try:
                element.click()
                return True
            except Exception:
                try:
                    self.driver.execute_script("arguments[0].click();", element)
                    return True
                except Exception:
                    pass
        return False

    def _label_text(self, element) -> str:
        try:
            return self.driver.execute_script(
                """
                const el = arguments[0];
                if (el.id) {
                    const lbl = document.querySelector(`label[for="${el.id}"]`);
                    if (lbl) return lbl.textContent.trim();
                }
                const parent = el.closest('label');
                if (parent) return parent.textContent.trim();
                return '';
                """,
                element,
            )
        except Exception:
            return ""

    def _find_input_by_label_text(self, label_text: str, input_type: str):
        """Find an input by matching a label's text content."""
        try:
            return self.driver.execute_script(
                """
                const text = arguments[0].toLowerCase();
                const type = arguments[1];
                const labels = Array.from(document.querySelectorAll('label'));
                for (const lbl of labels) {
                    if ((lbl.textContent || '').toLowerCase().includes(text)) {
                        const forId = lbl.getAttribute('for');
                        if (forId) {
                            const el = document.getElementById(forId);
                            if (el && el.type === type) return el;
                        }
                        const input = lbl.querySelector(`input[type="${type}"]`);
                        if (input) return input;
                    }
                }
                return null;
                """,
                label_text,
                input_type,
            )
        except Exception:
            return None

    @contextmanager
    def _frame_context(self, frame_selector: Optional[Union[str, int]] = None):
        """Context manager to switch into an iframe and safely return."""
        switched = False
        if frame_selector is None:
            yield switched
            return
        try:
            frame = self._find_frame(frame_selector)
            if frame is None:
                yield False
                return
            self.driver.switch_to.frame(frame)
            switched = True
            yield switched
        finally:
            if switched:
                try:
                    self.driver.switch_to.default_content()
                except Exception:
                    pass

    def _find_frame(self, frame_selector: Union[str, int]):
        try:
            if isinstance(frame_selector, int):
                frames = self.driver.find_elements(By.TAG_NAME, "iframe")
                return frames[frame_selector] if frame_selector < len(frames) else None
            if isinstance(frame_selector, str) and frame_selector.isdigit():
                idx = int(frame_selector)
                frames = self.driver.find_elements(By.TAG_NAME, "iframe")
                return frames[idx] if idx < len(frames) else None
            if isinstance(frame_selector, str) and frame_selector.startswith("index:"):
                idx = int(frame_selector.split(":", 1)[1])
                frames = self.driver.find_elements(By.TAG_NAME, "iframe")
                return frames[idx] if idx < len(frames) else None
            return self.driver.find_element(By.CSS_SELECTOR, str(frame_selector))
        except Exception:
            return None

    def _find_shadow_input_by_hint(self, hint: str, input_type: Optional[str] = None):
        """Best-effort search for inputs inside open shadow roots."""
        try:
            return self.driver.execute_script(
                """
                const hint = (arguments[0] || '').toLowerCase();
                const inputType = arguments[1];
                const hosts = Array.from(document.querySelectorAll('*')).filter(el => el.shadowRoot);
                for (const host of hosts) {
                    const root = host.shadowRoot;
                    const selector = inputType === 'select' ? 'select' : (inputType ? `input[type="${inputType}"]` : 'input, textarea');
                    const candidates = Array.from(root.querySelectorAll(selector));
                    for (const el of candidates) {
                        const attrs = [
                            el.getAttribute('name') || '',
                            el.getAttribute('id') || '',
                            el.getAttribute('placeholder') || '',
                            el.getAttribute('aria-label') || ''
                        ].join(' ').toLowerCase();
                        if (attrs.includes(hint)) return el;
                    }
                }
                return null;
                """,
                hint,
                input_type,
            )
        except Exception:
            return None

    def _find_shadow_element_by_text(self, text: str, tag: str = "button"):
        """Best-effort search for elements by text inside open shadow roots."""
        try:
            return self.driver.execute_script(
                """
                const text = (arguments[0] || '').toLowerCase();
                const tag = arguments[1];
                const hosts = Array.from(document.querySelectorAll('*')).filter(el => el.shadowRoot);
                for (const host of hosts) {
                    const root = host.shadowRoot;
                    const candidates = Array.from(root.querySelectorAll(tag));
                    for (const el of candidates) {
                        const t = (el.textContent || '').toLowerCase();
                        if (t.includes(text)) return el;
                    }
                }
                return null;
                """,
                text,
                tag,
            )
        except Exception:
            return None

