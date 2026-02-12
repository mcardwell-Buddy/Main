"""
Tests for Artifact Cost Reconciliation System (Phase 4b)

Tests the cost tracking and reconciliation:
- Cost estimation recording
- Actual cost recording
- Cost reconciliation
- Variance analysis
- Provider-specific costs
- Report generation
"""

import json
from typing import Dict, Any
import pytest

from Back_End.artifact_cost_reconciliation import (
    CostReconciliationEngine,
    CostEstimate,
    CostActual,
    CostReconciliation,
    CostProvider,
    get_cost_reconciliation_engine,
)


class TestCostEstimateAndActual:
    """Test cost estimate and actual objects"""

    def test_cost_estimate_creation(self):
        """Verify CostEstimate can be created and converted"""
        estimate = CostEstimate(
            artifact_id="a-1",
            artifact_type="report",
            created_at="2026-02-12T10:00:00Z",
            provider="openai",
            model="gpt-4",
            tokens_estimated=1000,
            cost_usd=0.05
        )
        
        assert estimate.artifact_id == "a-1"
        assert estimate.cost_usd == 0.05
        
        # Test conversion
        data = estimate.to_dict()
        assert "artifact_id" in data
        assert data["cost_usd"] == 0.05

    def test_cost_actual_creation(self):
        """Verify CostActual can be created"""
        actual = CostActual(
            artifact_id="a-1",
            created_at="2026-02-12T10:05:00Z",
            provider="openai",
            model="gpt-4",
            input_tokens=900,
            output_tokens=150,
            total_tokens=1050,
            input_cost_usd=0.03,
            output_cost_usd=0.02,
            cost_usd=0.05
        )
        
        assert actual.input_tokens == 900
        assert actual.output_tokens == 150
        assert actual.total_tokens == 1050

    def test_cost_reconciliation_creation(self):
        """Verify CostReconciliation can be created"""
        reconciliation = CostReconciliation(
            artifact_id="a-1",
            reconciled_at="2026-02-12T10:10:00Z",
            estimated_cost=0.05,
            actual_cost=0.048,
            variance_usd=-0.002,
            variance_percent=-4.0,
            status="on_budget"
        )
        
        assert reconciliation.artifact_id == "a-1"
        assert reconciliation.status == "on_budget"
        assert reconciliation.variance_usd == -0.002


class TestCostRecording:
    """Test recording costs"""

    def test_record_estimate(self):
        """Verify recording cost estimate"""
        engine = CostReconciliationEngine()
        
        estimate = CostEstimate(
            artifact_id="a-1",
            artifact_type="report",
            created_at="2026-02-12T10:00:00Z",
            provider="openai",
            model="gpt-4",
            tokens_estimated=1000,
            cost_usd=0.05
        )
        
        success = engine.record_estimate(estimate)
        assert success is True
        assert "a-1" in engine.estimates
        assert engine.estimates["a-1"].cost_usd == 0.05

    def test_record_actual(self):
        """Verify recording actual cost"""
        engine = CostReconciliationEngine()
        
        actual = CostActual(
            artifact_id="a-1",
            created_at="2026-02-12T10:05:00Z",
            provider="openai",
            model="gpt-4",
            input_tokens=900,
            output_tokens=150,
            total_tokens=1050,
            input_cost_usd=0.03,
            output_cost_usd=0.02,
            cost_usd=0.051
        )
        
        success = engine.record_actual(actual)
        assert success is True
        assert "a-1" in engine.actuals
        assert engine.actuals["a-1"].cost_usd == 0.051

    def test_record_multiple_artifacts(self):
        """Verify recording costs for multiple artifacts"""
        engine = CostReconciliationEngine()
        
        for i in range(3):
            estimate = CostEstimate(
                artifact_id=f"a-{i+1}",
                artifact_type="report",
                created_at="2026-02-12T10:00:00Z",
                provider="openai",
                model="gpt-4",
                tokens_estimated=1000,
                cost_usd=0.05
            )
            engine.record_estimate(estimate)
        
        assert len(engine.estimates) == 3


class TestCostReconciliation:
    """Test cost reconciliation"""

    def test_reconcile_on_budget(self):
        """Verify reconciliation for on-budget scenario"""
        engine = CostReconciliationEngine()
        
        # Record estimate
        estimate = CostEstimate(
            artifact_id="a-1",
            artifact_type="report",
            created_at="2026-02-12T10:00:00Z",
            provider="openai",
            model="gpt-4",
            tokens_estimated=1000,
            cost_usd=0.50
        )
        engine.record_estimate(estimate)
        
        # Record actual (slightly less)
        actual = CostActual(
            artifact_id="a-1",
            created_at="2026-02-12T10:05:00Z",
            provider="openai",
            model="gpt-4",
            input_tokens=900,
            output_tokens=100,
            total_tokens=1000,
            input_cost_usd=0.30,
            output_cost_usd=0.18,
            cost_usd=0.48
        )
        engine.record_actual(actual)
        
        # Reconcile
        reconciliation = engine.reconcile("a-1", threshold_percent=10.0)
        
        assert reconciliation is not None, "Reconciliation should succeed"
        assert reconciliation.status == "on_budget", f"Status should be on_budget, got {reconciliation.status}"
        assert abs(reconciliation.variance_usd - (-0.02)) < 0.001, "Variance should be ~-0.02"
        assert reconciliation.variance_percent < 0, "Percentage should be negative"

    def test_reconcile_over_budget(self):
        """Verify reconciliation for over-budget scenario"""
        engine = CostReconciliationEngine()
        
        estimate = CostEstimate(
            artifact_id="a-2",
            artifact_type="report",
            created_at="2026-02-12T10:00:00Z",
            provider="openai",
            model="gpt-4",
            tokens_estimated=1000,
            cost_usd=0.50
        )
        engine.record_estimate(estimate)
        
        actual = CostActual(
            artifact_id="a-2",
            created_at="2026-02-12T10:05:00Z",
            provider="openai",
            model="gpt-4",
            input_tokens=1200,
            output_tokens=200,
            total_tokens=1400,
            input_cost_usd=0.40,
            output_cost_usd=0.20,
            cost_usd=0.60  # Over estimate
        )
        engine.record_actual(actual)
        
        reconciliation = engine.reconcile("a-2", threshold_percent=10.0)
        
        assert reconciliation is not None, "Reconciliation should succeed"
        assert reconciliation.status == "over_budget", f"Status should be over_budget, got {reconciliation.status}"
        assert abs(reconciliation.variance_usd - 0.10) < 0.001, "Variance should be ~0.10"
        assert reconciliation.variance_percent > 0, "Percentage should be positive"

    def test_reconcile_under_budget(self):
        """Verify reconciliation for under-budget scenario"""
        engine = CostReconciliationEngine()
        
        estimate = CostEstimate(
            artifact_id="a-3",
            artifact_type="report",
            created_at="2026-02-12T10:00:00Z",
            provider="openai",
            model="gpt-4",
            tokens_estimated=1000,
            cost_usd=0.50
        )
        engine.record_estimate(estimate)
        
        actual = CostActual(
            artifact_id="a-3",
            created_at="2026-02-12T10:05:00Z",
            provider="openai",
            model="gpt-4",
            input_tokens=500,
            output_tokens=50,
            total_tokens=550,
            input_cost_usd=0.15,
            output_cost_usd=0.03,
            cost_usd=0.35  # Under estimate
        )
        engine.record_actual(actual)
        
        reconciliation = engine.reconcile("a-3", threshold_percent=10.0)
        
        assert reconciliation is not None, "Reconciliation should succeed"
        assert reconciliation.status == "under_budget", f"Status should be under_budget, got {reconciliation.status}"
        assert abs(reconciliation.variance_usd - (-0.15)) < 0.001, "Variance should be ~-0.15"
        assert reconciliation.variance_percent < -10, "Percentage should be < -10"

    def test_reconcile_missing_estimate_returns_none(self):
        """Verify reconciliation returns None if estimate missing"""
        engine = CostReconciliationEngine()
        
        actual = CostActual(
            artifact_id="a-4",
            created_at="2026-02-12T10:05:00Z",
            provider="openai",
            model="gpt-4",
            input_tokens=900,
            output_tokens=100,
            total_tokens=1000,
            input_cost_usd=0.30,
            output_cost_usd=0.18,
            cost_usd=0.48
        )
        engine.record_actual(actual)
        
        reconciliation = engine.reconcile("a-4")
        assert reconciliation is None


class TestCostSummary:
    """Test cost summary generation"""

    def test_get_cost_summary_empty(self):
        """Verify cost summary with no data"""
        engine = CostReconciliationEngine()
        
        summary = engine.get_cost_summary()
        
        assert summary["total_estimated_usd"] == 0.0
        assert summary["total_actual_usd"] == 0.0
        assert summary["artifacts_tracked"] == 0

    def test_get_cost_summary_with_data(self):
        """Verify cost summary with multiple artifacts"""
        engine = CostReconciliationEngine()
        
        # Record 3 artifacts
        for i in range(3):
            estimate = CostEstimate(
                artifact_id=f"a-{i+1}",
                artifact_type="report",
                created_at="2026-02-12T10:00:00Z",
                provider="openai",
                model="gpt-4",
                tokens_estimated=1000,
                cost_usd=0.50
            )
            engine.record_estimate(estimate)
            
            actual = CostActual(
                artifact_id=f"a-{i+1}",
                created_at="2026-02-12T10:05:00Z",
                provider="openai",
                model="gpt-4",
                input_tokens=900,
                output_tokens=100,
                total_tokens=1000,
                input_cost_usd=0.30,
                output_cost_usd=0.18,
                cost_usd=0.50
            )
            engine.record_actual(actual)
        
        summary = engine.get_cost_summary()
        
        assert summary["total_estimated_usd"] == 1.50
        assert summary["total_actual_usd"] == 1.50
        assert summary["artifacts_tracked"] == 3

    def test_get_cost_summary_specific_artifacts(self):
        """Verify cost summary for specific artifacts"""
        engine = CostReconciliationEngine()
        
        # Record multiple artifacts
        for i in range(5):
            estimate = CostEstimate(
                artifact_id=f"a-{i+1}",
                artifact_type="report",
                created_at="2026-02-12T10:00:00Z",
                provider="openai",
                model="gpt-4",
                tokens_estimated=1000,
                cost_usd=0.10
            )
            engine.record_estimate(estimate)
        
        # Get summary for subset
        summary = engine.get_cost_summary(["a-1", "a-2"])
        
        assert summary["artifacts_tracked"] == 2


class TestProviderCosts:
    """Test provider-specific cost analysis"""

    def test_get_provider_costs(self):
        """Verify provider cost breakdown"""
        engine = CostReconciliationEngine()
        
        # OpenAI estimate
        estimate_openai = CostEstimate(
            artifact_id="a-1",
            artifact_type="report",
            created_at="2026-02-12T10:00:00Z",
            provider="openai",
            model="gpt-4",
            tokens_estimated=1000,
            cost_usd=0.50
        )
        engine.record_estimate(estimate_openai)
        
        # Anthropic estimate
        estimate_anthropic = CostEstimate(
            artifact_id="a-2",
            artifact_type="report",
            created_at="2026-02-12T10:00:00Z",
            provider="anthropic",
            model="claude-3",
            tokens_estimated=1000,
            cost_usd=0.80
        )
        engine.record_estimate(estimate_anthropic)
        
        openai_costs = engine.get_provider_costs("openai")
        assert openai_costs["estimated_usd"] == 0.50
        assert openai_costs["artifact_count"] == 1
        
        anthropic_costs = engine.get_provider_costs("anthropic")
        assert anthropic_costs["estimated_usd"] == 0.80
        assert anthropic_costs["artifact_count"] == 1


class TestReportGeneration:
    """Test report generation"""

    def test_export_report_json(self):
        """Verify JSON report export"""
        engine = CostReconciliationEngine()
        
        estimate = CostEstimate(
            artifact_id="a-1",
            artifact_type="report",
            created_at="2026-02-12T10:00:00Z",
            provider="openai",
            model="gpt-4",
            tokens_estimated=1000,
            cost_usd=0.50
        )
        engine.record_estimate(estimate)
        
        report = engine.export_report("json")
        data = json.loads(report)
        
        assert "total_estimated_usd" in data
        assert data["total_estimated_usd"] == 0.50

    def test_export_report_csv(self):
        """Verify CSV report export"""
        engine = CostReconciliationEngine()
        
        estimate = CostEstimate(
            artifact_id="a-1",
            artifact_type="report",
            created_at="2026-02-12T10:00:00Z",
            provider="openai",
            model="gpt-4",
            tokens_estimated=1000,
            cost_usd=0.50
        )
        engine.record_estimate(estimate)
        
        actual = CostActual(
            artifact_id="a-1",
            created_at="2026-02-12T10:05:00Z",
            provider="openai",
            model="gpt-4",
            input_tokens=900,
            output_tokens=100,
            total_tokens=1000,
            input_cost_usd=0.30,
            output_cost_usd=0.18,
            cost_usd=0.48
        )
        engine.record_actual(actual)
        engine.reconcile("a-1")
        
        report = engine.export_report("csv")
        assert "artifact_id,estimated_usd" in report
        assert "a-1" in report

    def test_export_report_markdown(self):
        """Verify Markdown report export"""
        engine = CostReconciliationEngine()
        
        estimate = CostEstimate(
            artifact_id="a-1",
            artifact_type="report",
            created_at="2026-02-12T10:00:00Z",
            provider="openai",
            model="gpt-4",
            tokens_estimated=1000,
            cost_usd=0.50
        )
        engine.record_estimate(estimate)
        
        report = engine.export_report("markdown")
        assert "# Cost Reconciliation Report" in report
        assert "Total Estimated" in report


class TestCostSingleton:
    """Test cost reconciliation singleton"""

    def test_get_cost_reconciliation_engine_singleton(self):
        """Verify get_cost_reconciliation_engine returns singleton"""
        engine1 = get_cost_reconciliation_engine()
        engine2 = get_cost_reconciliation_engine()
        
        assert engine1 is engine2, "Should return same instance"
