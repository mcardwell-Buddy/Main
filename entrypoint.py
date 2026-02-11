#!/usr/bin/env python3
"""
Entrypoint script for Cloud Run deployment.
Ensures PYTHONPATH is properly configured before starting uvicorn.
"""

import sys
import os
from pathlib import Path

# Get the application root directory (where this script lives)
APP_ROOT = Path(__file__).parent.absolute()

# Ensure /app is in Python's module search path so Back_End can be imported
sys.path.insert(0, str(APP_ROOT))

# Print diagnostic info
print(f"▶ Starting Buddy backend", flush=True)
print(f"▶ Working directory: {os.getcwd()}", flush=True)
print(f"▶ APP_ROOT: {APP_ROOT}", flush=True)
print(f"▶ sys.path[0]: {sys.path[0]}", flush=True)
print(f"▶ Back_End exists: {(APP_ROOT / 'Back_End').exists()}", flush=True)

# Now import and run uvicorn
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "Back_End.main:app",
        host="0.0.0.0",
        port=8080,
        log_level="info"
    )
