"""
Microsoft OneDrive Integration with OAuth 2.0

Enables Buddy to:
- Save artifacts to shared OneDrive folders
- Upload files to specific folders
- List and manage files
- Access shared folders from user's account

Uses Microsoft Graph API with OAuth 2.0 authentication.
Buddy can authenticate using his Yahoo email via Microsoft account linking.
"""

import os
import json
import mimetypes
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import requests
from requests.auth import HTTPBasicAuth


class OneDriveOAuthClient:
    """
    Manages Microsoft OAuth 2.0 authentication for OneDrive access.
    
    Setup Instructions:
    1. Go to https://portal.azure.com/ → Azure Active Directory → App registrations
    2. Create new registration with name "Buddy Agent"
    3. Add redirect URI: http://localhost:8080/oauth/microsoft/callback
    4. API permissions: Files.ReadWrite, Files.ReadWrite.All (for shared folders)
    5. Copy Application (client) ID and create a client secret
    """
    
    def __init__(self):
        self.config_path = Path("data/onedrive_oauth_config.json")
        self.tokens_path = Path("data/onedrive_tokens.json")
        self.config = self._load_config()
        self.tokens = self._load_tokens()
        
        # Microsoft OAuth endpoints
        self.authority = "https://login.microsoftonline.com/common"
        self.authorize_url = f"{self.authority}/oauth2/v2.0/authorize"
        self.token_url = f"{self.authority}/oauth2/v2.0/token"
        self.graph_api_base = "https://graph.microsoft.com/v1.0"
        
    def _load_config(self) -> Dict[str, str]:
        """Load Microsoft OAuth app credentials"""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                return json.load(f)
        return {
            "client_id": os.getenv("MICROSOFT_CLIENT_ID", ""),
            "client_secret": os.getenv("MICROSOFT_CLIENT_SECRET", ""),
            "redirect_uri": "http://localhost:8080/oauth/microsoft/callback",
            "scopes": "Files.ReadWrite Files.ReadWrite.All offline_access"
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
        params = {
            "client_id": self.config["client_id"],
            "response_type": "code",
            "redirect_uri": self.config["redirect_uri"],
            "response_mode": "query",
            "scope": self.config["scopes"],
            "state": "12345"  # Should be random in production
        }
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.authorize_url}?{query_string}"
    
    def exchange_code_for_tokens(self, authorization_code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access/refresh tokens.
        
        Args:
            authorization_code: Code from OAuth callback
            
        Returns:
            Token response with access_token, refresh_token, expires_in
        """
        data = {
            "client_id": self.config["client_id"],
            "client_secret": self.config["client_secret"],
            "code": authorization_code,
            "redirect_uri": self.config["redirect_uri"],
            "grant_type": "authorization_code"
        }
        
        response = requests.post(self.token_url, data=data)
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
        
        data = {
            "client_id": self.config["client_id"],
            "client_secret": self.config["client_secret"],
            "refresh_token": self.tokens["refresh_token"],
            "grant_type": "refresh_token",
            "scope": self.config["scopes"]
        }
        
        response = requests.post(self.token_url, data=data)
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
            print("🔄 OneDrive token expired, refreshing...")
            self.refresh_access_token()
        
        return self.tokens["access_token"]


class OneDriveClient:
    """
    Microsoft OneDrive client for file operations.
    
    Features:
    - Upload files to user's OneDrive
    - Upload to shared folders
    - List files in folders
    - Create folders
    - Download files
    - Delete files
    """
    
    def __init__(self):
        self.oauth_client = OneDriveOAuthClient()
        self.graph_api = self.oauth_client.graph_api_base
        
    def _get_headers(self) -> Dict[str, str]:
        """Get authorization headers with valid token"""
        token = self.oauth_client.get_valid_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def upload_file(
        self,
        file_path: str,
        onedrive_folder: str = "/Buddy Artifacts",
        custom_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload a file to OneDrive.
        
        Args:
            file_path: Local path to file
            onedrive_folder: Destination folder in OneDrive
            custom_name: Custom filename (default: use original name)
            
        Returns:
            Upload result with file ID, web URL, etc.
        """
        try:
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Determine filename
            filename = custom_name or path.name
            
            # Ensure folder exists
            self.create_folder(onedrive_folder)
            
            # Read file content
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            # Upload URL
            upload_path = f"{onedrive_folder.strip('/')}/{filename}"
            upload_url = f"{self.graph_api}/me/drive/root:/{upload_path}:/content"
            
            # Determine content type
            content_type, _ = mimetypes.guess_type(file_path)
            if content_type is None:
                content_type = 'application/octet-stream'
            
            # Upload file
            headers = {
                "Authorization": f"Bearer {self.oauth_client.get_valid_access_token()}",
                "Content-Type": content_type
            }
            
            response = requests.put(upload_url, headers=headers, data=file_content)
            response.raise_for_status()
            
            file_info = response.json()
            
            return {
                "success": True,
                "file_id": file_info.get("id"),
                "name": file_info.get("name"),
                "size": file_info.get("size"),
                "web_url": file_info.get("webUrl"),
                "download_url": file_info.get("@microsoft.graph.downloadUrl"),
                "created": file_info.get("createdDateTime"),
                "folder_path": onedrive_folder,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "file_path": file_path,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def create_folder(self, folder_path: str) -> Dict[str, Any]:
        """
        Create a folder in OneDrive (creates parent folders if needed).
        
        Args:
            folder_path: Path like "/Buddy Artifacts" or "/Projects/MyProject"
            
        Returns:
            Folder info dict
        """
        try:
            # Check if folder exists
            check_url = f"{self.graph_api}/me/drive/root:/{folder_path.strip('/')}"
            headers = self._get_headers()
            
            response = requests.get(check_url, headers=headers)
            if response.status_code == 200:
                return {"success": True, "exists": True, "data": response.json()}
            
            # Create folder
            parts = folder_path.strip('/').split('/')
            parent_path = ""
            
            for i, part in enumerate(parts):
                current_path = "/".join(parts[:i+1])
                check_url = f"{self.graph_api}/me/drive/root:/{current_path}"
                
                response = requests.get(check_url, headers=headers)
                if response.status_code == 404:
                    # Create this folder
                    if i == 0:
                        create_url = f"{self.graph_api}/me/drive/root/children"
                    else:
                        parent_path = "/".join(parts[:i])
                        create_url = f"{self.graph_api}/me/drive/root:/{parent_path}:/children"
                    
                    folder_data = {
                        "name": part,
                        "folder": {},
                        "@microsoft.graph.conflictBehavior": "rename"
                    }
                    
                    response = requests.post(create_url, headers=headers, json=folder_data)
                    response.raise_for_status()
            
            return {"success": True, "created": True, "path": folder_path}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def list_files(self, folder_path: str = "/") -> List[Dict[str, Any]]:
        """
        List files in a OneDrive folder.
        
        Args:
            folder_path: Folder path (default: root)
            
        Returns:
            List of file info dicts
        """
        try:
            if folder_path == "/":
                url = f"{self.graph_api}/me/drive/root/children"
            else:
                url = f"{self.graph_api}/me/drive/root:/{folder_path.strip('/')}:/children"
            
            headers = self._get_headers()
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            items = response.json().get("value", [])
            
            files = []
            for item in items:
                files.append({
                    "id": item.get("id"),
                    "name": item.get("name"),
                    "size": item.get("size"),
                    "type": "folder" if "folder" in item else "file",
                    "web_url": item.get("webUrl"),
                    "created": item.get("createdDateTime"),
                    "modified": item.get("lastModifiedDateTime")
                })
            
            return files
            
        except Exception as e:
            print(f"❌ Error listing files: {e}")
            return []
    
    def download_file(self, file_id: str, save_path: str) -> bool:
        """
        Download a file from OneDrive.
        
        Args:
            file_id: OneDrive file ID
            save_path: Local path to save file
            
        Returns:
            True if successful
        """
        try:
            # Get download URL
            url = f"{self.graph_api}/me/drive/items/{file_id}/content"
            headers = self._get_headers()
            
            response = requests.get(url, headers=headers, allow_redirects=True)
            response.raise_for_status()
            
            # Save file
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, 'wb') as f:
                f.write(response.content)
            
            return True
            
        except Exception as e:
            print(f"❌ Error downloading file: {e}")
            return False
    
    def delete_file(self, file_id: str) -> bool:
        """
        Delete a file from OneDrive.
        
        Args:
            file_id: OneDrive file ID
            
        Returns:
            True if successful
        """
        try:
            url = f"{self.graph_api}/me/drive/items/{file_id}"
            headers = self._get_headers()
            
            response = requests.delete(url, headers=headers)
            response.raise_for_status()
            
            return True
            
        except Exception as e:
            print(f"❌ Error deleting file: {e}")
            return False
    
    def get_shared_folder_items(self, shared_link: str) -> List[Dict[str, Any]]:
        """
        Access items in a shared folder.
        
        Args:
            shared_link: OneDrive sharing link
            
        Returns:
            List of items in shared folder
        """
        try:
            # Encode sharing link
            import base64
            encoded = base64.urlsafe_b64encode(shared_link.encode()).decode()
            # Remove padding
            encoded_no_padding = encoded.rstrip('=')
            share_token = f"u!{encoded_no_padding}"
            
            url = f"{self.graph_api}/shares/{share_token}/driveItem/children"
            headers = self._get_headers()
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            items = response.json().get("value", [])
            
            files = []
            for item in items:
                files.append({
                    "id": item.get("id"),
                    "name": item.get("name"),
                    "size": item.get("size"),
                    "type": "folder" if "folder" in item else "file",
                    "web_url": item.get("webUrl")
                })
            
            return files
            
        except Exception as e:
            print(f"❌ Error accessing shared folder: {e}")
            return []


class ArtifactDeliveryService:
    """
    Manages delivery of Buddy's artifacts via email or OneDrive.
    
    Features:
    - Email artifacts as attachments
    - Upload artifacts to OneDrive
    - Generate delivery confirmations
    - Track delivery history
    """
    
    def __init__(self):
        from backend.email_client import get_email_client
        self.email_client = get_email_client()
        self.onedrive_client = OneDriveClient()
        self.history_path = Path("data/artifact_deliveries.jsonl")
        
    def deliver_artifact(
        self,
        artifact_path: str,
        recipient_email: str,
        method: str = "email",  # "email" or "onedrive"
        onedrive_folder: str = "/Buddy Artifacts",
        message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Deliver an artifact to user via email or OneDrive.
        
        Args:
            artifact_path: Path to artifact file
            recipient_email: User's email address
            method: "email" or "onedrive"
            onedrive_folder: OneDrive destination folder
            message: Optional message to include
            
        Returns:
            Delivery result dict
        """
        artifact_name = Path(artifact_path).name
        
        if method == "email":
            result = self._deliver_via_email(
                artifact_path, recipient_email, message
            )
        elif method == "onedrive":
            result = self._deliver_via_onedrive(
                artifact_path, onedrive_folder, recipient_email, message
            )
        else:
            return {"success": False, "error": f"Unknown method: {method}"}
        
        # Record delivery
        self._record_delivery(artifact_path, method, result)
        
        return result
    
    def _deliver_via_email(
        self,
        artifact_path: str,
        recipient: str,
        message: Optional[str]
    ) -> Dict[str, Any]:
        """Send artifact via email attachment"""
        artifact_name = Path(artifact_path).name
        
        subject = f"Buddy Built: {artifact_name}"
        body = message or f"""Hi there! 👋

I've completed building {artifact_name}. Please find it attached to this email.

If you have any questions or need modifications, just reply to this email and I'll understand your request!

Best regards,
Buddy 🤖
"""
        
        return self.email_client.send_email(
            to=recipient,
            subject=subject,
            body=body,
            attachments=[artifact_path]
        )
    
    def _deliver_via_onedrive(
        self,
        artifact_path: str,
        folder: str,
        recipient_email: str,
        message: Optional[str]
    ) -> Dict[str, Any]:
        """Upload artifact to OneDrive and send notification email"""
        # Upload to OneDrive
        upload_result = self.onedrive_client.upload_file(
            artifact_path, folder
        )
        
        if not upload_result["success"]:
            return upload_result
        
        # Send notification email
        artifact_name = Path(artifact_path).name
        subject = f"Buddy Saved: {artifact_name} to OneDrive"
        body = message or f"""Hi there! 👋

I've saved {artifact_name} to your OneDrive in the "{folder}" folder.

📁 **Access it here:** {upload_result['web_url']}

File details:
- Name: {upload_result['name']}
- Size: {upload_result['size']:,} bytes
- Location: {upload_result['folder_path']}

If you need any changes, just let me know!

Best regards,
Buddy 🤖
"""
        
        email_result = self.email_client.send_email(
            to=recipient_email,
            subject=subject,
            body=body,
            html=False
        )
        
        return {
            "success": True,
            "method": "onedrive",
            "upload": upload_result,
            "notification": email_result,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _record_delivery(
        self,
        artifact_path: str,
        method: str,
        result: Dict[str, Any]
    ):
        """Record delivery in history log"""
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        
        record = {
            "timestamp": datetime.utcnow().isoformat(),
            "artifact": artifact_path,
            "method": method,
            "success": result.get("success", False),
            "result": result
        }
        
        with open(self.history_path, 'a') as f:
            f.write(json.dumps(record) + '\n')


# Singleton instances
_onedrive_client = None
_delivery_service = None


def get_onedrive_client() -> OneDriveClient:
    """Get or create OneDrive client singleton"""
    global _onedrive_client
    if _onedrive_client is None:
        _onedrive_client = OneDriveClient()
    return _onedrive_client


def get_delivery_service() -> ArtifactDeliveryService:
    """Get or create artifact delivery service singleton"""
    global _delivery_service
    if _delivery_service is None:
        _delivery_service = ArtifactDeliveryService()
    return _delivery_service
