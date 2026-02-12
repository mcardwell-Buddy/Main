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
    
    # Artifact System Feature Flag (Phase 2)
    # Controls creation of UniversalArtifact wrapper and artifact versioning
    # Zero-breaking: artifact system is entirely additive
    ARTIFACT_SYSTEM_ENABLED = os.getenv('ARTIFACT_SYSTEM_ENABLED', 'false').lower() == 'true'
    
    # Learning Signal Processor Feature Flag (Phase 2)
    # Controls processing of execution signals to extract insights
    # Non-blocking: processor failures don't affect execution
    LEARNING_PROCESSOR_ENABLED = os.getenv('LEARNING_PROCESSOR_ENABLED', 'false').lower() == 'true'
    
    # Artifact Graph Query Engine Feature Flag (Phase 3)
    # Controls loading and querying of artifact relationship graph
    # Non-blocking: graph queries are optional enhancements
    ARTIFACT_GRAPH_ENABLED = os.getenv('ARTIFACT_GRAPH_ENABLED', 'false').lower() == 'true'
    
    # Schema Versioning System Feature Flag (Phase 4a)
    # Controls artifact schema versioning and migration
    # Non-blocking: schema validation failures don't affect execution
    SCHEMA_VERSIONING_ENABLED = os.getenv('SCHEMA_VERSIONING_ENABLED', 'true').lower() == 'true'
    
    # Cost Reconciliation System Feature Flag (Phase 4b)
    # Controls cost tracking and variance analysis
    # Non-blocking: cost tracking doesn't affect execution
    COST_RECONCILIATION_ENABLED = os.getenv('COST_RECONCILIATION_ENABLED', 'true').lower() == 'true'
    
    # Add more config as needed

