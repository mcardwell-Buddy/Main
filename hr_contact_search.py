"""
HR Contact Search CLI Interface

Command-line interface for finding and managing HR contacts.
"""

import os
import sys
import json
import logging
from typing import Dict, List, Optional
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import after path setup
from backend.mployer_scraper import MployerScraper
from backend.hr_contact_manager import HRContactManager, find_hr_contacts, PresetSearches
from backend.hr_search_params import SeniorityLevel, ContactDataType


class HRContactSearchCLI:
    """Interactive CLI for HR contact search and analysis"""
    
    def __init__(self):
        self.manager = HRContactManager()
        self.scraper = None
        self.employer_data = []
    
    def run(self):
        """Run interactive CLI"""
        print("\n" + "="*60)
        print("  HR CONTACT FINDER & ENRICHMENT ANALYZER")
        print("="*60)
        print("\nFind HR managers and above with contact data")
        print("Analyzes duplicates and enrichment opportunities\n")
        
        while True:
            self._show_menu()
            choice = input("\nEnter command (1-9): ").strip()
            
            if choice == "1":
                self._step_mployer_search()
            elif choice == "2":
                self._step_search_contacts()
            elif choice == "3":
                self._step_analyze_results()
            elif choice == "4":
                self._step_export_contacts()
            elif choice == "5":
                self._step_view_duplicates()
            elif choice == "6":
                self._step_enrichment_targets()
            elif choice == "7":
                self._step_load_existing()
            elif choice == "8":
                self._step_quick_preset_search()
            elif choice == "9":
                print("\n✓ Exiting...")
                break
            else:
                print("Invalid choice. Try again.")
    
    def _show_menu(self):
        """Display main menu"""
        print("\n" + "-"*60)
        print("MAIN MENU")
        print("-"*60)
        print("1. Search Mployer for employers (get raw data)")
        print("2. Find HR contacts (from loaded employer data)")
        print("3. Analyze results (report & statistics)")
        print("4. Export contacts (to JSON/CSV)")
        print("5. View duplicate groups")
        print("6. Find enrichment targets")
        print("7. Load existing contacts from file")
        print("8. Quick preset search")
        print("9. Exit")
        print("-"*60)
    
    def _step_mployer_search(self):
        """Search Mployer for employer data"""
        print("\n" + "="*60)
        print("STEP 1: MPLOYER SEARCH")
        print("="*60)
        
        username = os.getenv("MPLOYER_USERNAME")
        password = os.getenv("MPLOYER_PASSWORD")
        
        if not username or not password:
            print("❌ Mployer credentials not set in .env file")
            print("Set MPLOYER_USERNAME and MPLOYER_PASSWORD")
            return
        
        try:
            self.scraper = MployerScraper(username, password, headless=False)
            self.scraper.initialize_browser()
            
            print("\n1. Logging in...")
            if not self.scraper.login_to_mployer():
                print("❌ Login failed")
                return
            
            print("✓ Logged in")
            
            print("\n2. Configure search parameters:")
            company_size_min = int(input("   Min employees (default 50): ") or "50")
            company_size_max = int(input("   Max employees (default 5000): ") or "5000")
            
            print("\n3. Running search...")
            employers = self.scraper.search_employers(
                employees_min=company_size_min,
                employees_max=company_size_max
            )
            
            print(f"\n✓ Found {len(employers)} employers")
            
            self.employer_data = employers
            
            # Save raw data
            timestamp = __import__('datetime').datetime.now().strftime("%Y%m%d_%H%M%S")
            with open(f"mployer_raw_data_{timestamp}.json", 'w') as f:
                json.dump(employers, f, indent=2)
            
            print(f"✓ Raw data saved to mployer_raw_data_{timestamp}.json")
            
            self.scraper.close()
            
        except Exception as e:
            print(f"❌ Error: {e}")
            if self.scraper:
                self.scraper.close()
    
    def _step_search_contacts(self):
        """Search for HR contacts"""
        print("\n" + "="*60)
        print("STEP 2: FIND HR CONTACTS")
        print("="*60)
        
        if not self.employer_data:
            print("❌ No employer data loaded. Run step 1 first or load from file.")
            return
        
        print("\nSearch parameters:")
        print("1. Seniority level:")
        print("   a) C-Suite only")
        print("   b) VP and above")
        print("   c) Director and above (default)")
        print("   d) All HR roles")
        
        seniority_choice = input("\nChoose seniority (a-d): ").strip().lower()
        
        seniority_map = {
            "a": "c_suite",
            "b": "executive",
            "c": "director_and_above",
            "d": "all",
        }
        seniority = seniority_map.get(seniority_choice, "director_and_above")
        
        print("\n2. Required contact data:")
        require_email = input("   Require email? (y/n, default y): ").strip().lower() != "n"
        require_phone = input("   Require phone? (y/n, default n): ").strip().lower() == "y"
        require_linkedin = input("   Require LinkedIn? (y/n, default n): ").strip().lower() == "y"
        
        max_results = input("   Max results (default unlimited): ").strip()
        max_results = int(max_results) if max_results else None
        
        print("\nSearching...")
        
        require_data = []
        if require_email:
            require_data.append("email")
        if require_phone:
            require_data.append("phone")
        if require_linkedin:
            require_data.append("linkedin")
        
        params = PresetSearches.custom_search(
            seniority=seniority,
            require_data=require_data if require_data else None,
            max_results=max_results,
        )
        
        results = self.manager.search_from_employer_data(self.employer_data, params)
        
        print(f"\n✓ Found {len(results)} matching HR contacts")
        
        if results:
            print("\nTop 5 results:")
            for i, contact in enumerate(results[:5], 1):
                print(f"\n  {i}. {contact.full_name}")
                print(f"     Company: {contact.company_name}")
                print(f"     Title: {contact.job_title}")
                print(f"     Email: {contact.email or 'N/A'}")
                print(f"     Phone: {contact.phone_direct or contact.phone_main or 'N/A'}")
                print(f"     LinkedIn: {contact.linkedin_url or 'N/A'}")
                print(f"     Completeness: {contact.data_completeness*100:.1f}%")
    
    def _step_analyze_results(self):
        """Analyze results and generate report"""
        print("\n" + "="*60)
        print("STEP 3: ANALYZE RESULTS")
        print("="*60)
        
        if not self.manager.contacts:
            print("❌ No contacts to analyze. Run step 2 first.")
            return
        
        print("Generating analysis report...")
        report = self.manager.generate_report()
        
        print("\n📊 STATISTICS:")
        stats = report["statistics"]
        print(f"  Total contacts: {stats['total_contacts']}")
        print(f"  With email: {stats['with_email']}")
        print(f"  With phone: {stats['with_phone']}")
        print(f"  With LinkedIn: {stats['with_linkedin']}")
        print(f"  Complete contact info: {stats['complete_contact_info']}")
        print(f"  Average completeness: {stats['avg_completeness']*100:.1f}%")
        
        print("\n🔄 DEDUPLICATION:")
        dupl = report["duplicate_summary"]
        print(f"  Duplicate groups found: {dupl['total_duplicates_found']}")
        print(f"  Records merged: {dupl['total_records_merged']}")
        
        print("\n📈 ENRICHMENT NEEDS:")
        enrich = report["enrichment_summary"]
        print(f"  High priority: {enrich['high_priority']}")
        print(f"  Medium priority: {enrich['medium_priority']}")
        print(f"  Low priority: {enrich['low_priority']}")
        print(f"  Complete contacts: {enrich['complete_contacts']}")
        
        print("\n💾 Saving full report...")
        filepath = self.manager.save_report()
        print(f"✓ Report saved to: {filepath}")
    
    def _step_export_contacts(self):
        """Export contacts to file"""
        print("\n" + "="*60)
        print("STEP 4: EXPORT CONTACTS")
        print("="*60)
        
        if not self.manager.last_search_results and not self.manager.contacts:
            print("❌ No contacts to export.")
            return
        
        contacts = self.manager.last_search_results or self.manager.contacts
        
        print("\nExport format:")
        print("1. JSON")
        print("2. CSV")
        
        choice = input("Choose format (1-2): ").strip()
        format_map = {"1": "json", "2": "csv"}
        format_type = format_map.get(choice, "json")
        
        filepath = self.manager.save_results(format=format_type, contacts=contacts)
        print(f"\n✓ Exported {len(contacts)} contacts to: {filepath}")
    
    def _step_view_duplicates(self):
        """View duplicate groups"""
        print("\n" + "="*60)
        print("STEP 5: DUPLICATE GROUPS")
        print("="*60)
        
        duplicates = self.manager.get_duplicate_groups()
        
        if not duplicates:
            print("✓ No duplicates found")
            return
        
        print(f"\nFound {len(duplicates)} duplicate groups:\n")
        
        for i, group in enumerate(duplicates[:10], 1):
            print(f"{i}. {group[0].company_name}")
            print(f"   {len(group)} duplicate records:")
            for contact in group:
                print(f"   - {contact.full_name}")
                if contact.email:
                    print(f"     Email: {contact.email}")
                if contact.phone_direct or contact.phone_main:
                    print(f"     Phone: {contact.phone_direct or contact.phone_main}")
            print()
    
    def _step_enrichment_targets(self):
        """Find enrichment targets"""
        print("\n" + "="*60)
        print("STEP 6: ENRICHMENT TARGETS")
        print("="*60)
        
        high = self.manager.get_enrichment_targets("high")
        medium = self.manager.get_enrichment_targets("medium")
        
        print(f"\n🔴 HIGH PRIORITY ({len(high)} contacts):")
        for contact in high[:10]:
            print(f"  • {contact.full_name}")
            print(f"    {contact.company_name} | {contact.job_title}")
            print(f"    Completeness: {contact.data_completeness*100:.1f}%")
            print(f"    Missing: {', '.join(self.manager._get_missing_fields(contact))}")
            print()
        
        print(f"\n🟡 MEDIUM PRIORITY ({len(medium)} contacts):")
        for contact in medium[:5]:
            print(f"  • {contact.full_name} ({contact.company_name})")
            print(f"    Missing: {', '.join(self.manager._get_missing_fields(contact))}")
    
    def _step_load_existing(self):
        """Load contacts from file"""
        print("\n" + "="*60)
        print("STEP 7: LOAD EXISTING CONTACTS")
        print("="*60)
        
        filepath = input("Enter file path: ").strip()
        
        if not Path(filepath).exists():
            print(f"❌ File not found: {filepath}")
            return
        
        try:
            self.manager.load_contacts_from_file(filepath)
            print(f"✓ Loaded {len(self.manager.contacts)} contacts")
        except Exception as e:
            print(f"❌ Error loading file: {e}")
    
    def _step_quick_preset_search(self):
        """Quick preset search"""
        print("\n" + "="*60)
        print("STEP 8: QUICK PRESET SEARCH")
        print("="*60)
        
        if not self.employer_data:
            print("❌ No employer data loaded.")
            return
        
        print("\nAvailable presets:")
        print("1. CHRO with email or phone")
        print("2. VP of HR with full contact (email, phone, LinkedIn)")
        print("3. Mid-market HR directors (100-2000 employees)")
        print("4. High priority enrichment targets")
        
        choice = input("\nChoose preset (1-4): ").strip()
        
        preset_map = {
            "1": "chro_with_contact",
            "2": "vp_hr_full_contact",
            "3": "mid_market_directors",
            "4": "enrichment_targets",
        }
        
        preset_name = preset_map.get(choice)
        if not preset_name:
            print("Invalid choice")
            return
        
        params = self.manager.get_preset_search(preset_name)
        results = self.manager.search_from_employer_data(self.employer_data, params)
        
        print(f"\n✓ Found {len(results)} contacts matching preset")
        
        for contact in results[:5]:
            print(f"\n  {contact.full_name}")
            print(f"  {contact.company_name} | {contact.job_title}")
            print(f"  {contact.email or 'No email'}")


def main():
    """Main entry point"""
    cli = HRContactSearchCLI()
    cli.run()


if __name__ == "__main__":
    main()
