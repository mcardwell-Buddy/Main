"""
Action Readiness Engine (with Session Context)

Deterministic, session-aware readiness checker for intent candidates.
Pure function: no I/O, no side effects, no mission creation.

Session context is READ-ONLY during validation.
Context updates happen ONLY after READY confirmation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Dict, TYPE_CHECKING
import re
import logging

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from Back_End.session_context import SessionContext


class ReadinessDecision(str, Enum):
    READY = "READY"
    INCOMPLETE = "INCOMPLETE"
    QUESTION = "QUESTION"
    META = "META"
    AMBIGUOUS = "AMBIGUOUS"


class ConfidenceTier(str, Enum):
    CERTAIN = "CERTAIN"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


class ClarificationType(str, Enum):
    """Type of clarification needed (only set when decision ≠ READY)"""
    MISSING_OBJECT = "MISSING_OBJECT"
    MISSING_TARGET = "MISSING_TARGET"
    MISSING_TARGET_NO_CONTEXT = "MISSING_TARGET_NO_CONTEXT"
    AMBIGUOUS_REFERENCE = "AMBIGUOUS_REFERENCE"
    MULTI_INTENT = "MULTI_INTENT"
    TOO_VAGUE = "TOO_VAGUE"
    INTENT_AMBIGUOUS = "INTENT_AMBIGUOUS"
    CONSTRAINT_UNCLEAR = "CONSTRAINT_UNCLEAR"


@dataclass(frozen=True)
class IntentCandidate:
    intent: str
    confidence: float


@dataclass(frozen=True)
class ReadinessResult:
    decision: ReadinessDecision
    intent_candidates: List[IntentCandidate]
    confidence_tier: ConfidenceTier
    missing_fields: List[str]
    clarification_question: Optional[str]
    clarification_options: Optional[List[str]]
    missing_field: Optional[str] = None
    options: Optional[List[str]] = None
    
    # Structured mission fields (populated only when READY)
    intent: Optional[str] = None
    action_object: Optional[str] = None
    action_target: Optional[str] = None
    source_url: Optional[str] = None
    constraints: Optional[Dict] = None
    
    # Clarification type (populated only when decision ≠ READY)
    clarification_type: Optional[ClarificationType] = None


class ActionReadinessEngine:
    def __init__(self, session_context: Optional[Dict] = None):
        self._session_context = session_context or {}

    def validate(
        self,
        user_message: str,
        session_context: Optional[Dict] = None,
        intent: str = None,
        context_obj: Optional[SessionContext] = None,
    ) -> ReadinessResult:
        """
        Readiness validation with optional session context.
        
        Args:
            user_message: The chat message to validate
            session_context: Legacy dict context (backward compat)
            intent: The detected intent type
            context_obj: SessionContext object for pronoun/follow-up resolution
        
        Session context is READ-ONLY during validation.
        It may only fill gaps when unambiguous.
        """
        engine = ActionReadinessEngine(session_context=session_context or self._session_context)
        engine._context_obj = context_obj  # Read-only during evaluation
        intent_candidates = [IntentCandidate(intent=intent, confidence=1.0)]
        return engine.evaluate(user_message=user_message, intent_candidates=intent_candidates)

    def evaluate(
        self,
        user_message: str,
        intent_candidates: List[IntentCandidate],
    ) -> ReadinessResult:
        """
        PURE FUNCTION.
        No side effects.
        No IO.
        No mission creation.
        """
        message = (user_message or "").strip()
        message_lower = message.lower()

        if self._is_meta_question(message_lower):
            return ReadinessResult(
                decision=ReadinessDecision.META,
                intent_candidates=intent_candidates,
                confidence_tier=self._tier_from_confidence(self._top_confidence(intent_candidates)),
                missing_fields=[],
                clarification_question=None,
                clarification_options=None,
                intent=None,
                action_object=None,
                action_target=None,
                source_url=None,
                constraints=None,
                clarification_type=None,
            )

        if self._is_question(message_lower):
            return ReadinessResult(
                decision=ReadinessDecision.QUESTION,
                intent_candidates=intent_candidates,
                confidence_tier=self._tier_from_confidence(self._top_confidence(intent_candidates)),
                missing_fields=[],
                clarification_question=None,
                clarification_options=None,
                intent=None,
                action_object=None,
                action_target=None,
                source_url=None,
                constraints=None,
                clarification_type=None,
            )

        sorted_candidates = sorted(
            intent_candidates,
            key=lambda c: c.confidence,
            reverse=True,
        )

        if self._is_ambiguous(sorted_candidates):
            return ReadinessResult(
                decision=ReadinessDecision.AMBIGUOUS,
                intent_candidates=sorted_candidates,
                confidence_tier=self._tier_from_confidence(self._top_confidence(sorted_candidates)),
                missing_fields=[],
                clarification_question="Clarify intent: choose the most appropriate action.",
                clarification_options=[c.intent for c in sorted_candidates[:2]],
                intent=None,
                action_object=None,
                action_target=None,
                source_url=None,
                constraints=None,
                clarification_type=ClarificationType.INTENT_AMBIGUOUS,
            )

        top_candidate = sorted_candidates[0] if sorted_candidates else None
        top_confidence = self._top_confidence(sorted_candidates)
        confidence_tier = self._tier_from_confidence(top_confidence)

        missing_fields = self._missing_fields(message_lower, top_candidate)

        # Attempt context-safe resolution before declaring INCOMPLETE
        if missing_fields and hasattr(self, '_context_obj') and self._context_obj:
            missing_fields = self._try_resolve_from_context(
                message_lower, top_candidate, missing_fields
            )

        if missing_fields:
            clarification_type = self._determine_clarification_type(
                message_lower, top_candidate, missing_fields
            )
            clarification_options = self._build_clarification_options(missing_fields)
            return ReadinessResult(
                decision=ReadinessDecision.INCOMPLETE,
                intent_candidates=sorted_candidates,
                confidence_tier=confidence_tier,
                missing_fields=missing_fields,
                clarification_question=self._build_placeholder_clarification(missing_fields),
                clarification_options=clarification_options,
                missing_field=missing_fields[0] if missing_fields else None,
                options=clarification_options,
                intent=None,
                action_object=None,
                action_target=None,
                source_url=None,
                constraints=None,
                clarification_type=clarification_type,
            )

        # Extract structured fields for READY missions
        intent = top_candidate.intent if top_candidate else None
        
        # Try LLM extraction ONCE (primary intelligence)
        llm_fields = None
        if intent:
            llm_fields = self._llm_extract_fields(message_lower)
            logger.info(f"[LLM_EXTRACTION] Result: {llm_fields}")
        
        # Use LLM results first, regex as fallback
        action_object = None
        if llm_fields and llm_fields.get('action_object'):
            action_object = llm_fields['action_object']
            logger.info(f"[ACTION_OBJECT] Using LLM result: {action_object}")
        else:
            action_object = self._extract_action_object(message_lower, intent) if intent else None
        
        action_target = None
        source_url = None
        if llm_fields and llm_fields.get('source_url'):
            source_url = llm_fields['source_url']
            # Normalize to https:// if needed
            if source_url and not source_url.startswith('http'):
                source_url = f"https://{source_url}"
            logger.info(f"[SOURCE_URL] Using LLM result: {source_url}")
        else:
            # Fallback to regex for URL extraction
            action_target = self._extract_action_target(message_lower, intent)
            source_url = self._extract_source_url(message_lower, action_target)
        
        constraints = self._extract_constraints(message_lower)
        
        # Try context resolution for pronouns and "do it again"
        if hasattr(self, '_context_obj') and self._context_obj:
            action_object = action_object or self._try_resolve_action_object(message_lower)
            action_target = action_target or self._try_resolve_action_target(message_lower)
            source_url = source_url or self._try_resolve_source_url(message_lower)
            
            # Handle "do it again" with full context
            if self._is_repeat_command(message_lower):
                if self._context_obj.can_repeat_last_mission():
                    mission_fields = self._context_obj.get_repeated_mission_fields()
                    if mission_fields:
                        intent = mission_fields.get('intent', intent)
                        action_object = mission_fields.get('action_object', action_object)
                        action_target = mission_fields.get('action_target', action_target)
                        source_url = mission_fields.get('source_url', source_url)
                        constraints = mission_fields.get('constraints', constraints)

        return ReadinessResult(
            decision=ReadinessDecision.READY,
            intent_candidates=sorted_candidates,
            confidence_tier=confidence_tier,
            missing_fields=[],
            clarification_question=None,
            clarification_options=None,
            missing_field=None,
            options=None,
            intent=intent,
            action_object=action_object,
            action_target=action_target,
            source_url=source_url,
            constraints=constraints,
            clarification_type=None,
        )

    def _top_confidence(self, intent_candidates: List[IntentCandidate]) -> float:
        if not intent_candidates:
            return 0.0
        return max(c.confidence for c in intent_candidates)

    def _tier_from_confidence(self, confidence: float) -> ConfidenceTier:
        if confidence >= 0.85:
            return ConfidenceTier.CERTAIN
        if confidence >= 0.70:
            return ConfidenceTier.HIGH
        if confidence >= 0.50:
            return ConfidenceTier.MEDIUM
        if confidence >= 0.20:
            return ConfidenceTier.LOW
        return ConfidenceTier.UNKNOWN

    def _is_ambiguous(self, intent_candidates: List[IntentCandidate]) -> bool:
        if len(intent_candidates) < 2:
            return False
        first = intent_candidates[0].confidence
        second = intent_candidates[1].confidence
        return abs(first - second) < 0.10

    def _missing_fields(self, message_lower: str, candidate: Optional[IntentCandidate]) -> List[str]:
        if not candidate:
            return ["intent"]

        intent = candidate.intent.lower()
        missing: List[str] = []

        if intent == "repeat":
            # For repeat commands, check if context has a prior mission
            if hasattr(self, '_context_obj') and self._context_obj:
                if not self._context_obj.can_repeat_last_mission():
                    missing.append("prior_mission")
            else:
                missing.append("prior_mission")

        elif intent == "navigate":
            if not self._has_source_url(message_lower):
                missing.append("source_url")

        elif intent == "extract":
            if not self._has_source_url(message_lower):
                missing.append("source_url")
            if not self._has_action_object(message_lower):
                missing.append("action_object")

        elif intent == "search":
            if not self._has_action_object(message_lower):
                missing.append("action_object")
            # Search also requires source context
            if not self._has_source_url(message_lower):
                missing.append("source_url")

        elif intent == "research":
            # Research just needs an entity/topic
            if not self._has_action_object(message_lower):
                missing.append("action_object")

        elif intent == "calculate":
            if not self._has_expression(message_lower):
                missing.append("expression")

        return missing

    def _has_source_url(self, message_lower: str) -> bool:
        url_pattern = r"https?://[^\s]+"
        domain_pattern = r"\b[a-z0-9.-]+\.[a-z]{2,}\b"

        if re.search(url_pattern, message_lower) or re.search(domain_pattern, message_lower):
            return True

        if any(token in message_lower for token in ["there", "here", "this site", "that site", "this page", "that page"]):
            recent_urls = self._session_context.get("recent_urls") or []
            return len(recent_urls) > 0

        return False

    def _has_action_object(self, message_lower: str) -> bool:
        """Quick check if message mentions something to extract/search.
        LLM does the actual extraction - this is just a fast filter.
        """
        # Common data types
        data_keywords = ["email", "price", "title", "product", "company", "service", 
                        "review", "address", "contact", "name", "phone", "list", "info"]
        if any(word in message_lower for word in data_keywords):
            return True
        
        # Action verbs that indicate extraction
        action_keywords = ["find", "search", "get", "extract", "collect", "show", "provide"]
        if any(word in message_lower for word in action_keywords):
            return True
        
        return False

    def _has_expression(self, message_lower: str) -> bool:
        """Check for math expressions - this is structural, regex is fine."""
        # Math operators (structural pattern)
        if any(op in message_lower for op in ["+", "-", "*", "/", "="]):
            return True
        # Math keywords
        math_keywords = ["calculate", "compute", "sum", "add", "subtract", "multiply", "divide"]
        return any(word in message_lower for word in math_keywords)

    def _is_question(self, message_lower: str) -> bool:
        question_starts = (
            "how ",
            "what ",
            "why ",
            "when ",
            "where ",
            "who ",
            "can ",
            "could ",
            "should ",
            "would ",
            "is ",
            "are ",
        )
        return message_lower.endswith("?") or message_lower.startswith(question_starts)

    def _is_meta_question(self, message_lower: str) -> bool:
        """Check if asking about system capabilities."""
        meta_keywords = ["what can you do", "capabilities", "what are you", "help me understand", 
                        "how do you work", "what can you help"]
        return any(phrase in message_lower for phrase in meta_keywords)

    def _build_placeholder_clarification(self, missing_fields: List[str]) -> str:
        fields = ", ".join(missing_fields)
        return f"Missing required fields: {fields}"

    def _build_clarification_options(self, missing_fields: List[str]) -> Optional[List[str]]:
        """
        Build structured clarification options (if applicable).

        Deterministic only. Uses session context history when available.
        """
        if not missing_fields:
            return None

        if "source_url" in missing_fields:
            if hasattr(self, '_context_obj') and self._context_obj:
                options = list(self._context_obj.recent_source_urls)
            else:
                options = list(self._session_context.get("recent_urls") or [])
            return options or None

        if "action_object" in missing_fields:
            if hasattr(self, '_context_obj') and self._context_obj:
                options = list(self._context_obj.recent_action_objects)
            else:
                options = list(self._session_context.get("recent_action_objects") or [])
            return options or None

        return None

    def _determine_clarification_type(
        self, message_lower: str, candidate: Optional[IntentCandidate], missing_fields: List[str]
    ) -> ClarificationType:
        """Determine the specific type of clarification needed."""
        if not missing_fields:
            return ClarificationType.TOO_VAGUE
        
        # Check for vague terms
        vague_terms = {"stuff", "things", "data", "information", "some", "any", "something", "anything"}
        if any(term in message_lower for term in vague_terms):
            return ClarificationType.TOO_VAGUE
        
        # Check for ambiguous pronoun reference
        if "ambiguous_reference" in str(missing_fields):
            return ClarificationType.AMBIGUOUS_REFERENCE
        
        # Determine based on missing fields
        intent = candidate.intent.lower() if candidate else None
        
        # For extract/search: missing action_object
        if intent in {"extract", "search"} and "action_object" in missing_fields:
            return ClarificationType.MISSING_OBJECT
        
        # For any intent: missing source_url
        if "source_url" in missing_fields:
            return ClarificationType.MISSING_TARGET
        
        # For repeat: missing prior mission
        if "prior_mission" in missing_fields:
            return ClarificationType.TOO_VAGUE
        
        # Check for multi-step/multi-intent
        if "and" in message_lower and any(
            keyword in message_lower 
            for keyword in ["extract", "navigate", "search", "go", "find"]
        ):
            return ClarificationType.MULTI_INTENT
        
        # Check for unclear constraints
        if any(
            pattern in message_lower 
            for pattern in ["how many", "how", "format", "type", "kind"]
        ):
            return ClarificationType.CONSTRAINT_UNCLEAR
        
        # Default: missing target
        return ClarificationType.MISSING_TARGET

    def _extract_action_object(self, message_lower: str, intent: str) -> Optional[str]:
        """Extract what the user wants to extract/search/get.
        
        Note: This is a FALLBACK - LLM extraction is attempted first in evaluate().
        Only called if LLM fails. For short responses, just return the cleaned message.
        """
        # Short response (1-3 words) to clarification question
        # Handles: "What would you like to extract?" -> "emails"
        words = message_lower.strip().split()
        if len(words) <= 3 and not any(word in message_lower for word in ["?", "how", "why", "when", "where", "what"]):
            filtered_words = [w for w in words if w not in ["the", "a", "an", "some", "all", "any"]]
            if filtered_words:
                action_object = " ".join(filtered_words)
                logger.info(f"[ACTION_OBJECT] Short response: '{action_object}'")
                return action_object
        
        # Try regex patterns for common extraction requests
        # "extract <object> from <url>"
        extract_pattern = r"extract\s+(?:the\s+)?(?:top\s+\d+\s+)?(.+?)\s+from"
        match = re.search(extract_pattern, message_lower)
        if match:
            action_object = match.group(1).strip()
            logger.info(f"[ACTION_OBJECT] Regex extract pattern: '{action_object}'")
            return action_object
        
        # "get <object> from <url>"
        get_pattern = r"get\s+(?:the\s+)?(?:top\s+\d+\s+)?(.+?)\s+from"
        match = re.search(get_pattern, message_lower)
        if match:
            action_object = match.group(1).strip()
            logger.info(f"[ACTION_OBJECT] Regex get pattern: '{action_object}'")
            return action_object
        
        # "search for <object> on <url>"
        search_pattern = r"search\s+for\s+(.+?)\s+(?:on|from|at)"
        match = re.search(search_pattern, message_lower)
        if match:
            action_object = match.group(1).strip()
            logger.info(f"[ACTION_OBJECT] Regex search pattern: '{action_object}'")
            return action_object
        
        logger.warning(f"[ACTION_OBJECT] LLM extraction failed, no fallback: {message_lower[:80]}")
        return None

    def _extract_action_target(self, message_lower: str, intent: str) -> Optional[str]:
        """Extract where to extract/search/navigate."""
        url_match = re.search(r"https?://[^\s]+", message_lower)
        if url_match:
            return url_match.group(0)
        
        domain_match = re.search(r"\b([a-z0-9.-]+\.[a-z]{2,})\b", message_lower)
        if domain_match:
            return domain_match.group(1)
        
        return None

    def _extract_source_url(self, message_lower: str, action_target: Optional[str]) -> Optional[str]:
        """Convert action_target to full URL."""
        if not action_target:
            return None
        if action_target.startswith("http"):
            return action_target
        return f"https://{action_target}"

    def _extract_constraints(self, message_lower: str) -> Optional[Dict]:
        """Extract constraints like count, format."""
        constraints = {}
        
        count_match = re.search(r"(?:top|first)\s+(\d+)", message_lower)
        if count_match:
            constraints["count"] = int(count_match.group(1))
        
        return constraints if constraints else None

    # ====== Session Context Resolution (SAFE) ======
    
    def _is_pronoun_reference(self, message_lower: str) -> bool:
        """Detect pronoun references using LLM understanding."""
        # Simple keyword check - LLM will handle context resolution
        pronouns = ["it", "that", "those", "there", "same site", "same place"]
        return any(word in message_lower for word in pronouns)
    
    def _is_repeat_command(self, message_lower: str) -> bool:
        """Detect repeat commands using simple keywords - LLM handles full understanding."""
        repeat_keywords = ["again", "repeat", "retry", "redo"]
        return any(word in message_lower for word in repeat_keywords)
    
    def _try_resolve_action_object(self, message_lower: str) -> Optional[str]:
        """
        Resolve 'it', 'that', 'those' to previous action object.
        
        SAFE: Only returns value if exactly one object in context.
        """
        if not self._is_pronoun_reference(message_lower):
            return None
        
        if hasattr(self, '_context_obj') and self._context_obj:
            return self._context_obj.resolve_action_object()
        
        return None
    
    def _try_resolve_action_target(self, message_lower: str) -> Optional[str]:
        """
        Resolve 'there', 'the same site' to previous source URL.
        
        SAFE: Only returns value if exactly one URL in context.
        """
        target_refs = {r"\bgo\s+there\b", r"\bfrom\s+there\b", r"\bfrom\s+the\s+same\s+site\b"}
        
        if not any(re.search(ref, message_lower) for ref in target_refs):
            return None
        
        if hasattr(self, '_context_obj') and self._context_obj:
            resolved_url = self._context_obj.resolve_source_url()
            # Extract domain for action_target
            if resolved_url:
                domain = resolved_url.replace("https://", "").replace("http://", "").split("/")[0]
                return domain
        
        return None
    
    def _try_resolve_source_url(self, message_lower: str) -> Optional[str]:
        """
        Resolve implicit source URL from context when explicitly referenced.
        
        SAFE: Only returns value if:
        1. Message contains pronoun/reference keyword
        2. Context has exactly one unambiguous URL candidate
        """
        # Check for explicit pronoun references (must use word boundaries to avoid false matches)
        pronoun_patterns = {
            r"\bthere\b",
            r"\bhere\b",
            r"\bfrom\s+there\b",
            r"\bfrom\s+the\s+same\s+site\b",
            r"this site",
            r"that site",
            r"this page",
            r"that page",
        }
        has_pronoun_ref = any(re.search(p, message_lower) for p in pronoun_patterns)
        
        if not has_pronoun_ref:
            return None
        
        if hasattr(self, '_context_obj') and self._context_obj:
            return self._context_obj.resolve_source_url()
        
        return None
    
    def _try_resolve_from_context(
        self, message_lower: str, candidate, missing_fields: List[str]
    ) -> List[str]:
        """
        Attempt to fill missing fields from context.
        
        Only removes fields from missing_fields if:
        1. Context has exactly one unambiguous candidate
        2. Message contains pronoun/reference
        
        Returns: Updated missing_fields list
        """
        still_missing = list(missing_fields)
        
        if not hasattr(self, '_context_obj') or not self._context_obj:
            return still_missing
        
        intent = candidate.intent.lower() if candidate else ""
        
        # Try to resolve action_object for "it", "that"
        if "action_object" in still_missing:
            if self._try_resolve_action_object(message_lower):
                still_missing.remove("action_object")
        
        # Try to resolve action_target/source for "there", "same site"
        if "source_url" in still_missing:
            if self._try_resolve_source_url(message_lower):
                still_missing.remove("source_url")
        
        return still_missing

    def _llm_extract_fields(self, message: str) -> Optional[dict]:
        """Use LLM to extract structured fields from natural language requests.
        
        This is the PRIMARY extraction method. Handles any phrasing, any intent, any tool.
        As tools expand, this method automatically adapts without code changes.
        
        Examples:
        - "can you visit site.com and provide services" -> {action_object: "services", source_url: "site.com"}
        - "I need contact info from example.com" -> {action_object: "contact info", source_url: "example.com"}
        - "show me the team from website.com" -> {action_object: "team", source_url: "website.com"}
        - "extract emails" -> {action_object: "emails", source_url: null}
        - "get prices from shop.com" -> {action_object: "prices", source_url: "shop.com"}
        """
        try:
            from Back_End.llm_client import llm_client
            import json
            
            prompt = f"""Extract structured fields from this user message for a web automation task.

Message: "{message}"

Extract the following fields (return null if not present):
1. **action_object**: What data to extract/get/search for (e.g., "services", "prices", "contact info", "team members", "reviews")
2. **source_url**: The target website URL or domain (if mentioned)

Examples:
- "visit site.com and provide services" → {{"action_object": "services", "source_url": "site.com"}}
- "I need contact info from example.com" → {{"action_object": "contact info", "source_url": "example.com"}}
- "can you get prices from shop.com" → {{"action_object": "prices", "source_url": "shop.com"}}
- "extract emails" → {{"action_object": "emails", "source_url": null}}
- "show me team members at company.com" → {{"action_object": "team members", "source_url": "company.com"}}

Return ONLY a valid JSON object:
{{"action_object": "...", "source_url": "..."}}"""

            response = llm_client.complete(prompt, max_tokens=150, temperature=0.2)
            if not response:
                logger.warning("[LLM_EXTRACT] No response from LLM - falling back to regex")
                return None
            
            # Strip code fences and parse JSON
            response = response.strip()
            if response.startswith("```"):
                lines = response.split("```")
                response = lines[1] if len(lines) > 1 else lines[0]
                if response.startswith("json"):
                    response = response[4:]
            response = response.strip()
            
            data = json.loads(response)
            logger.info(f"[LLM_EXTRACT] Successfully extracted: {data}")
            return data
        except json.JSONDecodeError as e:
            logger.warning(f"[LLM_EXTRACT] JSON parse error: {e}, response: {response[:100]}")
            return None
        except Exception as e:
            logger.debug(f"[LLM_EXTRACT] Extraction failed: {e}")
            return None

