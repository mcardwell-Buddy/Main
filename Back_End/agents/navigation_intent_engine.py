"""
Phase 2 Step 1: Navigation Intent Engine

Pure heuristic-based intent reasoning layer that scores navigation candidates
based on relevance to a goal. Does NOT make decisions or trigger actions.

NO LLM calls. NO hard-coded site paths. Deterministic output only.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import re
import logging

logger = logging.getLogger(__name__)


# === SCORING WEIGHTS (HEURISTIC CONSTANTS) ===

SCORE_WEIGHTS = {
    # Positive signals
    "text_directory_keyword": 3,      # "directory", "list", "browse" in text
    "url_directory_pattern": 3,       # /directory, /list, /companies in URL
    "text_navigation_keyword": 2,     # "next", "more", "view all"
    "aria_results_pattern": 2,        # aria-label contains "results", "page"
    "repeated_structure": 2,          # Link is part of repeated pattern
    "page_context_match": 1,          # Contextual relevance
    
    # Negative signals
    "external_link": -3,              # Link goes to different domain
    "footer_nav_link": -2,            # Footer or utility navigation
    "login_signup_link": -2,          # Login, signup, account links
    "social_media_link": -2,          # Social media links
}

# Keyword patterns
DIRECTORY_KEYWORDS = ["directory", "list", "browse", "catalog", "companies", "vendors", 
                     "businesses", "listings", "search", "find", "explore"]
NAVIGATION_KEYWORDS = ["next", "more", "view all", "see all", "show more", "load more",
                      "continue", "page"]
URL_DIRECTORY_PATTERNS = [r"/directory", r"/list", r"/companies", r"/vendors", r"/catalog",
                         r"/browse", r"/businesses", r"/search", r"/results"]
EXCLUDED_KEYWORDS = ["login", "sign", "account", "cart", "checkout", "privacy", "terms",
                    "contact", "about", "facebook", "twitter", "instagram", "linkedin"]


class NavigationIntentEngine:
    """
    Scores navigation candidates based on goal relevance using heuristic rules.
    
    This is a pure reasoning layer - it does NOT:
    - Make navigation decisions
    - Click elements
    - Modify page state
    - Use LLMs
    
    It only provides ranked suggestions.
    """
    
    def __init__(
        self,
        goal_description: str,
        page_context: Dict[str, Any],
        current_url: str
    ):
        """
        Initialize intent engine with goal and page context.
        
        Args:
            goal_description: Natural language goal (e.g., "Find small business listings")
            page_context: Inspection data from BuddysVisionCore
            current_url: Current page URL
        """
        self.goal_description = goal_description.lower()
        self.page_context = page_context
        self.current_url = current_url
        self.current_domain = self._extract_domain(current_url)
        
        # Extract goal keywords for matching
        self.goal_keywords = self._extract_goal_keywords(goal_description)
        
        logger.debug(f"Intent engine initialized: goal='{goal_description}', domain={self.current_domain}")
    
    def rank_navigation_candidates(self) -> List[Dict[str, Any]]:
        """
        Score and rank all navigation candidates on current page.
        
        Returns:
            List of ranked candidates with scores and signals, sorted descending by score
        """
        candidates = []
        
        # Extract links from page context
        links = self.page_context.get("links", [])
        
        if not links:
            logger.debug("No links found in page context")
            return []
        
        # Score each link
        for link in links:
            candidate = self._score_link(link)
            if candidate:
                candidates.append(candidate)
        
        # Sort by score descending
        candidates.sort(key=lambda x: x["score"], reverse=True)
        
        logger.info(f"Ranked {len(candidates)} navigation candidates")
        return candidates
    
    def _score_link(self, link: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Score a single link based on goal relevance.
        
        Args:
            link: Link data from page inspection
            
        Returns:
            Scored candidate dict or None if link should be excluded
        """
        text = (link.get("text") or "").lower().strip()
        href = (link.get("href") or "").lower().strip()
        aria_label = (link.get("aria_label") or "").lower().strip()
        link_class = (link.get("class") or "").lower()
        
        # Skip empty or invalid links
        if not text and not aria_label:
            return None
        if not href or href in ["#", "javascript:void(0)", "javascript:"]:
            return None
        
        score = 0
        signals = []
        
        # === POSITIVE SIGNALS ===
        
        # Check for directory keywords in text
        if any(keyword in text for keyword in DIRECTORY_KEYWORDS):
            score += SCORE_WEIGHTS["text_directory_keyword"]
            signals.append("text_directory_keyword")
        
        # Check for directory patterns in URL
        if any(re.search(pattern, href) for pattern in URL_DIRECTORY_PATTERNS):
            score += SCORE_WEIGHTS["url_directory_pattern"]
            signals.append("url_directory_pattern")
        
        # Check for navigation keywords in text
        if any(keyword in text for keyword in NAVIGATION_KEYWORDS):
            score += SCORE_WEIGHTS["text_navigation_keyword"]
            signals.append("text_navigation_keyword")
        
        # Check aria-label for results patterns
        if aria_label and any(word in aria_label for word in ["result", "page", "navigation"]):
            score += SCORE_WEIGHTS["aria_results_pattern"]
            signals.append("aria_results_pattern")
        
        # Check for goal keyword matches
        goal_matches = sum(1 for keyword in self.goal_keywords if keyword in text or keyword in href)
        if goal_matches > 0:
            score += goal_matches * SCORE_WEIGHTS["page_context_match"]
            signals.append(f"goal_keyword_match:{goal_matches}")
        
        # === NEGATIVE SIGNALS ===
        
        # Check if external link
        link_domain = self._extract_domain(href)
        if link_domain and link_domain != self.current_domain:
            score += SCORE_WEIGHTS["external_link"]
            signals.append("external_link")
        
        # Check for footer/utility nav
        if any(cls in link_class for cls in ["footer", "nav-utility", "sidebar", "menu"]):
            score += SCORE_WEIGHTS["footer_nav_link"]
            signals.append("footer_nav_link")
        
        # Check for excluded keywords
        if any(keyword in text or keyword in href for keyword in EXCLUDED_KEYWORDS):
            score += SCORE_WEIGHTS["login_signup_link"]
            signals.append("excluded_keyword")
        
        # Build candidate
        candidate = {
            "element_type": "link",
            "text": link.get("text", "").strip(),
            "href": href,
            "aria_label": link.get("aria_label"),
            "score": score,
            "signals": signals,
            "goal_relevance": self._calculate_relevance(text, href, aria_label)
        }
        
        return candidate
    
    def _calculate_relevance(self, text: str, href: str, aria_label: str) -> float:
        """Calculate normalized relevance score (0.0 to 1.0)."""
        # Count goal keyword matches
        matches = 0
        total_keywords = len(self.goal_keywords)
        
        if total_keywords == 0:
            return 0.0
        
        for keyword in self.goal_keywords:
            if keyword in text or keyword in href or keyword in aria_label:
                matches += 1
        
        return min(matches / total_keywords, 1.0)
    
    def _extract_goal_keywords(self, goal: str) -> List[str]:
        """Extract meaningful keywords from goal description."""
        # Remove common stop words
        stop_words = {"a", "an", "the", "for", "to", "in", "on", "at", "from", "with", 
                     "find", "get", "show", "list"}
        
        words = re.findall(r'\b\w+\b', goal.lower())
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        
        return keywords
    
    def _extract_domain(self, url: str) -> Optional[str]:
        """Extract domain from URL."""
        if not url:
            return None
        
        # Handle relative URLs
        if url.startswith("/"):
            return self.current_domain
        
        # Extract domain from absolute URL
        match = re.search(r'(?:https?://)?(?:www\.)?([^/]+)', url)
        if match:
            return match.group(1)
        
        return None
    
    def get_top_candidates(self, n: int = 5) -> List[Dict[str, Any]]:
        """
        Get top N navigation candidates.
        
        Args:
            n: Number of top candidates to return
            
        Returns:
            Top N candidates sorted by score
        """
        all_candidates = self.rank_navigation_candidates()
        return all_candidates[:n]
    
    def select_action(self, confidence_threshold: float = 0.25) -> Optional[Dict[str, Any]]:
        """
        Select a navigation action based on intent ranking with safety gating.
        
        Phase 2 Step 2: Conditional action selection with strict safety rules.
        
        Safety Gates:
        - No intent candidates → return None
        - Top confidence < threshold → return None
        - Top candidate not clickable → return None
        - Top candidate href equals current URL → return None
        
        Args:
            confidence_threshold: Minimum confidence required (default 0.25)
            
        Returns:
            Action dict with element info or None if gated
        """
        # Gate 1: Check if candidates exist
        candidates = self.rank_navigation_candidates()
        if not candidates:
            logger.debug("Intent action blocked: no candidates")
            return None
        
        top_candidate = candidates[0]
        
        # Calculate confidence
        score = top_candidate.get("score", 0)
        confidence = min(max(score / 10.0, 0.0), 1.0)
        
        # Gate 2: Check confidence threshold
        if confidence < confidence_threshold:
            logger.debug(f"Intent action blocked: confidence {confidence:.2f} < {confidence_threshold}")
            return None
        
        # Gate 3: Check if element is clickable (has href)
        href = top_candidate.get("href", "").strip()
        if not href or href in ["#", "javascript:void(0)", "javascript:"]:
            logger.debug("Intent action blocked: element not clickable")
            return None
        
        # Gate 4: Check if href equals current URL (avoid self-navigation)
        if href == self.current_url or href == self.current_url.split("?")[0]:
            logger.debug("Intent action blocked: href equals current URL")
            return None
        
        # All gates passed - return action
        action = {
            "element_type": "link",
            "text": top_candidate.get("text"),
            "href": href,
            "score": score,
            "confidence": confidence,
            "signals": top_candidate.get("signals", [])
        }
        
        logger.info(f"Intent action selected: '{action['text']}' (confidence={confidence:.2f})")
        return action
    
    def emit_intent_signal(self, top_candidate: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create intent signal for logging.
        
        Args:
            top_candidate: The highest-scored candidate
            
        Returns:
            Signal dict ready for logging
        """
        signal = {
            "signal_type": "navigation_intent_ranked",
            "signal_layer": "intent",
            "signal_source": "navigation_intent_engine",
            "goal": self.goal_description,
            "top_candidate": None,
            "confidence": 0.0,
            "total_candidates": len(self.page_context.get("links", [])),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        if top_candidate:
            signal["top_candidate"] = {
                "text": top_candidate.get("text"),
                "href": top_candidate.get("href"),
                "score": top_candidate.get("score"),
                "signals": top_candidate.get("signals", [])
            }
            
            # Calculate confidence based on score (normalize to 0.0-1.0)
            # Positive scores give higher confidence
            score = top_candidate.get("score", 0)
            signal["confidence"] = min(max(score / 10.0, 0.0), 1.0)
        
        return signal

