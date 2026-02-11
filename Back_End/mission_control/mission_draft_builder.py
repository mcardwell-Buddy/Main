"""
Mission Draft Builder

Converts actionable chat intents into structured mission drafts.

HARD CONSTRAINTS:
- NO execution
- NO automatic approval
- Safe defaults only
- All missions start as "proposed"
- Source always = "chat"
"""

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
import uuid
import re


@dataclass
class MissionDraft:
    """
    Proposed mission awaiting approval.
    
    Status is ALWAYS "proposed" - never "active".
    """
    mission_id: str
    source: str  # Always "chat"
    status: str  # Always "proposed"
    
    # Mission details
    objective_description: str
    objective_type: str  # search | extract | navigate
    target_count: Optional[int]
    
    # Scope constraints (safe defaults)
    allowed_domains: List[str]
    max_pages: int
    max_duration_seconds: int
    
    # Metadata
    created_at: str
    raw_chat_message: str
    intent_keywords: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)


class MissionDraftBuilder:
    """
    Builds mission drafts from actionable chat intents.
    
    Uses deterministic heuristics to extract:
    - Objective type
    - Target data
    - Safe scope constraints
    
    NO LLM calls. NO execution. NO autonomy.
    """
    
    # Safe default constraints
    DEFAULT_MAX_PAGES = 5
    DEFAULT_MAX_DURATION = 300  # 5 minutes
    DEFAULT_TARGET_COUNT = 50
    
    # Domain extraction patterns
    DOMAIN_PATTERN = r'(?:from\s+)?(?:https?://)?(?:www\.)?([a-z0-9.-]+\.[a-z]{2,})(?:/\S*)?'
    
    # Objective type keywords
    SEARCH_KEYWORDS = ['search', 'find', 'look for', 'discover']
    EXTRACT_KEYWORDS = ['get', 'extract', 'collect', 'scrape', 'download', 'fetch', 'pull', 'grab', 'retrieve']
    NAVIGATE_KEYWORDS = ['navigate', 'go to', 'visit', 'open', 'browse']
    
    def __init__(self):
        pass
    
    def build_draft(
        self,
        raw_message: str,
        intent_type: str,
        intent_keywords: List[str]
    ) -> MissionDraft:
        """
        Build a mission draft from chat intent.
        
        Args:
            raw_message: Original chat message
            intent_type: Intent classification (action_request or exploratory_request)
            intent_keywords: Keywords that triggered the intent
            
        Returns:
            MissionDraft with safe defaults
        """
        mission_id = self._generate_mission_id()
        
        # Extract objective details
        objective_type = self._determine_objective_type(raw_message, intent_keywords)
        objective_description = self._clean_objective_description(raw_message)
        target_count = self._extract_target_count(raw_message)
        
        # Extract domain constraints
        allowed_domains = self._extract_domains(raw_message)
        
        # Apply safe defaults
        max_pages = self._determine_max_pages(raw_message)
        max_duration = self.DEFAULT_MAX_DURATION
        
        return MissionDraft(
            mission_id=mission_id,
            source='chat',
            status='proposed',
            objective_description=objective_description,
            objective_type=objective_type,
            target_count=target_count,
            allowed_domains=allowed_domains,
            max_pages=max_pages,
            max_duration_seconds=max_duration,
            created_at=datetime.now(timezone.utc).isoformat(),
            raw_chat_message=raw_message,
            intent_keywords=intent_keywords
        )
    
    def _generate_mission_id(self) -> str:
        """Generate unique mission ID."""
        return f"mission_chat_{uuid.uuid4().hex[:12]}"
    
    def _determine_objective_type(self, message: str, keywords: List[str]) -> str:
        """
        Determine mission objective type from message.
        
        Returns: 'search' | 'extract' | 'navigate'
        """
        message_lower = message.lower()
        
        # Check for extract patterns (most specific)
        for keyword in self.EXTRACT_KEYWORDS:
            if keyword in keywords or keyword in message_lower:
                return 'extract'
        
        # Check for search patterns
        for keyword in self.SEARCH_KEYWORDS:
            if keyword in keywords or keyword in message_lower:
                return 'search'
        
        # Check for navigate patterns
        for keyword in self.NAVIGATE_KEYWORDS:
            if keyword in keywords or keyword in message_lower:
                return 'navigate'
        
        # Default to search
        return 'search'
    
    def _clean_objective_description(self, message: str) -> str:
        """
        Clean and format objective description.
        
        Removes URLs, normalizes whitespace.
        """
        # Remove URLs
        cleaned = re.sub(r'https?://\S+', '', message)
        
        # Normalize whitespace
        cleaned = ' '.join(cleaned.split())
        
        # Limit length
        if len(cleaned) > 200:
            cleaned = cleaned[:197] + '...'
        
        return cleaned.strip()
    
    def _extract_target_count(self, message: str) -> Optional[int]:
        """
        Extract target count from message.
        
        Examples:
        - "get 100 contacts" -> 100
        - "find all quotes" -> None (use default)
        - "extract 25 leads" -> 25
        """
        # Look for number + items pattern
        count_pattern = r'\b(\d+)\s+(?:items|contacts|leads|results|quotes|records|entries|pages)\b'
        match = re.search(count_pattern, message.lower())
        
        if match:
            count = int(match.group(1))
            # Cap at reasonable maximum
            return min(count, 1000)
        
        # Look for "all" keyword - return None for default
        if 'all' in message.lower():
            return None
        
        # Return default
        return self.DEFAULT_TARGET_COUNT
    
    def _extract_domains(self, message: str) -> List[str]:
        """
        Extract domain constraints from message.
        
        Examples:
        - "scrape quotes.toscrape.com" -> ["quotes.toscrape.com"]
        - "get leads from yellowpages.com" -> ["yellowpages.com"]
        - "find contacts" -> [] (no domain specified)
        """
        domains = []
        
        matches = re.findall(self.DOMAIN_PATTERN, message.lower())
        
        for domain in matches:
            # Clean and validate
            domain = domain.strip()
            if domain and '.' in domain:
                domains.append(domain)
        
        return list(set(domains))  # Remove duplicates
    
    def _determine_max_pages(self, message: str) -> int:
        """
        Determine max pages from message.
        
        Uses safe defaults.
        """
        # Look for page limit in message
        page_pattern = r'\b(?:first|max|maximum|up to)\s+(\d+)\s+pages?\b'
        match = re.search(page_pattern, message.lower())
        
        if match:
            pages = int(match.group(1))
            # Cap at reasonable maximum
            return min(pages, 20)
        
        # Return safe default
        return self.DEFAULT_MAX_PAGES


# Convenience function
def build_mission_draft(raw_message: str, intent_type: str, intent_keywords: List[str]) -> MissionDraft:
    """Build a mission draft from chat intent."""
    builder = MissionDraftBuilder()
    return builder.build_draft(raw_message, intent_type, intent_keywords)

