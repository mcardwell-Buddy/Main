import os
from dotenv import load_dotenv

# Load .env file from project root
load_dotenv()

class Config:
    API_KEYS = {
        'SERPAPI': os.getenv('SERPAPI_KEY'),
        # Add more keys as needed
    }
    TIMEOUT = int(os.getenv('TOOL_TIMEOUT', '10'))  # seconds
    MAX_AGENT_STEPS = int(os.getenv('MAX_AGENT_STEPS', '8'))
    DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
    MOCK_MODE = os.getenv('MOCK_MODE', 'true').lower() == 'true'
    FIREBASE_ENABLED = os.getenv('FIREBASE_ENABLED', 'false').lower() == 'true'
    FIREBASE_COLLECTION = os.getenv('FIREBASE_COLLECTION', 'agent_memory')
    FIREBASE_CREDENTIALS_PATH = os.getenv('FIREBASE_CREDENTIALS_PATH')
    FIREBASE_CREDENTIALS_JSON = os.getenv('FIREBASE_CREDENTIALS_JSON')
    FIREBASE_PROJECT_ID = os.getenv('FIREBASE_PROJECT_ID')
    FIREBASE_CLIENT_EMAIL = os.getenv('FIREBASE_CLIENT_EMAIL')
    FIREBASE_PRIVATE_KEY = os.getenv('FIREBASE_PRIVATE_KEY')
    
    # Mission Storage Mode (Cost Optimization)
    # 'local-first': Write to SQLite, sync to Firebase in background (70-90% cost savings)
    # 'cloud-direct': Write directly to Firebase (original behavior)
    MISSION_STORAGE_MODE = os.getenv('MISSION_STORAGE_MODE', 'cloud-direct')
    
    # Add more config as needed

