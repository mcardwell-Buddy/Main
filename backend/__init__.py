"""Backend package init for the autonomous agent runtime."""

# Import and initialize all tools on package load
from backend import tools
from backend import additional_tools
from backend import learning_tools
from backend import extended_tools

# Import new iterative components
from backend import iterative_decomposer
from backend import iterative_executor

__all__ = []
