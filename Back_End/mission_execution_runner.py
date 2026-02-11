"""
Simple mission executor runner - starts the async executor loop.

This is used for testing and can also be called from FastAPI startup handlers.
No FastAPI dependency - pure asyncio.
"""

import asyncio
import logging
from Back_End.execution import executor, execution_queue

logger = logging.getLogger(__name__)


async def run_executor_with_timeout(duration_seconds: int = 10) -> None:
    """
    Run the mission executor loop for a fixed duration.
    
    Args:
        duration_seconds: How long to run the executor before stopping
    """
    executor.running = True
    try:
        await asyncio.wait_for(
            executor.run_executor_loop(),
            timeout=duration_seconds
        )
    except asyncio.TimeoutError:
        # Expected - we ran for the duration
        pass
    finally:
        executor.running = False


def start_executor_background():
    """Create a background task for the executor (for FastAPI integration)."""
    return asyncio.create_task(executor.run_executor_loop())

