"""
Phase 12.6: Economic Test Preparation

Simulation-only economic scenarios. NO execution, NO money moved.
Append-only JSONL persistence.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any
import json
import uuid


SCENARIOS_FILE = Path("outputs/phase25/economic_scenarios.jsonl")


@dataclass(frozen=True)
class EconomicScenario:
    """Immutable economic scenario (simulation only)."""
    scenario_id: str
    build_id: str
    hypothetical_price: float
    hypothetical_response_rate: float
    risk_level: str
    confidence: float
    timestamp: str

    @staticmethod
    def new(
        build_id: str,
        hypothetical_price: float,
        hypothetical_response_rate: float,
        risk_level: str,
        confidence: float,
    ) -> "EconomicScenario":
        """Create a new scenario with generated ID and timestamp."""
        return EconomicScenario(
            scenario_id=str(uuid.uuid4()),
            build_id=build_id,
            hypothetical_price=hypothetical_price,
            hypothetical_response_rate=hypothetical_response_rate,
            risk_level=risk_level,
            confidence=confidence,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "scenario_id": self.scenario_id,
            "build_id": self.build_id,
            "hypothetical_price": self.hypothetical_price,
            "hypothetical_response_rate": self.hypothetical_response_rate,
            "risk_level": self.risk_level,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "EconomicScenario":
        """Deserialize from dictionary."""
        return EconomicScenario(
            scenario_id=data.get("scenario_id") or str(uuid.uuid4()),
            build_id=data.get("build_id", ""),
            hypothetical_price=float(data.get("hypothetical_price", 0.0)),
            hypothetical_response_rate=float(data.get("hypothetical_response_rate", 0.0)),
            risk_level=data.get("risk_level", ""),
            confidence=float(data.get("confidence", 0.0)),
            timestamp=data.get("timestamp") or datetime.now(timezone.utc).isoformat(),
        )


class EconomicScenarioRegistry:
    """Append-only registry for economic scenarios."""

    def __init__(self, stream_file: Optional[Path] = None):
        self._stream_file = stream_file or SCENARIOS_FILE
        self._stream_file.parent.mkdir(parents=True, exist_ok=True)

    def register_scenario(self, scenario: EconomicScenario) -> None:
        """Persist scenario (append-only)."""
        self._validate(scenario)
        with self._stream_file.open("a", encoding="utf-8") as f:
            json.dump(scenario.to_dict(), f)
            f.write("\n")

    def list_by_build(self, build_id: str) -> List[EconomicScenario]:
        """List scenarios for a build."""
        return [s for s in self._read_all() if s.build_id == build_id]

    def list_all(self) -> List[EconomicScenario]:
        """List all scenarios."""
        return self._read_all()

    def _read_all(self) -> List[EconomicScenario]:
        if not self._stream_file.exists():
            return []
        items: List[EconomicScenario] = []
        with self._stream_file.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                items.append(EconomicScenario.from_dict(data))
        return items

    def _validate(self, scenario: EconomicScenario) -> None:
        if not scenario.scenario_id:
            raise ValueError("scenario_id is required")
        if not scenario.build_id:
            raise ValueError("build_id is required")
        if not isinstance(scenario.hypothetical_price, (float, int)):
            raise ValueError("hypothetical_price must be a number")
        if not isinstance(scenario.hypothetical_response_rate, (float, int)):
            raise ValueError("hypothetical_response_rate must be a number")
        if scenario.hypothetical_response_rate < 0.0 or scenario.hypothetical_response_rate > 1.0:
            raise ValueError("hypothetical_response_rate must be between 0 and 1")
        if not scenario.risk_level:
            raise ValueError("risk_level is required")
        if not isinstance(scenario.confidence, (float, int)):
            raise ValueError("confidence must be a number")
        if scenario.confidence < 0.0 or scenario.confidence > 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if not scenario.timestamp:
            raise ValueError("timestamp is required")

