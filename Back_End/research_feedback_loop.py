"""
Research Feedback Loop

Evaluates research mission outcomes and generates learning signals
for continuous improvement of:
- Engine selection strategies
- Task decomposition effectiveness
- Entity matching/deduplication quality
- Confidence scoring calibration
- Research completion heuristics

This bridges research execution with Buddy's learning system,
enabling adaptive improvement over time.
"""

import logging
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum

from Back_End.memory import memory

logger = logging.getLogger(__name__)


class ResearchOutcomeType(str, Enum):
    """Types of research outcomes"""
    ENTITY_FOUND = "entity_found"
    INCOMPLETE_DATA = "incomplete_data"
    CONFLICTING_DATA = "conflicting_data"
    FAILED = "failed"
    AMBIGUOUS = "ambiguous"


@dataclass
class ResearchMetrics:
    """Metrics from a completed research session"""
    session_id: str
    query: str
    task_type: str  # COMPANY_RESEARCH, CONTACT_EXTRACTION, etc
    entities_found: int
    data_points_total: int
    deduplicated_count: int
    avg_confidence: float
    sources_used: List[str]
    engine_contributions: Dict[str, int]  # engine -> count of data points
    completeness_score: float
    duration_seconds: float
    success: bool
    error: Optional[str] = None


@dataclass
class ResearchFeedbackEvent:
    """Single feedback event from research execution"""
    feedback_id: str
    session_id: str
    task_type: str
    outcome: ResearchOutcomeType
    confidence: float
    query_quality: float  # 0.0-1.0: how clear was the query?
    engine_quality: Dict[str, float]  # engine -> quality score
    deduplication_quality: float  # how well did deduping work?
    completeness_assessment: float  # is research complete?
    reasoning: List[str]
    recommendation: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class ResearchLearningSignal:
    """Learning signal derived from research feedback"""
    signal_id: str
    signal_type: str  # "engine_effectiveness", "task_decomposition", etc
    target_component: str  # "engine_selection", "deduplication", "completeness", etc
    
    # Defaults
    signal_layer: str = "research"
    signal_source: str = "research_feedback_loop"
    task_type: str = ""
    
    # The learning
    confidence: float = 0.0
    recommendation: str = ""
    supporting_evidence: Dict[str, Any] = field(default_factory=dict)
    
    # Context
    research_session_id: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "signal_id": self.signal_id,
            "signal_type": self.signal_type,
            "signal_layer": self.signal_layer,
            "signal_source": self.signal_source,
            "target_component": self.target_component,
            "task_type": self.task_type,
            "confidence": self.confidence,
            "recommendation": self.recommendation,
            "supporting_evidence": self.supporting_evidence,
            "research_session_id": self.research_session_id,
            "timestamp": self.timestamp,
        }


class ResearchFeedbackLoop:
    """
    Evaluates research outcomes and generates learning signals.
    
    Process:
    1. Receive completed research session
    2. Calculate research metrics
    3. Assess outcome quality
    4. Generate feedback events
    5. Create learning signals
    6. Emit for learning system
    """
    
    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize research feedback loop.
        
        Args:
            output_dir: Where to write learning signals (default: outputs/research)
        """
        self.output_dir = output_dir or Path("outputs/research")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.feedback_events: List[ResearchFeedbackEvent] = []
        self.learning_signals: List[ResearchLearningSignal] = []
        self.metrics_history: List[ResearchMetrics] = []
    
    def evaluate_research_session(
        self,
        session_output: Dict[str, Any]
    ) -> ResearchMetrics:
        """
        Evaluate a completed research session.
        
        Args:
            session_output: Output dict from ResearchIntelligenceEngine.research()
            
        Returns:
            ResearchMetrics with evaluation results
        """
        session_id = session_output.get("session_id", "unknown")
        original_query = session_output.get("original_query", "")
        task_type = session_output.get("task_type", "unknown")
        completeness_score = session_output.get("completeness_score", 0.0)
        
        # Count findings
        findings = session_output.get("findings", {})
        total_data_points = sum(len(v) for v in findings.values())
        
        # Extract audit trail for engine tracking
        audit_trail = session_output.get("audit_trail", [])
        engine_usage = {}
        for task in audit_trail:
            engines = task.get("engines_used", [])
            for engine in engines:
                engine_usage[engine] = engine_usage.get(engine, 0) + 1
        
        # Calculate metrics
        sources_used = list(engine_usage.keys())
        duration_seconds = 0.0  # Would need to track in session
        
        # Estimate average confidence
        all_entities = []
        for entities in findings.values():
            all_entities.extend(entities)
        
        avg_confidence = 0.0
        if all_entities:
            if isinstance(all_entities[0], dict):
                confidences = [e.get("confidence", 0.0) for e in all_entities]
                avg_confidence = sum(confidences) / len(confidences)
            else:
                # If they're objects with confidence attribute
                confidences = [getattr(e, "confidence", 0.0) for e in all_entities]
                avg_confidence = sum(confidences) / len(confidences)
        
        metrics = ResearchMetrics(
            session_id=session_id,
            query=original_query,
            task_type=task_type,
            entities_found=len(findings),
            data_points_total=total_data_points,
            deduplicated_count=total_data_points,  # Already deduplicated in engine
            avg_confidence=avg_confidence,
            sources_used=sources_used,
            engine_contributions=engine_usage,
            completeness_score=completeness_score,
            duration_seconds=duration_seconds,
            success=total_data_points > 0,
        )
        
        self.metrics_history.append(metrics)
        logger.info(f"[RESEARCH_EVAL] Session {session_id}: {metrics.entities_found} entities, "
                   f"confidence {avg_confidence:.2f}, completeness {completeness_score:.2f}")
        
        return metrics
    
    def assess_outcome(
        self,
        metrics: ResearchMetrics
    ) -> ResearchFeedbackEvent:
        """
        Assess research outcome quality.
        
        Args:
            metrics: Calculated research metrics
            
        Returns:
            ResearchFeedbackEvent with assessment
        """
        # Determine outcome type
        if metrics.completeness_score >= 0.8:
            outcome = ResearchOutcomeType.ENTITY_FOUND
            confidence = metrics.avg_confidence
        elif metrics.completeness_score >= 0.5:
            outcome = ResearchOutcomeType.INCOMPLETE_DATA
            confidence = metrics.avg_confidence * 0.7
        elif metrics.entities_found == 0:
            outcome = ResearchOutcomeType.FAILED
            confidence = 0.0
        else:
            outcome = ResearchOutcomeType.AMBIGUOUS
            confidence = metrics.avg_confidence * 0.5
        
        # Assess component quality
        engine_quality = {}
        for engine, count in metrics.engine_contributions.items():
            # Simple heuristic: engines that found data get higher scores
            engine_quality[engine] = min(1.0, metrics.avg_confidence * (1.0 + count * 0.1))
        
        # Deduplication quality (higher when we have multiple sources for same entity)
        dedup_quality = min(1.0, len(metrics.sources_used) / 3.0)  # Max at 3 sources
        
        reasoning = []
        if outcome == ResearchOutcomeType.ENTITY_FOUND:
            reasoning.append(f"Successfully found {metrics.entities_found} entities with {len(metrics.sources_used)} sources")
            reasoning.append(f"Average confidence: {metrics.avg_confidence:.2f}")
            reasoning.append(f"Completeness score: {metrics.completeness_score:.2f}")
        elif outcome == ResearchOutcomeType.INCOMPLETE_DATA:
            reasoning.append(f"Found {metrics.entities_found} entities but completeness only {metrics.completeness_score:.2f}")
            reasoning.append(f"Consider expanding search to more sources")
        elif outcome == ResearchOutcomeType.FAILED:
            reasoning.append(f"No entities found for query: {metrics.query}")
            reasoning.append(f"Research strategy needs adjustment")
        
        # Build recommendation
        if outcome == ResearchOutcomeType.ENTITY_FOUND:
            recommendation = "Research successful. Continue current engine selection strategy."
        elif outcome == ResearchOutcomeType.INCOMPLETE_DATA:
            recommendation = f"Add more {', '.join(metrics.sources_used)} searches or try fallback engines."
        else:
            recommendation = "Review task decomposition or try different engines."
        
        event = ResearchFeedbackEvent(
            feedback_id=f"rfb_{metrics.session_id[:12]}",
            session_id=metrics.session_id,
            task_type=metrics.task_type,
            outcome=outcome,
            confidence=confidence,
            query_quality=0.8,  # TODO: parse query clarity
            engine_quality=engine_quality,
            deduplication_quality=dedup_quality,
            completeness_assessment=metrics.completeness_score,
            reasoning=reasoning,
            recommendation=recommendation,
        )
        
        self.feedback_events.append(event)
        return event
    
    def generate_learning_signals(
        self,
        feedback_event: ResearchFeedbackEvent,
        metrics: ResearchMetrics
    ) -> List[ResearchLearningSignal]:
        """
        Generate learning signals from feedback event.
        
        Args:
            feedback_event: Assessment of outcome
            metrics: Research metrics
            
        Returns:
            List of learning signals for different components
        """
        signals = []
        
        # Signal 1: Engine effectiveness
        for engine, quality in feedback_event.engine_quality.items():
            signal = ResearchLearningSignal(
                signal_id=f"sig_eng_{metrics.session_id[:8]}_{engine}",
                signal_type="engine_effectiveness",
                target_component="engine_selection",
                task_type=metrics.task_type,
                confidence=quality,
                recommendation=f"Engine '{engine}' effectiveness: {quality:.2f}" + 
                              (f" - boost priority" if quality > 0.8 else " - consider alternatives"),
                supporting_evidence={
                    "engine": engine,
                    "data_points_found": metrics.engine_contributions.get(engine, 0),
                    "avg_confidence": metrics.avg_confidence,
                    "task_type": metrics.task_type,
                },
                research_session_id=metrics.session_id,
            )
            signals.append(signal)
        
        # Signal 2: Task decomposition effectiveness
        if feedback_event.outcome == ResearchOutcomeType.ENTITY_FOUND:
            signal = ResearchLearningSignal(
                signal_id=f"sig_task_{metrics.session_id[:8]}",
                signal_type="task_decomposition_effectiveness",
                target_component="task_decomposition",
                task_type=metrics.task_type,
                confidence=0.9,
                recommendation=f"Task decomposition for {metrics.task_type} was effective. Maintain current strategy.",
                supporting_evidence={
                    "entities_found": metrics.entities_found,
                    "completeness": metrics.completeness_score,
                    "sources_used": metrics.sources_used,
                },
                research_session_id=metrics.session_id,
            )
            signals.append(signal)
        else:
            signal = ResearchLearningSignal(
                signal_id=f"sig_task_{metrics.session_id[:8]}",
                signal_type="task_decomposition_effectiveness",
                target_component="task_decomposition",
                task_type=metrics.task_type,
                confidence=0.3,
                recommendation=f"Task decomposition for {metrics.task_type} needs refinement. "
                              f"Consider adding steps or reordering dependencies.",
                supporting_evidence={
                    "entities_found": metrics.entities_found,
                    "completeness": metrics.completeness_score,
                    "outcome": feedback_event.outcome.value,
                },
                research_session_id=metrics.session_id,
            )
            signals.append(signal)
        
        # Signal 3: Deduplication effectiveness
        if feedback_event.deduplication_quality > 0.7:
            signal = ResearchLearningSignal(
                signal_id=f"sig_dedup_{metrics.session_id[:8]}",
                signal_type="deduplication_quality",
                target_component="deduplication",
                task_type=metrics.task_type,
                confidence=feedback_event.deduplication_quality,
                recommendation="Deduplication performing well. Multi-source normalization effective.",
                supporting_evidence={
                    "sources_used": len(metrics.sources_used),
                    "dedup_quality": feedback_event.deduplication_quality,
                    "total_deduplicated": metrics.deduplicated_count,
                },
                research_session_id=metrics.session_id,
            )
            signals.append(signal)
        
        # Signal 4: Completeness heuristics
        signal = ResearchLearningSignal(
            signal_id=f"sig_comp_{metrics.session_id[:8]}",
            signal_type="completeness_assessment",
            target_component="completeness",
            task_type=metrics.task_type,
            confidence=feedback_event.completeness_assessment,
            recommendation=f"Research completeness: {feedback_event.completeness_assessment:.1%}. " +
                          ("Research goal met." if feedback_event.completeness_assessment >= 0.8 
                           else "Additional research may be needed."),
            supporting_evidence={
                "completeness_score": metrics.completeness_score,
                "avg_confidence": metrics.avg_confidence,
                "entities_found": metrics.entities_found,
            },
            research_session_id=metrics.session_id,
        )
        signals.append(signal)
        
        self.learning_signals.extend(signals)
        logger.info(f"[RESEARCH_SIGNALS] Generated {len(signals)} learning signals for {metrics.session_id}")
        
        return signals
    
    def write_learning_signals(self) -> str:
        """
        Write learning signals to Firebase memory only (no local file).
        
        Returns:
            Firebase collection path (for logging)
        """
        # Persist to Firebase-backed memory only
        try:
            index_key = "research_learning_signal_index"
            existing_index = memory.safe_call("get", index_key) or []
            for signal in self.learning_signals:
                payload = signal.to_dict()
                signal_key = f"research_signal:{payload['signal_id']}"
                memory.safe_call("set", signal_key, payload)
                existing_index.append(payload["signal_id"])
            # Keep index bounded
            if len(existing_index) > 500:
                existing_index = existing_index[-500:]
            memory.safe_call("set", index_key, existing_index)
            
            logger.info(f"[RESEARCH_SIGNALS] Wrote {len(self.learning_signals)} signals to Firebase memory")
            return "firebase:agent_memory:research_signals"
        except Exception as e:
            logger.error(f"[RESEARCH_SIGNALS] Firebase memory write failed: {e}")
            return ""
    
    def get_engine_rankings(self) -> Dict[str, float]:
        """
        Calculate engine effectiveness rankings from signals.
        
        Returns:
            Dict of engine -> average effectiveness score
        """
        engine_scores = {}
        engine_counts = {}
        
        for signal in self.learning_signals:
            if signal.signal_type == "engine_effectiveness":
                engine = signal.supporting_evidence.get("engine", "unknown")
                score = signal.confidence
                
                if engine not in engine_scores:
                    engine_scores[engine] = 0.0
                    engine_counts[engine] = 0
                
                engine_scores[engine] += score
                engine_counts[engine] += 1
        
        # Calculate averages
        rankings = {
            engine: engine_scores[engine] / engine_counts[engine]
            for engine in engine_scores
        }
        
        return rankings
    
    def get_task_type_insights(self, task_type: str) -> Dict[str, Any]:
        """
        Get insights about how we perform on a specific task type.
        
        Args:
            task_type: e.g., CONTACT_EXTRACTION, COMPANY_RESEARCH
            
        Returns:
            Dict with performance insights
        """
        relevant_metrics = [m for m in self.metrics_history if m.task_type == task_type]
        
        if not relevant_metrics:
            return {"task_type": task_type, "insights": "No data yet"}
        
        success_rate = sum(1 for m in relevant_metrics if m.success) / len(relevant_metrics)
        avg_completeness = sum(m.completeness_score for m in relevant_metrics) / len(relevant_metrics)
        avg_confidence = sum(m.avg_confidence for m in relevant_metrics) / len(relevant_metrics)
        
        # Best performing engines for this task
        engine_performance = {}
        for m in relevant_metrics:
            for engine, count in m.engine_contributions.items():
                if engine not in engine_performance:
                    engine_performance[engine] = []
                engine_performance[engine].append(m.avg_confidence)
        
        best_engines = {
            engine: sum(scores) / len(scores)
            for engine, scores in engine_performance.items()
        }
        
        return {
            "task_type": task_type,
            "sessions": len(relevant_metrics),
            "success_rate": success_rate,
            "avg_completeness": avg_completeness,
            "avg_confidence": avg_confidence,
            "best_engines": best_engines,
        }
    
    def process_research_session(
        self,
        session_output: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Complete feedback loop for a research session.
        
        Args:
            session_output: Output from ResearchIntelligenceEngine.research()
            
        Returns:
            Dict with feedback results
        """
        # Step 1: Evaluate
        metrics = self.evaluate_research_session(session_output)
        
        # Step 2: Assess
        feedback_event = self.assess_outcome(metrics)
        
        # Step 3: Generate signals
        signals = self.generate_learning_signals(feedback_event, metrics)
        
        # Step 4: Write signals
        signals_file = self.write_learning_signals()
        
        return {
            "session_id": metrics.session_id,
            "metrics": {
                "entities_found": metrics.entities_found,
                "avg_confidence": metrics.avg_confidence,
                "completeness_score": metrics.completeness_score,
                "sources_used": metrics.sources_used,
            },
            "feedback": {
                "outcome": feedback_event.outcome.value,
                "confidence": feedback_event.confidence,
                "recommendation": feedback_event.recommendation,
            },
            "signals_generated": len(signals),
            "signals_file": signals_file,
        }


# Global instance
research_feedback_loop = ResearchFeedbackLoop()

