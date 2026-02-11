"""
Phase 10: Investment Core Validation Tests

Comprehensive validation suite proving:
- Deterministic output
- Same input → same score
- Zero side effects
- Signals emitted correctly
- Whiteboard reads investment results
- Full constraint compliance
"""

import unittest
import tempfile
from pathlib import Path
from datetime import datetime

from Back_End.investment_core import (
    CandidateType, InvestmentCost, InvestmentReturn, InvestmentRisk,
    InvestmentCandidate, InvestmentScoringRubric, InvestmentCore,
    RiskBand, InvestmentRecommendation
)
from Back_End.investment_signal_emitter import (
    InvestmentSignalEmitter, InvestmentEvaluationSignal
)
from Back_End.investment_whiteboard_panel import (
    InvestmentWhiteboardPanel, InvestmentPanelManager
)


class TestInvestmentCostCalculation(unittest.TestCase):
    """Test cost calculation and normalization."""
    
    def test_zero_cost(self):
        """Zero cost should normalize to 0.0."""
        cost = InvestmentCost(time_hours=0, capital=0, effort=0, attention_days=0)
        normalized = cost.total_normalized_cost()
        self.assertEqual(normalized, 0.0)
    
    def test_time_normalization(self):
        """Test time component normalization."""
        cost = InvestmentCost(time_hours=500, capital=0, effort=0, attention_days=0)
        normalized = cost.total_normalized_cost()
        # 500/1000 = 0.5, averaged with 0, 0 = 0.167
        self.assertAlmostEqual(normalized, 0.167, places=2)
    
    def test_effort_component(self):
        """Test effort component in normalization."""
        cost = InvestmentCost(time_hours=0, capital=0, effort=0.6, attention_days=0)
        normalized = cost.total_normalized_cost()
        # Effort is 0.6, averaged = 0.2
        self.assertAlmostEqual(normalized, 0.2, places=2)
    
    def test_mixed_cost(self):
        """Test mixed cost components."""
        cost = InvestmentCost(time_hours=100, capital=50000, effort=0.5, attention_days=30)
        normalized = cost.total_normalized_cost()
        # Should be between 0 and 1
        self.assertGreater(normalized, 0.0)
        self.assertLessEqual(normalized, 1.0)


class TestInvestmentScoring(unittest.TestCase):
    """Test deterministic investment scoring."""
    
    def test_deterministic_scoring(self):
        """Same input always produces same score (determinism)."""
        candidate = InvestmentCandidate(
            candidate_id="test1",
            candidate_type=CandidateType.BUILD,
            description="Build forecasting engine",
            estimated_cost=InvestmentCost(time_hours=40, capital=0, effort=0.6),
            expected_return=InvestmentReturn(value=0.9, confidence=0.8, time_horizon_days=90),
            risk=InvestmentRisk(uncertainty=0.2, downside=0.1),
            reusability=0.8
        )
        
        # Score twice - should be identical
        score1 = InvestmentScoringRubric.calculate_investment_score(candidate)
        score2 = InvestmentScoringRubric.calculate_investment_score(candidate)
        
        self.assertEqual(score1.investment_score, score2.investment_score)
        self.assertEqual(score1.recommendation, score2.recommendation)
    
    def test_score_normalization(self):
        """Score is normalized to 0.0-1.0."""
        candidate = InvestmentCandidate(
            candidate_id="test2",
            candidate_type=CandidateType.MISSION,
            description="Quick task",
            estimated_cost=InvestmentCost(time_hours=10, capital=0, effort=0.3),
            expected_return=InvestmentReturn(value=0.95, confidence=0.95, time_horizon_days=7),
            risk=InvestmentRisk(uncertainty=0.05, downside=0.02),
            reusability=0.5
        )
        
        score = InvestmentScoringRubric.calculate_investment_score(candidate)
        
        self.assertGreaterEqual(score.investment_score, 0.0)
        self.assertLessEqual(score.investment_score, 1.0)
    
    def test_high_value_investment(self):
        """High value investment gets high score."""
        candidate = InvestmentCandidate(
            candidate_id="high_value",
            candidate_type=CandidateType.BUILD,
            description="AI forecasting system",
            estimated_cost=InvestmentCost(time_hours=80, capital=5000, effort=0.7),
            expected_return=InvestmentReturn(value=0.95, confidence=0.85, time_horizon_days=180),
            risk=InvestmentRisk(uncertainty=0.15, downside=0.1),
            reusability=0.9
        )
        
        score = InvestmentScoringRubric.calculate_investment_score(candidate)
        
        # High value with high confidence and reusability should score well
        self.assertGreater(score.investment_score, 0.5)
        self.assertIn(score.recommendation, [
            InvestmentRecommendation.STRONG_BUY,
            InvestmentRecommendation.BUY
        ])
    
    def test_low_value_investment(self):
        """Low value investment gets low score."""
        candidate = InvestmentCandidate(
            candidate_id="low_value",
            candidate_type=CandidateType.OPPORTUNITY,
            description="Minor optimization",
            estimated_cost=InvestmentCost(time_hours=50, capital=2000, effort=0.8),
            expected_return=InvestmentReturn(value=0.2, confidence=0.3, time_horizon_days=365),
            risk=InvestmentRisk(uncertainty=0.6, downside=0.4),
            reusability=0.1
        )
        
        score = InvestmentScoringRubric.calculate_investment_score(candidate)
        
        # Low value with low confidence should score poorly
        self.assertLess(score.investment_score, 0.5)
    
    def test_risk_adjustment_applied(self):
        """Risk adjustment is applied to score."""
        # Low risk, medium value
        candidate_low_risk = InvestmentCandidate(
            candidate_id="low_risk",
            candidate_type=CandidateType.MISSION,
            description="Task",
            estimated_cost=InvestmentCost(time_hours=50, capital=5000, effort=0.5),
            expected_return=InvestmentReturn(value=0.65, confidence=0.75, time_horizon_days=60),
            risk=InvestmentRisk(uncertainty=0.05, downside=0.02),
        )
        
        # High risk, same value
        candidate_high_risk = InvestmentCandidate(
            candidate_id="high_risk",
            candidate_type=CandidateType.MISSION,
            description="Task",
            estimated_cost=InvestmentCost(time_hours=50, capital=5000, effort=0.5),
            expected_return=InvestmentReturn(value=0.65, confidence=0.75, time_horizon_days=60),
            risk=InvestmentRisk(uncertainty=0.7, downside=0.6),
        )
        
        score_low_risk = InvestmentScoringRubric.calculate_investment_score(candidate_low_risk)
        score_high_risk = InvestmentScoringRubric.calculate_investment_score(candidate_high_risk)
        
        # Low risk should score higher (not capped at 1.0)
        self.assertGreater(score_low_risk.investment_score, score_high_risk.investment_score)
    
    def test_reusability_multiplier_applied(self):
        """Reusability multiplier affects score."""
        # High reusability, moderate inputs
        candidate_reusable = InvestmentCandidate(
            candidate_id="reusable",
            candidate_type=CandidateType.BUILD,
            description="Framework",
            estimated_cost=InvestmentCost(time_hours=120, capital=10000, effort=0.7),
            expected_return=InvestmentReturn(value=0.7, confidence=0.75, time_horizon_days=60),
            risk=InvestmentRisk(uncertainty=0.2, downside=0.1),
            reusability=0.9
        )
        
        # No reusability, same inputs
        candidate_one_time = InvestmentCandidate(
            candidate_id="one_time",
            candidate_type=CandidateType.MISSION,
            description="One-off task",
            estimated_cost=InvestmentCost(time_hours=120, capital=10000, effort=0.7),
            expected_return=InvestmentReturn(value=0.7, confidence=0.75, time_horizon_days=60),
            risk=InvestmentRisk(uncertainty=0.2, downside=0.1),
            reusability=0.0
        )
        
        score_reusable = InvestmentScoringRubric.calculate_investment_score(candidate_reusable)
        score_one_time = InvestmentScoringRubric.calculate_investment_score(candidate_one_time)
        
        # Reusable should score higher (not capped at 1.0)
        self.assertGreater(score_reusable.investment_score, score_one_time.investment_score)


class TestInvestmentCore(unittest.TestCase):
    """Test Investment Core functionality."""
    
    def test_add_candidate(self):
        """Add candidate to core."""
        core = InvestmentCore()
        candidate = core.add_candidate(
            candidate_id="c1",
            candidate_type=CandidateType.BUILD,
            description="Test build",
            estimated_cost=InvestmentCost(time_hours=40, capital=0, effort=0.5),
            expected_return=InvestmentReturn(value=0.8, confidence=0.8),
            risk=InvestmentRisk(uncertainty=0.2, downside=0.1)
        )
        
        self.assertIsNotNone(candidate)
        self.assertEqual(candidate.candidate_id, "c1")
        self.assertEqual(core.get_candidate_count(), 1)
    
    def test_evaluate_candidate(self):
        """Evaluate a single candidate."""
        core = InvestmentCore()
        core.add_candidate(
            candidate_id="eval_test",
            candidate_type=CandidateType.MISSION,
            description="Task",
            estimated_cost=InvestmentCost(time_hours=20, capital=0, effort=0.3),
            expected_return=InvestmentReturn(value=0.9, confidence=0.9),
            risk=InvestmentRisk(uncertainty=0.1, downside=0.05)
        )
        
        score = core.evaluate_candidate("eval_test")
        
        self.assertIsNotNone(score)
        self.assertGreater(score.investment_score, 0.5)
    
    def test_rank_candidates(self):
        """Rank candidates by score."""
        core = InvestmentCore()
        
        # High value candidate
        core.add_candidate(
            candidate_id="high",
            candidate_type=CandidateType.BUILD,
            description="High value build",
            estimated_cost=InvestmentCost(time_hours=50, capital=0, effort=0.6),
            expected_return=InvestmentReturn(value=0.95, confidence=0.9),
            risk=InvestmentRisk(uncertainty=0.1, downside=0.05),
            reusability=0.8
        )
        
        # Low value candidate
        core.add_candidate(
            candidate_id="low",
            candidate_type=CandidateType.MISSION,
            description="Low value task",
            estimated_cost=InvestmentCost(time_hours=50, capital=0, effort=0.6),
            expected_return=InvestmentReturn(value=0.3, confidence=0.5),
            risk=InvestmentRisk(uncertainty=0.5, downside=0.3),
            reusability=0.0
        )
        
        ranked = core.rank_candidates()
        
        self.assertEqual(len(ranked), 2)
        self.assertEqual(ranked[0].candidate_id, "high")
        self.assertEqual(ranked[1].candidate_id, "low")
    
    def test_get_recommended_investments(self):
        """Get only recommended investments."""
        core = InvestmentCore()
        
        # Recommended
        core.add_candidate(
            candidate_id="rec1",
            candidate_type=CandidateType.BUILD,
            description="Good investment",
            estimated_cost=InvestmentCost(time_hours=30, capital=0, effort=0.4),
            expected_return=InvestmentReturn(value=0.85, confidence=0.85),
            risk=InvestmentRisk(uncertainty=0.15, downside=0.1),
            reusability=0.7
        )
        
        # Not recommended
        core.add_candidate(
            candidate_id="notrec1",
            candidate_type=CandidateType.MISSION,
            description="Poor investment",
            estimated_cost=InvestmentCost(time_hours=100, capital=0, effort=0.9),
            expected_return=InvestmentReturn(value=0.2, confidence=0.3),
            risk=InvestmentRisk(uncertainty=0.7, downside=0.5),
            reusability=0.0
        )
        
        recommended = core.get_recommended_investments()
        
        self.assertGreater(len(recommended), 0)
        self.assertIn("rec1", [s.candidate_id for s in recommended])
    
    def test_portfolio_analysis(self):
        """Get portfolio analysis."""
        core = InvestmentCore()
        
        for i in range(5):
            core.add_candidate(
                candidate_id=f"c{i}",
                candidate_type=CandidateType.MISSION,
                description=f"Task {i}",
                estimated_cost=InvestmentCost(time_hours=20+i*10, capital=0, effort=0.3),
                expected_return=InvestmentReturn(value=0.8-i*0.1, confidence=0.8),
                risk=InvestmentRisk(uncertainty=0.2+i*0.1, downside=0.1)
            )
        
        analysis = core.get_portfolio_analysis()
        
        self.assertEqual(analysis['total_candidates'], 5)
        self.assertIn('recommended', analysis)
        self.assertIn('average_score', analysis)


class TestSignalEmission(unittest.TestCase):
    """Test investment signal emission."""
    
    def test_emit_signal(self):
        """Emit a signal."""
        core = InvestmentCore()
        candidate = core.add_candidate(
            candidate_id="sig_test",
            candidate_type=CandidateType.BUILD,
            description="Test",
            estimated_cost=InvestmentCost(time_hours=40, capital=0, effort=0.5),
            expected_return=InvestmentReturn(value=0.85, confidence=0.85),
            risk=InvestmentRisk(uncertainty=0.15, downside=0.1)
        )
        
        score = core.evaluate_candidate("sig_test")
        
        signal = InvestmentSignalEmitter.emit_investment_signal(score, candidate)
        
        self.assertIsNotNone(signal)
        self.assertEqual(signal.signal_type, "investment_evaluation")
        self.assertEqual(signal.signal_layer, "economic")
        self.assertEqual(signal.signal_source, "investment_core")
    
    def test_signal_to_jsonl(self):
        """Write signal to JSONL file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            stream_file = Path(tmpdir) / "signals.jsonl"
            
            core = InvestmentCore()
            candidate = core.add_candidate(
                candidate_id="file_test",
                candidate_type=CandidateType.MISSION,
                description="Test",
                estimated_cost=InvestmentCost(time_hours=20, capital=0, effort=0.3),
                expected_return=InvestmentReturn(value=0.9, confidence=0.9),
                risk=InvestmentRisk(uncertainty=0.1, downside=0.05)
            )
            
            score = core.evaluate_candidate("file_test")
            
            signal = InvestmentSignalEmitter.emit_investment_signal(
                score, candidate, stream_file=stream_file
            )
            
            # Verify file created and readable
            self.assertTrue(stream_file.exists())
            
            signals = InvestmentSignalEmitter.get_signals_from_file(stream_file)
            self.assertEqual(len(signals), 1)
            self.assertEqual(signals[0].candidate_id, "file_test")
    
    def test_batch_signals(self):
        """Emit batch of signals."""
        with tempfile.TemporaryDirectory() as tmpdir:
            stream_file = Path(tmpdir) / "batch.jsonl"
            
            core = InvestmentCore()
            
            # Add 3 candidates
            for i in range(3):
                core.add_candidate(
                    candidate_id=f"batch_{i}",
                    candidate_type=CandidateType.MISSION,
                    description=f"Task {i}",
                    estimated_cost=InvestmentCost(time_hours=20, capital=0, effort=0.3),
                    expected_return=InvestmentReturn(value=0.8, confidence=0.8),
                    risk=InvestmentRisk(uncertainty=0.2, downside=0.1)
                )
            
            scores = core.evaluate_all()
            candidates_map = core._candidates
            
            signals = InvestmentSignalEmitter.emit_batch_signals(
                scores, candidates_map, stream_file
            )
            
            self.assertEqual(len(signals), 3)
            
            # Verify in file
            file_signals = InvestmentSignalEmitter.get_signals_from_file(stream_file)
            self.assertEqual(len(file_signals), 3)


class TestWhiteboardPanel(unittest.TestCase):
    """Test whiteboard visualization."""
    
    def test_panel_rendering(self):
        """Panel renders without errors."""
        core = InvestmentCore()
        
        for i in range(3):
            core.add_candidate(
                candidate_id=f"render_{i}",
                candidate_type=CandidateType.BUILD,
                description=f"Build {i}",
                estimated_cost=InvestmentCost(time_hours=40+i*20, capital=0, effort=0.5),
                expected_return=InvestmentReturn(value=0.8-i*0.1, confidence=0.8),
                risk=InvestmentRisk(uncertainty=0.2, downside=0.1)
            )
        
        panel = InvestmentWhiteboardPanel()
        panel.set_investment_core(core)
        
        rendered = panel.render()
        
        self.assertIsNotNone(rendered)
        self.assertGreater(len(rendered), 0)
        self.assertIn("INVESTMENT", rendered)
    
    def test_quick_summary(self):
        """Quick summary generation."""
        core = InvestmentCore()
        
        core.add_candidate(
            candidate_id="quick",
            candidate_type=CandidateType.MISSION,
            description="Task",
            estimated_cost=InvestmentCost(time_hours=20, capital=0, effort=0.3),
            expected_return=InvestmentReturn(value=0.85, confidence=0.85),
            risk=InvestmentRisk(uncertainty=0.15, downside=0.1)
        )
        
        panel = InvestmentWhiteboardPanel()
        panel.set_investment_core(core)
        
        summary = panel.render_quick_summary()
        
        self.assertIn("INVESTMENTS", summary)
        self.assertIn("Total:", summary)


class TestConstraintVerification(unittest.TestCase):
    """Verify all design constraints are maintained."""
    
    def test_no_autonomy_advisory_only(self):
        """Verify system is advisory only."""
        core = InvestmentCore()
        
        # Add candidate
        candidate = core.add_candidate(
            candidate_id="adv_test",
            candidate_type=CandidateType.MISSION,
            description="Task",
            estimated_cost=InvestmentCost(time_hours=20, capital=0, effort=0.3),
            expected_return=InvestmentReturn(value=0.9, confidence=0.9),
            risk=InvestmentRisk(uncertainty=0.1, downside=0.05)
        )
        
        # Evaluate
        score = core.evaluate_candidate("adv_test")
        
        # Score should be recommendation only
        self.assertIsNotNone(score.recommendation)
        
        # No side effects - candidate unchanged
        self.assertEqual(candidate.estimated_cost, core._candidates["adv_test"].estimated_cost)
    
    def test_no_execution_side_effects(self):
        """Verify no execution or state changes."""
        core1 = InvestmentCore()
        core2 = InvestmentCore()
        
        # Add same candidates to both cores
        for core in [core1, core2]:
            core.add_candidate(
                candidate_id="side_effect_test",
                candidate_type=CandidateType.BUILD,
                description="Build",
                estimated_cost=InvestmentCost(time_hours=50, capital=0, effort=0.6),
                expected_return=InvestmentReturn(value=0.8, confidence=0.8),
                risk=InvestmentRisk(uncertainty=0.2, downside=0.1),
                reusability=0.7
            )
        
        # Evaluate on core1
        score1 = core1.evaluate_candidate("side_effect_test")
        
        # Evaluate on core2 - should be identical
        score2 = core2.evaluate_candidate("side_effect_test")
        
        self.assertEqual(score1.investment_score, score2.investment_score)
        self.assertEqual(score1.recommendation, score2.recommendation)
    
    def test_deterministic_scoring(self):
        """Verify deterministic output (reproducible)."""
        core = InvestmentCore()
        
        candidate = core.add_candidate(
            candidate_id="det_test",
            candidate_type=CandidateType.BUILD,
            description="Build",
            estimated_cost=InvestmentCost(time_hours=60, capital=5000, effort=0.7),
            expected_return=InvestmentReturn(value=0.9, confidence=0.85, time_horizon_days=120),
            risk=InvestmentRisk(uncertainty=0.15, downside=0.1),
            reusability=0.8
        )
        
        # Evaluate 10 times
        scores = []
        for _ in range(10):
            score = InvestmentScoringRubric.calculate_investment_score(candidate)
            scores.append(score.investment_score)
        
        # All scores should be identical
        for score in scores[1:]:
            self.assertEqual(scores[0], score)
    
    def test_read_only_no_mutations(self):
        """Verify read-only analysis."""
        core = InvestmentCore()
        
        original_candidate = core.add_candidate(
            candidate_id="ro_test",
            candidate_type=CandidateType.MISSION,
            description="Task",
            estimated_cost=InvestmentCost(time_hours=25, capital=1000, effort=0.4),
            expected_return=InvestmentReturn(value=0.75, confidence=0.8),
            risk=InvestmentRisk(uncertainty=0.25, downside=0.15),
            reusability=0.5
        )
        
        # Analyze multiple times
        core.evaluate_candidate("ro_test")
        core.rank_candidates()
        core.get_portfolio_analysis()
        
        # Candidate should be unchanged (frozen dataclass)
        current = core._candidates["ro_test"]
        self.assertEqual(current.estimated_cost, original_candidate.estimated_cost)
        self.assertEqual(current.expected_return, original_candidate.expected_return)


class TestPhase10Integration(unittest.TestCase):
    """Integration tests for Phase 10."""
    
    def test_full_investment_workflow(self):
        """Full workflow: add → evaluate → rank → signal → display."""
        with tempfile.TemporaryDirectory() as tmpdir:
            signal_file = Path(tmpdir) / "investments.jsonl"
            
            # Create core
            core = InvestmentCore()
            
            # Add 5 candidates
            for i in range(5):
                core.add_candidate(
                    candidate_id=f"workflow_{i}",
                    candidate_type=CandidateType.BUILD,
                    description=f"Build option {i}",
                    estimated_cost=InvestmentCost(
                        time_hours=30 + i*10, capital=i*1000, effort=0.4+i*0.1
                    ),
                    expected_return=InvestmentReturn(
                        value=0.9-i*0.1, confidence=0.85, time_horizon_days=60+i*30
                    ),
                    risk=InvestmentRisk(uncertainty=0.2, downside=0.1),
                    reusability=0.7-i*0.1
                )
            
            # Rank
            ranked = core.rank_candidates()
            self.assertEqual(len(ranked), 5)
            
            # Emit signals
            candidates_map = core._candidates
            signals = InvestmentSignalEmitter.emit_batch_signals(
                ranked, candidates_map, signal_file
            )
            self.assertEqual(len(signals), 5)
            
            # Verify in file
            file_signals = InvestmentSignalEmitter.get_signals_from_file(signal_file)
            self.assertEqual(len(file_signals), 5)
            
            # Display on whiteboard
            panel = InvestmentWhiteboardPanel()
            panel.set_investment_core(core)
            
            display = panel.render()
            self.assertIn("INVESTMENT", display)
            
            summary = panel.render_quick_summary()
            self.assertIn("5", summary)


if __name__ == "__main__":
    unittest.main()

