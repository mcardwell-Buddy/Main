"""
BUDDY MULTI-STEP TEST SYSTEM - Main Execution Script
=====================================================

Runs multi-step test campaigns with various difficulty levels.
Demonstrates context propagation across sequential requests.

PHASE 6 INTEGRATION: Now includes dynamic task scheduler support

Usage:
    python buddy_multi_step_main.py [--basic N] [--intermediate N] [--edge N] [--adversarial N]
    python buddy_multi_step_main.py --scheduler [options]  # Use Phase 6 dynamic scheduler
    
Examples:
    python buddy_multi_step_main.py                    # Run default campaign (Phase 4)
    python buddy_multi_step_main.py --basic 5          # Run 5 basic sequences
    python buddy_multi_step_main.py --all 10           # Run 10 of each difficulty
    python buddy_multi_step_main.py --scheduler --dry-run  # Run with Phase 6 scheduler
"""

import sys
import argparse
import json
from pathlib import Path

# Import components
from buddy_multi_step_test_harness import (
    MultiStepTestCoordinator,
    SequenceDifficulty
)
from buddy_context_manager import get_session_manager, MULTI_STEP_TESTING_ENABLED

# Phase 6: Import task scheduler (optional)
try:
    from buddy_dynamic_task_scheduler import create_scheduler, TaskPriority, RiskLevel
    PHASE6_SCHEDULER_AVAILABLE = True
except ImportError:
    PHASE6_SCHEDULER_AVAILABLE = False


def parse_arguments():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description="Run Buddy multi-step test campaigns",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python buddy_multi_step_main.py
  python buddy_multi_step_main.py --all 10
  python buddy_multi_step_main.py --basic 5 --intermediate 5
  python buddy_multi_step_main.py --adversarial 20
        """
    )
    
    parser.add_argument(
        "--basic",
        type=int,
        default=3,
        help="Number of basic sequences (default: 3)"
    )
    parser.add_argument(
        "--intermediate",
        type=int,
        default=3,
        help="Number of intermediate sequences (default: 3)"
    )
    parser.add_argument(
        "--edge",
        type=int,
        default=3,
        help="Number of edge case sequences (default: 3)"
    )
    parser.add_argument(
        "--adversarial",
        type=int,
        default=3,
        help="Number of adversarial sequences (default: 3)"
    )
    parser.add_argument(
        "--all",
        type=int,
        dest="all_sequences",
        help="Run N sequences of each difficulty (overrides other options)"
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=5,
        help="Steps per sequence (default: 5)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="buddy_multi_step_metrics.json",
        help="Output file for results (default: buddy_multi_step_metrics.json)"
    )
    parser.add_argument(
        "--export-sessions",
        type=str,
        help="Export all sessions to directory"
    )
    parser.add_argument(
        "--disable-feature-flag",
        action="store_true",
        help="Disable multi-step testing feature flag"
    )
    parser.add_argument(
        "--scheduler",
        action="store_true",
        help="Use Phase 6 dynamic task scheduler (experimental)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Enable dry-run mode for high-risk tasks (Phase 6 only)"
    )
    
    return parser.parse_args()


def validate_feature_flag():
    """Check if multi-step testing is enabled"""
    if not MULTI_STEP_TESTING_ENABLED:
        print("ERROR: Multi-step testing is disabled (MULTI_STEP_TESTING_ENABLED = False)")
        print("Enable it in buddy_context_manager.py to proceed")
        return False
    return True


def print_header(use_scheduler=False):
    """Print campaign header"""
    print("\n" + "="*80)
    print("BUDDY MULTI-STEP TEST CAMPAIGN")
    print("="*80)
    if use_scheduler:
        print("\nPhase 6: Dynamic Task Scheduler (Priority Queue + Conditional Branching)")
        print("Mode: Task-based execution with dependency resolution")
    else:
        print("\nPhase 2 + Soul Integration: Sequential Request Testing")
        print("Mode: Linear sequence execution")
    print("Safety Mode: READ-ONLY (No Phase 1-4 modifications)")
    print("Test Type: Progressive Difficulty Sequences\n")


def print_footer(args, coordinator):
    """Print campaign footer"""
    print("\n" + "="*80)
    print("CAMPAIGN COMPLETE")
    print("="*80)
    print(f"\nResults saved to: {args.output}")
    
    session_manager = get_session_manager()
    sessions = session_manager.list_sessions()
    print(f"Active sessions: {len(sessions)}")
    
    if args.export_sessions:
        print(f"Exporting sessions to: {args.export_sessions}")
        session_manager.export_all_sessions(args.export_sessions)
    
    print("\nNext Steps:")
    print("  1. Review results in: " + args.output)
    print("  2. Analyze per-step metrics in the JSON output")
    print("  3. Check session state for context propagation")
    print("  4. Run again with different parameters for additional data\n")


def run_campaign(args):
    """Run the test campaign"""
    
    # Check if using Phase 6 scheduler
    if args.scheduler:
        if not PHASE6_SCHEDULER_AVAILABLE:
            print("ERROR: Phase 6 scheduler not available")
            print("Ensure buddy_dynamic_task_scheduler.py is present")
            return 1
        return run_scheduler_campaign(args)
    
    # Check feature flag
    if not validate_feature_flag():
        return 1
    
    print_header(use_scheduler=False)
    
    # Create coordinator
    coordinator = MultiStepTestCoordinator(output_file=args.output)
    
    # Determine sequence counts
    if args.all_sequences:
        num_basic = num_intermediate = num_edge = num_adversarial = args.all_sequences
    else:
        num_basic = args.basic
        num_intermediate = args.intermediate
        num_edge = args.edge
        num_adversarial = args.adversarial
    
    print(f"Sequence Configuration:")
    print(f"  Basic:        {num_basic}")
    print(f"  Intermediate: {num_intermediate}")
    print(f"  Edge Cases:   {num_edge}")
    print(f"  Adversarial:  {num_adversarial}")
    print(f"  Steps/Seq:    {args.steps}")
    print(f"  Total Seqs:   {num_basic + num_intermediate + num_edge + num_adversarial}\n")
    
    try:
        # Run campaign
        results = coordinator.run_test_campaign(
            num_basic=num_basic,
            num_intermediate=num_intermediate,
            num_edge=num_edge,
            num_adversarial=num_adversarial,
            steps_per_sequence=args.steps
        )
        
        print_footer(args, coordinator)
        return 0
    
    except Exception as e:
        print(f"\nERROR: Campaign failed with exception:")
        print(f"  {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


def run_scheduler_campaign(args):
    """Run campaign using Phase 6 dynamic task scheduler"""
    print_header(use_scheduler=True)
    
    print("PHASE 6 SCHEDULER: Task-based execution (experimental)")
    print(f"Dry-run mode: {args.dry_run}")
    print("\nNote: Full Phase 6 campaign integration coming soon.")
    print("For now, run: python buddy_dynamic_task_scheduler_tests.py")
    print("\nPhase 6 features:")
    print("  - Priority-based task queue")
    print("  - Dependency resolution")
    print("  - Conditional branching")
    print("  - Risk-aware execution")
    print("  - Automatic retry logic\n")
    
    # For now, suggest running test harness
    print("To test Phase 6 scheduler:")
    print("  python buddy_dynamic_task_scheduler_tests.py\n")
    
    return 0


def main():
    """Main entry point"""
    args = parse_arguments()
    
    return run_campaign(args)


if __name__ == "__main__":
    sys.exit(main())

