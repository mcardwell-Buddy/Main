"""
Buddy Phase 25 Dry-Run Test Scenario
Purpose: Full end-to-end test of Phase 25 capabilities in MOCK/DRY_RUN mode
Outputs: JSONL logs for Whiteboard consumption
"""

import os
import json
from pathlib import Path
from datetime import datetime, timedelta
import random

# -------------------------
# Environment Setup
# -------------------------
os.environ["MOCK"] = "true"        # All web interactions simulated
os.environ["DRY_RUN"] = "true"     # Prevent live changes to GHL or external sites

OUTPUT_DIR = Path("./outputs/phase25")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# -------------------------
# Import Phase 25 Components
# -------------------------
from phase25_orchestrator import (
    Phase25Orchestrator, 
    Goal, 
    Task,
    TaskType,
    TaskPriority,
    GoalStatus,
    TaskStatus,
    ExecutionMode
)
from phase25_dashboard_aggregator import Phase25DashboardAggregator

# -------------------------
# Initialize Core Phase 25 Agents
# -------------------------
orchestrator = Phase25Orchestrator()
aggregator = Phase25DashboardAggregator()

# -------------------------
# Define Test Goals
# -------------------------
test_goals = [
    {
        "description": "Scrape 3 employers from Mployer, enrich data, prepare GHL draft campaigns",
        "goal_type": TaskType.SCRAPE,
        "owner": "system",
        "approval_required": True,
        "success_metrics": ["3 employers scraped", "enriched data collected", "GHL draft created"]
    },
    {
        "description": "Explore 2 new side hustle opportunities, generate revenue potential report",
        "goal_type": TaskType.SIDE_HUSTLE,
        "owner": "system",
        "approval_required": False,
        "success_metrics": ["2 opportunities identified", "revenue potential calculated"]
    },
    {
        "description": "Monitor competitor GHL pipelines and market opportunities",
        "goal_type": TaskType.RESEARCH,
        "owner": "system",
        "approval_required": False,
        "success_metrics": ["competitor analysis complete", "market trends identified"]
    }
]

# -------------------------
# Ingest Goals
# -------------------------
print("📝 Ingesting test goals...")
goal_ids = []
for idx, goal_data in enumerate(test_goals):
    goal_id = f"G25-{idx+1:03d}"
    goal = Goal(
        goal_id=goal_id,
        description=goal_data["description"],
        owner=goal_data["owner"],
        goal_type=goal_data["goal_type"],
        approval_required=goal_data["approval_required"],
        success_metrics=goal_data["success_metrics"]
    )
    success = orchestrator.ingest_goal(goal)
    if success:
        goal_ids.append(goal_id)
        print(f"  ✓ Goal {goal_id}: {goal_data['description'][:50]}...")
    else:
        print(f"  ✗ Failed to ingest goal {goal_id}")

# -------------------------
# Create Test Tasks
# -------------------------
print("\n📋 Creating test tasks...")
task_configs = [
    {
        "goal_idx": 0,
        "task_type": TaskType.SCRAPE,
        "parameters": {"target_url": "https://mployer.com/employers", "query": "AI companies"},
        "priority": TaskPriority.HIGH
    },
    {
        "goal_idx": 0,
        "task_type": TaskType.RESEARCH,
        "parameters": {"domain": "GHL marketing", "keywords": ["campaigns", "automation"]},
        "priority": TaskPriority.HIGH
    },
    {
        "goal_idx": 0,
        "task_type": TaskType.GHL_CAMPAIGN,
        "parameters": {"template": "B2B outreach", "contacts_count": 3},
        "priority": TaskPriority.MEDIUM
    },
    {
        "goal_idx": 1,
        "task_type": TaskType.SIDE_HUSTLE,
        "parameters": {"market": "freelance", "category": "AI automation"},
        "priority": TaskPriority.MEDIUM
    },
    {
        "goal_idx": 1,
        "task_type": TaskType.SIDE_HUSTLE,
        "parameters": {"market": "saas", "category": "productivity tools"},
        "priority": TaskPriority.MEDIUM
    },
    {
        "goal_idx": 2,
        "task_type": TaskType.RESEARCH,
        "parameters": {"domain": "competitor analysis", "keywords": ["GHL", "automation"]},
        "priority": TaskPriority.LOW
    }
]

task_ids = []
for config in task_configs:
    task_id = orchestrator.create_task(
        goal_id=goal_ids[config["goal_idx"]],
        task_type=config["task_type"],
        priority=config["priority"],
        parameters=config["parameters"]
    )
    if task_id:
        task_ids.append(task_id)
        print(f"  ✓ Task {task_id}: {config['task_type'].value} for goal {goal_ids[config['goal_idx']]}")
    else:
        print(f"  ✗ Failed to create task for goal {goal_ids[config['goal_idx']]}")

# -------------------------
# Execute Tasks (Dry-Run Mode)
# -------------------------
print("\n⚙️  Executing tasks in DRY_RUN mode...")
execution_modes = [ExecutionMode.MOCK, ExecutionMode.DRY_RUN]
execution_statuses = [TaskStatus.COMPLETED, TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.COMPLETED]

for idx, task_id in enumerate(task_ids):
    execution_mode = random.choice(execution_modes)
    status = random.choice(execution_statuses)
    
    # Log execution with proper signature
    orchestrator.log_execution(
        task_id=task_id,
        tool_name=f"tool_{task_id[:8]}",
        action_type="scrape" if random.choice([True, False]) else "process",
        status=status.value,
        data={"result": f"Simulated output for {task_id}"},
        duration_ms=random.randint(100, 5000)
    )
    print(f"  ✓ {task_id}: {status.value} ({execution_mode.value})")

# -------------------------
# Simulate State Transitions
# -------------------------
print("\n🔄 Logging state transitions...")
states = [GoalStatus.CREATED, GoalStatus.APPROVED, GoalStatus.IN_PROGRESS, GoalStatus.COMPLETED]
for goal_id in goal_ids:
    for idx, state in enumerate(states):
        prev_state = states[idx-1].value if idx > 0 else "none"
        orchestrator._log_state_transition(
            from_state=prev_state,
            to_state=state.value,
            trigger="test_execution",
            details=f"Goal {goal_id} transitioned to {state.value}"
        )
    print(f"  ✓ {goal_id}: transitioned through all states")

# -------------------------
# Simulate Learning Signals
# -------------------------
print("\n📊 Generating learning signals...")
signal_types = ["confidence_increase", "pattern_detected", "efficiency_gain", "risk_identified"]
for idx in range(len(goal_ids) * 3):
    orchestrator.log_learning_signal(
        signal_type=random.choice(signal_types),
        tool_name=random.choice(["web_navigator", "ghl_analyzer", "hustle_explorer"]),
        insight=f"Insight from Phase 25 task execution #{idx}",
        confidence=round(random.uniform(0.6, 1.0), 2),
        recommended_action="Continue execution"
    )
    print(f"  ✓ Signal #{idx+1} logged")


# -------------------------
# Simulate Conflicts
# -------------------------
print("\n⚠️  Simulating multi-agent conflicts...")
conflicts = [
    ("resource_contention", "Multiple tasks competing for GHL API quota", "medium"),
    ("data_mismatch", "Conflicting employer data from different sources", "low"),
    ("execution_conflict", "Rollback required due to failed task execution", "high")
]
for conflict_type, description, severity in conflicts:
    orchestrator.log_execution(
        task_id=f"conflict_{conflict_type}",
        tool_name="conflict_resolver",
        action_type="detect_conflict",
        status="warning",
        data={"description": description, "severity": severity},
        duration_ms=0
    )
    print(f"  ⚠️  {conflict_type}: {description}")

# -------------------------
# Simulate Rollback Events
# -------------------------
print("\n🔙 Simulating rollback events...")
rollbacks = [
    ("ROLLBACK_001", task_ids[2] if len(task_ids) > 2 else "TASK_003", "GHL draft validation failed"),
    ("ROLLBACK_002", task_ids[0] if len(task_ids) > 0 else "TASK_001", "Scrape encountered rate limiting")
]
for rollback_id, task_id, reason in rollbacks:
    orchestrator.log_execution(
        task_id=task_id,
        tool_name="rollback_manager",
        action_type="rollback",
        status="completed",
        data={"rollback_id": rollback_id, "reason": reason},
        duration_ms=random.randint(500, 3000)
    )
    print(f"  🔙 {rollback_id}: {reason}")

# -------------------------
# Get Dashboard Data
# -------------------------
print("\n📈 Generating dashboard data...")
operations_data = aggregator.get_operations_dashboard_data()
learning_data = aggregator.get_learning_dashboard_data()
hustle_data = aggregator.get_side_hustle_dashboard_data()

print(f"  ✓ Operations dashboard: {operations_data.get('active_goals', 0)} active goals")
print(f"  ✓ Learning dashboard: {len(learning_data.get('learning_signals', []))} signals")
print(f"  ✓ Hustle dashboard: {len(hustle_data.get('active_opportunities', []))} opportunities")

# -------------------------
# Save Test Summary
# -------------------------
print("\n💾 Saving test summary...")
summary = {
    "test_name": "Phase 25 Dry-Run Test",
    "timestamp": datetime.now().isoformat(),
    "goals_created": len(goal_ids),
    "tasks_created": len(task_ids),
    "execution_mode": "DRY_RUN",
    "mock_enabled": True,
    "outputs_directory": str(OUTPUT_DIR.resolve()),
    "status": "✅ COMPLETE"
}

summary_path = OUTPUT_DIR / "test_summary.json"
with open(summary_path, 'w') as f:
    json.dump(summary, f, indent=2)

# -------------------------
# Final Report
# -------------------------
print("\n" + "="*60)
print("✅ PHASE 25 DRY-RUN TEST COMPLETE")
print("="*60)
print(f"\nTest Summary:")
print(f"  • Goals created: {len(goal_id)}")
print(f"  • Tasks created: {len(task_ids)}")
print(f"  • Conflicts simulated: {len(conflicts)}")
print(f"  • Rollbacks simulated: {len(rollbacks)}")
print(f"  • Learning signals generated: {len(learning_data.get('learning_signals', []))}")
print(f"\nOutput Files:")
print(f"  • Goals: {OUTPUT_DIR / 'goals.jsonl'}")
print(f"  • Tasks: {OUTPUT_DIR / 'tasks.jsonl'}")
print(f"  • Executions: {OUTPUT_DIR / 'tool_execution_log.jsonl'}")
print(f"  • State Transitions: {OUTPUT_DIR / 'execution_state_transitions.jsonl'}")
print(f"  • Learning Signals: {OUTPUT_DIR / 'learning_signals.jsonl'}")
print(f"  • Summary: {summary_path}")
print(f"\n📊 Whiteboard should now display Phase 25 test data!")
print(f"🔗 Dashboard: http://localhost:3001 → Click Buddy → View Whiteboard")
print("="*60 + "\n")

