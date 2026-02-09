# IMPORTANT: Mployer Automation Setup Requirements

## ⚠️ Important Notices

### HTML Selectors Need Adjustment
The `mployer_scraper.py` file has **placeholder selectors** that need to be updated with Mployer's actual HTML structure.

**What are selectors?** They're like "addresses" for finding elements on the webpage:
```python
# Example:
username_field = wait.until(EC.presence_of_element_located((By.ID, "email")))
# This looks for an element with ID="email"
```

### Why They Need Updating:
Every website has different HTML. Mployer's structure is specific to their system. I provided a template with common patterns, but you'll need to verify/adjust them.

---

## How to Update Selectors (Step-by-Step)

### 1. Find the Right Selectors:

**Method A: Using Chrome DevTools (Easiest)**
1. Go to mployer.com
2. Right-click on the login email field → **Inspect**
3. Look at the HTML:
   ```html
   <input id="emailField" name="login_email" type="email" />
   ```
4. You now know the selector is: `By.ID, "emailField"`

**Method B: Ask for Help**
Send me a screenshot of Mployer's login page or search page HTML, and I'll update the selectors for you.

---

## Areas That Will Likely Need Adjustment:

### 1. Login Page Selectors (Lines 42-60)
```python
# THESE NEED TO BE VERIFIED:
username_field = wait.until(EC.presence_of_element_located((By.ID, "email")))
password_field = self.driver.find_element(By.ID, "password")
login_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Sign In')]")
```

### 2. Search Form Selectors (Lines 79-98)
```python
# THESE NEED TO BE VERIFIED:
title_field = wait.until(EC.presence_of_element_located((By.NAME, "job_title")))
location_field = self.driver.find_element(By.NAME, "location")
size_min_field = self.driver.find_element(By.NAME, "company_size_min")
```

### 3. Results Extraction Selectors (Lines 125-170)
```python
# THESE NEED TO BE VERIFIED:
result_rows = self.driver.find_elements(By.CLASS_NAME, "contact-row")
name_elem = row.find_element(By.CLASS_NAME, "contact-name")
email_elem = row.find_element(By.CLASS_NAME, "email")
```

---

## How to Get the Correct Selectors

### Step 1: Find Elements with Inspect

Open Chrome DevTools on Mployer:
- **Right-click** on element → **Inspect**
- Look for unique identifiers:

```html
<input id="emailAddress" ... />           ← Use: By.ID, "emailAddress"
<input name="search_title" ... />         ← Use: By.NAME, "search_title"
<input class="form-input email" ... />    ← Use: By.CLASS_NAME, "form-input"
<button data-test="search-btn" ... />     ← Use: By.CSS_SELECTOR, "[data-test='search-btn']"
<div role="result" ... />                 ← Use: By.XPATH, "//div[@role='result']"
```

### Step 2: Test Before Using

Before automation runs, test each selector:
```python
# In test file
from selenium import webdriver
from selenium.webdriver.common.by import By

driver = webdriver.Chrome()
driver.get("https://www.mployer.com/login")

# Test selector:
try:
    element = driver.find_element(By.ID, "email")
    print("✓ Found element!")
except:
    print("✗ Selector not found - try different one")
```

---

## Simple Starting Test

Run this to verify the basic setup before worrying about selectors:

```python
# test_mployer_setup.py
import sys
sys.path.insert(0, 'C:/Users/micha/Buddy')

from backend.credential_manager import CredentialManager

try:
    creds = CredentialManager.get_credentials()
    print("✓ Credentials loaded successfully!")
    print(f"  Username: {creds['username']}")
except Exception as e:
    print(f"✗ Credentials error: {e}")
    print("\nRun setup:")
    print('python -c "from backend.credential_manager import CredentialManager; CredentialManager.setup_credentials()"')
```

---

## Getting Help with Selectors

### I Can Help If You:
1. Run the automation once (it will show errors)
2. Share the error messages
3. Share a screenshot of Mployer's page
4. Share the Chrome DevTools inspect view of the element

Then I'll update the selectors for you.

---

## Expected Behavior Once Working

When running correctly:
```
✓ Browser initialized
✓ Successfully logged into Mployer
✓ Searching Mployer for Head of HR in Baltimore...
✓ Processing 15 result rows...
  ✓ Extracted: Sarah Johnson (TechCorp Inc)
  ✓ Extracted: John Smith (ABC Corp)
  ✓ Extracted: Jane Doe (XYZ Industries)
✓ Found 15 contacts matching criteria
✓ Added to GHL: Sarah Johnson (Contact ID: abc123xyz)
✓ Added to GHL: John Smith (Contact ID: def456xyz)
✓ Added to GHL: Jane Doe (Contact ID: ghi789xyz)
✓ Mployer import complete: 3 added, 0 failed
```

---

## Quick Reference: Selector Types

```python
from selenium.webdriver.common.by import By

By.ID                    # <input id="myField" />
By.NAME                  # <input name="myField" />
By.CLASS_NAME            # <input class="myClass" />
By.TAG_NAME              # <input /> ← finds by tag
By.CSS_SELECTOR          # Complex CSS paths
By.XPATH                 # XPath expressions
By.LINK_TEXT             # <a>Click me</a>
By.PARTIAL_LINK_TEXT     # Partial link text
```

---

## Next Action

1. **Try the basic setup first:**
   ```powershell
   python -c "from backend.credential_manager import CredentialManager; CredentialManager.setup_credentials()"
   ```

2. **Get the selectors from Mployer** (inspect the page)

3. **Update the selectors in mployer_scraper.py** or send them to me

4. **Test with one run:**
   ```powershell
   python -c "from backend.mployer_scheduler import MployerScheduler; s = MployerScheduler(); result = s.run_once_now()"
   ```

That's it! Once selectors are right, you're hands-off.
