"""
Microsoft Graph API Email Helper

Retrieves emails using Microsoft Graph API with OAuth authentication.
"""

import os
import re
import logging
import json
from typing import Optional
from datetime import datetime, timedelta
from pathlib import Path
import msal
import requests

logger = logging.getLogger(__name__)

TOKEN_CACHE_FILE = "msgraph_token_cache.json"


class MSGraphEmailClient:
    """Microsoft Graph API client for reading emails"""
    
    def __init__(self):
        """Initialize MS Graph client with credentials from environment"""
        self.client_id = os.getenv("MSGRAPH_CLIENT_ID")
        self.client_secret = os.getenv("MSGRAPH_CLIENT_SECRET")
        self.tenant_id = os.getenv("MSGRAPH_TENANT_ID")
        self.email_address = os.getenv("EMAIL_IMAP_USER")
        
        if not all([self.client_id, self.tenant_id]):
            raise ValueError("Missing Microsoft Graph credentials in .env")
        
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.scopes = ["https://graph.microsoft.com/Mail.Read"]
        self.graph_endpoint = "https://graph.microsoft.com/v1.0"
        self.cache = self._load_cache()
        
    def _load_cache(self):
        """Load token cache from file"""
        cache = msal.SerializableTokenCache()
        if Path(TOKEN_CACHE_FILE).exists():
            cache.deserialize(open(TOKEN_CACHE_FILE, "r").read())
        return cache
    
    def _save_cache(self):
        """Save token cache to file"""
        if self.cache.has_state_changed:
            with open(TOKEN_CACHE_FILE, "w") as f:
                f.write(self.cache.serialize())
        
    def _get_access_token(self) -> Optional[str]:
        """Get access token using delegated permissions with device code flow"""
        try:
            # Use PublicClientApplication for delegated permissions
            app = msal.PublicClientApplication(
                self.client_id,
                authority=self.authority,
                token_cache=self.cache
            )
            
            # Try to get token from cache first
            accounts = app.get_accounts()
            if accounts:
                logger.info("Found cached account, attempting silent authentication...")
                result = app.acquire_token_silent(self.scopes, account=accounts[0])
                if result and "access_token" in result:
                    logger.info("✓ Successfully acquired token from cache")
                    self._save_cache()
                    return result["access_token"]
            
            # If no cached token, use device code flow
            logger.info("No cached token found, initiating device code flow...")
            flow = app.initiate_device_flow(scopes=self.scopes)
            
            if "user_code" not in flow:
                raise ValueError("Failed to create device flow")
            
            print("\n" + "="*60)
            print("MICROSOFT AUTHENTICATION REQUIRED")
            print("="*60)
            print(flow["message"])
            print("="*60 + "\n")
            
            # Wait for user to authenticate
            result = app.acquire_token_by_device_flow(flow)
            
            if "access_token" in result:
                logger.info("✓ Successfully acquired access token")
                self._save_cache()
                return result["access_token"]
            else:
                logger.error(f"Failed to acquire token: {result.get('error_description', 'Unknown error')}")
                return None
        except Exception as e:
            logger.error(f"Error getting access token: {e}")
            return None
    
    def get_mfa_code(self, from_sender: str = "mployer", max_wait: int = 60) -> Optional[str]:
        """
        Retrieve MFA code from recent emails. Will poll for new emails if not found immediately.
        
        Args:
            from_sender: Sender email/domain to filter by
            max_wait: Maximum seconds to wait for email to arrive
            
        Returns:
            6-digit verification code or None if not found
        """
        import time
        
        try:
            token = self._get_access_token()
            if not token:
                return None
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # Record start time and last seen email timestamp
            start_time = datetime.utcnow()
            poll_interval = 5  # Check every 5 seconds
            attempts = 0
            max_attempts = max_wait // poll_interval
            
            # Look for emails from last 2 minutes (to get fresh ones)
            cutoff_time = (datetime.utcnow() - timedelta(minutes=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
            
            # Build filter query
            filter_query = f"receivedDateTime ge {cutoff_time}"
            if from_sender:
                filter_query += f" and contains(from/emailAddress/address, '{from_sender}')"
            
            # Get messages for the user (use "me" instead of specific email)
            user_endpoint = f"{self.graph_endpoint}/me/messages"
            params = {
                "$filter": filter_query,
                "$orderby": "receivedDateTime DESC",
                "$top": 3,
                "$select": "subject,body,receivedDateTime"
            }
            
            logger.info(f"Waiting for email from {from_sender}...")
            code_pattern = r"\b(\d{6})\b"
            last_check_time = start_time
            
            while attempts < max_attempts:
                attempts += 1
                logger.info(f"Checking for new emails (attempt {attempts}/{max_attempts})...")
                
                response = requests.get(user_endpoint, headers=headers, params=params)
                
                if response.status_code != 200:
                    logger.error(f"Failed to get messages: {response.status_code} - {response.text}")
                    return None
                
                messages = response.json().get("value", [])
                
                if messages:
                    logger.info(f"Found {len(messages)} recent email(s), searching for verification code...")
                    
                    for msg in messages:
                        body_content = msg.get("body", {}).get("content", "")
                        subject = msg.get("subject", "")
                        received_time_str = msg.get("receivedDateTime", "")
                        
                        # Parse received time
                        try:
                            received_time = datetime.strptime(received_time_str.replace('Z', '+00:00').split('+')[0], "%Y-%m-%dT%H:%M:%S")
                            # Only check emails received after we started looking (or within 30 seconds before)
                            if received_time < (start_time - timedelta(seconds=30)):
                                logger.debug(f"Skipping old email: {subject} (received {received_time_str})")
                                continue
                        except:
                            pass  # If parsing fails, still check the email
                        
                        logger.debug(f"Checking email: {subject} (received {received_time_str})")
                        
                        # Search in body
                        match = re.search(code_pattern, body_content)
                        if match:
                            code = match.group(1)
                            logger.info(f"✓ Found verification code: {code}")
                            return code
                
                if attempts < max_attempts:
                    logger.info(f"No code found yet, waiting {poll_interval} seconds before next check...")
                    time.sleep(poll_interval)
                    last_check_time = datetime.utcnow()
            
            logger.warning(f"Could not find verification code after {max_wait} seconds")
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving MFA code from Microsoft Graph: {e}")
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving MFA code from Microsoft Graph: {e}")
            return None


def get_mfa_code_from_msgraph(from_sender: str = "mployer", max_wait: int = 60) -> Optional[str]:
    """
    Convenience function to get MFA code from Microsoft Graph.
    
    Args:
        from_sender: Sender email/domain to filter by
        max_wait: Maximum seconds to wait for email
        
    Returns:
        6-digit verification code or None if not found
    """
    try:
        client = MSGraphEmailClient()
        return client.get_mfa_code(from_sender=from_sender, max_wait=max_wait)
    except Exception as e:
        logger.error(f"Failed to retrieve MFA code: {e}")
        return None
