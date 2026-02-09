from backend.agent import Agent

agent = Agent('10 + 5', preferred_tool='calculate')
steps = []
while not agent.state.done and len(steps) < 3:
    state = agent.step()
    steps.append(state)
    if state.get('done'):
        break

print('Total steps:', len(steps))
for i, step in enumerate(steps):
    obs = step.get('observation', {})
    print(f'Step {i}: obs_keys={list(obs.keys()) if obs else "empty"}')
    if 'result' in obs:
        print(f'  -> Found result: {obs["result"]}')

print('\nExtracting answer...')
for step in reversed(steps):
    obs = step.get('observation', {})
    if obs and 'result' in obs:
        print(f'Answer: The result is {obs["result"]}')
        break
else:
    print('Answer: Unable to extract')
