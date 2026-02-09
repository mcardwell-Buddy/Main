"""
HR Contact Search Examples

Demonstrates how to use the HR contact finding system programmatically.
"""

import json
import logging
from backend.mployer_scraper import MployerScraper
from backend.hr_contact_manager import HRContactManager, find_hr_contacts, PresetSearches
from backend.hr_search_params import HRContactSearchBuilder, SeniorityLevel, ContactDataType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# EXAMPLE 1: Quick Find HR Contacts
# ============================================================================
def example_quick_find():
    """
    Quick example: Find HR contacts with minimal parameters
    """
    print("\n" + "="*70)
    print("EXAMPLE 1: Quick Find HR Contacts")
    print("="*70)
    
    # Load employer data (from Mployer or another source)
    with open("sample_employer_data.json", "r") as f:
        employer_data = json.load(f)
    
    # Find HR contacts
    contacts = find_hr_contacts(
        employer_data=employer_data,
        seniority="director_and_above",
        require_email=True,
        require_phone=False,
        max_results=100
    )
    
    print(f"\nFound {len(contacts)} HR contacts")
    
    # Display results
    for contact in contacts[:5]:
        print(f"\n  {contact.full_name}")
        print(f"  {contact.company_name} | {contact.job_title}")
        print(f"  Email: {contact.email}")
        print(f"  Completeness: {contact.data_completeness*100:.1f}%")


# ============================================================================
# EXAMPLE 2: Advanced Search with Builder
# ============================================================================
def example_advanced_search():
    """
    Advanced example: Use fluent API to build complex search
    """
    print("\n" + "="*70)
    print("EXAMPLE 2: Advanced Search with Builder")
    print("="*70)
    
    manager = HRContactManager()
    
    # Load employer data
    with open("sample_employer_data.json", "r") as f:
        employer_data = json.load(f)
    
    # Build advanced search
    search_params = (HRContactSearchBuilder()
                    .director_and_above()
                    .with_company_size(100, 5000)
                    .require_contact_data(
                        ContactDataType.EMAIL,
                        ContactDataType.ANY_PHONE,
                        ContactDataType.LINKEDIN
                    )
                    .exclude_keywords("outsource", "staffing", "temp")
                    .limit(100)
                    .build())
    
    # Search
    results = manager.search_from_employer_data(employer_data, search_params)
    
    print(f"\nFound {len(results)} matching contacts")
    
    # Show statistics
    stats = manager.get_statistics()
    print(f"\nStatistics:")
    print(f"  Total: {stats['total_contacts']}")
    print(f"  With email: {stats['with_email']}")
    print(f"  With phone: {stats['with_phone']}")
    print(f"  With LinkedIn: {stats['with_linkedin']}")
    print(f"  Average completeness: {stats['avg_completeness']*100:.1f}%")


# ============================================================================
# EXAMPLE 3: Find Enrichment Targets
# ============================================================================
def example_enrichment_targets():
    """
    Find contacts that need data enrichment
    """
    print("\n" + "="*70)
    print("EXAMPLE 3: Find Enrichment Targets")
    print("="*70)
    
    manager = HRContactManager()
    
    # Load employer data
    with open("sample_employer_data.json", "r") as f:
        employer_data = json.load(f)
    
    # Search with enrichment focus
    params = PresetSearches.high_priority_enrichment_targets()
    results = manager.search_from_employer_data(employer_data, params)
    
    # Get high priority targets
    high_priority = manager.get_enrichment_targets("high")
    
    print(f"\nFound {len(high_priority)} high priority enrichment targets")
    
    for contact in high_priority[:10]:
        print(f"\n  {contact.full_name}")
        print(f"  {contact.company_name}")
        print(f"  Completeness: {contact.data_completeness*100:.1f}%")
        print(f"  Has: email={bool(contact.email)}, phone={bool(contact.phone_direct or contact.phone_main)}, linkedin={bool(contact.linkedin_url)}")
        missing = [
            field for field in ["email", "phone", "linkedin"]
            if field == "email" and not contact.email
            or field == "phone" and not (contact.phone_direct or contact.phone_main)
            or field == "linkedin" and not contact.linkedin_url
        ]
        if missing:
            print(f"  Missing: {', '.join(missing)}")


# ============================================================================
# EXAMPLE 4: Analyze Duplicates
# ============================================================================
def example_analyze_duplicates():
    """
    Identify and analyze duplicate contacts
    """
    print("\n" + "="*70)
    print("EXAMPLE 4: Analyze Duplicates")
    print("="*70)
    
    manager = HRContactManager()
    
    # Load employer data
    with open("sample_employer_data.json", "r") as f:
        employer_data = json.load(f)
    
    # Extract and deduplicate
    contacts = manager.extractor.extract_batch(employer_data)
    unique = manager.extractor.deduplicate()
    
    duplicates = manager.get_duplicate_groups()
    
    print(f"\nDuplicate Analysis:")
    print(f"  Original records: {len(contacts)}")
    print(f"  Unique contacts: {len(unique)}")
    print(f"  Duplicate groups: {len(duplicates)}")
    
    print(f"\nTop duplicate groups:")
    for i, group in enumerate(duplicates[:5], 1):
        print(f"\n  {i}. {group[0].company_name}")
        print(f"     {len(group)} duplicate records merged into 1")
        for j, contact in enumerate(group[:3]):
            print(f"       • {contact.full_name} ({contact.email or 'no email'})")


# ============================================================================
# EXAMPLE 5: Search from Mployer
# ============================================================================
def example_mployer_search():
    """
    Full workflow: Search Mployer → Extract HR contacts → Analyze
    """
    print("\n" + "="*70)
    print("EXAMPLE 5: Full Workflow - Mployer to HR Contacts")
    print("="*70)
    
    import os
    
    username = os.getenv("MPLOYER_USERNAME")
    password = os.getenv("MPLOYER_PASSWORD")
    
    if not username or not password:
        print("❌ Mployer credentials not set. Skipping this example.")
        return
    
    try:
        # Step 1: Initialize scraper
        print("\n1. Initializing Mployer scraper...")
        scraper = MployerScraper(username, password, headless=False)
        scraper.initialize_browser()
        
        # Step 2: Login
        print("2. Logging in...")
        if not scraper.login_to_mployer():
            print("❌ Login failed")
            return
        
        # Step 3: Search
        print("3. Searching for employers (50-5000 employees)...")
        employers = scraper.search_employers(
            employees_min=50,
            employees_max=5000
        )
        print(f"   Found {len(employers)} employers")
        
        # Step 4: Extract HR contacts
        print("4. Extracting HR contacts...")
        manager = HRContactManager()
        
        params = PresetSearches.director_and_above()
        contacts = manager.search_from_employer_data(employers, params)
        
        print(f"   Found {len(contacts)} HR contacts")
        
        # Step 5: Analyze
        print("5. Analyzing contacts...")
        report = manager.generate_report()
        
        print(f"\n   Statistics:")
        print(f"   - With email: {report['statistics']['with_email']}")
        print(f"   - With phone: {report['statistics']['with_phone']}")
        print(f"   - With LinkedIn: {report['statistics']['with_linkedin']}")
        
        # Step 6: Identify enrichment targets
        print(f"\n   Enrichment targets:")
        print(f"   - High priority: {report['enrichment_summary']['high_priority']}")
        print(f"   - Medium priority: {report['enrichment_summary']['medium_priority']}")
        print(f"   - Complete: {report['enrichment_summary']['complete_contacts']}")
        
        # Step 7: Export
        print("\n6. Exporting results...")
        filepath = manager.save_results(format="json")
        print(f"   ✓ Saved to {filepath}")
        
        scraper.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")


# ============================================================================
# EXAMPLE 6: Custom Search with Fluent API
# ============================================================================
def example_custom_fluent_search():
    """
    Create custom search using fluent builder API
    """
    print("\n" + "="*70)
    print("EXAMPLE 6: Custom Search with Fluent API")
    print("="*70)
    
    manager = HRContactManager()
    
    # Load employer data
    with open("sample_employer_data.json", "r") as f:
        employer_data = json.load(f)
    
    # Build custom search
    params = (manager.create_search_builder()
              .executive_and_above()  # VP and C-suite
              .with_company_size(500, 50000)  # Large companies
              .require_contact_data(
                  ContactDataType.EMAIL,
                  ContactDataType.LINKEDIN
              )
              .exclude_keywords("non-profit", "government")
              .min_completeness(0.7)  # At least 70% complete
              .limit(50)
              .build())
    
    results = manager.search_from_employer_data(employer_data, params)
    
    print(f"\nFound {len(results)} executive-level HR contacts in large companies")
    
    for contact in results[:3]:
        print(f"\n  {contact.full_name}")
        print(f"  {contact.company_name} | {contact.job_title}")
        print(f"  Email: {contact.email}")
        print(f"  LinkedIn: {contact.linkedin_url}")


# ============================================================================
# EXAMPLE 7: Export and Save Results
# ============================================================================
def example_export_results():
    """
    Export contacts in different formats
    """
    print("\n" + "="*70)
    print("EXAMPLE 7: Export Results")
    print("="*70)
    
    manager = HRContactManager()
    
    # Load employer data
    with open("sample_employer_data.json", "r") as f:
        employer_data = json.load(f)
    
    # Search
    params = PresetSearches.mid_market_hr_directors()
    results = manager.search_from_employer_data(employer_data, params)
    
    # Export to JSON
    print("\n1. Exporting to JSON...")
    json_path = manager.save_results(format="json")
    print(f"   ✓ Saved to {json_path}")
    
    # Export to CSV
    print("2. Exporting to CSV...")
    csv_path = manager.save_results(format="csv")
    print(f"   ✓ Saved to {csv_path}")
    
    # Save analysis report
    print("3. Saving analysis report...")
    report_path = manager.save_report()
    print(f"   ✓ Saved to {report_path}")


# ============================================================================
# Main Runner
# ============================================================================
def main():
    """Run examples"""
    
    print("\n" + "="*70)
    print("HR CONTACT FINDER - USAGE EXAMPLES")
    print("="*70)
    
    print("\nSelect an example to run:")
    print("1. Quick find HR contacts")
    print("2. Advanced search with builder")
    print("3. Find enrichment targets")
    print("4. Analyze duplicates")
    print("5. Full Mployer workflow (requires credentials)")
    print("6. Custom search with fluent API")
    print("7. Export results")
    
    choice = input("\nEnter choice (1-7): ").strip()
    
    examples = {
        "1": example_quick_find,
        "2": example_advanced_search,
        "3": example_enrichment_targets,
        "4": example_analyze_duplicates,
        "5": example_mployer_search,
        "6": example_custom_fluent_search,
        "7": example_export_results,
    }
    
    example_func = examples.get(choice)
    if example_func:
        try:
            example_func()
        except FileNotFoundError as e:
            print(f"\n⚠️  {e}")
            print("Make sure you have sample_employer_data.json in the current directory")
        except Exception as e:
            print(f"\n❌ Error: {e}")
    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()
