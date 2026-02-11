"""
HR Contact System - Quick Reference Guide
"""

# ============================================================================
# QUICK START - Copy & Paste Recipes
# ============================================================================

# 1️⃣ FIND HR CONTACTS (Simplest)
# ─────────────────────────────────────────────────────────────────────────
from Back_End.hr_contact_manager import find_hr_contacts

contacts = find_hr_contacts(
    employer_data=employers,              # From Mployer search
    seniority="director_and_above",       # c_suite, executive, director_and_above, all
    require_email=True,                   # Must have email
    require_phone=False,                  # Must have phone
    require_linkedin=False,               # Must have LinkedIn
    max_results=100                       # Limit results
)

for contact in contacts:
    print(f"{contact.full_name} | {contact.company_name}")
    print(f"  Email: {contact.email}")
    print(f"  Phone: {contact.phone_direct or contact.phone_main}")
    print(f"  Data: {contact.data_completeness*100:.0f}%")


# 2️⃣ USE PRESET SEARCHES
# ─────────────────────────────────────────────────────────────────────────
from Back_End.hr_contact_manager import HRContactManager, PresetSearches

manager = HRContactManager()

# Preset options:
# - chro_contacts_with_contact_data()     → C-suite with email or phone
# - vp_hr_with_full_contact()            → VPs with email, phone, LinkedIn
# - mid_market_hr_directors()            → Directors in 100-2000 employee companies
# - high_priority_enrichment_targets()   → Contacts needing data

results = manager.search_from_employer_data(
    employers,
    PresetSearches.vp_hr_with_full_contact()
)


# 3️⃣ CUSTOM FLUENT SEARCH
# ─────────────────────────────────────────────────────────────────────────
from Back_End.hr_search_params import HRContactSearchBuilder, ContactDataType

params = (HRContactSearchBuilder()
    .executive_and_above()                           # VP or C-suite
    .with_company_size(500, 50000)                   # 500-50k employees
    .require_contact_data(
        ContactDataType.EMAIL,                       # Need email
        ContactDataType.ANY_PHONE                    # Need any phone
    )
    .exclude_keywords("staffing", "non-profit")     # Skip these
    .min_completeness(0.7)                           # At least 70% complete
    .limit(100)                                      # Max 100 results
    .build())

results = manager.search_from_employer_data(employers, params)


# 4️⃣ FIND ENRICHMENT TARGETS
# ─────────────────────────────────────────────────────────────────────────
# Contacts that need data updates

high_priority = manager.get_enrichment_targets("high")      # Lots of missing data
medium_priority = manager.get_enrichment_targets("medium")  # Some missing data
low_priority = manager.get_enrichment_targets("low")        # Mostly complete

for contact in high_priority:
    missing = []
    if not contact.email:
        missing.append("email")
    if not contact.phone_direct and not contact.phone_main:
        missing.append("phone")
    if not contact.linkedin_url:
        missing.append("linkedin")
    
    print(f"{contact.full_name} - Missing: {', '.join(missing)}")


# 5️⃣ ANALYZE DUPLICATES
# ─────────────────────────────────────────────────────────────────────────
duplicates = manager.get_duplicate_groups()

print(f"Found {len(duplicates)} duplicate groups")

for group in duplicates:
    print(f"\n{group[0].company_name}:")
    for contact in group:
        print(f"  • {contact.full_name} - {contact.email}")


# 6️⃣ GET STATISTICS
# ─────────────────────────────────────────────────────────────────────────
stats = manager.get_statistics()

print(f"Total: {stats['total_contacts']}")
print(f"With email: {stats['with_email']}")
print(f"With phone: {stats['with_phone']}")
print(f"With LinkedIn: {stats['with_linkedin']}")
print(f"Complete: {stats['complete_contact_info']}")
print(f"Avg completeness: {stats['avg_completeness']*100:.1f}%")


# 7️⃣ GENERATE REPORT
# ─────────────────────────────────────────────────────────────────────────
report = manager.generate_report()

# Access data
print(f"High priority enrichment: {report['enrichment_summary']['high_priority']}")
print(f"Complete contacts: {report['enrichment_summary']['complete_contacts']}")
print(f"Duplicate groups: {report['duplicate_summary']['total_duplicates_found']}")


# 8️⃣ EXPORT RESULTS
# ─────────────────────────────────────────────────────────────────────────
# Save to JSON
manager.save_results(
    filename="hr_contacts.json",
    format="json",
    contacts=results  # Optional, defaults to last search results
)

# Save to CSV
manager.save_results(
    filename="hr_contacts.csv",
    format="csv"
)

# Save analysis report
manager.save_report(filename="analysis.json")

# Or export as string
json_str = manager.export_results(format="json")
csv_str = manager.export_results(format="csv")


# 9️⃣ FULL MPLOYER WORKFLOW
# ─────────────────────────────────────────────────────────────────────────
from Back_End.mployer_scraper import MployerScraper

# 1. Search Mployer
scraper = MployerScraper(username, password, headless=False)
scraper.initialize_browser()
scraper.login_to_mployer()
employers = scraper.search_employers(employees_min=50, employees_max=5000)

# 2. Extract HR contacts
manager = HRContactManager()
results = manager.search_from_employer_data(
    employers,
    PresetSearches.director_and_above()
)

# 3. Analyze
report = manager.generate_report()
print(f"Found {len(results)} HR directors+")
print(f"With email: {report['statistics']['with_email']}")

# 4. Export
manager.save_results(format="json")

scraper.close()


# 🔟 LOAD PREVIOUS RESULTS
# ─────────────────────────────────────────────────────────────────────────
manager.load_contacts_from_file("hr_contacts_20240205.json")

# Now you can search/filter previously loaded contacts
filtered = manager.search(params)


# ============================================================================
# SENIORITY LEVELS
# ============================================================================

# String values (for custom_search):
# "c_suite"              → Chief HR Officer, Chief People Officer
# "executive"            → VP, SVP of HR
# "director_and_above"   → Director level and above (default)
# "all"                  → All HR roles including managers

# Enum values (for builder):
from Back_End.hr_search_params import SeniorityLevel

SeniorityLevel.C_SUITE
SeniorityLevel.EXECUTIVE
SeniorityLevel.DIRECTOR
SeniorityLevel.SENIOR_MANAGER
SeniorityLevel.MANAGER
SeniorityLevel.ALL


# ============================================================================
# CONTACT DATA TYPES
# ============================================================================

from Back_End.hr_search_params import ContactDataType

ContactDataType.EMAIL              # Email address
ContactDataType.PHONE_DIRECT       # Direct phone line
ContactDataType.PHONE_MAIN         # Main/office line
ContactDataType.PHONE_MOBILE       # Mobile number
ContactDataType.PHONE_EXTENSION    # Extension (e.g., ext. 1234)
ContactDataType.LINKEDIN           # LinkedIn URL
ContactDataType.ANY_PHONE          # Any phone type


# ============================================================================
# FLUENT API EXAMPLES
# ============================================================================

# Find CHRO with full contact
params = (HRContactSearchBuilder()
    .c_suite_only()
    .require_complete_contact()
    .build())

# Find directors in specific locations
params = (HRContactSearchBuilder()
    .director_and_above()
    .with_locations("Baltimore", "Maryland")
    .require_email()
    .build())

# Find enrichment targets
params = (HRContactSearchBuilder()
    .all_hr_roles()
    .high_priority_enrichment()
    .require_email()
    .build())

# Mid-market companies only
params = (HRContactSearchBuilder()
    .director_and_above()
    .with_company_size(100, 2000)
    .require_email()
    .build())


# ============================================================================
# BUILDER METHODS (Fluent API)
# ============================================================================

builder = HRContactSearchBuilder()

# Seniority
.c_suite_only()
.executive_and_above()
.director_and_above()
.all_hr_roles()

# Company size
.with_company_size(min_size, max_size)

# Contact data required
.require_email()
.require_phone()
.require_linkedin()
.require_complete_contact()
.require_contact_data(ContactDataType.EMAIL, ...)

# Industries
.with_industries("Technology", "Finance")
.exclude_industries("Non-profit")

# Keywords to exclude
.exclude_keywords("consulting", "staffing", "temp")

# Data quality
.min_completeness(0.7)  # 0-1

# Enrichment
.needs_enrichment(True)
.high_priority_enrichment()
.by_enrichment_priority(min=1, max=3)

# Results
.limit(100)
.with_deduplication(True)


# ============================================================================
# CONTACT OBJECT PROPERTIES
# ============================================================================

contact.first_name              # "Sarah"
contact.last_name               # "Johnson"
contact.full_name               # "Sarah Johnson"
contact.job_title               # "Vice President of Human Resources"
contact.company_name            # "Tech Corp"
contact.company_id              # Optional

# Contact methods
contact.email                   # "sarah@techcorp.com"
contact.phone_direct            # "(410) 555-1234"
contact.phone_main              # "(410) 555-1000"
contact.phone_mobile            # "(410) 555-9999"
contact.phone_extension         # "ext. 4567"
contact.linkedin_url            # "https://linkedin.com/in/sarahjohnson"

# Data quality
contact.data_completeness       # 0.95 (float 0-1)
contact.contact_methods_count   # 5 (how many contact types have data)
contact.source                  # "mployer"

# Enrichment status
contact.needs_enrichment        # True/False
contact.enrichment_priority     # 0=none, 1=high, 2=medium, 3=low
contact.last_enrichment_date    # Optional date
contact.enrichment_notes        # ["Note 1", "Note 2"]

# Dates
contact.extracted_date          # ISO timestamp


# ============================================================================
# REPORT STRUCTURE
# ============================================================================

report = manager.generate_report()

# Statistics
report["statistics"]["total_contacts"]
report["statistics"]["unique_contacts"]
report["statistics"]["with_email"]
report["statistics"]["with_phone"]
report["statistics"]["with_linkedin"]
report["statistics"]["complete_contact_info"]
report["statistics"]["needing_enrichment"]
report["statistics"]["avg_completeness"]

# Deduplication
report["duplicate_summary"]["total_duplicates_found"]
report["duplicate_summary"]["total_records_merged"]
report["duplicate_summary"]["details"]  # List of duplicate groups

# Enrichment
report["enrichment_summary"]["high_priority"]
report["enrichment_summary"]["medium_priority"]
report["enrichment_summary"]["low_priority"]
report["enrichment_summary"]["complete_contacts"]

# Details
report["high_priority_enrichment_targets"]  # List of contacts


# ============================================================================
# COMMON SCENARIOS
# ============================================================================

# Scenario 1: "I want VPs and C-suite with email and phone"
contacts = find_hr_contacts(
    employer_data=employers,
    seniority="executive",
    require_email=True,
    require_phone=True
)

# Scenario 2: "Find HR directors in our state with complete contact info"
from Back_End.hr_search_params import HRContactSearchBuilder, ContactDataType

params = (HRContactSearchBuilder()
    .director_and_above()
    .with_locations("Maryland")
    .require_contact_data(
        ContactDataType.EMAIL,
        ContactDataType.ANY_PHONE,
        ContactDataType.LINKEDIN
    )
    .build())

manager = HRContactManager()
results = manager.search_from_employer_data(employers, params)

# Scenario 3: "Which contacts are missing LinkedIn info?"
no_linkedin = [c for c in manager.contacts if not c.linkedin_url and c.email]

# Scenario 4: "Export high priority enrichment targets"
targets = manager.get_enrichment_targets("high")
manager.save_results(format="csv", contacts=targets)

# Scenario 5: "Find duplicates in our database"
manager.load_contacts_from_file("our_database.json")
duplicates = manager.get_duplicate_groups()
for group in duplicates:
    print(f"Keep {group[0].full_name}, merge others")

# Scenario 6: "Get analytics on our contact database"
stats = manager.get_statistics()
print(f"Database has {stats['total_contacts']} contacts")
print(f"{stats['avg_completeness']*100:.0f}% average data completeness")
print(f"{stats['complete_contact_info']} contacts have all 3 data types")


# ============================================================================
# ENRICHMENT PRIORITY REFERENCE
# ============================================================================

# Priority 0: No enrichment needed (≥90% complete)
#   └─ Action: Use as-is, ready for outreach

# Priority 1: HIGH (< 30% complete)
#   └─ Action: Need basic contact info, difficult to reach
#   └─ Example: Has name only, no email/phone/LinkedIn

# Priority 2: MEDIUM (30-60% complete)
#   └─ Action: Missing some contact methods
#   └─ Example: Has email, but no phone or LinkedIn

# Priority 3: LOW (60-90% complete)
#   └─ Action: Almost complete, minor gaps
#   └─ Example: Has email and phone, but no LinkedIn


# ============================================================================
# COMPLETENESS SCORING
# ============================================================================

# Contact completeness is calculated from:
# - Full name: +1.0
# - Email: +1.5
# - Any phone: +1.0
# - LinkedIn: +1.0
# - Job title: +1.0
# - Company: +0.5
# - Extension: +0.5
# ─────────────────
# Max: 7.0 points = 100%

# Examples:
# Name + Email + Job + Company = 3.5 / 7.0 = 50%
# Full profile = 7.0 / 7.0 = 100%


# ============================================================================
# ERROR HANDLING
# ============================================================================

try:
    contacts = find_hr_contacts(employer_data, max_results=-1)  # Invalid
except ValueError as e:
    print(f"Invalid parameter: {e}")

try:
    manager.load_contacts_from_file("nonexistent.json")
except FileNotFoundError:
    print("File not found")

try:
    contacts = manager.get_enrichment_targets("invalid_priority")
except ValueError:
    print("Unknown priority level")


# ============================================================================
# PERFORMANCE TIPS
# ============================================================================

# 1. For large datasets (10k+ contacts):
#    Use limit() in search params
results = (HRContactSearchBuilder()
    .director_and_above()
    .limit(500)  # ← Limit results
    .build())

# 2. Batch processing:
#    Process in chunks rather than all at once
batch_size = 1000
for i in range(0, len(all_data), batch_size):
    batch = all_data[i:i+batch_size]
    manager.search_from_employer_data(batch, params)

# 3. Caching search results:
#    Store results to avoid re-processing
manager.save_results(format="json")
manager.load_contacts_from_file("cached.json")


# ============================================================================
# FILE EXPORTS
# ============================================================================

# Default locations
# JSON: hr_contacts/hr_contacts_<timestamp>.json
# CSV:  hr_contacts/hr_contacts_<timestamp>.csv
# Reports: hr_contacts/hr_analysis_report_<timestamp>.json

# Custom location
from pathlib import Path
manager.storage_path = Path("my_exports")
manager.save_results()

# Check what was created
import os
os.listdir("hr_contacts")

