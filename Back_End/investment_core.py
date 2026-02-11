"""
Phase 10: Investment Core

Evaluates whether builds, missions, opportunities, or learning efforts are worth investing in.

Hard constraints:
- NO autonomy (advisory only)
- NO execution side effects
- NO real trading/purchasing/financial actions
- NO LLM usage
- NO retries, loops, or optimization logic
- NO behavior changes to existing systems
- Pure evaluation (deterministic, read-only, auditable)

Investment types:
  MISSION: Time investment in a mission
  BUILD: Building a new system/tool/capability
  OPPORTUNITY: One-off opportunity with specific ROI
  LEARNING: Skill/knowledge investment
  ASSET: Capital/resource investment

Investment ≠ money only. Includes:
  - Time (hours)
  - Attention (normalized 0-1)
  - Cognitive load (normalized 0-1)
  - Capital (currency units)
  - Opportunity cost (what else could be done)
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
import math


class CandidateType(Enum):
    """Types of investment candidates."""
    MISSION = "mission"
    BUILD = "build"
    OPPORTUNITY = "opportunity"
    LEARNING = "learning"
    ASSET = "asset"


class RiskBand(Enum):
    """Risk classification."""
    LOW = "low"              # < 0.2 uncertainty
    MEDIUM = "medium"        # 0.2-0.5 uncertainty
    HIGH = "high"            # 0.5-0.8 uncertainty
    EXTREME = "extreme"      # > 0.8 uncertainty


class InvestmentRecommendation(Enum):
    """Investment recommendation."""
    STRONG_BUY = "strong_buy"           # Score >= 0.80
    BUY = "buy"                         # Score >= 0.60
    HOLD = "hold"                       # Score >= 0.40
    SELL = "sell"                       # Score < 0.40
    HIGH_RISK = "high_risk"             # High uncertainty/downside
    POOR_TIMING = "poor_timing"         # Good opportunity, bad timing


@dataclass(frozen=True)
class InvestmentCost:
    """Immutable investment cost breakdown."""
    time_hours: float = 0.0             # Hours to complete
    capital: float = 0.0                # Currency units
    effort: float = 0.0                 # Normalized 0-1 (cognitive/physical)
    attention_days: int = 0             # Days of attention required
    
    def total_normalized_cost(self) -> float:
        """
        Compute normalized total cost (0.0-1.0).
        
        Components:
          - Time: hours / 1000 (5 years)
          - Capital: normalized to effort scale
          - Effort: direct 0-1
          - Attention: days / 365
        """
        time_score = min(1.0, self.time_hours / 1000.0)
        capital_score = min(1.0, self.capital / 100000.0) if self.capital > 0 else 0.0
        attention_score = min(1.0, self.attention_days / 365.0)
        
        # Average: 1/3 from time, 1/3 from effort, 1/3 from capital + attention
        costs = [time_score, self.effort, (capital_score + attention_score) / 2]
        return sum(costs) / len(costs)


@dataclass(frozen=True)
class InvestmentReturn:
    """Immutable expected return specification."""
    value: float = 0.0                  # Abstract value units (0-1 normalized)
    confidence: float = 0.5             # Confidence in return (0-1)
    time_horizon_days: int = 30         # Days until return realized
    
    def is_short_term(self) -> bool:
        """Return realized in < 30 days."""
        return self.time_horizon_days < 30
    
    def is_long_term(self) -> bool:
        """Return realized in > 365 days."""
        return self.time_horizon_days > 365


@dataclass(frozen=True)
class InvestmentRisk:
    """Immutable risk specification."""
    uncertainty: float = 0.0            # 0-1 uncertainty about outcome
    downside: float = 0.0               # 0-1 maximum downside
    
    def risk_band(self) -> RiskBand:
        """Classify risk into bands."""
        if self.uncertainty < 0.2:
            return RiskBand.LOW
        elif self.uncertainty < 0.5:
            return RiskBand.MEDIUM
        elif self.uncertainty < 0.8:
            return RiskBand.HIGH
        else:
            return RiskBand.EXTREME
    
    def is_acceptable(self, risk_tolerance: float = 0.5) -> bool:
        """Is risk acceptable given tolerance (0-1)?"""
        return self.uncertainty <= risk_tolerance


@dataclass(frozen=True)
class InvestmentCandidate:
    """
    Immutable investment candidate specification.
    
    Represents a potential investment in time, attention, capital, or effort.
    """
    candidate_id: str
    candidate_type: CandidateType
    description: str
    estimated_cost: InvestmentCost
    expected_return: InvestmentReturn
    risk: InvestmentRisk
    reusability: float = 0.0            # 0-1 compounding benefit
    mission_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """Validate ranges."""
        assert 0.0 <= self.reusability <= 1.0, "reusability must be 0.0-1.0"
        assert 0.0 <= self.expected_return.value <= 1.0, "return value must be 0.0-1.0"
        assert 0.0 <= self.expected_return.confidence <= 1.0, "confidence must be 0.0-1.0"
        assert 0.0 <= self.risk.uncertainty <= 1.0, "uncertainty must be 0.0-1.0"
        assert 0.0 <= self.risk.downside <= 1.0, "downside must be 0.0-1.0"


@dataclass(frozen=True)
class InvestmentScore:
    """Immutable investment evaluation result."""
    candidate_id: str
    candidate_type: CandidateType
    investment_score: float             # 0.0-1.0
    expected_return: float              # 0.0-1.0
    estimated_cost: float               # 0.0-1.0 normalized
    risk_adjusted: float                # Risk multiplier applied
    risk_band: RiskBand
    recommendation: InvestmentRecommendation
    reasoning: List[str] = field(default_factory=list)
    confidence: float = 0.0             # 0.0-1.0 confidence in score
    time_horizon_impact: str = ""       # short/medium/long term
    reusability_multiplier: float = 1.0 # Compounding benefit applied
    
    def is_recommended(self) -> bool:
        """Is this investment recommended (BUY or STRONG_BUY)?"""
        return self.recommendation in [
            InvestmentRecommendation.BUY,
            InvestmentRecommendation.STRONG_BUY
        ]


class InvestmentScoringRubric:
    """Deterministic investment scoring model."""
    
    # Fixed scoring constants
    CONFIDENCE_WEIGHT = 0.4
    REUSABILITY_WEIGHT = 0.6
    RISK_PENALTY_BASE = 0.5
    SHORT_TERM_BONUS = 1.1      # 10% bonus for quick returns
    LONG_TERM_MULTIPLIER = 1.2  # 20% multiplier for strategic long-term
    
    @staticmethod
    def calculate_investment_score(candidate: InvestmentCandidate) -> InvestmentScore:
        """
        Calculate deterministic investment score.
        
        Formula:
          base_score = (value × confidence × reusability_mult) / cost_normalized
          risk_adjustment = 1.0 - (uncertainty × 0.5)  # Uncertainty penalty
          final_score = base_score × risk_adjustment × time_horizon_bonus
          
        Normalize to 0.0-1.0.
        """
        # Calculate base return score
        return_value = candidate.expected_return.value
        confidence = candidate.expected_return.confidence
        reusability_mult = 1.0 + (candidate.reusability * InvestmentScoringRubric.REUSABILITY_WEIGHT)
        
        base_return = return_value * confidence * reusability_mult
        
        # Normalize cost
        cost_normalized = candidate.estimated_cost.total_normalized_cost()
        if cost_normalized == 0:
            cost_normalized = 0.01  # Prevent division by zero
        
        # Calculate raw score
        raw_score = base_return / cost_normalized
        
        # Apply risk adjustment
        uncertainty_penalty = candidate.risk.uncertainty * 0.5
        downside_penalty = candidate.risk.downside * 0.3
        risk_adjustment = 1.0 - (uncertainty_penalty + downside_penalty)
        risk_adjustment = max(0.1, risk_adjustment)  # Floor at 0.1
        
        # Apply time horizon adjustment
        time_horizon_bonus = InvestmentScoringRubric._get_time_horizon_bonus(
            candidate.expected_return.time_horizon_days
        )
        
        # Calculate final score
        final_score = raw_score * risk_adjustment * time_horizon_bonus
        
        # Normalize to 0.0-1.0
        final_score = min(1.0, final_score / 2.0)  # Divide by 2 to normalize typical scores
        final_score = max(0.0, final_score)
        
        # Determine recommendation
        recommendation = InvestmentScoringRubric._get_recommendation(
            final_score, candidate.risk
        )
        
        # Generate reasoning
        reasoning = InvestmentScoringRubric._generate_reasoning(
            candidate, final_score, risk_adjustment
        )
        
        # Calculate confidence in score
        score_confidence = confidence * (1.0 - candidate.risk.uncertainty)
        
        # Determine time horizon impact
        time_horizon_impact = InvestmentScoringRubric._classify_time_horizon(
            candidate.expected_return.time_horizon_days
        )
        
        return InvestmentScore(
            candidate_id=candidate.candidate_id,
            candidate_type=candidate.candidate_type,
            investment_score=final_score,
            expected_return=base_return,
            estimated_cost=cost_normalized,
            risk_adjusted=risk_adjustment,
            risk_band=candidate.risk.risk_band(),
            recommendation=recommendation,
            reasoning=reasoning,
            confidence=score_confidence,
            time_horizon_impact=time_horizon_impact,
            reusability_multiplier=reusability_mult
        )
    
    @staticmethod
    def _get_time_horizon_bonus(days: int) -> float:
        """Get time horizon multiplier."""
        if days < 30:
            return InvestmentScoringRubric.SHORT_TERM_BONUS
        elif days > 365:
            return InvestmentScoringRubric.LONG_TERM_MULTIPLIER
        else:
            return 1.0
    
    @staticmethod
    def _get_recommendation(score: float, risk: InvestmentRisk) -> InvestmentRecommendation:
        """Determine recommendation from score and risk."""
        # Risk override
        if risk.uncertainty > 0.8 or risk.downside > 0.8:
            return InvestmentRecommendation.HIGH_RISK
        
        # Score-based recommendation
        if score >= 0.80:
            return InvestmentRecommendation.STRONG_BUY
        elif score >= 0.60:
            return InvestmentRecommendation.BUY
        elif score >= 0.40:
            return InvestmentRecommendation.HOLD
        else:
            return InvestmentRecommendation.SELL
    
    @staticmethod
    def _generate_reasoning(
        candidate: InvestmentCandidate,
        score: float,
        risk_adjustment: float
    ) -> List[str]:
        """Generate reasoning for the score."""
        reasons = []
        
        # Return assessment
        if candidate.expected_return.value >= 0.8:
            reasons.append(f"High expected return ({candidate.expected_return.value:.1%})")
        elif candidate.expected_return.value >= 0.5:
            reasons.append(f"Moderate return ({candidate.expected_return.value:.1%})")
        else:
            reasons.append(f"Low return ({candidate.expected_return.value:.1%})")
        
        # Cost assessment
        cost = candidate.estimated_cost.total_normalized_cost()
        if cost < 0.3:
            reasons.append("Low cost / effort required")
        elif cost > 0.7:
            reasons.append("Significant investment required")
        
        # Confidence
        if candidate.expected_return.confidence >= 0.8:
            reasons.append("High confidence in outcome")
        elif candidate.expected_return.confidence < 0.5:
            reasons.append("Low confidence - uncertain outcome")
        
        # Risk
        if candidate.risk.uncertainty >= 0.7:
            reasons.append("High uncertainty - risky investment")
        elif candidate.risk.uncertainty < 0.2:
            reasons.append("Low risk - predictable")
        
        # Reusability
        if candidate.reusability >= 0.7:
            reasons.append("High reusability - long-term value")
        
        # Time horizon
        if candidate.expected_return.time_horizon_days < 30:
            reasons.append("Quick return (< 30 days)")
        elif candidate.expected_return.time_horizon_days > 365:
            reasons.append("Strategic long-term investment")
        
        # Score interpretation
        if risk_adjustment < 0.5:
            reasons.append("Downside risk is significant concern")
        
        return reasons
    
    @staticmethod
    def _classify_time_horizon(days: int) -> str:
        """Classify time horizon."""
        if days < 30:
            return "short_term"
        elif days < 180:
            return "medium_term"
        else:
            return "long_term"


class InvestmentCore:
    """
    Deterministic investment evaluation engine.
    
    Pure evaluation, no side effects, no autonomy.
    """
    
    def __init__(self):
        """Initialize investment core."""
        self._candidates: Dict[str, InvestmentCandidate] = {}
        self._scores: Dict[str, InvestmentScore] = {}
        self._evaluation_history: List[Tuple[str, InvestmentScore]] = []
    
    def add_candidate(
        self,
        candidate_id: str,
        candidate_type: CandidateType,
        description: str,
        estimated_cost: InvestmentCost,
        expected_return: InvestmentReturn,
        risk: InvestmentRisk,
        reusability: float = 0.0,
        mission_id: Optional[str] = None
    ) -> InvestmentCandidate:
        """Add a new investment candidate."""
        candidate = InvestmentCandidate(
            candidate_id=candidate_id,
            candidate_type=candidate_type,
            description=description,
            estimated_cost=estimated_cost,
            expected_return=expected_return,
            risk=risk,
            reusability=reusability,
            mission_id=mission_id
        )
        self._candidates[candidate_id] = candidate
        return candidate
    
    def evaluate_candidate(self, candidate_id: str) -> Optional[InvestmentScore]:
        """Evaluate a single candidate."""
        candidate = self._candidates.get(candidate_id)
        if candidate is None:
            return None
        
        score = InvestmentScoringRubric.calculate_investment_score(candidate)
        self._scores[candidate_id] = score
        self._evaluation_history.append((candidate_id, score))
        return score
    
    def evaluate_all(self) -> List[InvestmentScore]:
        """Evaluate all candidates."""
        scores = []
        for candidate_id in self._candidates.keys():
            score = self.evaluate_candidate(candidate_id)
            if score:
                scores.append(score)
        return scores
    
    def rank_candidates(self) -> List[InvestmentScore]:
        """
        Rank candidates by investment score (descending).
        
        Returns list sorted highest score first.
        """
        # Evaluate all candidates
        all_scores = self.evaluate_all()
        
        # Sort by score descending
        ranked = sorted(all_scores, key=lambda s: s.investment_score, reverse=True)
        return ranked
    
    def get_recommended_investments(self) -> List[InvestmentScore]:
        """Get all recommended investments (BUY or STRONG_BUY)."""
        all_scores = self.rank_candidates()
        return [s for s in all_scores if s.is_recommended()]
    
    def get_score(self, candidate_id: str) -> Optional[InvestmentScore]:
        """Get score for candidate (cached)."""
        return self._scores.get(candidate_id)
    
    def compare_investments(self, candidate_ids: List[str]) -> Tuple[List[InvestmentScore], str]:
        """
        Compare multiple investments.
        
        Returns:
            (ranked scores, summary analysis)
        """
        scores = []
        for cid in candidate_ids:
            score = self.evaluate_candidate(cid)
            if score:
                scores.append(score)
        
        # Sort by score
        ranked = sorted(scores, key=lambda s: s.investment_score, reverse=True)
        
        # Generate summary
        if not ranked:
            return [], "No candidates to compare"
        
        top = ranked[0]
        summary = (
            f"Top pick: {top.candidate_id} (score {top.investment_score:.2f}). "
            f"Recommendation: {top.recommendation.value}. "
            f"Risk: {top.risk_band.value}."
        )
        
        return ranked, summary
    
    def get_portfolio_analysis(self) -> Dict[str, Any]:
        """Analyze full investment portfolio."""
        all_scores = self.rank_candidates()
        
        if not all_scores:
            return {"total": 0, "recommended": 0, "high_risk": 0}
        
        recommended = [s for s in all_scores if s.is_recommended()]
        high_risk = [s for s in all_scores if s.risk_band in [RiskBand.HIGH, RiskBand.EXTREME]]
        
        avg_score = sum(s.investment_score for s in all_scores) / len(all_scores)
        
        return {
            "total_candidates": len(all_scores),
            "recommended": len(recommended),
            "high_risk": len(high_risk),
            "average_score": avg_score,
            "top_investment": all_scores[0] if all_scores else None,
            "candidates_by_type": self._analyze_by_type(all_scores),
            "candidates_by_time_horizon": self._analyze_by_time_horizon(all_scores)
        }
    
    @staticmethod
    def _analyze_by_type(scores: List[InvestmentScore]) -> Dict[str, int]:
        """Count candidates by type."""
        counts = {}
        for score in scores:
            type_name = score.candidate_type.value
            counts[type_name] = counts.get(type_name, 0) + 1
        return counts
    
    @staticmethod
    def _analyze_by_time_horizon(scores: List[InvestmentScore]) -> Dict[str, int]:
        """Count candidates by time horizon."""
        counts = {}
        for score in scores:
            horizon = score.time_horizon_impact
            counts[horizon] = counts.get(horizon, 0) + 1
        return counts
    
    def get_candidate_count(self) -> int:
        """Total number of candidates."""
        return len(self._candidates)
    
    def get_evaluation_count(self) -> int:
        """Total evaluations performed."""
        return len(self._evaluation_history)

