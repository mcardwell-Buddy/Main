from backend.agent import Agent

agent = Agent('10 + 5', preferred_tool='calculate')
steps = []
for i in range(1):  # Just first step
    state = agent.step()
    steps.append(state)
    print(f'Step {i}:')
    print(f'  Done: {state.get("done")}')
    print(f'  Tool: {state.get("decision", {}).get("tool")}')
    print(f'  Observation: {state.get("observation", {})}')
    if state.get('done'):
        print(f'  Agent marked done')
        break

print(f'\nAgent state.done: {agent.state.done}')
print(f'Agent state.steps: {agent.state.steps}')
print(f'Total steps taken: {len(steps)}')
