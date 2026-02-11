from Back_End.agent import Agent as AtomicAgent

agent = AtomicAgent('20 * 3', preferred_tool='calculate')
steps = []

for i in range(1):
    state = agent.step()
    steps.append(state)
    
    obs = state.get('observation', {})
    print(f'Observation: {obs}')
    print(f'Has result: {"result" in obs}')
    
    if obs and 'error' not in obs and 'result' in obs:
        print('Breaking - result found')
        break

print(f'\nTotal steps: {len(steps)}')

# Try extraction
for step in reversed(steps):
    obs = step.get('observation', {})
    print(f'Obs keys: {list(obs.keys())}')
    if obs and 'result' in obs:
        print(f'Found result: {obs["result"]}')
        break

