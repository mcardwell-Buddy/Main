# HR Contact Finder & Enrichment Analyzer

Complete system for finding HR managers and above with contact data, deduplicating records, and identifying enrichment opportunities.

## Overview

This system allows you to:

✅ **Find HR Contacts** - Automatically locate HR managers, directors, VPs, and C-suite executives  
✅ **Extract Contact Data** - Capture emails, phone numbers (direct, main, mobile, extensions), LinkedIn URLs  
✅ **Deduplicate Records** - Identify and merge duplicate contacts intelligently  
✅ **Analyze Data Quality** - Get completeness scores and identify missing information  
✅ **Find Enrichment Targets** - Prioritize which contacts need data updates  
✅ **Export Results** - Save contacts to JSON or CSV for further use  

## Quick Start

### 1. Simple Usage

```python
from backend.hr_contact_manager import find_hr_contacts

# Find HR contacts from employer data
contacts = find_hr_contacts(
    employer_data=employers_from_mployer,
    location="Baltimore, Maryland",
    seniority="executive",  # c_suite, executive, director_and_above, all
    require_email=True,
    require_phone=False,
    require_linkedin=False,
    max_results=100
)

# Use the contacts
for contact in contacts:
    print(f"{contact.full_name} - {contact.email}")
```

### 2. Interactive CLI

```bash
python hr_contact_search.py
```

Provides a menu-driven interface to:
- Search Mployer for employers
- Find HR contacts with custom parameters
- Analyze results and deduplication
- Export to JSON/CSV
- View enrichment targets

### 3. Advanced API Usage

```python
from backend.hr_contact_manager import HRContactManager
from backend.hr_search_params import HRContactSearchBuilder, SeniorityLevel, ContactDataType

manager = HRContactManager()

# Build custom search
params = (HRContactSearchBuilder()
    .executive_and_above()  # VP and C-suite
    .with_company_size(500, 50000)  # 500-50k employees
    .require_contact_data(
        ContactDataType.EMAIL,
        ContactDataType.ANY_PHONE,
        ContactDataType.LINKEDIN
    )
    .exclude_keywords("non-profit", "staffing")
    .min_completeness(0.7)  # At least 70% data completeness
    .limit(100)
    .build())

# Search employer data
results = manager.search_from_employer_data(employer_data, params)

# Analyze
report = manager.generate_report()
print(f"Found {len(results)} contacts")
print(f"High priority enrichment: {report['enrichment_summary']['high_priority']}")

# Export
manager.save_results(format="json")
manager.save_report()
```

## Architecture

### Core Modules

#### 1. `hr_contact_extractor.py`
Extracts and analyzes individual contacts from raw data.

**Main Classes:**
- `ContactInfo` - Structured contact data with completeness metrics
- `HRContactExtractor` - Extracts contacts, deduplicates, and analyzes

**Key Features:**
- Identifies HR roles (manager level and above)
- Extracts all contact methods (email, phone types, LinkedIn)
- Calculates data completeness scores
- Intelligent deduplication using similarity scoring
- Identifies enrichment priorities

**Usage:**
```python
from backend.hr_contact_extractor import HRContactExtractor

extractor = HRContactExtractor()

# Extract from raw data
contact = extractor.extract_contact_info({
    "first_name": "Sarah",
    "last_name": "Johnson",
    "job_title": "Vice President of Human Resources",
    "company_name": "Tech Corp",
    "email": "sarah.johnson@techcorp.com",
    "phone": "Office: (410) 555-1234, Mobile: (410) 555-5678",
    "linkedin_url": "https://linkedin.com/in/sarahjohnson"
})

# Check data quality
print(f"Completeness: {contact.data_completeness*100:.1f}%")
print(f"Needs enrichment: {contact.needs_enrichment}")
print(f"Priority: {contact.enrichment_priority}")

# Batch extract
contacts = extractor.extract_batch(raw_data_list)

# Deduplicate
unique = extractor.deduplicate(similarity_threshold=0.85)
print(f"Merged {len(extractor.duplicates)} duplicate groups")
```

#### 2. `hr_search_params.py`
Flexible parameter system for configuring searches.

**Main Classes:**
- `HRContactSearchParams` - Data class holding all search parameters
- `HRContactSearchBuilder` - Fluent API for building searches
- `PresetSearches` - Pre-configured common searches

**Seniority Levels:**
- `C_SUITE` - CHRO, Chief People Officer
- `EXECUTIVE` - VP of HR, SVP
- `DIRECTOR` - Director of HR
- `SENIOR_MANAGER` - Senior HR Manager
- `MANAGER` - HR Manager
- `ALL` - All HR roles

**Contact Data Types:**
- `EMAIL` - Email address
- `PHONE_DIRECT` - Direct phone line
- `PHONE_MAIN` - Main/office line
- `PHONE_MOBILE` - Mobile number
- `PHONE_EXTENSION` - Extension number
- `LINKEDIN` - LinkedIn URL
- `ANY_PHONE` - Any phone type

**Usage:**
```python
from backend.hr_search_params import HRContactSearchBuilder, PresetSearches

# Method 1: Fluent API
params = (HRContactSearchBuilder()
    .c_suite_only()
    .with_company_size(1000, 100000)
    .require_email()
    .require_linkedin()
    .exclude_keywords("non-profit")
    .build())

# Method 2: Preset
params = PresetSearches.vp_hr_with_full_contact()

# Method 3: Custom
from backend.hr_search_params import ContactDataType
params = (HRContactSearchBuilder()
    .director_and_above()
    .require_contact_data(ContactDataType.EMAIL, ContactDataType.PHONE_DIRECT)
    .min_completeness(0.6)
    .build())
```

#### 3. `hr_contact_manager.py`
Main interface combining extraction, search, and analysis.

**Main Classes:**
- `HRContactManager` - Unified interface for all operations
- Helper functions: `find_hr_contacts()`, `analyze_hr_contacts()`

**Key Methods:**
```python
manager = HRContactManager()

# Search
results = manager.search_from_employer_data(employer_data, search_params)

# Analysis
stats = manager.get_statistics()
report = manager.generate_report()
enrichment_targets = manager.get_enrichment_targets("high")
duplicates = manager.get_duplicate_groups()

# Export
manager.save_results(format="json")  # Save last search results
manager.save_report()  # Save analysis report
manager.load_contacts_from_file("path/to/file.json")  # Load previous results
```

#### 4. `hr_contact_search.py`
Interactive CLI for command-line usage.

**Features:**
- Menu-driven interface
- Mployer integration
- Real-time search and analysis
- Interactive export

**Run:**
```bash
python hr_contact_search.py
```

## Workflow Examples

### Example 1: Find CHRO with Email/Phone

```python
from backend.hr_contact_manager import find_hr_contacts

contacts = find_hr_contacts(
    employer_data=employers,
    seniority="c_suite",
    require_email=True,
    require_phone=True
)
```

### Example 2: Find Mid-Market HR Directors

```python
from backend.hr_contact_manager import HRContactManager, PresetSearches

manager = HRContactManager()

# Mid-market: 100-2000 employees
params = PresetSearches.mid_market_hr_directors()

results = manager.search_from_employer_data(employers, params)
print(f"Found {len(results)} directors in mid-market companies")
```

### Example 3: Identify Enrichment Targets

```python
# Find contacts that need data enrichment
enrichment_targets = manager.get_enrichment_targets("high")

for contact in enrichment_targets:
    print(f"{contact.full_name} - {contact.company_name}")
    print(f"  Completeness: {contact.data_completeness*100:.1f}%")
    print(f"  Missing: {', '.join(contact.enrichment_notes)}")
```

### Example 4: Full Mployer Workflow

```python
from backend.mployer_scraper import MployerScraper
from backend.hr_contact_manager import HRContactManager, PresetSearches

# 1. Search Mployer
scraper = MployerScraper(username, password, headless=False)
scraper.initialize_browser()
scraper.login_to_mployer()
employers = scraper.search_employers(employees_min=50, employees_max=5000)

# 2. Extract HR contacts
manager = HRContactManager()
params = PresetSearches.director_and_above()
contacts = manager.search_from_employer_data(employers, params)

# 3. Analyze
report = manager.generate_report()

# 4. Export
manager.save_results(format="json")

scraper.close()
```

### Example 5: Custom Complex Search

```python
from backend.hr_search_params import HRContactSearchBuilder, ContactDataType

# Build: VP/C-suite in tech, with complete contact info, no consultancies
params = (HRContactSearchBuilder()
    .executive_and_above()
    .with_company_size(500, 100000)
    .require_contact_data(
        ContactDataType.EMAIL,
        ContactDataType.ANY_PHONE,
        ContactDataType.LINKEDIN
    )
    .with_industries("Technology", "Software", "SaaS")
    .exclude_keywords("consulting", "staffing", "temporary")
    .min_completeness(0.85)
    .limit(50)
    .build())

results = manager.search_from_employer_data(employers, params)
```

## Data Structures

### ContactInfo

```python
@dataclass
class ContactInfo:
    # Personal Info
    first_name: str
    last_name: str
    full_name: str
    job_title: str
    
    # Company Info
    company_name: str
    company_id: Optional[str]
    
    # Contact Methods
    email: Optional[str]
    phone_direct: Optional[str]  # Direct line
    phone_main: Optional[str]    # Main/office
    phone_mobile: Optional[str]  # Mobile
    phone_extension: Optional[str]
    linkedin_url: Optional[str]
    
    # Data Metadata
    source: str  # "mployer", etc.
    extracted_date: str  # ISO format
    data_completeness: float  # 0-1
    contact_methods_count: int
    
    # Enrichment Tracking
    needs_enrichment: bool
    enrichment_priority: int  # 1=high, 2=medium, 3=low, 0=not needed
    last_enrichment_date: Optional[str]
    enrichment_notes: List[str]
```

### HRContactSearchParams

```python
@dataclass
class HRContactSearchParams:
    locations: List[str]
    company_size_min: int
    company_size_max: int
    seniority_levels: List[SeniorityLevel]
    required_contact_types: List[ContactDataType]
    industries: List[str]
    excluded_industries: List[str]
    exclude_keywords: List[str]
    min_data_completeness: float
    needs_enrichment_only: bool
    enrichment_priority_min: Optional[int]
    enrichment_priority_max: Optional[int]
    max_results: Optional[int]
```

## Report Output

When you call `generate_report()`, you get:

```json
{
  "timestamp": "2024-02-05T10:30:00",
  "statistics": {
    "total_contacts": 250,
    "unique_contacts": 245,
    "with_email": 240,
    "with_phone": 180,
    "with_linkedin": 120,
    "complete_contact_info": 85,
    "needing_enrichment": 165,
    "avg_completeness": 0.72
  },
  "duplicate_summary": {
    "total_duplicates_found": 3,
    "total_records_merged": 5,
    "details": [...]
  },
  "enrichment_summary": {
    "high_priority": 85,
    "medium_priority": 60,
    "low_priority": 20,
    "complete_contacts": 85
  },
  "high_priority_enrichment_targets": [...]
}
```

## Deduplication Algorithm

The system uses a similarity-based approach:

1. **Exact Matches:**
   - Same email (2.0 points)
   - Same phone (2.0 points)
   - Exact name match (2.0 points)

2. **Fuzzy Matches:**
   - Similar names (1.5 points)
   - Same company (1.0 point)
   - Same LinkedIn (1.0 point)

3. **Merging:**
   - Identifies duplicate groups
   - Merges highest quality version as primary
   - Fills missing data from secondary records

## Data Completeness Scoring

Scores are calculated as percentage of fields populated:

- Email: 1.5 points
- Phone (any type): 1.0 points
- LinkedIn: 1.0 points
- Name: 1.0 points
- Job title: 1.0 points
- Company: 0.5 points
- Extension: 0.5 points

**Maximum: 7.0 points = 100% complete**

## HR Role Detection

The system recognizes these job title patterns:

**C-Suite:**
- Chief Human Resources Officer
- Chief People Officer
- CHRO

**Executive:**
- Vice President of HR/Human Resources
- VP HR
- SVP Human Resources

**Director:**
- Director of Human Resources
- Director HR

**Senior Manager:**
- Senior HR Manager
- Senior Human Resources Manager
- Regional HR Manager

**Manager:**
- HR Manager
- Human Resources Manager

## Enrichment Priority

Contacts are prioritized for enrichment based on data completeness:

- **High Priority (1):** < 30% completeness
- **Medium Priority (2):** 30-60% completeness
- **Low Priority (3):** 60-90% completeness
- **Not Needed (0):** ≥ 90% completeness

## Export Formats

### JSON
```json
[
  {
    "first_name": "Sarah",
    "last_name": "Johnson",
    "full_name": "Sarah Johnson",
    "email": "sarah@techcorp.com",
    "phone_direct": "(410) 555-1234",
    "phone_mobile": "(410) 555-5678",
    "linkedin_url": "https://linkedin.com/in/sarahjohnson",
    "company_name": "Tech Corp",
    "job_title": "Vice President of Human Resources",
    "data_completeness": 0.95,
    "needs_enrichment": false
  }
]
```

### CSV
```
First Name,Last Name,Email,Phone Direct,Phone Main,Phone Mobile,LinkedIn,Company,Job Title,Completeness,Needs Enrichment
Sarah,Johnson,sarah@techcorp.com,(410) 555-1234,,(410) 555-5678,https://linkedin.com/in/sarahjohnson,Tech Corp,Vice President of Human Resources,0.95,false
```

## Integration with Mployer

The system integrates with Mployer scraper:

```python
from backend.mployer_scraper import MployerScraper
from backend.hr_contact_manager import HRContactManager, PresetSearches

# Use existing scraper workflow
scraper = MployerScraper(username, password)
scraper.initialize_browser()
scraper.login_to_mployer()

# Search Mployer
employers = scraper.search_employers(
    employees_min=50,
    employees_max=5000,
    location="Maryland"
)

# Extract HR contacts from results
manager = HRContactManager()
results = manager.search_from_employer_data(
    employers,
    PresetSearches.director_and_above()
)

scraper.close()
```

## Performance Considerations

- **Deduplication:** Uses O(n²) similarity comparison. For 10k+ contacts, consider batching.
- **Completeness:** Cached in ContactInfo object, recalculated on demand.
- **Memory:** Contacts stored in-memory. For millions of records, use pagination/streaming.

## Error Handling

```python
try:
    manager = HRContactManager()
    results = manager.search_from_employer_data(employer_data, params)
except ValueError as e:
    print(f"Invalid parameters: {e}")
except FileNotFoundError as e:
    print(f"File not found: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Command Line Usage

```bash
# Interactive menu
python hr_contact_search.py

# Run examples
python hr_contact_examples.py
```

## File Structure

```
Buddy/
├── backend/
│   ├── hr_contact_extractor.py      # Core extraction & deduplication
│   ├── hr_search_params.py          # Search configuration
│   ├── hr_contact_manager.py        # Main interface
│   └── mployer_scraper.py           # Mployer integration
├── hr_contact_search.py              # Interactive CLI
├── hr_contact_examples.py            # Usage examples
├── HR_CONTACT_FINDER.md             # This documentation
└── hr_contacts/                      # Output directory
    ├── hr_contacts_*.json           # Exported contacts
    ├── hr_contacts_*.csv            # Exported contacts
    └── hr_analysis_report_*.json    # Analysis reports
```

## Common Tasks

### Task 1: Find all CHRO with email or phone
```python
contacts = find_hr_contacts(
    employer_data=employers,
    seniority="c_suite",
    require_email=True,
    require_phone=True
)
```

### Task 2: Find directors in Maryland
```python
builder = HRContactSearchBuilder()
params = builder.director_and_above().with_locations("Maryland").build()
results = manager.search_from_employer_data(employers, params)
```

### Task 3: Find contacts needing LinkedIn enrichment
```python
contacts_without_linkedin = [
    c for c in manager.contacts
    if not c.linkedin_url and c.email  # Has email but no LinkedIn
]
```

### Task 4: Export all high-priority enrichment targets
```python
high_priority = manager.get_enrichment_targets("high")
manager.save_results(format="csv", contacts=high_priority)
```

### Task 5: Find duplicates across two data sources
```python
manager.extractor.extract_batch(source1_data)
manager.extractor.extract_batch(source2_data)
unique = manager.extractor.deduplicate()
duplicates = manager.get_duplicate_groups()
```

## Troubleshooting

**No HR contacts found:**
- Check that job titles match HR patterns
- Try lowering the seniority filter
- Verify source data has job titles

**Too many duplicates:**
- Increase similarity_threshold in `deduplicate()`
- Check if data sources have repeated entries

**Low completeness scores:**
- Source data may not include phone/LinkedIn
- Consider separate enrichment pass with data providers

**Export files are empty:**
- Run search first: `manager.search_from_employer_data()`
- Or use `manager.contacts` directly

## Support & Examples

See `hr_contact_examples.py` for 7 complete working examples:
1. Quick find
2. Advanced search
3. Enrichment targets
4. Duplicate analysis
5. Full Mployer workflow
6. Custom fluent searches
7. Export formats

Run: `python hr_contact_examples.py`
