#!/usr/bin/env python3
"""
HR Contact System - Validation Test

Tests that all components work correctly.
"""

import sys
import json
from pathlib import Path

# Test suite
def test_imports():
    """Test that all modules import correctly"""
    print("\n1️⃣  Testing imports...")
    try:
        from backend.hr_contact_extractor import HRContactExtractor, ContactInfo
        print("   ✓ hr_contact_extractor")
        
        from backend.hr_search_params import (
            HRContactSearchBuilder, 
            HRContactSearchParams,
            PresetSearches,
            SeniorityLevel,
            ContactDataType
        )
        print("   ✓ hr_search_params")
        
        from backend.hr_contact_manager import HRContactManager, find_hr_contacts
        print("   ✓ hr_contact_manager")
        
        return True
    except Exception as e:
        print(f"   ❌ Import error: {e}")
        return False


def test_contact_info():
    """Test ContactInfo data structure"""
    print("\n2️⃣  Testing ContactInfo...")
    try:
        from backend.hr_contact_extractor import ContactInfo
        
        contact = ContactInfo(
            first_name="John",
            last_name="Smith",
            full_name="John Smith",
            job_title="Vice President of Human Resources",
            company_name="Tech Corp",
            email="john@techcorp.com",
            phone_direct="(410) 555-1234",
            phone_mobile="(410) 555-5678",
            linkedin_url="https://linkedin.com/in/johnsmith"
        )
        
        # Calculate completeness
        completeness = contact.calculate_completeness()
        
        assert completeness > 0, "Completeness should be > 0"
        assert contact.contact_methods_count >= 2, "Should have multiple contact methods"
        assert contact.full_name == "John Smith"
        
        print(f"   ✓ Created contact: {contact.full_name}")
        print(f"   ✓ Completeness: {completeness*100:.1f}%")
        print(f"   ✓ Contact methods: {contact.contact_methods_count}")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_hr_role_detection():
    """Test HR role detection"""
    print("\n3️⃣  Testing HR role detection...")
    try:
        from backend.hr_contact_extractor import HRContactExtractor
        
        extractor = HRContactExtractor()
        
        # Test various titles
        test_cases = [
            ("Vice President of Human Resources", True),
            ("HR Manager", True),
            ("Director of Human Resources", True),
            ("Chief Human Resources Officer", True),
            ("Sales Manager", False),
            ("IT Director", False),
            ("Chief People Officer", True),
            ("HR Business Partner", True),
        ]
        
        all_passed = True
        for title, expected in test_cases:
            result = extractor.is_hr_title(title)
            if result == expected:
                print(f"   ✓ '{title}' → {result}")
            else:
                print(f"   ❌ '{title}' expected {expected}, got {result}")
                all_passed = False
        
        return all_passed
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_extractor():
    """Test contact extraction"""
    print("\n4️⃣  Testing contact extraction...")
    try:
        from backend.hr_contact_extractor import HRContactExtractor
        
        extractor = HRContactExtractor()
        
        raw_data = {
            "first_name": "Sarah",
            "last_name": "Johnson",
            "job_title": "Director of Human Resources",
            "company_name": "Finance Corp",
            "email": "sarah.j@financecorp.com",
            "phone_data": "Office: (410) 555-0123, Mobile: (410) 555-5555, ext. 1234"
        }
        
        contact = extractor.extract_contact_info(raw_data)
        
        assert contact is not None, "Should extract HR contact"
        assert contact.email == "sarah.j@financecorp.com"
        assert contact.first_name == "Sarah"
        
        print(f"   ✓ Extracted: {contact.full_name}")
        print(f"   ✓ Email: {contact.email}")
        print(f"   ✓ Company: {contact.company_name}")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_search_builder():
    """Test search parameter builder"""
    print("\n5️⃣  Testing search builder...")
    try:
        from backend.hr_search_params import HRContactSearchBuilder, ContactDataType
        
        params = (HRContactSearchBuilder()
            .executive_and_above()
            .with_company_size(100, 5000)
            .require_contact_data(ContactDataType.EMAIL)
            .limit(50)
            .build())
        
        assert params.max_results == 50
        assert params.company_size_min == 100
        assert params.company_size_max == 5000
        assert len(params.seniority_levels) > 0
        
        print(f"   ✓ Built search with {len(params.seniority_levels)} seniority levels")
        print(f"   ✓ Company size: {params.company_size_min}-{params.company_size_max}")
        print(f"   ✓ Max results: {params.max_results}")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_preset_searches():
    """Test preset searches"""
    print("\n6️⃣  Testing preset searches...")
    try:
        from backend.hr_search_params import PresetSearches
        
        presets = [
            ("CHRO with contact", PresetSearches.chro_contacts_with_contact_data()),
            ("VP HR full contact", PresetSearches.vp_hr_with_full_contact()),
            ("Mid-market directors", PresetSearches.mid_market_hr_directors()),
            ("Enrichment targets", PresetSearches.high_priority_enrichment_targets()),
        ]
        
        for name, params in presets:
            assert params is not None, f"Preset {name} is None"
            print(f"   ✓ {name}")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_deduplication():
    """Test deduplication"""
    print("\n7️⃣  Testing deduplication...")
    try:
        from backend.hr_contact_extractor import HRContactExtractor, ContactInfo
        
        extractor = HRContactExtractor()
        
        # Create duplicate contacts
        contact1 = ContactInfo(
            first_name="John",
            last_name="Smith",
            full_name="John Smith",
            job_title="HR Manager",
            company_name="Corp A",
            email="john.smith@corpa.com"
        )
        
        contact2 = ContactInfo(
            first_name="John",
            last_name="Smith",
            full_name="John Smith",
            job_title="HR Manager",
            company_name="Corp A",
            email="john.smith@corpa.com",
            phone_direct="(410) 555-1234"
        )
        
        extractor.add_contact(contact1)
        extractor.add_contact(contact2)
        
        # Deduplicate
        unique = extractor.deduplicate()
        
        assert len(unique) == 1, f"Should have 1 unique contact, got {len(unique)}"
        assert len(extractor.duplicates) == 1, "Should find 1 duplicate group"
        
        print(f"   ✓ Detected duplicate group")
        print(f"   ✓ Merged to 1 unique contact")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_completeness_scoring():
    """Test data completeness scoring"""
    print("\n8️⃣  Testing completeness scoring...")
    try:
        from backend.hr_contact_extractor import ContactInfo
        
        # Incomplete contact
        incomplete = ContactInfo(
            first_name="Jane",
            last_name="Doe",
            full_name="Jane Doe"
        )
        score1 = incomplete.calculate_completeness()
        
        # Complete contact
        complete = ContactInfo(
            first_name="Jane",
            last_name="Doe",
            full_name="Jane Doe",
            job_title="VP HR",
            company_name="Tech Corp",
            email="jane@techcorp.com",
            phone_direct="(410) 555-1234",
            phone_mobile="(410) 555-5678",
            linkedin_url="https://linkedin.com/in/janedoe"
        )
        score2 = complete.calculate_completeness()
        
        assert score1 < score2, "Complete should score higher"
        assert 0 <= score1 <= 1, "Score should be 0-1"
        assert 0 <= score2 <= 1, "Score should be 0-1"
        
        print(f"   ✓ Incomplete: {score1*100:.1f}%")
        print(f"   ✓ Complete: {score2*100:.1f}%")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_manager():
    """Test HR Contact Manager"""
    print("\n9️⃣  Testing HR Contact Manager...")
    try:
        from backend.hr_contact_manager import HRContactManager
        
        manager = HRContactManager()
        
        # Create some test data
        test_data = [
            {
                "first_name": "Sarah",
                "last_name": "Johnson",
                "job_title": "Director of Human Resources",
                "company_name": "Tech Corp",
                "email": "sarah@techcorp.com"
            },
            {
                "first_name": "John",
                "last_name": "Smith",
                "job_title": "HR Manager",
                "company_name": "Finance Corp",
                "email": "john@financecorp.com"
            }
        ]
        
        # Search using builder - extract without filtering
        results = manager.search_from_employer_data(test_data)
        
        # Just test basic functionality
        assert isinstance(results, list)
        print(f"   ✓ Search returns list: {type(results)}")
        
        # Get statistics
        stats = manager.get_statistics()
        assert isinstance(stats, dict)
        print(f"   ✓ Statistics work: {len(stats)} metrics")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_exports():
    """Test export functionality"""
    print("\n🔟 Testing exports...")
    try:
        from backend.hr_contact_extractor import ContactInfo
        from backend.hr_contact_manager import HRContactManager
        
        manager = HRContactManager()
        
        # Create test contact
        contact = ContactInfo(
            first_name="Jane",
            last_name="Doe",
            full_name="Jane Doe",
            job_title="VP HR",
            company_name="Tech Corp",
            email="jane@techcorp.com"
        )
        contact.calculate_completeness()
        
        manager.contacts = [contact]
        manager.last_search_results = [contact]
        
        # Test JSON export
        json_str = manager.export_results(format="json")
        json_data = json.loads(json_str)
        
        assert isinstance(json_data, list)
        assert len(json_data) == 1
        assert json_data[0]["email"] == "jane@techcorp.com"
        
        print(f"   ✓ JSON export works")
        
        # Test CSV export
        csv_str = manager.export_results(format="csv")
        assert "Jane" in csv_str
        assert "jane@techcorp.com" in csv_str
        
        print(f"   ✓ CSV export works")
        
        # Test dict conversion
        contact_dict = contact.to_dict()
        assert contact_dict["full_name"] == "Jane Doe"
        
        print(f"   ✓ Dict conversion works")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("HR CONTACT SYSTEM - VALIDATION TESTS")
    print("="*70)
    
    tests = [
        test_imports,
        test_contact_info,
        test_hr_role_detection,
        test_extractor,
        test_search_builder,
        test_preset_searches,
        test_deduplication,
        test_completeness_scoring,
        test_manager,
        test_exports,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\n✅ Passed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed! System is ready to use.")
        print("\nQuick start:")
        print("  1. Interactive:  python hr_contact_search.py")
        print("  2. Examples:     python hr_contact_examples.py")
        print("  3. In code:      from backend.hr_contact_manager import find_hr_contacts")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
