"""
Research Adaptive Engine Selector

Uses learning signals to dynamically improve engine selection strategies.

Reads learning signals from Firebase memory and adjusts:
1. Engine priority weights per task type
2. Task decomposition strategies  
3. Completeness thresholds
4. Confidence scoring calibration

This creates a continuous feedback loop where each research session
teaches the system to make better decisions next time.
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ResearchAdaptiveSelector:
    """
    Dynamically adjusts research strategy based on learning signals.
    
    Process:
    1. Load learning signals from Firebase memory
    2. Calculate engine effectiveness per task type
    3. Adjust engine selection weights
    4. Update task decomposition heuristics
    5. Calibrate completeness thresholds
    """
    
    def __init__(self):
        """Initialize adaptive selector."""
        from backend.memory_manager import memory
        self.memory = memory
        
        # Learned weights (initialized to neutral)
        self.engine_weights: Dict[str, Dict[str, float]] = {}  # task_type -> engine -> weight
        self.task_decomposition_scores: Dict[str, float] = {}  # task_type -> effectiveness
        self.completeness_thresholds: Dict[str, float] = {}  # task_type -> min_threshold
        
        # Load initial weights from Firebase signals if available
        self._load_signals()
    
    def _load_signals(self) -> None:
        """Load and process learning signals from Firebase."""
        try:
            index_key = "research_learning_signal_index"
            signal_ids = self.memory.safe_call("get", index_key) or []
            
            if not signal_ids:
                logger.debug("[ADAPTIVE] No signals in Firebase yet, using default weights")
                return
            
            signals = []
            for signal_id in signal_ids:
                signal_key = f"research_signal:{signal_id}"
                signal = self.memory.safe_call("get", signal_key)
                if signal:
                    signals.append(signal)
            
            logger.debug(f"[ADAPTIVE] Loaded {len(signals)} signals from Firebase")
            
            # Process signals to update weights
            self._process_engine_signals(signals)
            self._process_task_decomposition_signals(signals)
            self._process_completeness_signals(signals)
        except Exception as e:
            logger.warning(f"[ADAPTIVE] Failed to load signals from Firebase: {e}")
    
    def _process_engine_signals(self, signals: List[Dict]) -> None:
        """Extract engine effectiveness from signals."""
        for signal in signals:
            if signal.get("signal_type") != "engine_effectiveness":
                continue
            
            task_type = signal.get("task_type", "custom")
            engine = signal.get("supporting_evidence", {}).get("engine", "unknown")
            confidence = signal.get("confidence", 0.5)
            
            if task_type not in self.engine_weights:
                self.engine_weights[task_type] = {}
            
            # Update weight with exponential moving average
            current = self.engine_weights[task_type].get(engine, 0.5)
            new_weight = 0.7 * current + 0.3 * confidence
            self.engine_weights[task_type][engine] = new_weight
            
            logger.debug(f"[ADAPTIVE] Updated {task_type}/{engine} weight to {new_weight:.2f}")
    
    def _process_task_decomposition_signals(self, signals: List[Dict]) -> None:
        """Extract task decomposition effectiveness."""
        for signal in signals:
            if signal.get("signal_type") != "task_decomposition_effectiveness":
                continue
            
            task_type = signal.get("task_type", "CUSTOM")
            confidence = signal.get("confidence", 0.5)
            
            # Task decomposition scores indicate strategy effectiveness
            current = self.task_decomposition_scores.get(task_type, 0.5)
            new_score = 0.7 * current + 0.3 * confidence
            self.task_decomposition_scores[task_type] = new_score
            
            logger.debug(f"[ADAPTIVE] Updated {task_type} decomposition score to {new_score:.2f}")
    
    def _process_completeness_signals(self, signals: List[Dict]) -> None:
        """Extract completeness threshold from signals."""
        for signal in signals:
            if signal.get("signal_type") != "completeness_assessment":
                continue
            
            task_type = signal.get("task_type", "CUSTOM")
            completeness = signal.get("supporting_evidence", {}).get("completeness_score", 0.7)
            
            # Use this as baseline for future completeness expectations
            current = self.completeness_thresholds.get(task_type, 0.7)
            new_threshold = 0.8 * current + 0.2 * completeness
            self.completeness_thresholds[task_type] = new_threshold
            
            logger.debug(f"[ADAPTIVE] Updated {task_type} completeness threshold to {new_threshold:.2f}")
    
    def select_engines_for_task(
        self,
        task_type: str,
        default_engines: List[str]
    ) -> Tuple[List[str], Dict[str, float]]:
        """
        Select and rank engines for a research task using learned weights.
        
        Args:
            task_type: Type of research task
            default_engines: Fallback engines if no learned data
            
        Returns:
            Tuple of (ranked_engines, weights)
        """
        # Get learned weights or use defaults
        if task_type not in self.engine_weights:
            logger.debug(f"[ADAPTIVE] No learned weights for {task_type}, using defaults")
            weights = {engine: 0.5 for engine in default_engines}
        else:
            weights = self.engine_weights[task_type]
        
        # Ensure all default engines are in weights (for new engines)
        for engine in default_engines:
            if engine not in weights:
                weights[engine] = 0.5
        
        # Sort by weight (highest first)
        ranked_engines = sorted(weights.keys(), key=lambda e: weights[e], reverse=True)
        
        logger.info(f"[ADAPTIVE] Selected engines for {task_type}: {ranked_engines}")
        logger.info(f"[ADAPTIVE] Weights: {weights}")
        
        return ranked_engines, weights
    
    def get_completeness_threshold(self, task_type: str) -> float:
        """
        Get learned completeness threshold for task type.
        
        Args:
            task_type: Type of research task
            
        Returns:
            Completeness threshold (0.0-1.0)
        """
        threshold = self.completeness_thresholds.get(task_type, 0.7)
        logger.debug(f"[ADAPTIVE] Completeness threshold for {task_type}: {threshold:.2f}")
        return threshold
    
    def should_continue_research(
        self,
        task_type: str,
        current_completeness: float,
        attempts_made: int = 1,
        max_attempts: int = 3
    ) -> bool:
        """
        Decide whether to continue researching based on completeness and attempts.
        
        Args:
            task_type: Type of research task
            current_completeness: Current completeness score
            attempts_made: Number of attempts so far
            max_attempts: Maximum allowed attempts
            
        Returns:
            True if should continue, False if should stop
        """
        threshold = self.get_completeness_threshold(task_type)
        
        # Stop if we've reached threshold or maxed out attempts
        if current_completeness >= threshold:
            logger.debug(f"[ADAPTIVE] Completeness {current_completeness:.2f} >= threshold {threshold:.2f}, stopping")
            return False
        
        if attempts_made >= max_attempts:
            logger.debug(f"[ADAPTIVE] Max attempts {max_attempts} reached, stopping")
            return False
        
        logger.debug(f"[ADAPTIVE] Completeness {current_completeness:.2f} < threshold {threshold:.2f}, continuing")
        return True
    
    def get_task_strategy_adjustment(self, task_type: str) -> Dict[str, any]:
        """
        Get recommended adjustments to task strategy based on learning.
        
        Args:
            task_type: Type of research task
            
        Returns:
            Dict with adjustment recommendations
        """
        decomposition_score = self.task_decomposition_scores.get(task_type, 0.5)
        
        adjustments = {
            "task_type": task_type,
            "decomposition_effective": decomposition_score > 0.7,
            "decomposition_confidence": decomposition_score,
        }
        
        if decomposition_score < 0.5:
            adjustments["recommendation"] = "Consider revising task decomposition strategy"
        elif decomposition_score < 0.7:
            adjustments["recommendation"] = "Task decomposition could be improved"
        else:
            adjustments["recommendation"] = "Task decomposition strategy is working well"
        
        return adjustments
    
    def get_performance_summary(self) -> Dict[str, any]:
        """Get summary of learned performance."""
        return {
            "task_types_learned": len(self.engine_weights),
            "total_engines_tracked": sum(len(e) for e in self.engine_weights.values()),
            "engine_weights": self.engine_weights,
            "task_decomposition_scores": self.task_decomposition_scores,
            "completeness_thresholds": self.completeness_thresholds,
        }


# Global instance
research_adaptive_selector = ResearchAdaptiveSelector()
