#!/usr/bin/env python3
"""Quick proposal demo - shows one proposal output"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from Back_End.task_breakdown_and_proposal import TaskBreakdownEngine
from Back_End.proposal_presenter import ProposalPresenter
from Back_End.cost_estimator import ServiceTier

# Initialize
engine = TaskBreakdownEngine(serpapi_tier=ServiceTier.FREE)
presenter = ProposalPresenter()

# Test mission
objective = "Research the latest machine learning trends and create a technical summary document"

print("\n" + "="*80)
print("  UNIFIED PROPOSAL SYSTEM - SAMPLE OUTPUT")
print("="*80)
print(f"\nUser Request: {objective}\n")

# Analyze task
print("Processing task...")
task_breakdown = engine.analyze_task(objective)
print(f"✓ Identified {len(task_breakdown.steps)} steps\n")

# Create proposal
proposal = presenter.create_proposal(
    mission_id="mission_demo_001",
    objective=objective,
    task_breakdown=task_breakdown,
)

# Get dict
proposal_dict = proposal.to_dict()

# Pretty print
print("-" * 80)
print("PROPOSAL DISPLAY")
print("-" * 80)
print(f"\n📋 {proposal_dict['mission_title']}")
print(f"   {proposal_dict['objective']}\n")

print("📝 SUMMARY")
print(f"   {proposal_dict['executive_summary']}\n")

metrics = proposal_dict['metrics']
print("📊 STEPS")
print(f"   Total: {metrics['total_steps']} | Buddy: {metrics['buddy_steps']} | You: {metrics['human_steps']} | Hybrid: {metrics['hybrid_steps']}\n")

costs = proposal_dict['costs']
print("💰 COST")
print(f"   Total: ${costs['total_usd']:.4f}")
if costs['breakdown']:
    for item in costs['breakdown']:
        print(f"      {item['service']}: ${item['cost_usd']:.4f}")
print()

time_est = proposal_dict['time']
print("⏱️  TIME")
print(f"   My work: {time_est['buddy_seconds']:.1f} seconds")
print(f"   Your time: {time_est['human_minutes']} minutes")
print(f"   Total: ~{time_est['total_minutes']} minutes\n")

print("🎯 OPTIONS: [Approve] [Modify] [Reject]\n")

print("-" * 80)
print("DETAILED STEPS")
print("-" * 80)

steps = proposal_dict['task_breakdown']['steps']
for step in steps:
    print(f"\nStep {step['step_number']}: {step['description']}")
    print(f"   Type: {step['step_type'].replace('_', ' ').upper()}")
    if step.get('estimated_cost'):
        print(f"   Cost: ${step['estimated_cost']['total_usd']:.4f}")
    print(f"   My time: {step.get('estimated_buddy_time', 0):.1f}s")
    if step.get('estimated_human_time', 0) > 0:
        print(f"   Your time: {step['estimated_human_time']}min")
    
    if step.get('is_blocking'):
        print(f"   ⚠️  BLOCKING - will wait for your input")

print("\n" + "-" * 80)
print("RAW JSON (sent to frontend)")
print("-" * 80)
print(json.dumps(proposal_dict, indent=2, default=str)[:2000] + "\n... (JSON continues)")
print("\n" + "="*80)
print("Sample proposal demo complete. Not starting mission execution.")
print("="*80 + "\n")

