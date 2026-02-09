import os
from dotenv import load_dotenv

load_dotenv()

from backend.config import Config

print('FIREBASE_ENABLED:', Config.FIREBASE_ENABLED)
print('FIREBASE_CREDENTIALS_JSON present:', bool(Config.FIREBASE_CREDENTIALS_JSON))
print('Length:', len(Config.FIREBASE_CREDENTIALS_JSON or ''))
