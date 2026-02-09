"""
Capability Boundary Model
Deterministic task classification: DIGITAL, PHYSICAL, HYBRID
No LLM usage, read-only classification only
"""

from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import List, Tuple, Dict, Any, Optional
import json
import re


class Capability(Enum):
    """Task capability classification"""
    DIGITAL = "digital"
    PHYSICAL = "physical"
    HYBRID = "hybrid"


@dataclass
class ClassificationResult:
    """Result of task capability classification"""
    
    task_description: str
    capability: Capability
    confidence: float  # 0.0 to 1.0
    evidence_keywords: List[str]
    reasoning: str
    classified_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "task_description": self.task_description,
            "capability": self.capability.value,
            "confidence": self.confidence,
            "evidence_keywords": self.evidence_keywords,
            "reasoning": self.reasoning,
            "classified_at": self.classified_at.isoformat(),
        }


class CapabilityBoundaryModel:
    """
    Deterministic capability boundary classification.
    Uses keyword + action heuristics to classify tasks.
    """
    
    # Digital keywords - Buddy can execute these
    DIGITAL_KEYWORDS = {
        # Web/Browse activities
        "browse", "web", "search", "google", "website", "url", "link",
        "page", "screenshot", "screenshot", "view", "read",
        
        # Form activities
        "form", "submit", "fill", "input", "field", "checkbox", "select",
        "button", "click", "type", "enter", "keyboard",
        
        # Data extraction
        "extract", "parse", "scrape", "copy", "paste", "select",
        "highlight", "collect", "gather", "download",
        
        # Email/Communication
        "email", "send", "mail", "message", "compose", "reply",
        "forward", "attachment", "inbox",
        
        # Data processing
        "process", "analyze", "calculate", "compare", "filter",
        "sort", "aggregate", "count", "sum", "average", "total",
        
        # File operations
        "file", "upload", "download", "save", "load", "create",
        "write", "read", "export", "import", "convert",
        
        # API operations
        "api", "rest", "json", "request", "response", "call",
        "fetch", "get", "post", "endpoint",
        
        # Database operations
        "database", "query", "db", "sql", "record", "table",
        "schema", "field", "column", "row",
        
        # Code/Automation
        "code", "script", "run", "execute", "automate", "program",
        "logic", "condition", "loop", "function", "method",
        
        # UI Interaction
        "ui", "interface", "button", "menu", "navigation", "tab",
        "window", "dialog", "modal", "dropdown", "slider",
        
        # Clipboard/Copy
        "clipboard", "copy", "paste", "cut", "duplicate",
        
        # Screenshot/Monitor
        "screenshot", "capture", "snapshot", "record", "monitor",
        
        # Verification
        "verify", "check", "validate", "confirm", "assert",
        "compare", "match", "validate", "test",
        
        # Text operations
        "text", "string", "word", "character", "regex",
        "replace", "find", "split", "join", "format",
    }
    
    # Physical keywords - User/human required
    PHYSICAL_KEYWORDS = {
        # Phone/Voice
        "call", "phone", "dial", "voice", "speak", "talk",
        "conversation", "meeting", "conference",
        
        # In-person/Visit
        "visit", "go", "travel", "visit", "meet", "in-person",
        "location", "address", "office", "store", "warehouse",
        
        # Signing/Legal
        "sign", "signature", "document", "contract", "legal",
        "notary", "witness", "approval", "authorize",
        
        # Shipping/Logistics
        "ship", "mail", "deliver", "pickup", "parcel", "package",
        "post", "courier", "carrier", "freight", "logistics",
        
        # Packing/Handling
        "pack", "unpack", "box", "seal", "wrap", "tape",
        "handle", "transport", "carry", "lift", "move",
        
        # Manufacturing/Assembly
        "manufacture", "assemble", "build", "construct", "install",
        "fabricate", "weld", "cut", "drill", "machine",
        
        # Inspection/Physical verification
        "inspect", "examine", "look", "check", "verify", "observe",
        "see", "witness", "physical", "tangible", "touch",
        
        # Human decision/Approval
        "approve", "authorize", "decision", "judgment", "discretion",
        "human", "person", "operator", "manager", "executive",
        
        # Handoff/Transfer
        "handoff", "transfer", "give", "receive", "exchange",
        "hand", "take", "pass", "handover",
        
        # Printing/Physical output
        "print", "print", "paper", "document", "physical",
        "hardcopy", "ink", "printer",
        
        # Physical inventory
        "inventory", "stock", "shelf", "warehouse", "storage",
        "physical", "count", "tangible",
        
        # Warehouse/Retail
        "warehouse", "store", "retail", "inventory", "stock",
        "shelf", "aisle", "bin", "location",
        
        # Payment/Cash
        "pay", "payment", "cash", "check", "money", "transfer",
        "credit", "debit", "account",
    }
    
    # Hybrid keywords - Requires handoff or approval
    HYBRID_KEYWORDS = {
        "handoff", "approval", "authorization", "wait",
        "approval", "review", "decision", "confirm", "notify",
        "escalate", "manager", "owner", "stakeholder",
    }
    
    # Action patterns that indicate capability
    DIGITAL_ACTIONS = [
        r"(navigate|go to|visit|open).*\b(website|url|page|link|site)\b",
        r"(fill|complete|submit).*form",
        r"(extract|scrape|collect).*data",
        r"(send|compose).*email",
        r"(search|query|find).*\b(on|in|using)\b",
        r"(download|upload|save).*file",
        r"(call|query).*api",
        r"(read|parse).*\b(json|xml|csv|data)\b",
        r"(compare|analyze|process).*data",
        r"(click|type|select|enter).*",
        r"(screenshot|capture).*screen",
        r"(copy|paste).*",
        r"(verify|check|validate).*",
    ]
    
    PHYSICAL_ACTIONS = [
        r"(call|phone|dial).*",
        r"(visit|go to|travel to|meet).*\b(office|store|location|person)\b",
        r"(sign|authorize).*document",
        r"(ship|mail|deliver|send).*\b(package|item|goods)\b",
        r"(pack|unpack|wrap).*",
        r"(inspect|examine|look at).*physical",
        r"(approve|authorize).*manually",
        r"(print|print out).*",
        r"(hand.*|give|receive|transfer).*",
    ]
    
    def classify_task(
        self,
        task_description: str,
    ) -> ClassificationResult:
        """
        Classify a task as DIGITAL, PHYSICAL, or HYBRID.
        Uses deterministic keyword + action heuristics.
        """
        task_lower = task_description.lower()
        
        # Score keywords
        digital_score, digital_keywords = self._score_keywords(
            task_lower,
            self.DIGITAL_KEYWORDS,
        )
        
        physical_score, physical_keywords = self._score_keywords(
            task_lower,
            self.PHYSICAL_KEYWORDS,
        )
        
        hybrid_score, hybrid_keywords = self._score_keywords(
            task_lower,
            self.HYBRID_KEYWORDS,
        )
        
        # Score action patterns
        digital_actions = self._score_actions(
            task_lower,
            self.DIGITAL_ACTIONS,
        )
        physical_actions = self._score_actions(
            task_lower,
            self.PHYSICAL_ACTIONS,
        )
        
        # Combine scores
        digital_total = digital_score + digital_actions
        physical_total = physical_score + physical_actions
        hybrid_total = hybrid_score
        
        # Determine capability and confidence
        capability, confidence, evidence = self._determine_capability(
            digital_total,
            physical_total,
            hybrid_total,
            digital_keywords,
            physical_keywords,
            hybrid_keywords,
        )
        
        reasoning = self._generate_reasoning(
            capability,
            digital_score,
            physical_score,
            hybrid_score,
            digital_actions,
            physical_actions,
            evidence,
        )
        
        return ClassificationResult(
            task_description=task_description,
            capability=capability,
            confidence=confidence,
            evidence_keywords=evidence,
            reasoning=reasoning,
            classified_at=datetime.utcnow(),
        )
    
    def _score_keywords(
        self,
        text: str,
        keywords: set,
    ) -> Tuple[float, List[str]]:
        """Score text against keyword set"""
        found_keywords = []
        score = 0.0
        
        for keyword in keywords:
            # Use word boundaries to avoid partial matches
            pattern = r"\b" + re.escape(keyword) + r"\b"
            matches = len(re.findall(pattern, text))
            
            if matches > 0:
                found_keywords.append(keyword)
                # Each match contributes to score
                score += matches * 0.5
        
        return score, found_keywords
    
    def _score_actions(
        self,
        text: str,
        actions: List[str],
    ) -> float:
        """Score text against action patterns"""
        score = 0.0
        
        for pattern in actions:
            if re.search(pattern, text, re.IGNORECASE):
                score += 1.0
        
        return score
    
    def _determine_capability(
        self,
        digital_score: float,
        physical_score: float,
        hybrid_score: float,
        digital_keywords: List[str],
        physical_keywords: List[str],
        hybrid_keywords: List[str],
    ) -> Tuple[Capability, float, List[str]]:
        """Determine capability classification and confidence"""
        
        total_score = digital_score + physical_score + hybrid_score
        
        # If hybrid keywords present and scores are close, prefer hybrid
        if hybrid_keywords and abs(digital_score - physical_score) < 2.0:
            confidence = min(
                (hybrid_score + 1.0) / (total_score + 1.0),
                1.0,
            )
            return Capability.HYBRID, confidence, hybrid_keywords
        
        # If no strong signal, classify as hybrid
        if total_score < 1.0:
            return Capability.HYBRID, 0.5, []
        
        # Determine primary capability
        if digital_score > physical_score:
            confidence = min(
                digital_score / (total_score + 0.1),
                1.0,
            )
            return Capability.DIGITAL, confidence, digital_keywords
        
        elif physical_score > digital_score:
            confidence = min(
                physical_score / (total_score + 0.1),
                1.0,
            )
            return Capability.PHYSICAL, confidence, physical_keywords
        
        else:
            # Scores are equal, classify as hybrid
            return Capability.HYBRID, 0.5, []
    
    def _generate_reasoning(
        self,
        capability: Capability,
        digital_score: float,
        physical_score: float,
        hybrid_score: float,
        digital_actions: float,
        physical_actions: float,
        evidence: List[str],
    ) -> str:
        """Generate human-readable reasoning"""
        
        if capability == Capability.DIGITAL:
            return (
                f"Classified as DIGITAL based on digital keywords "
                f"(score: {digital_score:.1f}), digital action patterns "
                f"(score: {digital_actions:.1f}). Evidence: {', '.join(evidence[:3])}"
            )
        
        elif capability == Capability.PHYSICAL:
            return (
                f"Classified as PHYSICAL based on physical keywords "
                f"(score: {physical_score:.1f}), physical action patterns "
                f"(score: {physical_actions:.1f}). Evidence: {', '.join(evidence[:3])}"
            )
        
        else:  # HYBRID
            return (
                f"Classified as HYBRID: ambiguous task requiring handoff or approval. "
                f"Digital score: {digital_score:.1f}, Physical score: {physical_score:.1f}, "
                f"Hybrid indicators: {', '.join(evidence[:3]) if evidence else 'task complexity'}"
            )


# Global model instance
_model: Optional[CapabilityBoundaryModel] = None


def get_capability_model() -> CapabilityBoundaryModel:
    """Get or create global capability model"""
    global _model
    if _model is None:
        _model = CapabilityBoundaryModel()
    return _model


def classify_task(task_description: str) -> ClassificationResult:
    """Classify a task's capability (convenience function)"""
    model = get_capability_model()
    return model.classify_task(task_description)
