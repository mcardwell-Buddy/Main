"""
Chat Intent Router

Deterministic intent classification for chat messages.
Uses keyword + structure heuristics only (NO LLM calls).

Maps chat messages to one of:
- informational_question: User asking for information
- exploratory_request: User wants to research/explore
- action_request: User wants data collected/extracted
- non_actionable: Can't be converted to mission
"""

from dataclasses import dataclass
from typing import List, Optional
import re


@dataclass
class ChatIntent:
    """Classified intent from chat message."""
    intent_type: str  # informational_question | exploratory_request | action_request | non_actionable
    confidence: float
    keywords_matched: List[str]
    raw_message: str
    actionable: bool
    
    def to_dict(self):
        return {
            'intent_type': self.intent_type,
            'confidence': self.confidence,
            'keywords_matched': self.keywords_matched,
            'raw_message': self.raw_message,
            'actionable': self.actionable,
        }


class ChatIntentRouter:
    """
    Deterministic chat intent router using keyword/pattern matching.
    
    NO LLM calls. NO autonomy. Pure heuristics.
    """
    
    # Intent classification patterns
    QUESTION_KEYWORDS = [
        'what', 'when', 'where', 'why', 'how', 'who',
        'is', 'are', 'can', 'could', 'would', 'should',
        'tell me', 'explain', 'show me', '?'
    ]
    
    EXPLORATORY_KEYWORDS = [
        'find', 'search', 'look for', 'discover', 'explore',
        'research', 'investigate', 'check', 'see if',
        'browse', 'scan', 'review'
    ]
    
    ACTION_KEYWORDS = [
        'get', 'extract', 'collect', 'scrape', 'download',
        'fetch', 'pull', 'grab', 'retrieve', 'gather',
        'list all', 'get all', 'extract all'
    ]
    
    NON_ACTIONABLE_PATTERNS = [
        r'^(hi|hey|hello|thanks|thank you|ok|okay)',
        r'^(yes|no|maybe|sure|nope)',
    ]
    
    def __init__(self):
        pass
    
    def route(self, message: str) -> ChatIntent:
        """
        Route a chat message to an intent type.
        
        Args:
            message: Raw chat message text
            
        Returns:
            ChatIntent with classification
        """
        if not message or not message.strip():
            return ChatIntent(
                intent_type='non_actionable',
                confidence=1.0,
                keywords_matched=[],
                raw_message=message,
                actionable=False
            )
        
        message_lower = message.lower().strip()
        
        # Check non-actionable patterns first
        for pattern in self.NON_ACTIONABLE_PATTERNS:
            if re.match(pattern, message_lower):
                return ChatIntent(
                    intent_type='non_actionable',
                    confidence=0.9,
                    keywords_matched=['greeting_or_acknowledgment'],
                    raw_message=message,
                    actionable=False
                )
        
        # Count keyword matches for each intent type
        question_matches = self._count_matches(message_lower, self.QUESTION_KEYWORDS)
        exploratory_matches = self._count_matches(message_lower, self.EXPLORATORY_KEYWORDS)
        action_matches = self._count_matches(message_lower, self.ACTION_KEYWORDS)
        
        # Determine primary intent
        max_matches = max(question_matches['count'], exploratory_matches['count'], action_matches['count'])
        
        if max_matches == 0:
            # No clear intent keywords
            return ChatIntent(
                intent_type='non_actionable',
                confidence=0.5,
                keywords_matched=[],
                raw_message=message,
                actionable=False
            )
        
        # Action requests take priority if present
        if action_matches['count'] > 0 and action_matches['count'] >= exploratory_matches['count']:
            return ChatIntent(
                intent_type='action_request',
                confidence=self._calculate_confidence(action_matches['count'], len(message_lower.split())),
                keywords_matched=action_matches['keywords'],
                raw_message=message,
                actionable=True
            )
        
        # Exploratory requests
        if exploratory_matches['count'] > 0:
            return ChatIntent(
                intent_type='exploratory_request',
                confidence=self._calculate_confidence(exploratory_matches['count'], len(message_lower.split())),
                keywords_matched=exploratory_matches['keywords'],
                raw_message=message,
                actionable=True
            )
        
        # Questions (informational)
        if question_matches['count'] > 0:
            return ChatIntent(
                intent_type='informational_question',
                confidence=self._calculate_confidence(question_matches['count'], len(message_lower.split())),
                keywords_matched=question_matches['keywords'],
                raw_message=message,
                actionable=False
            )
        
        # Fallback
        return ChatIntent(
            intent_type='non_actionable',
            confidence=0.3,
            keywords_matched=[],
            raw_message=message,
            actionable=False
        )
    
    def _count_matches(self, text: str, keywords: List[str]) -> dict:
        """Count keyword matches in text."""
        matched = []
        for keyword in keywords:
            if keyword in text:
                matched.append(keyword)
        return {
            'count': len(matched),
            'keywords': matched
        }
    
    def _calculate_confidence(self, match_count: int, word_count: int) -> float:
        """
        Calculate confidence based on keyword density.
        
        More keywords + shorter message = higher confidence
        """
        if word_count == 0:
            return 0.0
        
        density = match_count / word_count
        
        # Scale to 0.5-0.95 range
        confidence = 0.5 + (min(density, 0.5) * 0.9)
        
        return round(confidence, 2)


# Convenience function
def classify_chat_message(message: str) -> ChatIntent:
    """Classify a chat message into an intent."""
    router = ChatIntentRouter()
    return router.route(message)
