import json
import logging
from dotenv import load_dotenv

load_dotenv()

from Back_End.config import Config

class MockMemory:
    def __init__(self):
        self.data = {}

    def get(self, key):
        return self.data.get(key)

    def set(self, key, value):
        self.data[key] = value
        return True
    
    def get_all(self):
        """Get all stored values as a dict"""
        return dict(self.data)

    def safe_call(self, method, *args, **kwargs):
        try:
            return getattr(self, method)(*args, **kwargs)
        except Exception as e:
            logging.error(f"Memory error: {e}")
            return None

class FirebaseMemory:
    def __init__(self):
        try:
            import firebase_admin
            from firebase_admin import credentials, firestore
        except Exception as e:
            raise RuntimeError(f"firebase-admin not installed: {e}")

        if not firebase_admin._apps:
            cred = self._build_credentials(credentials)
            firebase_admin.initialize_app(cred)

        self._db = firestore.client()
        self._collection = Config.FIREBASE_COLLECTION

    def _build_credentials(self, credentials_module):
        if Config.FIREBASE_CREDENTIALS_PATH:
            return credentials_module.Certificate(Config.FIREBASE_CREDENTIALS_PATH)
        
        if Config.FIREBASE_CREDENTIALS_JSON:
            data = json.loads(Config.FIREBASE_CREDENTIALS_JSON)
            return credentials_module.Certificate(data)

        if Config.FIREBASE_PROJECT_ID and Config.FIREBASE_CLIENT_EMAIL and Config.FIREBASE_PRIVATE_KEY:
            private_key = Config.FIREBASE_PRIVATE_KEY.replace('\\n', '\n')
            data = {
                "type": "service_account",
                "project_id": Config.FIREBASE_PROJECT_ID,
                "private_key_id": "",
                "private_key": private_key,
                "client_email": Config.FIREBASE_CLIENT_EMAIL,
                "client_id": "",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": ""
            }
            return credentials_module.Certificate(data)

        raise RuntimeError("Firebase credentials missing")

    @staticmethod
    def _sanitize_key(key: str) -> str:
        """
        Sanitize key for Firestore document ID.
        Firestore document IDs cannot contain: / [ ] * ? 
        and cannot be just . or ..
        Also replace : ' " with _ to avoid path issues
        """
        import re
        # Replace problematic characters with underscore
        sanitized = re.sub(r'[/\[\]\*\?:\'" ]', '_', str(key))
        # Ensure it's not . or ..
        if sanitized in ('.', '..'):
            sanitized = f'doc_{sanitized}'
        # Firestore has 1500 byte limit on document IDs
        if len(sanitized.encode('utf-8')) > 1500:
            # Hash long keys
            import hashlib
            hash_suffix = hashlib.md5(sanitized.encode()).hexdigest()[:16]
            sanitized = sanitized[:1450] + '_' + hash_suffix
        return sanitized

    def get(self, key):
        try:
            sanitized_key = self._sanitize_key(key)
            logging.debug(f"[FIREBASE_MEMORY] GET: key={key}, sanitized={sanitized_key}, collection={self._collection}")
            doc = self._db.collection(self._collection).document(sanitized_key).get()
            if not doc.exists:
                logging.debug(f"[FIREBASE_MEMORY] GET: key={key} NOT FOUND")
                return None
            value = doc.to_dict().get('value')
            logging.info(f"[FIREBASE_MEMORY] GET SUCCESS: key={key}, value_type={type(value).__name__}")
            return value
        except Exception as e:
            logging.error(f"[FIREBASE_MEMORY] GET ERROR: key={key}, error={e}")
            return None

    def set(self, key, value):
        try:
            sanitized_key = self._sanitize_key(key)
            logging.debug(f"[FIREBASE_MEMORY] SET: key={key}, sanitized={sanitized_key}, collection={self._collection}, value_type={type(value).__name__}")
            self._db.collection(self._collection).document(sanitized_key).set({'value': value})
            logging.info(f"[FIREBASE_MEMORY] SET SUCCESS: key={key}, persisted to Firebase")
            return True
        except Exception as e:
            logging.error(f"[FIREBASE_MEMORY] SET ERROR: key={key}, error={e}")
            return False
    
    def get_all(self):
        """Get all documents from the collection as a dict"""
        try:
            docs = self._db.collection(self._collection).stream()
            result = {}
            for doc in docs:
                key = doc.id
                value = doc.to_dict().get('value')
                if value is not None:
                    result[key] = value
            return result
        except Exception as e:
            logging.error(f"Firebase get_all error: {e}")
            return {}

    def safe_call(self, method, *args, **kwargs):
        try:
            return getattr(self, method)(*args, **kwargs)
        except Exception as e:
            logging.error(f"Memory error: {e}")
            return None

def _select_memory():
    if Config.FIREBASE_ENABLED:
        try:
            return FirebaseMemory()
        except Exception as e:
            logging.error(f"Falling back to MockMemory: {e}")
    return MockMemory()

memory = _select_memory()

