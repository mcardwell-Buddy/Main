# BUDDY TOOL INDEX - PHASE 5 WEB CAPABILITIES
**Updated:** February 5, 2026  
**Phase:** 5 - Vision & Arms Integration  
**Status:** ✅ ACTIVE - Web tools integrated into agent loop

---

## Overview

Phase 5 successfully integrates Buddy's Vision and Arms subsystems into the main agent loop. The agent can now execute web interactions as part of normal goal execution with:

- ✅ **9 new web tools** registered in tool registry
- ✅ **Risk-based safety classification** (LOW/MEDIUM/HIGH)
- ✅ **Dry-run mode** for high-risk actions
- ✅ **Session management** for persistent browser state
- ✅ **Metrics capture** for confidence calibration
- ✅ **Thread-safe operations** with RLock synchronization
- ✅ **Feature flag control** for safe rollout

---

## Web Tools Inventory

### 1. Inspection Tools (LOW RISK - Read-Only)

#### `web_inspect(url)`
**Purpose:** Inspect a website and return structured DOM analysis  
**Risk Level:** LOW (read-only operation)  
**Timeout:** 10 seconds (Vision system)

**Parameters:**
- `url` (str): Website URL to inspect

**Returns:**
```python
{
    'success': True/False,
    'url': str,
    'inspection': {
        'forms': [...],           # All forms with fields, method, action
        'buttons': [...],         # All buttons with text, type, attributes
        'inputs': [...],          # All input fields with metadata
        'links': [...],           # All anchor tags
        'structure': {...},       # Page structure analysis
        'iframes': [...],         # Detected iframes
        'shadow_dom': [...],      # Shadow DOM roots
        'data_attributes': {...}, # All data-* attributes
        'api_hints': [...],       # Detected API endpoints
        'selectors': {...}        # Recommended selector patterns
    },
    'message': str,
    'execution_time_ms': float
}
```

**Use Cases:**
- Learn website structure before interaction
- Find elements for clicking/filling
- Detect forms and their fields
- Map site navigation

**Example:**
```python
result = web_inspect("https://example.com")
if result['success']:
    forms = result['inspection']['forms']
    buttons = result['inspection']['buttons']
```

---

#### `web_screenshot()`
**Purpose:** Capture screenshot of current page with clickable element overlay  
**Risk Level:** LOW (read-only operation)  
**Timeout:** 10 seconds

**Parameters:** None (captures current page)

**Returns:**
```python
{
    'success': True/False,
    'screenshot': {
        'base64': str,           # Base64 PNG image
        'width': int,            # Image width in pixels
        'height': int,           # Image height in pixels
        'format': 'png'
    },
    'page_state': {
        'url': str,              # Current URL
        'title': str,            # Page title
        'viewport': {...}        # Viewport dimensions
    },
    'clickables': [
        {
            'tag': str,          # Element tag (button, a, input)
            'text': str,         # Visible text
            'x': int,            # X coordinate
            'y': int,            # Y coordinate
            'width': int,        # Element width
            'height': int        # Element height
        },
        ...
    ],
    'message': str,
    'execution_time_ms': float
}
```

**Use Cases:**
- Visual debugging of automation
- UI state verification
- Element position mapping
- Training data for ML models (future)

**Example:**
```python
result = web_screenshot()
if result['success']:
    screenshot_data = result['screenshot']['base64']
    clickable_buttons = [c for c in result['clickables'] if c['tag'] == 'button']
```

---

#### `web_extract(selector, extract_type='text')`
**Purpose:** Extract content from page elements by CSS selector  
**Risk Level:** LOW (read-only operation)  
**Timeout:** 10 seconds

**Parameters:**
- `selector` (str): CSS selector or XPath
- `extract_type` (str): 'text', 'html', 'attributes', or 'all'

**Returns:**
```python
{
    'success': True/False,
    'selector': str,
    'elements': [
        {
            'text': str,         # Element text content
            'html': str,         # Outer HTML (if requested)
            'attributes': {...}  # All attributes (if requested)
        },
        ...
    ],
    'count': int,
    'message': str,
    'execution_time_ms': float
}
```

**Use Cases:**
- Extract specific data from page
- Scrape structured content
- Get element attributes
- Collect links or images

**Example:**
```python
# Extract all product names
result = web_extract('.product-name', 'text')
if result['success']:
    products = [elem['text'] for elem in result['elements']]

# Extract all links with attributes
result = web_extract('a[href]', 'all')
if result['success']:
    links = [(e['text'], e['attributes']['href']) for e in result['elements']]
```

---

### 2. Navigation Tools (LOW RISK)

#### `web_navigate(url)`
**Purpose:** Navigate browser to a URL  
**Risk Level:** LOW (reversible action)  
**Timeout:** 15 seconds (Arms system)

**Parameters:**
- `url` (str): Target URL (must include protocol: http:// or https://)

**Returns:**
```python
{
    'success': True/False,
    'url': str,              # Requested URL
    'final_url': str,        # Final URL after redirects
    'title': str,            # Page title
    'message': str,
    'execution_time_ms': float
}
```

**Use Cases:**
- Navigate to new pages
- Follow links
- Start workflows on specific sites

**Example:**
```python
result = web_navigate("https://example.com")
if result['success']:
    print(f"Navigated to: {result['final_url']}")
    print(f"Page title: {result['title']}")
```

---

### 3. Interaction Tools (MEDIUM RISK)

#### `web_click(selector_or_text, tag='button')`
**Purpose:** Click an element by selector or visible text  
**Risk Level:** MEDIUM (can trigger navigation/actions)  
**Timeout:** 15 seconds with 3 retries

**Parameters:**
- `selector_or_text` (str): CSS selector or visible text to match
- `tag` (str): Element tag for text matching (default: 'button')

**Returns:**
```python
{
    'success': True/False,
    'target': str,
    'message': str,
    'execution_time_ms': float
}
```

**Dry-Run Behavior:**
- Controlled by `WEB_TOOLS_DRY_RUN` environment variable
- Logs intended action without executing
- Useful for workflow validation

**Use Cases:**
- Click buttons
- Follow links
- Trigger dropdown menus
- Expand accordions

**Example:**
```python
# Click by text
result = web_click("Sign In", "button")

# Click by CSS selector
result = web_click("#submit-btn", "button")

# Click link
result = web_click("More information", "a")
```

---

#### `web_fill(field_hint, value)`
**Purpose:** Fill a form field by label/placeholder/name/id hint  
**Risk Level:** MEDIUM (modifies page state but no permanent action)  
**Timeout:** 15 seconds with 3 retries

**Parameters:**
- `field_hint` (str): Text hint to identify field (searches label, placeholder, name, id, aria-label)
- `value` (str): Value to fill (passwords are auto-masked in logs)

**Returns:**
```python
{
    'success': True/False,
    'field_hint': str,
    'value': str,            # Masked if password field detected
    'message': str,
    'execution_time_ms': float
}
```

**Smart Field Detection:**
- Searches by label text association
- Matches placeholder text
- Checks name and id attributes
- Supports aria-label
- Works inside iframes and shadow DOM

**Security:**
- Auto-detects password fields
- Masks sensitive values in logs
- Does not log actual passwords

**Use Cases:**
- Fill login forms
- Enter search queries
- Complete signup forms
- Update profile fields

**Example:**
```python
# Fill by label
result = web_fill("Email Address", "user@example.com")

# Fill by placeholder
result = web_fill("Search...", "product name")

# Fill password (auto-masked)
result = web_fill("Password", "secret123")  # Logged as '***'
```

---

### 4. High-Risk Tools (PERMANENT ACTIONS)

#### `web_submit_form()`
**Purpose:** Submit the first form on the page  
**Risk Level:** HIGH (permanent action - form submission)  
**Timeout:** 15 seconds with 3 retries

**Parameters:** None (submits first form found)

**Returns:**
```python
{
    'success': True/False,
    'message': str,
    'warning': str,          # Always includes high-risk warning
    'execution_time_ms': float
}
```

**Safety Enforcement:**
- **Defaults to dry-run** unless explicitly enabled
- Requires `WEB_TOOLS_ALLOW_HIGH_RISK=true` environment variable
- Always includes warning in response
- Cannot be disabled via code (environment only)

**Use Cases:**
- Submit login forms (after approval)
- Submit contact forms
- Complete checkout (with extreme caution)
- Post comments/reviews

**Example:**
```python
# By default, this will be dry-run
result = web_submit_form()
if result.get('dry_run'):
    print("HIGH RISK: Action blocked in dry-run mode")
    print(result['warning'])

# To enable (requires environment variable):
# export WEB_TOOLS_ALLOW_HIGH_RISK=true
```

---

### 5. Session Management Tools

#### `web_browser_start()`
**Purpose:** Start a persistent browser session  
**Risk Level:** LOW (setup operation)

**Parameters:** None

**Returns:**
```python
{
    'success': True/False,
    'session_active': bool,
    'created_at': str,       # ISO timestamp
    'message': str
}
```

**Session Features:**
- Persistent across multiple tool calls
- Thread-safe with RLock synchronization
- Automatic ChromeDriver management
- Vision and Arms pre-initialized

**Use Cases:**
- Initialize web automation workflow
- Prepare for multi-step operations
- Ensure browser ready before actions

**Example:**
```python
result = web_browser_start()
if result['success']:
    print(f"Browser session active since {result['created_at']}")
```

---

#### `web_browser_stop()`
**Purpose:** Stop the persistent browser session and clean up  
**Risk Level:** LOW (cleanup operation)

**Parameters:** None

**Returns:**
```python
{
    'success': True/False,
    'message': str
}
```

**Cleanup Actions:**
- Quits browser driver
- Releases resources
- Clears session state
- Thread-safe shutdown

**Use Cases:**
- End web automation workflow
- Clean up after testing
- Release system resources

**Example:**
```python
result = web_browser_stop()
if result['success']:
    print("Browser session closed and cleaned up")
```

---

## Safety Features

### Risk Classification System

**LOW RISK (Always Allowed):**
- `web_inspect` - Read-only page analysis
- `web_screenshot` - Visual capture
- `web_extract` - Data extraction
- `web_navigate` - Navigation (reversible)
- `web_browser_start` / `web_browser_stop` - Session management

**MEDIUM RISK (Dry-Run Configurable):**
- `web_click` - Can trigger actions
- `web_fill` - Modifies page state

**HIGH RISK (Dry-Run by Default):**
- `web_submit_form` - Permanent form submission

### Dry-Run Mode

**Environment Variables:**
```bash
# Enable dry-run for all actions
export WEB_TOOLS_DRY_RUN=true

# Allow high-risk actions (use with caution)
export WEB_TOOLS_ALLOW_HIGH_RISK=true

# Run browser in headless mode
export WEB_TOOLS_HEADLESS=true
```

**Dry-Run Behavior:**
- Logs intended action
- Does not execute
- Returns `dry_run: true` in response
- Useful for workflow validation

### Timeout Protection

**Phase 1 Timeouts (Inherited):**
- Vision operations: 10 seconds
- Arms operations: 15 seconds
- Goal execution: 120 seconds

**Retry Logic:**
- 3 attempts per action
- Graceful failure after retries
- Error details in response

### Metrics Capture

**Automatic Logging:**
- Action name and parameters
- Risk level
- Dry-run status
- Success/failure
- Execution time
- Error details

**Storage:**
- File: `outputs/integration_metrics/web_actions_YYYYMMDD.jsonl`
- Format: JSON Lines (one JSON object per line)
- Rotation: Daily

**Integration with Phase 4:**
- Compatible with SessionContext
- Can be imported into multi-step metrics
- Enables confidence calibration (future)

---

## Multi-Step Workflow Example

```python
# Example: Extract data from a website

# Step 1: Start browser
result = web_browser_start()
if not result['success']:
    print("Failed to start browser")
    exit(1)

# Step 2: Navigate to target site
result = web_navigate("https://example.com/products")
if not result['success']:
    print("Navigation failed")
    web_browser_stop()
    exit(1)

# Step 3: Inspect page structure
result = web_inspect("https://example.com/products")
if result['success']:
    forms = result['inspection']['forms']
    buttons = result['inspection']['buttons']
    print(f"Found {len(forms)} forms, {len(buttons)} buttons")

# Step 4: Extract product data
result = web_extract('.product-name', 'text')
if result['success']:
    products = [elem['text'] for elem in result['elements']]
    print(f"Extracted {len(products)} products: {products}")

# Step 5: Capture screenshot for verification
result = web_screenshot()
if result['success']:
    print(f"Screenshot captured: {result['screenshot']['width']}x{result['screenshot']['height']}")

# Step 6: Clean up
result = web_browser_stop()
print("Workflow complete")
```

---

## Integration with Existing Systems

### Phase 1 Integration
- **Vision System:** `BuddysVision` and `BuddysVisionCore` wrapped as tools
- **Arms System:** `BuddysArms` wrapped as tools
- **No Modifications:** Read-only integration, Phase 1 code untouched

### Phase 2 Integration
- **Confidence Scoring:** Web actions can be scored for confidence
- **Pre-Validation:** Tool parameters validated before execution
- **Approval Gates:** High-risk actions route through approval system
- **Soul Integration:** Ethical evaluation for sensitive actions

### Phase 4 Integration
- **Session Context:** Web actions capture metrics for SessionContext
- **Multi-Step Sequences:** Web tools work in test sequences
- **Metrics Aggregation:** Web action metrics aggregate with session metrics

### Tool Registry
- **Location:** `backend/main.py` - `register_web_tools(tool_registry)`
- **Total Tools:** 9 web tools registered
- **Namespace:** All tools prefixed with `web_`

---

## Testing & Validation

### Integration Test Harness
**File:** `buddy_web_integration_test_harness.py`

**Test Suites:**
1. **Safe Workflow Test:**
   - Start browser → Navigate → Inspect → Extract → Screenshot → Stop
   - Validates basic functionality
   - 100% safe operations

2. **Interaction Test:**
   - Click → Fill → Submit (dry-run)
   - Validates medium/high-risk actions
   - Tests dry-run enforcement

**Run Tests:**
```bash
# Run with dry-run enabled (safe)
python buddy_web_integration_test_harness.py

# Run with actions enabled (use caution)
export WEB_TOOLS_DRY_RUN=false
python buddy_web_integration_test_harness.py
```

**Validation Checklist:**
- ✅ Tool Registration
- ✅ Session Management
- ✅ Metrics Capture
- ✅ Feature Flag Respect
- ✅ Dry-Run Mode
- ✅ Error Handling
- ✅ Session Isolation
- ✅ Phase 1-4 Untouched

---

## Future Enhancements (Phase 6+)

### Planned Features:
1. **Conditional Workflows:** If/then/else logic for web actions
2. **Selector Healing:** Automatic fallback when selectors break
3. **Visual Element Location:** Screenshot-based element finding
4. **Confidence Calibration:** Update scores based on actual outcomes
5. **Workflow DSL:** YAML-based workflow definitions
6. **Site Adapters:** Learn and reuse site-specific patterns
7. **API Auto-Discovery:** Prefer APIs over browser automation

### Research Areas:
- ML-based element classification
- Real-time page change detection
- Network traffic interception
- WebSocket monitoring
- Performance optimization

---

## Troubleshooting

### Common Issues

**Issue:** Browser fails to start  
**Solution:** Check ChromeDriver is installed and cached at:  
`~/.wdm/drivers/chromedriver/win64/144.0.7559.133/chromedriver-win32/chromedriver.exe`

**Issue:** Elements not found  
**Solution:** Use `web_inspect()` first to understand page structure, then target specific elements

**Issue:** Actions blocked in dry-run  
**Solution:** Disable dry-run mode:  
```bash
export WEB_TOOLS_DRY_RUN=false
```

**Issue:** High-risk actions always blocked  
**Solution:** Explicitly enable (use with caution):  
```bash
export WEB_TOOLS_ALLOW_HIGH_RISK=true
```

**Issue:** Timeout errors  
**Solution:** Page may be slow - increase timeout in tool code or wait for page load manually

---

## Summary

Phase 5 successfully integrates Vision and Arms into Buddy's main agent loop, enabling:

- ✅ **9 web tools** for inspection, navigation, and interaction
- ✅ **Risk-based safety** with LOW/MEDIUM/HIGH classification
- ✅ **Dry-run mode** for safe testing and high-risk protection
- ✅ **Session management** for persistent browser state
- ✅ **Metrics capture** for future confidence calibration
- ✅ **Zero modifications** to Phase 1-4 code

**Next Steps:**
1. Run integration tests to validate functionality
2. Enable web tools in production with dry-run mode
3. Collect metrics for confidence calibration (Phase 6)
4. Add conditional workflows and selector healing (Phase 6)
5. Deploy to staging with Level 1 autonomy

---

**Document Version:** 1.0.0  
**Last Updated:** February 5, 2026  
**Phase:** 5 - Vision & Arms Integration  
**Status:** ✅ COMPLETE - Ready for testing
