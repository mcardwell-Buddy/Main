"""
Human feedback manager: stores and applies high-priority feedback.
"""

import re
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from Back_End.memory import memory


class FeedbackManager:
    def __init__(self):
        self.collection_key = "human_feedback"

    def submit_feedback(
        self,
        goal_pattern: str,
        tool: str = None,
        domain: str = "_global",
        verdict: str = "negative",
        reason: str = "",
        evidence: str = "",
        action: str = "penalize",
        impact: Dict = None,
        human_id: str = "default_user",
    ) -> Dict:
        record = {
            "type": "human_feedback",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "human_id": human_id,
            "goal_pattern": goal_pattern or "",
            "tool": tool,
            "domain": domain or "_global",
            "verdict": verdict,
            "reason": reason,
            "evidence": evidence,
            "importance": 0.95,
            "action": action,
            "impact": impact or {"tool_adjustment": 0.5, "penalty_duration": "permanent", "hard_constraint": None},
        }

        key = f"{self.collection_key}"
        existing = memory.safe_call("get", key) or []
        existing.append(record)
        memory.safe_call("set", key, existing)
        return record

    def list_feedback(self, domain: str = None) -> List[Dict]:
        records = memory.safe_call("get", self.collection_key) or []
        if not domain:
            return records
        return [r for r in records if r.get("domain") in {domain, "_global"}]

    def get_tool_adjustment(self, goal: str, tool: str, domain: str) -> Tuple[float, Optional[str], List[Dict]]:
        """Return (multiplier, hard_constraint, matched_feedback)."""
        multiplier = 1.0
        hard_constraint = None
        matched = []

        for record in self._find_applicable_feedback(goal, tool, domain):
            matched.append(record)
            action = record.get("action")
            impact = record.get("impact") or {}
            adjustment = impact.get("tool_adjustment", 0.5)
            constraint = impact.get("hard_constraint")

            if action == "constraint" or constraint:
                hard_constraint = constraint or "never_use"
                multiplier = 0.0
                break
            if action == "boost":
                multiplier *= max(1.0, float(adjustment))
            else:
                multiplier *= max(0.0, float(adjustment))

        return multiplier, hard_constraint, matched

    def get_feedback_stats(self, goal_pattern: str, domain: str = "_global") -> Dict:
        """Get feedback statistics for a specific goal pattern"""
        records = self._find_applicable_feedback(goal_pattern, None, domain)
        
        stats = {
            'total_feedback': len(records),
            'positive': 0,
            'negative': 0,
            'corrections': 0,
            'confidence_adjustment': 1.0
        }
        
        for record in records:
            verdict = record.get('verdict', 'negative')
            if verdict == 'positive':
                stats['positive'] += 1
            else:
                stats['negative'] += 1
            
            # Check if this is a correction
            if record.get('impact', {}).get('correction'):
                stats['corrections'] += 1
        
        # Calculate confidence adjustment
        if stats['total_feedback'] > 0:
            positive_ratio = stats['positive'] / stats['total_feedback']
            # Adjust confidence: more positive = boost, more negative = reduce
            stats['confidence_adjustment'] = 0.5 + (positive_ratio * 0.5)
        
        return stats

    def _find_applicable_feedback(self, goal: str, tool: str, domain: str) -> List[Dict]:
        records = memory.safe_call("get", self.collection_key) or []
        applicable = []

        for record in records:
            record_domain = record.get("domain", "_global")
            if record_domain not in {domain, "_global"}:
                continue
            record_tool = record.get("tool")
            if record_tool and record_tool != tool:
                continue

            pattern = record.get("goal_pattern", "")
            if pattern and not self._matches_pattern(goal, pattern):
                continue

            applicable.append(record)

        return applicable

    def _matches_pattern(self, goal: str, pattern: str) -> bool:
        try:
            return re.search(pattern, goal, re.IGNORECASE) is not None
        except re.error:
            # treat as literal substring if regex invalid
            return pattern.lower() in goal.lower()


feedback_manager = FeedbackManager()

