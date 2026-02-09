"""
Goal Satisfaction Evaluator: Deterministic assessment of mission objective completion.
Phase 3 Step 1: Read-only, non-autonomous evaluation with no side effects.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import json


@dataclass
class GoalEvaluation:
    """Result of goal satisfaction evaluation."""
    mission_id: str
    goal_satisfied: bool
    confidence: float
    evidence: List[str]
    gap_reason: Optional[str] = None
    evaluation_timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mission_id": self.mission_id,
            "goal_satisfied": self.goal_satisfied,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "gap_reason": self.gap_reason,
            "evaluation_timestamp": self.evaluation_timestamp
        }

    def to_signal(self) -> Dict[str, Any]:
        """Convert to learning signal format."""
        return {
            "signal_type": "goal_evaluation",
            "signal_layer": "mission",
            "signal_source": "goal_evaluator",
            "mission_id": self.mission_id,
            "goal_satisfied": self.goal_satisfied,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "gap_reason": self.gap_reason,
            "timestamp": self.evaluation_timestamp
        }


class GoalSatisfactionEvaluator:
    """
    Deterministic evaluator for mission objective satisfaction.
    Uses keyword matching, count validation, and heuristic scoring.
    """

    def __init__(self):
        pass

    def evaluate(
        self,
        mission_id: str,
        mission_objective: str,
        items_collected: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> GoalEvaluation:
        """
        Evaluate whether collected items satisfy the mission objective.

        Args:
            mission_id: Unique mission identifier
            mission_objective: Natural language objective (e.g., "Collect 5 items")
            items_collected: List of extracted items (dicts with title, content, etc.)
            context: Optional context (page_title, url, counts, etc.)

        Returns:
            GoalEvaluation with satisfaction status, confidence, and evidence
        """
        evaluation_timestamp = datetime.now(timezone.utc).isoformat()
        evidence: List[str] = []
        gap_reason: Optional[str] = None
        confidence: float = 0.0
        goal_satisfied: bool = False

        # Parse objective for quantitative targets
        target_count = self._extract_target_count(mission_objective)
        required_keywords = self._extract_required_keywords(mission_objective)
        has_count_requirement = target_count is not None

        # Evaluate collected items
        item_count = len(items_collected)

        # Evidence gathering
        if item_count == 0:
            evidence.append("No items were collected")
            gap_reason = "zero_items_collected"
            goal_satisfied = False
            confidence = 0.0
        else:
            evidence.append(f"{item_count} items collected")

            # Quantitative evaluation (count-based)
            if has_count_requirement:
                if item_count >= target_count:
                    evidence.append(f"Item count {item_count} meets target {target_count}")
                    goal_satisfied = True
                    confidence = min(item_count / target_count, 1.0)
                else:
                    gap_reason = f"insufficient_items: collected {item_count}, target {target_count}"
                    evidence.append(f"Item count {item_count} below target {target_count}")
                    goal_satisfied = False
                    confidence = item_count / target_count if target_count > 0 else 0.0

            # Qualitative evaluation (keyword-based)
            elif required_keywords:
                keyword_matches = self._count_keyword_matches(items_collected, required_keywords)
                total_keywords = len(required_keywords)
                match_rate = keyword_matches / total_keywords if total_keywords > 0 else 0.0

                if match_rate >= 0.5:  # At least 50% of keywords found
                    evidence.append(f"Found {keyword_matches}/{total_keywords} required keywords")
                    goal_satisfied = True
                    confidence = match_rate
                else:
                    gap_reason = f"insufficient_keyword_match: {match_rate:.0%} coverage"
                    evidence.append(f"Only {keyword_matches}/{total_keywords} keywords found")
                    goal_satisfied = False
                    confidence = match_rate

            # Default: any items satisfy generic objectives
            else:
                # If no specific targets or keywords, any items satisfy
                evidence.append("Generic objective satisfied by collected items")
                goal_satisfied = True
                confidence = min(item_count / 3.0, 1.0)  # Normalize confidence

        # Create evaluation result
        evaluation = GoalEvaluation(
            mission_id=mission_id,
            goal_satisfied=goal_satisfied,
            confidence=min(max(confidence, 0.0), 1.0),  # Clamp to [0, 1]
            evidence=evidence,
            gap_reason=gap_reason,
            evaluation_timestamp=evaluation_timestamp
        )

        # Optional artifact registry hook (read-only, no behavior change)
        try:
            if context and (context.get("artifact_registry_store") or context.get("register_artifact")):
                from backend.artifact_registry import Artifact, ArtifactType, PresentationHint, ArtifactStatus
                from backend.artifact_registry_store import ArtifactRegistryStore

                registry = context.get("artifact_registry_store") or ArtifactRegistryStore()
                summary = "Goal satisfied" if goal_satisfied else "Goal not satisfied"
                artifact = Artifact.new(
                    artifact_type=ArtifactType.REPORT,
                    title="Goal Evaluation Summary",
                    description=summary,
                    created_by=mission_id,
                    source_module="goal_satisfaction_evaluator",
                    presentation_hint=PresentationHint.TEXT,
                    confidence=evaluation.confidence,
                    tags=["goal_evaluation"],
                    status=ArtifactStatus.FINAL,
                )
                registry.register_artifact(artifact)
        except Exception:
            pass

        return evaluation

    def _extract_target_count(self, objective: str) -> Optional[int]:
        """
        Extract numeric target from objective string.
        E.g., "Collect 5 items" → 5
        E.g., "Collect at least 10 items" → 10
        """
        import re

        # Pattern: digit followed by relevant words
        patterns = [
            r"(\d+)\s+(?:items?|results?|entries?|quotes?|articles?|products?|pages?)",
            r"(?:at least|minimum)\s+(\d+)",
            r"(?:collect|gather|find)\s+(\d+)"
        ]

        for pattern in patterns:
            match = re.search(pattern, objective, re.IGNORECASE)
            if match:
                return int(match.group(1))

        return None

    def _extract_required_keywords(self, objective: str) -> List[str]:
        """
        Extract keyword requirements from objective.
        E.g., "Find quotes by famous authors" → ["quotes", "authors"]
        """
        import re

        # Remove common words and action verbs
        stop_words = {
            "find", "collect", "gather", "search", "get", "retrieve",
            "all", "the", "a", "an", "and", "or", "with", "from",
            "about", "on", "in", "at", "to", "for", "is", "are",
            "items", "results", "entries", "data", "information",
            "any", "some", "each", "every", "where", "browse", "extract",
            "by", "of", "that", "this", "these", "those"
        }

        # Split by common delimiters and filter
        words = re.split(r'[\s\-_,;:]+', objective.lower())
        keywords = [w for w in words if len(w) > 2 and w not in stop_words and w.isalpha()]

        # If no keywords found, it's generic
        if not keywords:
            return []

        return list(set(keywords))[:5]  # Unique keywords, max 5

    def _count_keyword_matches(self, items: List[Dict[str, Any]], keywords: List[str]) -> int:
        """Count how many required keywords appear in collected items."""
        matched_keywords = set()

        for item in items:
            # Combine all text from item
            item_text = " ".join([
                str(item.get("title", "")),
                str(item.get("content", "")),
                str(item.get("text", ""))
            ]).lower()

            # Check each keyword
            for keyword in keywords:
                if keyword.lower() in item_text:
                    matched_keywords.add(keyword)

        return len(matched_keywords)
