"""
Decision Rationale Emitter: Deterministic explanations for key actions.
Purely explanatory - no LLM, no autonomy changes, no behavioral changes.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class DecisionRationale:
    """Structured explanation for a decision."""
    decision: str
    because: List[str]
    action_type: str
    decision_inputs: Dict[str, Any]
    thresholds_used: Dict[str, Any]
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "decision": self.decision,
            "because": self.because,
            "action_type": self.action_type,
            "decision_inputs": self.decision_inputs,
            "thresholds_used": self.thresholds_used,
            "timestamp": self.timestamp
        }
    
    def to_signal(self, mission_id: str) -> Dict[str, Any]:
        """Convert to learning signal format."""
        return {
            "signal_type": "decision_rationale",
            "signal_layer": "explainability",
            "signal_source": "decision_engine",
            "mission_id": mission_id,
            "action_type": self.action_type,
            "rationale": {
                "decision": self.decision,
                "because": self.because
            },
            "decision_inputs": self.decision_inputs,
            "thresholds_used": self.thresholds_used,
            "timestamp": self.timestamp
        }


class DecisionRationaleEmitter:
    """
    Emits deterministic explanations for key actions.
    
    Used for:
    - intent_action_taken: Why we chose this navigation action
    - intent_action_blocked: Why we rejected an action
    - selector execution choice: Why we used this selector
    
    Purely explanatory - does not influence execution.
    """
    
    def explain_intent_action_taken(
        self,
        action: Dict[str, Any],
        goal: str,
        confidence: float,
        score: int,
        total_candidates: int,
        confidence_threshold: float = 0.5
    ) -> DecisionRationale:
        """
        Explain why we took this navigation action.
        
        Args:
            action: The action taken (text, href, score, signals)
            goal: The mission goal
            confidence: Action confidence score
            score: Action ranking score
            total_candidates: Total candidates considered
            confidence_threshold: Minimum confidence for action
            
        Returns:
            DecisionRationale with deterministic explanation
        """
        decision = f"Navigate to: {action.get('text', 'unknown')}"
        because = []
        
        # Reason 1: Score-based ranking
        if score > 0:
            because.append(f"Highest ranked action (score: {score}/{total_candidates} candidates)")
        
        # Reason 2: Confidence threshold
        if confidence >= confidence_threshold:
            because.append(f"Confidence ({confidence:.2f}) exceeds threshold ({confidence_threshold:.2f})")
        else:
            because.append(f"Best available action despite low confidence ({confidence:.2f} < {confidence_threshold:.2f})")
        
        # Reason 3: Matching signals
        action_signals = action.get('signals', [])
        if action_signals:
            signal_desc = ', '.join(action_signals[:3])  # Show first 3
            because.append(f"Matched signals: {signal_desc}")
        
        # Reason 4: Goal alignment
        if 'goal_keyword_match' in str(action_signals):
            because.append("Keywords from goal found in target")
        
        return DecisionRationale(
            decision=decision,
            because=because,
            action_type="intent_action_taken",
            decision_inputs={
                "action_text": action.get('text'),
                "action_href": action.get('href'),
                "goal": goal,
                "confidence": confidence,
                "score": score,
                "total_candidates": total_candidates
            },
            thresholds_used={
                "confidence_threshold": confidence_threshold
            },
            timestamp=datetime.now(timezone.utc).isoformat()
        )
    
    def explain_intent_action_blocked(
        self,
        action: Dict[str, Any],
        goal: str,
        confidence: float,
        block_reason: str,
        confidence_threshold: float = 0.5
    ) -> DecisionRationale:
        """
        Explain why we blocked/rejected this navigation action.
        
        Args:
            action: The action that was blocked
            goal: The mission goal
            confidence: Action confidence score
            block_reason: Why it was blocked
            confidence_threshold: Minimum confidence required
            
        Returns:
            DecisionRationale with deterministic explanation
        """
        decision = f"Blocked navigation to: {action.get('text', 'unknown')}"
        because = []
        
        # Primary blocking reason
        if block_reason == "confidence_too_low":
            because.append(f"Confidence ({confidence:.2f}) below threshold ({confidence_threshold:.2f})")
        elif block_reason == "no_goal_match":
            because.append("No keywords from goal found in target")
        elif block_reason == "negative_signals":
            because.append("Matched negative/exclusion patterns")
        else:
            because.append(f"Blocked: {block_reason}")
        
        # Additional context
        action_signals = action.get('signals', [])
        if not action_signals:
            because.append("No positive signals detected")
        
        return DecisionRationale(
            decision=decision,
            because=because,
            action_type="intent_action_blocked",
            decision_inputs={
                "action_text": action.get('text'),
                "action_href": action.get('href'),
                "goal": goal,
                "confidence": confidence,
                "block_reason": block_reason
            },
            thresholds_used={
                "confidence_threshold": confidence_threshold
            },
            timestamp=datetime.now(timezone.utc).isoformat()
        )
    
    def explain_selector_choice(
        self,
        selector: str,
        selector_type: str,
        ranked: bool,
        fallback_used: bool,
        success_rate: Optional[float] = None,
        page_number: int = 1
    ) -> DecisionRationale:
        """
        Explain why we used this selector.
        
        Args:
            selector: The selector used
            selector_type: Type (css, xpath, interaction)
            ranked: Whether from ranking system
            fallback_used: Whether this is a fallback
            success_rate: Historical success rate if available
            page_number: Current page number
            
        Returns:
            DecisionRationale with deterministic explanation
        """
        decision = f"Execute selector: {selector}"
        because = []
        
        # Reason 1: Selection method
        if ranked and not fallback_used:
            because.append("Selected from learned selector rankings")
            if success_rate is not None:
                because.append(f"Historical success rate: {success_rate:.1%}")
        elif fallback_used:
            because.append("Using fallback selector (ranked selectors unavailable)")
        else:
            because.append("Using provided selector")
        
        # Reason 2: Selector type
        if selector_type == "css":
            because.append("CSS selector preferred for performance")
        elif selector_type == "xpath":
            because.append("XPath selector for complex matching")
        elif selector_type == "interaction":
            because.append("Direct interaction with located element")
        
        # Reason 3: Page context
        if page_number > 1:
            because.append(f"Pagination context (page {page_number})")
        
        return DecisionRationale(
            decision=decision,
            because=because,
            action_type="selector_execution",
            decision_inputs={
                "selector": selector,
                "selector_type": selector_type,
                "page_number": page_number,
                "ranked": ranked,
                "fallback_used": fallback_used,
                "success_rate": success_rate
            },
            thresholds_used={},
            timestamp=datetime.now(timezone.utc).isoformat()
        )
    
    def explain_goal_evaluation_decision(
        self,
        goal_satisfied: bool,
        confidence: float,
        items_collected: int,
        target_items: Optional[int],
        confidence_threshold: float = 0.6
    ) -> DecisionRationale:
        """
        Explain goal satisfaction decision.
        
        Args:
            goal_satisfied: Whether goal is satisfied
            confidence: Confidence in evaluation
            items_collected: Items collected count
            target_items: Target item count
            confidence_threshold: Minimum confidence for satisfaction
            
        Returns:
            DecisionRationale with deterministic explanation
        """
        if goal_satisfied:
            decision = "Goal satisfied"
            because = []
            
            if target_items and items_collected >= target_items:
                because.append(f"Target reached ({items_collected}/{target_items} items)")
            
            if confidence >= confidence_threshold:
                because.append(f"High confidence ({confidence:.2f} >= {confidence_threshold:.2f})")
            
            if items_collected > 0:
                because.append(f"Evidence collected ({items_collected} items)")
        else:
            decision = "Goal not satisfied"
            because = []
            
            if items_collected == 0:
                because.append("Zero items collected")
            elif target_items and items_collected < target_items:
                because.append(f"Target not reached ({items_collected}/{target_items} items)")
            
            if confidence < confidence_threshold:
                because.append(f"Low confidence ({confidence:.2f} < {confidence_threshold:.2f})")
        
        return DecisionRationale(
            decision=decision,
            because=because,
            action_type="goal_evaluation",
            decision_inputs={
                "goal_satisfied": goal_satisfied,
                "confidence": confidence,
                "items_collected": items_collected,
                "target_items": target_items
            },
            thresholds_used={
                "confidence_threshold": confidence_threshold
            },
            timestamp=datetime.now(timezone.utc).isoformat()
        )
    
    def should_emit_signal(self, rationale: DecisionRationale) -> bool:
        """
        Determine if decision rationale signal should be emitted.
        
        Always emit - these are always valuable for explainability.
        
        Args:
            rationale: The rationale to check
            
        Returns:
            True (always emit)
        """
        return True

