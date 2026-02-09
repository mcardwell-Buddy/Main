"""
Phase 12.3: Build Reviews

Deterministic, read-only review layer for builds and deliverables.
No execution, no autonomy, no retries.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Any
import json
import uuid


class BuildReviewer(Enum):
    """Allowed reviewers."""
    USER = "user"
    BUDDY = "buddy"


class BuildReviewVerdict(Enum):
    """Allowed review verdicts."""
    APPROVED = "approved"
    REVISE = "revise"
    KILL = "kill"


@dataclass(frozen=True)
class BuildReview:
    """Immutable build review record."""
    review_id: str
    build_id: str
    reviewer: BuildReviewer
    verdict: BuildReviewVerdict
    rationale: str
    confidence: float
    timestamp: str

    @staticmethod
    def new(
        build_id: str,
        reviewer: BuildReviewer,
        verdict: BuildReviewVerdict,
        rationale: str,
        confidence: float,
    ) -> "BuildReview":
        """Create a new build review with generated ID and timestamp."""
        return BuildReview(
            review_id=str(uuid.uuid4()),
            build_id=build_id,
            reviewer=reviewer,
            verdict=verdict,
            rationale=rationale,
            confidence=confidence,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "review_id": self.review_id,
            "build_id": self.build_id,
            "reviewer": self.reviewer.value,
            "verdict": self.verdict.value,
            "rationale": self.rationale,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "BuildReview":
        """Deserialize from dictionary."""
        return BuildReview(
            review_id=data.get("review_id") or str(uuid.uuid4()),
            build_id=data.get("build_id", ""),
            reviewer=BuildReviewer(data.get("reviewer", BuildReviewer.USER.value)),
            verdict=BuildReviewVerdict(data.get("verdict", BuildReviewVerdict.REVISE.value)),
            rationale=data.get("rationale", ""),
            confidence=float(data.get("confidence", 0.0)),
            timestamp=data.get("timestamp") or datetime.now(timezone.utc).isoformat(),
        )


class BuildReviewRegistry:
    """Append-only registry for build reviews."""

    def __init__(self, stream_file: Optional[Path] = None):
        self._stream_file = stream_file or Path("outputs/phase25/build_reviews.jsonl")
        self._stream_file.parent.mkdir(parents=True, exist_ok=True)

    def register_review(self, review: BuildReview) -> None:
        """Persist a review (append-only)."""
        self._validate(review)
        with self._stream_file.open("a", encoding="utf-8") as f:
            json.dump(review.to_dict(), f)
            f.write("\n")

    def list_by_build(self, build_id: str) -> List[BuildReview]:
        """List all reviews for a build."""
        return [r for r in self._read_all() if r.build_id == build_id]

    def get_latest_review(self, build_id: str) -> Optional[BuildReview]:
        """Get most recent review for a build."""
        reviews = self.list_by_build(build_id)
        return reviews[-1] if reviews else None

    def get_latest_reviews_summary(self) -> List[Dict[str, Any]]:
        """Return latest review summary per build."""
        latest: Dict[str, BuildReview] = {}
        for review in self._read_all():
            latest[review.build_id] = review
        return [
            {
                "build_id": review.build_id,
                "verdict": review.verdict.value,
                "confidence": review.confidence,
                "reviewer": review.reviewer.value,
                "timestamp": review.timestamp,
            }
            for review in latest.values()
        ]

    def _read_all(self) -> List[BuildReview]:
        if not self._stream_file.exists():
            return []
        items: List[BuildReview] = []
        with self._stream_file.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                items.append(BuildReview.from_dict(data))
        return items

    def _validate(self, review: BuildReview) -> None:
        if not review.review_id:
            raise ValueError("review_id is required")
        if not review.build_id:
            raise ValueError("build_id is required")
        if not isinstance(review.reviewer, BuildReviewer):
            raise ValueError("reviewer must be BuildReviewer")
        if not isinstance(review.verdict, BuildReviewVerdict):
            raise ValueError("verdict must be BuildReviewVerdict")
        if not isinstance(review.confidence, (float, int)):
            raise ValueError("confidence must be a number")
        if review.confidence < 0.0 or review.confidence > 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if not review.rationale:
            raise ValueError("rationale is required")
        if not review.timestamp:
            raise ValueError("timestamp is required")
