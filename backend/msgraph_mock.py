"""
Mock MS Graph Email Client for dry-run testing and development

Simulates Microsoft Graph API for email without requiring live API access.
Activated via DRY_RUN=true environment variable.
"""

import os
import json
from typing import Dict, List, Optional
from datetime import datetime, timezone, timedelta
import random
import string


class MsGraphMock:
    """Mock MS Graph client for email operations"""
    
    def __init__(self, dry_run: bool = True, user_id: str = "mock_user"):
        self.dry_run = dry_run or os.getenv('DRY_RUN', 'false').lower() == 'true'
        self.user_id = user_id
        self.is_authenticated = True  # Always authenticated in mock
        self.mailbox = {}  # In-memory mailbox storage
        self.message_counter = 0
        self.init_mock_emails()
    
    def init_mock_emails(self):
        """Initialize mock emails in mailbox"""
        senders = ["alice@example.com", "bob@example.com", "carol@example.com"]
        subjects = [
            "Project update",
            "Meeting notes",
            "Budget review",
            "Action items",
            "Weekly summary"
        ]
        
        for i in range(5):
            message_id = f"msg_{''.join(random.choices(string.ascii_lowercase + string.digits, k=12))}"
            self.mailbox[message_id] = {
                "id": message_id,
                "subject": random.choice(subjects) + f" #{i}",
                "from": {
                    "emailAddress": {
                        "address": random.choice(senders),
                        "name": "Sender Name"
                    }
                },
                "body": {
                    "contentType": "html",
                    "content": f"<p>Mock email body {i}</p>"
                },
                "receivedDateTime": (datetime.now(timezone.utc) - timedelta(days=i)).isoformat(),
                "isRead": random.choice([True, False]),
                "hasAttachments": random.choice([True, False])
            }
    
    def send_email(self, to_recipients: List[str], subject: str, body: str, 
                   cc_recipients: List[str] = None, bcc_recipients: List[str] = None) -> Dict:
        """Mock send email"""
        if not self.is_authenticated:
            return {"success": False, "error": "Not authenticated"}
        
        # Validate recipients
        if not to_recipients or not isinstance(to_recipients, list):
            return {
                "success": False,
                "error": "Invalid recipient list",
                "error_code": 400
            }
        
        # Simulate network timeout (2% chance)
        if random.random() < 0.02:
            return {
                "success": False,
                "error": "Request timeout",
                "error_code": 408
            }
        
        # Simulate rate limiting (1% chance)
        if random.random() < 0.01:
            return {
                "success": False,
                "error": "Rate limit exceeded",
                "retry_after": 300,
                "error_code": 429
            }
        
        # Generate mock message ID
        message_id = f"msg_{''.join(random.choices(string.ascii_lowercase + string.digits, k=12))}"
        
        return {
            "success": True,
            "message_id": message_id,
            "to_recipients": to_recipients,
            "cc_recipients": cc_recipients or [],
            "bcc_recipients": bcc_recipients or [],
            "subject": subject,
            "sent_at": datetime.now(timezone.utc).isoformat(),
            "status": "sent",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def get_messages(self, limit: int = 10, skip: int = 0, filter_str: str = None) -> Dict:
        """Mock get messages from mailbox"""
        if not self.is_authenticated:
            return {"success": False, "error": "Not authenticated"}
        
        all_messages = list(self.mailbox.values())
        
        # Apply filter if provided
        if filter_str:
            all_messages = [m for m in all_messages if 
                           filter_str.lower() in m.get("subject", "").lower() or
                           filter_str.lower() in str(m.get("body", {})).lower()]
        
        paginated = all_messages[skip:skip+limit]
        
        return {
            "success": True,
            "total_count": len(all_messages),
            "returned_count": len(paginated),
            "messages": paginated,
            "pagination": {
                "limit": limit,
                "skip": skip,
                "total": len(all_messages)
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def read_message(self, message_id: str) -> Dict:
        """Mock read specific message"""
        if not self.is_authenticated:
            return {"success": False, "error": "Not authenticated"}
        
        if message_id not in self.mailbox:
            return {
                "success": False,
                "error": f"Message not found: {message_id}",
                "error_code": 404
            }
        
        message = self.mailbox[message_id]
        message["isRead"] = True
        
        return {
            "success": True,
            "message_id": message_id,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def search_messages(self, query: str, limit: int = 20) -> Dict:
        """Mock search messages"""
        if not self.is_authenticated:
            return {"success": False, "error": "Not authenticated"}
        
        # Simulate auth failure (1% chance)
        if random.random() < 0.01:
            return {
                "success": False,
                "error": "Unauthorized",
                "error_code": 401
            }
        
        results = []
        for msg_id, msg in self.mailbox.items():
            if (query.lower() in msg.get("subject", "").lower() or
                query.lower() in msg.get("from", {}).get("emailAddress", {}).get("address", "").lower() or
                query.lower() in str(msg.get("body", {})).lower()):
                results.append(msg)
                if len(results) >= limit:
                    break
        
        return {
            "success": True,
            "total_results": len(results),
            "results": results,
            "query": query,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def delete_message(self, message_id: str) -> Dict:
        """Mock delete message"""
        if not self.is_authenticated:
            return {"success": False, "error": "Not authenticated"}
        
        if message_id not in self.mailbox:
            return {
                "success": False,
                "error": f"Message not found: {message_id}",
                "error_code": 404
            }
        
        deleted_msg = self.mailbox.pop(message_id)
        
        return {
            "success": True,
            "message_id": message_id,
            "message": deleted_msg,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def reply_to_message(self, message_id: str, reply_body: str) -> Dict:
        """Mock reply to message"""
        if not self.is_authenticated:
            return {"success": False, "error": "Not authenticated"}
        
        if message_id not in self.mailbox:
            return {
                "success": False,
                "error": f"Message not found: {message_id}",
                "error_code": 404
            }
        
        # Generate mock reply message ID
        reply_id = f"reply_{''.join(random.choices(string.ascii_lowercase + string.digits, k=12))}"
        
        return {
            "success": True,
            "reply_id": reply_id,
            "parent_message_id": message_id,
            "reply_body": reply_body,
            "sent_at": datetime.now(timezone.utc).isoformat(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def test_connection(self) -> Dict:
        """Mock test API connection"""
        return {
            "success": True,
            "message": "Connection successful",
            "user_id": self.user_id,
            "api_version": "v1.0",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


def get_msgraph_client(dry_run: bool = True, user_id: str = ""):
    """Factory function to get MS Graph client (mock or real)"""
    if dry_run or os.getenv('DRY_RUN', 'false').lower() == 'true':
        return MsGraphMock(dry_run=True, user_id=user_id or "mock_user")
    else:
        # In production, would import real client
        raise NotImplementedError("Real MS Graph client requires production Azure credentials")
