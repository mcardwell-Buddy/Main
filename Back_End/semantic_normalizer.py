"""
Phase 5: Semantic Normalization Layer

PURPOSE:
Rewrite user input into canonical, intent-equivalent form to reduce phrasing brittleness.

CONSTRAINTS:
- MUST NOT create missions
- MUST NOT execute tools
- MUST NOT modify session context
- MUST NOT guess missing fields (URLs, objects, constraints)
- MUST NOT bypass ActionReadinessEngine, clarifications, or approval
- MUST NOT call tool selector
- MUST NOT replace existing logic

ONLY allowed to return rewritten text.
"""

from dataclasses import dataclass
from typing import Optional
import json
import logging

logger = logging.getLogger(__name__)

# Confidence threshold for accepting normalized text
NORMALIZATION_CONFIDENCE_THRESHOLD = 0.6


@dataclass
class NormalizationResult:
    """Result of semantic normalization attempt."""
    original_text: str
    normalized_text: str
    confidence: float  # 0.0 – 1.0
    reason: str


def maybe_normalize(text: str, session_context: Optional[dict] = None) -> str:
    """
    Attempt to normalize user input into canonical form.
    
    Returns normalized_text ONLY if confidence >= THRESHOLD.
    Otherwise returns original text unchanged.
    
    Args:
        text: Raw user input
        session_context: Optional context for reference resolution (last_url, etc.)
        
    Returns:
        str: Normalized text if high confidence, otherwise original text
        
    Side effects: None (except logging)
    """
    if not text or not text.strip():
        return text
    
    try:
        result = _attempt_normalization(text, session_context)
        
        if result.confidence >= NORMALIZATION_CONFIDENCE_THRESHOLD:
            logger.info(
                f"Normalization accepted (conf={result.confidence:.2f}): "
                f"'{result.original_text}' → '{result.normalized_text}'"
            )
            return result.normalized_text
        else:
            logger.info(
                f"Normalization rejected (conf={result.confidence:.2f}): "
                f"using original text. Reason: {result.reason}"
            )
            return result.original_text
            
    except Exception as e:
        logger.warning(f"Normalization failed: {e}. Using original text.")
        return text


def _attempt_normalization(text: str, session_context: Optional[dict]) -> NormalizationResult:
    """
    Call LLM to attempt semantic normalization.
    
    Returns NormalizationResult with confidence score.
    """
    from Back_End.llm_client import llm_client
    
    # Build context hints (but never guess missing values)
    context_hints = ""
    if session_context:
        last_url = session_context.get("last_visited_url")
        last_artifact = session_context.get("last_artifact_id")
        
        if last_url:
            context_hints += "\n- last_visited_url: " + str(last_url)
        if last_artifact:
            context_hints += "\n- last_artifact_id: " + str(last_artifact)
    
    if not context_hints:
        context_hints = "\n- (no context available)"
    
    prompt = """You are a semantic rewrite engine, not an agent.

Your ONLY job is to rewrite natural language into canonical command form that preserves intent but reduces wording variability.

STRICT RULES:
1. Rewrite only when meaning is clear
2. Do NOT add new intent
3. Do NOT invent missing information
4. Do NOT guess URLs, objects, or constraints
5. Do NOT execute actions
6. If unclear or ambiguous, return original text unchanged with LOW confidence

Context (for reference resolution ONLY, do NOT invent values):""" + context_hints + """

CANONICAL PATTERNS (examples):
- Arithmetic: "What is 1+2?" → "calculate 1 + 2"
- Navigation: "Go to example.com" → "navigate to example.com"
- Navigation: "Open that site" → "navigate to example.com" (if last_visited_url is example.com)
- Extract: "What's the page title?" → "extract title from last_visited_url"
- Extract: "Grab the title" → "extract title from last_visited_url"
- Repetition: "Do it again" → "repeat last_mission"
- Ambiguous: "Tell me more" → (unchanged, low confidence)

User input: \"""" + text + """\"

Return ONLY valid JSON (no markdown, no explanation):
{
  "normalized_text": "...",
  "confidence": 0.0,
  "reason": "brief explanation"
}

Confidence scale:
- 0.9-1.0: Exact canonical match
- 0.7-0.9: Clear intent, minor rewording
- 0.5-0.7: Moderate rewording, some ambiguity
- 0.0-0.5: Ambiguous or unclear, use original
"""

    try:
        response = llm_client.complete(prompt, max_tokens=200, temperature=0.1)
        
        if not response:
            logger.warning("LLM returned no response for normalization")
            return NormalizationResult(
                original_text=text,
                normalized_text=text,
                confidence=0.0,
                reason="LLM unavailable"
            )
        
        # Parse JSON response
        response_text = response.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1]) if len(lines) > 2 else response_text
        
        data = json.loads(response_text)
        
        normalized_text = data.get("normalized_text", text)
        confidence = float(data.get("confidence", 0.0))
        reason = data.get("reason", "No reason provided")
        
        # Clamp confidence to [0.0, 1.0]
        confidence = max(0.0, min(1.0, confidence))
        
        return NormalizationResult(
            original_text=text,
            normalized_text=normalized_text,
            confidence=confidence,
            reason=reason
        )
        
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse LLM response as JSON: {e}")
        return NormalizationResult(
            original_text=text,
            normalized_text=text,
            confidence=0.0,
            reason=f"JSON parse error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Normalization LLM call failed: {e}")
        return NormalizationResult(
            original_text=text,
            normalized_text=text,
            confidence=0.0,
            reason=f"LLM call failed: {str(e)}"
        )


def get_normalization_stats(session_context: Optional[dict] = None) -> dict:
    """
    Return statistics about normalization (for monitoring/debugging).
    
    This is a placeholder for future telemetry integration.
    """
    return {
        "threshold": NORMALIZATION_CONFIDENCE_THRESHOLD,
        "available_context": bool(session_context),
        "context_keys": list(session_context.keys()) if session_context else []
    }

