"""
Backend package init for the autonomous agent runtime.

This module ensures proper module paths are configured at import time,
making the backend resilient to different deployment contexts.
"""

import sys
import os
from pathlib import Path


def ensure_backend_in_path() -> Path:
    """
    Ensure Back_End package can be imported from anywhere.
    
    This fixes module import issues during Cloud Run deployment where
    the module path might not be set up correctly.
    
    Returns:
        Path to the project root directory
    """
    try:
        # Get the directory containing this file (./Back_End/)
        backend_dir = Path(__file__).parent.absolute()
        
        # Get the parent directory (project root)
        project_root = backend_dir.parent.absolute()
        
        # Ensure project root is in path so Back_End can be imported as a module
        root_str = str(project_root)
        if root_str not in sys.path:
            sys.path.insert(0, root_str)
        
        return project_root
    except Exception as e:
        # If anything fails, try to continue anyway
        import logging
        logging.debug(f"Could not ensure backend path: {e}")
        return Path.cwd()


def load_optional_modules() -> None:
	"""Load optional backend modules when explicitly requested."""
	try:
		from Back_End import tools  # noqa: F401
		from Back_End import additional_tools  # noqa: F401
		from Back_End import learning_tools  # noqa: F401
		from Back_End import extended_tools  # noqa: F401
		from Back_End import iterative_decomposer  # noqa: F401
		from Back_End import iterative_executor  # noqa: F401
	except Exception:
		# Keep import errors from breaking minimal deployments.
		pass


# Initialize path setup at package import time
_PROJECT_ROOT = ensure_backend_in_path()

__all__ = ["load_optional_modules", "ensure_backend_in_path"]

