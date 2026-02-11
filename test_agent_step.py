"""Test agent execution with verbose logging"""
import logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(message)s')

from Back_End.agent import Agent

agent = Agent("What is the current time?", domain="_global")
print(f"Initial state: steps={agent.state.steps}, done={agent.state.done}")

# Run first step
state1 = agent.step()
print(f"\nStep 1 result:")
print(f"  Tool: {state1.get('decision', {}).get('tool')}")
print(f"  Observation: {str(state1.get('observation', {}))[:100]}")
print(f"  Steps: {agent.state.steps}, Done: {agent.state.done}")

