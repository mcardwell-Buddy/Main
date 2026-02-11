"""
Phase 9: Comprehensive Test Suite

Tests for multi-mission orchestration with fatigue & ROI balancing.

Test Coverage:
  - Fatigue model calculations
  - Mission orchestration logic
  - Signal emission
  - Whiteboard rendering
  - Constraint verification (5 concurrent missions scenario)

Requirements:
  - 5+ concurrent missions
  - All decisions are advisory
  - No autonomy, no execution
"""

import unittest
import tempfile
from pathlib import Path
from datetime import datetime

from Back_End.fatigue_model import (
    FatigueState, DailyBudget, FatigueScore, FatigueCalculator
)
from Back_End.mission_orchestrator import (
    MissionStatus, MissionEntry, MissionOrchestrator, MissionPriority
)
from Back_End.orchestration_whiteboard_panel import (
    OrchestrationWhiteboardPanel, OrchestrationPanelManager
)
from Back_End.orchestration_signal_emitter import (
    MissionPrioritizationSignal, OrchestrationSignalEmitter
)
from Back_End.tradeoff_evaluator import TradeoffScore, TradeoffDecision


class TestFatigueModel(unittest.TestCase):
    """Test fatigue calculation and state transitions."""
    
    def test_fresh_state(self):
        """Fresh state: 0% usage."""
        budget = DailyBudget(total_minutes=480, used_minutes=0)
        score = FatigueCalculator.calculate_fatigue_score(budget)
        
        self.assertEqual(score.state, FatigueState.FRESH)
        self.assertEqual(score.exhaustion_ratio, 0.0)
        self.assertEqual(score.capacity_multiplier, 1.0)
        self.assertEqual(score.complexity_threshold, "COMPLEX")
        self.assertTrue(score.can_accept_new_mission())
    
    def test_normal_state(self):
        """Normal state: 20-60% usage."""
        budget = DailyBudget(total_minutes=480, used_minutes=240)  # 50%
        score = FatigueCalculator.calculate_fatigue_score(budget)
        
        self.assertEqual(score.state, FatigueState.NORMAL)
        self.assertAlmostEqual(score.exhaustion_ratio, 0.5)
        self.assertEqual(score.capacity_multiplier, 0.85)
        self.assertEqual(score.complexity_threshold, "MEDIUM")
        self.assertTrue(score.can_accept_new_mission())
    
    def test_tired_state(self):
        """Tired state: 60-85% usage."""
        budget = DailyBudget(total_minutes=480, used_minutes=330)  # 68.75%
        score = FatigueCalculator.calculate_fatigue_score(budget)
        
        self.assertEqual(score.state, FatigueState.TIRED)
        self.assertGreater(score.exhaustion_ratio, 0.60)
        self.assertEqual(score.capacity_multiplier, 0.6)
        self.assertEqual(score.complexity_threshold, "SIMPLE")
        self.assertTrue(score.can_accept_new_mission())
    
    def test_exhausted_state(self):
        """Exhausted state: 85%+ usage."""
        budget = DailyBudget(total_minutes=480, used_minutes=450)  # 93.75%
        score = FatigueCalculator.calculate_fatigue_score(budget)
        
        self.assertEqual(score.state, FatigueState.EXHAUSTED)
        self.assertGreater(score.exhaustion_ratio, 0.85)
        self.assertEqual(score.capacity_multiplier, 0.3)
        self.assertEqual(score.complexity_threshold, "NONE")
        self.assertFalse(score.can_accept_new_mission())
        self.assertTrue(score.is_budget_exhausted())
    
    def test_budget_remaining(self):
        """Test budget remaining calculation."""
        budget = DailyBudget(total_minutes=480, used_minutes=100)
        self.assertEqual(budget.remaining_minutes(), 380)
    
    def test_budget_can_afford_mission(self):
        """Test budget affordability check."""
        budget = DailyBudget(total_minutes=480, used_minutes=450)
        self.assertFalse(budget.can_afford_mission(60))  # 450 + 60 > 480
        self.assertTrue(budget.can_afford_mission(30))   # 450 + 30 <= 480
    
    def test_budget_update_used(self):
        """Test budget update with additional used minutes."""
        budget = DailyBudget(total_minutes=480, used_minutes=100)
        updated = budget.update_used(50)
        
        self.assertEqual(updated.used_minutes, 150)
        self.assertEqual(updated.total_minutes, 480)
        self.assertEqual(updated.remaining_minutes(), 330)
    
    def test_capacity_multiplier_roi_adjustment(self):
        """Test ROI adjustment for fatigue."""
        # Fresh: ROI = 2.0x → adjusted 2.0x
        score_fresh = FatigueCalculator.calculate_fatigue_score(
            DailyBudget(total_minutes=480, used_minutes=50)
        )
        adjusted_fresh = FatigueCalculator.adjust_roi_for_fatigue(2.0, score_fresh)
        self.assertEqual(adjusted_fresh, 2.0)
        
        # Tired: ROI = 2.0x → adjusted 1.2x
        score_tired = FatigueCalculator.calculate_fatigue_score(
            DailyBudget(total_minutes=480, used_minutes=330)
        )
        adjusted_tired = FatigueCalculator.adjust_roi_for_fatigue(2.0, score_tired)
        self.assertEqual(adjusted_tired, 1.2)  # 2.0 * 0.6
    
    def test_quality_impact_per_state(self):
        """Test quality degradation across fatigue states."""
        impacts_fresh = FatigueCalculator.get_quality_impact(FatigueState.FRESH)
        impacts_exhausted = FatigueCalculator.get_quality_impact(FatigueState.EXHAUSTED)
        
        # Error rate increases
        self.assertEqual(impacts_fresh["error_rate"], 0.02)
        self.assertEqual(impacts_exhausted["error_rate"], 0.40)
        
        # Decision quality decreases
        self.assertEqual(impacts_fresh["decision_quality"], 1.0)
        self.assertEqual(impacts_exhausted["decision_quality"], 0.50)


class TestMissionOrchestration(unittest.TestCase):
    """Test mission orchestration logic."""
    
    def test_add_mission(self):
        """Test adding a mission."""
        orchestrator = MissionOrchestrator()
        mission = orchestrator.add_mission(
            description="Fix authentication bug",
            estimated_effort_minutes=45,
            estimated_payoff_minutes=120,
            mission_id="m1"
        )
        
        self.assertEqual(mission.mission_id, "m1")
        self.assertEqual(mission.status, MissionStatus.QUEUED)
        self.assertEqual(mission.roi_ratio(), 120/45)  # ~2.67x
    
    def test_pause_mission(self):
        """Test pausing a mission."""
        orchestrator = MissionOrchestrator()
        mission = orchestrator.add_mission(
            description="Nice-to-have feature",
            estimated_effort_minutes=120,
            estimated_payoff_minutes=240,
            mission_id="m1"
        )
        
        paused = orchestrator.pause_mission("m1", "Budget constraint")
        self.assertEqual(paused.status, MissionStatus.PAUSED)
        self.assertEqual(paused.paused_reason, "Budget constraint")
    
    def test_resume_mission(self):
        """Test resuming a paused mission."""
        orchestrator = MissionOrchestrator()
        orchestrator.add_mission(
            description="Test",
            estimated_effort_minutes=30,
            estimated_payoff_minutes=60,
            mission_id="m1"
        )
        orchestrator.pause_mission("m1")
        
        resumed = orchestrator.resume_mission("m1")
        self.assertEqual(resumed.status, MissionStatus.QUEUED)
    
    def test_five_concurrent_missions(self):
        """Test orchestration with 5 concurrent missions."""
        orchestrator = MissionOrchestrator()
        
        # Add 5 missions with varying ROI
        missions_data = [
            ("m1", "High-ROI task", 30, 120, 4.0),      # 4.0x ROI
            ("m2", "Medium-ROI task", 60, 120, 2.0),    # 2.0x ROI
            ("m3", "Low-ROI task", 90, 90, 1.0),        # 1.0x ROI
            ("m4", "Good idea", 120, 360, 3.0),         # 3.0x ROI (large)
            ("m5", "Quick win", 15, 45, 3.0),           # 3.0x ROI
        ]
        
        for mid, desc, effort, payoff, expected_roi in missions_data:
            mission = orchestrator.add_mission(
                description=desc,
                estimated_effort_minutes=effort,
                estimated_payoff_minutes=payoff,
                mission_id=mid
            )
            self.assertAlmostEqual(mission.roi_ratio(), expected_roi, places=1)
        
        # Verify all missions added
        self.assertEqual(len(orchestrator._missions), 5)
        
        # Test prioritization with limited budget
        priorities, _ = orchestrator.prioritize_missions(
            available_budget_minutes=180,  # Only 180 min available
            max_recommendations=5
        )
        
        # Should rank m5 and m1 as affordable/priority
        self.assertGreater(len(priorities), 0)
        
        # Manually pause the large mission to test deferred good ideas
        orchestrator.pause_mission("m4", "Budget constraint")
        
        # Check for good ideas being deferred
        deferred = orchestrator.get_deferred_good_ideas()
        self.assertGreater(len(deferred), 0)
        self.assertIn("m4", [m.mission_id for m in deferred])
    
    def test_mission_prioritization(self):
        """Test mission prioritization algorithm."""
        orchestrator = MissionOrchestrator()
        
        # Add missions in random order
        orchestrator.add_mission("Task A", 60, 180, mission_id="a")   # 3.0x ROI
        orchestrator.add_mission("Task B", 30, 60, mission_id="b")    # 2.0x ROI
        orchestrator.add_mission("Task C", 90, 90, mission_id="c")    # 1.0x ROI
        
        priorities, _ = orchestrator.prioritize_missions(available_budget_minutes=120)
        
        # Should prioritize by ROI
        rank_a = next((p for p in priorities if p.mission_id == "a"), None)
        rank_b = next((p for p in priorities if p.mission_id == "b"), None)
        rank_c = next((p for p in priorities if p.mission_id == "c"), None)
        
        self.assertLess(rank_a.rank, rank_b.rank)
        self.assertLess(rank_b.rank, rank_c.rank)
    
    def test_deferred_good_ideas(self):
        """Test identification of deferred good ideas."""
        orchestrator = MissionOrchestrator()
        
        # Add a good idea (positive ROI)
        orchestrator.add_mission("Good idea", 120, 360, mission_id="good")
        
        # Pause it
        orchestrator.pause_mission("good", "Budget exceeded")
        
        # Verify it's identified as deferred good idea
        deferred = orchestrator.get_deferred_good_ideas()
        self.assertEqual(len(deferred), 1)
        self.assertEqual(deferred[0].mission_id, "good")
    
    def test_portfolio_roi(self):
        """Test portfolio ROI calculation."""
        orchestrator = MissionOrchestrator()
        
        orchestrator.add_mission("Task 1", 30, 90, mission_id="t1")   # 3.0x
        orchestrator.add_mission("Task 2", 60, 120, mission_id="t2")  # 2.0x
        
        roi = orchestrator.get_portfolio_roi()
        expected = (3.0 + 2.0) / 2
        self.assertAlmostEqual(roi, expected, places=1)


class TestOrchestrationSignals(unittest.TestCase):
    """Test orchestration signal emission."""
    
    def test_emit_prioritization_signal(self):
        """Test emitting a prioritization signal."""
        orchestrator = MissionOrchestrator()
        orchestrator.add_mission("Task 1", 30, 90, mission_id="m1")
        
        budget = DailyBudget(total_minutes=480, used_minutes=100)
        fatigue = FatigueCalculator.calculate_fatigue_score(budget)
        priorities = []
        
        signal = OrchestrationSignalEmitter.emit_prioritization_signal(
            orchestrator, fatigue, priorities, work_id="w1"
        )
        
        self.assertEqual(signal.signal_type, "mission_prioritization")
        self.assertEqual(signal.signal_layer, "orchestration")
        self.assertEqual(signal.signal_source, "mission_orchestrator")
        self.assertEqual(signal.work_id, "w1")
        self.assertEqual(signal.queued_count, 1)
    
    def test_signal_to_jsonl(self):
        """Test writing signal to JSONL file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            stream_file = Path(tmpdir) / "signals.jsonl"
            
            orchestrator = MissionOrchestrator()
            orchestrator.add_mission("Task", 30, 90, mission_id="m1")
            
            budget = DailyBudget(total_minutes=480, used_minutes=100)
            fatigue = FatigueCalculator.calculate_fatigue_score(budget)
            
            signal = OrchestrationSignalEmitter.emit_prioritization_signal(
                orchestrator, fatigue, [], work_id="w1", stream_file=stream_file
            )
            
            # Verify file was created and contains signal
            self.assertTrue(stream_file.exists())
            signals = OrchestrationSignalEmitter.get_signals_from_file(stream_file)
            self.assertEqual(len(signals), 1)
            self.assertEqual(signals[0].work_id, "w1")
    
    def test_get_latest_signal(self):
        """Test retrieving latest signal from file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            stream_file = Path(tmpdir) / "signals.jsonl"
            
            orchestrator = MissionOrchestrator()
            orchestrator.add_mission("Task 1", 30, 90, mission_id="m1")
            budget = DailyBudget(total_minutes=480, used_minutes=50)
            fatigue = FatigueCalculator.calculate_fatigue_score(budget)
            
            # Emit first signal
            signal1 = OrchestrationSignalEmitter.emit_prioritization_signal(
                orchestrator, fatigue, [], work_id="w1", stream_file=stream_file
            )
            
            # Emit second signal
            orchestrator.add_mission("Task 2", 60, 120, mission_id="m2")
            signal2 = OrchestrationSignalEmitter.emit_prioritization_signal(
                orchestrator, fatigue, [], work_id="w1", stream_file=stream_file
            )
            
            # Get latest
            latest = OrchestrationSignalEmitter.get_latest_signal(stream_file)
            self.assertIsNotNone(latest)
            self.assertEqual(latest.queued_count, 2)


class TestWhiteboardPanel(unittest.TestCase):
    """Test orchestration whiteboard rendering."""
    
    def test_panel_rendering(self):
        """Test whiteboard panel renders without errors."""
        orchestrator = MissionOrchestrator()
        orchestrator.add_mission("Task 1", 30, 90, mission_id="m1")
        orchestrator.set_active_mission("m1")
        
        budget = DailyBudget(total_minutes=480, used_minutes=100)
        fatigue = FatigueCalculator.calculate_fatigue_score(budget)
        
        panel = OrchestrationWhiteboardPanel()
        panel.set_orchestration_state(orchestrator, fatigue, budget, [])
        
        rendered = panel.render()
        
        self.assertIsNotNone(rendered)
        self.assertGreater(len(rendered), 0)
        self.assertIn("MISSION ORCHESTRATION WHITEBOARD", rendered)
        self.assertIn("FATIGUE", rendered)
    
    def test_quick_summary(self):
        """Test quick summary generation."""
        orchestrator = MissionOrchestrator()
        orchestrator.add_mission("Task", 30, 90, mission_id="m1")
        
        budget = DailyBudget(total_minutes=480, used_minutes=240)
        fatigue = FatigueCalculator.calculate_fatigue_score(budget)
        
        panel = OrchestrationWhiteboardPanel()
        panel.set_orchestration_state(orchestrator, fatigue, budget, [])
        
        summary = panel.render_quick_summary()
        
        self.assertIn("NORMAL", summary)
        self.assertIn("50%", summary)
    
    def test_portfolio_view(self):
        """Test portfolio view rendering."""
        orchestrator = MissionOrchestrator()
        orchestrator.add_mission("Task 1", 30, 90, mission_id="m1")
        orchestrator.add_mission("Task 2", 60, 120, mission_id="m2")
        
        panel = OrchestrationWhiteboardPanel()
        
        # Need to set orchestration state for portfolio view
        budget = DailyBudget(total_minutes=480, used_minutes=100)
        fatigue = FatigueCalculator.calculate_fatigue_score(budget)
        panel.set_orchestration_state(orchestrator, fatigue, budget, [])
        
        portfolio = panel.render_portfolio_view()
        
        self.assertIn("PORTFOLIO", portfolio)
        self.assertIn("Total Missions", portfolio)


class TestConstraintVerification(unittest.TestCase):
    """Verify all design constraints are maintained."""
    
    def test_no_autonomy_advisory_only(self):
        """Verify orchestration is advisory only."""
        orchestrator = MissionOrchestrator()
        
        # Add mission
        mission = orchestrator.add_mission(
            description="Test",
            estimated_effort_minutes=30,
            estimated_payoff_minutes=90,
            mission_id="m1"
        )
        
        # Mission should not change its status without explicit user action
        self.assertEqual(mission.status, MissionStatus.QUEUED)
        
        # Prioritization gives recommendations but doesn't change mission state
        priorities, _ = orchestrator.prioritize_missions(available_budget_minutes=100)
        
        # Original mission still in same state
        fetched = orchestrator.get_mission("m1")
        self.assertEqual(fetched.status, MissionStatus.QUEUED)
    
    def test_no_parallel_execution(self):
        """Verify no parallel execution (single active mission)."""
        orchestrator = MissionOrchestrator()
        
        orchestrator.add_mission("Task 1", 30, 90, mission_id="m1")
        orchestrator.add_mission("Task 2", 60, 120, mission_id="m2")
        
        # Only one mission can be active at a time
        orchestrator.set_active_mission("m1")
        self.assertEqual(orchestrator.get_active_mission().mission_id, "m1")
        
        # Set different active mission
        orchestrator.set_active_mission("m2")
        self.assertEqual(orchestrator.get_active_mission().mission_id, "m2")
        
        # Only one active at a time
        active, queued, paused = orchestrator.get_queue_summary()
        self.assertLessEqual(active, 1)
    
    def test_no_mission_killing_pause_is_advisory(self):
        """Verify paused missions can always be resumed (no mission killing)."""
        orchestrator = MissionOrchestrator()
        
        mission = orchestrator.add_mission(
            description="Good idea",
            estimated_effort_minutes=120,
            estimated_payoff_minutes=360,
            mission_id="m1"
        )
        
        # Pause it
        paused = orchestrator.pause_mission("m1", "Budget exceeded")
        self.assertEqual(paused.status, MissionStatus.PAUSED)
        
        # Can always resume (no permanent deletion)
        resumed = orchestrator.resume_mission("m1")
        self.assertEqual(resumed.status, MissionStatus.QUEUED)
    
    def test_no_learning_loops_deterministic(self):
        """Verify deterministic behavior (no learning loops)."""
        orchestrator1 = MissionOrchestrator()
        orchestrator2 = MissionOrchestrator()
        
        # Add same missions to both
        for orch in [orchestrator1, orchestrator2]:
            orch.add_mission("Task A", 30, 90, mission_id="a")
            orch.add_mission("Task B", 60, 120, mission_id="b")
        
        budget = DailyBudget(total_minutes=480, used_minutes=100)
        fatigue = FatigueCalculator.calculate_fatigue_score(budget)
        
        # Get priorities (deterministic - no randomization)
        priorities1, _ = orchestrator1.prioritize_missions(240)
        priorities2, _ = orchestrator2.prioritize_missions(240)
        
        # Should be identical
        self.assertEqual(len(priorities1), len(priorities2))
        for p1, p2 in zip(priorities1, priorities2):
            self.assertEqual(p1.mission_id, p2.mission_id)
            self.assertEqual(p1.rank, p2.rank)
    
    def test_read_only_no_side_effects(self):
        """Verify analysis is read-only with no side effects."""
        orchestrator = MissionOrchestrator()
        mission = orchestrator.add_mission(
            description="Task",
            estimated_effort_minutes=30,
            estimated_payoff_minutes=90,
            mission_id="m1"
        )
        
        # Analyze
        budget = DailyBudget(total_minutes=480, used_minutes=100)
        fatigue = FatigueCalculator.calculate_fatigue_score(budget)
        priorities, _ = orchestrator.prioritize_missions(available_budget_minutes=200)
        
        # Mission should be unchanged
        fetched = orchestrator.get_mission("m1")
        self.assertEqual(fetched.status, MissionStatus.QUEUED)
        self.assertEqual(fetched.estimated_effort_minutes, 30)


class TestPhase9Integration(unittest.TestCase):
    """Integration tests for Phase 9 components."""
    
    def test_five_missions_full_scenario(self):
        """Full scenario: orchestrate 5 missions with fatigue."""
        orchestrator = MissionOrchestrator()
        
        # Add 5 missions
        missions = [
            ("m1", "Fix critical bug", 30, 120, 4.0),
            ("m2", "Add feature X", 90, 180, 2.0),
            ("m3", "Refactor module", 120, 120, 1.0),
            ("m4", "Write tests", 60, 180, 3.0),
            ("m5", "Code review", 20, 40, 2.0),
        ]
        
        for mid, desc, effort, payoff, _ in missions:
            orchestrator.add_mission(desc, effort, payoff, mission_id=mid)
        
        # Start fresh
        budget = DailyBudget(total_minutes=480, used_minutes=0)
        fatigue = FatigueCalculator.calculate_fatigue_score(budget)
        
        # Set first as active
        orchestrator.set_active_mission("m1")
        
        # Get priorities
        priorities, reasons = orchestrator.prioritize_missions(
            available_budget_minutes=480, max_recommendations=5
        )
        
        # Verify orchestration works
        self.assertEqual(len(orchestrator._missions), 5)
        self.assertGreater(len(priorities), 0)
        self.assertEqual(fatigue.state, FatigueState.FRESH)
        
        # Simulate doing first mission
        budget = budget.update_used(30)
        fatigue = FatigueCalculator.calculate_fatigue_score(budget)
        self.assertEqual(fatigue.state, FatigueState.FRESH)
        
        # Simulate heavy usage (350 min used)
        budget = DailyBudget(total_minutes=480, used_minutes=350)
        fatigue = FatigueCalculator.calculate_fatigue_score(budget)
        self.assertEqual(fatigue.state, FatigueState.TIRED)
        
        # With fatigue, prioritization should be constrained
        priorities_tired, _ = orchestrator.prioritize_missions(
            available_budget_minutes=100
        )
        
        # Should still give recommendations
        self.assertGreater(len(priorities_tired), 0)
    
    def test_panel_manager_multiple_workspaces(self):
        """Test panel manager handling multiple orchestrations."""
        manager = OrchestrationPanelManager()
        
        # Create 3 different orchestrations
        for work_id in ["w1", "w2", "w3"]:
            orchestrator = MissionOrchestrator()
            orchestrator.add_mission(f"Task for {work_id}", 30, 90, mission_id="m1")
            
            budget = DailyBudget(total_minutes=480, used_minutes=100)
            fatigue = FatigueCalculator.calculate_fatigue_score(budget)
            
            manager.set_orchestration_panel(work_id, orchestrator, fatigue, budget, [])
        
        # Get summaries
        summary = manager.get_all_panels_summary()
        self.assertIn("w1", summary)
        self.assertIn("w2", summary)
        self.assertIn("w3", summary)


if __name__ == "__main__":
    unittest.main()

