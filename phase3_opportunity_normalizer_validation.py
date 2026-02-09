"""
Phase 3 Step 2 Validation: Opportunity Normalizer
Tests deterministic opportunity creation from collected items.
"""

from backend.mission_control.opportunity_normalizer import OpportunityNormalizer


def test_directory_style_items():
    """Test: Directory-style items create multiple opportunities."""
    print("\n🧪 Test 1: Directory-style Items → Multiple Opportunities")
    
    normalizer = OpportunityNormalizer()
    
    items = [
        {
            "title": "Tech Company Directory",
            "content": "Listing of technology companies",
            "url": "https://companies.example.com/tech",
            "contact": "contact@companies.com"
        },
        {
            "title": "Startups Index",
            "content": "Database of startup companies",
            "url": "https://companies.example.com/startups",
            "email": "info@index.com"
        },
        {
            "title": "Enterprise Registry",
            "content": "Catalog of enterprise solutions",
            "url": "https://companies.example.com/enterprise",
            "phone": "1-800-COMPANY"
        }
    ]
    
    opportunities = normalizer.normalize(
        mission_id="test-directory",
        mission_objective="Find company directories",
        items_collected=items,
        context={
            "page_url": "https://companies.example.com",
            "page_title": "Company Directory"
        }
    )
    
    print(f"   ✓ Items: {len(items)}")
    print(f"   ✓ Opportunities created: {len(opportunities)}")
    print(f"   ✓ Types detected: {set(o.opportunity_type for o in opportunities)}")
    
    for idx, opp in enumerate(opportunities, 1):
        print(f"     [{idx}] {opp.opportunity_type}: {opp.title} (confidence={opp.confidence:.2f})")
        print(f"          Signals: contact={opp.signals.has_contact}, price={opp.signals.has_price}, deadline={opp.signals.has_deadline}")
    
    assert len(opportunities) == 3, "Should create 3 opportunities"
    assert all(o.mission_id == "test-directory" for o in opportunities), "All should have mission_id"
    assert all(o.opportunity_type == "directory" for o in opportunities), "All should be classified as directory"
    print("   ✅ PASSED\n")


def test_empty_items():
    """Test: Empty items list returns zero opportunities."""
    print("🧪 Test 2: Empty Items → Zero Opportunities")
    
    normalizer = OpportunityNormalizer()
    
    opportunities = normalizer.normalize(
        mission_id="test-empty",
        mission_objective="Find items",
        items_collected=[],
        context={"page_url": "https://example.com"}
    )
    
    print(f"   ✓ Items: 0")
    print(f"   ✓ Opportunities created: {len(opportunities)}")
    
    assert len(opportunities) == 0, "Should create 0 opportunities"
    print("   ✅ PASSED\n")


def test_mixed_quality_items():
    """Test: Mixed quality items show confidence variance."""
    print("🧪 Test 3: Mixed Quality Items → Confidence Variance")
    
    normalizer = OpportunityNormalizer()
    
    items = [
        {
            "title": "High Quality Job Posting",
            "content": "Senior developer role with competitive salary",
            "url": "https://jobs.example.com/dev",
            "email": "hr@example.com",
            "phone": "555-1234",
            "price": "$120k-150k"
        },
        {
            "title": "Medium Lead",
            "content": "Some contact info available",
            "url": "https://example.com/lead"
        },
        {
            "title": "X",
            "content": ""
        }
    ]
    
    opportunities = normalizer.normalize(
        mission_id="test-mixed",
        mission_objective="Find mixed opportunities",
        items_collected=items
    )
    
    print(f"   ✓ Items: {len(items)}")
    print(f"   ✓ Opportunities created: {len(opportunities)}")
    
    confidences = [o.confidence for o in opportunities]
    print(f"   ✓ Confidence range: {min(confidences):.2f} - {max(confidences):.2f}")
    print(f"   ✓ Average confidence: {sum(confidences)/len(confidences):.2f}")
    
    for idx, opp in enumerate(opportunities, 1):
        print(f"     [{idx}] {opp.title[:30]}... confidence={opp.confidence:.2f}")
    
    # High quality should have higher confidence
    high_quality = opportunities[0]
    medium_quality = opportunities[1]
    
    assert high_quality.confidence > medium_quality.confidence, "High quality should have higher confidence"
    assert high_quality.signals.has_contact == True, "Should detect contact signal"
    assert high_quality.signals.has_price == True, "Should detect price signal"
    print("   ✅ PASSED\n")


def test_job_classification():
    """Test: Job-related items classified as 'job'."""
    print("🧪 Test 4: Job Classification")
    
    normalizer = OpportunityNormalizer()
    
    items = [
        {
            "title": "Software Engineer Position",
            "content": "We are hiring senior software engineers"
        },
        {
            "title": "Marketing Manager Vacancy",
            "content": "Exciting role for marketing professional"
        },
        {
            "title": "Recruitment Drive",
            "content": "Employment opportunities available"
        }
    ]
    
    opportunities = normalizer.normalize(
        mission_id="test-jobs",
        mission_objective="Find job postings",
        items_collected=items
    )
    
    types = [o.opportunity_type for o in opportunities]
    job_count = sum(1 for t in types if t == "job")
    
    print(f"   ✓ Items: {len(items)}")
    print(f"   ✓ Opportunities created: {len(opportunities)}")
    print(f"   ✓ Classified as 'job': {job_count}/{len(opportunities)}")
    
    assert job_count >= 2, "Should classify at least 2 as jobs"
    print("   ✅ PASSED\n")


def test_signal_detection():
    """Test: Signals properly detected from item content."""
    print("🧪 Test 5: Signal Detection")
    
    normalizer = OpportunityNormalizer()
    
    item_with_all_signals = {
        "title": "Complete Opportunity",
        "content": "Email me at john@example.com, deadline is March 31, price is $500",
        "url": "https://example.com"
    }
    
    opportunities = normalizer.normalize(
        mission_id="test-signals",
        mission_objective="Test signals",
        items_collected=[item_with_all_signals]
    )
    
    assert len(opportunities) == 1, "Should create 1 opportunity"
    opp = opportunities[0]
    
    print(f"   ✓ Item: {item_with_all_signals['title']}")
    print(f"   ✓ Signals detected:")
    print(f"     - has_contact: {opp.signals.has_contact}")
    print(f"     - has_price: {opp.signals.has_price}")
    print(f"     - has_deadline: {opp.signals.has_deadline}")
    
    assert opp.signals.has_contact == True, "Should detect email"
    assert opp.signals.has_price == True, "Should detect price"
    assert opp.signals.has_deadline == True, "Should detect deadline"
    print("   ✅ PASSED\n")


def test_traceability():
    """Test: Raw item references preserve traceability."""
    print("🧪 Test 6: Traceability & Raw Item References")
    
    normalizer = OpportunityNormalizer()
    
    items = [
        {"title": "Item 1", "content": "Content 1"},
        {"title": "Item 2", "content": "Content 2"},
        {"title": "Item 3", "content": "Content 3"}
    ]
    
    opportunities = normalizer.normalize(
        mission_id="test-trace",
        mission_objective="Test traceability",
        items_collected=items
    )
    
    print(f"   ✓ Items: {len(items)}")
    print(f"   ✓ Opportunities: {len(opportunities)}")
    print(f"   ✓ Raw item references:")
    
    for opp in opportunities:
        print(f"     - {opp.raw_item_ref} → {opp.title}")
        assert opp.raw_item_ref.startswith("item_"), "Reference should start with 'item_'"
        assert opp.mission_id == "test-trace", "Mission ID should be preserved"
    
    print("   ✅ PASSED\n")


def test_unknown_type_fallback():
    """Test: Unknown items classified as 'unknown'."""
    print("🧪 Test 7: Unknown Type Fallback")
    
    normalizer = OpportunityNormalizer()
    
    items = [
        {"title": "Random Article", "content": "Some random content about general topics"}
    ]
    
    opportunities = normalizer.normalize(
        mission_id="test-unknown",
        mission_objective="Find anything",
        items_collected=items
    )
    
    assert len(opportunities) == 1, "Should create 1 opportunity"
    opp = opportunities[0]
    
    print(f"   ✓ Item: {opp.title}")
    print(f"   ✓ Type: {opp.opportunity_type}")
    print(f"   ✓ Confidence: {opp.confidence:.2f}")
    
    assert opp.opportunity_type == "unknown" or opp.confidence < 0.7, "Should be unknown or low confidence"
    print("   ✅ PASSED\n")


def test_opportunity_object_structure():
    """Test: Opportunity objects have correct structure."""
    print("🧪 Test 8: Opportunity Object Structure")
    
    normalizer = OpportunityNormalizer()
    
    items = [
        {"title": "Test Opportunity", "content": "Test content", "url": "https://example.com"}
    ]
    
    opportunities = normalizer.normalize(
        mission_id="test-structure",
        mission_objective="Test",
        items_collected=items
    )
    
    assert len(opportunities) == 1, "Should create 1 opportunity"
    opp = opportunities[0]
    
    # Verify all required fields
    required_fields = [
        "opportunity_id", "mission_id", "source", "opportunity_type",
        "title", "description", "url", "signals", "raw_item_ref", "confidence"
    ]
    
    opp_dict = opp.to_dict()
    
    print(f"   ✓ Checking required fields:")
    for field in required_fields:
        assert field in opp_dict, f"Missing field: {field}"
        print(f"     - {field}: ✓")
    
    # Verify structure
    assert len(opp.opportunity_id) > 0, "opportunity_id should be non-empty"
    assert 0.0 <= opp.confidence <= 1.0, "Confidence should be in [0, 1]"
    assert isinstance(opp.signals.has_contact, bool), "Signals should be boolean"
    
    print("   ✅ PASSED\n")


def main():
    """Run all validation tests."""
    print("\n" + "="*60)
    print("PHASE 3 STEP 2: OPPORTUNITY NORMALIZER VALIDATION")
    print("="*60)
    
    try:
        test_directory_style_items()
        test_empty_items()
        test_mixed_quality_items()
        test_job_classification()
        test_signal_detection()
        test_traceability()
        test_unknown_type_fallback()
        test_opportunity_object_structure()
        
        print("="*60)
        print("✅ ALL VALIDATION TESTS PASSED")
        print("="*60)
        print("\n📊 Summary:")
        print("   ✓ Directory-style items create multiple opportunities")
        print("   ✓ Empty items return zero opportunities")
        print("   ✓ Confidence properly reflects item quality")
        print("   ✓ Job classification works")
        print("   ✓ Contact/price/deadline signals detected")
        print("   ✓ Raw item traceability preserved")
        print("   ✓ Unknown types handled gracefully")
        print("   ✓ All opportunity fields present")
        
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
