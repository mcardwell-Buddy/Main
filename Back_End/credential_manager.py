"""
Secure Credential Storage for Mployer

Stores and manages Mployer login credentials securely using environment variables
and encrypted configuration files.
"""

import os
import json
import logging
from pathlib import Path
from cryptography.fernet import Fernet
import keyring

logger = logging.getLogger(__name__)

BUDDY_ROOT = Path(__file__).parent.parent
CREDENTIALS_FILE = BUDDY_ROOT / ".credentials"
CREDENTIALS_ENCRYPTED = BUDDY_ROOT / ".credentials.enc"
DOTENV_FILE = BUDDY_ROOT / ".env"


def redact_secret(value: str, show_last: int = 2) -> str:
    """Redact secrets for safe display/logging."""
    if not value:
        return ""
    if len(value) <= show_last:
        return "*" * len(value)
    return "*" * (len(value) - show_last) + value[-show_last:]


class CredentialManager:
    """Manage secure storage of Mployer credentials"""
    
    @staticmethod
    def setup_credentials():
        """
        Interactive setup to store Mployer credentials securely.
        Run this once to configure your credentials.
        """
        print("\n" + "="*60)
        print("BUDDY - Mployer Credential Setup")
        print("="*60)
        print("\nThis will securely store your Mployer login credentials.")
        print("Your password will be encrypted and never stored in plain text.\n")
        
        # Get Mployer username
        username = input("Enter your Mployer email/username: ").strip()
        
        # Get Mployer password
        import getpass
        password = getpass.getpass("Enter your Mployer password (hidden): ")
        
        # Option 1: Store in environment variables (simplest)
        print("\n" + "-"*60)
        print("OPTION 1: Environment Variables (Recommended)")
        print("-"*60)
        print("Add these lines to your .env file or system environment:")
        print(f"\nMPLOYER_USERNAME={username}")
        print(f"MPLOYER_PASSWORD={redact_secret(password)}")
        
        # Option 2: Store encrypted
        print("\n" + "-"*60)
        print("OPTION 2: Encrypted Storage")
        print("-"*60)
        
        use_encryption = input("Encrypt and save credentials locally? (y/n): ").lower() == 'y'
        
        if use_encryption:
            # Generate encryption key
            key = Fernet.generate_key()
            cipher = Fernet(key)
            
            # Encrypt credentials
            creds_json = json.dumps({
                "username": username,
                "password": password
            }).encode()
            
            encrypted = cipher.encrypt(creds_json)
            
            # Save encrypted credentials
            with open(CREDENTIALS_ENCRYPTED, 'wb') as f:
                f.write(encrypted)
            
            # Save key in OS keyring (requires user interaction once)
            keyring.set_password("Buddy-Mployer", "encryption_key", key.decode())
            
            print(f"\n✓ Credentials encrypted and saved to {CREDENTIALS_ENCRYPTED}")
            print("✓ Encryption key stored in Windows Credential Manager")
            print("\nCredentials are now secure and ready to use!")
        
        # Option 3: OS Keyring
        print("\n" + "-"*60)
        print("OPTION 3: Windows Credential Manager (Most Secure)")
        print("-"*60)
        
        use_keyring = input("Store credentials in Windows Credential Manager? (y/n): ").lower() == 'y'
        
        if use_keyring:
            keyring.set_password("Buddy-Mployer", "username", username)
            keyring.set_password("Buddy-Mployer", "password", password)
            print("✓ Credentials stored in Windows Credential Manager")
            print("✓ Automatically retrieved by Buddy when needed")
    
    @staticmethod
    def get_credentials() -> dict:
        """
        Retrieve stored credentials from environment or secure storage.
        
        Returns:
            Dictionary with 'username' and 'password' keys
            
        Raises:
            Exception if credentials not found
        """
        
        # Try loading from .env (if present) into environment
        try:
            if DOTENV_FILE.exists():
                with open(DOTENV_FILE, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#") or "=" not in line:
                            continue
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip().strip("\"").strip("'")
                        if key and key not in os.environ:
                            os.environ[key] = value
        except Exception as e:
            logger.warning(f"Could not load .env: {e}")
        
        # Try environment variables first (fastest)
        username = os.getenv("MPLOYER_USERNAME")
        password = os.getenv("MPLOYER_PASSWORD")
        
        if username and password:
            logger.info("✓ Credentials loaded from environment variables")
            return {"username": username, "password": password}
        
        # Try Windows Credential Manager (most secure)
        try:
            username = keyring.get_password("Buddy-Mployer", "username")
            password = keyring.get_password("Buddy-Mployer", "password")
            
            if username and password:
                logger.info("✓ Credentials loaded from Windows Credential Manager")
                return {"username": username, "password": password}
        except Exception as e:
            logger.debug(f"Keyring not available: {e}")
        
        # Try encrypted file
        try:
            if CREDENTIALS_ENCRYPTED.exists():
                key_str = keyring.get_password("Buddy-Mployer", "encryption_key")
                if key_str:
                    key = key_str.encode()
                    cipher = Fernet(key)
                    
                    with open(CREDENTIALS_ENCRYPTED, 'rb') as f:
                        encrypted = f.read()
                    
                    decrypted = cipher.decrypt(encrypted).decode()
                    creds = json.loads(decrypted)
                    
                    logger.info("✓ Credentials loaded from encrypted storage")
                    return creds
        except Exception as e:
            logger.warning(f"Could not load encrypted credentials: {e}")
        
        raise Exception(
            "Mployer credentials not found. "
            "Run: python -c \"from Back_End.credential_manager import CredentialManager; CredentialManager.setup_credentials()\""
        )


def initialize_mployer_credentials():
    """Initialize Mployer credentials on startup"""
    try:
        creds = CredentialManager.get_credentials()
        logger.info("✓ Mployer credentials loaded successfully")
        return creds
    except Exception as e:
        logger.warning(f"Mployer credentials not configured: {e}")
        return None

