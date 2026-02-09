from backend.iterative_executor import IterativeExecutor

executor = IterativeExecutor('20 * 3')

# Create sample steps
sample_steps = [{
    'phase': 'step',
    'decision': {'tool': 'calculate'},
    'observation': {'result': 60, 'expression': '20 * 3'},
}]

answer = executor._extract_answer_from_steps(sample_steps)
print(f'Extracted answer: {answer}')
