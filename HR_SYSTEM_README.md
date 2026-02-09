# 🎯 HR Contact Finder & Enrichment System

**Complete solution for finding, analyzing, and managing HR contacts with automated deduplication and data enrichment tracking.**

## What You Get

A production-ready system that:

✅ **Finds HR Contacts** - Automatically identify HR managers, directors, VPs, and C-suite executives  
✅ **Extracts Contact Data** - Capture emails, phones (all types), LinkedIn URLs  
✅ **Deduplicates** - Intelligently merge duplicate records  
✅ **Analyzes Data Quality** - Get completeness scores (0-100%)  
✅ **Identifies Enrichment Targets** - See which contacts need data updates  
✅ **Exports Results** - Save to JSON, CSV, or PDF-ready reports  
✅ **Integrates with Mployer** - Works with your existing scraper  

## Quick Start (3 Options)

### 🎮 Interactive Menu (Easiest)
```bash
python hr_contact_search.py
```
Menu-driven interface with step-by-step workflow.

### 💻 Python Code (Most Common)
```python
from backend.hr_contact_manager import find_hr_contacts

contacts = find_hr_contacts(
    employer_data=employers,           # From Mployer
    seniority="director_and_above",    # c_suite, executive, etc.
    require_email=True,                 # Must have email
    max_results=100                     # Limit results
)

for contact in contacts:
    print(f"{contact.full_name} - {contact.email}")
```

### 🧪 Run Examples
```bash
python hr_contact_examples.py
```
7 working examples covering all features.

## System Architecture

```
┌─────────────────────────────────────────────────────┐
│         HRContactManager (Main Interface)           │
├─────────────────────────────────────────────────────┤
│  ├─ Search & Filter Contacts                        │
│  ├─ Get Statistics & Reports                        │
│  ├─ Export to JSON/CSV                              │
│  └─ Save/Load Contact Lists                         │
├─────────────────────────────────────────────────────┤
│  Powered by:                                         │
│  ├─ HRContactExtractor (extraction & dedup)        │
│  ├─ HRContactSearchBuilder (fluent search API)     │
│  ├─ PresetSearches (pre-built searches)            │
│  └─ ContactInfo (data structure)                   │
└─────────────────────────────────────────────────────┘
```

## Files Overview

| File | Purpose | Lines |
|------|---------|-------|
| `backend/hr_contact_extractor.py` | Core extraction & deduplication | 556 |
| `backend/hr_search_params.py` | Search configuration | 335 |
| `backend/hr_contact_manager.py` | Main interface | 500+ |
| `hr_contact_search.py` | Interactive CLI | 400+ |
| `hr_contact_examples.py` | Working examples | 400+ |
| `test_hr_system.py` | Validation tests | 350+ |
| `HR_CONTACT_FINDER.md` | Full documentation | 800+ |
| `HR_QUICK_REFERENCE.py` | Quick reference guide | 500+ |

## Common Tasks

### Task 1: Find HR Directors with Complete Contact Info
```python
from backend.hr_contact_manager import find_hr_contacts

contacts = find_hr_contacts(
    employer_data=employers,
    seniority="director_and_above",
    require_email=True,
    require_phone=True,
    require_linkedin=True,
    max_results=200
)
```

### Task 2: Find Contacts Needing Enrichment
```python
from backend.hr_contact_manager import HRContactManager

manager = HRContactManager()
manager.search_from_employer_data(employers)

# Get high-priority enrichment targets
targets = manager.get_enrichment_targets("high")

for contact in targets:
    print(f"{contact.full_name} - Missing: {', '.join(contact.enrichment_notes)}")
```

### Task 3: Analyze Duplicates
```python
duplicates = manager.get_duplicate_groups()

print(f"Found {len(duplicates)} duplicate groups")
for group in duplicates:
    print(f"  {len(group)} records for {group[0].full_name}")
```

### Task 4: Export to CSV
```python
# Export last search results
manager.save_results(format="csv", filename="hr_contacts.csv")

# Export specific contacts
enrichment_targets = manager.get_enrichment_targets("high")
manager.save_results(format="csv", contacts=enrichment_targets)
```

### Task 5: Generate Analysis Report
```python
report = manager.generate_report()

print(f"Total contacts: {report['statistics']['total_contacts']}")
print(f"With email: {report['statistics']['with_email']}")
print(f"High priority enrichment: {report['enrichment_summary']['high_priority']}")
```

## Seniority Levels

| Level | Examples |
|-------|----------|
| `c_suite` | Chief HR Officer, Chief People Officer |
| `executive` | VP, SVP of HR |
| `director` | Director of HR |
| `senior_manager` | Senior HR Manager, Regional HR Manager |
| `manager` | HR Manager |
| `all` | All HR roles |

## Contact Data Types

- **email** - Email address
- **phone_direct** - Direct phone line
- **phone_main** - Main/office line
- **phone_mobile** - Mobile number
- **phone_extension** - Extension
- **linkedin** - LinkedIn URL
- **any_phone** - Any phone type

## Data Completeness

Contacts are scored 0-100% based on available data:

- Full name: 14%
- Email: 21%
- Phone (any): 14%
- LinkedIn: 14%
- Job title: 14%
- Company: 7%
- Extension: 7%

**Total: 100%**

### Enrichment Priorities

- **High (1)**: < 30% complete - Missing critical data
- **Medium (2)**: 30-60% complete - Missing some fields
- **Low (3)**: 60-90% complete - Almost complete
- **Not Needed (0)**: ≥ 90% complete - Ready to use

## Search Builder (Fluent API)

```python
from backend.hr_search_params import HRContactSearchBuilder, ContactDataType

params = (HRContactSearchBuilder()
    .executive_and_above()
    .with_company_size(500, 50000)
    .require_contact_data(
        ContactDataType.EMAIL,
        ContactDataType.ANY_PHONE,
        ContactDataType.LINKEDIN
    )
    .exclude_keywords("staffing", "non-profit")
    .min_completeness(0.7)
    .limit(100)
    .build())

results = manager.search_from_employer_data(employers, params)
```

## Deduplication Algorithm

The system intelligently identifies duplicates using:

1. **Exact Matches** (Very Strong)
   - Same email (2.0 points)
   - Same phone (2.0 points)
   - Exact name (2.0 points)

2. **Fuzzy Matches** (Strong)
   - Similar names (1.5 points)
   - Same company (1.0 point)
   - Same LinkedIn (1.0 point)

3. **Merging** - Keeps highest quality data from all duplicates

## Report Output

```json
{
  "statistics": {
    "total_contacts": 250,
    "with_email": 240,
    "with_phone": 180,
    "with_linkedin": 120,
    "avg_completeness": 0.72
  },
  "duplicate_summary": {
    "total_duplicates_found": 3,
    "total_records_merged": 5
  },
  "enrichment_summary": {
    "high_priority": 85,
    "medium_priority": 60,
    "low_priority": 20,
    "complete_contacts": 85
  }
}
```

## Export Formats

### JSON
```json
[{
  "first_name": "Sarah",
  "last_name": "Johnson",
  "email": "sarah@techcorp.com",
  "phone_direct": "(410) 555-1234",
  "linkedin_url": "https://linkedin.com/in/sarahjohnson",
  "company_name": "Tech Corp",
  "job_title": "VP of Human Resources",
  "data_completeness": 0.95,
  "needs_enrichment": false
}]
```

### CSV
```
First Name,Last Name,Email,Phone Direct,LinkedIn,Company,Job Title,Completeness,Needs Enrichment
Sarah,Johnson,sarah@techcorp.com,(410) 555-1234,linkedin.com/in/sarahjohnson,Tech Corp,VP HR,0.95,false
```

## Integration with Mployer

```python
from backend.mployer_scraper import MployerScraper
from backend.hr_contact_manager import HRContactManager, PresetSearches

# Use existing Mployer scraper
scraper = MployerScraper(username, password)
scraper.initialize_browser()
scraper.login_to_mployer()

# Search employers
employers = scraper.search_employers(employees_min=50, employees_max=5000)

# Extract HR contacts
manager = HRContactManager()
results = manager.search_from_employer_data(
    employers,
    PresetSearches.director_and_above()
)

# Analyze and export
report = manager.generate_report()
manager.save_results(format="json")

scraper.close()
```

## Validation

Run tests to validate system:

```bash
python test_hr_system.py
```

Expected output:
```
✅ Passed: 10/10
🎉 All tests passed! System is ready to use.
```

## File Structure

```
Buddy/
├── backend/
│   ├── hr_contact_extractor.py      # Extraction & deduplication
│   ├── hr_search_params.py          # Search configuration
│   ├── hr_contact_manager.py        # Main interface
│   ├── mployer_scraper.py           # Mployer integration
│   └── ...
├── hr_contact_search.py              # Interactive CLI
├── hr_contact_examples.py            # 7 working examples
├── test_hr_system.py                 # Validation tests
├── HR_CONTACT_FINDER.md              # Full documentation
├── HR_QUICK_REFERENCE.py             # Quick reference
├── IMPLEMENTATION_SUMMARY.md         # This summary
└── hr_contacts/                      # Output directory
    ├── hr_contacts_*.json
    ├── hr_contacts_*.csv
    └── hr_analysis_report_*.json
```

## Examples

### Example 1: Quick Find
```python
from backend.hr_contact_manager import find_hr_contacts

contacts = find_hr_contacts(
    employer_data=employers,
    seniority="director_and_above",
    require_email=True
)
```

### Example 2: Advanced Search
```python
from backend.hr_contact_manager import HRContactManager
from backend.hr_search_params import HRContactSearchBuilder, ContactDataType

builder = HRContactManager().create_search_builder()
params = builder.executive_and_above()\
    .with_company_size(500, 50000)\
    .require_complete_contact()\
    .exclude_keywords("non-profit")\
    .build()

results = manager.search_from_employer_data(employers, params)
```

### Example 3: Enrichment Analysis
```python
manager = HRContactManager()
manager.search_from_employer_data(employers)

high_priority = manager.get_enrichment_targets("high")
medium_priority = manager.get_enrichment_targets("medium")

print(f"High priority: {len(high_priority)}")
print(f"Medium priority: {len(medium_priority)}")
```

### Example 4: Duplicate Analysis
```python
duplicates = manager.get_duplicate_groups()

for group in duplicates:
    print(f"\n{group[0].company_name}:")
    for contact in group:
        print(f"  {contact.full_name} ({contact.email})")
```

## Performance

- **Extraction**: ~100ms per 100 contacts
- **Deduplication**: ~50ms for 100 contacts (O(n²) algorithm)
- **Search/Filter**: ~10ms for 100 contacts
- **Export**: ~50ms for 100 contacts to JSON

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No HR contacts found | Check job titles match HR patterns, try lower seniority level |
| Too many duplicates | Increase `similarity_threshold` in `deduplicate()` |
| Low completeness | Source data may not include phone/LinkedIn info |
| Export is empty | Run search first, use `manager.last_search_results` |

## Documentation

- **Full docs**: [HR_CONTACT_FINDER.md](HR_CONTACT_FINDER.md) (800+ lines)
- **Quick ref**: [HR_QUICK_REFERENCE.py](HR_QUICK_REFERENCE.py) (500+ lines)
- **Examples**: [hr_contact_examples.py](hr_contact_examples.py) (7 examples)
- **Summary**: [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)

## Support

### Getting Help

1. Check [HR_QUICK_REFERENCE.py](HR_QUICK_REFERENCE.py) for copy-paste recipes
2. Run examples: `python hr_contact_examples.py`
3. Read full docs: [HR_CONTACT_FINDER.md](HR_CONTACT_FINDER.md)
4. Run tests: `python test_hr_system.py`

### Common Recipes

```python
# Find CHRO with contact data
contacts = find_hr_contacts(employers, seniority="c_suite", require_email=True)

# Find directors in Maryland  
params = builder.director_and_above().with_locations("Maryland").build()

# Export high-priority enrichment targets
targets = manager.get_enrichment_targets("high")
manager.save_results(format="csv", contacts=targets)

# Analyze duplicates
duplicates = manager.get_duplicate_groups()

# Get statistics
stats = manager.get_statistics()

# Generate report
report = manager.generate_report()
```

---

**Ready to use! 🚀**

Start with: `python hr_contact_search.py`
