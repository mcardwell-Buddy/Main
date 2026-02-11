"""
Email Tool for Buddy

Dual email sending tools:
1. Microsoft Graph API - For Michael Cardwell's professional work emails (Cardwell Associates)
2. Yahoo SMTP - For Buddy's personal/operational emails

Features:
- Template support
- Attachment support
- Scheduling integration
- HTML/plain text support

Author: Buddy Phase 2 Architecture Team
Date: February 11, 2026
"""

import os
import logging
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


# Template registry
EMAIL_TEMPLATES = {
    'greeting': {
        'subject': 'Hello from Buddy',
        'body': 'Hi {name},\n\nThis is an automated message from Buddy.\n\n{content}\n\nBest regards,\nBuddy'
    },
    'notification': {
        'subject': 'Notification: {title}',
        'body': 'Hi {name},\n\n{content}\n\nThis is an automated notification.\n\nBest regards,\nBuddy'
    },
    'report': {
        'subject': 'Report: {title}',
        'body': 'Hi {name},\n\nPlease find the report below:\n\n{content}\n\nBest regards,\nBuddy'
    },
    'custom': {
        'subject': '{subject}',
        'body': '{body}'
    }
}


def _log_external_api(company: str, request_type: str, duration_ms: float = 0.0, cost_usd: float = 0.0):
    """Log external API usage for metrics"""
    try:
        from Back_End.whiteboard_metrics import log_external_api_usage
        log_external_api_usage(company, request_type, duration_ms, cost_usd)
    except Exception as e:
        logger.debug(f"Could not log API usage: {e}")


class EmailSender:
    """
    Unified email sender using Microsoft Graph API.
    
    Features:
    - OAuth authentication
    - Template rendering
    - Attachment support
    - HTML/plain text
    """
    
    def __init__(self):
        """Initialize email sender with Microsoft Graph credentials"""
        self.client_id = os.getenv("MSGRAPH_CLIENT_ID")
        self.client_secret = os.getenv("MSGRAPH_CLIENT_SECRET")
        self.tenant_id = os.getenv("MSGRAPH_TENANT_ID")
        self.sender_email = os.getenv("EMAIL_IMAP_USER")
        
        if not all([self.client_id, self.tenant_id]):
            logger.warning("Missing Microsoft Graph credentials - email sending disabled")
            self.enabled = False
        else:
            self.enabled = True
        
        logger.info(f"EmailSender initialized: enabled={self.enabled}")
    
    def _get_access_token(self) -> Optional[str]:
        """Get Microsoft Graph access token for sending email"""
        try:
            import msal
            
            # Use ConfidentialClientApplication for app-only permissions
            app = msal.ConfidentialClientApplication(
                self.client_id,
                authority=f"https://login.microsoftonline.com/{self.tenant_id}",
                client_credential=self.client_secret
            )
            
            # Request token with Mail.Send scope
            result = app.acquire_token_for_client(
                scopes=["https://graph.microsoft.com/.default"]
            )
            
            if "access_token" in result:
                return result["access_token"]
            else:
                logger.error(f"Failed to acquire token: {result.get('error_description', 'Unknown error')}")
                return None
        except Exception as e:
            logger.error(f"Error getting access token: {e}")
            return None
    
    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        attachments: Optional[List[str]] = None,
        cc: Optional[str] = None,
        bcc: Optional[str] = None,
        html: bool = False,
        template: Optional[str] = None,
        template_vars: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Send an email via Microsoft Graph API.
        
        Args:
            to: Recipient email address (or comma-separated list)
            subject: Email subject
            body: Email body content
            attachments: List of file paths to attach
            cc: CC recipients (comma-separated)
            bcc: BCC recipients (comma-separated)
            html: If True, send as HTML email
            template: Template name from EMAIL_TEMPLATES
            template_vars: Variables to render in template
            
        Returns:
            Status dict with success/failure info
        """
        start_time = time.time()
        
        if not self.enabled:
            return {
                "success": False,
                "error": "Email sending disabled - missing Microsoft Graph credentials",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        try:
            # Apply template if specified
            if template and template in EMAIL_TEMPLATES:
                template_data = EMAIL_TEMPLATES[template]
                vars_dict = template_vars or {}
                subject = template_data['subject'].format(**vars_dict)
                body = template_data['body'].format(**vars_dict)
                logger.info(f"Applied template: {template}")
            
            # Get access token
            token = self._get_access_token()
            if not token:
                return {
                    "success": False,
                    "error": "Failed to acquire access token",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # Build email message
            message = {
                "message": {
                    "subject": subject,
                    "body": {
                        "contentType": "HTML" if html else "Text",
                        "content": body
                    },
                    "toRecipients": self._parse_recipients(to)
                }
            }
            
            # Add CC/BCC if specified
            if cc:
                message["message"]["ccRecipients"] = self._parse_recipients(cc)
            if bcc:
                message["message"]["bccRecipients"] = self._parse_recipients(bcc)
            
            # Add attachments if specified
            if attachments:
                message["message"]["attachments"] = self._build_attachments(attachments)
            
            # Send via Microsoft Graph API
            import requests
            
            graph_endpoint = f"https://graph.microsoft.com/v1.0/users/{self.sender_email}/sendMail"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                graph_endpoint,
                headers=headers,
                json=message
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 202:
                # Success (202 Accepted is the success code for sendMail)
                logger.info(f"✅ Email sent to {to}")
                _log_external_api("Microsoft Graph", "mail_send", duration_ms, 0.0)
                
                return {
                    "success": True,
                    "message": f"Email sent to {to}",
                    "timestamp": datetime.utcnow().isoformat(),
                    "subject": subject,
                    "recipients": to,
                    "attachments": len(attachments) if attachments else 0,
                    "duration_ms": round(duration_ms, 2)
                }
            else:
                # Failed
                error_msg = response.text
                logger.error(f"❌ Failed to send email: {response.status_code} - {error_msg}")
                
                return {
                    "success": False,
                    "error": f"Graph API error: {response.status_code} - {error_msg[:200]}",
                    "timestamp": datetime.utcnow().isoformat()
                }
        
        except Exception as e:
            logger.error(f"❌ Email send exception: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _parse_recipients(self, recipients: str) -> List[Dict[str, Any]]:
        """Parse comma-separated email addresses into Graph API format"""
        emails = [email.strip() for email in recipients.split(',')]
        return [
            {"emailAddress": {"address": email}}
            for email in emails if email
        ]
    
    def _build_attachments(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """Build attachment objects for Graph API"""
        attachments = []
        
        for file_path in file_paths:
            path = Path(file_path)
            
            if not path.exists():
                logger.warning(f"Attachment not found: {file_path}")
                continue
            
            try:
                # Read file content
                with open(path, 'rb') as f:
                    content = f.read()
                
                # Encode to base64
                import base64
                content_bytes = base64.b64encode(content).decode('utf-8')
                
                # Add to attachments
                attachments.append({
                    "@odata.type": "#microsoft.graph.fileAttachment",
                    "name": path.name,
                    "contentType": "application/octet-stream",
                    "contentBytes": content_bytes
                })
                
                logger.info(f"Added attachment: {path.name} ({len(content)} bytes)")
            
            except Exception as e:
                logger.error(f"Failed to attach {file_path}: {e}")
        
        return attachments


class YahooEmailSender:
    """
    Yahoo email sender using SMTP for Buddy's personal/operational emails.
    
    Features:
    - SMTP authentication with app password
    - Template rendering
    - Attachment support
    - HTML/plain text
    """
    
    def __init__(self):
        """Initialize Yahoo email sender with SMTP credentials"""
        self.email_address = os.getenv("BUDDY_EMAIL_ADDRESS")
        self.app_password = os.getenv("BUDDY_EMAIL_APP_PASSWORD")
        self.smtp_host = os.getenv("BUDDY_EMAIL_SMTP_HOST", "smtp.mail.yahoo.com")
        self.smtp_port = int(os.getenv("BUDDY_EMAIL_SMTP_PORT", "465"))
        
        if not all([self.email_address, self.app_password]):
            logger.warning("Missing Yahoo credentials - Buddy email sending disabled")
            self.enabled = False
        else:
            self.enabled = True
        
        logger.info(f"YahooEmailSender initialized: enabled={self.enabled}, from={self.email_address}")
    
    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        attachments: Optional[List[str]] = None,
        cc: Optional[str] = None,
        bcc: Optional[str] = None,
        html: bool = False,
        template: Optional[str] = None,
        template_vars: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Send an email via Yahoo SMTP.
        
        Args:
            to: Recipient email address (or comma-separated list)
            subject: Email subject
            body: Email body content
            attachments: List of file paths to attach
            cc: CC recipients (comma-separated)
            bcc: BCC recipients (comma-separated)
            html: If True, send as HTML email
            template: Template name from EMAIL_TEMPLATES
            template_vars: Variables to render in template
            
        Returns:
            Status dict with success/failure info
        """
        start_time = time.time()
        
        if not self.enabled:
            return {
                "success": False,
                "error": "Buddy email sending disabled - missing Yahoo credentials",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        try:
            # Apply template if specified
            if template and template in EMAIL_TEMPLATES:
                template_data = EMAIL_TEMPLATES[template]
                vars_dict = template_vars or {}
                subject = template_data['subject'].format(**vars_dict)
                body = template_data['body'].format(**vars_dict)
                logger.info(f"Applied template: {template}")
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.email_address
            msg['To'] = to
            msg['Subject'] = subject
            
            if cc:
                msg['Cc'] = cc
            if bcc:
                msg['Bcc'] = bcc
            
            # Add body
            mime_type = 'html' if html else 'plain'
            msg.attach(MIMEText(body, mime_type))
            
            # Add attachments if specified
            if attachments:
                for file_path in attachments:
                    path = Path(file_path)
                    if not path.exists():
                        logger.warning(f"Attachment not found: {file_path}")
                        continue
                    
                    try:
                        with open(path, 'rb') as f:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(f.read())
                        
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename={path.name}'
                        )
                        msg.attach(part)
                        logger.info(f"Added attachment: {path.name}")
                    
                    except Exception as e:
                        logger.error(f"Failed to attach {file_path}: {e}")
            
            # Parse recipients
            recipients = [email.strip() for email in to.split(',')]
            if cc:
                recipients.extend([email.strip() for email in cc.split(',')])
            if bcc:
                recipients.extend([email.strip() for email in bcc.split(',')])
            
            # Connect and send via SMTP
            with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port) as server:
                server.login(self.email_address, self.app_password)
                server.send_message(msg)
            
            duration_ms = (time.time() - start_time) * 1000
            logger.info(f"✅ Buddy email sent to {to}")
            _log_external_api("Yahoo Mail", "smtp_send", duration_ms, 0.0)
            
            return {
                "success": True,
                "message": f"Buddy email sent to {to}",
                "timestamp": datetime.utcnow().isoformat(),
                "subject": subject,
                "recipients": to,
                "from": self.email_address,
                "attachments": len(attachments) if attachments else 0,
                "duration_ms": round(duration_ms, 2)
            }
        
        except Exception as e:
            logger.error(f"❌ Buddy email send exception: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


def send_work_email(
    to: str,
    subject: str = "",
    body: str = "",
    attachments: Optional[List[str]] = None,
    cc: Optional[str] = None,
    bcc: Optional[str] = None,
    html: bool = False,
    template: Optional[str] = None,
    **template_vars
) -> Dict[str, Any]:
    """
    Send a WORK/PROFESSIONAL email via Microsoft Graph API.
    
    Use this for Michael Cardwell's professional communications for Cardwell Associates.
    This uses Michael's work email account.
    
    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body content
        attachments: List of file paths to attach
        cc: CC recipients (comma-separated)
        bcc: BCC recipients (comma-separated)
        html: If True, send as HTML email
        template: Template name (greeting, notification, report, custom)
        **template_vars: Variables to render in template
        
    Returns:
        Status dict with success/failure info
        
    Example:
        >>> send_work_email(
        ...     to="client@example.com",
        ...     template="notification",
        ...     name="Client Name",
        ...     title="Project Update",
        ...     content="Your project milestone has been completed."
        ... )
    """
    sender = EmailSender()
    return sender.send_email(
        to=to,
        subject=subject,
        body=body,
        attachments=attachments,
        cc=cc,
        bcc=bcc,
        html=html,
        template=template,
        template_vars=template_vars if template_vars else None
    )


def send_buddy_email(
    to: str,
    subject: str = "",
    body: str = "",
    attachments: Optional[List[str]] = None,
    cc: Optional[str] = None,
    bcc: Optional[str] = None,
    html: bool = False,
    template: Optional[str] = None,
    **template_vars
) -> Dict[str, Any]:
    """
    Send a BUDDY/PERSONAL email via Yahoo SMTP.
    
    Use this for Buddy's own operational emails, system notifications, and personal activities.
    This uses Buddy's personal Yahoo account (buddy.cardwell@yahoo.com).
    
    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body content
        attachments: List of file paths to attach
        cc: CC recipients (comma-separated)
        bcc: BCC recipients (comma-separated)
        html: If True, send as HTML email
        template: Template name (greeting, notification, report, custom)
        **template_vars: Variables to render in template
        
    Returns:
        Status dict with success/failure info
        
    Example:
        >>> send_buddy_email(
        ...     to="service@example.com",
        ...     template="notification",
        ...     name="Service",
        ...     title="Daily Report",
        ...     content="Today's activity summary..."
        ... )
    """
    sender = YahooEmailSender()
    return sender.send_email(
        to=to,
        subject=subject,
        body=body,
        attachments=attachments,
        cc=cc,
        bcc=bcc,
        html=html,
        template=template,
        template_vars=template_vars if template_vars else None
    )


def send_email(
    to: str,
    subject: str = "",
    body: str = "",
    attachments: Optional[List[str]] = None,
    cc: Optional[str] = None,
    bcc: Optional[str] = None,
    html: bool = False,
    template: Optional[str] = None,
    **template_vars
) -> Dict[str, Any]:
    """
    DEPRECATED: Use send_work_email() or send_buddy_email() instead.
    
    Legacy interface for backward compatibility - defaults to Buddy's personal email.
    """
    logger.warning("send_email() is deprecated - use send_work_email() or send_buddy_email() instead")
    return send_buddy_email(
        to=to,
        subject=subject,
        body=body,
        attachments=attachments,
        cc=cc,
        bcc=bcc,
        html=html,
        template=template,
        **template_vars
    )


# Register tools
def register_email_tools():
    """Register both email tools with tool registry"""
    try:
        from Back_End.tool_registry import tool_registry
        
        # Register work email tool
        tool_registry.register(
            name='email_send_work',
            func=send_work_email,
            description=(
                "Send PROFESSIONAL/WORK emails for Michael Cardwell at Cardwell Associates. "
                "Uses Microsoft Graph API with Michael's work email account. "
                "Use this for business communications, client emails, and professional correspondence. "
                "Supports HTML/plain text, CC/BCC, attachments, and template rendering."
            )
        )
        logger.info("✅ Work email tool registered: email_send_work")
        
        # Register Buddy's personal email tool
        tool_registry.register(
            name='email_send_buddy',
            func=send_buddy_email,
            description=(
                "Send PERSONAL/OPERATIONAL emails for Buddy's activities. "
                "Uses Yahoo SMTP with Buddy's personal account (buddy.cardwell@yahoo.com). "
                "Use this for system notifications, operational reports, Buddy's own communications, "
                "and any non-professional emails. Supports HTML/plain text, CC/BCC, attachments, and templates."
            )
        )
        logger.info("✅ Buddy email tool registered: email_send_buddy")
        
        # Register legacy tool for backward compatibility
        tool_registry.register(
            name='email_send',
            func=send_email,
            description=(
                "DEPRECATED: Use email_send_work or email_send_buddy instead. "
                "Legacy email tool for backward compatibility."
            )
        )
        logger.info("✅ Legacy email tool registered: email_send (deprecated)")
    
    except Exception as e:
        logger.error(f"Failed to register email tools: {e}")


# Auto-register on import
register_email_tools()
