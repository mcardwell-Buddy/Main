#!/usr/bin/env python3
"""
BUDDY'S VISION CORE - Website Structure Inspector & Mapper
A comprehensive site inspection and learning system that allows Buddy to understand
any website's structure, elements, and interaction patterns.

This is Buddy's vision system - he uses this to "see" and understand websites.
"""

import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select


class BuddysVisionCore:
    """
    Buddy's vision core engine.
    Analyzes website structure, maps interactive elements, and creates a
    knowledge base of how to interact with any website.
    """

    def __init__(self, driver, timeout=10):
        """Initialize Buddy's Vision Core with a Selenium WebDriver instance"""
        self.driver = driver
        self.timeout = timeout
        self.wait = WebDriverWait(driver, timeout)
        self.site_knowledge = {}
        self.knowledge_file = Path("buddy_site_knowledge.json")
        self.load_knowledge()

    def inspect_website(self, url: str, expand_interactive: bool = True, max_scrolls: int = 4) -> Dict[str, Any]:
        """
        Comprehensive website inspection - Buddy's vision.

        Returns a complete map of:
        - Page structure
        - All interactive elements
        - Form fields and their purposes
        - Buttons and their actions
        - Navigation elements
        - Data-driven attributes
        - API endpoints (if exposed)
        - Selectors for key elements

        This is what Buddy "sees" when he looks at a website.
        """

        print(f"\n[VISION] INSPECTING: {url}")
        print("=" * 70)

        try:
            # Navigate to site
            self.driver.get(url)
            self._wait_for_dom_ready()
            self._scroll_page(max_scrolls=max_scrolls)
            if expand_interactive:
                self._reveal_interactive_elements()

            # Start comprehensive inspection
            inspection = {
                "url": url,
                "timestamp": datetime.now().isoformat(),
                "page_title": self.driver.title,
                "page_url": self.driver.current_url,
                # Structure
                "structure": self._inspect_structure(),
                # Interactive Elements
                "forms": self._find_all_forms(),
                "buttons": self._find_all_buttons(),
                "inputs": self._find_all_inputs(),
                "links": self._find_all_links(),
                "selects": self._find_all_selects(),
                "textareas": self._find_all_textareas(),
                # Navigation & Layout
                "navigation": self._find_navigation(),
                "headers": self._find_headers(),
                "footers": self._find_footers(),
                "sidebars": self._find_sidebars(),
                "iframes": self._find_iframes(),
                "iframe_contents": self._inspect_iframe_contents(),
                "shadow_hosts": self._find_shadow_hosts(),
                "shadow_dom": self._inspect_shadow_dom(),
                # Data Attributes
                "data_attributes": self._extract_data_attributes(),
                # API/AJAX Endpoints
                "api_hints": self._find_api_hints(),
                # Security & Auth
                "auth_elements": self._find_auth_elements(),
                "csrf_tokens": self._find_csrf_tokens(),
                # Performance & Analytics
                "tracking": self._find_tracking(),
                "performance": self._get_performance_data(),
                # Key Selectors & Patterns
                "selectors": self._analyze_selector_patterns(),
                # Problems & Warnings
                "issues": self._check_for_issues(),
            }

            # Display what Buddy sees (disabled to avoid console encoding issues)
            # self._display_inspection_report(inspection)

            # Store in knowledge base
            domain = self._extract_domain(url)
            self.site_knowledge[domain] = inspection
            self.save_knowledge()

            return inspection

        except Exception as e:
            print(f"[ERR] Inspection error: {e}")
            import traceback

            traceback.print_exc()
            return {}

    def _inspect_structure(self) -> Dict:
        """Analyze overall page structure"""
        return self.driver.execute_script(
            """
        return {
            doctype: document.doctype ? document.doctype.name : 'unknown',
            html_lang: document.documentElement.lang,

            sections: {
                header: !!document.querySelector('header'),
                main: !!document.querySelector('main'),
                section: document.querySelectorAll('section').length,
                article: document.querySelectorAll('article').length,
                aside: !!document.querySelector('aside'),
                footer: !!document.querySelector('footer'),
                nav: document.querySelectorAll('nav').length
            },

            containers: {
                total_divs: document.querySelectorAll('div').length,
                total_spans: document.querySelectorAll('span').length,
                total_paragraphs: document.querySelectorAll('p').length,
                total_lists: document.querySelectorAll('ul, ol').length
            },

            depth: {
                html_depth: Math.max(...Array.from(document.querySelectorAll('*')).map(el => {
                    let depth = 0, parent = el;
                    while (parent) { depth++; parent = parent.parentElement; }
                    return depth;
                })) || 0
            }
        };
        """
        )

    def _wait_for_dom_ready(self, timeout: int = 10) -> None:
        """Wait until document.readyState is complete or timeout is reached."""
        end_time = time.time() + timeout
        while time.time() < end_time:
            try:
                state = self.driver.execute_script("return document.readyState;")
                if state == "complete":
                    return
            except Exception:
                pass
            time.sleep(0.2)

    def _scroll_page(self, max_scrolls: int = 4) -> None:
        """Scroll down and up to trigger lazy-loaded content."""
        try:
            for _ in range(max_scrolls):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(0.5)
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(0.5)
        except Exception:
            pass

    def _reveal_interactive_elements(self) -> None:
        """Attempt to expand accordions, dropdowns, and collapsed sections."""
        try:
            self.driver.execute_script(
                """
                // Expand <details>
                document.querySelectorAll('details').forEach(d => d.open = true);

                // Click elements that control collapsible regions
                const toggles = Array.from(document.querySelectorAll('[aria-expanded="false"], [data-toggle], [data-target], [data-accordion]'));
                toggles.forEach(el => {
                    try {
                        if (el.getAttribute('aria-expanded') === 'false') {
                            el.click();
                        }
                    } catch (e) {}
                });

                // Expand common accordion patterns
                document.querySelectorAll('[role="button"]').forEach(el => {
                    const text = (el.textContent || '').toLowerCase();
                    if (text.includes('expand') || text.includes('more') || text.includes('show')) {
                        try { el.click(); } catch (e) {}
                    }
                });

                // Open custom dropdowns
                document.querySelectorAll('[role="combobox"], [aria-haspopup="listbox"]').forEach(el => {
                    try { el.click(); } catch (e) {}
                });
                """
            )
            time.sleep(0.5)
        except Exception:
            pass

    def _find_iframes(self) -> List[Dict]:
        """Collect iframe metadata for visibility and potential inspection."""
        try:
            return self.driver.execute_script(
                """
                return Array.from(document.querySelectorAll('iframe')).map((f, i) => ({
                    index: i,
                    id: f.id || '',
                    name: f.name || '',
                    src: f.src || '',
                    title: f.title || '',
                    visible: f.offsetHeight > 0
                }));
                """
            )
        except Exception:
            return []

    def _find_shadow_hosts(self) -> List[Dict]:
        """Detect open shadow DOM hosts (closed roots cannot be inspected)."""
        try:
            return self.driver.execute_script(
                """
                return Array.from(document.querySelectorAll('*')).filter(el => el.shadowRoot).map((el, i) => ({
                    index: i,
                    tag: el.tagName.toLowerCase(),
                    id: el.id || '',
                    class: el.className || ''
                }));
                """
            )
        except Exception:
            return []

    def _inspect_iframe_contents(self, max_iframes: int = 3) -> List[Dict]:
        """Attempt to inspect visible iframe contents with safe switching."""
        results = []
        try:
            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            for i, frame in enumerate(iframes[:max_iframes]):
                info = {
                    "index": i,
                    "id": frame.get_attribute("id") or "",
                    "name": frame.get_attribute("name") or "",
                    "src": frame.get_attribute("src") or "",
                    "title": frame.get_attribute("title") or "",
                    "visible": frame.size.get("height", 0) > 0,
                    "error": None,
                }
                try:
                    self.driver.switch_to.frame(frame)
                    self._wait_for_dom_ready()
                    info.update({
                        "forms": len(self.driver.find_elements(By.TAG_NAME, "form")),
                        "buttons": len(self.driver.find_elements(By.CSS_SELECTOR, "button, [role='button']")),
                        "inputs": len(self.driver.find_elements(By.CSS_SELECTOR, "input, textarea, select")),
                    })
                except Exception as e:
                    info["error"] = str(e)
                finally:
                    try:
                        self.driver.switch_to.default_content()
                    except Exception:
                        pass
                results.append(info)
        except Exception:
            return []
        return results

    def _inspect_shadow_dom(self, max_hosts: int = 10) -> List[Dict]:
        """Inspect open shadow DOM roots (limited, best-effort)."""
        try:
            return self.driver.execute_script(
                """
                const hosts = Array.from(document.querySelectorAll('*')).filter(el => el.shadowRoot).slice(0, arguments[0]);
                return hosts.map((el, i) => {
                    const root = el.shadowRoot;
                    return {
                        index: i,
                        tag: el.tagName.toLowerCase(),
                        id: el.id || '',
                        class: el.className || '',
                        counts: {
                            buttons: root.querySelectorAll('button, [role="button"]').length,
                            inputs: root.querySelectorAll('input, textarea, select').length,
                            links: root.querySelectorAll('a').length
                        }
                    };
                });
                """,
                max_hosts,
            )
        except Exception:
            return []

    def _find_all_forms(self) -> List[Dict]:
        """Find and map all forms"""
        forms = []
        form_elements = self.driver.find_elements(By.TAG_NAME, "form")

        for i, form in enumerate(form_elements):
            form_data = self.driver.execute_script(
                f"""
            const form = arguments[0];
            return {{
                index: {i},
                id: form.id,
                name: form.name,
                method: form.method,
                action: form.action,
                class: form.className,
                fields_count: form.querySelectorAll('input, textarea, select').length,
                fields: Array.from(form.querySelectorAll('input, textarea, select')).map(field => ({
                    type: field.type,
                    name: field.name,
                    id: field.id,
                    placeholder: field.placeholder,
                    required: field.required,
                    value: field.value
                }))
            }};
            """,
                form,
            )
            forms.append(form_data)

        return forms

    def _find_all_buttons(self) -> List[Dict]:
        """Find and map all buttons"""
        buttons = []
        button_elements = self.driver.find_elements(By.TAG_NAME, "button")

        for i, btn in enumerate(button_elements[:30]):  # Limit to first 30
            btn_data = self.driver.execute_script(
                f"""
            const btn = arguments[0];
            return {{
                index: {i},
                text: btn.textContent.substring(0, 50),
                type: btn.type,
                id: btn.id,
                name: btn.name,
                class: btn.className,
                aria_label: btn.getAttribute('aria-label'),
                disabled: btn.disabled,
                visible: btn.offsetHeight > 0,
                data_attrs: Object.fromEntries(
                    Array.from(btn.attributes)
                        .filter(attr => attr.name.startsWith('data-'))
                        .map(attr => [attr.name, attr.value])
                )
            }};
            """,
                btn,
            )
            buttons.append(btn_data)

        return buttons

    def _find_all_inputs(self) -> List[Dict]:
        """Find and map all input fields"""
        inputs = []
        input_elements = self.driver.find_elements(By.TAG_NAME, "input")

        for i, inp in enumerate(input_elements):
            inp_data = self.driver.execute_script(
                f"""
            const inp = arguments[0];
            return {{
                index: {i},
                type: inp.type,
                name: inp.name,
                id: inp.id,
                placeholder: inp.placeholder,
                value: inp.value,
                class: inp.className,
                required: inp.required,
                disabled: inp.disabled,
                visible: inp.offsetHeight > 0,
                aria_label: inp.getAttribute('aria-label'),
                data_attrs: Object.fromEntries(
                    Array.from(inp.attributes)
                        .filter(attr => attr.name.startsWith('data-'))
                        .map(attr => [attr.name, attr.value])
                )
            }};
            """,
                inp,
            )
            inputs.append(inp_data)

        return inputs

    def _find_all_links(self) -> List[Dict]:
        """Find and map all links"""
        links = []
        link_elements = self.driver.find_elements(By.TAG_NAME, "a")

        for i, link in enumerate(link_elements[:50]):  # Limit to first 50
            link_data = self.driver.execute_script(
                f"""
            const link = arguments[0];
            return {{
                index: {i},
                text: link.textContent.substring(0, 50),
                href: link.href,
                id: link.id,
                class: link.className,
                aria_label: link.getAttribute('aria-label'),
                target: link.target
            }};
            """,
                link,
            )
            links.append(link_data)

        return links

    def _find_all_selects(self) -> List[Dict]:
        """Find and map all select dropdowns"""
        selects = []
        select_elements = self.driver.find_elements(By.TAG_NAME, "select")

        for i, select in enumerate(select_elements):
            select_data = self.driver.execute_script(
                f"""
            const select = arguments[0];
            return {{
                index: {i},
                name: select.name,
                id: select.id,
                class: select.className,
                options_count: select.options.length,
                options: Array.from(select.options).slice(0, 10).map(opt => ({{
                    value: opt.value,
                    text: opt.text
                }}))
            }};
            """,
                select,
            )
            selects.append(select_data)

        return selects

    def _find_all_textareas(self) -> List[Dict]:
        """Find and map all textareas"""
        textareas = []
        textarea_elements = self.driver.find_elements(By.TAG_NAME, "textarea")

        for i, ta in enumerate(textarea_elements):
            ta_data = self.driver.execute_script(
                f"""
            const ta = arguments[0];
            return {{
                index: {i},
                name: ta.name,
                id: ta.id,
                placeholder: ta.placeholder,
                class: ta.className,
                rows: ta.rows,
                cols: ta.cols
            }};
            """,
                ta,
            )
            textareas.append(ta_data)

        return textareas

    def _find_navigation(self) -> Dict:
        """Find navigation elements"""
        return self.driver.execute_script(
            """
        return {
            navbars: document.querySelectorAll('nav').length,
            nav_items: Array.from(document.querySelectorAll('nav a')).map(a => ({
                text: a.textContent.substring(0, 30),
                href: a.href
            })),
            breadcrumbs: !!document.querySelector('[aria-label="breadcrumb"]'),
            menus: document.querySelectorAll('[role="menubar"], [role="menu"]').length
        };
        """
        )

    def _find_headers(self) -> Dict:
        """Find header information"""
        return self.driver.execute_script(
            """
        return {
            h1: Array.from(document.querySelectorAll('h1')).map(h => h.textContent.substring(0, 50)),
            h2: document.querySelectorAll('h2').length,
            h3: document.querySelectorAll('h3').length,
            h4: document.querySelectorAll('h4').length,
            h5: document.querySelectorAll('h5').length,
            h6: document.querySelectorAll('h6').length
        };
        """
        )

    def _find_footers(self) -> Dict:
        """Find footer information"""
        return self.driver.execute_script(
            """
        return {
            has_footer: !!document.querySelector('footer'),
            footer_text: document.querySelector('footer')?.textContent.substring(0, 100) || 'No footer'
        };
        """
        )

    def _find_sidebars(self) -> Dict:
        """Find sidebar information"""
        return self.driver.execute_script(
            """
        return {
            has_aside: !!document.querySelector('aside'),
            sidebars: document.querySelectorAll('[class*="sidebar"], [class*="aside"]').length
        };
        """
        )

    def _extract_data_attributes(self) -> Dict:
        """Extract all data-* attributes (key for understanding dynamic behavior)"""
        return self.driver.execute_script(
            """
        const dataAttrs = {};
        document.querySelectorAll('[data-test], [data-id], [data-name], [data-action], [data-target], [data-toggle], [data-value], [data-type], [data-endpoint], [data-api]').forEach(el => {
            Array.from(el.attributes).forEach(attr => {
                if (attr.name.startsWith('data-')) {
                    if (!dataAttrs[attr.name]) {
                        dataAttrs[attr.name] = [];
                    }
                    dataAttrs[attr.name].push(attr.value);
                }
            });
        });
        // Also scan all elements for data attributes
        document.querySelectorAll('*').forEach(el => {
            Array.from(el.attributes).forEach(attr => {
                if (attr.name.startsWith('data-')) {
                    if (!dataAttrs[attr.name]) {
                        dataAttrs[attr.name] = [];
                    }
                    if (!dataAttrs[attr.name].includes(attr.value)) {
                        dataAttrs[attr.name].push(attr.value);
                    }
                }
            });
        });
        return dataAttrs;
        """
        )

    def _find_api_hints(self) -> Dict:
        """Find hints about API endpoints"""
        return self.driver.execute_script(
            """
        const hints = {
            script_tags: [],
            fetch_patterns: [],
            api_endpoints: []
        };

        // Check script tags for API hints
        Array.from(document.querySelectorAll('script')).forEach(script => {
            if (script.textContent.includes('api') || script.textContent.includes('fetch')) {
                const matches = script.textContent.match(/https?:\/\/[^\s"'<>]+/g) || [];
                hints.api_endpoints.push(...matches);
            }
        });

        return hints;
        """
        )

    def _find_auth_elements(self) -> Dict:
        """Find authentication-related elements"""
        return self.driver.execute_script(
            """
        return {
            has_login: !!document.querySelector('[class*="login"], [class*="sign-in"]'),
            has_logout: !!document.querySelector('[class*="logout"], [class*="sign-out"]'),
            has_register: !!document.querySelector('[class*="register"], [class*="signup"]'),
            auth_forms: document.querySelectorAll('[class*="auth"], [class*="login"]').length
        };
        """
        )

    def _find_csrf_tokens(self) -> Dict:
        """Find CSRF and security tokens"""
        return self.driver.execute_script(
            """
        return {
            csrf_tokens: Array.from(document.querySelectorAll('input[name*="csrf"], input[name*="token"], input[name*="authenticity"]')).map(inp => ({
                name: inp.name,
                type: inp.type
            })),
            meta_tokens: Array.from(document.querySelectorAll('meta[name*="csrf"], meta[name*="token"]')).map(meta => ({
                name: meta.name,
                content: meta.content.substring(0, 20) + '...'
            }))
        };
        """
        )

    def _find_tracking(self) -> Dict:
        """Find tracking and analytics elements"""
        return self.driver.execute_script(
            """
        return {
            google_analytics: !!window.ga || !!window.gtag,
            facebook_pixel: !!window.fbq,
            scripts_with_tracking: Array.from(document.querySelectorAll('script')).filter(s =>
                s.src && (s.src.includes('google') || s.src.includes('analytics') ||
                         s.src.includes('facebook') || s.src.includes('mixpanel'))
            ).map(s => s.src)
        };
        """
        )

    def _get_performance_data(self) -> Dict:
        """Get page performance metrics"""
        return self.driver.execute_script(
            """
        const perf = performance.timing;
        const loadTime = perf.loadEventEnd - perf.navigationStart;

        return {
            load_time_ms: loadTime,
            dom_ready_ms: perf.domContentLoadedEventEnd - perf.navigationStart,
            resource_count: performance.getEntriesByType('resource').length
        };
        """
        )

    def _analyze_selector_patterns(self) -> Dict:
        """Analyze common selector patterns used on the site"""
        return self.driver.execute_script(
            """
        const patterns = {
            id_patterns: [],
            class_patterns: [],
            data_attr_patterns: []
        };

        // Analyze ID patterns
        document.querySelectorAll('[id]').forEach(el => {
            patterns.id_patterns.push(el.id);
        });

        // Analyze class patterns
        document.querySelectorAll('[class]').forEach(el => {
            const classes = el.className.split(' ');
            patterns.class_patterns.push(...classes.filter(c => c.length > 0));
        });

        return {
            common_ids: [...new Set(patterns.id_patterns)].slice(0, 20),
            common_classes: [...new Set(patterns.class_patterns)].slice(0, 20),
            unique_ids: patterns.id_patterns.length,
            unique_classes: new Set(patterns.class_patterns).size
        };
        """
        )

    def _check_for_issues(self) -> List[str]:
        """Check for common issues Buddy should be aware of"""
        issues = []

        # Check basic issues
        checks = self.driver.execute_script(
            """
        return {
            missing_titles: document.querySelectorAll('input, button').length > 0 &&
                           !Array.from(document.querySelectorAll('input, button')).every(el => el.title || el.aria_label),
            multiple_forms: document.querySelectorAll('form').length > 1,
            no_lang_attr: !document.documentElement.lang
        };
        """
        )

        if checks.get("missing_titles"):
            issues.append("Some interactive elements missing titles/labels")
        if checks.get("multiple_forms"):
            issues.append("Multiple forms present - ensure targeting correct form")
        if checks.get("no_lang_attr"):
            issues.append("HTML missing lang attribute")

        return issues

    def _display_inspection_report(self, inspection: Dict) -> None:
        """Display a formatted inspection report"""
        print(f"\n[REPORT] INSPECTION REPORT FOR: {inspection['page_title']}")
        print("=" * 70)

        print(f"\n[URL] {inspection['page_url']}")

        print(f"\n[STRUCTURE]")
        struct = inspection["structure"].get("sections", {})
        print(f"   Headers: {struct.get('header')}, Footers: {struct.get('footer')}")
        print(f"   Navigation sections: {struct.get('nav')}")
        print(f"   Total divs: {inspection['structure'].get('containers', {}).get('total_divs')}")

        print(f"\n[INTERACTIVE ELEMENTS]")
        print(f"   Forms: {len(inspection['forms'])}")
        print(f"   Buttons: {len(inspection['buttons'])}")
        print(f"   Inputs: {len(inspection['inputs'])}")
        print(f"   Links: {len(inspection['links'])}")
        print(f"   Selects: {len(inspection['selects'])}")
        print(f"   Textareas: {len(inspection['textareas'])}")

        print(f"\n[NAVIGATION]")
        nav = inspection["navigation"]
        print(f"   Navigation sections: {nav.get('nav_items', [])[:3]}")

        print(f"\n[DATA ATTRIBUTES] {len(inspection['data_attributes'])} unique data-* attributes")

        print(f"\n[ISSUES] {len(inspection['issues'])} detected")
        for issue in inspection["issues"][:3]:
            print(f"   • {issue}")

        print(f"\n[OK] Inspection complete - knowledge saved")

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        from urllib.parse import urlparse

        return urlparse(url).netloc

    def load_knowledge(self) -> None:
        """Load previously learned site knowledge"""
        if self.knowledge_file.exists():
            try:
                with open(self.knowledge_file) as f:
                    self.site_knowledge = json.load(f)
                print(f"[OK] Loaded knowledge of {len(self.site_knowledge)} websites")
            except Exception:
                pass

    def save_knowledge(self) -> None:
        """Save learned site knowledge"""
        try:
            with open(self.knowledge_file, "w") as f:
                json.dump(self.site_knowledge, f, indent=2, default=str)
        except Exception as e:
            print(f"[WARN] Could not save knowledge: {e}")

    def get_knowledge_about_site(self, url: str) -> Dict:
        """Retrieve learned knowledge about a site"""
        domain = self._extract_domain(url)
        return self.site_knowledge.get(domain, {})

    def find_element_for_action(self, action: str, context: str = None) -> Optional[str]:
        """
        Buddy asks: "Where do I find the element to [action]?"
        Uses learned knowledge to locate elements intelligently.

        Examples:
        - find_element_for_action("login") -> selector for login button
        - find_element_for_action("search") -> selector for search input
        - find_element_for_action("submit") -> selector for submit button
        """

        current_domain = self._extract_domain(self.driver.current_url)
        knowledge = self.site_knowledge.get(current_domain, {})

        action_lower = action.lower()

        # Search through buttons
        for btn in knowledge.get("buttons", []):
            if action_lower in btn.get("text", "").lower():
                return f"button text containing '{action}'"

        # Search through inputs
        for inp in knowledge.get("inputs", []):
            if action_lower in inp.get("placeholder", "").lower() or action_lower in inp.get(
                "name", ""
            ).lower():
                return f"input #{inp.get('id') or inp.get('name')}"

        # Search through forms
        for form in knowledge.get("forms", []):
            if action_lower in str(form).lower():
                return f"form #{form.get('id') or form.get('action')}"

        return None

    def autofill_signup_form(self, profile: Dict[str, Any], submit: bool = False) -> Dict[str, Any]:
        """
        Attempt to auto-fill a signup form using the provided profile data.
        Returns a summary of fields filled. Does not submit unless submit=True.
        """
        if not profile:
            return {"filled": 0, "skipped": 0, "submitted": False, "error": "Profile is empty"}

        value_map = self._build_profile_value_map(profile)
        filled_fields = []
        skipped = 0

        elements = self.driver.find_elements(By.CSS_SELECTOR, "input, textarea, select")
        for el in elements:
            try:
                if not el.is_enabled():
                    skipped += 1
                    continue
            except Exception:
                skipped += 1
                continue

            tag = el.tag_name.lower()
            el_type = (el.get_attribute("type") or "").lower()
            name = el.get_attribute("name") or ""
            el_id = el.get_attribute("id") or ""
            placeholder = el.get_attribute("placeholder") or ""
            aria_label = el.get_attribute("aria-label") or ""

            label_text = self._get_label_text(el)
            combined = " ".join([name, el_id, placeholder, aria_label, label_text]).lower().strip()

            value = self._match_value_for_field(combined, el_type, value_map)
            if not value:
                continue

            if tag == "select":
                if self._select_option(el, value):
                    filled_fields.append(self._field_id(el))
                else:
                    skipped += 1
                continue

            if el_type in ("hidden", "submit", "button", "file"):
                skipped += 1
                continue

            if el_type == "password" and not value:
                skipped += 1
                continue

            if self._set_input_value(el, value):
                filled_fields.append(self._field_id(el))
            else:
                skipped += 1

        submitted = False
        if submit:
            submitted = self._submit_first_form()

        return {
            "filled": len(filled_fields),
            "skipped": skipped,
            "submitted": submitted,
            "fields": filled_fields[:20],
        }

    def _build_profile_value_map(self, profile: Dict[str, Any]) -> Dict[str, str]:
        full_name = profile.get("full_name", "").strip()
        first_name = profile.get("first_name", "").strip()
        last_name = profile.get("last_name", "").strip()
        if full_name and (not first_name or not last_name):
            parts = full_name.split()
            if parts:
                first_name = first_name or parts[0]
                if len(parts) > 1:
                    last_name = last_name or parts[-1]

        email = profile.get("email", "").strip()
        phones = profile.get("phones", {}) or {}
        phone_mobile = (phones.get("mobile") or "").strip()
        phone_office = (phones.get("office") or "").strip()

        addresses = profile.get("addresses", []) or []
        primary = addresses[0] if addresses else {}
        addr_line1 = (primary.get("street") or "").strip()
        city = (primary.get("city") or "").strip()
        state = (primary.get("state") or "").strip()
        postal = (primary.get("postal_code") or "").strip()

        return {
            "full_name": full_name,
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "phone_mobile": phone_mobile,
            "phone_office": phone_office,
            "address_line1": addr_line1,
            "city": city,
            "state": state,
            "postal_code": postal,
            "company": (profile.get("company") or "").strip(),
            "website": (profile.get("website") or "").strip(),
            "password": (profile.get("password") or profile.get("account_password") or "").strip(),
        }

    def _match_value_for_field(self, combined: str, el_type: str, value_map: Dict[str, str]) -> str:
        text = combined

        if el_type == "email" and value_map.get("email"):
            return value_map["email"]
        if el_type == "tel":
            return value_map.get("phone_mobile") or value_map.get("phone_office")

        if "email" in text:
            return value_map.get("email")
        if "first name" in text or "firstname" in text:
            return value_map.get("first_name")
        if "last name" in text or "lastname" in text or "surname" in text:
            return value_map.get("last_name")
        if "full name" in text or ("name" in text and "company" not in text and "business" not in text):
            return value_map.get("full_name")
        if "phone" in text or "mobile" in text or "cell" in text:
            if "office" in text or "work" in text:
                return value_map.get("phone_office")
            return value_map.get("phone_mobile") or value_map.get("phone_office")
        if "address" in text or "street" in text:
            return value_map.get("address_line1")
        if "city" in text:
            return value_map.get("city")
        if "state" in text or "province" in text:
            return value_map.get("state")
        if "zip" in text or "postal" in text:
            return value_map.get("postal_code")
        if "company" in text or "organization" in text or "business" in text:
            return value_map.get("company")
        if "website" in text or "url" in text:
            return value_map.get("website")
        if "password" in text:
            return value_map.get("password")

        return ""

    def _get_label_text(self, element) -> str:
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

    def _set_input_value(self, element, value: str) -> bool:
        try:
            self.driver.execute_script("arguments[0].focus();", element)
            try:
                element.clear()
            except Exception:
                pass
            element.send_keys(value)
            self.driver.execute_script(
                "arguments[0].dispatchEvent(new Event('input', {bubbles: true}));"  # noqa: E501
                "arguments[0].dispatchEvent(new Event('change', {bubbles: true}));",
                element,
            )
            return True
        except Exception:
            return False

    def _select_option(self, element, value: str) -> bool:
        try:
            select = Select(element)
            # Try exact value
            try:
                select.select_by_value(value)
                return True
            except Exception:
                pass
            # Try visible text contains
            for opt in element.find_elements(By.TAG_NAME, "option"):
                if value.lower() in (opt.text or "").lower():
                    opt.click()
                    return True
        except Exception:
            return False
        return False

    def _submit_first_form(self) -> bool:
        try:
            submit_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
            if submit_buttons:
                submit_buttons[0].click()
                return True
        except Exception:
            return False
        return False

    def _field_id(self, element) -> str:
        return element.get_attribute("name") or element.get_attribute("id") or element.tag_name
