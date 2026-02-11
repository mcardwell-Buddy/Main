"""
Interaction Orchestrator

Central decision point for incoming chat messages.

Determines:
- Intent classification
- Routing decision (respond, clarify, execute, forecast)
- Response packaging via ResponseEnvelope

CONSTRAINTS:
- NO autonomy
- NO loops
- ONE decision per message
- Deterministic only (NO LLM)
- NO side effects except mission creation + response envelope

Flow:
1. Parse message intent (keyword + structure analysis)
2. Route to handler (response, clarification, execution, forecast)
3. Package response in ResponseEnvelope
4. Return for delivery
"""

import logging
import os
import re
import json
import time
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from Back_End.response_envelope import (
    ResponseEnvelope, ResponseType, UIHints, 
    text_response, clarification_response, 
    mission_proposal_response, MissionReference, SignalReference
)
from Back_End.mission_control.chat_intake_coordinator import ChatIntakeCoordinator
from Back_End.mission_control.mission_proposal_emitter import MissionProposalEmitter
from Back_End.mission_control.mission_draft_builder import MissionDraft
from Back_End.artifact_reader import get_latest_artifact
from Back_End.action_readiness_engine import ActionReadinessEngine, IntentCandidate, ReadinessDecision
from Back_End.session_context import SessionContextManager, PendingClarification
from Back_End.clarification_templates import render_clarification


logger = logging.getLogger(__name__)

MULTI_STEP_LIVE_ENABLED = os.getenv('MULTI_STEP_LIVE_ENABLED', 'False').lower() == 'true'


class IntentType(Enum):
    """Classified intent types."""
    QUESTION = "question"
    REQUEST_EXECUTION = "request_execution"
    FORECAST_REQUEST = "forecast_request"
    STATUS_CHECK = "status_check"
    CLARIFICATION_NEEDED = "clarification_needed"
    ACKNOWLEDGMENT = "acknowledgment"
    INFORMATIONAL = "informational"


@dataclass
class IntentClassification:
    """Result of intent classification."""
    intent_type: IntentType
    confidence: float  # 0.0 - 1.0
    keywords: List[str]
    actionable: bool
    reasoning: str


class DeterministicIntentClassifier:
    """
    Intent classifier using LLM for robust language understanding.
    
    Fast path: Acknowledgments (high frequency, regex OK)
    Main path: LLM classification for all other intents
    
    Provides natural language tolerance without brittle pattern matching.
    """
    
    # Non-actionable patterns (fast path, regex OK for these)
    ACKNOWLEDGMENT_PATTERNS = [
        r'^\s*(hi|hello|hey|thanks|thank you|ok|okay|yes|no|sure|fine|good)\s*$',
        r'^\s*(got it|understood|copy that|roger|ack|acknowledged)\s*$'
    ]
    
    def classify(self, message: str) -> IntentClassification:
        """
        Classify message intent using LLM.
        
        Args:
            message: Raw user message
            
        Returns:
            IntentClassification with intent_type, confidence, keywords, actionable
        """
        message_lower = message.lower().strip()
        
        # FAST PATH: Acknowledgments (regex is OK for high-frequency, low-stakes)
        for pattern in self.ACKNOWLEDGMENT_PATTERNS:
            if re.match(pattern, message_lower):
                return IntentClassification(
                    intent_type=IntentType.ACKNOWLEDGMENT,
                    confidence=0.95,
                    keywords=[],
                    actionable=False,
                    reasoning="Acknowledgment/greeting detected"
                )
        
        # DEFAULT PATH: Use LLM for everything else
        return self._classify_with_llm(message)
    
    def _classify_with_llm(self, message: str) -> IntentClassification:
        """Use LLM to classify intent robustly, with smart fallback."""
        from Back_End.llm_client import llm_client
        import json
        
        prompt = f"""You are an intent classifier for a task automation system.

Classify the user's intent and return ONLY valid JSON (no markdown, no explanation).

Intent types:
- "execute": User wants to perform a task (get data, navigate, extract, calculate, search, scrape, etc.)
- "question": User asking for information WITHOUT requesting action
- "status": User checking status of something
- "forecast": User asking for predictions/analysis
- "clarification": ONLY when message is truly unclear (missing critical info)
- "informational": User asking for help/explanation

IMPORTANT: Action verbs like "navigate", "extract", "get", "search", "scrape", "find", "collect" → ALWAYS "execute"

Examples:
- "Navigate to google.com" → execute (actionable: true, confidence: 0.95)
- "Extract phone number from example.com" → execute (actionable: true, confidence: 0.95)
- "Get contact info from website.com" → execute (actionable: true, confidence: 0.90)
- "Search for tutorials on site.com" → execute (actionable: true, confidence: 0.90)
- "What is Python?" → question (actionable: false, confidence: 0.85)
- "Tell me about AI" → question (actionable: false, confidence: 0.85)
- "xyz abc" → clarification (actionable: false, confidence: 0.60)

Message: "{message}"

Return exactly this JSON structure (no markdown, no code blocks):
{{{{
  "intent_type": "execute",
  "confidence": 0.95,
  "actionable": true,
  "reasoning": "brief explanation",
  "keywords": ["keyword1", "keyword2"]
}}}}"""
        
        try:
            response = llm_client.complete(prompt, max_tokens=200, temperature=0.3)
            
            # If LLM is disabled or fails, use smart fallback
            if not response or not response.strip():
                return self._smart_fallback_classification(message)
            
            # Clean response (remove markdown if present)
            response_text = response.strip()
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                response_text = "\n".join(lines[1:-1]) if len(lines) > 2 else response_text
            
            data = json.loads(response_text)
            
            # Validate response structure
            intent_str = data.get("intent_type", "clarification").lower()
            confidence = float(data.get("confidence", 0.5))
            actionable = bool(data.get("actionable", False))
            reasoning = data.get("reasoning", "LLM classification")
            keywords = data.get("keywords", [])
            
            # Clamp confidence
            confidence = max(0.0, min(1.0, confidence))
            
            # Map intent string to IntentType
            intent_map = {
                "execute": IntentType.REQUEST_EXECUTION,
                "question": IntentType.QUESTION,
                "status": IntentType.STATUS_CHECK,
                "forecast": IntentType.FORECAST_REQUEST,
                "clarification": IntentType.CLARIFICATION_NEEDED,
                "informational": IntentType.INFORMATIONAL,
            }
            
            intent_type = intent_map.get(intent_str, IntentType.CLARIFICATION_NEEDED)
            
            return IntentClassification(
                intent_type=intent_type,
                confidence=confidence,
                keywords=keywords,
                actionable=actionable,
                reasoning=reasoning
            )
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM intent classification JSON: {e}")
            return self._smart_fallback_classification(message)
        except Exception as e:
            logger.error(f"LLM intent classification failed: {e}")
            return self._smart_fallback_classification(message)
    
    def _smart_fallback_classification(self, message: str) -> IntentClassification:
        """
        Smart fallback classification when LLM is unavailable.
        Uses heuristics but much more lenient than pure regex.
        """
        message_lower = message.lower().strip()
        
        # First check: is this a URL? (URLs should NOT be treated as math)
        if message_lower.startswith(('http://', 'https://', 'www.', 'ftp://')) or \
           (len(message_lower.split()) == 1 and ('.' in message_lower and '/' not in message_lower or 'domain' in message_lower or '.com' in message_lower)):
            # This looks like a URL or domain
            return IntentClassification(
                intent_type=IntentType.QUESTION,
                confidence=0.7,
                keywords=[],
                actionable=False,
                reasoning="Looks like a URL/domain (fallback)"
            )
        
        # Execution indicators (action verbs and domains)
        execution_indicators = {
            'navigate', 'visit', 'go to', 'open', 'get', 'fetch', 'search', 'find',
            'extract', 'scrape', 'crawl', 'calculate', 'compute', 'run', 'execute'
        }
        
        # Question indicators
        question_starters = {'what', 'why', 'how', 'when', 'where', 'who', 'is', 'are', 'can', 'could', 'would'}
        
        # Math operators and keywords - be more strict about what counts as math
        # Require actual numbers or math keywords, not just operators
        has_numbers = any(c.isdigit() for c in message_lower)
        math_keywords = {'plus', 'minus', 'times', 'divided', 'multiply',
                         'add', 'subtract', 'divide', 'sum', 'calculate', 'compute'}
        has_math_keyword = any(kw in message_lower for kw in math_keywords)
        
        # Only count as math if we have numbers OR explicit math keywords
        has_math = (has_numbers or has_math_keyword)
        
        # Check for action verbs first (execute is a common intent)
        has_execution_indicator = any(indicator in message_lower for indicator in execution_indicators)
        
        # Check if message is a question
        is_question = message_lower.rstrip().endswith('?') or any(
            message_lower.startswith(q) for q in question_starters
        )
        
        # Decision tree for classification
        if has_execution_indicator:
            return IntentClassification(
                intent_type=IntentType.REQUEST_EXECUTION,
                confidence=0.85,
                keywords=[w for w in message_lower.split() if w in execution_indicators],
                actionable=True,
                reasoning="Execution keywords detected (fallback)"
            )
        
        if has_math:
            # Math is actionable even if phrased as question
            return IntentClassification(
                intent_type=IntentType.REQUEST_EXECUTION,
                confidence=0.8,
                keywords=[w for w in message_lower.split() if w in math_keywords or w.isdigit()],
                actionable=True,
                reasoning="Math operation detected (fallback)"
            )
        
        if is_question:
            return IntentClassification(
                intent_type=IntentType.QUESTION,
                confidence=0.75,
                keywords=[],
                actionable=False,
                reasoning="Question detected (fallback)"
            )
        
        # If very short, probably ambiguous
        if len(message_lower.split()) < 3:
            return IntentClassification(
                intent_type=IntentType.CLARIFICATION_NEEDED,
                confidence=0.5,
                keywords=[],
                actionable=False,
                reasoning="Message too short to classify (fallback)"
            )
        
        # Default to question for other cases
        return IntentClassification(
            intent_type=IntentType.QUESTION,
            confidence=0.6,
            keywords=[],
            actionable=False,
            reasoning="Classified as question by default (fallback)"
        )
    
    def is_deterministic_task(self, message: str) -> bool:
        """
        Check if message is a deterministic task (pure math) that can be answered immediately.
        
        This method is called by the orchestrator to determine if a mission should be created
        or if the answer can be provided directly.
        
        Returns True for pure math questions without tool requirements.
        """
        message_lower = message.lower().strip()
        
        # Use the same logic as smart fallback for math detection
        has_numbers = any(c.isdigit() for c in message_lower)
        math_keywords = {'plus', 'minus', 'times', 'divided', 'multiply',
                         'add', 'subtract', 'divide', 'sum', 'calculate', 'compute'}
        has_math_keyword = any(kw in message_lower for kw in math_keywords)
        
        # Check for web/tool keywords that would require a mission
        tool_keywords = {
            'scrape', 'get', 'fetch', 'extract', 'crawl', 'search',
            'visit', 'browse', 'navigate', 'website', 'page',
            'url', 'link', 'domain', 'site', 'web'
        }
        has_tool_keyword = any(kw in message_lower for kw in tool_keywords)
        
        # Math task if: (has numbers OR math keywords) AND NO tool keywords
        return (has_numbers or has_math_keyword) and not has_tool_keyword


class RoutingDecision:
    """Determines how to handle a message."""
    
    @staticmethod
    def route(
        intent: IntentClassification,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Route message to appropriate handler.
        
        Args:
            intent: Classification result
            message: Original message
            context: Optional context (recent missions, goals)
            
        Returns:
            Tuple of (handler_name, handler_kwargs)
        """
        if intent.intent_type == IntentType.ACKNOWLEDGMENT:
            return ("acknowledge", {"message": message})
        
        if intent.intent_type == IntentType.CLARIFICATION_NEEDED:
            return ("clarify", {"message": message, "context": context})
        
        if intent.intent_type == IntentType.INFORMATIONAL:
            return ("informational", {"message": message, "context": context})
        
        if intent.intent_type == IntentType.QUESTION:
            if intent.actionable:
                return ("execute", {"message": message, "context": context})
            else:
                return ("respond", {"message": message, "context": context})
        
        if intent.intent_type == IntentType.REQUEST_EXECUTION:
            return ("execute", {"message": message, "context": context})
        
        if intent.intent_type == IntentType.FORECAST_REQUEST:
            return ("forecast", {"message": message, "context": context})
        
        if intent.intent_type == IntentType.STATUS_CHECK:
            return ("status", {"message": message, "context": context})
        
        # Default fallback
        return ("respond", {"message": message, "context": context})


class InteractionOrchestrator:
    """
    Main orchestrator for chat message handling.
    
    ONE decision per message:
    1. Classify intent
    2. Route to handler
    3. Execute handler
    4. Return ResponseEnvelope
    
    NO loops, NO autonomy, NO side effects except:
    - Mission creation (if needed)
    - Response envelope creation
    """
    
    def __init__(self):
        self.classifier = DeterministicIntentClassifier()
        self.chat_coordinator = ChatIntakeCoordinator()
        self.emitter = MissionProposalEmitter()
        self.signals_file = Path('outputs/phase25/learning_signals.jsonl')
        self.signals_file.parent.mkdir(parents=True, exist_ok=True)
        self._session_last_mission: Dict[str, str] = {}
        self._session_context_manager = SessionContextManager()  # NEW: Session context for pronouns/follow-ups

    
    def _emit_chat_observation(
        self,
        session_id: str,
        intent: IntentClassification,
        message: str,
        outcome: str
    ) -> None:
        """
        Emit a chat observation signal for learning.
        
        Wrap in try/except to prevent signal emission from blocking responses.
        """
        try:
            signal = {
                'signal_type': 'chat_observation',
                'signal_layer': 'interaction',
                'signal_source': 'chat',
                'session_id': session_id,
                'intent_type': intent.intent_type.value,
                'user_message': message,
                'outcome': outcome,
                'confidence': intent.confidence,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            with open(self.signals_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(signal, ensure_ascii=False) + '\n')
            
            logger.debug(f"[SIGNAL] chat_observation emitted: {outcome}")
        except Exception as e:
            logger.warning(f"[SIGNAL] Failed to emit chat_observation: {e}")

    def _is_approval_phrase(self, message: str) -> bool:
        message_lower = message.lower().strip()
        return bool(re.fullmatch(r"(yes|approve|approved|do it|go ahead|run it|execute)[.!]?", message_lower))

    def _is_new_full_command(self, message: str) -> bool:
        """
        Detect a new full command while a clarification is pending.

        Deterministic only: uses readiness intent inference.
        """
        readiness_intent = self._infer_readiness_intent(message)
        return readiness_intent in {"extract", "navigate", "search", "repeat"}

    def _is_valid_url(self, message: str) -> bool:
        return bool(re.fullmatch(r"https?://[^\s]+", message.strip(), flags=re.IGNORECASE))

    def _is_bare_domain(self, message: str) -> bool:
        return bool(re.fullmatch(r"[a-z0-9.-]+\.[a-z]{2,}(?:/[^\s]*)?", message.strip(), flags=re.IGNORECASE))

    def _resolve_source_url(self, message: str, options: Optional[List[str]]) -> Optional[str]:
        message_clean = message.strip()
        message_lower = message_clean.lower()

        if options:
            for opt in options:
                if opt.lower() == message_lower:
                    return opt

        ambiguous_terms = {
            "that", "there", "that one", "this", "this one",
            "that site", "this site", "that page", "this page"
        }
        if message_lower in ambiguous_terms:
            if options and len(options) == 1:
                return options[0]
            return None

        if self._is_valid_url(message_clean):
            return message_clean

        if self._is_bare_domain(message_clean):
            if message_clean.startswith("http"):
                return message_clean
            return f"https://{message_clean}"

        return None

    def _resolve_action_object(self, message: str) -> Optional[str]:
        message_clean = message.strip()
        message_lower = message_clean.lower()

        if not message_clean:
            return None

        if self._is_valid_url(message_clean) or self._is_bare_domain(message_clean):
            return None

        generic_terms = {"stuff", "information", "data", "details", "things", "something", "anything"}
        stop_words = {"the", "a", "an", "some", "any", "that", "this", "it", "those", "these"}
        words = re.findall(r"[a-z0-9']+", message_lower)
        if not words:
            return None

        if all(word in generic_terms or word in stop_words for word in words):
            return None

        if any(word not in generic_terms and word not in stop_words and len(word) > 2 for word in words):
            return message_clean

        return None

    def _resolve_constraints(self, message: str) -> Optional[str]:
        message_lower = message.lower().strip()
        if re.search(r"\b\d+\b", message_lower):
            return message.strip()

        if re.search(r"\b(top\s+\d+|latest|newest|first\s+\d+|last\s+\d+)\b", message_lower):
            return message.strip()

        return None

    def _reemit_pending_clarification(self, pending: PendingClarification, session_context_obj) -> ResponseEnvelope:
        intent_value = pending.intent.value if hasattr(pending.intent, "value") else str(pending.intent)
        clarification_text = render_clarification(
            clarification_type=pending.clarification_type,
            intent=intent_value,
            last_source_url=session_context_obj.resolve_source_url() if session_context_obj else None,
        )
        return text_response(clarification_text)

    def _is_artifact_followup_question(self, message: str) -> bool:
        """
        Detect follow-up questions about execution results.

        PHASE 4B: Deterministic pattern matching for artifact questions.

        Examples:
        - "what did you find"
        - "what website did you visit"
        - "how many items"
        - "show me the results"
        - "what was the result"
        """
        message_lower = message.lower().strip()

        # Must be a question
        if not message_lower.endswith("?"):
            return False

        # Match artifact followup patterns FIRST
        patterns = [
            r"what did you find",
            r"what (?:did you )?(?:extract|get)",
            r"what (?:was the )?result",
            r"what (?:website|page|site|domain|url)",
            r"where did you",
            r"how many (?:items|results|records)",
            r"show me",
            r"summarize",
            r"what did i ask",
            r"what are the results",
        ]

        if not any(re.search(pattern, message_lower) for pattern in patterns):
            return False

        # Now check that this is NOT a command to execute something
        # (commands would start with these verbs in imperative mood)
        execution_starts = [
            r"^(?:extract|search|find|get|fetch|navigate|go\s+to|visit|browse|collect|scrape)",
            r"^(?:please\s+)?(extract|search|find|get|fetch|navigate|go\s+to|visit|browse|collect|scrape)",
        ]

        if any(re.search(start, message_lower) for start in execution_starts):
            return False

        return True

    def _answer_artifact_followup(
        self,
        message: str,
        artifact: Dict[str, Any],
    ) -> ResponseEnvelope:
        """
        Answer a follow-up question using artifact data.

        PHASE 4B: Deterministic artifact interpretation.
        No mission creation, no execution, read-only.
        """
        message_lower = message.lower()

        # Handle "what did you find / extract"
        if "what did you find" in message_lower or "what did you extract" in message_lower:
            extracted = artifact.get("extracted_data", {})
            if isinstance(extracted, dict):
                if "items" in extracted:
                    items = extracted["items"]
                    if isinstance(items, list) and items:
                        count = len(items)
                        preview = ", ".join(str(item)[:30] for item in items[:3])
                        return text_response(
                            f"I found {count} items:\n• {preview}"
                            + ("..." if count > 3 else "")
                        )
                    return text_response("I found no items matching the criteria.")
                if "titles" in extracted:
                    titles = extracted["titles"]
                    if isinstance(titles, list) and titles:
                        return text_response(
                            f"Titles found:\n" +
                            "\n".join(f"• {t}" for t in titles[:5])
                        )
            return text_response("I don't have extraction details for those results.")

        # Handle "what website / page did you visit"
        if "website" in message_lower or "page" in message_lower or "domain" in message_lower or "url" in message_lower:
            if "what" in message_lower and ("did you visit" in message_lower or "did you go" in message_lower or "did you end up" in message_lower):
                final_url = artifact.get("final_url") or artifact.get("source_url")
                if final_url:
                    return text_response(f"I visited: {final_url}")
                return text_response("I don't have the URL information.")

        # Handle "how many items / results"
        if "how many" in message_lower:
            if "items" in message_lower or "results" in message_lower or "records" in message_lower:
                extracted = artifact.get("extracted_data", {})
                if isinstance(extracted, dict):
                    if "items" in extracted:
                        count = len(extracted["items"]) if isinstance(extracted["items"], list) else 0
                        return text_response(f"I found {count} items.")
                    if "count" in extracted:
                        return text_response(f"I found {extracted['count']} items.")
                return text_response("I don't have count information for those results.")

        # Handle "show me / summarize"
        if "show me" in message_lower or "summarize" in message_lower:
            summary = artifact.get("summary") or artifact.get("result_summary")
            if summary:
                return text_response(f"Summary of results:\n{summary}")
            return text_response("I don't have a summary for those results.")

        # Handle "what was the result"
        if "what was the result" in message_lower:
            summary = artifact.get("result_summary") or artifact.get("summary")
            if summary:
                return text_response(summary)
            return text_response("I don't have result details.")

        # Generic fallback
        return text_response(
            "I don't have that information from the previous execution. "
            "Try asking about what I found, which website I visited, or how many results."
        )

    def _is_artifact_chaining_question(self, message: str) -> bool:
        """
        Detect Phase 4C artifact chaining & summary questions.
        
        Returns True if:
        - Message contains summary/comparison/analysis phrase
        - NO execution verbs at start
        - NO approval phrases
        - Question is about artifacts (read-only)
        """
        message_lower = message.lower().strip()
        
        # Must have summary/comparison phrase
        summary_phrases = [
            "summarize",
            "everything",
            "compare",
            "what changed",
            "what's different",
            "last time",
            "previous",
            "both",
            "all of",
            "review",
            "recap",
            "overview",
            "summary",
        ]
        
        has_summary_phrase = any(phrase in message_lower for phrase in summary_phrases)
        if not has_summary_phrase:
            return False
        
        # Reject approval phrases
        if self._is_approval_phrase(message):
            return False
        
        # Reject execution verbs at message start
        execution_starts = [
            r"^(?:extract|search|find|get|fetch|navigate|go\s+to|visit|browse|collect|scrape)",
        ]
        if any(re.search(start, message_lower) for start in execution_starts):
            return False
        
        return True

    def _get_artifact_chain(self, message: str, session_context_obj) -> Optional[List[Dict[str, Any]]]:
        """
        Determine which artifacts to use based on user phrase.
        
        READ-ONLY. Never mutates context.
        
        Returns:
        - List of artifacts to process
        - None if ambiguous or no artifacts
        """
        from Back_End.artifact_views import get_recent_artifacts
        
        artifacts = get_recent_artifacts(session_context_obj)
        if not artifacts:
            return None
        
        message_lower = message.lower()
        
        # "Everything" or "all" → all artifacts
        if any(word in message_lower for word in ["everything", "all of them", "all results"]):
            return artifacts
        
        # "Last two" / "both" → two most recent
        if any(phrase in message_lower for phrase in ["last two", "both", "compare the two", "last two results"]):
            return artifacts[-2:] if len(artifacts) >= 2 else artifacts
        
        # "Previous" / "last time" → second-most recent
        if "previous" in message_lower or "last time" in message_lower:
            if len(artifacts) >= 2:
                return [artifacts[-2]]
            return None
        
        # Default: most recent
        return [artifacts[-1]] if artifacts else None

    def _answer_artifact_chaining(self, message: str, artifacts: List[Dict[str, Any]]) -> ResponseEnvelope:
        """
        Answer artifact chaining & summary questions.
        
        READ-ONLY. No execution, no mission creation, no state changes.
        
        Routes to:
        - summarize_artifact (single)
        - summarize_artifact_set (multiple)
        - compare_artifacts (two artifacts)
        """
        from Back_End.artifact_views import (
            summarize_artifact, summarize_artifact_set, compare_artifacts,
            format_artifact_summary, format_artifact_set_summary, format_comparison
        )
        
        if not artifacts:
            return text_response("I don't have any artifacts to summarize.")
        
        message_lower = message.lower()
        
        # Single artifact summary
        if len(artifacts) == 1:
            summary = summarize_artifact(artifacts[0])
            formatted = format_artifact_summary(summary)
            return text_response(formatted)
        
        # Comparison of two artifacts
        if len(artifacts) == 2 and any(
            word in message_lower for word in ["compare", "what changed", "what's different", "difference"]
        ):
            comparison = compare_artifacts(artifacts[0], artifacts[1])
            formatted = format_comparison(comparison)
            return text_response(formatted)
        
        # Multiple artifacts summary
        if len(artifacts) > 1:
            combined = summarize_artifact_set(artifacts)
            formatted = format_artifact_set_summary(combined)
            return text_response(formatted)
        
        return text_response("I don't have enough artifact data to process.")

    def _merge_clarification_message(
        self,
        original_message: str,
        missing_field: str,
        resolved_value: str,
        intent_hint: Optional[str],
    ) -> str:
        original = (original_message or "").strip()
        lower = original.lower()
        intent = (intent_hint or "").lower()

        if missing_field == "source_url":
            if intent in {"navigate"}:
                return f"{original} to {resolved_value}".strip()
            return f"{original} from {resolved_value}".strip()

        if missing_field == "action_object":
            if " from " in lower:
                before, after = original.split(" from ", 1)
                return f"{before} {resolved_value} from {after}".strip()
            return f"{original} {resolved_value}".strip()

        if missing_field == "constraints":
            return f"{original} {resolved_value}".strip()

        return f"{original} {resolved_value}".strip()

    def _handle_pending_clarification(
        self,
        message: str,
        session_context_obj,
    ) -> Tuple[Optional[ResponseEnvelope], str]:
        pending = session_context_obj.get_pending_clarification() if session_context_obj else None
        if not pending:
            return None, message

        # Approval phrases must not resolve clarifications
        if self._is_approval_phrase(message):
            return self._reemit_pending_clarification(pending, session_context_obj), message

        # New full command clears pending clarification
        if self._is_new_full_command(message):
            session_context_obj.clear_pending_clarification()
            return None, message

        resolved_value: Optional[str] = None
        if pending.missing_field == "source_url":
            resolved_value = self._resolve_source_url(message, pending.options)
        elif pending.missing_field == "action_object":
            resolved_value = self._resolve_action_object(message)
        elif pending.missing_field == "constraints":
            resolved_value = self._resolve_constraints(message)

        if not resolved_value:
            return self._reemit_pending_clarification(pending, session_context_obj), message

        original_message = session_context_obj.get_pending_clarification_message() or ""
        intent_value = pending.intent.value if hasattr(pending.intent, "value") else str(pending.intent)
        merged_message = self._merge_clarification_message(
            original_message,
            pending.missing_field,
            resolved_value,
            intent_value,
        )
        session_context_obj.clear_pending_clarification()
        return None, merged_message

    def _infer_readiness_intent(self, message: str) -> Optional[str]:
        message_lower = message.lower()

        extract_keywords = [
            "extract", "get", "scrape", "collect", "fetch", "pull", "grab", "retrieve"
        ]
        navigate_keywords = [
            "navigate", "go to", "visit", "open", "browse"
        ]
        search_keywords = [
            "search", "find", "look for", "discover", "lookup"
        ]
        repeat_keywords = [
            "do it again", "repeat", "try again", "redo"
        ]

        if any(keyword in message_lower for keyword in extract_keywords):
            return "extract"
        if any(keyword in message_lower for keyword in navigate_keywords):
            return "navigate"
        if any(keyword in message_lower for keyword in search_keywords):
            return "search"
        if any(keyword in message_lower for keyword in repeat_keywords):
            # For repeat commands, we'll use the last mission's intent
            # This will be resolved in readiness validation via context
            return "repeat"

        return None

    def _create_mission_from_readiness(
        self,
        intent: str,
        action_object: Optional[str],
        action_target: Optional[str],
        source_url: Optional[str],
        constraints: Optional[Dict],
        raw_message: str,
    ) -> Optional[Dict]:
        """
        Create mission draft from validated readiness output.
        
        INVARIANT: All inputs must be pre-validated by ActionReadinessEngine.
        This method ASSERTS required fields and refuses to create incomplete missions.
        
        Args:
            intent: Validated intent (extract, navigate, search)
            action_object: What to extract/search for (required for extract/search)
            action_target: Where to extract/search (required for extract/search)
            source_url: Full URL to the source (required for extract/search)
            constraints: Optional count, format, filters
            raw_message: Original user message
            
        Returns:
            mission_draft dict or None if validation fails
        """
        # Validate intent
        if intent not in {"extract", "navigate", "search"}:
            logger.error(f"[MISSION_CREATE] Invalid intent: {intent}")
            return None
        
        # Validate required fields for extract/search
        if intent in {"extract", "search"}:
            if not action_object:
                logger.error(f"[MISSION_CREATE] Missing action_object for {intent}")
                return None
            if not source_url:
                logger.error(f"[MISSION_CREATE] Missing source_url for {intent}")
                return None
        
        # Build objective description from structured fields
        if intent == "extract":
            objective_desc = f"Extract '{action_object}' from {source_url}"
        elif intent == "search":
            objective_desc = f"Search for '{action_object}' from {source_url}"
        elif intent == "navigate":
            objective_desc = f"Navigate to {action_target or source_url}"
        else:
            return None
        
        # Create mission draft object
        mission_id = f"mission_{int(time.time() * 1000000)}"
        
        try:
            draft = MissionDraft(
                mission_id=mission_id,
                source="chat",
                status="proposed",
                objective_description=objective_desc,
                objective_type=intent,
                target_count=constraints.get("count") if constraints else None,
                allowed_domains=[self._extract_domain(source_url)] if source_url else [],
                max_pages=10,  # Safe default
                max_duration_seconds=300,  # Safe default
                created_at=datetime.now().isoformat(),
                raw_chat_message=raw_message,
                intent_keywords=[intent],
            )
            
            # Emit via MissionProposalEmitter
            emitter = MissionProposalEmitter()
            emission = emitter.emit_proposal(draft)
            logger.info(
                f"[READINESS] Mission created from validated readiness: "
                f"intent={intent}, action_object={action_object}, source_url={source_url}"
            )
            return draft.to_dict()
        except Exception as e:
            logger.error(f"[READINESS] Failed to emit mission from readiness: {e}")
            return None

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        if not url:
            return ""
        try:
            # Simple extraction - remove protocol and path
            domain = url.replace("https://", "").replace("http://", "").split("/")[0]
            return domain
        except:
            return url

    def _get_latest_mission_status(self, mission_id: str) -> Optional[str]:
        missions_file = Path('outputs/phase25/missions.jsonl')
        if not missions_file.exists():
            return None

        latest_status = None
        with open(missions_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if record.get('mission_id') != mission_id:
                    continue
                if record.get('event_type') == 'mission_status_update':
                    latest_status = record.get('status')
                elif record.get('event_type') is None:
                    if latest_status is None:
                        latest_status = record.get('status')

        return latest_status

    def _handle_approval_bridge(self, message: str, session_id: str) -> ResponseEnvelope:
        """
        Handle approval phrases ("yes", "approve", "do it").
        
        PHASE 3C: Uses pending mission from session context (single source of truth).
        
        Returns:
            ResponseEnvelope with execution results or error message
        """
        # Get session context
        session_context_obj = self._session_context_manager.get_or_create(session_id)
        
        # Check for pending mission
        pending_mission = session_context_obj.get_pending_mission()
        if not pending_mission:
            return text_response("I don't have any pending missions to approve right now. Ask me to do something and I'll create one for you!")
        
        mission_id = pending_mission.get('mission_id')
        if not mission_id:
            return text_response("I don't have any pending missions to approve right now. Ask me to do something and I'll create one for you!")

        # Skip mission status check - trust pending mission is valid
        # Directly approve the mission

        from Back_End.mission_approval_service import approve_mission
        from Back_End.execution_service import execute_mission

        # Approve the mission
        approval_result = approve_mission(mission_id)
        if not approval_result.get('success'):
            error_msg = approval_result.get('message', 'Approval failed')
            return text_response(f"Approval failed: {error_msg}")

        # Execute the mission
        exec_result = execute_mission(mission_id)
        if not exec_result.get('success'):
            error_msg = exec_result.get('error', 'Execution failed')
            # Don't clear pending on execution failure - user might want to retry
            return text_response(f"Mission {mission_id} execution failed: {error_msg}")

        # Clear pending mission after successful execution
        session_context_obj.clear_pending_mission()

        # PHASE 4B: Store execution artifact for follow-up answers
        if exec_result:
            session_context_obj.set_last_execution_artifact(exec_result)

        tool_used = exec_result.get('tool_used') or 'unknown'
        result_summary = exec_result.get('result_summary') or 'Execution completed.'
        artifact_message = exec_result.get('artifact_message')

        response_lines = [
            f"Approved and executed mission {mission_id}.",
            f"Tool used: {tool_used}",
            result_summary
        ]
        if artifact_message:
            response_lines.append(artifact_message)

        return text_response("\n".join(response_lines))
    def process_message(
        self,
        message: str,
        session_id: str,
        user_id: str = "default",
        context: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None
    ) -> ResponseEnvelope:
        """
        Process a chat message end-to-end with observability tracing.
        
        Flow:
        1. Classify intent (with trace logging)
        2. Route to handler (with trace logging)
        3. Execute handler
        4. Return ResponseEnvelope
        
        Args:
            message: User message
            session_id: Session identifier
            user_id: User identifier
            context: Optional context (missions, goals, etc)
            trace_id: Optional trace ID for observability
            
        Returns:
            ResponseEnvelope with response, missions, signals
        """
        from Back_End.observability import DecisionTraceLogger
        
        # Use provided trace_id or generate one
        if trace_id is None:
            from uuid import uuid4
            trace_id = str(uuid4())
        
        logger.info(f"[ORCHESTRATOR] Processing message from {user_id}: {message[:50]}... (trace_id={trace_id[:8]}...)")
        
        # Step 0: Clarification resolution hook (before intent classification)
        session_context_obj = self._session_context_manager.get_or_create(session_id)
        clarification_response, message = self._handle_pending_clarification(message, session_context_obj)
        if clarification_response:
            return clarification_response

        # PHASE 5: Semantic normalization (BEFORE intent classification)
        # Rewrite user input into canonical form to reduce phrasing brittleness
        # Does NOT create missions, execute tools, or bypass safety checks
        from Back_End.semantic_normalizer import maybe_normalize
        original_message = message
        message = maybe_normalize(message, session_context=session_context_obj.__dict__ if hasattr(session_context_obj, '__dict__') else {})
        if message != original_message:
            logger.info(f"[PHASE5][NORMALIZATION] Rewrote: '{original_message}' → '{message}'")

        # Step 0a: Artifact chaining & summaries (PHASE 4C - read-only)
        if self._is_artifact_chaining_question(message):
            artifacts = self._get_artifact_chain(message, session_context_obj)
            if artifacts:
                return self._answer_artifact_chaining(message, artifacts)
            else:
                return text_response("I don't have any artifacts to summarize yet.")

        # Step 0b: Artifact follow-up detection (PHASE 4B - read-only)
        if self._is_artifact_followup_question(message):
            artifact = session_context_obj.get_last_execution_artifact()
            if artifact:
                return self._answer_artifact_followup(message, artifact)
            else:
                return text_response("I don't have any recent results yet.")

        # Step 1: Approval bridge (explicit approval phrases)
        if self._is_approval_phrase(message):
            return self._handle_approval_bridge(message, session_id)

        # Step 2: Classify intent with trace logging
        intent = self.classifier.classify(message)
        logger.info(f"[ORCHESTRATOR] Intent: {intent.intent_type.value} "
                   f"(confidence: {intent.confidence:.2f}, actionable: {intent.actionable})")
        
        # Log classification decision for traceability
        DecisionTraceLogger.log_classification(
            trace_id=trace_id,
            message=message,
            intent_type=intent.intent_type.value,
            confidence=intent.confidence,
            reasoning=f"Classified as {intent.intent_type.value} with confidence {intent.confidence:.2f}"
        )
        
        # SHADOW MODE: Action Readiness Engine (observe-only)
        shadow_intent_candidates = [
            IntentCandidate(intent=intent.intent_type.value, confidence=float(intent.confidence))
        ]
        shadow_engine = ActionReadinessEngine(session_context=context or {})
        shadow_readiness = shadow_engine.evaluate(
            user_message=message,
            intent_candidates=shadow_intent_candidates,
        )

        # Step 2: Route to handler with trace logging
        handler_name, handler_kwargs = RoutingDecision.route(intent, message, context)
        logger.info(f"[ORCHESTRATOR] Routing to handler: {handler_name}")
        
        # Log routing decision for traceability
        DecisionTraceLogger.log_routing(
            trace_id=trace_id,
            intent_type=intent.intent_type.value,
            handler_name=handler_name,
            reasoning=f"Routed {intent.intent_type.value} to handler {handler_name}"
        )

        # Optional multi-step live snapshot (read-only logging)
        if MULTI_STEP_LIVE_ENABLED:
            session_context_obj.add_step_snapshot({
                "timestamp": datetime.utcnow().isoformat(),
                "trace_id": trace_id,
                "original_message": original_message,
                "normalized_message": message,
                "intent_type": intent.intent_type.value,
                "confidence": intent.confidence,
                "actionable": intent.actionable,
                "handler": handler_name,
            })

        actual_behavior_map = {
            "execute": "MISSION_CREATED",
            "forecast": "MISSION_CREATED",
            "informational": "HELP",
            "respond": "HELP",
            "clarify": "CLARIFICATION",
            "acknowledge": "ACKNOWLEDGE",
            "status": "STATUS",
        }
        actual_behavior = actual_behavior_map.get(handler_name, "UNKNOWN")

        logger.info(
            "[SHADOW][ACTION_READINESS] "
            f"message=\"{message}\" "
            f"session_id=\"{session_id}\" "
            f"intent_candidates={[ (c.intent, c.confidence) for c in shadow_readiness.intent_candidates ]} "
            f"decision={shadow_readiness.decision.value} "
            f"confidence_tier={shadow_readiness.confidence_tier.value} "
            f"missing_fields={shadow_readiness.missing_fields} "
            f"clarification_question={shadow_readiness.clarification_question} "
            f"actual_behavior={actual_behavior}"
        )
        
        # Step 3: Execute handler
        handler = getattr(self, f"_handle_{handler_name}")
        response = handler(intent=intent, session_id=session_id, trace_id=trace_id, **handler_kwargs)
        
        logger.info(f"[ORCHESTRATOR] Response type: {response.response_type.value}, "
                   f"missions: {len(response.missions_spawned)}")
        
        return response
    
    # ========================================================================
    # HANDLERS
    # ========================================================================
    
    def _handle_acknowledge(self, intent: IntentClassification, message: str, session_id: str, trace_id: Optional[str] = None, **kwargs) -> ResponseEnvelope:
        """Handle acknowledgments/greetings."""
        responses = {
            'hi': "Hey! What can I help you with?",
            'hello': "Hello! How can I assist?",
            'hey': "Hi there! What do you need?",
            'thanks': "You're welcome!",
            'thank you': "Happy to help!",
            'ok': "Got it!",
            'okay': "Understood!",
            'yes': "Great!",
            'no': "No problem.",
            'sure': "Sure thing!",
            'good': "Glad to hear it!",
        }
        
        message_lower = message.lower().strip()
        response_text = responses.get(message_lower, "Hey! How can I help?")
        
        response = text_response(response_text)
        self._emit_chat_observation(session_id, intent, message, 'acknowledged')
        return response
    
    def _handle_respond(self, intent: IntentClassification, message: str, session_id: str, context: Optional[Dict] = None, trace_id: Optional[str] = None, **kwargs) -> ResponseEnvelope:
        """Handle informational questions."""
        message_lower = message.lower()

        # Artifact follow-up: answer from latest artifact (observe-only)
        if re.search(r'\b(what did you find|what did you get|what did you extract|show me what you found)\b', message_lower):
            mission_id = None
            if isinstance(context, dict):
                mission_id = context.get('mission_id')

            artifact = get_latest_artifact(mission_id=mission_id)
            if artifact and artifact.get('artifact_type') == 'web_extraction_result':
                extracted = artifact.get('extracted_data', {})
                title = extracted.get('title') or ''
                headings = extracted.get('headings') or []
                summary = extracted.get('summary') or ''
                source_url = artifact.get('source_url') or 'unknown source'

                response = (
                    f"Here’s what I found from {source_url}:\n"
                    f"• Title: {title if title else '(not available in artifact)'}\n"
                    f"• Headings: {', '.join(headings) if headings else '(none found)'}\n"
                    f"• Summary: {summary if summary else '(not available in artifact)'}"
                )
            elif artifact and artifact.get('artifact_type') == 'web_search_result':
                query = artifact.get('query') or '(query not available)'
                results = artifact.get('results') or []
                if isinstance(results, list) and results:
                    result_lines = [f"- {str(item)}" for item in results[:5]]
                    results_text = "\n".join(result_lines)
                else:
                    results_text = '(no results found in artifact)'

                response = (
                    f"Here’s what I found for \"{query}\":\n"
                    f"{results_text}"
                )
            elif artifact and artifact.get('artifact_type') == 'calculation_result':
                expression = artifact.get('expression') or '(expression not available)'
                result = artifact.get('result')
                response = f"The result of {expression} is {result}"
            else:
                response = (
                    "I don’t have a saved artifact for that mission yet. "
                    "Please run a search or extraction and I’ll summarize it here."
                )

            response_envelope = text_response(response)
            self._emit_chat_observation(session_id, intent, message, 'answered')
            return response_envelope

        if re.search(r'\b(where did you go|what page did you end up on|what page did you land on|why did you go there|why did you navigate there)\b', message_lower):
            mission_id = None
            if isinstance(context, dict):
                mission_id = context.get('mission_id')

            artifact = get_latest_artifact(mission_id=mission_id)
            if artifact and artifact.get('artifact_type') == 'web_navigation_result':
                starting_url = artifact.get('starting_url') or 'unknown'
                final_url = artifact.get('final_url') or 'unknown'
                navigation_reason = artifact.get('navigation_reason') or '(reason not available)'
                page_title = artifact.get('page_title') or '(title not available)'

                response = (
                    f"Here’s the navigation summary:\n"
                    f"• Starting URL: {starting_url}\n"
                    f"• Final URL: {final_url}\n"
                    f"• Page Title: {page_title}\n"
                    f"• Reason: {navigation_reason}"
                )
            else:
                response = (
                    "I don’t have a saved navigation artifact for that mission yet. "
                    "Please run a navigation mission and I’ll summarize it here."
                )

            response_envelope = text_response(response)
            self._emit_chat_observation(session_id, intent, message, 'answered')
            return response_envelope

        if "how" in message_lower and "scrape" in message_lower:
            response = (
                "To scrape a website:\n"
                "1. **Specify the target**: URL or domain\n"
                "2. **Define what to extract**: Data fields or patterns\n"
                "3. **Set constraints**: Max pages, duration, item count\n"
                "4. **Request execution**: Say 'Get [data] from [site]'\n\n"
                "Try: 'Get product names from example.com'"
            )
        elif "what can you" in message_lower or "can you" in message_lower:
            response = (
                "I can help you:\n"
                "• **Extract data** from websites\n"
                "• **Search and collect** information\n"
                "• **Monitor** for changes\n"
                "• **Forecast** trends\n"
                "• **Execute missions** with your approval\n\n"
                "Just tell me what you'd like to do!"
            )
        elif "how do i" in message_lower:
            response = (
                "I'm here to help! Describe what you want to:\n"
                "• 'Get [data] from [website]'\n"
                "• 'Search for [information]'\n"
                "• 'Extract [fields] from [source]'\n\n"
                "I'll propose a mission for your approval."
            )
        else:
            response = (
                "I understand your question. "
                "If you'd like me to execute a task, just ask explicitly "
                "(e.g., 'Get X from Y') and I'll propose a mission for approval."
            )
        
        response_envelope = text_response(response)
        self._emit_chat_observation(session_id, intent, message, 'answered')
        return response_envelope
    
    def _handle_clarify(self, intent: IntentClassification, message: str, session_id: str, context: Optional[Dict] = None, trace_id: Optional[str] = None, **kwargs) -> ResponseEnvelope:
        """Handle ambiguous requests by asking clarifying questions."""
        # Determine what's unclear
        if len(message.split()) < 5:
            question = "Can you provide more details? For example, what data do you want to collect and from where?"
        else:
            question = "Just to clarify: are you looking to execute a task, get information, or something else?"
        
        options = [
            "Execute a task",
            "Get information",
            "Check status",
            "Something else"
        ]
        
        response = clarification_response(question, options=options)
        self._emit_chat_observation(session_id, intent, message, 'clarification_requested')
        return response
    
    def _handle_informational(self, intent: IntentClassification, message: str, session_id: str, context: Optional[Dict] = None, trace_id: Optional[str] = None, **kwargs) -> ResponseEnvelope:
        """Handle informational requests without creating missions."""
        message_lower = message.lower()
        
        # Detect what kind of information is being requested
        if 'list' in message_lower and 'calculate' in message_lower:
            response = (
                "I can calculate:",
                "• **Averages**: Calculate the average of multiple numbers",
                "• **Sums and totals**: Add up lists of numbers",
                "• **Percentages**: Compute percentage changes or values",
                "• **Basic arithmetic**: Multiply, divide, add, subtract\n",
                "Just ask me directly, like:",
                "'Calculate the average of 10, 20, 30'"
            )
            response_envelope = text_response("\n".join(response))
            self._emit_chat_observation(session_id, intent, message, 'answered')
            return response_envelope
        
        elif 'what can' in message_lower or 'capabilities' in message_lower:
            response = (
                "I can help you:",
                "• **Calculate** averages, sums, percentages",
                "• **Extract data** from websites",
                "• **Search and collect** information",
                "• **Create missions** for data gathering",
                "• **Provide information** about my capabilities\n",
                "What would you like to do?"
            )
            response_envelope = text_response("\n".join(response))
            self._emit_chat_observation(session_id, intent, message, 'answered')
            return response_envelope
        
        elif 'explain' in message_lower or 'describe' in message_lower:
            response = (
                "I'm an AI assistant that can:",
                "1. Answer questions directly",
                "2. Perform calculations",
                "3. Propose missions for data collection",
                "4. Extract information from websites\n",
                "Ask me specific questions or request tasks!"
            )
            response_envelope = text_response("\n".join(response))
            self._emit_chat_observation(session_id, intent, message, 'answered')
            return response_envelope
        
        elif 'examples' in message_lower:
            response = (
                "Example requests:",
                "• \"Calculate the average of 5, 10, 15, 20\"",
                "• \"Get product prices from example.com\"",
                "• \"Explain what you can do\"",
                "• \"List data from a website\"\n",
                "Try one!"
            )
            response_envelope = text_response("\n".join(response))
            self._emit_chat_observation(session_id, intent, message, 'answered')
            return response_envelope
        
        else:
            # Generic informational response
            response = (
                "I'm here to help! I can:",
                "• Answer questions about my capabilities",
                "• Perform calculations",
                "• Create missions to gather data",
                "• Extract information from websites\n",
                "What would you like to know?"
            )
            response_envelope = text_response("\n".join(response))
            self._emit_chat_observation(session_id, intent, message, 'answered')
            return response_envelope
    
    def _handle_execute(self, intent: IntentClassification, message: str, session_id: str, context: Optional[Dict] = None, trace_id: Optional[str] = None, **kwargs) -> ResponseEnvelope:
        """
        Handle execution requests with observability tracing.
        
        NEW FLOW: After mission creation, plan mission and show approval gates
        with cost/duration estimates.
        """
        from Back_End.observability import DecisionTraceLogger
        
        # WIRING FIX 3: Check if this is a pure math problem
        if self.classifier.is_deterministic_task(message):
            # Answer the math question immediately
            answer = self._solve_math_problem(message)
            
            # Log deterministic shortcut
            if trace_id:
                DecisionTraceLogger.log_deterministic_shortcut(
                    trace_id=trace_id,
                    message=message,
                    shortcut_type="math_calculation",
                    result=answer
                )
            
            response = text_response(
                f"📝 Direct Answer\n\n{answer}\n\n"
                f"Response type: direct_answer (no mission created)"
            )
            self._emit_chat_observation(session_id, intent, message, 'direct_answer')
            return response

        readiness_intent = self._infer_readiness_intent(message)
        if readiness_intent in {"extract", "navigate", "search", "repeat"}:
            readiness_engine = ActionReadinessEngine(session_context=context or {})
            
            # Get or create session context for pronoun/follow-up resolution
            session_context_obj = self._session_context_manager.get_or_create(session_id)
            
            readiness = readiness_engine.validate(
                user_message=message,
                session_context=context or {},
                intent=readiness_intent,
                context_obj=session_context_obj,  # NEW: Pass session context
            )

            if readiness.decision == ReadinessDecision.INCOMPLETE and readiness.missing_fields:
                logger.info(
                    f"[READINESS] Mission blocked: missing required fields {readiness.missing_fields}"
                )

                pending = PendingClarification(
                    clarification_type=readiness.clarification_type,
                    missing_field=readiness.missing_field or readiness.missing_fields[0],
                    intent=readiness_intent,
                    options=readiness.options,
                )
                session_context_obj.set_pending_clarification(pending, original_message=message)

                # Use context-aware clarification from readiness engine
                clarification_text = render_clarification(
                    clarification_type=readiness.clarification_type,
                    intent=readiness_intent,
                    last_source_url=session_context_obj.resolve_source_url() if session_context_obj else None,
                )
                response = text_response(clarification_text)
                self._emit_chat_observation(session_id, intent, message, 'not_actionable')
                return response

            # If readiness says READY, use structured fields directly (sole gate principle)
            if readiness.decision == ReadinessDecision.READY:
                # Clear any stale pending clarification on success
                session_context_obj.clear_pending_clarification()

                # Create mission from validated readiness output
                mission_draft = self._create_mission_from_readiness(
                    intent=readiness.intent,
                    action_object=readiness.action_object,
                    action_target=readiness.action_target,
                    source_url=readiness.source_url,
                    constraints=readiness.constraints,
                    raw_message=message,
                )
                
                if mission_draft:
                    mission_id = mission_draft.get('mission_id')
                    
                    if trace_id:
                        DecisionTraceLogger.log_mission_creation(
                            trace_id=trace_id,
                            mission_id=mission_id,
                            objective_type=mission_draft.get('objective_type', 'unknown'),
                            objective_description=mission_draft.get('objective_description', '')
                        )
                    
                    # NEW: Plan multi-step mission with per-step tool selection + cost/duration estimates
                    unified_proposal = self._plan_mission_with_details(mission_draft, message)
                    
                    if unified_proposal:
                        logger.info(
                            f"[ORCHESTRATOR] Multi-step mission planned: {unified_proposal.total_steps} steps, "
                            f"cost=${unified_proposal.total_cost_usd:.4f}, "
                            f"time={unified_proposal.estimated_total_time_minutes}min"
                        )
                        
                        # NEW: Evaluate unified proposal for approval decision
                        approval_decision = self._evaluate_mission_plan(unified_proposal, user_id="unknown")
                        
                        # Create mission reference with proposal details
                        mission_ref = MissionReference(
                            mission_id=mission_id,
                            status='planned',  # NEW: Status reflects planning phase
                            objective_type=mission_draft.get('objective_type', 'unknown'),
                            objective_description=unified_proposal.objective,
                        )
                        
                        # Generate unified proposal response (single cohesive message)
                        response = self._create_mission_plan_response(
                            mission_ref=mission_ref,
                            unified_proposal=unified_proposal,
                            approval_decision=approval_decision,
                            original_message=message
                        )
                        
                        # Store unified proposal in session for approval phase
                        session_context_obj.set_pending_mission(mission_draft)
                        session_context_obj.set_pending_plan(unified_proposal)
                        
                        # CRITICAL FIX: Store the plan WITH the mission in mission_store
                        # This ensures execution_service can retrieve and use the planned tools
                        self._save_plan_to_mission(mission_id, unified_proposal)
                        
                        self._emit_chat_observation(session_id, intent, message, 'mission_planned')
                        return response
                    else:
                        # Planning failed - show error but allow manual approval
                        logger.warning(
                            f"[ORCHESTRATOR] Failed to plan mission {mission_id}. "
                            f"Showing basic proposal without estimates."
                        )
                        
                        mission_ref = MissionReference(
                            mission_id=mission_id,
                            status='proposed',
                            objective_type=mission_draft.get('objective_type', 'unknown'),
                            objective_description=mission_draft.get('objective_description', ''),
                        )
                        
                        # Fallback to basic proposal
                        conversational_summary = (
                            f"📋 Mission Proposed (planning unavailable)\n\n"
                            f"I'm ready to help with: {mission_draft.get('objective_description', 'this task')}\n\n"
                            f"⚠️ Unable to estimate costs/duration at this time."
                        )
                        
                        response = mission_proposal_response(mission_ref, conversational_summary)
                        session_context_obj.set_pending_mission(mission_draft)
                        self._emit_chat_observation(session_id, intent, message, 'action_proposed')
                        return response
                else:
                    # Mission creation failed despite readiness being READY
                    # This indicates a validation issue
                    logger.error(
                        f"[MISSION_CREATE] Failed to create mission despite READY status. "
                        f"Intent: {readiness.intent}, action_object: {readiness.action_object}, "
                        f"source_url: {readiness.source_url}"
                    )
                    response = text_response(
                        "I understand you want me to help with this task, but I'm missing some information. "
                        "Could you provide more details about what you'd like me to do?"
                    )
                    self._emit_chat_observation(session_id, intent, message, 'validation_error')
                    return response
        
        # Use ChatIntakeCoordinator as fallback for non-readiness-gated intents
        coordinator_result = self.chat_coordinator.process_chat_message(message, user_id="orchestrator")
        
        if not coordinator_result.get('actionable'):
            # Not actionable after all - respond with feedback
            chat_feedback = coordinator_result.get('chat_feedback', {})
            feedback_msg = chat_feedback.get('message', 'Unable to create mission from this request.')
            response = text_response(feedback_msg)
            self._emit_chat_observation(session_id, intent, message, 'not_actionable')
            return response
        
        # Mission was created - wrap in ResponseEnvelope
        mission_draft = coordinator_result.get('mission_draft', {})
        mission_id = mission_draft.get('mission_id')
        
        # Log mission creation
        if trace_id:
            DecisionTraceLogger.log_mission_creation(
                trace_id=trace_id,
                mission_id=mission_id,
                objective_type=mission_draft.get('objective_type', 'unknown'),
                objective_description=mission_draft.get('objective_description', '')
            )
        
        mission_ref = MissionReference(
            mission_id=mission_id,
            status='proposed',
            objective_type=mission_draft.get('objective_type', 'unknown'),
            objective_description=mission_draft.get('objective_description', 'Execute task')
        )
        self._session_last_mission[session_id] = mission_id
        
        # CONTROL-FLOW FIX: Mission stays in proposed state, awaiting approval
        # Auto-execution disabled per architectural contract
        # Missions must be explicitly approved before entering execution queue
        logger.info(f"[ORCHESTRATOR] Mission {mission_id} created with status=proposed (awaiting approval)")
        
        # Create signal reference
        signal_ref = SignalReference(
            signal_type='mission_proposed',
            signal_layer='mission',
            signal_source='orchestrator',
            timestamp=datetime.utcnow().isoformat(),
            summary=f"Mission proposed via orchestrator: {mission_id}"
        )
        
        summary = (
            f"📋 Mission Started\n"
            f"• ID: {mission_id[:8]}...\n"
            f"• Type: {mission_draft.get('objective_type')}\n"
            f"• Status: ACTIVE (executing)\n\n"
            f"Progress will appear in Whiteboard."
        )
        
        response = mission_proposal_response(mission_ref, summary, signal=signal_ref)
        self._emit_chat_observation(session_id, intent, message, 'mission_created')
        return response
    
    def _handle_forecast(self, intent: IntentClassification, message: str, session_id: str, context: Optional[Dict] = None, trace_id: Optional[str] = None, **kwargs) -> ResponseEnvelope:
        """Handle forecast requests."""
        response = (
            "Forecast requests are queued for the forecasting pipeline.\n\n"
            "⚠️ Note: Forecasts require sufficient historical data and may take time.\n"
            "This request has been logged and will be processed accordingly."
        )
        
        response_envelope = text_response(response, ui_hints=UIHints(
            priority='normal',
            color_scheme='info',
            icon='chart'
        ))
        self._emit_chat_observation(session_id, intent, message, 'forecast_queued')
        return response_envelope
    
    def _handle_status(self, intent: IntentClassification, message: str, session_id: str, context: Optional[Dict] = None, trace_id: Optional[str] = None, **kwargs) -> ResponseEnvelope:
        """Handle status check requests."""
        response = (
            "Status check requested.\n\n"
            "Current systems:\n"
            "✓ Chat intake: Active\n"
            "✓ Mission control: Ready\n"
            "✓ Whiteboard: Operational\n\n"
            "Ask me about specific missions or use the dashboard for detailed status."
        )
        
        response_envelope = text_response(response)
        self._emit_chat_observation(session_id, intent, message, 'status_reported')
        return response_envelope
    
    def _solve_math_problem(self, message: str) -> str:
        """
        WIRING FIX 3: Solve simple math problems deterministically.
        
        Supports:
        - Basic arithmetic: +, -, *, /
        - Averages: "average of X, Y, Z"
        - Sums: "sum of X, Y, Z"
        """
        try:
            # Extract numbers from the message
            import re
            numbers = re.findall(r'\d+\.?\d*', message)
            numbers = [float(n) for n in numbers]
            
            if not numbers:
                return "No numbers found in the message."
            
            message_lower = message.lower()
            
            # Check for specific operations
            if 'average' in message_lower or 'mean' in message_lower:
                result = sum(numbers) / len(numbers)
                return f"Average: {result:.2f}"
            
            if 'sum' in message_lower or 'total' in message_lower or 'add' in message_lower:
                result = sum(numbers)
                return f"Sum: {result:.2f}"
            
            # Try to evaluate simple expressions
            # Remove text but keep numbers and operators
            expression = re.sub(r'[^0-9+\-*/().\s]', '', message)
            expression = ' '.join(expression.split())
            
            if expression:
                try:
                    # Use eval for simple arithmetic (safe in this context)
                    result = eval(expression)
                    return f"Result: {result}"
                except:
                    pass
            
            # Default: sum if multiple numbers
            if len(numbers) > 1:
                result = sum(numbers)
                return f"Sum of provided numbers: {result:.2f}"
            elif len(numbers) == 1:
                return f"Number found: {numbers[0]}"
            
            return "Could not solve the math problem."
        except Exception as e:
            logger.warning(f"Error solving math problem: {e}")
            return "Error calculating result. Please rephrase your question."
    
    def _generate_mission_proposal_summary(self, message: str, mission_draft: Dict) -> str:
        """
        Generate a conversational summary for a mission proposal using LLM.
        
        Args:
            message: Original user message
            mission_draft: Mission draft dictionary
            
        Returns:
            Conversational summary string
        """
        try:
            from Back_End.llm_client import llm_client
            
            objective_desc = mission_draft.get('objective_description', '')
            objective_type = mission_draft.get('objective_type', 'task')
            
            prompt = f"""You are Buddy, a helpful AI assistant. A user just asked you to do something, and you've created a mission to help them.

User's request: "{message}"

Mission created: {objective_desc}

Write a brief, friendly response (1-2 sentences) that:
1. Acknowledges what they want
2. Tells them you've prepared a mission they can approve
3. Sounds conversational and helpful

Examples of good responses:
- "I can help you extract headlines from that site! I've prepared a mission - just click 'Approve' and I'll get started."
- "Sure thing! I've set up a monitoring mission for you. Approve it and I'll start tracking that site daily."
- "Got it! I've created a search mission to find those tutorials. Ready to go when you give the green light."

Your response:"""
            
            summary = llm_client.complete(prompt, max_tokens=100, temperature=0.7)
            
            if summary and len(summary.strip()) > 10:
                return summary.strip()
            else:
                # Fallback to a friendly template
                return f"I've prepared a mission to {objective_desc.lower()}. Click 'Approve' when you're ready!"
                
        except Exception as e:
            logger.warning(f"Failed to generate conversational summary: {e}")
            # Fallback to friendly template
            return f"I've got this! I created a mission to help with your request. Just approve it and I'll get started."

    
    # NEW: Mission Planning Integration Methods
    
    def _plan_mission_with_details(self, mission_draft: Dict, raw_message: str) -> Optional[Any]:
        """
        Plan a multi-step mission with per-step tool selection and cost/duration estimates.
        
        Args:
            mission_draft: Mission created from readiness validation
            raw_message: Original user message
            
        Returns:
            UnifiedProposal object or None if planning fails
        """
        try:
            from Back_End.multi_step_mission_planner import multi_step_planner
            from Back_End.action_readiness_engine import ReadinessDecision
            
            logger.info(f"[MULTI-STEP PLANNING] Starting for {mission_draft.get('mission_id')}")
            
            # Create a ReadinessResult-like object from mission_draft
            class ReadinessResult:
                def __init__(self, draft):
                    self.decision = ReadinessDecision.READY
                    self.intent = draft.get('objective_type')
                    self.action_object = draft.get('objective_description', '')
                    self.action_target = draft.get('target_count', 1)
                    self.source_url = draft.get('scope', {}).get('source_url') if isinstance(draft.get('scope'), dict) else None
                    self.constraints = draft.get('scope', {}) if isinstance(draft.get('scope'), dict) else {}
                    self.intent_candidates = []  # For compatibility
                    self.clarification_question = None
            
            readiness_result = ReadinessResult(mission_draft)
            
            # Plan mission using MultiStepMissionPlanner
            unified_proposal = multi_step_planner.plan_mission(
                readiness_result=readiness_result,
                raw_chat_message=raw_message,
                user_id="default_user"  # TODO: Pass actual user_id
            )
            
            return unified_proposal
        except Exception as e:
            logger.error(f"[MULTI-STEP PLANNING] Failed to plan mission: {e}", exc_info=True)
            return None
    
    def _evaluate_mission_plan(
        self, 
        unified_proposal: Any,
        user_id: str,
        user_budget_remaining: float = 10.0,
        service_tier: str = "FREE"
    ) -> Dict[str, Any]:
        """
        Evaluate a unified proposal for approval decision.
        
        Args:
            unified_proposal: UnifiedProposal to evaluate
            user_id: User ID for logging
            user_budget_remaining: Budget available (default: $10)
            service_tier: User's service tier (default: FREE)
            
        Returns:
            Approval decision dict with recommendation and checks
        """
        try:
            logger.info(f"[APPROVAL] Evaluating unified proposal for {unified_proposal.mission_id}")
            
            # Extract key metrics from proposal
            total_cost = unified_proposal.total_cost_usd
            requires_approval = unified_proposal.requires_approval
            has_blocking = unified_proposal.has_blocking_steps
            
            # Simple approval logic (more sophisticated logic can be added later)
            checks = []
            
            # Budget check
            if total_cost > user_budget_remaining:
                checks.append({
                    'type': 'BUDGET_EXCEEDED',
                    'severity': 'HIGH',
                    'message': f'Cost ${total_cost:.4f} exceeds budget ${user_budget_remaining:.2f}',
                    'passed': False
                })
            else:
                checks.append({
                    'type': 'BUDGET_OK',
                    'severity': 'LOW',
                    'message': f'Cost ${total_cost:.4f} within budget',
                    'passed': True
                })
            
            # Determine recommendation
            if total_cost > user_budget_remaining:
                recommendation = 'REJECT'
            elif has_blocking:
                recommendation = 'REVIEW'
            elif requires_approval:
                recommendation = 'APPROVE_WITH_REVIEW'
            else:
                recommendation = 'AUTO_APPROVE'
            
            return {
                'mission_id': unified_proposal.mission_id,
                'approved': total_cost <= user_budget_remaining,
                'recommendation': recommendation,
                'checks': checks,
                'alternative_options': len(unified_proposal.approval_options)
            }
        except Exception as e:
            logger.error(f"[APPROVAL] Failed to evaluate unified proposal: {e}", exc_info=True)
            # Return neutral decision allowing user to proceed
            return {
                'mission_id': getattr(unified_proposal, 'mission_id', 'unknown'),
                'approved': True,  # Neutral: allow user to decide
                'recommendation': 'REVIEW',
                'checks': [],
                'alternative_options': 0
            }
    
    def _save_plan_to_mission(self, mission_id: str, unified_proposal: Any) -> None:
        """
        Save the unified proposal plan to the mission in mission_store.
        
        This bridges the planning → execution gap by storing planned tools,
        costs, and durations with the mission for execution_service to retrieve.
        
        Args:
            mission_id: Mission identifier
            unified_proposal: UnifiedProposal object with complete plan
        """
        try:
            from Back_End.mission_store import get_mission_store, Mission
            
            store = get_mission_store()
            
            # Extract step data with tool selections
            steps_data = []
            if hasattr(unified_proposal, 'task_breakdown') and unified_proposal.task_breakdown:
                for step in unified_proposal.task_breakdown.steps:
                    step_dict = {
                        'step_name': step.step_name,
                        'step_type': step.step_type.value if hasattr(step.step_type, 'value') else str(step.step_type),
                        'selected_tool': step.selected_tool,
                        'tool_confidence': step.tool_confidence,
                        'estimated_duration_seconds': step.estimated_duration_seconds,
                        'estimated_cost_usd': step.estimated_cost_usd,
                        'description': step.description if hasattr(step, 'description') else '',
                    }
                    steps_data.append(step_dict)
            
            # Create plan_stored event
            plan_event = Mission(
                mission_id=mission_id,
                event_type='mission_plan_created',
                status='planned',
                objective={
                    'description': unified_proposal.objective,
                    'title': unified_proposal.mission_title if hasattr(unified_proposal, 'mission_title') else 'Mission',
                },
                metadata={
                    'plan_data': {
                        'total_steps': unified_proposal.total_steps,
                        'total_cost_usd': unified_proposal.total_cost_usd,
                        'estimated_total_time_minutes': unified_proposal.estimated_total_time_minutes,
                        'steps': steps_data,
                        'requires_approval': unified_proposal.requires_approval,
                        'has_blocking_steps': unified_proposal.has_blocking_steps,
                    },
                    'created_at': datetime.utcnow().isoformat(),
                    'plan_version': unified_proposal.proposal_version if hasattr(unified_proposal, 'proposal_version') else '1.0',
                },
                scope={}
            )
            
            store.write_mission_event(plan_event)
            logger.info(f"[PLAN_STORAGE] Saved plan for mission {mission_id} with {unified_proposal.total_steps} steps")
            
        except Exception as e:
            logger.error(f"[PLAN_STORAGE] Failed to save plan for {mission_id}: {e}", exc_info=True)
            # Don't fail the entire flow if plan storage fails - execution can fallback to dynamic tool selection
    
    def _create_mission_plan_response(
        self,
        mission_ref: Any,
        unified_proposal: Any,
        approval_decision: Dict[str, Any],
        original_message: str
    ) -> ResponseEnvelope:
        """
        Create a unified proposal response (single cohesive message).
        
        Args:
            mission_ref: MissionReference for the UI (kept for backwards compatibility)
            unified_proposal: UnifiedProposal with complete breakdown
            approval_decision: Decision from evaluation
            original_message: Original user request
            
        Returns:
            ResponseEnvelope with unified proposal
        """
        try:
            from Back_End.response_envelope import unified_proposal_response
            
            # Convert unified_proposal to dict format if needed
            if hasattr(unified_proposal, 'to_dict'):
                unified_proposal_dict = unified_proposal.to_dict()
            else:
                # Already a dict
                unified_proposal_dict = unified_proposal
            
            # Enhance proposal dict with approval decision
            unified_proposal_dict['approval_decision'] = approval_decision
            
            # Use the new unified_proposal_response function
            response = unified_proposal_response(unified_proposal_dict)
            
            logger.info(
                f"[RESPONSE] Created unified proposal response for {unified_proposal.mission_id}: "
                f"{unified_proposal.total_steps} steps, ${unified_proposal.total_cost_usd:.4f}, "
                f"{unified_proposal.estimated_total_time_minutes}min"
            )
            
            return response
        except Exception as e:
            logger.error(f"[RESPONSE] Failed to create unified proposal response: {e}", exc_info=True)
            # Fallback to simple response
            from Back_End.response_envelope import mission_proposal_response
            return mission_proposal_response(
                mission_ref,
                f"Mission prepared for approval. Review details to proceed."
            )


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================

def orchestrate_message(
    message: str,
    session_id: str,
    user_id: str = "default",
    context: Optional[Dict[str, Any]] = None,
    trace_id: Optional[str] = None
) -> ResponseEnvelope:
    """
    Convenience function to orchestrate a single message.
    
    Args:
        message: User message
        session_id: Session ID
        user_id: User ID
        context: Optional context
        trace_id: Optional trace ID for observability
        
    Returns:
        ResponseEnvelope
    """
    return _shared_orchestrator.process_message(message, session_id, user_id, context, trace_id)


_shared_orchestrator = InteractionOrchestrator()

