"""
Phase 25: Dashboard Application - Main Entry Point

Provides CLI interface for dashboard navigation, state management, and JSON export.
Serves as the primary user-facing application for Phase 25 dashboards.
"""

import json
import argparse
from pathlib import Path
from typing import Optional
from datetime import datetime, timezone

from buddy_phase25.dashboard_router import DashboardManager, DashboardMode, ExecutionEnvironment
from buddy_phase25.learning_dashboard import LearningDashboard
from buddy_phase25.operations_dashboard import OperationsDashboard
from buddy_phase25.interaction_dashboard import InteractionDashboard
from buddy_phase25.dashboard_state_models import UnifiedDashboardState
from buddy_phase25.phase24_adapters import Phase24AggregateAdapter


class DashboardApp:
    """Main dashboard application"""
    
    def __init__(self):
        """Initialize dashboard app"""
        self.manager = DashboardManager()
        self.learning_dashboard = LearningDashboard()
        self.operations_dashboard = OperationsDashboard()
        self.interaction_dashboard = InteractionDashboard()
    
    def display_learning_dashboard(self):
        """Display learning dashboard"""
        print("\n" + "="*80)
        print("LEARNING DASHBOARD - Buddy's Adaptive Behavior Insights")
        print("="*80 + "\n")
        
        self.learning_dashboard.load()
        
        # Summary
        print(self.learning_dashboard.get_learning_summary())
        print()
        
        # Confidence visualization
        print("Confidence Trajectory:")
        print(self.learning_dashboard.get_confidence_visualization())
        print()
        
        # Learning signals
        print("Recent Learning Signals:")
        print(self.learning_dashboard.get_learning_signals_table())
        print()
        
        # Tool performance
        print("Tool Performance Metrics:")
        print(self.learning_dashboard.get_tool_performance_table())
        print()
        
        # Improvement chains
        print("Improvement Chains (Failure → Insight → Action):")
        chains = self.learning_dashboard.get_improvement_chains()
        if chains:
            print(chains)
        else:
            print("[No improvement chains available]")
    
    def display_operations_dashboard(self):
        """Display operations dashboard"""
        print("\n" + "="*80)
        print("OPERATIONS DASHBOARD - Real-Time System Monitoring & Health")
        print("="*80 + "\n")
        
        env = self.manager.get_state().environment
        self.operations_dashboard.load(env)
        
        # Summary
        print(self.operations_dashboard.get_operations_summary())
        print()
        
        # Environment info
        print(f"Execution Environment: {env.value.upper()}")
        print()
        
        # Health report
        print("System Health Report:")
        print(self.operations_dashboard.get_system_health_report())
        print()
        
        # Active agents
        print("Active Agents:")
        print(self.operations_dashboard.get_active_agents_table())
        print()
        
        # Tool executions
        print("Recent Tool Executions:")
        print(self.operations_dashboard.get_tool_executions_table(limit=10))
        print()
        
        # Safety decisions
        print("Safety Gate Decisions:")
        print(self.operations_dashboard.get_safety_decisions_table(limit=10))
    
    def display_interaction_dashboard(self):
        """Display interaction dashboard"""
        print("\n" + "="*80)
        print("INTERACTION DASHBOARD - Chat, Approvals & Tasks")
        print("="*80 + "\n")
        
        self.interaction_dashboard.load()
        
        # Summary
        print(self.interaction_dashboard.get_interaction_summary())
        print()
        
        # Pending approvals
        print("Pending Approvals:")
        approvals = self.interaction_dashboard.get_pending_approvals_display()
        if approvals:
            print(approvals)
        else:
            print("[No pending approvals]")
        print()
        
        # Active tasks
        print("Active Tasks:")
        tasks = self.interaction_dashboard.get_active_tasks_display()
        if tasks:
            print(tasks)
        else:
            print("[No active tasks]")
        print()
        
        # Execution feedback
        print("Recent Execution Feedback:")
        feedback = self.interaction_dashboard.get_execution_feedback_summary()
        if feedback:
            print(feedback)
        else:
            print("[No recent feedback]")
    
    def display_developer_dashboard(self):
        """Display developer/audit mode dashboard"""
        print("\n" + "="*80)
        print("DEVELOPER MODE - Phase Tabs & Audit Timeline")
        print("="*80 + "\n")
        
        state = self.manager.get_state()
        dev_mode = state.developer_mode
        
        print(f"Developer Mode: {'ACTIVE' if dev_mode.mode_active else 'INACTIVE'}")
        print(f"Last Accessed: {dev_mode.last_accessed}")
        print()
        
        # Available phases
        if dev_mode.available_phases:
            print("Available Phases:")
            for phase in dev_mode.available_phases:
                print(f"  - Phase {phase}")
            print()
        
        # Audit timeline
        if dev_mode.audit_timeline:
            print("Recent Audit Timeline:")
            for i, event in enumerate(dev_mode.audit_timeline[-10:], 1):
                print(f"  {i}. {event}")
    
    def navigate_to_dashboard(self, mode: str, reason: str = "CLI navigation"):
        """Navigate to specified dashboard"""
        try:
            dash_mode = DashboardMode[mode.upper()]
            self.manager.navigate_to(dash_mode, reason)
            print(f"✓ Navigated to {dash_mode.value.upper()} Dashboard")
        except KeyError:
            print(f"✗ Invalid dashboard mode: {mode}")
            print(f"  Available modes: {', '.join([m.value for m in DashboardMode])}")
    
    def set_environment(self, env: str, reason: str = "CLI environment change"):
        """Set execution environment"""
        try:
            execution_env = ExecutionEnvironment[env.upper()]
            self.manager.set_environment(execution_env, reason)
            print(f"✓ Environment changed to {execution_env.value.upper()}")
        except KeyError:
            print(f"✗ Invalid environment: {env}")
            print(f"  Available: {', '.join([e.value for e in ExecutionEnvironment])}")
    
    def toggle_developer_mode(self):
        """Toggle developer mode on/off"""
        current_state = self.manager.get_state()
        is_active = current_state.developer_mode.mode_active
        
        router = self.manager.router
        router.toggle_developer_mode()
        
        new_state = self.manager.get_state()
        new_is_active = new_state.developer_mode.mode_active
        
        if new_is_active:
            print("✓ Developer Mode ENABLED")
        else:
            print("✓ Developer Mode DISABLED")
    
    def export_state(self, output_file: Optional[str] = None):
        """Export current dashboard state to JSON"""
        if output_file is None:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            output_file = f"dashboard_state_{timestamp}.json"
        
        output_path = Path(output_file)
        state_dict = self.manager.export_state_json()
        
        with open(output_path, 'w') as f:
            json.dump(state_dict, f, indent=2)
        
        print(f"✓ State exported to {output_path.absolute()}")
    
    def export_audit_trail(self, output_file: Optional[str] = None):
        """Export audit trail to JSON"""
        if output_file is None:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            output_file = f"audit_trail_{timestamp}.json"
        
        output_path = Path(output_file)
        self.manager.export_audit_trail(output_path)
        
        print(f"✓ Audit trail exported to {output_path.absolute()}")
    
    def display_navigation_history(self, limit: int = 10):
        """Display navigation history"""
        history = self.manager.get_navigation_history()
        
        print("\nNavigation History (most recent first):")
        print("-" * 80)
        
        for i, event in enumerate(history[-limit:][::-1], 1):
            print(f"{i}. {event.timestamp}: {event.from_mode.value} → {event.to_mode.value}")
            if event.reason:
                print(f"   Reason: {event.reason}")
    
    def display_environment_history(self, limit: int = 10):
        """Display environment change history"""
        env_history = self.manager.event_bus.get_environment_history()
        
        print("\nEnvironment Change History (most recent first):")
        print("-" * 80)
        
        for i, event in enumerate(env_history[-limit:][::-1], 1):
            print(f"{i}. {event.timestamp}: {event.from_environment.value} → {event.to_environment.value}")
            if event.reason:
                print(f"   Reason: {event.reason}")
    
    def display_help(self):
        """Display help information"""
        print("""
╔════════════════════════════════════════════════════════════════════╗
║             BUDDY PHASE 25 - Dashboard Application                 ║
║                   UI/UX Consolidation Interface                    ║
╚════════════════════════════════════════════════════════════════════╝

AVAILABLE DASHBOARDS:

  learning      - Learning insights & adaptive behavior
  operations    - Real-time monitoring & system health
  interaction   - Chat, approvals & task management
  developer     - Phase tabs 1-24 & audit timeline

PHASE 24 INTEGRATION (Autonomous System Observability):

  phase24-conflicts         - Display unresolved tool conflicts
  phase24-rollbacks [limit] - Display recent rollback events (default: 10)
  phase24-signals           - Display high-confidence learning signals
  phase24-health            - Display system health snapshot
  phase24-summary           - Display complete Phase 24 summary

COMMANDS:

  navigate <mode>           - Navigate to dashboard (learning, operations, interaction, developer)
  environment <env>         - Change execution environment (mock, dry_run, live, locked)
  dev-mode                  - Toggle developer mode on/off
  export-state [file]       - Export current dashboard state to JSON
  export-audit [file]       - Export audit trail to JSON
  nav-history [limit]       - Display navigation history (default: 10)
  env-history [limit]       - Display environment change history (default: 10)
  status                    - Display current dashboard status
  help                      - Show this help message

EXAMPLES:

  # View operations dashboard
  python dashboard_app.py operations

  # Switch to learning dashboard and enable dry-run
  python dashboard_app.py learning
  python dashboard_app.py environment dry_run

  # View Phase 24 orchestration data
  python dashboard_app.py phase24-health
  python dashboard_app.py phase24-conflicts
  python dashboard_app.py phase24-rollbacks 20

  # Toggle developer mode to see phase tabs
  python dashboard_app.py dev-mode

  # Export state for backup/analysis
  python dashboard_app.py export-state my_state.json

  # View navigation audit trail
  python dashboard_app.py nav-history 20
        """)
    
    def display_phase24_conflicts(self):
        """Display Phase 24 unresolved conflicts"""
        print("\n" + "="*80)
        print("PHASE 24 - TOOL CONFLICTS (Autonomous System)")
        print("="*80 + "\n")
        
        try:
            adapter = Phase24AggregateAdapter()
            conflict_adapter = adapter.conflict_adapter
            
            unresolved = conflict_adapter.get_unresolved_conflicts()
            if not unresolved:
                print("[No unresolved conflicts detected]")
                return
            
            print(f"Total Unresolved Conflicts: {len(unresolved)}\n")
            
            for i, conflict in enumerate(unresolved, 1):
                print(f"{i}. Conflict ID: {conflict.conflict_id}")
                print(f"   Tools Involved: {', '.join(conflict.tools_involved)}")
                print(f"   Type: {conflict.conflict_type}")
                print(f"   Severity: {conflict.severity.upper()}")
                print(f"   Strategy: {conflict.resolution_strategy}")
                print(f"   Status: {conflict.resolution_status.upper()}")
                print()
        except Exception as e:
            print(f"✗ Error reading Phase 24 conflicts: {str(e)}")
    
    def display_phase24_rollbacks(self, limit: int = 10):
        """Display Phase 24 recent rollback events"""
        print("\n" + "="*80)
        print("PHASE 24 - ROLLBACK EVENTS (Autonomous System)")
        print("="*80 + "\n")
        
        try:
            adapter = Phase24AggregateAdapter()
            rollback_adapter = adapter.rollback_adapter
            
            rollbacks = rollback_adapter.get_recent_rollbacks(limit=limit)
            if not rollbacks:
                print("[No rollback events recorded]")
                return
            
            print(f"Recent Rollbacks (Last {limit}):\n")
            
            for i, rb in enumerate(rollbacks, 1):
                print(f"{i}. Rollback ID: {rb.rollback_id}")
                print(f"   Trigger: {rb.trigger.upper()}")
                print(f"   Reason: {rb.reason}")
                print(f"   Recovery Status: {rb.recovery_status.upper()}")
                print(f"   Duration: {rb.duration_ms}ms")
                print(f"   Affected Executions: {len(rb.affected_executions)}")
                print()
        except Exception as e:
            print(f"✗ Error reading Phase 24 rollbacks: {str(e)}")
    
    def display_phase24_signals(self):
        """Display Phase 24 high-confidence learning signals"""
        print("\n" + "="*80)
        print("PHASE 24 - LEARNING SIGNALS (Autonomous System)")
        print("="*80 + "\n")
        
        try:
            adapter = Phase24AggregateAdapter()
            signal_adapter = adapter.learning_adapter
            
            high_conf = signal_adapter.get_high_confidence_signals(threshold=0.8)
            if not high_conf:
                print("[No high-confidence learning signals]")
                return
            
            print(f"High-Confidence Signals (confidence >= 0.80):\n")
            
            for i, sig in enumerate(high_conf, 1):
                print(f"{i}. Signal ID: {sig.signal_id}")
                print(f"   Type: {sig.signal_type}")
                print(f"   Tool: {sig.tool_name}")
                print(f"   Insight: {sig.insight}")
                print(f"   Confidence: {sig.confidence:.2%}")
                print(f"   Recommended Action: {sig.recommended_action}")
                print()
        except Exception as e:
            print(f"✗ Error reading Phase 24 signals: {str(e)}")
    
    def display_phase24_health(self):
        """Display Phase 24 system health snapshot"""
        print("\n" + "="*80)
        print("PHASE 24 - SYSTEM HEALTH (Autonomous System)")
        print("="*80 + "\n")
        
        try:
            adapter = Phase24AggregateAdapter()
            health_adapter = adapter.health_adapter
            
            snapshot = health_adapter.get_health_snapshot()
            if not snapshot:
                print("[No health snapshot available]")
                return
            
            tier = health_adapter.get_health_tier(snapshot.health_score)
            indicators = health_adapter.get_health_indicators()
            
            print(f"Timestamp: {snapshot.timestamp}")
            print(f"Health Score: {snapshot.health_score:.1f}/100 [{tier}]")
            print(f"Execution Mode: {snapshot.execution_mode}")
            print(f"Active Tools: {snapshot.active_tools}")
            print(f"Completed Executions: {snapshot.completed_executions}")
            print(f"Failed Executions: {snapshot.failed_executions}")
            print(f"Blocked Executions: {snapshot.blocked_executions}")
            print(f"Average Confidence: {snapshot.average_confidence:.2%}")
            
            if snapshot.anomalies:
                print(f"\n⚠ Anomalies Detected:")
                for anomaly in snapshot.anomalies:
                    print(f"  - {anomaly}")
        except Exception as e:
            print(f"✗ Error reading Phase 24 health: {str(e)}")
    
    def display_phase24_summary(self):
        """Display complete Phase 24 summary"""
        print("\n" + "="*80)
        print("PHASE 24 - COMPLETE SUMMARY (Autonomous System Observability)")
        print("="*80 + "\n")
        
        try:
            adapter = Phase24AggregateAdapter()
            
            # Operations summary
            print("═" * 80)
            print("OPERATIONS CONTEXT")
            print("═" * 80)
            ops_summary = adapter.get_operations_summary()
            if ops_summary:
                print(f"Execution Mode: {ops_summary.get('execution_mode', 'UNKNOWN')}")
                print(f"Health Score: {ops_summary.get('health_score', 'N/A')}")
                print(f"Active Tools: {ops_summary.get('active_tools', 0)}")
                print(f"Total Executions: {ops_summary.get('total_executions', 0)}")
                print(f"Success Rate: {ops_summary.get('success_rate', 0):.1%}")
            print()
            
            # Learning summary
            print("═" * 80)
            print("LEARNING CONTEXT")
            print("═" * 80)
            learn_summary = adapter.get_learning_summary()
            if learn_summary:
                print(f"Total Signals: {learn_summary.get('total', 0)}")
                print(f"High-Confidence: {learn_summary.get('high_confidence_count', 0)}")
                print(f"Average Confidence: {learn_summary.get('avg_confidence', 0):.2%}")
            print()
            
            # Interaction summary
            print("═" * 80)
            print("INTERACTION CONTEXT")
            print("═" * 80)
            interact_summary = adapter.get_interaction_summary()
            if interact_summary:
                print(f"Pending Approvals: {interact_summary.get('pending_approvals', 0)}")
                print(f"Blocked by Safety: {interact_summary.get('blocked_by_safety', 0)}")
                print(f"Recent Conflicts: {len(interact_summary.get('recent_conflicts', []))}")
        except Exception as e:
            print(f"✗ Error generating Phase 24 summary: {str(e)}")



def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Phase 25 - Dashboard Application",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python dashboard_app.py learning                     # Show learning dashboard
  python dashboard_app.py operations                   # Show operations dashboard
  python dashboard_app.py environment dry_run          # Set dry-run mode
  python dashboard_app.py dev-mode                     # Toggle developer mode
  python dashboard_app.py export-state my_state.json   # Export state
        """
    )
    
    parser.add_argument(
        "command",
        nargs='?',
        help="Dashboard or command to execute",
        choices=[
            'learning', 'operations', 'interaction', 'developer',
            'navigate', 'environment', 'dev-mode',
            'export-state', 'export-audit',
            'nav-history', 'env-history',
            'phase24-conflicts', 'phase24-rollbacks', 'phase24-signals', 'phase24-health',
            'phase24-summary',
            'status', 'help'
        ]
    )
    
    parser.add_argument(
        "args",
        nargs='*',
        help="Additional arguments for commands"
    )
    
    args = parser.parse_args()
    
    # If no command, show help
    if not args.command:
        args.command = 'help'
    
    app = DashboardApp()
    
    # Route commands
    if args.command == 'learning':
        app.display_learning_dashboard()
    
    elif args.command == 'operations':
        app.display_operations_dashboard()
    
    elif args.command == 'interaction':
        app.display_interaction_dashboard()
    
    elif args.command == 'developer':
        app.display_developer_dashboard()
    
    elif args.command == 'navigate':
        if args.args:
            app.navigate_to_dashboard(args.args[0])
        else:
            print("✗ navigate requires a dashboard mode (learning, operations, interaction, developer)")
    
    elif args.command == 'environment':
        if args.args:
            app.set_environment(args.args[0])
        else:
            print("✗ environment requires an environment (mock, dry_run, live, locked)")
    
    elif args.command == 'dev-mode':
        app.toggle_developer_mode()
    
    elif args.command == 'export-state':
        output_file = args.args[0] if args.args else None
        app.export_state(output_file)
    
    elif args.command == 'export-audit':
        output_file = args.args[0] if args.args else None
        app.export_audit_trail(output_file)
    
    elif args.command == 'nav-history':
        limit = int(args.args[0]) if args.args else 10
        app.display_navigation_history(limit)
    
    elif args.command == 'env-history':
        limit = int(args.args[0]) if args.args else 10
        app.display_environment_history(limit)
    
    elif args.command == 'status':
        state = app.manager.get_state()
        print("\n" + "="*80)
        print("DASHBOARD STATUS")
        print("="*80)
        print(f"Current Dashboard: {state.current_mode.value.upper()}")
        print(f"Environment: {state.environment.value.upper()}")
        print(f"Developer Mode: {'ACTIVE' if state.developer_mode.mode_active else 'INACTIVE'}")
        print(f"State ID: {state.state_id}")
        print(f"Last Updated: {state.timestamp}")
        print()
        
        nav_history = app.manager.get_navigation_history()
        print(f"Total Navigations: {len(nav_history)}")
        
        env_history = app.manager.event_bus.get_environment_history()
        print(f"Environment Changes: {len(env_history)}")
    
    elif args.command == 'phase24-conflicts':
        app.display_phase24_conflicts()
    
    elif args.command == 'phase24-rollbacks':
        limit = int(args.args[0]) if args.args else 10
        app.display_phase24_rollbacks(limit)
    
    elif args.command == 'phase24-signals':
        app.display_phase24_signals()
    
    elif args.command == 'phase24-health':
        app.display_phase24_health()
    
    elif args.command == 'phase24-summary':
        app.display_phase24_summary()
    
    elif args.command == 'help':
        app.display_help()


if __name__ == "__main__":
    main()
