"""
Opportunity Normalizer: Convert collected items into canonical Opportunity representation.
Phase 3 Step 2: Deterministic normalization with no autonomy or LLM usage.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid
import hashlib
import re


@dataclass
class OpportunitySignals:
    """Detected signals in an opportunity."""
    has_contact: bool = False
    has_price: bool = False
    has_deadline: bool = False

    def to_dict(self) -> Dict[str, bool]:
        return {
            "has_contact": self.has_contact,
            "has_price": self.has_price,
            "has_deadline": self.has_deadline
        }


@dataclass
class Opportunity:
    """Canonical internal opportunity representation."""
    opportunity_id: str
    mission_id: str
    source: str
    opportunity_type: str  # directory | job | lead | request | unknown
    title: str
    description: str
    url: Optional[str]
    signals: OpportunitySignals
    raw_item_ref: str  # index or hash
    confidence: float
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "opportunity_id": self.opportunity_id,
            "mission_id": self.mission_id,
            "source": self.source,
            "opportunity_type": self.opportunity_type,
            "title": self.title,
            "description": self.description,
            "url": self.url,
            "signals": self.signals.to_dict(),
            "raw_item_ref": self.raw_item_ref,
            "confidence": self.confidence,
            "timestamp": self.timestamp
        }


class OpportunityNormalizer:
    """
    Deterministic converter from collected items to canonical opportunities.
    
    Uses heuristic rules only - no LLM, no guessing, no autonomy.
    """

    def __init__(self):
        pass

    def normalize(
        self,
        mission_id: str,
        mission_objective: str,
        items_collected: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> List[Opportunity]:
        """
        Convert collected items into normalized opportunities.

        Args:
            mission_id: Mission identifier
            mission_objective: Natural language objective
            items_collected: List of extracted items
            context: Optional context (url, title, source_domain)

        Returns:
            List of normalized Opportunity objects
        """
        opportunities: List[Opportunity] = []

        if not items_collected:
            return opportunities

        # Extract context
        source = self._extract_source(context)

        # Normalize each item
        for idx, item in enumerate(items_collected):
            opportunity = self._normalize_item(
                mission_id=mission_id,
                item=item,
                source=source,
                item_index=idx
            )

            if opportunity:
                opportunities.append(opportunity)

        # Optional artifact registry hook (read-only, no behavior change)
        try:
            if context and (context.get("artifact_registry_store") or context.get("register_artifact")):
                if opportunities:
                    from backend.artifact_registry import Artifact, ArtifactType, PresentationHint, ArtifactStatus
                    from backend.artifact_registry_store import ArtifactRegistryStore

                    registry = context.get("artifact_registry_store") or ArtifactRegistryStore()
                    avg_conf = sum(o.confidence for o in opportunities) / len(opportunities)
                    artifact = Artifact.new(
                        artifact_type=ArtifactType.DATASET,
                        title="Normalized Opportunities",
                        description=f"{len(opportunities)} opportunities normalized",
                        created_by=mission_id,
                        source_module="opportunity_normalizer",
                        presentation_hint=PresentationHint.TABLE,
                        confidence=round(avg_conf, 3),
                        tags=["opportunities"],
                        status=ArtifactStatus.FINAL,
                    )
                    registry.register_artifact(artifact)
        except Exception:
            pass

        return opportunities

    def _normalize_item(
        self,
        mission_id: str,
        item: Dict[str, Any],
        source: str,
        item_index: int
    ) -> Optional[Opportunity]:
        """Normalize a single item to an opportunity."""
        if not item:
            return None

        # Generate traceable reference
        raw_item_ref = self._generate_item_ref(item, item_index)

        # Extract fields
        title = self._extract_title(item)
        description = self._extract_description(item)
        url = self._extract_url(item)

        if not title:
            return None

        # Classify opportunity type
        opp_type = self._classify_type(item, title, description)

        # Extract signals
        signals = self._extract_signals(item, title, description, url)

        # Calculate confidence
        confidence = self._calculate_confidence(item, opp_type, signals)

        opportunity = Opportunity(
            opportunity_id=str(uuid.uuid4()),
            mission_id=mission_id,
            source=source,
            opportunity_type=opp_type,
            title=title,
            description=description,
            url=url,
            signals=signals,
            raw_item_ref=raw_item_ref,
            confidence=confidence
        )

        return opportunity

    def _extract_source(self, context: Optional[Dict[str, Any]]) -> str:
        """Extract source domain/platform from context."""
        if not context:
            return "unknown"

        # Try URL first
        url = context.get("page_url") or context.get("url")
        if url:
            try:
                from urllib.parse import urlparse
                parsed = urlparse(url)
                domain = parsed.netloc or parsed.path
                return domain.split(':')[0] if domain else "unknown"
            except Exception:
                pass

        # Try explicit source
        source = context.get("source_domain") or context.get("source")
        if source:
            return source

        return "unknown"

    def _generate_item_ref(self, item: Dict[str, Any], item_index: int) -> str:
        """Generate traceable reference to original item."""
        # Prefer hash of content over index for deduplication
        item_str = str(sorted(item.items()))
        item_hash = hashlib.md5(item_str.encode()).hexdigest()[:8]
        return f"item_{item_index}_{item_hash}"

    def _extract_title(self, item: Dict[str, Any]) -> str:
        """Extract title from item."""
        candidates = ["title", "name", "text", "heading", "label"]
        for key in candidates:
            value = item.get(key, "").strip()
            if value and len(value) > 1:
                return value[:200]  # Truncate to 200 chars
        return ""

    def _extract_description(self, item: Dict[str, Any]) -> str:
        """Extract description from item."""
        candidates = ["content", "description", "body", "summary", "details"]
        for key in candidates:
            value = item.get(key, "").strip()
            if value and len(value) > 5:
                return value[:500]  # Truncate to 500 chars
        return ""

    def _extract_url(self, item: Dict[str, Any]) -> Optional[str]:
        """Extract URL from item."""
        candidates = ["url", "href", "link", "uri"]
        for key in candidates:
            value = item.get(key, "").strip()
            if value and (value.startswith("http://") or value.startswith("https://")):
                return value
        return None

    def _classify_type(self, item: Dict[str, Any], title: str, description: str) -> str:
        """Classify opportunity type deterministically."""
        text = f"{title} {description}".lower()

        # Type keywords
        directory_keywords = ["directory", "listing", "index", "catalog", "registry", "database"]
        job_keywords = ["job", "position", "vacancy", "hiring", "recruit", "employment", "role"]
        lead_keywords = ["lead", "prospect", "contact", "referral", "client", "customer"]
        request_keywords = ["request", "need", "want", "looking for", "seeking", "help wanted"]

        # Count keyword matches
        directory_score = sum(1 for kw in directory_keywords if kw in text)
        job_score = sum(1 for kw in job_keywords if kw in text)
        lead_score = sum(1 for kw in lead_keywords if kw in text)
        request_score = sum(1 for kw in request_keywords if kw in text)

        # Determine type by highest score
        scores = {
            "directory": directory_score,
            "job": job_score,
            "lead": lead_score,
            "request": request_score
        }

        if max(scores.values()) > 0:
            return max(scores, key=scores.get)

        return "unknown"

    def _extract_signals(
        self, item: Dict[str, Any], title: str, description: str, url: Optional[str]
    ) -> OpportunitySignals:
        """Extract signals from item."""
        text = f"{title} {description}".lower()

        # Contact signal
        contact_keywords = ["email", "phone", "contact", "reach", "call", "message", "whatsapp"]
        has_contact = any(kw in text for kw in contact_keywords) or bool(
            item.get("email") or item.get("phone") or item.get("contact")
        )

        # Price signal
        price_keywords = ["price", "cost", "fee", "rate", "salary", "$", "€", "£", "amount"]
        has_price = any(kw in text for kw in price_keywords) or bool(
            item.get("price") or item.get("cost") or item.get("rate")
        )

        # Deadline signal
        deadline_keywords = ["deadline", "due", "expires", "until", "by", "close date", "application close"]
        has_deadline = any(kw in text for kw in deadline_keywords) or bool(
            item.get("deadline") or item.get("due_date")
        )

        return OpportunitySignals(
            has_contact=has_contact,
            has_price=has_price,
            has_deadline=has_deadline
        )

    def _calculate_confidence(
        self, item: Dict[str, Any], opp_type: str, signals: OpportunitySignals
    ) -> float:
        """Calculate confidence deterministically based on multiple factors."""
        confidence = 0.3  # Base confidence for any opportunity

        # 1. Type classification quality (0.0 - 0.35)
        type_scores = {
            "directory": 0.35,
            "job": 0.30,
            "lead": 0.25,
            "request": 0.25,
            "unknown": 0.10
        }
        confidence += type_scores.get(opp_type, 0.10)

        # 2. Signal richness (0.0 - 0.25)
        signal_count = sum([signals.has_contact, signals.has_price, signals.has_deadline])
        confidence += min(signal_count * 0.08, 0.25)

        # 3. Content completeness and quality (0.0 - 0.25)
        non_empty_fields = sum(1 for v in item.values() if v and str(v).strip())
        field_quality = min(non_empty_fields / 5.0, 0.15)
        confidence += field_quality

        # 4. Content length bonus for substantive items (0.0 - 0.1)
        content_length = len(str(item.get("content", ""))) + len(str(item.get("title", "")))
        if content_length > 100:
            confidence += 0.1
        elif content_length > 50:
            confidence += 0.05

        # Clamp to [0, 1]
        return min(max(confidence, 0.0), 1.0)
