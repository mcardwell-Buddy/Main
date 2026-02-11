"""Intent classification for message understanding.

Classifies incoming messages into intent categories without triggering actions.
Uses deterministic pattern matching only - no ML, no learning.

Intent types:
- conversation: Default - general chat, questions, social
- status_request: Asking for current state, availability, information
- reflection: Messages about thinking, opinions, values
- exploration: Questions about possibilities, ideas, alternatives
- potential_action: Messages that WOULD require approval if executed (FLAG ONLY)
"""

import re
from typing import Literal

IntentType = Literal["conversation", "status_request", "reflection", "exploration", "potential_action"]


class IntentClassifier:
    """Simple, deterministic intent classifier using keyword and pattern matching."""

    def __init__(self):
        """Initialize classifier patterns."""
        # Status request patterns
        self.status_patterns = [
            r"\b(are\s+you\s+(online|available|ready|working))\b",
            r"\b(what\s+(are\s+)?you\s+(doing|working\s+on))\b",
            r"\b(how\s+(are\s+)?you)\b",
            r"\b(status|check-in)\b",
            r"\b(can\s+you\s+(help|assist))\b",
        ]

        # Reflection patterns
        self.reflection_patterns = [
            r"\b(i\s+(think|believe|feel|wonder|realize))\b",
            r"\b(what\s+do\s+you\s+(think|believe|feel))\b",
            r"\b(in\s+my\s+(opinion|view))\b",
            r"\b(should\s+[a-z]+)\b",  # Opinions about what should be
            r"\b(meaning|purpose|why)\b",
        ]

        # Exploration patterns
        self.exploration_patterns = [
            r"\b(what\s+if|suppose|imagine|consider)\b",
            r"\b(how\s+(would|could|might))\b",
            r"\b(possibilities|alternatives|options)\b",
            r"\b(ideas|suggestions|recommendations)\b",
            r"\b(explore|investigate|research)\b",
        ]

        # Potential action patterns (FLAGGED but NOT executed)
        self.potential_action_patterns = [
            r"\b(send|email|message|notify)\s+(me|them|[a-z]+@[a-z.]+)\b",
            r"\b(search|find|lookup|research)\b",
            r"\b(create|make|write|generate|build)\b",
            r"\b(schedule|book|arrange|plan)\b",
            r"\b(update|change|modify|edit)\b",
            r"\b(delete|remove|cancel)\b",
            r"\b(check\s+(my|the))\b",
            r"\b(please\s+(do|send|find|search))\b",
                r"\b(can\s+you\s+(send|email|search|find|create|make|write|modify|delete|update))\b",
                r"\b((send|email|search|find|create|make|write|modify|delete|update)\s+(an?\s+)?(\w+\s+)*(email|message|note|draft|file|page|item))\b",
            ]

    def classify(self, message: str) -> IntentType:
        """Classify message intent deterministically.

        Args:
            message: Incoming message text

        Returns:
            Intent type classification
        """
        if not message:
            return "conversation"

        # Normalize for matching
        text_lower = message.lower().strip()

        # Check patterns in order of specificity (most specific first)
        # Potential actions are checked first because they're most actionable
        if self._matches_patterns(text_lower, self.potential_action_patterns):
            return "potential_action"

        # Status requests are high priority
        if self._matches_patterns(text_lower, self.status_patterns):
            return "status_request"

        # Reflection
        if self._matches_patterns(text_lower, self.reflection_patterns):
            return "reflection"

        # Exploration
        if self._matches_patterns(text_lower, self.exploration_patterns):
            return "exploration"

        # Default to conversation
        return "conversation"

    def get_response_hint(self, intent: IntentType) -> str:
        """Get guidance for response based on intent.

        Args:
            intent: Classified intent type

        Returns:
            Guidance string for response generation
        """
        hints = {
            "conversation": "Respond naturally and conversationally. Be helpful and friendly.",
            "status_request": "Provide brief status information. Keep it factual.",
            "reflection": "Acknowledge their perspective. Be thoughtful and considerate.",
            "exploration": "Discuss possibilities and ideas. Be creative but don't commit to actions.",
            "potential_action": "Acknowledge the request. Note that approval will be required to execute actions.",
        }
        return hints.get(intent, hints["conversation"])

    @staticmethod
    def _matches_patterns(text: str, patterns: list[str]) -> bool:
        """Check if text matches any pattern.

        Args:
            text: Normalized text to check
            patterns: List of regex patterns

        Returns:
            True if any pattern matches
        """
        for pattern in patterns:
            try:
                if re.search(pattern, text, re.IGNORECASE):
                    return True
            except re.error:
                # Skip invalid patterns
                continue
        return False

