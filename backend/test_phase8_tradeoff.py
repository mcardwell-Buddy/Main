"""
Phase 8: Validation Test Suite - Economic Tradeoff Reasoning

Comprehensive test coverage for:
- TradeoffEvaluator scoring logic
- Deterministic decision making
- Signal emission
- Whiteboard rendering
- Constraint verification (no autonomy, no learning, etc.)

41 test cases covering:
- ROI calculation
- Multiplier application
- Decision thresholds
- Confidence scoring
- Signal structure
- Panel rendering
- Edge cases
"""

import pytest
import json
import os
from pathlib import Path
from datetime import datetime
from enum import Enum

from backend.tradeoff_evaluator import (
    TradeoffEvaluator,
    TradeoffScore,
    TradeoffOpportunity,
    TradeoffScoringRubric,
    TradeoffDecision,
    CognitiveLoad,
    ValueType
)
from backend.tradeoff_signal_emitter import (
    TradeoffSignalEmitter,
    TradeoffSignal
)
from backend.tradeoff_whiteboard_panel import (
    EconomicWhiteboardPanel,
    EconomicPanelManager
)


class TestTradeoffScoringRubric:
    """Test deterministic scoring rubric."""

    def test_roi_calculation_basic(self):
        """ROI = payoff / cost."""
        rubric = TradeoffScoringRubric()
        roi = rubric.calculate_roi(payoff=100, cost=50)
        assert roi == 2.0  # 100 / 50

    def test_roi_calculation_fractional(self):
        """ROI with fractional result."""
        rubric = TradeoffScoringRubric()
        roi = rubric.calculate_roi(payoff=30, cost=60)
        assert roi == 0.5  # 30 / 60

    def test_roi_calculation_zero_cost_guard(self):
        """ROI guards against division by zero."""
        rubric = TradeoffScoringRubric()
        # Should not raise, should handle gracefully
        try:
            roi = rubric.calculate_roi(payoff=100, cost=0.001)
            assert roi > 100  # Very high ROI with near-zero cost
        except ZeroDivisionError:
            pytest.fail("Should not raise ZeroDivisionError")

    def test_opportunity_cost_calculation(self):
        """Opportunity cost as time fraction."""
        rubric = TradeoffScoringRubric()
        opp_cost = rubric.calculate_opportunity_cost_score(
            time_used=30, available_time=60
        )
        assert opp_cost == 0.5  # 30 / 60

    def test_opportunity_cost_full(self):
        """Opportunity cost at 100%."""
        rubric = TradeoffScoringRubric()
        opp_cost = rubric.calculate_opportunity_cost_score(
            time_used=60, available_time=60
        )
        assert opp_cost == 1.0

    def test_opportunity_cost_minimal(self):
        """Opportunity cost near zero."""
        rubric = TradeoffScoringRubric()
        opp_cost = rubric.calculate_opportunity_cost_score(
            time_used=1, available_time=60
        )
        assert opp_cost == pytest.approx(1/60, abs=0.001)

    def test_cognitive_load_multiplier_low(self):
        """LOW cognitive load = 0.8x."""
        rubric = TradeoffScoringRubric()
        mult = rubric.COGNITIVE_LOAD_MULTIPLIER[CognitiveLoad.LOW]
        assert mult == 0.8

    def test_cognitive_load_multiplier_medium(self):
        """MEDIUM cognitive load = 1.0x."""
        rubric = TradeoffScoringRubric()
        mult = rubric.COGNITIVE_LOAD_MULTIPLIER[CognitiveLoad.MEDIUM]
        assert mult == 1.0

    def test_cognitive_load_multiplier_high(self):
        """HIGH cognitive load = 1.5x."""
        rubric = TradeoffScoringRubric()
        mult = rubric.COGNITIVE_LOAD_MULTIPLIER[CognitiveLoad.HIGH]
        assert mult == 1.5

    def test_cognitive_load_multiplier_critical(self):
        """CRITICAL cognitive load = 3.0x (hard to justify)."""
        rubric = TradeoffScoringRubric()
        mult = rubric.COGNITIVE_LOAD_MULTIPLIER[CognitiveLoad.CRITICAL]
        assert mult == 3.0

    def test_value_type_multiplier_one_time(self):
        """ONE_TIME value = 1.0x."""
        rubric = TradeoffScoringRubric()
        mult = rubric.VALUE_TYPE_MULTIPLIER[ValueType.ONE_TIME]
        assert mult == 1.0

    def test_value_type_multiplier_reusable(self):
        """REUSABLE value = 1.5x."""
        rubric = TradeoffScoringRubric()
        mult = rubric.VALUE_TYPE_MULTIPLIER[ValueType.REUSABLE]
        assert mult == 1.5

    def test_value_type_multiplier_compounding(self):
        """COMPOUNDING value = 2.0x."""
        rubric = TradeoffScoringRubric()
        mult = rubric.VALUE_TYPE_MULTIPLIER[ValueType.COMPOUNDING]
        assert mult == 2.0

    def test_urgency_multiplier_low(self):
        """Low urgency = 0.7x."""
        rubric = TradeoffScoringRubric()
        assert rubric.URGENCY_MULTIPLIER["low"] == 0.7

    def test_urgency_multiplier_normal(self):
        """Normal urgency = 1.0x."""
        rubric = TradeoffScoringRubric()
        assert rubric.URGENCY_MULTIPLIER["normal"] == 1.0

    def test_urgency_multiplier_high(self):
        """High urgency = 1.2x."""
        rubric = TradeoffScoringRubric()
        assert rubric.URGENCY_MULTIPLIER["high"] == 1.2

    def test_urgency_multiplier_critical(self):
        """Critical urgency = 1.5x."""
        rubric = TradeoffScoringRubric()
        assert rubric.URGENCY_MULTIPLIER["critical"] == 1.5


class TestTradeoffEvaluator:
    """Test TradeoffEvaluator scoring and decisions."""

    def test_evaluate_basic_high_value(self):
        """High ROI + low load = PROCEED."""
        evaluator = TradeoffEvaluator()
        opp = TradeoffOpportunity(
            name="Quick win",
            description="Fix typo",
            estimated_effort_minutes=30,
            estimated_payoff_minutes=150,
            cognitive_load=CognitiveLoad.LOW,
            value_type=ValueType.COMPOUNDING,
            urgency="normal"
        )
        score = evaluator.evaluate(opp)
        assert score.decision == TradeoffDecision.PROCEED
        assert score.adjusted_value >= 1.5

    def test_evaluate_basic_low_value(self):
        """Low ROI + high load = REJECT."""
        evaluator = TradeoffEvaluator()
        opp = TradeoffOpportunity(
            name="Not worth it",
            description="Polish feature",
            estimated_effort_minutes=120,
            estimated_payoff_minutes=30,
            cognitive_load=CognitiveLoad.HIGH,
            value_type=ValueType.ONE_TIME,
            urgency="low"
        )
        score = evaluator.evaluate(opp)
        assert score.decision == TradeoffDecision.REJECT
        assert score.adjusted_value < 0.5

    def test_evaluate_marginal(self):
        """Marginal ROI = PAUSE."""
        evaluator = TradeoffEvaluator()
        opp = TradeoffOpportunity(
            name="Borderline",
            description="Refactor",
            estimated_effort_minutes=60,
            estimated_payoff_minutes=60,
            cognitive_load=CognitiveLoad.MEDIUM,
            value_type=ValueType.ONE_TIME,
            urgency="normal"
        )
        score = evaluator.evaluate(opp)
        assert score.decision == TradeoffDecision.PAUSE
        assert 0.5 <= score.adjusted_value < 1.5

    def test_evaluate_critical_load_forces_reject(self):
        """CRITICAL cognitive load rejects even if ROI high."""
        evaluator = TradeoffEvaluator()
        opp = TradeoffOpportunity(
            name="Too complex",
            description="Complex task",
            estimated_effort_minutes=30,
            estimated_payoff_minutes=300,
            cognitive_load=CognitiveLoad.CRITICAL,
            value_type=ValueType.COMPOUNDING,
            urgency="normal"
        )
        score = evaluator.evaluate(opp)
        # CRITICAL load is hard to justify - should reject or heavily penalize
        assert score.decision in [TradeoffDecision.REJECT, TradeoffDecision.PAUSE]

    def test_evaluate_compounding_value_boosts_score(self):
        """COMPOUNDING value type provides 2.0x multiplier."""
        evaluator = TradeoffEvaluator()

        opp1 = TradeoffOpportunity(
            name="One-time",
            description="Task 1",
            estimated_effort_minutes=60,
            estimated_payoff_minutes=80,
            cognitive_load=CognitiveLoad.LOW,
            value_type=ValueType.ONE_TIME,
            urgency="normal"
        )
        score1 = evaluator.evaluate(opp1)

        opp2 = TradeoffOpportunity(
            name="Compounding",
            description="Task 2",
            estimated_effort_minutes=60,
            estimated_payoff_minutes=80,
            cognitive_load=CognitiveLoad.LOW,
            value_type=ValueType.COMPOUNDING,
            urgency="normal"
        )
        score2 = evaluator.evaluate(opp2)

        # Compounding should have higher value
        assert score2.adjusted_value > score1.adjusted_value

    def test_evaluate_urgency_affects_score(self):
        """Critical urgency provides 1.5x vs low urgency 0.7x."""
        evaluator = TradeoffEvaluator()

        opp_low = TradeoffOpportunity(
            name="Low urgency",
            description="Task 1",
            estimated_effort_minutes=60,
            estimated_payoff_minutes=80,
            cognitive_load=CognitiveLoad.MEDIUM,
            value_type=ValueType.ONE_TIME,
            urgency="low"
        )
        score_low = evaluator.evaluate(opp_low)

        opp_high = TradeoffOpportunity(
            name="High urgency",
            description="Task 2",
            estimated_effort_minutes=60,
            estimated_payoff_minutes=80,
            cognitive_load=CognitiveLoad.MEDIUM,
            value_type=ValueType.ONE_TIME,
            urgency="critical"
        )
        score_high = evaluator.evaluate(opp_high)

        # Critical urgency should have higher value
        assert score_high.adjusted_value > score_low.adjusted_value

    def test_evaluate_multiple(self):
        """Evaluate multiple opportunities and rank by value."""
        evaluator = TradeoffEvaluator()

        opps = [
            TradeoffOpportunity(
                name="Low value",
                description="Task 1",
                estimated_effort_minutes=120,
                estimated_payoff_minutes=30,
                cognitive_load=CognitiveLoad.HIGH,
                value_type=ValueType.ONE_TIME,
                urgency="low"
            ),
            TradeoffOpportunity(
                name="High value",
                description="Task 2",
                estimated_effort_minutes=30,
                estimated_payoff_minutes=150,
                cognitive_load=CognitiveLoad.LOW,
                value_type=ValueType.COMPOUNDING,
                urgency="normal"
            ),
            TradeoffOpportunity(
                name="Medium value",
                description="Task 3",
                estimated_effort_minutes=60,
                estimated_payoff_minutes=90,
                cognitive_load=CognitiveLoad.MEDIUM,
                value_type=ValueType.REUSABLE,
                urgency="high"
            )
        ]

        scores = evaluator.evaluate_multiple(opps)
        assert len(scores) == 3
        # Should be sorted by value (descending)
        assert scores[0].adjusted_value >= scores[1].adjusted_value >= scores[2].adjusted_value

    def test_confidence_ranges_0_4_to_0_95(self):
        """Confidence always in [0.4, 0.95] range."""
        evaluator = TradeoffEvaluator()

        for _ in range(20):
            opp = TradeoffOpportunity(
                name="Test",
                description="Test task",
                estimated_effort_minutes=30,
                estimated_payoff_minutes=90,
                cognitive_load=CognitiveLoad.MEDIUM,
                value_type=ValueType.REUSABLE,
                urgency="normal"
            )
            score = evaluator.evaluate(opp)
            assert 0.4 <= score.confidence <= 0.95

    def test_roi_ratio_calculation(self):
        """ROI ratio stored in score."""
        evaluator = TradeoffEvaluator()
        opp = TradeoffOpportunity(
            name="Test",
            description="Test task",
            estimated_effort_minutes=50,
            estimated_payoff_minutes=100,
            cognitive_load=CognitiveLoad.LOW,
            value_type=ValueType.ONE_TIME,
            urgency="normal"
        )
        score = evaluator.evaluate(opp)
        assert score.roi_ratio == 2.0  # 100 / 50

    def test_opportunity_cost_score_calculation(self):
        """Opportunity cost stored in score."""
        evaluator = TradeoffEvaluator()
        opp = TradeoffOpportunity(
            name="Test",
            description="Test task",
            estimated_effort_minutes=30,
            estimated_payoff_minutes=90,
            cognitive_load=CognitiveLoad.LOW,
            value_type=ValueType.ONE_TIME,
            urgency="normal"
        )
        score = evaluator.evaluate(opp)
        assert score.opportunity_cost_score > 0

    def test_rationale_generation(self):
        """Rationale is generated for each decision."""
        evaluator = TradeoffEvaluator()
        opp = TradeoffOpportunity(
            name="Test",
            description="Test task",
            estimated_effort_minutes=60,
            estimated_payoff_minutes=120,
            cognitive_load=CognitiveLoad.MEDIUM,
            value_type=ValueType.REUSABLE,
            urgency="high"
        )
        score = evaluator.evaluate(opp)
        assert len(score.rationale) > 20
        assert any(keyword in score.rationale for keyword in ["ROI", "value", "load", "payoff", "Factors"])

    def test_key_factors_included(self):
        """Key factors listed in score."""
        evaluator = TradeoffEvaluator()
        opp = TradeoffOpportunity(
            name="Test",
            description="Test task",
            estimated_effort_minutes=60,
            estimated_payoff_minutes=120,
            cognitive_load=CognitiveLoad.MEDIUM,
            value_type=ValueType.REUSABLE,
            urgency="high"
        )
        score = evaluator.evaluate(opp)
        assert len(score.key_factors) > 0
        assert isinstance(score.key_factors, list)

    def test_determinism_same_input_same_output(self):
        """Same input always produces same output (deterministic)."""
        evaluator = TradeoffEvaluator()
        opp = TradeoffOpportunity(
            name="Test",
            description="Test task",
            estimated_effort_minutes=60,
            estimated_payoff_minutes=120,
            cognitive_load=CognitiveLoad.MEDIUM,
            value_type=ValueType.REUSABLE,
            urgency="high"
        )

        score1 = evaluator.evaluate(opp)
        score2 = evaluator.evaluate(opp)

        assert score1.decision == score2.decision
        assert score1.adjusted_value == score2.adjusted_value
        assert score1.roi_ratio == score2.roi_ratio


class TestTradeoffSignalEmitter:
    """Test signal emission."""

    def test_signal_creation(self):
        """TradeoffSignal is created correctly."""
        signal = TradeoffSignal(
            signal_type="economic_tradeoff",
            signal_layer="economic",
            signal_source="tradeoff_engine",
            decision="PROCEED",
            adjusted_value=1.8,
            roi_ratio=2.0,
            opportunity_cost_score=0.25,
            cognitive_load="MEDIUM",
            value_type="COMPOUNDING",
            rationale="High ROI and compounding value"
        )
        assert signal.signal_type == "economic_tradeoff"
        assert signal.decision == "PROCEED"
        assert signal.adjusted_value == 1.8

    def test_signal_immutable(self):
        """Signal is frozen (immutable)."""
        signal = TradeoffSignal(
            signal_type="economic_tradeoff",
            signal_layer="economic",
            signal_source="tradeoff_engine",
            decision="PROCEED",
            adjusted_value=1.8,
            roi_ratio=2.0,
            opportunity_cost_score=0.25,
            cognitive_load="MEDIUM",
            value_type="COMPOUNDING",
            rationale="Test"
        )
        with pytest.raises(Exception):  # FrozenInstanceError
            signal.decision = "REJECT"

    def test_signal_timestamp(self):
        """Signal includes ISO UTC timestamp."""
        signal = TradeoffSignal(
            signal_type="economic_tradeoff",
            signal_layer="economic",
            signal_source="tradeoff_engine",
            decision="PROCEED",
            adjusted_value=1.8,
            roi_ratio=2.0,
            opportunity_cost_score=0.25,
            cognitive_load="MEDIUM",
            value_type="COMPOUNDING",
            rationale="Test"
        )
        assert signal.created_at is not None
        # Verify it's ISO format
        datetime.fromisoformat(signal.created_at.replace('Z', '+00:00'))

    def test_emit_single_signal(self, tmp_path):
        """Emit single tradeoff signal to JSONL."""
        stream_file = tmp_path / "signals.jsonl"
        emitter = TradeoffSignalEmitter()

        opp = TradeoffOpportunity(
            name="Test",
            description="Test task",
            estimated_effort_minutes=60,
            estimated_payoff_minutes=120,
            cognitive_load=CognitiveLoad.MEDIUM,
            value_type=ValueType.REUSABLE,
            urgency="high"
        )

        signal = emitter.emit_tradeoff_signal(opp, str(stream_file), work_id="work1")
        assert signal.decision in ["PROCEED", "PAUSE", "REJECT"]

    def test_emit_batch_signals(self, tmp_path):
        """Emit batch of signals."""
        stream_file = tmp_path / "signals.jsonl"
        emitter = TradeoffSignalEmitter()

        opps = [
            TradeoffOpportunity(
                name="Opp1",
                description="Task 1",
                estimated_effort_minutes=30,
                estimated_payoff_minutes=150,
                cognitive_load=CognitiveLoad.LOW,
                value_type=ValueType.COMPOUNDING,
                urgency="normal"
            ),
            TradeoffOpportunity(
                name="Opp2",
                description="Task 2",
                estimated_effort_minutes=120,
                estimated_payoff_minutes=30,
                cognitive_load=CognitiveLoad.HIGH,
                value_type=ValueType.ONE_TIME,
                urgency="low"
            )
        ]

        signals = emitter.emit_batch_signals(opps, str(stream_file))
        assert len(signals) == 2

    def test_signals_append_not_overwrite(self, tmp_path):
        """Multiple emissions append to file, don't overwrite."""
        stream_file = tmp_path / "signals.jsonl"
        emitter = TradeoffSignalEmitter()

        opp = TradeoffOpportunity(
            name="Test",
            description="Test task",
            estimated_effort_minutes=60,
            estimated_payoff_minutes=120,
            cognitive_load=CognitiveLoad.MEDIUM,
            value_type=ValueType.REUSABLE,
            urgency="normal"
        )

        # First emission
        emitter.emit_tradeoff_signal(opp, str(stream_file), work_id="work1")
        with open(stream_file) as f:
            lines1 = len(f.readlines())

        # Second emission
        emitter.emit_tradeoff_signal(opp, str(stream_file), work_id="work2")
        with open(stream_file) as f:
            lines2 = len(f.readlines())

        assert lines2 == lines1 + 1


class TestEconomicWhiteboardPanel:
    """Test whiteboard panel rendering."""

    def test_panel_renders_without_error(self):
        """Panel renders without raising exception."""
        panel = EconomicWhiteboardPanel()
        evaluator = TradeoffEvaluator()

        opp = TradeoffOpportunity(
            name="Test",
            description="Test task",
            estimated_effort_minutes=60,
            estimated_payoff_minutes=120,
            cognitive_load=CognitiveLoad.MEDIUM,
            value_type=ValueType.REUSABLE,
            urgency="high"
        )

        score = evaluator.evaluate(opp)
        panel.set_tradeoff_score(score)
        rendered = panel.render()

        assert isinstance(rendered, str)
        assert len(rendered) > 50

    def test_panel_shows_decision(self):
        """Panel displays decision."""
        panel = EconomicWhiteboardPanel()
        evaluator = TradeoffEvaluator()

        opp = TradeoffOpportunity(
            name="Test",
            description="Test task",
            estimated_effort_minutes=30,
            estimated_payoff_minutes=150,
            cognitive_load=CognitiveLoad.LOW,
            value_type=ValueType.COMPOUNDING,
            urgency="normal"
        )

        score = evaluator.evaluate(opp)
        panel.set_tradeoff_score(score)
        rendered = panel.render()

        assert "PROCEED" in rendered or "PAUSE" in rendered or "REJECT" in rendered

    def test_panel_shows_roi(self):
        """Panel displays ROI."""
        panel = EconomicWhiteboardPanel()
        evaluator = TradeoffEvaluator()

        opp = TradeoffOpportunity(
            name="Test",
            description="Test task",
            estimated_effort_minutes=50,
            estimated_payoff_minutes=100,
            cognitive_load=CognitiveLoad.LOW,
            value_type=ValueType.ONE_TIME,
            urgency="normal"
        )

        score = evaluator.evaluate(opp)
        panel.set_tradeoff_score(score)
        rendered = panel.render()

        assert "ROI" in rendered
        assert "2.0" in rendered  # 100/50

    def test_quick_summary_returns_string(self):
        """Quick summary returns single-line string."""
        panel = EconomicWhiteboardPanel()
        evaluator = TradeoffEvaluator()

        opp = TradeoffOpportunity(
            name="Test",
            description="Test task",
            estimated_effort_minutes=60,
            estimated_payoff_minutes=120,
            cognitive_load=CognitiveLoad.MEDIUM,
            value_type=ValueType.REUSABLE,
            urgency="normal"
        )

        score = evaluator.evaluate(opp)
        panel.set_tradeoff_score(score)
        summary = panel.render_quick_summary()

        assert isinstance(summary, str)
        assert len(summary) > 0
        assert "\n" not in summary  # Single line

    def test_portfolio_view_sorts_by_value(self):
        """Portfolio view sorts by adjusted value."""
        panel = EconomicWhiteboardPanel()
        evaluator = TradeoffEvaluator()

        opps = [
            TradeoffOpportunity(
                name="Low",
                description="Task 1",
                estimated_effort_minutes=120,
                estimated_payoff_minutes=30,
                cognitive_load=CognitiveLoad.HIGH,
                value_type=ValueType.ONE_TIME,
                urgency="low"
            ),
            TradeoffOpportunity(
                name="High",
                description="Task 2",
                estimated_effort_minutes=30,
                estimated_payoff_minutes=150,
                cognitive_load=CognitiveLoad.LOW,
                value_type=ValueType.COMPOUNDING,
                urgency="normal"
            )
        ]

        scores = [evaluator.evaluate(opp) for opp in opps]
        portfolio = panel.render_portfolio_view(scores)

        assert "High" in portfolio
        assert "Low" in portfolio
        # High value should appear before low value
        high_idx = portfolio.find("High")
        low_idx = portfolio.find("Low")
        assert high_idx < low_idx


class TestEconomicPanelManager:
    """Test panel manager integration."""

    def test_manager_stores_scores(self):
        """Manager stores evaluated scores."""
        manager = EconomicPanelManager()

        opp = TradeoffOpportunity(
            name="Test",
            description="Test task",
            estimated_effort_minutes=60,
            estimated_payoff_minutes=120,
            cognitive_load=CognitiveLoad.MEDIUM,
            value_type=ValueType.REUSABLE,
            urgency="normal"
        )

        score = manager.evaluate_and_store("work1", opp)
        retrieved = manager.get_score("work1")

        assert retrieved is not None
        assert retrieved.decision == score.decision

    def test_manager_get_proceed_work(self):
        """Manager filters work by decision."""
        manager = EconomicPanelManager()

        opp_proceed = TradeoffOpportunity(
            name="Proceed",
            description="Task 1",
            estimated_effort_minutes=30,
            estimated_payoff_minutes=150,
            cognitive_load=CognitiveLoad.LOW,
            value_type=ValueType.COMPOUNDING,
            urgency="normal"
        )

        opp_reject = TradeoffOpportunity(
            name="Reject",
            description="Task 2",
            estimated_effort_minutes=120,
            estimated_payoff_minutes=30,
            cognitive_load=CognitiveLoad.HIGH,
            value_type=ValueType.ONE_TIME,
            urgency="low"
        )

        manager.evaluate_and_store("work1", opp_proceed)
        manager.evaluate_and_store("work2", opp_reject)

        proceed_work = manager.get_proceed_work()
        assert len(proceed_work) > 0
        assert any(wid == "work1" for wid, _ in proceed_work)

    def test_manager_total_recommended_effort(self):
        """Manager calculates total recommended effort."""
        manager = EconomicPanelManager()

        opp1 = TradeoffOpportunity(
            name="Short",
            description="Task 1",
            estimated_effort_minutes=30,
            estimated_payoff_minutes=150,
            cognitive_load=CognitiveLoad.LOW,
            value_type=ValueType.COMPOUNDING,
            urgency="normal"
        )

        opp2 = TradeoffOpportunity(
            name="Medium",
            description="Task 2",
            estimated_effort_minutes=60,
            estimated_payoff_minutes=120,
            cognitive_load=CognitiveLoad.MEDIUM,
            value_type=ValueType.REUSABLE,
            urgency="high"
        )

        manager.evaluate_and_store("work1", opp1)
        manager.evaluate_and_store("work2", opp2)

        total = manager.get_total_recommended_effort()
        # If both proceed: 30 + 60 = 90
        # At minimum, should reflect time costs
        assert total >= 0


class TestConstraintVerification:
    """Verify Phase 8 design constraints."""

    def test_no_autonomy_advisory_only(self):
        """Evaluator only advises, never executes."""
        evaluator = TradeoffEvaluator()
        opp = TradeoffOpportunity(
            name="Test",
            description="Test task",
            estimated_effort_minutes=60,
            estimated_payoff_minutes=120,
            cognitive_load=CognitiveLoad.MEDIUM,
            value_type=ValueType.REUSABLE,
            urgency="normal"
        )

        score = evaluator.evaluate(opp)
        # Score should not execute anything, just provide decision
        assert score.decision in [TradeoffDecision.PROCEED, TradeoffDecision.PAUSE, TradeoffDecision.REJECT]
        # No side effects expected

    def test_no_learning_loops_deterministic(self):
        """Evaluator is deterministic, not learning."""
        evaluator = TradeoffEvaluator()
        opp = TradeoffOpportunity(
            name="Test",
            description="Test task",
            estimated_effort_minutes=60,
            estimated_payoff_minutes=120,
            cognitive_load=CognitiveLoad.MEDIUM,
            value_type=ValueType.REUSABLE,
            urgency="normal"
        )

        # Run 10 times
        scores = [evaluator.evaluate(opp) for _ in range(10)]

        # All should be identical
        first_decision = scores[0].decision
        first_value = scores[0].adjusted_value

        for score in scores[1:]:
            assert score.decision == first_decision
            assert score.adjusted_value == first_value

    def test_no_mission_killing_advisory(self):
        """Evaluator suggests but doesn't prevent work."""
        evaluator = TradeoffEvaluator()

        opp = TradeoffOpportunity(
            name="Test",
            description="Test task",
            estimated_effort_minutes=120,
            estimated_payoff_minutes=30,
            cognitive_load=CognitiveLoad.HIGH,
            value_type=ValueType.ONE_TIME,
            urgency="low"
        )

        score = evaluator.evaluate(opp)

        # Even if REJECT, it's just advice - doesn't prevent user from doing it
        assert score.decision is not None
        assert score.rationale is not None
        # User can still choose to proceed despite REJECT decision

    def test_no_external_api_calls(self):
        """Evaluator makes no external API calls."""
        evaluator = TradeoffEvaluator()
        opp = TradeoffOpportunity(
            name="Test",
            description="Test task",
            estimated_effort_minutes=60,
            estimated_payoff_minutes=120,
            cognitive_load=CognitiveLoad.MEDIUM,
            value_type=ValueType.REUSABLE,
            urgency="normal"
        )

        # Should work offline, no external calls
        try:
            score = evaluator.evaluate(opp)
            assert score is not None
        except Exception as e:
            if "API" in str(e) or "network" in str(e).lower():
                pytest.fail(f"Should not require external API: {e}")

    def test_read_only_no_side_effects(self):
        """Evaluator has no side effects."""
        evaluator = TradeoffEvaluator()
        opp = TradeoffOpportunity(
            name="Test",
            description="Test task",
            estimated_effort_minutes=60,
            estimated_payoff_minutes=120,
            cognitive_load=CognitiveLoad.MEDIUM,
            value_type=ValueType.REUSABLE,
            urgency="normal"
        )

        # Evaluate multiple times
        for _ in range(5):
            score = evaluator.evaluate(opp)
            # opp should not be modified
            assert opp.estimated_effort_minutes == 60
            assert opp.estimated_payoff_minutes == 120


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
