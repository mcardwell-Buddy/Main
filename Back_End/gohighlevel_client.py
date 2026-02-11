"""
GoHighLevel API Client

Connects Buddy to your GHL CRM for contact management and outreach.
"""

import requests
import logging
import time
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


# Helper function to log external API usage
def _log_external_api(company: str, request_type: str, duration_ms: float = 0.0, cost_usd: float = 0.0):
    """Log external API usage for metrics"""
    try:
        from Back_End.whiteboard_metrics import log_external_api_usage
        log_external_api_usage(company, request_type, duration_ms, cost_usd)
    except Exception as e:
        logger.debug(f"Could not log API usage: {e}")


class GoHighLevelClient:
    """Client for GoHighLevel API v2"""
    
    def __init__(self, api_token: str, location_id: str = None):
        """
        Initialize GHL client.
        
        Args:
            api_token: Your GHL API token
            location_id: Your GHL location ID (optional, can be set per request)
        """
        self.api_token = api_token
        self.location_id = location_id
        self.base_url = "https://services.leadconnectorhq.com"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
            "Version": "2021-07-28"
        }

    def _request(self, method: str, path: str, params: Dict = None, data: Dict = None) -> Dict:
        """Generic request wrapper for GHL API."""
        url = f"{self.base_url}{path}"
        start_time = time.time()
        try:
            response = requests.request(method, url, params=params, json=data, headers=self.headers)
            response.raise_for_status()
            
            # Log API usage
            duration_ms = (time.time() - start_time) * 1000
            # Infer request type from path
            request_type = "contact_get"
            if "/contacts" in path:
                if method == "POST":
                    request_type = "contact_create"
                elif method == "PUT":
                    request_type = "contact_update"
                elif method == "DELETE":
                    request_type = "contact_delete"
            _log_external_api("GoHighLevel", request_type, duration_ms, 0.0)
            
            return {"success": True, "data": response.json()}
        except requests.exceptions.RequestException as e:
            error_detail = str(e)
            try:
                error_detail = f"{e} - Response: {e.response.text if hasattr(e, 'response') else 'No response'}"
            except Exception:
                pass
            logger.error(f"GHL request failed: {method} {path} - {error_detail}")
            return {"success": False, "error": error_detail}

    def _with_location(self, payload: Dict) -> Dict:
        if payload is None:
            payload = {}
        if self.location_id and "locationId" not in payload:
            payload["locationId"] = self.location_id
        return payload
    
    def add_contact(self, contact_data: Dict) -> Dict:
        """
        Add a new contact to GHL.
        
        Args:
            contact_data: {
                "firstName": "John",
                "lastName": "Doe",
                "email": "john@example.com",
                "phone": "+1234567890",
                "companyName": "Acme Corp",
                "tags": ["hr-manager", "tech-industry"],
                "customFields": {
                    "linkedin_url": "https://linkedin.com/in/...",
                    "job_title": "HR Manager",
                    "company_size": "100-500"
                },
                "source": "Buddy AI Research"
            }
        
        Returns:
            Response with contact ID
        """
        endpoint = f"{self.base_url}/contacts/"
        
        # Add location ID if provided
        contact_data = self._with_location(contact_data)
        
        try:
            response = requests.post(endpoint, json=contact_data, headers=self.headers)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"✓ Added contact: {contact_data.get('firstName')} {contact_data.get('lastName')} (ID: {result.get('contact', {}).get('id')})")
            
            return {
                "success": True,
                "contact_id": result.get("contact", {}).get("id"),
                "data": result
            }
        except requests.exceptions.RequestException as e:
            error_detail = str(e)
            try:
                error_detail = f"{e} - Response: {e.response.text if hasattr(e, 'response') else 'No response'}"
            except:
                pass
            logger.error(f"Failed to add contact: {error_detail}")
            return {
                "success": False,
                "error": error_detail
            }
    
    def update_contact(self, contact_id: str, updates: Dict) -> Dict:
        """
        Update existing contact.
        
        Args:
            contact_id: GHL contact ID
            updates: Fields to update
        
        Returns:
            Updated contact data
        """
        endpoint = f"{self.base_url}/contacts/{contact_id}"
        
        try:
            response = requests.put(endpoint, json=updates, headers=self.headers)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"✓ Updated contact: {contact_id}")
            
            return {
                "success": True,
                "data": result
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to update contact: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_contact(self, contact_id: str) -> Dict:
        """Get contact details by ID."""
        return self._request("GET", f"/contacts/{contact_id}")

    def list_contacts(self, query: str = None, limit: int = 50, offset: int = 0) -> Dict:
        """List contacts with optional query search."""
        params = {"limit": limit}
        # Note: GHL API v2 may not support offset parameter
        # Use skip or startAfterId instead if needed
        if query:
            params["query"] = query
        if self.location_id:
            params["locationId"] = self.location_id
        return self._request("GET", "/contacts/", params=params)
    
    def search_contacts(self, query: str) -> Dict:
        """
        Search for contacts by email, phone, or name.
        
        Args:
            query: Search query (email, phone, or name)
        
        Returns:
            List of matching contacts
        """
        endpoint = f"{self.base_url}/contacts/"
        params = {"query": query}
        
        if self.location_id:
            params["locationId"] = self.location_id
        
        try:
            response = requests.get(endpoint, params=params, headers=self.headers)
            response.raise_for_status()
            
            result = response.json()
            contacts = result.get("contacts", [])
            
            logger.info(f"✓ Found {len(contacts)} contacts matching '{query}'")
            
            return {
                "success": True,
                "contacts": contacts,
                "count": len(contacts)
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to search contacts: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def add_tag_to_contact(self, contact_id: str, tag: str) -> Dict:
        """
        Add a tag to a contact.
        
        Args:
            contact_id: GHL contact ID
            tag: Tag name to add
        
        Returns:
            Success status
        """
        endpoint = f"{self.base_url}/contacts/{contact_id}/tags"
        
        try:
            response = requests.post(endpoint, json={"tags": [tag]}, headers=self.headers)
            response.raise_for_status()
            
            logger.info(f"✓ Added tag '{tag}' to contact {contact_id}")
            
            return {
                "success": True
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to add tag: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_opportunity(self, opportunity_data: Dict) -> Dict:
        """
        Create a new opportunity/deal.
        
        Args:
            opportunity_data: {
                "contactId": "contact_123",
                "name": "Acme Corp - HR Services",
                "pipelineId": "pipeline_123",
                "pipelineStageId": "stage_123",
                "status": "open",
                "monetaryValue": 5000,
                "assignedTo": "user_id"
            }
        
        Returns:
            Opportunity ID
        """
        endpoint = f"{self.base_url}/opportunities/"
        
        opportunity_data = self._with_location(opportunity_data)
        
        try:
            response = requests.post(endpoint, json=opportunity_data, headers=self.headers)
            response.raise_for_status()
            
            result = response.json()
            opp_id = result.get("opportunity", {}).get("id")
            
            logger.info(f"✓ Created opportunity: {opportunity_data.get('name')} (ID: {opp_id})")
            
            return {
                "success": True,
                "opportunity_id": opp_id,
                "data": result
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create opportunity: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_task(self, task_data: Dict) -> Dict:
        """
        Create a task/reminder.
        
        Args:
            task_data: {
                "contactId": "contact_123",
                "title": "Follow up with HR manager",
                "body": "Send personalized message about...",
                "dueDate": "2026-02-10T10:00:00Z",
                "assignedTo": "user_id"
            }
        
        Returns:
            Task ID
        """
        endpoint = f"{self.base_url}/contacts/{task_data['contactId']}/tasks"
        
        try:
            response = requests.post(endpoint, json=task_data, headers=self.headers)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"✓ Created task: {task_data.get('title')}")
            
            return {
                "success": True,
                "task_id": result.get("id"),
                "data": result
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create task: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def update_opportunity(self, opportunity_id: str, updates: Dict) -> Dict:
        """Update an opportunity/deal."""
        endpoint = f"/opportunities/{opportunity_id}"
        return self._request("PUT", endpoint, data=self._with_location(updates))

    def move_opportunity_stage(self, opportunity_id: str, pipeline_stage_id: str) -> Dict:
        """Move an opportunity to another stage."""
        return self.update_opportunity(opportunity_id, {"pipelineStageId": pipeline_stage_id})

    def list_pipelines(self) -> Dict:
        """List pipelines."""
        params = {"locationId": self.location_id} if self.location_id else None
        return self._request("GET", "/opportunities/pipelines", params=params)

    def list_pipeline_stages(self, pipeline_id: str) -> Dict:
        """List stages for a pipeline."""
        return self._request("GET", f"/opportunities/pipelines/{pipeline_id}")

    # Conversations (SMS/Email/Chat)
    def list_conversations(self, status: str = None, limit: int = 50, offset: int = 0) -> Dict:
        params = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status
        if self.location_id:
            params["locationId"] = self.location_id
        return self._request("GET", "/conversations/", params=params)

    def get_conversation_messages(self, conversation_id: str, limit: int = 50) -> Dict:
        params = {"conversationId": conversation_id, "limit": limit}
        return self._request("GET", "/conversations/messages", params=params)

    def send_message(self, contact_id: str, message: str, msg_type: str = "SMS", subject: str = None, conversation_id: str = None) -> Dict:
        payload = {
            "contactId": contact_id,
            "type": msg_type,
            "message": message,
        }
        if subject:
            payload["subject"] = subject
        if conversation_id:
            payload["conversationId"] = conversation_id
        payload = self._with_location(payload)
        return self._request("POST", "/conversations/messages", data=payload)

    def update_conversation(self, conversation_id: str, updates: Dict) -> Dict:
        payload = self._with_location(updates)
        return self._request("PUT", f"/conversations/{conversation_id}", data=payload)

    # Calendars & appointments
    def list_calendars(self) -> Dict:
        params = {"locationId": self.location_id} if self.location_id else None
        return self._request("GET", "/calendars/", params=params)

    def get_calendar_availability(self, calendar_id: str, start: str, end: str) -> Dict:
        params = {"calendarId": calendar_id, "start": start, "end": end}
        return self._request("GET", "/calendars/availability", params=params)

    def create_appointment(self, appointment_data: Dict) -> Dict:
        payload = self._with_location(appointment_data)
        return self._request("POST", "/calendars/events", data=payload)

    def update_appointment(self, appointment_id: str, updates: Dict) -> Dict:
        payload = self._with_location(updates)
        return self._request("PUT", f"/calendars/events/{appointment_id}", data=payload)

    def cancel_appointment(self, appointment_id: str) -> Dict:
        return self._request("DELETE", f"/calendars/events/{appointment_id}")

    # Workflows
    def list_workflows(self) -> Dict:
        params = {"locationId": self.location_id} if self.location_id else None
        return self._request("GET", "/workflows/", params=params)

    def enroll_in_workflow(self, workflow_id: str, contact_id: str) -> Dict:
        payload = self._with_location({"contactId": contact_id})
        return self._request("POST", f"/workflows/{workflow_id}/enrollments", data=payload)

    def remove_from_workflow(self, workflow_id: str, enrollment_id: str) -> Dict:
        return self._request("DELETE", f"/workflows/{workflow_id}/enrollments/{enrollment_id}")

    def trigger_workflow(self, workflow_id: str, payload: Dict) -> Dict:
        payload = self._with_location(payload)
        return self._request("POST", f"/workflows/{workflow_id}/trigger", data=payload)

    # Forms & surveys
    def list_forms(self) -> Dict:
        params = {"locationId": self.location_id} if self.location_id else None
        return self._request("GET", "/forms/", params=params)

    def list_form_submissions(self, form_id: str = None, limit: int = 50) -> Dict:
        params = {"limit": limit}
        if form_id:
            params["formId"] = form_id
        if self.location_id:
            params["locationId"] = self.location_id
        return self._request("GET", "/forms/submissions", params=params)

    def list_surveys(self) -> Dict:
        params = {"locationId": self.location_id} if self.location_id else None
        return self._request("GET", "/surveys/", params=params)

    def list_survey_submissions(self, survey_id: str = None, limit: int = 50) -> Dict:
        params = {"limit": limit}
        if survey_id:
            params["surveyId"] = survey_id
        if self.location_id:
            params["locationId"] = self.location_id
        return self._request("GET", "/surveys/submissions", params=params)

    # Funnels & pages (metadata)
    def list_funnels(self) -> Dict:
        params = {"locationId": self.location_id} if self.location_id else None
        return self._request("GET", "/funnels/", params=params)

    def list_funnel_pages(self, funnel_id: str = None) -> Dict:
        params = {"locationId": self.location_id} if self.location_id else None
        if funnel_id:
            params["funnelId"] = funnel_id
        return self._request("GET", "/funnels/pages", params=params)

    # Campaigns & broadcasts
    def list_campaigns(self) -> Dict:
        params = {"locationId": self.location_id} if self.location_id else None
        return self._request("GET", "/campaigns/", params=params)

    def add_contact_to_campaign(self, campaign_id: str, contact_id: str) -> Dict:
        payload = self._with_location({"contactId": contact_id})
        return self._request("POST", f"/campaigns/{campaign_id}/contacts", data=payload)

    def update_campaign(self, campaign_id: str, updates: Dict) -> Dict:
        payload = self._with_location(updates)
        return self._request("PUT", f"/campaigns/{campaign_id}", data=payload)

    # Users & locations
    def list_users(self) -> Dict:
        params = {"locationId": self.location_id} if self.location_id else None
        return self._request("GET", "/users/", params=params)

    def list_locations(self) -> Dict:
        return self._request("GET", "/locations/")

    # Tags & custom fields
    def list_tags(self) -> Dict:
        params = {"locationId": self.location_id} if self.location_id else None
        return self._request("GET", "/tags/", params=params)

    def create_tag(self, name: str) -> Dict:
        payload = self._with_location({"name": name})
        return self._request("POST", "/tags/", data=payload)

    def list_custom_fields(self) -> Dict:
        params = {"locationId": self.location_id} if self.location_id else None
        return self._request("GET", "/custom-fields/", params=params)

    def create_custom_field(self, field_data: Dict) -> Dict:
        payload = self._with_location(field_data)
        return self._request("POST", "/custom-fields/", data=payload)

    # Webhooks
    def list_webhooks(self) -> Dict:
        params = {"locationId": self.location_id} if self.location_id else None
        return self._request("GET", "/webhooks/", params=params)

    def create_webhook(self, webhook_data: Dict) -> Dict:
        payload = self._with_location(webhook_data)
        return self._request("POST", "/webhooks/", data=payload)

    def delete_webhook(self, webhook_id: str) -> Dict:
        return self._request("DELETE", f"/webhooks/{webhook_id}")
    
    def add_note(self, contact_id: str, note: str) -> Dict:
        """
        Add a note to a contact.
        
        Args:
            contact_id: GHL contact ID
            note: Note content
        
        Returns:
            Success status
        """
        endpoint = f"{self.base_url}/contacts/{contact_id}/notes"
        
        try:
            response = requests.post(endpoint, json={"body": note}, headers=self.headers)
            response.raise_for_status()
            
            logger.info(f"✓ Added note to contact {contact_id}")
            
            return {
                "success": True
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to add note: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def bulk_import_contacts(self, contacts: List[Dict]) -> Dict:
        """
        Import multiple contacts at once.
        
        Args:
            contacts: List of contact data dictionaries
        
        Returns:
            Summary of import results
        """
        results = {
            "success": 0,
            "failed": 0,
            "errors": [],
            "contact_ids": []
        }
        
        for contact in contacts:
            result = self.add_contact(contact)
            
            if result["success"]:
                results["success"] += 1
                results["contact_ids"].append(result["contact_id"])
            else:
                results["failed"] += 1
                results["errors"].append({
                    "contact": contact,
                    "error": result["error"]
                })
        
        logger.info(f"✓ Bulk import complete: {results['success']} success, {results['failed']} failed")
        
        return results


# Global instance (will be initialized with your token)
ghl_client = None


def initialize_ghl(api_token: str, location_id: str = None):
    """Initialize the GoHighLevel client with your credentials"""
    global ghl_client
    ghl_client = GoHighLevelClient(api_token, location_id)
    logger.info("✓ GoHighLevel client initialized")
    return ghl_client

