"""
Error Recovery - Safe response creation with retries and fallback behavior.

Phase 3: Provides a lightweight recovery layer that can:
- Retry build/format operations
- Record recovery actions in Response metadata
- Create standardized error responses
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, Optional
import time
import logging

from Back_End.response_engine.types import Response


logger = logging.getLogger(__name__)


@dataclass
class RetryPolicy:
    """Retry configuration for recovery operations."""
    max_attempts: int = 2
    base_delay_ms: int = 200
    backoff_multiplier: float = 2.0


@dataclass
class RecoveryAction:
    """Record of a recovery step taken."""
    action: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
        }


class ErrorRecoveryManager:
    """
    Provides safe build/format operations with retry and fallback handling.
    """

    def __init__(self, retry_policy: Optional[RetryPolicy] = None):
        self.retry_policy = retry_policy or RetryPolicy()

    def safe_build(self, builder: Any) -> Response:
        """
        Safely build a response using the provided builder.

        Args:
            builder: ResponseBuilder instance

        Returns:
            Response (either built or error fallback)
        """
        attempts = 0
        last_error: Optional[str] = None
        while attempts < self.retry_policy.max_attempts:
            try:
                return builder.build()
            except Exception as exc:  # pylint: disable=broad-except
                attempts += 1
                last_error = str(exc)
                logger.exception("Response build failed, attempt %s", attempts)
                self._sleep_with_backoff(attempts)

        # Fallback response if all attempts fail
        response = self.create_error_response(
            mission_id=getattr(builder, "mission_id", "unknown"),
            error_message=last_error or "Unknown build error",
        )
        response.error_recovery_attempts = attempts
        response.recovery_actions.append(
            RecoveryAction(
                action="fallback_error_response",
                details={"attempts": attempts, "error": last_error},
            ).to_dict()
        )
        return response

    def safe_format(self, formatter: Callable[[Response], str], response: Response) -> str:
        """
        Safely format a response with retry.

        Args:
            formatter: Callable that formats a Response into string
            response: Response to format

        Returns:
            Formatted output or a minimal error string
        """
        attempts = 0
        last_error: Optional[str] = None
        while attempts < self.retry_policy.max_attempts:
            try:
                return formatter(response)
            except Exception as exc:  # pylint: disable=broad-except
                attempts += 1
                last_error = str(exc)
                logger.exception("Response format failed, attempt %s", attempts)
                self._sleep_with_backoff(attempts)

        response.last_error = last_error
        response.last_error_at = datetime.utcnow()
        response.error_recovery_attempts += attempts
        response.recovery_actions.append(
            RecoveryAction(
                action="fallback_plain_text",
                details={"attempts": attempts, "error": last_error},
            ).to_dict()
        )
        return f"[Formatting error] {last_error}"

    @staticmethod
    def create_error_response(mission_id: str, error_message: str) -> Response:
        """
        Create a standardized error response.
        """
        response = Response(
            response_id=f"resp_error_{int(time.time())}",
            mission_id=mission_id,
            status="error",
            primary_content="An error occurred while generating the response.",
            requires_approval=False,
            last_error=error_message,
            last_error_at=datetime.utcnow(),
            error_history=[error_message],
        )
        return response

    def _sleep_with_backoff(self, attempt: int) -> None:
        delay = self.retry_policy.base_delay_ms * (self.retry_policy.backoff_multiplier ** (attempt - 1))
        time.sleep(delay / 1000.0)

