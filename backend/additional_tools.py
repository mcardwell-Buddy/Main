import os
import json
import logging
from pathlib import Path
from backend.config import Config

def calculate(goal: str) -> dict:
    """Safely evaluate mathematical expressions"""
    # The goal is the expression to calculate
    expression = goal.strip()
    
    # Normalize 'x' or 'X' to '*' for multiplication
    expression = expression.replace('x', '*').replace('X', '*')
    
    try:
        # Only allow safe operations
        allowed_chars = set('0123456789+-*/() .')
        if not all(c in allowed_chars for c in expression):
            return {'error': 'Invalid characters in expression'}
        
        # Evaluate the expression safely
        result = eval(expression, {"__builtins__": {}}, {})
        return {'result': result, 'expression': goal.strip()}
    except Exception as e:
        return {'error': f'Calculation failed: {str(e)}'}

def read_file_tool(goal: str, max_lines: int = 100) -> dict:
    """Read file contents safely (read-only, bounded)"""
    # Extract filepath from goal (assuming goal contains the filepath)
    filepath = goal
    try:
        path = Path(filepath)
        if not path.exists():
            return {'error': 'File not found'}
        
        if not path.is_file():
            return {'error': 'Path is not a file'}
        
        # Security: prevent reading outside allowed directories (optional, adjust as needed)
        # For now, just read
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()[:max_lines]
        
        return {
            'filepath': str(path),
            'lines': len(lines),
            'content': ''.join(lines),
            'truncated': len(lines) >= max_lines
        }
    except Exception as e:
        return {'error': str(e)}

def list_directory(goal: str) -> dict:
    """List directory contents safely"""
    # Extract dirpath from goal
    dirpath = goal
    try:
        path = Path(dirpath)
        if not path.exists():
            return {'error': 'Directory not found'}
        
        if not path.is_dir():
            return {'error': 'Path is not a directory'}
        
        items = []
        for item in path.iterdir():
            items.append({
                'name': item.name,
                'type': 'dir' if item.is_dir() else 'file',
                'size': item.stat().st_size if item.is_file() else None
            })
        
        return {
            'dirpath': str(path),
            'items': items,
            'count': len(items)
        }
    except Exception as e:
        return {'error': str(e)}

def get_current_time(goal: str = "") -> dict:
    """Get current date and time in local timezone"""
    from datetime import datetime
    now = datetime.now()  # Local time instead of UTC
    return {
        'date': now.strftime('%m/%d/%y'),
        'time': now.strftime('%I:%M %p'),  # 12-hour format with AM/PM
        'iso': now.isoformat(),
        'timestamp': now.timestamp()
    }

def register_additional_tools(tool_registry):
    tool_registry.register(
        'calculate',
        calculate,
        mock_func=lambda goal: {'result': 42, 'expression': goal, 'mock': True},
        description='Evaluate mathematical expressions safely'
    )
    
    tool_registry.register(
        'read_file',
        read_file_tool,
        mock_func=lambda goal, **kw: {'filepath': goal, 'content': 'Mock file content', 'lines': 10, 'mock': True},
        description='Read file contents (read-only, bounded)'
    )
    
    tool_registry.register(
        'list_directory',
        list_directory,
        mock_func=lambda goal: {'dirpath': goal, 'items': [{'name': 'mock_file.txt', 'type': 'file'}], 'count': 1, 'mock': True},
        description='List directory contents'
    )
    
    tool_registry.register(
        'get_time',
        get_current_time,
        mock_func=lambda goal: {'date': '02/03/26', 'time': '09:43 PM', 'iso': '2026-02-03T21:43:00', 'timestamp': 1770190980, 'mock': True},
        description='Get current date and time'
    )

# Auto-register on import
from backend.tool_registry import tool_registry
register_additional_tools(tool_registry)
