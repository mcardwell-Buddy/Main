from backend.iterative_executor import IterativeExecutor
from backend.iterative_decomposer import iterative_decomposer

executor = IterativeExecutor('20 * 3')
analysis = iterative_decomposer.analyze_goal_complexity('20 * 3')
print(f'Analysis: {analysis}')

result = executor._execute_simple(analysis)
print(f'\nResult keys: {list(result.keys())}')
print(f'Total steps: {result["total_steps"]}')
print(f'Final answer: {result["final_answer"]}')

if result['execution_log']:
    print(f'\nFirst step obs: {list(result["execution_log"][0].get("observation", {}).keys())}')
