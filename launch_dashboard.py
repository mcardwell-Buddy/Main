#!/usr/bin/env python
"""
Phase 8: Dashboard Launcher
Starts the FastAPI dashboard server with integrated analytics engine
"""

import subprocess
import sys
import time
import socket
import logging
from pathlib import Path
from typing import Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_port_available(port: int, host: str = "127.0.0.1") -> bool:
    """Check if a port is available."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((host, port))
            return True
    except OSError:
        return False


def find_available_port(start_port: int = 8000, max_attempts: int = 10) -> int:
    """Find an available port starting from start_port."""
    for port in range(start_port, start_port + max_attempts):
        if check_port_available(port):
            return port
    raise RuntimeError(f"No available ports found between {start_port} and {start_port + max_attempts}")


def start_dashboard(
    port: Optional[int] = None,
    host: str = "0.0.0.0",
    reload: bool = False
):
    """Start the dashboard API server."""
    
    logger.info("=" * 70)
    logger.info("🚀 STARTING BUDDY DASHBOARD SERVER")
    logger.info("=" * 70)
    
    # Find available port if not specified
    if port is None:
        port = find_available_port()
        logger.info(f"📍 Using auto-detected port: {port}")
    
    # Verify phase8_dashboard_api.py exists
    api_file = Path(__file__).parent / "phase8_dashboard_api.py"
    if not api_file.exists():
        logger.error(f"❌ Dashboard API file not found: {api_file}")
        sys.exit(1)
    
    # Verify dashboard.html exists
    html_file = Path(__file__).parent / "dashboard.html"
    if not html_file.exists():
        logger.error(f"❌ Dashboard HTML file not found: {html_file}")
        sys.exit(1)
    
    logger.info(f"✅ Dashboard files located")
    logger.info(f"📊 API: http://localhost:{port}/api/")
    logger.info(f"📈 Dashboard: http://localhost:{port}/")
    
    # Build uvicorn command
    cmd = [
        sys.executable,
        "-m", "uvicorn",
        "phase8_dashboard_api:app",
        f"--host={host}",
        f"--port={port}",
        "--log-level=info"
    ]
    
    if reload:
        cmd.append("--reload")
    
    logger.info(f"🔧 Command: {' '.join(cmd)}")
    logger.info("\n" + "=" * 70)
    logger.info("Dashboard is starting... Open http://localhost:{port}/ in your browser")
    logger.info("=" * 70 + "\n")
    
    # Start the server
    try:
        subprocess.run(cmd, cwd=Path(__file__).parent)
    except KeyboardInterrupt:
        logger.info("\n\n🛑 Dashboard stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Error starting dashboard: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Start Buddy Dashboard")
    parser.add_argument("--port", type=int, default=None, help="Port to run dashboard on (default: auto-detect)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload on file changes")
    
    args = parser.parse_args()
    
    start_dashboard(port=args.port, host=args.host, reload=args.reload)
