from backend.iterative_executor import IterativeExecutor
from backend.iterative_decomposer import iterative_decomposer

executor = IterativeExecutor('10 + 5')
analysis = executor._execute_simple(iterative_decomposer.analyze_goal_complexity('10 + 5'))
print('Result keys:', list(analysis.keys()))
print('Execution type:', analysis['execution_type'])
print('Total steps:', analysis['total_steps'])
print('Final answer:', analysis['final_answer'])
print('\nExecution log type:', type(analysis['execution_log']))
print('Log entries:', len(analysis['execution_log']))
if analysis['execution_log']:
    first = analysis['execution_log'][0]
    print('First entry keys:', list(first.keys()) if isinstance(first, dict) else type(first))
    if isinstance(first, dict) and 'observation' in first:
        print('  Observation keys:', list(first['observation'].keys()))
