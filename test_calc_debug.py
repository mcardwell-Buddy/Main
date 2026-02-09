import logging
logging.basicConfig(level=logging.DEBUG, format='%(message)s')

from backend.tool_selector import tool_selector

tool_name, tool_input, conf = tool_selector.select_tool('What is 100-10?', {'domain': '_global', 'step': 0})
print(f'\nFinal result:')
print(f'  Tool: {tool_name}')
print(f'  Input: "{tool_input}"')
print(f'  Confidence: {conf}')
