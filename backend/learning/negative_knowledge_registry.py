"""
Negative Knowledge Registry for Buddy

CONSTRAINTS:
- NO autonomy (never blocks execution)
- NO LLM usage (deterministic pattern detection)
- Observational only (learns from failures)
- Analytical only (surfaces insights)

PURPOSE:
Captures what Buddy should NOT do again by learning from:
- Repeated mission failures
- High cost / low value patterns
- Non-converting opportunity types
- Dead-end navigation patterns

This system NEVER triggers actions or blocks execution.
It only persists negative knowledge for human review and future analysis.
"""

import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Set
from pathlib import Path
from dataclasses import dataclass, asdict


@dataclass
class NegativeKnowledgeEntry:
    """
    A single entry representing a pattern Buddy should avoid.
    
    Attributes:
        pattern_type: Category of the pattern (site, goal, selector, opportunity, program)
        pattern_signature: Hashable identifier for deduplication
        reason: Human-readable explanation of why to avoid
        evidence: List of signal IDs supporting this pattern
        confidence: 0.0-1.0 indicating strength of evidence
        first_observed: When pattern was first detected
        last_observed: When pattern was most recently observed
        occurrence_count: How many times this pattern has been observed
    """
    pattern_type: str  # "site" | "goal" | "selector" | "opportunity" | "program"
    pattern_signature: str
    reason: str
    evidence: List[str]
    confidence: float
    first_observed: str
    last_observed: str
    occurrence_count: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'NegativeKnowledgeEntry':
        """Create entry from dictionary."""
        return NegativeKnowledgeEntry(**data)


class NegativeKnowledgeRegistry:
    """
    Registry for capturing and persisting negative knowledge.
    
    This is a PURELY OBSERVATIONAL system that:
    1. Analyzes learning_signals.jsonl for failure patterns
    2. Persists patterns to negative_knowledge.jsonl
    3. Surfaces insights via whiteboard
    
    It NEVER:
    - Blocks mission execution
    - Modifies Selenium behavior
    - Makes autonomous decisions
    - Uses LLMs for analysis
    """
    
    def __init__(self, outputs_dir: str = "outputs/phase25"):
        """
        Initialize the registry.
        
        Args:
            outputs_dir: Directory containing learning_signals.jsonl
        """
        self.outputs_dir = Path(outputs_dir)
        self.registry_file = self.outputs_dir / "negative_knowledge.jsonl"
        self.learning_signals_file = self.outputs_dir / "learning_signals.jsonl"
        
        # In-memory cache of patterns (signature -> entry)
        self._registry: Dict[str, NegativeKnowledgeEntry] = {}
        
        # Load existing registry if present
        self._load_registry()
    
    def _load_registry(self) -> None:
        """Load existing negative knowledge from disk."""
        if not self.registry_file.exists():
            return
        
        try:
            with open(self.registry_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        entry_dict = json.loads(line)
                        entry = NegativeKnowledgeEntry.from_dict(entry_dict)
                        self._registry[entry.pattern_signature] = entry
        except Exception as e:
            print(f"Warning: Failed to load negative knowledge registry: {e}")
    
    def _persist_entry(self, entry: NegativeKnowledgeEntry) -> None:
        """Append entry to registry file."""
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        
        with open(self.registry_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry.to_dict()) + '\n')
    
    def _generate_signature(self, pattern_type: str, components: Dict[str, Any]) -> str:
        """
        Generate a deterministic signature for a pattern.
        
        Args:
            pattern_type: Type of pattern (site, goal, selector, etc.)
            components: Key components to hash
            
        Returns:
            Hexadecimal signature string
        """
        # Sort components for deterministic hashing
        sorted_items = sorted(components.items())
        signature_input = f"{pattern_type}::{json.dumps(sorted_items, sort_keys=True)}"
        return hashlib.sha256(signature_input.encode()).hexdigest()[:16]
    
    def add_pattern(
        self,
        pattern_type: str,
        pattern_components: Dict[str, Any],
        reason: str,
        evidence_signal_ids: List[str],
        confidence: float = 0.5
    ) -> NegativeKnowledgeEntry:
        """
        Add or update a negative knowledge pattern.
        
        Args:
            pattern_type: Category of pattern
            pattern_components: Dictionary of identifying components
            reason: Why this pattern should be avoided
            evidence_signal_ids: Signal IDs supporting this pattern
            confidence: Confidence in this pattern (0.0-1.0)
            
        Returns:
            The created or updated entry
        """
        signature = self._generate_signature(pattern_type, pattern_components)
        now = datetime.now(timezone.utc).isoformat()
        
        if signature in self._registry:
            # Update existing entry
            entry = self._registry[signature]
            entry.last_observed = now
            entry.occurrence_count += 1
            entry.evidence.extend(evidence_signal_ids)
            # Increase confidence with more observations (capped at 1.0)
            entry.confidence = min(1.0, entry.confidence + 0.1)
        else:
            # Create new entry
            entry = NegativeKnowledgeEntry(
                pattern_type=pattern_type,
                pattern_signature=signature,
                reason=reason,
                evidence=evidence_signal_ids,
                confidence=confidence,
                first_observed=now,
                last_observed=now,
                occurrence_count=1
            )
            self._registry[signature] = entry
        
        # Persist to disk
        self._persist_entry(entry)
        
        return entry
    
    def analyze_mission_failure(self, mission_signal: Dict[str, Any]) -> Optional[NegativeKnowledgeEntry]:
        """
        Analyze a mission_failed signal for negative patterns.
        
        Args:
            mission_signal: The mission_failed or mission_status_update signal
            
        Returns:
            Newly created/updated entry if pattern detected, None otherwise
        """
        if mission_signal.get("signal_type") not in ["mission_failed", "mission_status_update"]:
            return None
        
        if mission_signal.get("status") == "failed" or mission_signal.get("signal_type") == "mission_failed":
            reason = mission_signal.get("reason", "unknown")
            mission_id = mission_signal.get("mission_id", "unknown")
            
            # Pattern: Failed mission by reason
            pattern_components = {
                "failure_reason": reason,
                "mission_id": mission_id
            }
            
            return self.add_pattern(
                pattern_type="mission",
                pattern_components=pattern_components,
                reason=f"Mission failed: {reason}",
                evidence_signal_ids=[mission_id],
                confidence=0.6
            )
        
        return None
    
    def analyze_selector_failures(self, selector_signals: List[Dict[str, Any]]) -> List[NegativeKnowledgeEntry]:
        """
        Analyze selector_outcome signals for failing selector patterns.
        
        Args:
            selector_signals: List of selector_outcome signals
            
        Returns:
            List of entries for failing selectors
        """
        entries = []
        
        # Group by selector
        selector_outcomes: Dict[str, List[str]] = {}
        
        for signal in selector_signals:
            if signal.get("signal_type") == "selector_outcome":
                selector = signal.get("selector", "")
                outcome = signal.get("outcome", "")
                
                if outcome == "failure":
                    if selector not in selector_outcomes:
                        selector_outcomes[selector] = []
                    selector_outcomes[selector].append(signal.get("timestamp", ""))
        
        # Create patterns for selectors with multiple failures
        for selector, timestamps in selector_outcomes.items():
            if len(timestamps) >= 2:  # At least 2 failures
                pattern_components = {
                    "selector": selector,
                    "selector_type": "css" if selector.startswith((".","#","[")) else "xpath"
                }
                
                confidence = min(0.9, 0.5 + (len(timestamps) * 0.1))
                
                entry = self.add_pattern(
                    pattern_type="selector",
                    pattern_components=pattern_components,
                    reason=f"Selector consistently fails (failed {len(timestamps)} times)",
                    evidence_signal_ids=timestamps[:5],  # Keep first 5 as evidence
                    confidence=confidence
                )
                entries.append(entry)
        
        return entries
    
    def analyze_goal_ambiguity(self, ambiguity_signal: Dict[str, Any]) -> Optional[NegativeKnowledgeEntry]:
        """
        Analyze mission_ambiguous signal for problematic goal patterns.
        
        Args:
            ambiguity_signal: The mission_ambiguous signal
            
        Returns:
            Entry if pattern detected, None otherwise
        """
        if ambiguity_signal.get("signal_type") != "mission_ambiguous":
            return None
        
        mission_id = ambiguity_signal.get("mission_id", "unknown")
        ambiguity_type = ambiguity_signal.get("ambiguity_type", "unknown")
        
        pattern_components = {
            "mission_id": mission_id,
            "ambiguity_type": ambiguity_type
        }
        
        return self.add_pattern(
            pattern_type="goal",
            pattern_components=pattern_components,
            reason=f"Goal produces ambiguous results: {ambiguity_type}",
            evidence_signal_ids=[mission_id],
            confidence=0.7
        )
    
    def analyze_high_cost_pattern(self, cost_signal: Dict[str, Any]) -> Optional[NegativeKnowledgeEntry]:
        """
        Analyze excessive_cost signal for expensive patterns.
        
        Args:
            cost_signal: Signal with cost information
            
        Returns:
            Entry if expensive pattern detected, None otherwise
        """
        if cost_signal.get("signal_type") != "excessive_cost":
            return None
        
        mission_id = cost_signal.get("mission_id", "unknown")
        cost_type = cost_signal.get("cost_type", "unknown")
        
        pattern_components = {
            "mission_id": mission_id,
            "cost_type": cost_type
        }
        
        return self.add_pattern(
            pattern_type="opportunity",
            pattern_components=pattern_components,
            reason=f"Pattern has excessive cost: {cost_type}",
            evidence_signal_ids=[mission_id],
            confidence=0.8
        )
    
    def get_all_patterns(self) -> List[NegativeKnowledgeEntry]:
        """
        Get all patterns in the registry.
        
        Returns:
            List of all entries
        """
        return list(self._registry.values())
    
    def get_patterns_by_type(self, pattern_type: str) -> List[NegativeKnowledgeEntry]:
        """
        Get patterns filtered by type.
        
        Args:
            pattern_type: Type to filter by
            
        Returns:
            List of matching entries
        """
        return [entry for entry in self._registry.values() if entry.pattern_type == pattern_type]
    
    def get_high_confidence_patterns(self, min_confidence: float = 0.7) -> List[NegativeKnowledgeEntry]:
        """
        Get patterns with high confidence.
        
        Args:
            min_confidence: Minimum confidence threshold
            
        Returns:
            List of high-confidence entries
        """
        return [entry for entry in self._registry.values() if entry.confidence >= min_confidence]
    
    def process_learning_signals(self, max_signals: Optional[int] = None) -> Dict[str, int]:
        """
        Process learning_signals.jsonl to extract negative patterns.
        
        This is the main analysis function that scans all signals.
        
        Args:
            max_signals: Maximum number of signals to process (None = all)
            
        Returns:
            Statistics about patterns detected
        """
        if not self.learning_signals_file.exists():
            return {"processed": 0, "patterns_detected": 0}
        
        stats = {
            "processed": 0,
            "mission_failures": 0,
            "selector_failures": 0,
            "ambiguity_patterns": 0,
            "cost_patterns": 0
        }
        
        selector_signals = []
        
        with open(self.learning_signals_file, 'r', encoding='utf-8') as f:
            for line in f:
                if max_signals and stats["processed"] >= max_signals:
                    break
                
                if line.strip():
                    signal = json.loads(line)
                    stats["processed"] += 1
                    
                    # Analyze mission failures
                    if signal.get("signal_type") in ["mission_failed", "mission_status_update"]:
                        if signal.get("status") == "failed" or signal.get("signal_type") == "mission_failed":
                            entry = self.analyze_mission_failure(signal)
                            if entry:
                                stats["mission_failures"] += 1
                    
                    # Collect selector outcomes for batch analysis
                    elif signal.get("signal_type") == "selector_outcome":
                        selector_signals.append(signal)
                    
                    # Analyze ambiguity
                    elif signal.get("signal_type") == "mission_ambiguous":
                        entry = self.analyze_goal_ambiguity(signal)
                        if entry:
                            stats["ambiguity_patterns"] += 1
                    
                    # Analyze excessive cost
                    elif signal.get("signal_type") == "excessive_cost":
                        entry = self.analyze_high_cost_pattern(signal)
                        if entry:
                            stats["cost_patterns"] += 1
        
        # Batch analyze selector failures
        selector_entries = self.analyze_selector_failures(selector_signals)
        stats["selector_failures"] = len(selector_entries)
        
        stats["patterns_detected"] = (
            stats["mission_failures"] + 
            stats["selector_failures"] + 
            stats["ambiguity_patterns"] + 
            stats["cost_patterns"]
        )
        
        return stats
    
    def get_summary_by_type(self) -> Dict[str, Dict[str, Any]]:
        """
        Get summary statistics grouped by pattern type.
        
        Returns:
            Dictionary with stats for each pattern type
        """
        summary = {}
        
        for pattern_type in ["mission", "selector", "goal", "opportunity", "program", "site"]:
            patterns = self.get_patterns_by_type(pattern_type)
            if patterns:
                total_occurrences = sum(p.occurrence_count for p in patterns)
                avg_confidence = sum(p.confidence for p in patterns) / len(patterns)
                
                summary[pattern_type] = {
                    "pattern_count": len(patterns),
                    "total_occurrences": total_occurrences,
                    "avg_confidence": round(avg_confidence, 2),
                    "high_confidence_count": len([p for p in patterns if p.confidence >= 0.7])
                }
        
        return summary


def get_negative_knowledge_for_whiteboard(outputs_dir: str = "outputs/phase25") -> Dict[str, Any]:
    """
    Get negative knowledge formatted for whiteboard display.
    
    Args:
        outputs_dir: Directory containing negative_knowledge.jsonl
        
    Returns:
        Dictionary with "what_buddy_avoids" section
    """
    registry = NegativeKnowledgeRegistry(outputs_dir=outputs_dir)
    
    summary = registry.get_summary_by_type()
    high_confidence = registry.get_high_confidence_patterns(min_confidence=0.7)
    
    # Group high-confidence patterns by type
    grouped_patterns = {}
    for entry in high_confidence[:10]:  # Top 10 only
        if entry.pattern_type not in grouped_patterns:
            grouped_patterns[entry.pattern_type] = []
        
        grouped_patterns[entry.pattern_type].append({
            "reason": entry.reason,
            "confidence": entry.confidence,
            "occurrences": entry.occurrence_count,
            "first_seen": entry.first_observed,
            "last_seen": entry.last_observed
        })
    
    return {
        "summary": summary,
        "high_confidence_patterns": grouped_patterns,
        "total_patterns": len(registry.get_all_patterns())
    }
