"""
Phase 12.1: Revenue Signal Pipeline

Read-only revenue signal schema and emitter.
Signals are observational only (no payments, no outreach, no automation).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any
import json
import uuid


class RevenueSignalType(Enum):
    """Allowed revenue signal types."""
    OFFER_SENT = "offer_sent"
    RESPONSE_RECEIVED = "response_received"
    PRICE_VIEWED = "price_viewed"
    INTENT_DETECTED = "intent_detected"
    PAYMENT_REQUESTED = "payment_requested"
    PAYMENT_CONFIRMED = "payment_confirmed"
    REJECTED = "rejected"


class RevenueSignalSource(Enum):
    """Allowed revenue signal sources."""
    CHAT = "chat"
    WEB = "web"
    MANUAL = "manual"


@dataclass(frozen=True)
class RevenueSignal:
    """Immutable revenue signal record."""
    revenue_signal_id: str
    signal_type: RevenueSignalType
    confidence: float
    timestamp: str
    source: RevenueSignalSource
    mission_id: Optional[str] = None
    build_id: Optional[str] = None
    opportunity_id: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None

    @staticmethod
    def new(
        signal_type: RevenueSignalType,
        confidence: float,
        source: RevenueSignalSource,
        mission_id: Optional[str] = None,
        build_id: Optional[str] = None,
        opportunity_id: Optional[str] = None,
        amount: Optional[float] = None,
        currency: Optional[str] = None,
    ) -> "RevenueSignal":
        """Create a new revenue signal with generated ID and timestamp."""
        return RevenueSignal(
            revenue_signal_id=str(uuid.uuid4()),
            signal_type=signal_type,
            confidence=confidence,
            timestamp=datetime.now(timezone.utc).isoformat(),
            source=source,
            mission_id=mission_id,
            build_id=build_id,
            opportunity_id=opportunity_id,
            amount=amount,
            currency=currency,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "revenue_signal_id": self.revenue_signal_id,
            "mission_id": self.mission_id,
            "build_id": self.build_id,
            "opportunity_id": self.opportunity_id,
            "signal_type": self.signal_type.value,
            "amount": self.amount,
            "currency": self.currency,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
            "source": self.source.value,
        }


class RevenueSignalEmitter:
    """Persist revenue signals to JSONL (append-only)."""

    def __init__(self, stream_file: Optional[Path] = None):
        self._stream_file = stream_file or Path("outputs/phase25/revenue_signals.jsonl")
        self._stream_file.parent.mkdir(parents=True, exist_ok=True)

    def emit(self, signal: RevenueSignal) -> None:
        """Validate and persist a revenue signal (no side effects)."""
        self._validate(signal)
        with self._stream_file.open("a", encoding="utf-8") as f:
            json.dump(signal.to_dict(), f)
            f.write("\n")

    def _validate(self, signal: RevenueSignal) -> None:
        """Validate schema and constraints."""
        if not signal.revenue_signal_id:
            raise ValueError("revenue_signal_id is required")
        if not isinstance(signal.signal_type, RevenueSignalType):
            raise ValueError("signal_type must be RevenueSignalType")
        if not isinstance(signal.source, RevenueSignalSource):
            raise ValueError("source must be RevenueSignalSource")
        if not isinstance(signal.confidence, (float, int)):
            raise ValueError("confidence must be a number")
        if signal.confidence < 0.0 or signal.confidence > 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if signal.amount is not None and not isinstance(signal.amount, (float, int)):
            raise ValueError("amount must be a number if provided")
        if signal.currency is not None and not isinstance(signal.currency, str):
            raise ValueError("currency must be a string if provided")
        if not signal.timestamp:
            raise ValueError("timestamp is required")

