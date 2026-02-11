#!/usr/bin/env python3
"""Display sample mission proposal"""
import sys, json
sys.path.insert(0, r'c:\Users\micha\Buddy')

from Back_End.task_breakdown_and_proposal import TaskBreakdownEngine
from Back_End.proposal_presenter import ProposalPresenter
from Back_End.cost_estimator import ServiceTier

print('\n' + '='*80)
print('  BUDDY UNIFIED PROPOSAL SYSTEM - SAMPLE')
print('='*80)

objective = 'Research latest ML trends and create a technical summary document'
print(f'\nUser Request:\n   "{objective}"\n')

# Initialize
engine = TaskBreakdownEngine(serpapi_tier=ServiceTier.FREE)
presenter = ProposalPresenter()

# Process
print('▶ Processing task...')
task_breakdown = engine.analyze_task(objective)
print(f'✓ Identified {len(task_breakdown.steps)} execution steps\n')

print('▶ Generating proposal...')
proposal = presenter.create_proposal(
    mission_id='demo_001',
    objective=objective,
    task_breakdown=task_breakdown,
)
pd = proposal.to_dict()
print('✓ Proposal ready\n')

# Display
print('-' * 80)
print('WHAT BUDDY PROPOSES')
print('-' * 80)

print(f'\nMission: {pd["mission_title"]}')
print(f'Goal: {pd["objective"]}\n')

print(f'Summary: {pd["executive_summary"]}\n')

# Key metrics
m = pd['metrics']
print(f'Execution Breakdown:')
print(f'  • Total steps: {m["total_steps"]}')
print(f'  • Buddy (autonomous): {m["buddy_steps"]} steps')
print(f'  • You (manual): {m["human_steps"]} steps')
print(f'  • Hybrid (Buddy + approval): {m["hybrid_steps"]} steps\n')

# Costs
c = pd['costs']
print(f'Cost Estimate: ${c["total_usd"]:.4f} total')
if c.get('breakdown'):
    for item in c['breakdown'][:3]:
        print(f'  • {item["service"].upper()}: ${item["cost_usd"]:.4f}')
print()

# Time
t = pd['time']
print(f'Time Estimate:')
print(f'  • Buddy execution: {t["buddy_seconds"]:.1f} seconds (~{t["buddy_seconds"]/60:.1f} min)')
print(f'  • Your involvement: {t["human_minutes"]} minutes')
print(f'  • Total time: ~{t["total_minutes"]} minutes\n')

# Approval options
print('Next Step:')
print('  [1] ✓ Approve - Let Buddy execute this plan')
print('  [2] ⚙  Modify - Adjust costs, steps, or timeline')
print('  [3] ✗ Reject - Cancel this proposal\n')

# Show steps
print('-' * 80)
print(f'DETAILED EXECUTION PLAN ({len(pd["task_breakdown"]["steps"])} steps)')
print('-' * 80)

for idx, step in enumerate(pd['task_breakdown']['steps'][:5], 1):
    print(f'\nStep {step["step_number"]}: {step["description"]}')
    print(f'  Type: {step["step_type"].replace("_", " ").title()}')
    if step.get('estimated_cost'):
        cost = step['estimated_cost'].get('total_usd', 0)
        print(f'  Cost: ${cost:.4f}')
    bt = step.get('estimated_buddy_time', 0)
    if bt > 0:
        print(f'  Buddy time: {bt:.1f}s')
    if step.get('is_blocking'):
        print(f'  ⚠️  BLOCKING STEP - requires your input')

if len(pd['task_breakdown']['steps']) > 5:
    print(f'\n... and {len(pd["task_breakdown"]["steps"]) - 5} more steps')

print('\n' + '='*80)
print('Sample complete. Proposal is ready but NOT executing.')
print('='*80 + '\n')

