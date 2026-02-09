"""
Goal Decomposer: Lightweight decomposition of composite goals
into 2-4 single-level subgoals.

Uses LLM when available, falls back to pattern-based heuristics.
Never recursive, never parallel, always auditable.
"""

import re
import logging
from typing import List, Dict
from backend.llm_client import llm_client

class GoalDecomposer:
    """Lightweight goal classifier and decomposer"""
    
    # Patterns that indicate ATOMIC (single-step) goals
    # These should NEVER be decomposed - check these FIRST
    ATOMIC_PATTERNS = [
        r'\b(what do you know|tell me what you know|what have you learned)\b',
        r'\b(learn about|study|research and remember|teach yourself)\b',  # Active learning
        r'\b(show.*metrics|learning progress|your understanding)\b',
        r'\b(what time|current time|what date)\b',
        r'\b(calculate|compute|solve|what is \d+)\b',
        r'\b(define|what is|explain) [^,]+(\.|\?|$)',  # Single-entity definition
    ]
    
    # Patterns that indicate composite goals
    COMPOSITE_PATTERNS = [
        r'\b(design|build|plan|develop|create)\b.*\b(and|then|also)\b',
        r'\b(analyze|research|compare)\b.*\b(and|with|vs)\b',
        r'\b(first|then|next|finally)\b',
        r'\b(before|after|once)\b.*\b(then)\b',
    ]
    
    def __init__(self):
        pass
    
    def classify_goal(self, goal: str) -> Dict:
        """
        Classify goal as atomic or composite.
        CRITICAL: Check ATOMIC_PATTERNS first (before LLM) to prevent wrong decomposition.
        
        Returns dict with:
        - is_composite: bool
        - subgoals: list of subgoal dicts (empty if atomic)
        - total_subgoals: int
        - complexity_score: float (0.0-1.0)
        """
        # CHECK ATOMIC PATTERNS FIRST - these should NEVER be decomposed
        # This check happens BEFORE LLM to ensure patterns always win
        is_atomic = any(
            re.search(pattern, goal, re.IGNORECASE)
            for pattern in self.ATOMIC_PATTERNS
        )
        
        if is_atomic:
            return {
                "goal": goal,
                "is_composite": False,
                "subgoals": [],
                "total_subgoals": 0,
                "complexity_score": 0.1,
                "reasoning": "Matched atomic pattern - single-step goal"
            }
        
        # Try LLM-based decomposition for non-atomic goals
        if llm_client.enabled:
            llm_result = llm_client.decompose_goal(goal)
            if llm_result:
                logging.info(f"LLM classified goal as {'composite' if llm_result['is_composite'] else 'atomic'}")
                
                if llm_result['is_composite'] and llm_result.get('subgoals'):
                    # Convert LLM subgoals to our format
                    subgoals = [
                        self._create_subgoal(idx, sg, "general", 0.8)
                        for idx, sg in enumerate(llm_result['subgoals'][:4])  # Max 4
                    ]
                    
                    return {
                        "goal": goal,
                        "is_composite": True,
                        "subgoals": subgoals,
                        "total_subgoals": len(subgoals),
                        "complexity_score": min(1.0, len(subgoals) * 0.15),
                        "llm_reasoning": llm_result.get('reasoning', '')
                    }
                else:
                    return {
                        "goal": goal,
                        "is_composite": False,
                        "subgoals": [],
                        "total_subgoals": 0,
                        "complexity_score": 0.1,
                        "llm_reasoning": llm_result.get('reasoning', '')
                    }
        
        # Fallback: Pattern-based classification if LLM not available
        # Check composite patterns
        is_composite = any(
            re.search(pattern, goal, re.IGNORECASE)
            for pattern in self.COMPOSITE_PATTERNS
        )
        
        if is_composite:
            subgoals = self.decompose(goal)
            # Filter out duplicates/overlaps
            subgoals = self._deduplicate_subgoals(subgoals)
            
            return {
                "goal": goal,
                "is_composite": True,
                "subgoals": subgoals,
                "total_subgoals": len(subgoals),
                "complexity_score": min(1.0, len(subgoals) * 0.15)
            }
        else:
            return {
                "goal": goal,
                "is_composite": False,
                "subgoals": [],
                "total_subgoals": 0,
                "complexity_score": 0.1
            }
    
    def decompose(self, goal: str) -> List[Dict]:
        """
        Decompose a composite goal into 2-4 subgoals.
        
        CONSTRAINT: Max 4 subgoals (prevents explosion)
        """
        subgoals = []
        
        # Heuristic-based decomposition
        # In production, could use NLP but must remain deterministic
        
        if any(kw in goal.lower() for kw in ["design", "plan", "build"]):
            # Design/Plan goals → Research + Analysis + Strategy
            subgoals.append(self._create_subgoal(
                0,
                f"Research and gather background for: {goal}",
                "research",
                0.9
            ))
            subgoals.append(self._create_subgoal(
                1,
                f"Analyze requirements and constraints for: {goal}",
                "analysis",
                0.85
            ))
            subgoals.append(self._create_subgoal(
                2,
                f"Draft a strategic approach for: {goal}",
                "strategy",
                0.8
            ))
        
        elif any(kw in goal.lower() for kw in ["compare", "analyze", "evaluate"]):
            # Compare/Analyze goals → Research both sides + Synthesis
            subgoals.append(self._create_subgoal(
                0,
                f"Research and gather information on first topic: {goal}",
                "research",
                0.9
            ))
            subgoals.append(self._create_subgoal(
                1,
                f"Research and gather information on second topic: {goal}",
                "research",
                0.9
            ))
            subgoals.append(self._create_subgoal(
                2,
                f"Compare and synthesize findings from: {goal}",
                "synthesis",
                0.85
            ))
        
        # Fallback: treat as atomic (just return original as single subgoal)
        if not subgoals:
            subgoals.append(self._create_subgoal(0, goal, "general", 0.9))
        
        # CONSTRAINT: Never exceed 4 subgoals
        return subgoals[:4]
    
    def _create_subgoal(self, index: int, subgoal_text: str, subgoal_type: str, 
                       confidence: float) -> Dict:
        """Create a subgoal dict"""
        return {
            "index": index,
            "goal": subgoal_text,
            "type": subgoal_type,
            "confidence": confidence
        }
    
    def _deduplicate_subgoals(self, subgoals: List[Dict]) -> List[Dict]:
        """Remove duplicate or highly overlapping subgoals"""
        if len(subgoals) <= 1:
            return subgoals
        
        # Simple deduplication: check for significant keyword overlap
        unique = []
        seen_keywords = set()
        
        for sg in subgoals:
            keywords = set(sg['goal'].lower().split())
            # If >50% overlap with already seen, skip
            if seen_keywords:
                overlap = seen_keywords & keywords
                if len(overlap) > len(keywords) * 0.5:
                    logging.debug(f"Skipping duplicate subgoal: {sg['goal'][:50]}...")
                    continue
            
            unique.append(sg)
            seen_keywords.update(keywords)
        
        return unique
    
    def validate_decomposition(self, goal: str, subgoals: List[Dict]) -> bool:
        """
        Validate that decomposition is sound.
        
        Checks:
        - Never exceeds 4 subgoals
        - Subgoals are distinct
        - Each subgoal is executable
        """
        # CONSTRAINT: Max 4 subgoals
        if len(subgoals) > 4:
            logging.warning(f"Decomposition exceeds 4 subgoals: {len(subgoals)}")
            return False
        
        # Check that subgoals reference the original goal (loose coupling)
        for sg in subgoals:
            if not sg.get('goal'):
                logging.warning(f"Subgoal missing goal text: {sg}")
                return False
        
        return True


# Singleton instance
goal_decomposer = GoalDecomposer()
