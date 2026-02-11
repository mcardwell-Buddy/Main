"""
HR Contact Manager

Main interface for searching, extracting, deduplicating, and enriching HR contacts.
"""

import logging
import json
from typing import Dict, List, Optional, Union
from datetime import datetime
from pathlib import Path

from Back_End.hr_contact_extractor import HRContactExtractor, ContactInfo
from Back_End.hr_search_params import HRContactSearchParams, HRContactSearchBuilder, PresetSearches, ContactDataType

logger = logging.getLogger(__name__)


class HRContactManager:
    """Unified interface for HR contact management"""
    
    def __init__(self, storage_path: str = "hr_contacts"):
        """
        Initialize HR Contact Manager
        
        Args:
            storage_path: Directory to store contact data and reports
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.extractor = HRContactExtractor()
        self.contacts: List[ContactInfo] = []
        self.search_params: Optional[HRContactSearchParams] = None
        self.last_search_results: List[ContactInfo] = []
    
    def search_from_employer_data(
        self,
        employer_data_list: List[Dict],
        search_params: Union[HRContactSearchParams, Dict, None] = None
    ) -> List[ContactInfo]:
        """
        Search for HR contacts in employer data
        
        Args:
            employer_data_list: List of employer/contact records from scraper
            search_params: HRContactSearchParams, dict, or None for no filtering
            
        Returns:
            List of matching HR contacts
        """
        # Extract HR contacts from raw data
        logger.info(f"Extracting HR contacts from {len(employer_data_list)} records...")
        extracted = self.extractor.extract_batch(employer_data_list)
        
        if not extracted:
            logger.warning("No HR contacts extracted from data")
            return []
        
        # Deduplicate
        logger.info("Deduplicating contacts...")
        unique = self.extractor.deduplicate()
        
        self.contacts = unique
        
        # Apply filters if params provided
        if search_params:
            logger.info("Applying search filters...")
            self.search_params = search_params
            filtered = self._apply_filters(unique, search_params)
        else:
            filtered = unique
        
        self.last_search_results = filtered
        
        logger.info(f"Search returned {len(filtered)} contacts")
        return filtered
    
    def _apply_filters(self, contacts: List[ContactInfo], 
                      params: HRContactSearchParams) -> List[ContactInfo]:
        """Apply search parameters to filter contacts"""
        
        filtered = contacts
        
        # Filter by location
        if params.locations:
            logger.debug(f"Filtering by locations: {params.locations}")
            # This would need location data in contacts
            # For now, skip location filtering
        
        # Filter by company size
        filtered = [c for c in filtered 
                   if hasattr(c, 'company_size') and 
                   params.company_size_min <= c.company_size <= params.company_size_max]
        
        # Filter by data completeness
        filtered = [c for c in filtered if c.data_completeness >= params.min_data_completeness]
        
        # Filter by required contact types
        if params.required_contact_types:
            filtered = self._filter_by_contact_types(filtered, params.required_contact_types)
        
        # Filter by exclude keywords
        if params.exclude_keywords:
            filtered = [c for c in filtered 
                       if not any(kw.lower() in c.company_name.lower() 
                                 for kw in params.exclude_keywords)]
        
        # Filter by enrichment needs
        if params.needs_enrichment_only:
            filtered = [c for c in filtered if c.needs_enrichment]
        
        # Filter by enrichment priority
        if params.enrichment_priority_min is not None:
            filtered = [c for c in filtered if c.enrichment_priority >= params.enrichment_priority_min]
        if params.enrichment_priority_max is not None:
            filtered = [c for c in filtered if c.enrichment_priority <= params.enrichment_priority_max]
        
        # Limit results
        if params.max_results:
            filtered = filtered[:params.max_results]
        
        return filtered
    
    def _filter_by_contact_types(self, contacts: List[ContactInfo],
                                 required_types: List[ContactDataType]) -> List[ContactInfo]:
        """Filter contacts by required contact data types"""
        
        def has_contact_type(contact: ContactInfo, contact_type: ContactDataType) -> bool:
            if contact_type == ContactDataType.EMAIL:
                return bool(contact.email)
            elif contact_type == ContactDataType.PHONE_DIRECT:
                return bool(contact.phone_direct)
            elif contact_type == ContactDataType.PHONE_MAIN:
                return bool(contact.phone_main)
            elif contact_type == ContactDataType.PHONE_MOBILE:
                return bool(contact.phone_mobile)
            elif contact_type == ContactDataType.PHONE_EXTENSION:
                return bool(contact.phone_extension)
            elif contact_type == ContactDataType.LINKEDIN:
                return bool(contact.linkedin_url)
            elif contact_type == ContactDataType.ANY_PHONE:
                return bool(contact.phone_direct or contact.phone_main or contact.phone_mobile)
            return False
        
        # Filter contacts that have at least one required type
        return [c for c in contacts if any(has_contact_type(c, t) for t in required_types)]
    
    def quick_search(self, location: str = None, 
                    seniority: str = "director_and_above",
                    company_size_min: int = 50,
                    company_size_max: int = 5000,
                    require_data: List[str] = None,
                    employer_data: List[Dict] = None) -> List[ContactInfo]:
        """
        Quick search with common parameters
        
        Args:
            location: Location to search
            seniority: Seniority level ('c_suite', 'executive', 'director_and_above', 'all')
            company_size_min: Min company size
            company_size_max: Max company size
            require_data: Required contact data types ('email', 'phone', 'linkedin')
            employer_data: Employer data to search
            
        Returns:
            List of matching HR contacts
        """
        locations = [location] if location else None
        
        params = PresetSearches.custom_search(
            locations=locations,
            seniority=seniority,
            company_size_min=company_size_min,
            company_size_max=company_size_max,
            require_data=require_data,
        )
        
        if employer_data:
            return self.search_from_employer_data(employer_data, params)
        else:
            return self.search(params)
    
    def search(self, params: HRContactSearchParams = None) -> List[ContactInfo]:
        """
        Search existing contacts with parameters
        
        Args:
            params: Search parameters
            
        Returns:
            Filtered contacts
        """
        if not params:
            return self.contacts
        
        self.search_params = params
        self.last_search_results = self._apply_filters(self.contacts, params)
        return self.last_search_results
    
    def create_search_builder(self) -> HRContactSearchBuilder:
        """Create a new search builder for fluent API"""
        return HRContactSearchBuilder()
    
    def get_preset_search(self, preset_name: str) -> HRContactSearchParams:
        """Get a preset search configuration"""
        presets = {
            "chro_with_contact": PresetSearches.chro_contacts_with_contact_data,
            "vp_hr_full_contact": PresetSearches.vp_hr_with_full_contact,
            "mid_market_directors": PresetSearches.mid_market_hr_directors,
            "enrichment_targets": PresetSearches.high_priority_enrichment_targets,
        }
        
        if preset_name not in presets:
            raise ValueError(f"Unknown preset: {preset_name}. Available: {list(presets.keys())}")
        
        return presets[preset_name]()
    
    def get_enrichment_targets(self, priority: str = "high") -> List[ContactInfo]:
        """
        Get contacts that need data enrichment
        
        Args:
            priority: 'high', 'medium', 'low', or 'any'
            
        Returns:
            List of contacts needing enrichment
        """
        enrichment_map = {
            "high": 1,
            "medium": 2,
            "low": 3,
        }
        
        if priority not in enrichment_map and priority != "any":
            raise ValueError(f"Unknown priority: {priority}")
        
        if priority == "any":
            return [c for c in self.contacts if c.needs_enrichment]
        else:
            p = enrichment_map[priority]
            return [c for c in self.contacts if c.enrichment_priority == p]
    
    def get_duplicate_groups(self) -> List[List[ContactInfo]]:
        """Get all duplicate contact groups"""
        return self.extractor.duplicates
    
    def get_statistics(self) -> Dict:
        """Get statistics about contacts"""
        return {
            "total_contacts": len(self.contacts),
            "unique_contacts": len(self.extractor.unique_contacts),
            "duplicate_groups": len(self.extractor.duplicates),
            "with_email": len([c for c in self.contacts if c.email]),
            "with_phone": len([c for c in self.contacts 
                              if c.phone_direct or c.phone_main or c.phone_mobile]),
            "with_linkedin": len([c for c in self.contacts if c.linkedin_url]),
            "complete_contact_info": len([c for c in self.contacts 
                                         if c.email and (c.phone_direct or c.phone_main or c.phone_mobile) 
                                         and c.linkedin_url]),
            "needing_enrichment": len([c for c in self.contacts if c.needs_enrichment]),
            "avg_completeness": sum(c.data_completeness for c in self.contacts) / len(self.contacts) 
                               if self.contacts else 0,
        }
    
    def generate_report(self, include_high_priority: int = 20) -> Dict:
        """Generate comprehensive report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "statistics": self.get_statistics(),
            "duplicate_summary": {
                "total_duplicates_found": len(self.extractor.duplicates),
                "total_records_merged": sum(len(g) for g in self.extractor.duplicates),
                "details": [
                    {
                        "count": len(group),
                        "names": [c.full_name for c in group],
                        "company": group[0].company_name,
                    }
                    for group in self.extractor.duplicates[:10]  # Top 10
                ]
            },
            "enrichment_summary": {
                "high_priority": len(self.get_enrichment_targets("high")),
                "medium_priority": len(self.get_enrichment_targets("medium")),
                "low_priority": len(self.get_enrichment_targets("low")),
                "complete_contacts": len([c for c in self.contacts if not c.needs_enrichment]),
            },
            "high_priority_enrichment_targets": [
                {
                    "name": c.full_name,
                    "company": c.company_name,
                    "title": c.job_title,
                    "completeness": f"{c.data_completeness*100:.1f}%",
                    "has_email": bool(c.email),
                    "has_phone": bool(c.phone_direct or c.phone_main or c.phone_mobile),
                    "has_linkedin": bool(c.linkedin_url),
                    "missing_fields": self._get_missing_fields(c),
                }
                for c in self.get_enrichment_targets("high")[:include_high_priority]
            ],
        }
        
        return report
    
    def _get_missing_fields(self, contact: ContactInfo) -> List[str]:
        """Get missing contact fields"""
        missing = []
        if not contact.email:
            missing.append("email")
        if not (contact.phone_direct or contact.phone_main or contact.phone_mobile):
            missing.append("phone")
        if not contact.linkedin_url:
            missing.append("linkedin")
        return missing
    
    def export_results(self, format: str = "json", 
                      contacts: List[ContactInfo] = None) -> str:
        """
        Export contacts to file
        
        Args:
            format: 'json' or 'csv'
            contacts: Contacts to export (defaults to last search results)
            
        Returns:
            Exported content as string
        """
        if contacts is None:
            contacts = self.last_search_results if self.last_search_results else self.contacts
        
        if format == "json":
            content = json.dumps([c.to_dict() for c in contacts], indent=2, default=str)
        elif format == "csv":
            content = self.extractor._export_csv(contacts)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        return content
    
    def save_results(self, filename: str = None, format: str = "json",
                    contacts: List[ContactInfo] = None) -> Path:
        """
        Save contacts to file
        
        Args:
            filename: Output filename (auto-generated if not specified)
            format: 'json' or 'csv'
            contacts: Contacts to save
            
        Returns:
            Path to saved file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            ext = "json" if format == "json" else "csv"
            filename = f"hr_contacts_{timestamp}.{ext}"
        
        filepath = self.storage_path / filename
        
        content = self.export_results(format, contacts)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Saved {len(contacts or self.last_search_results)} contacts to {filepath}")
        return filepath
    
    def save_report(self, filename: str = None) -> Path:
        """
        Save analysis report to file
        
        Args:
            filename: Output filename
            
        Returns:
            Path to saved file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"hr_analysis_report_{timestamp}.json"
        
        filepath = self.storage_path / filename
        
        report = self.generate_report()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Saved report to {filepath}")
        return filepath
    
    def load_contacts_from_file(self, filepath: str) -> List[ContactInfo]:
        """Load contacts from saved JSON file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            # List of contact dicts
            contacts = [self._dict_to_contact(d) for d in data]
        else:
            # Single contact dict
            contacts = [self._dict_to_contact(data)]
        
        self.contacts = contacts
        logger.info(f"Loaded {len(contacts)} contacts from {filepath}")
        return contacts
    
    def _dict_to_contact(self, data: Dict) -> ContactInfo:
        """Convert dictionary to ContactInfo"""
        contact = ContactInfo(
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name", ""),
            full_name=data.get("full_name", ""),
            job_title=data.get("job_title", ""),
            company_name=data.get("company_name", ""),
            email=data.get("email"),
            phone_direct=data.get("phone_direct"),
            phone_main=data.get("phone_main"),
            phone_mobile=data.get("phone_mobile"),
            phone_extension=data.get("phone_extension"),
            linkedin_url=data.get("linkedin_url"),
        )
        contact.calculate_completeness()
        contact.set_enrichment_priority()
        return contact


# Convenience functions for quick usage

def find_hr_contacts(
    employer_data: List[Dict],
    location: str = None,
    seniority: str = "director_and_above",
    require_email: bool = True,
    require_phone: bool = False,
    require_linkedin: bool = False,
    max_results: int = None
) -> List[ContactInfo]:
    """
    Quick function to find HR contacts
    
    Example:
        contacts = find_hr_contacts(
            employer_data=employers_from_mployer,
            location="Baltimore, Maryland",
            seniority="executive",
            require_email=True,
            require_phone=True,
            max_results=100
        )
    """
    manager = HRContactManager()
    
    require_data = []
    if require_email:
        require_data.append("email")
    if require_phone:
        require_data.append("phone")
    if require_linkedin:
        require_data.append("linkedin")
    
    params = PresetSearches.custom_search(
        locations=[location] if location else None,
        seniority=seniority,
        require_data=require_data if require_data else None,
        max_results=max_results,
    )
    
    return manager.search_from_employer_data(employer_data, params)


def analyze_hr_contacts(
    contacts: List[ContactInfo]
) -> Dict:
    """
    Analyze list of HR contacts and return report
    
    Example:
        report = analyze_hr_contacts(hr_contacts)
        print(f"High priority enrichment: {report['enrichment_summary']['high_priority']}")
    """
    manager = HRContactManager()
    manager.contacts = contacts
    manager.extractor.unique_contacts = contacts
    
    return manager.generate_report()

