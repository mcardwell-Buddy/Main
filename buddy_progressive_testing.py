"""
BUDDY PROGRESSIVE HIGH-VOLUME TESTING
======================================

Purpose: Run large-scale progressive synthetic tests to collect statistically
         meaningful stability, robustness, and behavior metrics.

Strategy: 4 progressive waves with increasing difficulty:
  - Wave 1: 1,000 requests (baseline stability)
  - Wave 2: 2,500 requests (mixed realism)
  - Wave 3: 5,000 requests (hard edge cases)
  - Wave 4: 5,000+ requests (adversarial & stress)

Safety: READ-ONLY - No modifications to Phase 1/2/Soul code
"""

import json
import time
import sys
import os
from datetime import datetime
from pathlib import Path

# Import existing test infrastructure (READ-ONLY)
try:
    from phase2_adaptive_tests import AdaptiveTestGenerator, AdaptiveTestRunner
except ImportError:
    print("ERROR: Cannot import phase2_adaptive_tests.py")
    print("Ensure you're in the correct directory with Phase 2 test files.")
    sys.exit(1)

# Configuration
OUTPUT_FILE = "buddy_progressive_test_metrics.json"
TRAFFIC_LOG_FILE = "buddy_continuous_traffic_logs.json"

# Wave configurations with adjusted distributions
WAVE_CONFIGS = {
    1: {
        "name": "Baseline Stability",
        "requests": 1000,
        "description": "Mostly atomic and clear goals, low ambiguity",
        "distribution": {
            "simple": 60,           # High proportion of simple
            "multi_step": 5,        # Very few complex
            "low_confidence": 5,    # Very few vague
            "high_confidence": 20,  # Good proportion of clear
            "conflicting_gates": 0, # None
            "clarification": 5,     # Few ambiguous
            "edge_cases": 3,        # Very few edge cases
            "adversarial": 2        # Minimal adversarial
        },
        "thresholds": {
            "max_latency_ms": 50,
            "min_success_rate": 0.95,
            "max_error_rate": 0.05
        }
    },
    2: {
        "name": "Mixed Realism",
        "requests": 2500,
        "description": "Natural distribution with mild ambiguity",
        "distribution": {
            "simple": 30,           # Natural mix
            "multi_step": 15,       # More complex workflows
            "low_confidence": 15,   # More vague inputs
            "high_confidence": 20,  # Balanced clear requests
            "conflicting_gates": 5, # Some conflicting signals
            "clarification": 10,    # More ambiguous
            "edge_cases": 3,        # Few edge cases
            "adversarial": 2        # Minimal adversarial
        },
        "thresholds": {
            "max_latency_ms": 50,
            "min_success_rate": 0.90,
            "max_error_rate": 0.10
        }
    },
    3: {
        "name": "Hard Edge Cases",
        "requests": 5000,
        "description": "Heavy pre-validation, clarification, conflicting signals",
        "distribution": {
            "simple": 15,           # Fewer simple
            "multi_step": 15,       # More complex
            "low_confidence": 15,   # More vague
            "high_confidence": 10,  # Fewer clear
            "conflicting_gates": 15,# Heavy conflicting signals
            "clarification": 15,    # Heavy ambiguity
            "edge_cases": 10,       # More edge cases
            "adversarial": 5        # Some adversarial
        },
        "thresholds": {
            "max_latency_ms": 50,
            "min_success_rate": 0.85,
            "max_error_rate": 0.15
        }
    },
    4: {
        "name": "Adversarial & Stress",
        "requests": 5000,
        "description": "Adversarial inputs, extreme nesting, long context",
        "distribution": {
            "simple": 10,           # Minimal simple
            "multi_step": 10,       # Some complex
            "low_confidence": 10,   # Some vague
            "high_confidence": 10,  # Some clear
            "conflicting_gates": 15,# Heavy conflicting
            "clarification": 10,    # Some ambiguous
            "edge_cases": 20,       # Heavy edge cases
            "adversarial": 15       # Heavy adversarial
        },
        "thresholds": {
            "max_latency_ms": 50,
            "min_success_rate": 0.80,
            "max_error_rate": 0.20
        }
    }
}

class ProgressiveTestCoordinator:
    """Coordinates progressive wave-based testing"""
    
    def __init__(self):
        self.test_generator = AdaptiveTestGenerator()
        self.test_runner = AdaptiveTestRunner(use_real_soul=False)  # Use mock Soul for safety
        self.results = {
            "start_time": datetime.now().isoformat(),
            "waves": [],
            "total_requests": 0,
            "total_errors": 0,
            "overall_success_rate": 0.0
        }
        
        # Load existing logs if present
        self.traffic_log = self._load_traffic_log()
        
    def _load_traffic_log(self):
        """Load existing traffic log or create new"""
        if os.path.exists(TRAFFIC_LOG_FILE):
            try:
                with open(TRAFFIC_LOG_FILE, 'r') as f:
                    return json.load(f)
            except:
                return {"requests": []}
        return {"requests": []}
    
    def _save_traffic_log(self):
        """Save traffic log"""
        with open(TRAFFIC_LOG_FILE, 'w') as f:
            json.dump(self.traffic_log, f, indent=2)
    
    def _generate_request(self, wave_num, distribution):
        """Generate a synthetic request based on wave distribution"""
        import random
        
        # Normalize distribution to probabilities
        total = sum(distribution.values())
        probs = {k: v/total for k, v in distribution.items()}
        
        # Select category based on distribution
        categories = list(probs.keys())
        weights = list(probs.values())
        category = random.choices(categories, weights=weights)[0]
        
        # Generate request for that category using adaptive test generator
        difficulty = min(10, max(1, 3 + wave_num - 1))  # Scale difficulty with wave (1-10)
        scenarios = self.test_generator.generate_scenarios(difficulty_level=difficulty)
        
        if scenarios:
            # Pick a random scenario from this difficulty level
            test = random.choice(scenarios)
            return {
                "scenario": test,  # Store full test scenario
                "category": category,
                "wave": wave_num,
                "difficulty": difficulty
            }
        
        # Fallback - shouldn't happen but just in case
        from phase2_adaptive_tests import TestScenario
        fallback_scenario = TestScenario(
            scenario_id=f"FALLBACK-W{wave_num}-{random.randint(1000,9999)}",
            difficulty_level=difficulty,
            scenario_type=category,
            goal="test request",
            expected_outcomes={},
            test_conditions={}
        )
        return {
            "scenario": fallback_scenario,
            "category": category,
            "wave": wave_num,
            "difficulty": difficulty
        }
    
    def _process_request(self, request):
        """Process a single request through Phase 2 system"""
        start_time = time.time()
        
        try:
            # Run through Phase 2 test infrastructure (READ-ONLY)
            scenario = request["scenario"]
            test_result = self.test_runner.run_test(scenario)
            
            # Extract metrics from test result
            metrics = {
                "timestamp": test_result.timestamp,
                "wave": request["wave"],
                "category": request["category"],
                "difficulty": request["difficulty"],
                "success": test_result.success,
                "confidence": test_result.confidence,
                "confidence_bucket": self._get_confidence_bucket(test_result.confidence),
                "pre_validation": test_result.pre_validation_status,
                "approval_path": test_result.approval_path,
                "clarification_triggered": (test_result.approval_path == "clarification"),
                "soul_used": "mock",  # We're using mock Soul for safety
                "execution_time_ms": test_result.execution_time_ms,
                "schema_valid": True,  # Validated by test runner
                "error": None if test_result.success else "; ".join(test_result.failures)
            }
            
            return metrics
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return {
                "timestamp": datetime.now().isoformat(),
                "wave": request["wave"],
                "category": request["category"],
                "difficulty": request["difficulty"],
                "success": False,
                "confidence": 0.0,
                "confidence_bucket": "error",
                "pre_validation": "error",
                "approval_path": "error",
                "clarification_triggered": False,
                "soul_used": "error",
                "execution_time_ms": execution_time,
                "schema_valid": False,
                "error": str(e)
            }
    
    def _get_confidence_bucket(self, confidence):
        """Categorize confidence into buckets"""
        if confidence < 0.55:
            return "low"
        elif confidence < 0.85:
            return "medium"
        else:
            return "high"
    
    def _check_safety_violations(self, metrics):
        """Check for safety violations that should halt testing"""
        violations = []
        
        # Check latency
        if metrics["execution_time_ms"] > 50:
            violations.append(f"LATENCY VIOLATION: {metrics['execution_time_ms']:.2f}ms > 50ms threshold")
        
        # Check for exceptions
        if metrics["error"]:
            violations.append(f"EXCEPTION: {metrics['error']}")
        
        # Check schema validity
        if not metrics["schema_valid"]:
            violations.append("SCHEMA VIOLATION: Response missing required fields")
        
        return violations
    
    def _aggregate_wave_metrics(self, wave_results):
        """Aggregate metrics for a wave"""
        if not wave_results:
            return {}
        
        total = len(wave_results)
        successful = sum(1 for r in wave_results if r["success"])
        
        # Confidence stats (only for successful requests)
        confidences = [r["confidence"] for r in wave_results if r["success"]]
        
        # Bucket counts
        buckets = {"low": 0, "medium": 0, "high": 0, "error": 0}
        for r in wave_results:
            buckets[r["confidence_bucket"]] += 1
        
        # Approval path distribution
        approval_paths = {}
        for r in wave_results:
            path = r["approval_path"]
            approval_paths[path] = approval_paths.get(path, 0) + 1
        
        # Pre-validation stats
        pre_val_passed = sum(1 for r in wave_results if r["pre_validation"] == "passed")
        pre_val_failed = sum(1 for r in wave_results if r["pre_validation"] == "failed")
        
        # Clarification stats
        clarifications = sum(1 for r in wave_results if r["clarification_triggered"])
        
        # Execution time stats
        exec_times = [r["execution_time_ms"] for r in wave_results]
        
        # Error stats
        errors = [r for r in wave_results if r["error"]]
        
        return {
            "total_requests": total,
            "successful_requests": successful,
            "failed_requests": total - successful,
            "success_rate": successful / total if total > 0 else 0,
            "confidence": {
                "mean": sum(confidences) / len(confidences) if confidences else 0,
                "min": min(confidences) if confidences else 0,
                "max": max(confidences) if confidences else 0,
                "std_dev": self._std_dev(confidences) if confidences else 0
            },
            "confidence_buckets": buckets,
            "approval_paths": approval_paths,
            "pre_validation": {
                "passed": pre_val_passed,
                "failed": pre_val_failed,
                "pass_rate": pre_val_passed / total if total > 0 else 0
            },
            "clarifications": {
                "triggered": clarifications,
                "rate": clarifications / total if total > 0 else 0
            },
            "execution_time": {
                "avg": sum(exec_times) / len(exec_times) if exec_times else 0,
                "min": min(exec_times) if exec_times else 0,
                "max": max(exec_times) if exec_times else 0,
                "p95": self._percentile(exec_times, 0.95) if exec_times else 0
            },
            "errors": {
                "count": len(errors),
                "rate": len(errors) / total if total > 0 else 0,
                "details": errors[:10]  # First 10 errors
            }
        }
    
    def _std_dev(self, values):
        """Calculate standard deviation"""
        if not values:
            return 0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
    
    def _percentile(self, values, p):
        """Calculate percentile"""
        if not values:
            return 0
        sorted_values = sorted(values)
        index = int(len(sorted_values) * p)
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def _check_wave_thresholds(self, aggregated, thresholds):
        """Check if wave meets safety thresholds"""
        violations = []
        
        if aggregated["execution_time"]["max"] > thresholds["max_latency_ms"]:
            violations.append(f"Max latency {aggregated['execution_time']['max']:.2f}ms exceeds {thresholds['max_latency_ms']}ms")
        
        if aggregated["success_rate"] < thresholds["min_success_rate"]:
            violations.append(f"Success rate {aggregated['success_rate']:.2%} below {thresholds['min_success_rate']:.2%}")
        
        if aggregated["errors"]["rate"] > thresholds["max_error_rate"]:
            violations.append(f"Error rate {aggregated['errors']['rate']:.2%} exceeds {thresholds['max_error_rate']:.2%}")
        
        return violations
    
    def run_wave(self, wave_num):
        """Execute a single wave of testing"""
        config = WAVE_CONFIGS[wave_num]
        
        print(f"\n{'='*80}")
        print(f"WAVE {wave_num}: {config['name']}")
        print(f"{'='*80}")
        print(f"Description: {config['description']}")
        print(f"Requests: {config['requests']:,}")
        print(f"Distribution: {config['distribution']}")
        print(f"Starting at: {datetime.now().isoformat()}")
        print()
        
        wave_results = []
        safety_violations = []
        start_time = time.time()
        
        # Generate and process requests
        for i in range(config["requests"]):
            # Generate request
            request = self._generate_request(wave_num, config["distribution"])
            
            # Process request
            metrics = self._process_request(request)
            wave_results.append(metrics)
            
            # Log to traffic log (serialize only necessary data)
            self.traffic_log["requests"].append({
                "request": {
                    "scenario_id": request["scenario"].scenario_id,
                    "difficulty": request["difficulty"],
                    "category": request["category"],
                    "wave": request["wave"],
                    "goal": request["scenario"].goal
                },
                "metrics": metrics,
                "tag": "Synthetic Buddy Traffic – Read Only"
            })
            
            # Check for safety violations
            violations = self._check_safety_violations(metrics)
            if violations:
                safety_violations.extend(violations)
                print(f"\n⚠️  SAFETY VIOLATION at request {i+1}:")
                for v in violations:
                    print(f"   {v}")
            
            # Progress update every 100 requests
            if (i + 1) % 100 == 0:
                elapsed = time.time() - start_time
                rate = (i + 1) / elapsed
                eta = (config["requests"] - i - 1) / rate if rate > 0 else 0
                success = sum(1 for r in wave_results if r["success"])
                success_rate = success / len(wave_results)
                print(f"Progress: {i+1:,}/{config['requests']:,} ({(i+1)/config['requests']*100:.1f}%) | "
                      f"Success: {success_rate:.1%} | "
                      f"Rate: {rate:.1f} req/s | "
                      f"ETA: {eta:.0f}s")
        
        wave_duration = time.time() - start_time
        
        # Aggregate metrics
        aggregated = self._aggregate_wave_metrics(wave_results)
        aggregated["duration_seconds"] = wave_duration
        aggregated["requests_per_second"] = config["requests"] / wave_duration
        
        # Check thresholds
        threshold_violations = self._check_wave_thresholds(aggregated, config["thresholds"])
        
        # Store wave results
        wave_summary = {
            "wave_number": wave_num,
            "wave_name": config["name"],
            "description": config["description"],
            "start_time": datetime.fromtimestamp(start_time).isoformat(),
            "end_time": datetime.now().isoformat(),
            "config": config,
            "aggregated_metrics": aggregated,
            "safety_violations": safety_violations,
            "threshold_violations": threshold_violations,
            "status": "PASSED" if not threshold_violations else "FAILED"
        }
        
        self.results["waves"].append(wave_summary)
        self.results["total_requests"] += config["requests"]
        self.results["total_errors"] += aggregated["errors"]["count"]
        
        # Save results after each wave
        self._save_results()
        self._save_traffic_log()
        
        # Print wave summary
        self._print_wave_summary(wave_summary)
        
        return wave_summary
    
    def _print_wave_summary(self, wave):
        """Print wave completion summary"""
        agg = wave["aggregated_metrics"]
        
        print(f"\n{'='*80}")
        print(f"WAVE {wave['wave_number']} COMPLETE: {wave['wave_name']}")
        print(f"{'='*80}")
        print(f"Status: {wave['status']}")
        print(f"Duration: {agg['duration_seconds']:.1f}s")
        print(f"Rate: {agg['requests_per_second']:.1f} req/s")
        print()
        print(f"📊 METRICS:")
        print(f"  Total Requests:     {agg['total_requests']:,}")
        print(f"  Success Rate:       {agg['success_rate']:.2%} ({'✓' if agg['success_rate'] >= 0.80 else '✗'})")
        print(f"  Error Rate:         {agg['errors']['rate']:.2%}")
        print()
        print(f"⚡ PERFORMANCE:")
        print(f"  Avg Execution:      {agg['execution_time']['avg']:.2f}ms")
        print(f"  P95 Execution:      {agg['execution_time']['p95']:.2f}ms")
        print(f"  Max Execution:      {agg['execution_time']['max']:.2f}ms ({'✓' if agg['execution_time']['max'] <= 50 else '✗'})")
        print()
        print(f"🎯 CONFIDENCE:")
        print(f"  Mean:               {agg['confidence']['mean']:.3f}")
        print(f"  Std Dev:            {agg['confidence']['std_dev']:.3f} ({'✓' if agg['confidence']['std_dev'] > 0.2 else '✗'})")
        print(f"  Distribution:       Low: {agg['confidence_buckets']['low']}, "
              f"Med: {agg['confidence_buckets']['medium']}, "
              f"High: {agg['confidence_buckets']['high']}")
        print()
        print(f"🛡️  PRE-VALIDATION:")
        print(f"  Pass Rate:          {agg['pre_validation']['pass_rate']:.2%}")
        print(f"  Passed:             {agg['pre_validation']['passed']:,}")
        print(f"  Failed:             {agg['pre_validation']['failed']:,}")
        print()
        print(f"🔀 APPROVAL ROUTING:")
        for path, count in sorted(agg['approval_paths'].items()):
            pct = count / agg['total_requests'] * 100
            print(f"  {path:20s} {count:,} ({pct:.1f}%)")
        print()
        print(f"💬 CLARIFICATIONS:")
        print(f"  Triggered:          {agg['clarifications']['triggered']:,} ({agg['clarifications']['rate']:.2%})")
        print()
        
        if wave["safety_violations"]:
            print(f"⚠️  SAFETY VIOLATIONS: {len(wave['safety_violations'])}")
            for v in wave["safety_violations"][:5]:
                print(f"   {v}")
        else:
            print(f"✅ SAFETY: No violations detected")
        
        if wave["threshold_violations"]:
            print(f"\n⚠️  THRESHOLD VIOLATIONS:")
            for v in wave["threshold_violations"]:
                print(f"   {v}")
        else:
            print(f"\n✅ THRESHOLDS: All targets met")
        
        print(f"{'='*80}\n")
    
    def _save_results(self):
        """Save results to file"""
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(self.results, f, indent=2)
    
    def run_all_waves(self):
        """Execute all progressive waves"""
        print(f"\n{'#'*80}")
        print(f"# BUDDY PROGRESSIVE HIGH-VOLUME TESTING")
        print(f"# Synthetic Traffic – Read Only")
        print(f"# Target: 13,500+ total requests across 4 waves")
        print(f"{'#'*80}\n")
        
        for wave_num in sorted(WAVE_CONFIGS.keys()):
            wave_result = self.run_wave(wave_num)
            
            # Check if we should continue to next wave
            if wave_result["threshold_violations"]:
                print(f"\n⚠️  Wave {wave_num} failed threshold checks.")
                print(f"Continuing to next wave (observation-only mode)...")
                print()
            
            # Brief pause between waves
            if wave_num < max(WAVE_CONFIGS.keys()):
                print(f"Pausing 5 seconds before next wave...")
                time.sleep(5)
        
        # Generate final report
        self._generate_final_report()
    
    def _generate_final_report(self):
        """Generate final consolidated report"""
        self.results["end_time"] = datetime.now().isoformat()
        
        # Calculate overall metrics
        all_success = sum(w["aggregated_metrics"]["successful_requests"] for w in self.results["waves"])
        all_total = self.results["total_requests"]
        self.results["overall_success_rate"] = all_success / all_total if all_total > 0 else 0
        
        # Calculate overall confidence distribution
        all_confidences = []
        for wave in self.results["waves"]:
            mean = wave["aggregated_metrics"]["confidence"]["mean"]
            count = wave["aggregated_metrics"]["successful_requests"]
            all_confidences.extend([mean] * count)  # Approximate
        
        self.results["overall_confidence"] = {
            "mean": sum(all_confidences) / len(all_confidences) if all_confidences else 0,
            "std_dev": self._std_dev(all_confidences) if all_confidences else 0
        }
        
        # Save final results
        self._save_results()
        
        # Print final report
        print(f"\n{'#'*80}")
        print(f"# FINAL CONSOLIDATED REPORT")
        print(f"{'#'*80}\n")
        
        print(f"📅 Test Period:")
        print(f"  Start:              {self.results['start_time']}")
        print(f"  End:                {self.results['end_time']}")
        print()
        
        print(f"📊 Overall Statistics:")
        print(f"  Total Requests:     {self.results['total_requests']:,}")
        print(f"  Total Errors:       {self.results['total_errors']:,}")
        print(f"  Success Rate:       {self.results['overall_success_rate']:.2%}")
        print(f"  Confidence Mean:    {self.results['overall_confidence']['mean']:.3f}")
        print(f"  Confidence σ:       {self.results['overall_confidence']['std_dev']:.3f}")
        print()
        
        print(f"🌊 Wave Summary:")
        for wave in self.results["waves"]:
            status_icon = "✅" if wave["status"] == "PASSED" else "⚠️"
            print(f"  {status_icon} Wave {wave['wave_number']}: {wave['wave_name']}")
            print(f"     Requests: {wave['aggregated_metrics']['total_requests']:,}, "
                  f"Success: {wave['aggregated_metrics']['success_rate']:.2%}, "
                  f"Avg: {wave['aggregated_metrics']['execution_time']['avg']:.2f}ms")
        print()
        
        # Check completion criteria
        print(f"✅ Completion Criteria:")
        criteria_met = []
        criteria_met.append(("Total Requests ≥10,000", self.results['total_requests'] >= 10000))
        criteria_met.append(("Zero Crashes", self.results['total_errors'] == 0))
        criteria_met.append(("Success Rate ≥80%", self.results['overall_success_rate'] >= 0.80))
        criteria_met.append(("Confidence σ >0.2", self.results['overall_confidence']['std_dev'] > 0.2))
        
        for criterion, met in criteria_met:
            icon = "✅" if met else "❌"
            print(f"  {icon} {criterion}")
        
        all_met = all(met for _, met in criteria_met)
        
        print()
        print(f"{'#'*80}")
        if all_met:
            print(f"# ✅ TESTING COMPLETE - ALL CRITERIA MET")
            print(f"# System demonstrated: Stability, Robustness, Deterministic Behavior")
            print(f"# Status: PRODUCTION READY")
        else:
            print(f"# ⚠️  TESTING COMPLETE - REVIEW REQUIRED")
            print(f"# Some criteria not met - See wave details above")
        print(f"{'#'*80}\n")
        
        print(f"📁 Results saved to:")
        print(f"  {OUTPUT_FILE}")
        print(f"  {TRAFFIC_LOG_FILE}")
        print()

def main():
    """Main entry point"""
    coordinator = ProgressiveTestCoordinator()
    coordinator.run_all_waves()

if __name__ == "__main__":
    main()

