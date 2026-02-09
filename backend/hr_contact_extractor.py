"""
HR Contact Extractor and Analyzer

Extracts HR manager and above level contacts with contact data,
deduplicates them, and identifies enrichment opportunities.
"""

import re
import logging
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime
from dataclasses import dataclass, field, asdict
import json

logger = logging.getLogger(__name__)

# HR-related job title keywords and hierarchy
HR_TITLES = {
    "executive": [
        "chief human resources officer",
        "chief people officer",
        "vp of human resources",
        "vice president of human resources",
        "vice president human resources",
        "vp hr",
        "svp human resources",
        "senior vice president",
    ],
    "director": [
        "director of human resources",
        "director hr",
        "director talent",
        "director people operations",
        "director organizational development",
    ],
    "manager_senior": [
        "senior hr manager",
        "senior human resources manager",
        "regional hr manager",
        "hr operations manager",
        "hr business partner",
    ],
    "manager": [
        "hr manager",
        "human resources manager",
        "hr specialist manager",
        "talent manager",
        "recruiting manager",
    ],
}

# Contact type keywords
CONTACT_TYPES = {
    "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    "linkedin": r'(?:https?://)?(?:www\.)?linkedin\.com/(?:in|company)/[\w-]+',
    "phone": r'(?:\+\d{1,3}[-.\s]?)?\(?[\d]{3}\)?[-.\s]?[\d]{3}[-.\s]?[\d]{4}|(?:\+\d{1,3}[-.\s]?)?[\d]{10,}',
    "mobile": r'(?:mobile|cell|m\.:|m:)\s*(?:\+\d{1,3}[-.\s]?)?(?:\(?[\d]{3}\)?[-.\s]?[\d]{3}[-.\s]?[\d]{4})',
    "mainline": r'(?:office|main|phone|tel|ph|p\.:|p:)\s*(?:\+\d{1,3}[-.\s]?)?(?:\(?[\d]{3}\)?[-.\s]?[\d]{3}[-.\s]?[\d]{4})',
    "extension": r'(?:ext|extension|x)\s*[\d]{2,5}|#[\d]{2,5}',
}


@dataclass
class ContactInfo:
    """Structured contact information"""
    first_name: str = ""
    last_name: str = ""
    full_name: str = ""
    job_title: str = ""
    company_name: str = ""
    company_id: Optional[str] = None
    
    # Contact methods
    email: Optional[str] = None
    phone_direct: Optional[str] = None
    phone_main: Optional[str] = None
    phone_extension: Optional[str] = None
    phone_mobile: Optional[str] = None
    linkedin_url: Optional[str] = None
    
    # Data metadata
    source: str = "mployer"
    extracted_date: str = field(default_factory=lambda: datetime.now().isoformat())
    data_completeness: float = 0.0  # 0-1 score of contact data
    contact_methods_count: int = 0
    
    # Enrichment tracking
    needs_enrichment: bool = False
    enrichment_priority: int = 0  # 1=high, 2=medium, 3=low, 0=not needed
    last_enrichment_date: Optional[str] = None
    enrichment_notes: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert to JSON"""
        return json.dumps(self.to_dict(), indent=2)
    
    def calculate_completeness(self) -> float:
        """Calculate data completeness score (0-1)"""
        score = 0.0
        max_score = 7.0  # Max points available
        
        if self.full_name:
            score += 1.0
        if self.email:
            score += 1.5
        if self.phone_direct or self.phone_main or self.phone_mobile:
            score += 1.0
        if self.linkedin_url:
            score += 1.0
        if self.company_name:
            score += 0.5
        if self.job_title:
            score += 1.0
        if self.phone_extension:
            score += 0.5
        
        self.data_completeness = min(1.0, score / max_score)
        self.contact_methods_count = sum([
            bool(self.email),
            bool(self.phone_direct),
            bool(self.phone_main),
            bool(self.phone_mobile),
            bool(self.linkedin_url),
        ])
        
        return self.data_completeness
    
    def set_enrichment_priority(self):
        """Determine enrichment priority based on missing data"""
        self.calculate_completeness()
        
        if self.data_completeness >= 0.9:
            self.enrichment_priority = 0
            self.needs_enrichment = False
        elif self.data_completeness >= 0.6:
            self.enrichment_priority = 3  # Low priority
            self.needs_enrichment = True
        elif self.data_completeness >= 0.3:
            self.enrichment_priority = 2  # Medium priority
            self.needs_enrichment = True
        else:
            self.enrichment_priority = 1  # High priority
            self.needs_enrichment = True
        
        return self.enrichment_priority


class HRContactExtractor:
    """Extract and analyze HR contacts from raw data"""
    
    def __init__(self):
        self.contacts: List[ContactInfo] = []
        self.duplicates: List[List[ContactInfo]] = []
        self.unique_contacts: List[ContactInfo] = []
    
    def is_hr_title(self, job_title: str) -> bool:
        """Check if job title is HR-related and manager level or above"""
        if not job_title:
            return False
        
        title_lower = job_title.lower().strip()
        
        # Check all HR title categories
        for category, titles in HR_TITLES.items():
            for hr_title in titles:
                if hr_title in title_lower:
                    return True
        
        return False
    
    def extract_contact_info(self, raw_data: Dict) -> Optional[ContactInfo]:
        """
        Extract structured contact from raw employer/contact data
        
        Args:
            raw_data: Raw data dictionary from scraper
            
        Returns:
            ContactInfo object or None if not HR role
        """
        # Check if this is an HR role
        job_title = raw_data.get("job_title", "") or raw_data.get("jobTitle", "")
        if not self.is_hr_title(job_title):
            return None
        
        contact = ContactInfo()
        
        # Basic info
        contact.first_name = raw_data.get("firstName", "") or raw_data.get("first_name", "")
        contact.last_name = raw_data.get("lastName", "") or raw_data.get("last_name", "")
        contact.full_name = f"{contact.first_name} {contact.last_name}".strip()
        contact.job_title = job_title
        contact.company_name = raw_data.get("companyName", "") or raw_data.get("company_name", "")
        contact.company_id = raw_data.get("company_id")
        contact.source = raw_data.get("source", "mployer")
        
        # Extract contact information
        self._extract_contact_methods(raw_data, contact)
        
        # Calculate completeness and enrichment priority
        contact.calculate_completeness()
        contact.set_enrichment_priority()
        
        return contact
    
    def _extract_contact_methods(self, raw_data: Dict, contact: ContactInfo):
        """Extract all contact methods from raw data"""
        
        # Email
        if raw_data.get("email"):
            contact.email = raw_data["email"]
        
        # LinkedIn
        linkedin = raw_data.get("linkedin_url") or raw_data.get("linkedinUrl")
        if linkedin:
            contact.linkedin_url = linkedin
        
        # Phone number variations
        phone_data = raw_data.get("phone_data", {})
        if isinstance(phone_data, str):
            # Parse phone string
            phone_data = self._parse_phone_string(phone_data)
        
        contact.phone_direct = phone_data.get("direct")
        contact.phone_main = phone_data.get("main")
        contact.phone_mobile = phone_data.get("mobile")
        contact.phone_extension = phone_data.get("extension")
        
        # Also check raw data fields
        if raw_data.get("phone"):
            contact.phone_direct = raw_data["phone"]
        if raw_data.get("phone_main"):
            contact.phone_main = raw_data["phone_main"]
        if raw_data.get("phone_mobile"):
            contact.phone_mobile = raw_data["phone_mobile"]
    
    def _parse_phone_string(self, phone_string: str) -> Dict[str, Optional[str]]:
        """Parse phone string and classify phone types"""
        result = {
            "direct": None,
            "main": None,
            "mobile": None,
            "extension": None,
        }
        
        # Extract mobile
        mobile_match = re.search(CONTACT_TYPES["mobile"], phone_string, re.IGNORECASE)
        if mobile_match:
            result["mobile"] = self._clean_phone(mobile_match.group(0))
        
        # Extract main/office line
        main_match = re.search(CONTACT_TYPES["mainline"], phone_string, re.IGNORECASE)
        if main_match:
            result["main"] = self._clean_phone(main_match.group(0))
        
        # Extract extension
        ext_match = re.search(CONTACT_TYPES["extension"], phone_string, re.IGNORECASE)
        if ext_match:
            result["extension"] = ext_match.group(0).strip()
        
        # Extract direct (raw phone number if not classified)
        if not (mobile_match or main_match):
            phone_match = re.search(CONTACT_TYPES["phone"], phone_string)
            if phone_match:
                result["direct"] = self._clean_phone(phone_match.group(0))
        
        return result
    
    def _clean_phone(self, phone: str) -> str:
        """Clean phone number to standard format"""
        # Remove common prefixes
        phone = re.sub(r'(?:mobile|cell|office|main|phone|tel|p\.:|m\.:|ext|extension|x)\s*[:\-]?\s*', 
                      '', phone, flags=re.IGNORECASE).strip()
        return phone
    
    def add_contact(self, contact: ContactInfo):
        """Add contact to list"""
        self.contacts.append(contact)
    
    def extract_batch(self, raw_data_list: List[Dict]) -> List[ContactInfo]:
        """Extract contacts from batch of raw data"""
        extracted = []
        for raw_data in raw_data_list:
            contact = self.extract_contact_info(raw_data)
            if contact:
                extracted.append(contact)
                self.add_contact(contact)
        
        logger.info(f"Extracted {len(extracted)} HR contacts from {len(raw_data_list)} records")
        return extracted
    
    def deduplicate(self, similarity_threshold: float = 0.85) -> List[ContactInfo]:
        """
        Identify duplicates and merge highest quality versions
        
        Args:
            similarity_threshold: Score (0-1) for considering matches duplicates
            
        Returns:
            List of unique contacts
        """
        if not self.contacts:
            return []
        
        self.duplicates = []
        processed = set()
        self.unique_contacts = []
        
        for i, contact1 in enumerate(self.contacts):
            if i in processed:
                continue
            
            duplicate_group = [contact1]
            
            for j in range(i + 1, len(self.contacts)):
                if j in processed:
                    continue
                
                contact2 = self.contacts[j]
                similarity = self._calculate_similarity(contact1, contact2)
                
                if similarity >= similarity_threshold:
                    duplicate_group.append(contact2)
                    processed.add(j)
            
            processed.add(i)
            
            if len(duplicate_group) > 1:
                self.duplicates.append(duplicate_group)
                # Merge - keep highest quality
                merged = self._merge_contacts(duplicate_group)
                self.unique_contacts.append(merged)
            else:
                self.unique_contacts.append(contact1)
        
        logger.info(f"Deduplication: {len(self.contacts)} → {len(self.unique_contacts)} unique contacts")
        logger.info(f"Found {len(self.duplicates)} duplicate groups")
        
        return self.unique_contacts
    
    def _calculate_similarity(self, contact1: ContactInfo, contact2: ContactInfo) -> float:
        """Calculate similarity score between two contacts (0-1)"""
        score = 0.0
        max_score = 0.0
        
        # Name similarity (strong indicator)
        if contact1.full_name and contact2.full_name:
            max_score += 2.0
            if contact1.full_name.lower() == contact2.full_name.lower():
                score += 2.0
            elif self._string_similarity(contact1.full_name.lower(), contact2.full_name.lower()) > 0.85:
                score += 1.5
        
        # Email match (very strong)
        if contact1.email and contact2.email and contact1.email.lower() == contact2.email.lower():
            max_score += 2.0
            score += 2.0
        
        # Phone match (very strong)
        phones1 = [contact1.phone_direct, contact1.phone_main, contact1.phone_mobile]
        phones2 = [contact2.phone_direct, contact2.phone_main, contact2.phone_mobile]
        phones1 = [p for p in phones1 if p]
        phones2 = [p for p in phones2 if p]
        
        if phones1 and phones2:
            max_score += 2.0
            if any(p1 == p2 for p1 in phones1 for p2 in phones2):
                score += 2.0
        
        # Company match
        if contact1.company_name and contact2.company_name:
            max_score += 1.0
            if contact1.company_name.lower() == contact2.company_name.lower():
                score += 1.0
        
        # LinkedIn match
        if contact1.linkedin_url and contact2.linkedin_url:
            max_score += 1.0
            if contact1.linkedin_url.lower() == contact2.linkedin_url.lower():
                score += 1.0
        
        if max_score == 0:
            return 0.0
        
        return score / max_score
    
    def _string_similarity(self, str1: str, str2: str) -> float:
        """Calculate string similarity using simple algorithm"""
        # Levenshtein-like approach
        if str1 == str2:
            return 1.0
        
        # Simple character overlap
        set1 = set(str1.replace(" ", ""))
        set2 = set(str2.replace(" ", ""))
        
        if not set1 or not set2:
            return 0.0
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union
    
    def _merge_contacts(self, duplicate_group: List[ContactInfo]) -> ContactInfo:
        """Merge duplicate contacts, keeping highest quality data"""
        # Sort by data completeness
        sorted_contacts = sorted(duplicate_group, 
                                key=lambda c: (c.data_completeness, c.contact_methods_count),
                                reverse=True)
        
        primary = sorted_contacts[0]
        
        # Fill in missing data from other duplicates
        for secondary in sorted_contacts[1:]:
            if not primary.email and secondary.email:
                primary.email = secondary.email
            if not primary.phone_direct and secondary.phone_direct:
                primary.phone_direct = secondary.phone_direct
            if not primary.phone_main and secondary.phone_main:
                primary.phone_main = secondary.phone_main
            if not primary.phone_mobile and secondary.phone_mobile:
                primary.phone_mobile = secondary.phone_mobile
            if not primary.phone_extension and secondary.phone_extension:
                primary.phone_extension = secondary.phone_extension
            if not primary.linkedin_url and secondary.linkedin_url:
                primary.linkedin_url = secondary.linkedin_url
        
        # Update metrics
        primary.calculate_completeness()
        primary.enrichment_notes.append(f"Merged {len(duplicate_group)} duplicate records")
        
        return primary
    
    def identify_enrichment_needs(self) -> Dict[str, List[ContactInfo]]:
        """Group contacts by enrichment priority"""
        result = {
            "high_priority": [],
            "medium_priority": [],
            "low_priority": [],
            "complete": [],
        }
        
        for contact in self.unique_contacts:
            if not contact.needs_enrichment:
                result["complete"].append(contact)
            elif contact.enrichment_priority == 1:
                result["high_priority"].append(contact)
            elif contact.enrichment_priority == 2:
                result["medium_priority"].append(contact)
            elif contact.enrichment_priority == 3:
                result["low_priority"].append(contact)
        
        logger.info(f"Enrichment needs: High={len(result['high_priority'])}, "
                   f"Medium={len(result['medium_priority'])}, "
                   f"Low={len(result['low_priority'])}, "
                   f"Complete={len(result['complete'])}")
        
        return result
    
    def generate_report(self) -> Dict:
        """Generate comprehensive analysis report"""
        enrichment_needs = self.identify_enrichment_needs()
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_contacts": len(self.unique_contacts),
                "duplicate_groups": len(self.duplicates),
                "contacts_needing_enrichment": len(enrichment_needs["high_priority"]) + 
                                              len(enrichment_needs["medium_priority"]) + 
                                              len(enrichment_needs["low_priority"]),
                "complete_contacts": len(enrichment_needs["complete"]),
            },
            "by_priority": {
                "high": len(enrichment_needs["high_priority"]),
                "medium": len(enrichment_needs["medium_priority"]),
                "low": len(enrichment_needs["low_priority"]),
                "complete": len(enrichment_needs["complete"]),
            },
            "contact_methods": {
                "with_email": len([c for c in self.unique_contacts if c.email]),
                "with_phone_direct": len([c for c in self.unique_contacts if c.phone_direct]),
                "with_phone_main": len([c for c in self.unique_contacts if c.phone_main]),
                "with_phone_mobile": len([c for c in self.unique_contacts if c.phone_mobile]),
                "with_linkedin": len([c for c in self.unique_contacts if c.linkedin_url]),
            },
            "duplicate_details": [
                {
                    "count": len(group),
                    "names": [c.full_name for c in group],
                    "company": group[0].company_name,
                }
                for group in self.duplicates
            ],
            "high_priority_enrichment": [
                {
                    "name": c.full_name,
                    "company": c.company_name,
                    "title": c.job_title,
                    "completeness": f"{c.data_completeness*100:.1f}%",
                    "contact_methods": c.contact_methods_count,
                    "missing": self._get_missing_fields(c),
                }
                for c in enrichment_needs["high_priority"][:20]  # Top 20
            ],
        }
        
        return report
    
    def _get_missing_fields(self, contact: ContactInfo) -> List[str]:
        """Get list of missing contact fields"""
        missing = []
        if not contact.email:
            missing.append("email")
        if not contact.phone_direct and not contact.phone_main and not contact.phone_mobile:
            missing.append("phone")
        if not contact.linkedin_url:
            missing.append("linkedin")
        return missing
    
    def export_contacts(self, contacts: Optional[List[ContactInfo]] = None, 
                       format: str = "json") -> str:
        """Export contacts to JSON or CSV format"""
        if contacts is None:
            contacts = self.unique_contacts
        
        if format == "json":
            return json.dumps([c.to_dict() for c in contacts], indent=2, default=str)
        elif format == "csv":
            return self._export_csv(contacts)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _export_csv(self, contacts: List[ContactInfo]) -> str:
        """Export contacts to CSV format"""
        lines = [
            "First Name,Last Name,Email,Phone Direct,Phone Main,Phone Mobile,Extension,"
            "LinkedIn,Company,Job Title,Completeness,Needs Enrichment,Enrichment Priority"
        ]
        
        for contact in contacts:
            lines.append(
                f'"{contact.first_name}","{contact.last_name}","{contact.email or ""}",'
                f'"{contact.phone_direct or ""}","{contact.phone_main or ""}","'
                f'{contact.phone_mobile or ""}","{contact.phone_extension or ""}",'
                f'"{contact.linkedin_url or ""}","{contact.company_name}","{contact.job_title}",'
                f'{contact.data_completeness:.2f},{contact.needs_enrichment},'
                f'{contact.enrichment_priority}'
            )
        
        return "\n".join(lines)
