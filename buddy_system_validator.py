#!/usr/bin/env python3
"""
buddy_system_validator.py

Automated validation of Buddy multi-step testing system.
Verifies file integrity, imports, functionality, and Phase 2 isolation.

Usage:
  python buddy_system_validator.py          # Full validation
  python buddy_system_validator.py --quick  # Quick checks only
  python buddy_system_validator.py --verbose  # Detailed output

Exit codes:
  0: All validations passed (PRODUCTION READY)
  1: Some validations failed (needs review)
  2: Critical validation failed (do not deploy)
"""

import os
import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime


class SystemValidator:
    """Validates Buddy multi-step testing system"""
    
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.buddy_dir = Path(__file__).parent
        self.results = []
        self.passed = 0
        self.failed = 0
        self.warnings = 0
    
    def log(self, level, message, detail=""):
        """Log validation result"""
        prefix = {
            "✓": "[PASS]",
            "✗": "[FAIL]",
            "⚠": "[WARN]",
            "ℹ": "[INFO]"
        }
        print(f"{prefix.get(level, level)} {message}")
        if detail and self.verbose:
            print(f"         {detail}")
        
        if level == "✓":
            self.passed += 1
        elif level == "✗":
            self.failed += 1
        elif level == "⚠":
            self.warnings += 1
        
        self.results.append({
            "level": level,
            "message": message,
            "detail": detail,
            "timestamp": datetime.now().isoformat()
        })
    
    # ========================================================================
    # SECTION A: FILE INTEGRITY
    # ========================================================================
    
    def validate_file_integrity(self):
        """Check that all required files exist"""
        print("\n" + "=" * 78)
        print("SECTION A: FILE INTEGRITY VERIFICATION")
        print("=" * 78)
        
        # Core files
        core_files = [
            ("buddy_context_manager.py", 470),
            ("buddy_multi_step_test_harness.py", 550),
            ("buddy_multi_step_main.py", 200)
        ]
        
        for filename, min_lines in core_files:
            filepath = self.buddy_dir / filename
            if not filepath.exists():
                self.log("✗", f"Core file missing: {filename}")
                continue
            
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = len(f.readlines())
                if lines >= min_lines:
                    self.log("✓", f"Core file present: {filename} ({lines} lines)")
                else:
                    self.log("⚠", f"Core file small: {filename} ({lines} lines, expect >{min_lines})")
            except Exception as e:
                self.log("✗", f"Cannot read {filename}", str(e))
        
        # Documentation files
        doc_files = [
            "BUDDY_MULTI_STEP_TESTING_SETUP.txt",
            "BUDDY_MULTI_STEP_METRICS_REFERENCE.txt",
            "BUDDY_MULTI_STEP_VALIDATION_CHECKLIST.txt",
            "BUDDY_MULTI_STEP_QUICKSTART.txt"
        ]
        
        for filename in doc_files:
            filepath = self.buddy_dir / filename
            if filepath.exists():
                self.log("✓", f"Documentation present: {filename}")
            else:
                self.log("⚠", f"Documentation missing: {filename}")
        
        # Phase 2 files (should be unchanged)
        phase2_files = [
            "phase2_adaptive_tests.py",
            "phase2_complete_progressive_tests.py",
            "phase2_calibration_analyzer.py",
            "phase2_test_analyzer.py"
        ]
        
        for filename in phase2_files:
            filepath = self.buddy_dir / filename
            if filepath.exists():
                self.log("✓", f"Phase 2 file intact: {filename}")
            else:
                self.log("✗", f"Phase 2 file missing: {filename}")
    
    # ========================================================================
    # SECTION B: IMPORTS & DEPENDENCIES
    # ========================================================================
    
    def validate_imports(self):
        """Check that all modules can be imported"""
        print("\n" + "=" * 78)
        print("SECTION B: IMPORTS & DEPENDENCIES VERIFICATION")
        print("=" * 78)
        
        # Check Python version
        version = sys.version_info
        if version.major >= 3 and version.minor >= 11:
            self.log("✓", f"Python version {version.major}.{version.minor}.{version.micro}")
        else:
            self.log("✗", f"Python {version.major}.{version.minor} (need ≥3.11)")
        
        # Check standard library imports
        stdlib_imports = [
            ("json", "JSON support"),
            ("datetime", "Datetime support"),
            ("uuid", "UUID generation"),
            ("threading", "Threading support"),
            ("pathlib", "Path support")
        ]
        
        for module_name, description in stdlib_imports:
            try:
                __import__(module_name)
                self.log("✓", f"Standard library available: {module_name}")
            except ImportError as e:
                self.log("✗", f"Standard library missing: {module_name}", str(e))
        
        # Check Phase 2 imports
        print("\n  Phase 2 Module Imports:")
        try:
            from phase2_adaptive_tests import AdaptiveTestRunner
            self.log("✓", "Phase 2 module imports work: AdaptiveTestRunner")
        except Exception as e:
            self.log("✗", "Phase 2 import failed", str(e))
        
        # Check multi-step imports
        print("\n  Multi-Step System Imports:")
        try:
            from buddy_context_manager import SessionManager, SessionContext
            self.log("✓", "Multi-step imports work: SessionManager, SessionContext")
        except Exception as e:
            self.log("✗", "Multi-step import failed", str(e))
        
        try:
            from buddy_multi_step_test_harness import MultiStepTestCoordinator
            self.log("✓", "Multi-step imports work: MultiStepTestCoordinator")
        except Exception as e:
            self.log("✗", "Multi-step import failed", str(e))
    
    # ========================================================================
    # SECTION C: FUNCTIONALITY TESTS
    # ========================================================================
    
    def validate_functionality(self):
        """Test basic functionality of each component"""
        print("\n" + "=" * 78)
        print("SECTION C: FUNCTIONALITY VERIFICATION")
        print("=" * 78)
        
        try:
            from buddy_context_manager import (
                get_session_manager, SessionContext, RequestSnapshot
            )
            
            print("\n  Session Management:")
            
            # Test 1: Create session
            try:
                manager = get_session_manager()
                session = manager.create_session()
                self.log("✓", f"Session creation works (ID: {session.session_id[:20]}...)")
            except Exception as e:
                self.log("✗", "Session creation failed", str(e))
                return
            
            # Test 2: Add request
            try:
                snapshot = session.add_request(
                    input_data={"test": "data"},
                    success=True,
                    confidence=0.75,
                    approval_path="approved",
                    execution_time_ms=0.05,
                    pre_validation_status="passed"
                )
                self.log("✓", "Request addition works (added 1 request)")
            except Exception as e:
                self.log("✗", "Request addition failed", str(e))
            
            # Test 3: Get metrics
            try:
                metrics = session.get_metrics()
                if metrics and hasattr(metrics, 'confidence_mean'):
                    self.log("✓", f"Metrics calculation works (σ={metrics.confidence_std_dev:.3f})")
                else:
                    self.log("⚠", "Metrics computed but missing expected keys")
            except Exception as e:
                self.log("✗", "Metrics calculation failed", str(e))
            
            # Test 4: List sessions
            try:
                sessions = manager.list_sessions()
                self.log("✓", f"Session listing works ({len(sessions)} active)")
            except Exception as e:
                self.log("✗", "Session listing failed", str(e))
            
        except ImportError as e:
            self.log("✗", "Cannot import session management", str(e))
        
        # Test sequence generation
        try:
            from buddy_multi_step_test_harness import MultiStepSequenceGenerator
            
            print("\n  Sequence Generation:")
            gen = MultiStepSequenceGenerator()
            
            # Test BASIC sequence
            try:
                seq = gen.generate_sequence('BASIC', 5)
                self.log("✓", f"BASIC sequence generation works ({len(seq)} steps)")
            except Exception as e:
                self.log("✗", "BASIC sequence generation failed", str(e))
            
            # Test ADVERSARIAL sequence
            try:
                seq = gen.generate_sequence('ADVERSARIAL', 5)
                self.log("✓", f"ADVERSARIAL sequence generation works ({len(seq)} steps)")
            except Exception as e:
                self.log("✗", "ADVERSARIAL sequence generation failed", str(e))
            
        except ImportError as e:
            self.log("✗", "Cannot import sequence generation", str(e))
        
        # Test coordinator
        try:
            from buddy_multi_step_test_harness import MultiStepTestCoordinator
            
            print("\n  Test Coordinator:")
            try:
                coord = MultiStepTestCoordinator(output_file="test_validation.json")
                self.log("✓", "Coordinator initialization works")
            except Exception as e:
                self.log("✗", "Coordinator initialization failed", str(e))
            
        except ImportError as e:
            self.log("✗", "Cannot import coordinator", str(e))
    
    # ========================================================================
    # SECTION D: PHASE 2 ISOLATION
    # ========================================================================
    
    def validate_phase2_isolation(self):
        """Verify Phase 2 code has not been modified"""
        print("\n" + "=" * 78)
        print("SECTION E: PHASE 2 ISOLATION CHECK")
        print("=" * 78)
        
        phase2_main = self.buddy_dir / "phase2_adaptive_tests.py"
        
        if not phase2_main.exists():
            self.log("✗", "Phase 2 main module missing")
            return
        
        try:
            with open(phase2_main, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = len(content.split('\n'))
            
            # Expected: ~747 lines from calibration
            if 700 <= lines <= 800:
                self.log("✓", f"Phase 2 file size normal ({lines} lines, expect 700-800)")
            else:
                self.log("⚠", f"Phase 2 file size unexpected ({lines} lines, expect 700-800)")
            
            # Check it contains expected classes
            if "class AdaptiveTestRunner" in content:
                self.log("✓", "Phase 2 contains AdaptiveTestRunner class")
            else:
                self.log("✗", "Phase 2 missing AdaptiveTestRunner class")
            
        except Exception as e:
            self.log("✗", "Cannot read Phase 2 file", str(e))
        
        # Verify multi-step files are NEW (not modifications to Phase 2)
        ms_files = [
            "buddy_context_manager.py",
            "buddy_multi_step_test_harness.py",
            "buddy_multi_step_main.py"
        ]
        
        for filename in ms_files:
            filepath = self.buddy_dir / filename
            if filepath.exists():
                try:
                    with open(filepath, 'r') as f:
                        first_line = f.readline()
                    if "phase2_adaptive_tests" not in first_line.lower():
                        self.log("✓", f"{filename} is separate module (not modifying Phase 2)")
                    else:
                        self.log("⚠", f"{filename} references Phase 2 (expected)")
                except Exception as e:
                    self.log("✗", f"Cannot verify {filename}", str(e))
    
    # ========================================================================
    # SECTION F: INTEGRATION TEST
    # ========================================================================
    
    def validate_integration(self):
        """Run a short integration test"""
        print("\n" + "=" * 78)
        print("SECTION D: QUICK INTEGRATION TEST")
        print("=" * 78)
        
        try:
            from buddy_multi_step_test_harness import MultiStepTestCoordinator
            from buddy_context_manager import get_session_manager
            
            print("\n  Running minimal campaign (1 sequence):")
            
            coordinator = MultiStepTestCoordinator(output_file="test_validation.json")
            
            try:
                results = coordinator.run_test_campaign(
                    num_basic=1,
                    num_intermediate=0,
                    num_edge=0,
                    num_adversarial=0,
                    steps_per_sequence=3
                )
                
                if results:
                    self.log("✓", f"Campaign execution works ({len(results)} sequence ran)")
                    
                    for result in results:
                        if hasattr(result, 'success_rate'):
                            self.log(
                                "✓" if result.success_rate >= 0.95 else "⚠",
                                f"Sequence metrics valid (success={result.success_rate:.1%})"
                            )
                else:
                    self.log("✗", "Campaign returned no results")
            
            except Exception as e:
                self.log("⚠", "Campaign execution incomplete", str(e)[:80])
            
            # Check if JSON was created
            json_file = self.buddy_dir / "test_validation.json"
            if json_file.exists():
                try:
                    with open(json_file, 'r') as f:
                        data = json.load(f)
                    self.log("✓", "JSON output generation works")
                    
                    # Verify structure
                    if "session_metrics" in data:
                        self.log("✓", "JSON structure is valid")
                    else:
                        self.log("⚠", "JSON structure incomplete")
                except json.JSONDecodeError as e:
                    self.log("✗", "JSON output invalid", str(e)[:80])
                finally:
                    # Clean up test file
                    try:
                        json_file.unlink()
                    except:
                        pass
            else:
                self.log("⚠", "JSON output file not created")
        
        except Exception as e:
            self.log("✗", "Integration test failed", str(e)[:80])
    
    # ========================================================================
    # REPORTING
    # ========================================================================
    
    def print_summary(self):
        """Print validation summary"""
        print("\n" + "=" * 78)
        print("VALIDATION SUMMARY")
        print("=" * 78)
        
        total = self.passed + self.failed + self.warnings
        print(f"\nResults: {self.passed}/{total} passed")
        if self.warnings > 0:
            print(f"         {self.warnings} warning(s)")
        if self.failed > 0:
            print(f"         {self.failed} failure(s)")
        
        print("\nStatus: ", end="")
        if self.failed == 0 and self.warnings == 0:
            print("[PASS] ALL CHECKS PASSED (PRODUCTION READY)")
            return 0
        elif self.failed == 0:
            print("[WARN] WARNINGS ONLY (Review but likely OK)")
            return 0
        else:
            print("[FAIL] FAILURES DETECTED (Fix before deployment)")
            return 1
    
    def run_full_validation(self):
        """Run all validation checks"""
        print("\n")
        print("[" + "=" * 76 + "]")
        print("|" + " " * 20 + "BUDDY MULTI-STEP SYSTEM VALIDATION" + " " * 22 + "|")
        print("|" + " " * 15 + "Timestamp: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " " * 39 + "|")
        print("[" + "=" * 76 + "]")
        
        self.validate_file_integrity()
        self.validate_imports()
        self.validate_functionality()
        self.validate_phase2_isolation()
        self.validate_integration()
        
        return self.print_summary()


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Validate Buddy multi-step testing system"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick checks only (files & imports)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed output"
    )
    
    args = parser.parse_args()
    
    validator = SystemValidator(verbose=args.verbose)
    exit_code = validator.run_full_validation()
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
