"""
HR Contact Search Parameters and Builder

Allows flexible parameter-based searches for HR contacts.
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class SeniorityLevel(Enum):
    """HR seniority levels"""
    C_SUITE = "c_suite"  # CHRO, Chief People Officer
    EXECUTIVE = "executive"  # VP level
    DIRECTOR = "director"  # Director level
    SENIOR_MANAGER = "senior_manager"  # Senior HR Manager
    MANAGER = "manager"  # HR Manager
    ALL = "all"


class ContactDataType(Enum):
    """Types of contact data"""
    EMAIL = "email"
    PHONE_DIRECT = "phone_direct"
    PHONE_MAIN = "phone_main"
    PHONE_MOBILE = "phone_mobile"
    PHONE_EXTENSION = "phone_extension"
    LINKEDIN = "linkedin"
    ANY_PHONE = "any_phone"


@dataclass
class HRContactSearchParams:
    """Parameters for searching HR contacts"""
    
    # Location parameters
    locations: List[str] = field(default_factory=list)
    
    # Company size parameters
    company_size_min: int = 0
    company_size_max: int = 1000000
    
    # Seniority level
    seniority_levels: List[SeniorityLevel] = field(
        default_factory=lambda: [SeniorityLevel.DIRECTOR, SeniorityLevel.EXECUTIVE, SeniorityLevel.C_SUITE]
    )
    
    # Required contact data types (at least one must be present)
    required_contact_types: List[ContactDataType] = field(
        default_factory=lambda: [ContactDataType.EMAIL]
    )
    
    # Industries to include (if any specified)
    industries: List[str] = field(default_factory=list)
    
    # Industries to exclude
    excluded_industries: List[str] = field(default_factory=list)
    
    # Keywords to exclude (company name, industry, etc)
    exclude_keywords: List[str] = field(default_factory=list)
    
    # Minimum data completeness (0-1)
    min_data_completeness: float = 0.0
    
    # Find only contacts needing enrichment
    needs_enrichment_only: bool = False
    
    # Enrichment priority level (0=not needed, 1=high, 2=medium, 3=low)
    enrichment_priority_min: Optional[int] = None
    enrichment_priority_max: Optional[int] = None
    
    # Remove duplicates before returning
    deduplicate: bool = True
    
    # Maximum results to return
    max_results: Optional[int] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "locations": self.locations,
            "company_size_min": self.company_size_min,
            "company_size_max": self.company_size_max,
            "seniority_levels": [s.value for s in self.seniority_levels],
            "required_contact_types": [c.value for c in self.required_contact_types],
            "industries": self.industries,
            "excluded_industries": self.excluded_industries,
            "exclude_keywords": self.exclude_keywords,
            "min_data_completeness": self.min_data_completeness,
            "needs_enrichment_only": self.needs_enrichment_only,
            "enrichment_priority_min": self.enrichment_priority_min,
            "enrichment_priority_max": self.enrichment_priority_max,
            "deduplicate": self.deduplicate,
            "max_results": self.max_results,
        }


class HRContactSearchBuilder:
    """Fluent builder for creating search parameters"""
    
    def __init__(self):
        self.params = HRContactSearchParams()
    
    def with_locations(self, *locations: str) -> 'HRContactSearchBuilder':
        """Add location filters (e.g., 'Baltimore, Maryland', 'New York')"""
        self.params.locations.extend(locations)
        return self
    
    def with_company_size(self, min_size: int = None, max_size: int = None) -> 'HRContactSearchBuilder':
        """Set company size range"""
        if min_size is not None:
            self.params.company_size_min = min_size
        if max_size is not None:
            self.params.company_size_max = max_size
        return self
    
    def with_seniority_levels(self, *levels: SeniorityLevel) -> 'HRContactSearchBuilder':
        """Set seniority levels to search for"""
        self.params.seniority_levels = list(levels)
        return self
    
    def c_suite_only(self) -> 'HRContactSearchBuilder':
        """Search only C-suite level HR executives"""
        self.params.seniority_levels = [SeniorityLevel.C_SUITE]
        return self
    
    def executive_and_above(self) -> 'HRContactSearchBuilder':
        """Search VP and C-suite level"""
        self.params.seniority_levels = [SeniorityLevel.C_SUITE, SeniorityLevel.EXECUTIVE]
        return self
    
    def director_and_above(self) -> 'HRContactSearchBuilder':
        """Search director level and above (default)"""
        self.params.seniority_levels = [SeniorityLevel.C_SUITE, SeniorityLevel.EXECUTIVE, SeniorityLevel.DIRECTOR]
        return self
    
    def all_hr_roles(self) -> 'HRContactSearchBuilder':
        """Include all HR roles"""
        self.params.seniority_levels = [
            SeniorityLevel.C_SUITE,
            SeniorityLevel.EXECUTIVE,
            SeniorityLevel.DIRECTOR,
            SeniorityLevel.SENIOR_MANAGER,
            SeniorityLevel.MANAGER,
        ]
        return self
    
    def require_contact_data(self, *data_types: ContactDataType) -> 'HRContactSearchBuilder':
        """Require at least one of these contact types"""
        self.params.required_contact_types = list(data_types)
        return self
    
    def require_email(self) -> 'HRContactSearchBuilder':
        """Require email addresses"""
        self.params.required_contact_types = [ContactDataType.EMAIL]
        return self
    
    def require_phone(self) -> 'HRContactSearchBuilder':
        """Require phone number (any type)"""
        self.params.required_contact_types = [ContactDataType.ANY_PHONE]
        return self
    
    def require_linkedin(self) -> 'HRContactSearchBuilder':
        """Require LinkedIn URL"""
        self.params.required_contact_types = [ContactDataType.LINKEDIN]
        return self
    
    def require_complete_contact(self) -> 'HRContactSearchBuilder':
        """Require email, phone, and LinkedIn"""
        self.params.required_contact_types = [
            ContactDataType.EMAIL,
            ContactDataType.ANY_PHONE,
            ContactDataType.LINKEDIN,
        ]
        return self
    
    def with_industries(self, *industries: str) -> 'HRContactSearchBuilder':
        """Include only specific industries"""
        self.params.industries.extend(industries)
        return self
    
    def exclude_industries(self, *industries: str) -> 'HRContactSearchBuilder':
        """Exclude specific industries"""
        self.params.excluded_industries.extend(industries)
        return self
    
    def exclude_keywords(self, *keywords: str) -> 'HRContactSearchBuilder':
        """Exclude companies/contacts with these keywords"""
        self.params.exclude_keywords.extend(keywords)
        return self
    
    def min_completeness(self, score: float) -> 'HRContactSearchBuilder':
        """Set minimum data completeness (0-1)"""
        self.params.min_data_completeness = max(0.0, min(1.0, score))
        return self
    
    def needs_enrichment(self, only: bool = True) -> 'HRContactSearchBuilder':
        """Filter to only contacts needing enrichment"""
        self.params.needs_enrichment_only = only
        return self
    
    def by_enrichment_priority(self, min_priority: int = None, max_priority: int = None) -> 'HRContactSearchBuilder':
        """Filter by enrichment priority (1=high, 2=medium, 3=low, 0=not needed)"""
        if min_priority is not None:
            self.params.enrichment_priority_min = min_priority
        if max_priority is not None:
            self.params.enrichment_priority_max = max_priority
        return self
    
    def high_priority_enrichment(self) -> 'HRContactSearchBuilder':
        """Only high priority enrichment targets"""
        self.params.enrichment_priority_min = 1
        self.params.enrichment_priority_max = 1
        return self
    
    def with_deduplication(self, deduplicate: bool = True) -> 'HRContactSearchBuilder':
        """Enable/disable deduplication"""
        self.params.deduplicate = deduplicate
        return self
    
    def limit(self, max_results: int) -> 'HRContactSearchBuilder':
        """Limit results to max_results"""
        self.params.max_results = max_results
        return self
    
    def build(self) -> HRContactSearchParams:
        """Build and return the search parameters"""
        return self.params


# Preset search configurations
class PresetSearches:
    """Common preset searches"""
    
    @staticmethod
    def chro_contacts_with_contact_data() -> HRContactSearchParams:
        """Find CHRO/Chief People Officers with email or phone"""
        return (HRContactSearchBuilder()
                .c_suite_only()
                .require_contact_data(ContactDataType.EMAIL, ContactDataType.ANY_PHONE)
                .build())
    
    @staticmethod
    def vp_hr_with_full_contact() -> HRContactSearchParams:
        """Find VP of HR with email, phone, and LinkedIn"""
        return (HRContactSearchBuilder()
                .executive_and_above()
                .require_complete_contact()
                .build())
    
    @staticmethod
    def mid_market_hr_directors() -> HRContactSearchParams:
        """Find HR directors in 100-2000 employee companies"""
        return (HRContactSearchBuilder()
                .director_and_above()
                .with_company_size(100, 2000)
                .require_email()
                .build())
    
    @staticmethod
    def high_priority_enrichment_targets() -> HRContactSearchParams:
        """Find contacts that need data enrichment"""
        return (HRContactSearchBuilder()
                .all_hr_roles()
                .high_priority_enrichment()
                .require_email()  # Must have at least email
                .build())
    
    @staticmethod
    def custom_search(
        locations: List[str] = None,
        seniority: str = "director_and_above",
        company_size_min: int = 50,
        company_size_max: int = 5000,
        require_data: List[str] = None,
        exclude_keywords: List[str] = None,
        max_results: int = None
    ) -> HRContactSearchParams:
        """
        Create a custom search with common parameters
        
        Args:
            locations: List of locations
            seniority: 'c_suite', 'executive', 'director_and_above', 'all'
            company_size_min: Minimum employees
            company_size_max: Maximum employees
            require_data: List of required data types ('email', 'phone', 'linkedin')
            exclude_keywords: Keywords to exclude
            max_results: Maximum results to return
        
        Returns:
            HRContactSearchParams
        """
        builder = HRContactSearchBuilder()
        
        if locations:
            builder.with_locations(*locations)
        
        builder.with_company_size(company_size_min, company_size_max)
        
        # Set seniority level
        if seniority == "c_suite":
            builder.c_suite_only()
        elif seniority == "executive":
            builder.executive_and_above()
        elif seniority == "director_and_above":
            builder.director_and_above()
        else:  # all
            builder.all_hr_roles()
        
        # Set required contact data
        if require_data:
            data_types = {
                'email': ContactDataType.EMAIL,
                'phone': ContactDataType.ANY_PHONE,
                'linkedin': ContactDataType.LINKEDIN,
            }
            types = [data_types[d] for d in require_data if d in data_types]
            if types:
                builder.require_contact_data(*types)
        
        # Add exclusions
        if exclude_keywords:
            builder.exclude_keywords(*exclude_keywords)
        
        # Set limit
        if max_results:
            builder.limit(max_results)
        
        return builder.build()

