"""
Mock Mployer Scraper for dry-run testing and development

Simulates Mployer automation without requiring live API access.
Activated via DRY_RUN=true environment variable.
"""

import os
import json
from typing import Dict, List, Optional
from datetime import datetime, timezone
import random


class MployerMock:
    """Mock Mployer client for safe testing"""
    
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run or os.getenv('DRY_RUN', 'false').lower() == 'true'
        self.logged_in = False
        self.is_authenticated = False
        
    def login(self, email: str, password: str) -> Dict:
        """Mock login to Mployer"""
        if not self.dry_run:
            raise RuntimeError("Mock client requires DRY_RUN=true")
        
        # Simulate login - 95% success rate
        if random.random() < 0.95:
            self.logged_in = True
            self.is_authenticated = True
            return {
                "success": True,
                "message": f"Logged in as {email}",
                "session_id": f"mock_session_{random.randint(1000, 9999)}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        else:
            # 5% failure rate (invalid credentials)
            return {
                "success": False,
                "message": "Invalid email or password",
                "error_code": 401,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    def search_contacts(self, 
                       first_name: str = None,
                       last_name: str = None,
                       email: str = None,
                       phone: str = None,
                       company: str = None,
                       industry: str = None,
                       city: str = None,
                       state: str = None,
                       country: str = None,
                       job_title: str = None,
                       skill: str = None) -> Dict:
        """Mock search contacts with multiple filters"""
        if not self.is_authenticated:
            return {"success": False, "error": "Not authenticated"}
        
        # Simulate rate limiting (5% chance)
        if random.random() < 0.05:
            return {
                "success": False,
                "error": "Rate limit exceeded",
                "retry_after": 60,
                "error_code": 429
            }
        
        # Determine search result count (3-10 contacts deterministically)
        filters_used = sum([
            first_name is not None,
            last_name is not None,
            email is not None,
            phone is not None,
            company is not None,
            industry is not None,
            city is not None,
            state is not None,
            country is not None,
            job_title is not None,
            skill is not None
        ])
        
        # More filters = fewer results
        result_count = max(3, 10 - filters_used)
        
        contacts = []
        for i in range(result_count):
            contact = {
                "id": f"contact_{random.randint(1000, 9999)}",
                "first_name": first_name or f"Contact{i}",
                "last_name": last_name or f"User{i}",
                "email": email or f"contact{i}@example.com",
                "phone": phone or f"+1-555-{random.randint(1000, 9999)}",
                "company": company or f"Company {i}",
                "job_title": job_title or "Manager",
                "industry": industry or "Technology",
                "location": {
                    "city": city or "San Francisco",
                    "state": state or "CA",
                    "country": country or "USA"
                },
                "verified": random.choice([True, True, True, False]),  # 75% verified
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
            contacts.append(contact)
        
        return {
            "success": True,
            "total_results": result_count,
            "contacts": contacts,
            "search_filters": {
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "phone": phone,
                "company": company,
                "industry": industry,
                "city": city,
                "state": state,
                "country": country,
                "job_title": job_title,
                "skill": skill
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def extract_contacts(self, search_results: Dict) -> List[Dict]:
        """Mock extract contacts from search results"""
        if not self.is_authenticated:
            return []
        
        extracted = []
        if search_results.get("success") and "contacts" in search_results:
            for contact in search_results["contacts"]:
                extracted.append({
                    "mployer_id": contact.get("id"),
                    "first_name": contact.get("first_name"),
                    "last_name": contact.get("last_name"),
                    "email": contact.get("email"),
                    "phone": contact.get("phone"),
                    "company": contact.get("company"),
                    "job_title": contact.get("job_title"),
                    "industry": contact.get("industry"),
                    "location": contact.get("location"),
                    "extraction_timestamp": datetime.now(timezone.utc).isoformat()
                })
        
        return extracted
    
    def add_to_gohighlevel(self, contacts: List[Dict], ghl_client) -> Dict:
        """Mock adding contacts to GoHighLevel"""
        if not self.is_authenticated:
            return {"success": False, "error": "Not authenticated"}
        
        added_count = 0
        failed_count = 0
        
        for contact in contacts:
            try:
                # Mock: 95% success rate for adding to GHL
                if random.random() < 0.95:
                    # Create GHL contact
                    ghl_result = ghl_client.create_contact({
                        "first_name": contact.get("first_name"),
                        "last_name": contact.get("last_name"),
                        "email": contact.get("email"),
                        "phone": contact.get("phone"),
                        "company": contact.get("company"),
                        "custom_field_mployer_id": contact.get("mployer_id")
                    })
                    if ghl_result.get("success"):
                        added_count += 1
                    else:
                        failed_count += 1
                else:
                    failed_count += 1
            except:
                failed_count += 1
        
        return {
            "success": True,
            "added_count": added_count,
            "failed_count": failed_count,
            "total_processed": len(contacts),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def logout(self) -> Dict:
        """Mock logout from Mployer"""
        self.logged_in = False
        self.is_authenticated = False
        return {
            "success": True,
            "message": "Logged out successfully",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


def get_mployer_client(dry_run: bool = True):
    """Factory function to get Mployer client (mock or real)"""
    if dry_run or os.getenv('DRY_RUN', 'false').lower() == 'true':
        return MployerMock(dry_run=True)
    else:
        # In production, would import real client
        raise NotImplementedError("Real Mployer client requires production API key")

