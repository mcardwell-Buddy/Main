"""
Yahoo Email Client with OAuth 2.0 Authentication

Enables Buddy to:
- Send emails with attachments
- Receive and parse emails
- Comprehend email content using LLM
- Manage email threads

Uses Yahoo OAuth 2.0 for secure authentication.
"""

import os
import json
import base64
import mimetypes
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import imaplib
import smtplib
import email as email_lib
from pathlib import Path

# OAuth libraries
import requests
from requests.auth import HTTPBasicAuth


class YahooOAuthClient:
    """
    Manages Yahoo OAuth 2.0 authentication and token refresh.
    
    Setup Instructions:
    1. Go to https://developer.yahoo.com/apps/
    2. Create new app with Mail API access
    3. Get Client ID and Client Secret
    4. Set redirect URI: http://localhost:8080/oauth/callback
    """
    
    def __init__(self):
        self.config_path = Path("data/yahoo_oauth_config.json")
        self.tokens_path = Path("data/yahoo_tokens.json")
        self.config = self._load_config()
        self.tokens = self._load_tokens()
        
    def _load_config(self) -> Dict[str, str]:
        """Load Yahoo OAuth app credentials"""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                return json.load(f)
        return {
            "client_id": os.getenv("YAHOO_CLIENT_ID", ""),
            "client_secret": os.getenv("YAHOO_CLIENT_SECRET", ""),
            "redirect_uri": "http://localhost:8080/oauth/callback",
            "buddy_email": os.getenv("BUDDY_YAHOO_EMAIL", "")
        }
    
    def _load_tokens(self) -> Dict[str, Any]:
        """Load stored access/refresh tokens"""
        if self.tokens_path.exists():
            with open(self.tokens_path, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_tokens(self, tokens: Dict[str, Any]):
        """Persist tokens to disk"""
        self.tokens_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.tokens_path, 'w') as f:
            json.dump(tokens, f, indent=2)
        self.tokens = tokens
    
    def get_authorization_url(self) -> str:
        """
        Generate OAuth authorization URL for user to approve access.
        
        Returns:
            URL to open in browser for authorization
        """
        auth_url = "https://api.login.yahoo.com/oauth2/request_auth"
        params = {
            "client_id": self.config["client_id"],
            "redirect_uri": self.config["redirect_uri"],
            "response_type": "code",
            "scope": "mail-w mail-r",  # read and write mail
        }
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{auth_url}?{query_string}"
    
    def exchange_code_for_tokens(self, authorization_code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access/refresh tokens.
        
        Args:
            authorization_code: Code from OAuth callback
            
        Returns:
            Token response with access_token, refresh_token, expires_in
        """
        token_url = "https://api.login.yahoo.com/oauth2/get_token"
        
        data = {
            "grant_type": "authorization_code",
            "code": authorization_code,
            "redirect_uri": self.config["redirect_uri"]
        }
        
        auth = HTTPBasicAuth(
            self.config["client_id"],
            self.config["client_secret"]
        )
        
        response = requests.post(token_url, data=data, auth=auth)
        response.raise_for_status()
        
        tokens = response.json()
        tokens["obtained_at"] = datetime.utcnow().isoformat()
        tokens["expires_at"] = (
            datetime.utcnow() + timedelta(seconds=tokens["expires_in"])
        ).isoformat()
        
        self._save_tokens(tokens)
        return tokens
    
    def refresh_access_token(self) -> Dict[str, Any]:
        """
        Refresh expired access token using refresh token.
        
        Returns:
            New token response
        """
        if "refresh_token" not in self.tokens:
            raise ValueError("No refresh token available. Re-authenticate.")
        
        token_url = "https://api.login.yahoo.com/oauth2/get_token"
        
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.tokens["refresh_token"]
        }
        
        auth = HTTPBasicAuth(
            self.config["client_id"],
            self.config["client_secret"]
        )
        
        response = requests.post(token_url, data=data, auth=auth)
        response.raise_for_status()
        
        tokens = response.json()
        tokens["obtained_at"] = datetime.utcnow().isoformat()
        tokens["expires_at"] = (
            datetime.utcnow() + timedelta(seconds=tokens["expires_in"])
        ).isoformat()
        
        # Preserve refresh token if not returned
        if "refresh_token" not in tokens and "refresh_token" in self.tokens:
            tokens["refresh_token"] = self.tokens["refresh_token"]
        
        self._save_tokens(tokens)
        return tokens
    
    def get_valid_access_token(self) -> str:
        """
        Get a valid access token, refreshing if expired.
        
        Returns:
            Valid access token
        """
        if not self.tokens or "access_token" not in self.tokens:
            raise ValueError("No access token. Complete OAuth flow first.")
        
        # Check if token is expired (with 5 min buffer)
        expires_at = datetime.fromisoformat(self.tokens["expires_at"])
        if datetime.utcnow() >= expires_at - timedelta(minutes=5):
            print("🔄 Access token expired, refreshing...")
            self.refresh_access_token()
        
        return self.tokens["access_token"]


class YahooEmailClient:
    """
    Yahoo Email client for sending and receiving emails.
    
    Features:
    - Send plain text and HTML emails
    - Attach files (any type)
    - Fetch and parse incoming emails
    - Search emails by criteria
    - Mark emails as read/unread
    """
    
    def __init__(self):
        self.oauth_client = YahooOAuthClient()
        self.smtp_server = "smtp.mail.yahoo.com"
        self.smtp_port = 587
        self.imap_server = "imap.mail.yahoo.com"
        self.imap_port = 993
        
    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        attachments: Optional[List[str]] = None,
        cc: Optional[str] = None,
        bcc: Optional[str] = None,
        html: bool = False
    ) -> Dict[str, Any]:
        """
        Send an email with optional attachments.
        
        Args:
            to: Recipient email address
            subject: Email subject line
            body: Email body content
            attachments: List of file paths to attach
            cc: CC recipients (comma-separated)
            bcc: BCC recipients (comma-separated)
            html: If True, send as HTML email
            
        Returns:
            Status dict with success/failure info
        """
        try:
            # Get OAuth token
            access_token = self.oauth_client.get_valid_access_token()
            from_email = self.oauth_client.config["buddy_email"]
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = to
            msg['Subject'] = subject
            
            if cc:
                msg['Cc'] = cc
            if bcc:
                msg['Bcc'] = bcc
            
            # Attach body
            body_type = 'html' if html else 'plain'
            msg.attach(MIMEText(body, body_type))
            
            # Attach files
            if attachments:
                for file_path in attachments:
                    self._attach_file(msg, file_path)
            
            # Connect to SMTP with OAuth
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                
                # OAuth authentication
                auth_string = f"user={from_email}\x01auth=Bearer {access_token}\x01\x01"
                server.docmd("AUTH", "XOAUTH2 " + base64.b64encode(auth_string.encode()).decode())
                
                # Send email
                recipients = [to]
                if cc:
                    recipients.extend(cc.split(','))
                if bcc:
                    recipients.extend(bcc.split(','))
                
                server.send_message(msg)
            
            return {
                "success": True,
                "message": f"Email sent to {to}",
                "timestamp": datetime.utcnow().isoformat(),
                "attachments": len(attachments) if attachments else 0
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _attach_file(self, msg: MIMEMultipart, file_path: str):
        """Attach a file to email message"""
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Attachment not found: {file_path}")
        
        # Guess MIME type
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type is None:
            mime_type = 'application/octet-stream'
        
        main_type, sub_type = mime_type.split('/', 1)
        
        # Read file
        with open(file_path, 'rb') as f:
            attachment = MIMEBase(main_type, sub_type)
            attachment.set_payload(f.read())
        
        # Encode in base64
        encoders.encode_base64(attachment)
        
        # Add header
        attachment.add_header(
            'Content-Disposition',
            f'attachment; filename={path.name}'
        )
        
        msg.attach(attachment)
    
    def fetch_emails(
        self,
        folder: str = "INBOX",
        limit: int = 10,
        unread_only: bool = False,
        since_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch emails from mailbox.
        
        Args:
            folder: Mail folder (INBOX, Sent, etc.)
            limit: Maximum number of emails to fetch
            unread_only: Only fetch unread emails
            since_date: Only fetch emails since this date
            
        Returns:
            List of parsed email dicts
        """
        try:
            access_token = self.oauth_client.get_valid_access_token()
            email_address = self.oauth_client.config["buddy_email"]
            
            # Connect to IMAP
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            
            # OAuth authentication
            auth_string = f"user={email_address}\x01auth=Bearer {access_token}\x01\x01"
            mail.authenticate("XOAUTH2", lambda x: auth_string.encode())
            
            # Select folder
            mail.select(folder)
            
            # Build search criteria
            criteria = []
            if unread_only:
                criteria.append("UNSEEN")
            if since_date:
                date_str = since_date.strftime("%d-%b-%Y")
                criteria.append(f"SINCE {date_str}")
            
            search_query = " ".join(criteria) if criteria else "ALL"
            
            # Search emails
            _, message_numbers = mail.search(None, search_query)
            
            email_ids = message_numbers[0].split()
            email_ids = email_ids[-limit:]  # Get last N emails
            
            emails = []
            for email_id in reversed(email_ids):  # Newest first
                _, msg_data = mail.fetch(email_id, "(RFC822)")
                
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        email_obj = self._parse_email(response_part[1])
                        email_obj['id'] = email_id.decode()
                        emails.append(email_obj)
            
            mail.close()
            mail.logout()
            
            return emails
            
        except Exception as e:
            print(f"❌ Error fetching emails: {e}")
            return []
    
    def _parse_email(self, raw_email: bytes) -> Dict[str, Any]:
        """Parse raw email into structured dict"""
        msg = email_lib.message_from_bytes(raw_email)
        
        # Extract body
        body = ""
        html_body = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    body = part.get_payload(decode=True).decode()
                elif content_type == "text/html":
                    html_body = part.get_payload(decode=True).decode()
        else:
            body = msg.get_payload(decode=True).decode()
        
        return {
            "from": msg.get("From"),
            "to": msg.get("To"),
            "subject": msg.get("Subject"),
            "date": msg.get("Date"),
            "body": body,
            "html_body": html_body,
            "has_attachments": any(
                part.get_content_disposition() == "attachment"
                for part in msg.walk()
            )
        }
    
    def mark_as_read(self, email_id: str, folder: str = "INBOX"):
        """Mark an email as read"""
        try:
            access_token = self.oauth_client.get_valid_access_token()
            email_address = self.oauth_client.config["buddy_email"]
            
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            auth_string = f"user={email_address}\x01auth=Bearer {access_token}\x01\x01"
            mail.authenticate("XOAUTH2", lambda x: auth_string.encode())
            
            mail.select(folder)
            mail.store(email_id, '+FLAGS', '\\Seen')
            
            mail.close()
            mail.logout()
            
            return True
        except Exception as e:
            print(f"❌ Error marking email as read: {e}")
            return False


class EmailComprehensionEngine:
    """
    Uses LLM to understand and process email content.
    
    Capabilities:
    - Extract key information (requests, questions, action items)
    - Determine intent and urgency
    - Suggest responses
    - Identify attachments needed
    """
    
    def __init__(self):
        from backend.llm_client import llm_client
        self.llm = llm_client
    
    def comprehend_email(self, email: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze email content and extract understanding.
        
        Args:
            email: Parsed email dict
            
        Returns:
            Comprehension dict with intent, action items, sentiment, etc.
        """
        prompt = f"""Analyze this email and extract key information:

FROM: {email['from']}
SUBJECT: {email['subject']}
DATE: {email['date']}

BODY:
{email['body']}

Please provide:
1. **Intent**: What is the sender asking for or communicating?
2. **Action Items**: What specific actions does the sender want?
3. **Urgency**: Low, Medium, High, or Critical
4. **Sentiment**: Positive, Neutral, or Negative
5. **Questions**: List any direct questions asked
6. **Key Points**: Bullet list of main points
7. **Suggested Response**: How should Buddy respond?

Format as JSON:
{{
    "intent": "...",
    "action_items": ["...", "..."],
    "urgency": "...",
    "sentiment": "...",
    "questions": ["...", "..."],
    "key_points": ["...", "..."],
    "suggested_response": "..."
}}"""
        
        try:
            response = self.llm.complete(prompt, temperature=0.3)
            
            # Extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            json_str = response[json_start:json_end]
            
            comprehension = json.loads(json_str)
            comprehension['raw_email'] = email
            
            return comprehension
            
        except Exception as e:
            print(f"❌ Error comprehending email: {e}")
            return {
                "intent": "unknown",
                "action_items": [],
                "urgency": "medium",
                "sentiment": "neutral",
                "questions": [],
                "key_points": [],
                "suggested_response": "",
                "error": str(e),
                "raw_email": email
            }


# Singleton instances
_email_client = None
_comprehension_engine = None


def get_email_client() -> YahooEmailClient:
    """Get or create Yahoo email client singleton"""
    global _email_client
    if _email_client is None:
        _email_client = YahooEmailClient()
    return _email_client


def get_comprehension_engine() -> EmailComprehensionEngine:
    """Get or create email comprehension engine singleton"""
    global _comprehension_engine
    if _comprehension_engine is None:
        _comprehension_engine = EmailComprehensionEngine()
    return _comprehension_engine
