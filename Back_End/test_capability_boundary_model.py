"""
Unit tests for Capability Boundary Model
Minimum 6 tests, covering DIGITAL, PHYSICAL, HYBRID classification
"""

import pytest
import json
from pathlib import Path
from datetime import datetime

from Back_End.capability_boundary_model import (
    CapabilityBoundaryModel,
    Capability,
    classify_task,
)
from Back_End.learning_signal_writer import get_signal_writer


class TestCapabilityBoundaryModel:
    """Test capability classification"""
    
    @pytest.fixture
    def model(self):
        """Create model instance for testing"""
        return CapabilityBoundaryModel()
    
    @pytest.fixture
    def signal_writer(self, tmp_path):
        """Create signal writer with temporary file"""
        log_file = tmp_path / "test_signals.jsonl"
        return get_signal_writer(str(log_file))
    
    # ====================
    # DIGITAL TESTS
    # ====================
    
    def test_classify_digital_email_task(self, model):
        """Test 1: Classify email task as DIGITAL"""
        result = model.classify_task(
            "Send email to customer with pricing information"
        )
        
        assert result.capability == Capability.DIGITAL
        assert result.confidence > 0.5
        assert "email" in result.evidence_keywords
        assert len(result.evidence_keywords) > 0
        print(f"\n✅ Test 1 passed: {result.reasoning}")
    
    def test_classify_digital_web_scrape_task(self, model):
        """Test 2: Classify web scraping task as DIGITAL"""
        result = model.classify_task(
            "Navigate to competitor website and extract pricing data from the table"
        )
        
        assert result.capability == Capability.DIGITAL
        assert result.confidence > 0.5
        assert any(kw in result.evidence_keywords for kw in ["website", "extract", "data"])
        print(f"\n✅ Test 2 passed: {result.reasoning}")
    
    def test_classify_digital_form_task(self, model):
        """Test 3: Classify form submission task as DIGITAL"""
        result = model.classify_task(
            "Fill out the contact form with company details and submit"
        )
        
        assert result.capability == Capability.DIGITAL
        assert result.confidence > 0.5
        assert any(kw in result.evidence_keywords for kw in ["form", "submit"])
        print(f"\n✅ Test 3 passed: {result.reasoning}")
    
    # ====================
    # PHYSICAL TESTS
    # ====================
    
    def test_classify_physical_shipping_task(self, model):
        """Test 4: Classify shipping task as PHYSICAL"""
        result = model.classify_task(
            "Ship the package via fedex to the customer address"
        )
        
        assert result.capability == Capability.PHYSICAL
        assert result.confidence > 0.5
        assert any(kw in result.evidence_keywords for kw in ["ship", "package"])
        print(f"\n✅ Test 4 passed: {result.reasoning}")
    
    def test_classify_physical_signing_task(self, model):
        """Test 5: Classify signing task as PHYSICAL"""
        result = model.classify_task(
            "Sign the contract and send it back to legal"
        )
        
        assert result.capability == Capability.PHYSICAL
        assert result.confidence > 0.5
        assert "sign" in result.evidence_keywords
        print(f"\n✅ Test 5 passed: {result.reasoning}")
    
    def test_classify_physical_call_task(self, model):
        """Test 6: Classify phone call task as PHYSICAL"""
        result = model.classify_task(
            "Call the customer support team to discuss the contract terms"
        )
        
        assert result.capability == Capability.PHYSICAL
        assert result.confidence > 0.5
        assert "call" in result.evidence_keywords
        print(f"\n✅ Test 6 passed: {result.reasoning}")
    
    # ====================
    # HYBRID TESTS
    # ====================
    
    def test_classify_hybrid_ambiguous_task(self, model):
        """Test 7: Classify ambiguous task as HYBRID"""
        result = model.classify_task(
            "Review and approve the customer request"
        )
        
        assert result.capability == Capability.HYBRID
        # Ambiguous tasks have lower confidence
        assert result.confidence <= 0.7
        print(f"\n✅ Test 7 passed: {result.reasoning}")
    
    def test_classify_hybrid_handoff_task(self, model):
        """Test 8: Classify handoff task as HYBRID"""
        result = model.classify_task(
            "Extract data from website and handoff to processing team for approval"
        )
        
        assert result.capability == Capability.HYBRID
        print(f"\n✅ Test 8 passed: {result.reasoning}")
    
    # ====================
    # SIGNAL EMISSION TESTS
    # ====================
    
    def test_emit_signal_on_classification(self, model, signal_writer):
        """Test 9: Verify signal is emitted on classification"""
        result = model.classify_task("Send email to customer")
        
        # Emit signal
        signal_writer.emit_classification_signal(result)
        
        # Verify signal was written
        signals = signal_writer.read_signals()
        assert len(signals) == 1
        
        signal = signals[0]
        assert signal["signal_type"] == "capability_classified"
        assert signal["signal_layer"] == "cognition"
        assert signal["signal_source"] == "capability_model"
        assert signal["data"]["capability"] == "digital"
        assert signal["data"]["confidence"] > 0.5
        assert "email" in signal["data"]["evidence_keywords"]
        print(f"\n✅ Test 9 passed: Signal emitted and verified")
    
    def test_multiple_signals_accumulated(self, signal_writer, model):
        """Test 10: Verify multiple signals are accumulated"""
        # Emit 3 signals
        tasks = [
            "Send email to customer",
            "Call the support team",
            "Extract data from website",
        ]
        
        for task in tasks:
            result = model.classify_task(task)
            signal_writer.emit_classification_signal(result)
        
        # Verify all signals are stored
        signals = signal_writer.read_signals()
        assert len(signals) == 3
        
        # Verify signal types
        capabilities = [s["data"]["capability"] for s in signals]
        assert "digital" in capabilities
        assert "physical" in capabilities
        print(f"\n✅ Test 10 passed: Multiple signals accumulated")
    
    def test_signal_statistics(self, signal_writer, model):
        """Test 11: Verify signal statistics generation"""
        # Emit signals with different capabilities
        test_cases = [
            ("Send email", Capability.DIGITAL),
            ("Browse website", Capability.DIGITAL),
            ("Call customer", Capability.PHYSICAL),
            ("Ship package", Capability.PHYSICAL),
            ("Review and approve", Capability.HYBRID),
        ]
        
        for task, expected_capability in test_cases:
            result = model.classify_task(task)
            signal_writer.emit_classification_signal(result)
        
        # Get statistics
        stats = signal_writer.get_statistics()
        
        assert stats["total_signals"] == 5
        assert stats["digital_count"] == 2
        assert stats["physical_count"] == 2
        assert stats["hybrid_count"] == 1
        assert stats["avg_confidence"] > 0.5
        assert stats["digital_percentage"] == 40.0
        assert stats["physical_percentage"] == 40.0
        assert stats["hybrid_percentage"] == 20.0
        print(f"\n✅ Test 11 passed: Statistics verified - {stats}")
    
    # ====================
    # EDGE CASE TESTS
    # ====================
    
    def test_classify_empty_task_description(self, model):
        """Test 12: Handle empty task description"""
        result = model.classify_task("")
        
        assert result.capability == Capability.HYBRID
        assert result.confidence <= 0.5
        print(f"\n✅ Test 12 passed: Empty task handled as HYBRID")
    
    def test_classify_vague_task(self, model):
        """Test 13: Handle vague task description"""
        result = model.classify_task("Do something with the thing")
        
        assert result.capability == Capability.HYBRID
        assert result.confidence <= 0.5
        print(f"\n✅ Test 13 passed: Vague task handled as HYBRID")
    
    def test_classify_complex_task(self, model):
        """Test 14: Handle complex multi-step task"""
        result = model.classify_task(
            "Navigate to competitor website, extract pricing data, email results to team, and request approval"
        )
        
        # Complex tasks might be HYBRID due to approval requirement
        assert result.capability in [Capability.DIGITAL, Capability.HYBRID]
        print(f"\n✅ Test 14 passed: Complex task classified as {result.capability.value}")
    
    # ====================
    # CONFIDENCE TESTS
    # ====================
    
    def test_high_confidence_digital(self, model):
        """Test 15: Strong digital signal has high confidence"""
        result = model.classify_task(
            "Send email, download file, extract data, submit form, and take screenshot"
        )
        
        assert result.capability == Capability.DIGITAL
        assert result.confidence > 0.7
        print(f"\n✅ Test 15 passed: High confidence digital task (conf={result.confidence})")
    
    def test_low_confidence_ambiguous(self, model):
        """Test 16: Ambiguous task has lower confidence"""
        result = model.classify_task(
            "Handle the situation appropriately"
        )
        
        assert result.capability == Capability.HYBRID
        assert result.confidence <= 0.5
        print(f"\n✅ Test 16 passed: Low confidence ambiguous task (conf={result.confidence})")
    
    # ====================
    # CONVENIENCE FUNCTION TESTS
    # ====================
    
    def test_convenience_function(self):
        """Test 17: Global convenience function works"""
        result = classify_task("Send email to customer with invoice")
        
        assert result is not None
        assert result.capability == Capability.DIGITAL
        assert "email" in result.evidence_keywords
        print(f"\n✅ Test 17 passed: Convenience function works")


def run_all_tests():
    """Run all tests with output"""
    print("\n" + "="*70)
    print("RUNNING CAPABILITY BOUNDARY MODEL TESTS")
    print("="*70)
    
    pytest.main([__file__, "-v", "-s"])
    
    print("\n" + "="*70)
    print("ALL TESTS COMPLETED")
    print("="*70)


if __name__ == "__main__":
    run_all_tests()

