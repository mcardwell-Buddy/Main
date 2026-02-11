"""
Mock GoHighLevel Client for dry-run testing and development

Simulates GoHighLevel API without requiring live API access.
Activated via DRY_RUN=true environment variable.
"""

import os
import json
from typing import Dict, List, Optional
from datetime import datetime, timezone
import random
import string


class GoHighLevelMock:
    """Mock GoHighLevel API client for safe testing"""
    
    def __init__(self, dry_run: bool = True, api_key: str = "mock_key"):
        self.dry_run = dry_run or os.getenv('DRY_RUN', 'false').lower() == 'true'
        self.api_key = api_key
        self.is_authenticated = True  # Always authenticated in mock
        self.contacts = {}  # In-memory contact storage
        
    def create_contact(self, contact_data: Dict) -> Dict:
        """Mock create contact in GoHighLevel"""
        if not self.is_authenticated:
            return {"success": False, "error": "Not authenticated"}
        
        # Simulate rate limiting (3% chance)
        if random.random() < 0.03:
            return {
                "success": False,
                "error": "Rate limit exceeded",
                "retry_after": 60,
                "error_code": 429
            }
        
        # Validate required fields
        required_fields = ["first_name", "last_name", "email"]
        missing_fields = [f for f in required_fields if f not in contact_data]
        if missing_fields:
            return {
                "success": False,
                "error": f"Missing required fields: {', '.join(missing_fields)}",
                "error_code": 400
            }
        
        # Generate mock contact ID
        contact_id = f"ghl_contact_{''.join(random.choices(string.ascii_lowercase + string.digits, k=12))}"
        
        # Store contact
        full_contact = {
            "id": contact_id,
            **contact_data,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        self.contacts[contact_id] = full_contact
        
        return {
            "success": True,
            "contact_id": contact_id,
            "message": f"Contact created successfully",
            "data": full_contact,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def search_contact(self, email: str = None, phone: str = None) -> Dict:
        """Mock search for contact"""
        if not self.is_authenticated:
            return {"success": False, "error": "Not authenticated"}
        
        # Simulate network timeout (2% chance)
        if random.random() < 0.02:
            return {
                "success": False,
                "error": "Request timeout",
                "error_code": 408
            }
        
        results = []
        
        # Search in mock contacts
        for contact_id, contact in self.contacts.items():
            if email and contact.get("email") == email:
                results.append(contact)
            elif phone and contact.get("phone") == phone:
                results.append(contact)
        
        # If not found and search would return results anyway (deterministic), create mock result
        if not results and (email or phone):
            results = [{
                "id": f"ghl_contact_{''.join(random.choices(string.ascii_lowercase, k=8))}",
                "first_name": "John",
                "last_name": "Doe",
                "email": email or "john@example.com",
                "phone": phone or "+1-555-0000",
                "created_at": datetime.now(timezone.utc).isoformat()
            }]
        
        return {
            "success": True,
            "total_results": len(results),
            "results": results,
            "search_criteria": {
                "email": email,
                "phone": phone
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def update_contact(self, contact_id: str, update_data: Dict) -> Dict:
        """Mock update contact"""
        if not self.is_authenticated:
            return {"success": False, "error": "Not authenticated"}
        
        # Simulate auth failure (1% chance)
        if random.random() < 0.01:
            return {
                "success": False,
                "error": "Unauthorized",
                "error_code": 401
            }
        
        if contact_id not in self.contacts:
            return {
                "success": False,
                "error": f"Contact not found: {contact_id}",
                "error_code": 404
            }
        
        # Update contact
        self.contacts[contact_id].update(update_data)
        self.contacts[contact_id]["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        return {
            "success": True,
            "contact_id": contact_id,
            "message": "Contact updated successfully",
            "data": self.contacts[contact_id],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def get_contact(self, contact_id: str) -> Dict:
        """Mock get contact details"""
        if not self.is_authenticated:
            return {"success": False, "error": "Not authenticated"}
        
        if contact_id not in self.contacts:
            return {
                "success": False,
                "error": f"Contact not found: {contact_id}",
                "error_code": 404
            }
        
        return {
            "success": True,
            "contact_id": contact_id,
            "data": self.contacts[contact_id],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def list_contacts(self, limit: int = 50, skip: int = 0) -> Dict:
        """Mock list all contacts"""
        if not self.is_authenticated:
            return {"success": False, "error": "Not authenticated"}
        
        all_contacts = list(self.contacts.values())
        paginated = all_contacts[skip:skip+limit]
        
        return {
            "success": True,
            "total_count": len(all_contacts),
            "returned_count": len(paginated),
            "contacts": paginated,
            "pagination": {
                "limit": limit,
                "skip": skip,
                "total": len(all_contacts)
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def delete_contact(self, contact_id: str) -> Dict:
        """Mock delete contact"""
        if not self.is_authenticated:
            return {"success": False, "error": "Not authenticated"}
        
        if contact_id not in self.contacts:
            return {
                "success": False,
                "error": f"Contact not found: {contact_id}",
                "error_code": 404
            }
        
        deleted_contact = self.contacts.pop(contact_id)
        
        return {
            "success": True,
            "contact_id": contact_id,
            "message": "Contact deleted successfully",
            "data": deleted_contact,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def test_connection(self) -> Dict:
        """Mock test API connection"""
        return {
            "success": True,
            "message": "Connection successful",
            "api_version": "2.0",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


def get_gohighlevel_client(dry_run: bool = True, api_key: str = ""):
    """Factory function to get GoHighLevel client (mock or real)"""
    if dry_run or os.getenv('DRY_RUN', 'false').lower() == 'true':
        return GoHighLevelMock(dry_run=True, api_key=api_key or "mock_key")
    else:
        # In production, would import real client
        raise NotImplementedError("Real GoHighLevel client requires production API key")

