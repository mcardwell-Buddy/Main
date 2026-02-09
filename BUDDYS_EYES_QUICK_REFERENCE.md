# 👀 BUDDY'S EYES - QUICK REFERENCE

## Initialize Vision
```python
from backend.buddys_vision import BuddysVision

vision = BuddysVision(scraper)
```

## Core Commands

### See & Learn
```python
# Buddy looks at a website
inspection = vision.see_website("https://example.com")

# Buddy remembers a site
vision.remember_site("https://example.com")

# Buddy analyzes deeply
analysis = vision.analyze_and_learn("https://example.com")
```

### Recall Knowledge
```python
# What does Buddy see now?
print(vision.what_do_you_see())

# What does Buddy remember about a site?
knowledge = vision.remember_about_site("example.com")

# Find an element by action
element = vision.find_element("login")
element = vision.find_element("search")
element = vision.find_element("submit")
```

---

## Inspection Output

```python
inspection = vision.see_website(url)

# Access data
inspection['page_title']           # Page title
inspection['forms']                # List of all forms
inspection['buttons']              # List of all buttons
inspection['inputs']               # List of all inputs
inspection['links']                # List of all links
inspection['data_attributes']      # All data-* attributes
inspection['auth_elements']        # Login/logout elements
inspection['selectors']            # Common IDs/classes
inspection['issues']               # Detected problems
```

---

## Form Inspection

```python
forms = inspection['forms']

for form in forms:
    form['id']          # Form ID
    form['method']      # POST/GET
    form['action']      # Form action URL
    form['fields']      # List of form fields
    
    for field in form['fields']:
        field['type']       # text, email, password, number
        field['name']       # Field name
        field['placeholder'] # Placeholder text
        field['required']   # Is required?
```

---

## Button Inspection

```python
buttons = inspection['buttons']

for btn in buttons:
    btn['text']         # Button text
    btn['id']           # Button ID
    btn['type']         # submit, button, reset
    btn['class']        # CSS classes
    btn['disabled']     # Is disabled?
    btn['data_attrs']   # Data attributes
```

---

## Input Inspection

```python
inputs = inspection['inputs']

for inp in inputs:
    inp['type']         # text, email, password, number
    inp['name']         # Input name
    inp['placeholder']  # Placeholder text
    inp['id']           # Input ID
    inp['required']     # Is required?
    inp['aria_label']   # Accessibility label
```

---

## Finding Elements

```python
# Buddy finds elements by action
login = vision.find_element("login")
search = vision.find_element("search")
filter = vision.find_element("filter")
apply = vision.find_element("apply")
submit = vision.find_element("submit")

# Returns selector string like:
# "button text containing 'login'"
# "input #search-box"
# "#apply-button"
```

---

## Knowledge Base

```python
# Buddy's memory is stored in:
# buddy_site_knowledge.json

# Load knowledge
knowledge = vision.eyes.site_knowledge

# Access site knowledge
mployer_knowledge = knowledge.get('mployeradvisor.com', {})

# What Buddy knows about Mployer:
mployer_knowledge['forms']           # Forms on site
mployer_knowledge['buttons']         # Buttons on site
mployer_knowledge['inputs']          # Inputs on site
mployer_knowledge['selectors']       # Common selectors
```

---

## Vision Tasks

```python
from backend.buddys_vision import BuddysVisionTasks

# Create site profile
profile = BuddysVisionTasks.create_site_profile(vision.eyes, url)

# Compare two websites
comparison = BuddysVisionTasks.compare_sites(vision.eyes, url1, url2)
```

---

## Practical Examples

### Example 1: Learn a Site
```python
vision = BuddysVision(scraper)
vision.see_website("https://example.com")
# Buddy now understands the site
```

### Example 2: Find and Interact
```python
# Buddy finds the login button
login_btn = vision.find_element("login")

# Buddy inspects the page
inspection = vision.see_website(current_url)

# Buddy finds the email input
for inp in inspection['inputs']:
    if 'email' in inp['placeholder'].lower():
        email_input = inp
```

### Example 3: Use Remembered Knowledge
```python
# Buddy remembers Mployer
knowledge = vision.remember_about_site("mployeradvisor.com")

# Find the Apply Filters button from memory
for btn in knowledge.get('buttons', []):
    if 'Apply' in btn.get('text', ''):
        apply_btn = btn
```

### Example 4: Adaptive Navigation
```python
# Buddy visits a site he's never seen
url = "https://newsite.com"

# He learns it immediately
vision.see_website(url)

# He can now find elements
search = vision.find_element("search")
login = vision.find_element("login")
```

---

## What Buddy Sees on Each Site

### At Mployer
```
✅ 13 forms (filters, search, etc)
✅ 27+ buttons (Apply, Clear, Search, etc)
✅ 88+ inputs (Min, Max, fields, searches)
✅ State/City/Industry dropdowns
✅ Data attributes for every element
✅ Apply Filters button
```

### At Any Website
```
✅ All forms and fields
✅ All buttons and clickables
✅ All inputs and types
✅ All navigation elements
✅ All data attributes
✅ API hints and endpoints
✅ Auth elements
✅ Performance metrics
```

---

## Tips for Using Buddy's Eyes

✅ **Always inspect first** - Let Buddy see before automating  
✅ **Use find_element for actions** - Buddy finds by action, not selector  
✅ **Check knowledge base** - Don't re-inspect if Buddy remembers  
✅ **Trust his learning** - He learns from every inspection  
✅ **Use data attributes** - They reveal element purposes  

---

## Troubleshooting

### Element Not Found
```python
# Re-inspect the page
inspection = vision.see_website(url)

# Check all elements
for inp in inspection['inputs']:
    print(inp)
```

### Knowledge Outdated
```python
# Buddy re-learns the site
vision.see_website(url)

# Knowledge is automatically updated
```

### Want More Detail
```python
# Get full inspection
inspection = vision.see_website(url)

# View specific section
print(json.dumps(inspection['forms'], indent=2))
```

---

## Summary

Buddy's Eyes gives him vision - the ability to:
- 👀 **See** website structures
- 🧠 **Remember** what he learns
- 🎯 **Find** elements intelligently
- 🔄 **Adapt** to changes
- 📚 **Build** knowledge over time

This is the foundation for truly intelligent web automation.

---

**Remember**: Without eyes, Buddy is blind. With eyes, he can navigate any website intelligently.

**Status**: ✅ **BUDDY CAN NOW SEE**
