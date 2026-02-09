"""
Phase 10: Investment Whiteboard Panel

Visualizes investment evaluation results and rankings.

Display elements:
  - Investment candidates ranked by score
  - Cost vs return visualization
  - Risk bands (low / medium / high)
  - Recommended investments highlighted
  - Time horizon categorization
  - Portfolio composition

Hard constraints:
- NO autonomy (display only)
- NO execution instructions
- READ-ONLY visualization
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime

from backend.investment_core import (
    InvestmentCore, InvestmentScore, InvestmentCandidate, 
    CandidateType, RiskBand, InvestmentRecommendation
)


@dataclass
class InvestmentWhiteboardDisplay:
    """Immutable investment view."""
    total_candidates: int
    ranked_scores: List[InvestmentScore]
    recommended: List[InvestmentScore]
    high_risk: List[InvestmentScore]
    portfolio_analysis: Dict[str, Any]


class InvestmentWhiteboardPanel:
    """Renders investment evaluation to whiteboard display."""
    
    def __init__(self):
        """Initialize panel."""
        self._core: Optional[InvestmentCore] = None
        self._ranked_scores: List[InvestmentScore] = []
        self._last_updated: datetime = datetime.utcnow()
    
    def set_investment_core(self, core: InvestmentCore) -> None:
        """Set or update investment core."""
        self._core = core
        self._ranked_scores = core.rank_candidates()
        self._last_updated = datetime.utcnow()
    
    def render(self, max_items: int = 10) -> str:
        """Render full investment whiteboard."""
        if self._core is None or not self._ranked_scores:
            return "No investment data available"
        
        lines = []
        lines.append("=" * 90)
        lines.append("INVESTMENT EVALUATION WHITEBOARD".center(90))
        lines.append("=" * 90)
        lines.append("")
        
        # Portfolio summary
        lines.extend(self._render_portfolio_summary())
        lines.append("")
        
        # Top investments
        lines.extend(self._render_top_investments(max_items))
        lines.append("")
        
        # Risk analysis
        lines.extend(self._render_risk_analysis())
        lines.append("")
        
        # Time horizon breakdown
        lines.extend(self._render_time_horizon())
        lines.append("")
        
        # Recommendations
        lines.extend(self._render_recommendations())
        lines.append("")
        
        lines.append("=" * 90)
        timestamp = self._last_updated.strftime("%Y-%m-%d %H:%M:%S UTC")
        lines.append(f"Updated: {timestamp}".rjust(90))
        
        return "\n".join(lines)
    
    def _render_portfolio_summary(self) -> List[str]:
        """Render portfolio summary section."""
        if self._core is None:
            return []
        
        analysis = self._core.get_portfolio_analysis()
        
        lines = [
            "[PORTFOLIO] Investment Summary",
            f"  Total Candidates: {analysis.get('total_candidates', 0)}",
            f"  Recommended: {analysis.get('recommended', 0)}",
            f"  High Risk: {analysis.get('high_risk', 0)}",
            f"  Average Score: {analysis.get('average_score', 0.0):.2f}",
        ]
        
        # Type breakdown
        types = analysis.get('candidates_by_type', {})
        if types:
            type_str = ", ".join([f"{t}({c})" for t, c in types.items()])
            lines.append(f"  By Type: {type_str}")
        
        return lines
    
    def _render_top_investments(self, max_items: int = 10) -> List[str]:
        """Render top ranked investments."""
        lines = ["[TOP INVESTMENTS] Ranked by Score"]
        
        for i, score in enumerate(self._ranked_scores[:max_items], 1):
            icon = self._get_recommendation_icon(score.recommendation)
            score_bar = self._get_score_bar(score.investment_score)
            
            lines.append(
                f"  #{i} {icon} {score.candidate_id[:30]:<30} "
                f"Score: {score_bar} {score.investment_score:.2f}"
            )
            
            # Second line with details
            risk_icon = self._get_risk_icon(score.risk_band)
            details = (
                f"      {risk_icon} {score.risk_band.value.upper():<7} | "
                f"Return: {score.expected_return:.2f} | "
                f"Cost: {score.estimated_cost:.2f} | "
                f"Horizon: {score.time_horizon_impact}"
            )
            lines.append(details)
        
        if len(self._ranked_scores) > max_items:
            remaining = len(self._ranked_scores) - max_items
            lines.append(f"  ... and {remaining} more candidates")
        
        return lines
    
    def _render_risk_analysis(self) -> List[str]:
        """Render risk distribution."""
        lines = ["[RISK ANALYSIS]"]
        
        if not self._ranked_scores:
            return lines + ["  No data"]
        
        # Count by risk band
        risk_counts = {band.value: 0 for band in RiskBand}
        for score in self._ranked_scores:
            risk_counts[score.risk_band.value] += 1
        
        total = len(self._ranked_scores)
        
        for band in [RiskBand.LOW, RiskBand.MEDIUM, RiskBand.HIGH, RiskBand.EXTREME]:
            count = risk_counts[band.value]
            pct = (count / total) * 100 if total > 0 else 0
            bar = self._get_bar(pct, 30)
            lines.append(f"  {band.value.upper():<8}: [{bar}] {count}/{total} ({pct:.0f}%)")
        
        return lines
    
    def _render_time_horizon(self) -> List[str]:
        """Render time horizon breakdown."""
        lines = ["[TIME HORIZON] Investment Duration"]
        
        if not self._ranked_scores:
            return lines + ["  No data"]
        
        # Count by horizon
        horizons = {'short_term': 0, 'medium_term': 0, 'long_term': 0}
        for score in self._ranked_scores:
            horizon = score.time_horizon_impact
            if horizon in horizons:
                horizons[horizon] += 1
        
        total = len(self._ranked_scores)
        
        for horizon, label in [
            ('short_term', 'Quick (< 30 days)'),
            ('medium_term', 'Medium (30-365 days)'),
            ('long_term', 'Long-term (> 1 year)')
        ]:
            count = horizons.get(horizon, 0)
            pct = (count / total) * 100 if total > 0 else 0
            lines.append(f"  {label:<20}: {count:>3} ({pct:>5.1f}%)")
        
        return lines
    
    def _render_recommendations(self) -> List[str]:
        """Render recommendation summary."""
        lines = ["[RECOMMENDATIONS] Investment Guidance"]
        
        recommended = [s for s in self._ranked_scores if s.is_recommended()]
        
        if not recommended:
            lines.append("  No recommended investments at this time")
            return lines
        
        lines.append(f"  {len(recommended)} investments recommended:")
        lines.append("")
        
        for score in recommended[:3]:
            candidate_id = score.candidate_id[:40]
            rec_text = {
                InvestmentRecommendation.STRONG_BUY: "STRONGLY BUY",
                InvestmentRecommendation.BUY: "BUY",
                InvestmentRecommendation.HOLD: "HOLD",
            }.get(score.recommendation, score.recommendation.value)
            
            lines.append(f"  → {candidate_id}")
            lines.append(f"    Recommendation: {rec_text}")
            lines.append(f"    Score: {score.investment_score:.2f} | Confidence: {score.confidence:.0%}")
            lines.append("")
        
        if len(recommended) > 3:
            lines.append(f"  ... and {len(recommended) - 3} more")
        
        return lines
    
    def render_quick_summary(self) -> str:
        """Render one-line summary."""
        if self._core is None or not self._ranked_scores:
            return "No investment data"
        
        analysis = self._core.get_portfolio_analysis()
        total = analysis.get('total_candidates', 0)
        recommended = analysis.get('recommended', 0)
        high_risk = analysis.get('high_risk', 0)
        avg_score = analysis.get('average_score', 0.0)
        
        return (
            f"[INVESTMENTS] "
            f"Total: {total} | Recommended: {recommended} | "
            f"High Risk: {high_risk} | Avg Score: {avg_score:.2f}"
        )
    
    def render_cost_return_matrix(self) -> str:
        """Render cost vs return visualization (2D matrix)."""
        if not self._ranked_scores:
            return "No data to display"
        
        lines = []
        lines.append("COST vs RETURN MATRIX".center(60))
        lines.append("=" * 60)
        lines.append("")
        
        # Create 4-quadrant matrix
        # High Return / Low Cost = BEST
        # High Return / High Cost = GOOD
        # Low Return / Low Cost = OKAY
        # Low Return / High Cost = WORST
        
        quadrants = {
            'best': [],      # high return, low cost
            'good': [],      # high return, high cost
            'okay': [],      # low return, low cost
            'worst': []      # low return, high cost
        }
        
        for score in self._ranked_scores:
            high_return = score.expected_return > 0.5
            low_cost = score.estimated_cost < 0.5
            
            if high_return and low_cost:
                quadrants['best'].append(score)
            elif high_return and not low_cost:
                quadrants['good'].append(score)
            elif not high_return and low_cost:
                quadrants['okay'].append(score)
            else:
                quadrants['worst'].append(score)
        
        # Render quadrants
        lines.append("HIGH RETURN, LOW COST (BEST)          HIGH RETURN, HIGH COST (GOOD)")
        for score in quadrants['best'][:2]:
            lines.append(f"  {score.candidate_id[:35]:<35}")
        lines.append("")
        
        lines.append("LOW RETURN, LOW COST (OKAY)           LOW RETURN, HIGH COST (WORST)")
        for score in quadrants['okay'][:2]:
            lines.append(f"  {score.candidate_id[:35]:<35}")
        
        return "\n".join(lines)
    
    def render_comparative_analysis(self, candidate_ids: List[str]) -> str:
        """Render comparison of specific candidates."""
        if self._core is None:
            return "No data"
        
        scores = []
        for cid in candidate_ids:
            score = self._core.get_score(cid)
            if score:
                scores.append(score)
        
        if not scores:
            return "No scores found for specified candidates"
        
        lines = ["COMPARATIVE ANALYSIS".center(70)]
        lines.append("=" * 70)
        lines.append("")
        
        # Header
        lines.append(
            f"{'Candidate':<25} {'Score':<8} {'Return':<8} {'Cost':<8} "
            f"{'Risk':<8} {'Rec':<12}"
        )
        lines.append("-" * 70)
        
        # Rows
        for score in sorted(scores, key=lambda s: s.investment_score, reverse=True):
            cid = score.candidate_id[:22]
            rec = score.recommendation.value[:10]
            
            lines.append(
                f"{cid:<25} {score.investment_score:<8.2f} "
                f"{score.expected_return:<8.2f} {score.estimated_cost:<8.2f} "
                f"{score.risk_adjusted:<8.2f} {rec:<12}"
            )
        
        return "\n".join(lines)
    
    @staticmethod
    def _get_recommendation_icon(rec: InvestmentRecommendation) -> str:
        """Get icon for recommendation."""
        icons = {
            InvestmentRecommendation.STRONG_BUY: "[GO++]",
            InvestmentRecommendation.BUY: "[GO+]",
            InvestmentRecommendation.HOLD: "[WAIT]",
            InvestmentRecommendation.SELL: "[SKIP]",
            InvestmentRecommendation.HIGH_RISK: "[RISK]",
            InvestmentRecommendation.POOR_TIMING: "[DEFER]",
        }
        return icons.get(rec, "[?]")
    
    @staticmethod
    def _get_risk_icon(risk: RiskBand) -> str:
        """Get icon for risk level."""
        icons = {
            RiskBand.LOW: ".",
            RiskBand.MEDIUM: ":",
            RiskBand.HIGH: "!",
            RiskBand.EXTREME: "!!",
        }
        return icons.get(risk, "?")
    
    @staticmethod
    def _get_score_bar(score: float, width: int = 10) -> str:
        """Get visual bar for score."""
        filled = int(score * width)
        bar = "█" * filled + "░" * (width - filled)
        return f"[{bar}]"
    
    @staticmethod
    def _get_bar(percentage: float, width: int = 20) -> str:
        """Get visual bar for percentage."""
        filled = int((percentage / 100.0) * width)
        return "█" * filled + "░" * (width - filled)


class InvestmentPanelManager:
    """Manages investment panels for multiple portfolios."""
    
    def __init__(self):
        """Initialize panel manager."""
        self._panels: Dict[str, InvestmentWhiteboardPanel] = {}
        self._cores: Dict[str, InvestmentCore] = {}
    
    def register_portfolio(self, portfolio_id: str, core: InvestmentCore) -> None:
        """Register investment portfolio."""
        panel = InvestmentWhiteboardPanel()
        panel.set_investment_core(core)
        
        self._panels[portfolio_id] = panel
        self._cores[portfolio_id] = core
    
    def render_portfolio(self, portfolio_id: str) -> str:
        """Render portfolio whiteboard."""
        panel = self._panels.get(portfolio_id)
        if panel is None:
            return f"Portfolio {portfolio_id} not registered"
        return panel.render()
    
    def get_portfolio_summary(self, portfolio_id: str) -> str:
        """Get portfolio quick summary."""
        panel = self._panels.get(portfolio_id)
        if panel is None:
            return f"Portfolio {portfolio_id} not registered"
        return panel.render_quick_summary()
    
    def get_all_summaries(self) -> str:
        """Get all portfolio summaries."""
        lines = ["=== INVESTMENT PORTFOLIOS ===", ""]
        for pid, panel in self._panels.items():
            summary = panel.render_quick_summary()
            lines.append(f"{pid}: {summary}")
        return "\n".join(lines)
