"""
Visual Demonstration: Mission Cost Accounting
Shows cost tracking for different mission scenarios
"""

from backend.mission.mission_cost_accountant import MissionCostReport
import json


def demonstrate_cost_accounting():
    """Show visual examples of mission cost tracking."""
    
    print("\n" + "="*70)
    print("BUDDY'S MISSION COST ACCOUNTING SYSTEM")
    print("Normalized Cost Tracking for Every Mission")
    print("="*70 + "\n")
    
    scenarios = [
        {
            "name": "💚 Scenario 1: Efficient Mission (Low Cost)",
            "description": "Quick mission with no failures",
            "report": MissionCostReport(
                mission_id="demo-efficient",
                total_duration_sec=5.2,
                pages_visited=1,
                selectors_attempted=3,
                selectors_failed=0,
                retries_total=0,
                time_cost=5.2,
                page_cost=1,
                failure_cost=0,
                timestamp="2026-02-07T15:00:00+00:00"
            )
        },
        {
            "name": "💛 Scenario 2: Standard Mission (Medium Cost)",
            "description": "Normal mission with some retries",
            "report": MissionCostReport(
                mission_id="demo-standard",
                total_duration_sec=45.8,
                pages_visited=5,
                selectors_attempted=15,
                selectors_failed=3,
                retries_total=5,
                time_cost=45.8,
                page_cost=5,
                failure_cost=3,
                timestamp="2026-02-07T15:05:00+00:00"
            )
        },
        {
            "name": "🧡 Scenario 3: Complex Mission (High Cost)",
            "description": "Long mission with multiple pages",
            "report": MissionCostReport(
                mission_id="demo-complex",
                total_duration_sec=180.5,
                pages_visited=20,
                selectors_attempted=50,
                selectors_failed=8,
                retries_total=15,
                time_cost=180.5,
                page_cost=20,
                failure_cost=8,
                timestamp="2026-02-07T15:10:00+00:00"
            )
        },
        {
            "name": "❤️  Scenario 4: Problematic Mission (Very High Cost)",
            "description": "Mission with many failures (60% failure rate)",
            "report": MissionCostReport(
                mission_id="demo-problematic",
                total_duration_sec=120.0,
                pages_visited=3,
                selectors_attempted=25,
                selectors_failed=15,
                retries_total=45,
                time_cost=120.0,
                page_cost=3,
                failure_cost=15,
                timestamp="2026-02-07T15:15:00+00:00"
            )
        },
        {
            "name": "💙 Scenario 5: Failed Mission (Zero Activity)",
            "description": "Mission failed immediately with no activity",
            "report": MissionCostReport(
                mission_id="demo-failed",
                total_duration_sec=2.5,
                pages_visited=0,
                selectors_attempted=0,
                selectors_failed=0,
                retries_total=0,
                time_cost=2.5,
                page_cost=0,
                failure_cost=0,
                timestamp="2026-02-07T15:20:00+00:00"
            )
        }
    ]
    
    for scenario in scenarios:
        report = scenario["report"]
        print(scenario["name"])
        print("-" * 70)
        print(f"Description: {scenario['description']}")
        print()
        
        # Raw metrics
        print("📊 Raw Metrics:")
        print(f"   • Duration: {report.total_duration_sec}s")
        print(f"   • Pages visited: {report.pages_visited}")
        print(f"   • Selectors attempted: {report.selectors_attempted}")
        print(f"   • Selectors failed: {report.selectors_failed}")
        print(f"   • Total retries: {report.retries_total}")
        
        if report.selectors_attempted > 0:
            failure_rate = (report.selectors_failed / report.selectors_attempted) * 100
            print(f"   • Failure rate: {failure_rate:.1f}%")
        print()
        
        # Cost units
        print("💰 Cost Units:")
        print(f"   • time_cost: {report.time_cost}s")
        print(f"   • page_cost: {report.page_cost} pages")
        print(f"   • failure_cost: {report.failure_cost} failures")
        print()
        
        # Cost assessment
        total_cost_score = report.time_cost / 10 + report.page_cost + report.failure_cost * 2
        if total_cost_score < 5:
            assessment = "✅ Low cost - efficient mission"
        elif total_cost_score < 20:
            assessment = "⚠️  Medium cost - acceptable"
        elif total_cost_score < 50:
            assessment = "🔶 High cost - needs attention"
        else:
            assessment = "🚨 Very high cost - investigate"
        
        print(f"Assessment: {assessment}")
        print(f"Cost score: {total_cost_score:.1f}")
        print()
        
        # Signal preview
        signal = report.to_signal()
        print("📤 Signal to be emitted:")
        print(json.dumps(signal, indent=4))
        print()
        print("="*70)
        print()
    
    # Show cost comparison
    print("📊 COST COMPARISON")
    print("-" * 70)
    print()
    print("Mission Type          Time    Pages   Failures   Cost Score")
    print("-" * 70)
    
    for scenario in scenarios:
        report = scenario["report"]
        score = report.time_cost / 10 + report.page_cost + report.failure_cost * 2
        mission_type = scenario["name"].split(":")[1].strip()[:20]
        print(f"{mission_type:<20} {report.time_cost:>6.1f}s  {report.page_cost:>5}   {report.failure_cost:>8}   {score:>10.1f}")
    
    print()
    print("="*70)
    print()
    
    # Show integration
    print("🔄 INTEGRATION WORKFLOW")
    print("-" * 70)
    print()
    print("1. Mission Executes")
    print("   ↓")
    print("2. Signals Emitted (selector_outcome, mission_status_update)")
    print("   ↓")
    print("3. Mission Completes")
    print("   ↓")
    print("4. Goal Evaluation")
    print("   ↓")
    print("5. Opportunity Normalization")
    print("   ↓")
    print("6. Ambiguity Detection")
    print("   ↓")
    print("7. Cost Accounting ← YOU ARE HERE")
    print("   ↓")
    print("8. Signal Emitted (mission_cost_report)")
    print("   ↓")
    print("9. Whiteboard Updated")
    print("   ↓")
    print("10. Available for Analysis")
    print()
    print("="*70)
    print()
    
    # Show use cases
    print("💡 USE CASES")
    print("-" * 70)
    print()
    print("1. Mission Comparison")
    print("   → Compare costs across missions to find patterns")
    print()
    print("2. Performance Monitoring")
    print("   → Track cost trends over time")
    print()
    print("3. Resource Planning")
    print("   → Estimate mission duration and resource needs")
    print()
    print("4. Selector Quality")
    print("   → High failure_cost indicates selector issues")
    print()
    print("5. Optimization Targets")
    print("   → Focus on high-cost missions for improvements")
    print()
    print("="*70)
    print()


if __name__ == "__main__":
    demonstrate_cost_accounting()
