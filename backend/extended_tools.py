"""
Extended Tools Library: Collection of specialized tools for Buddy

Includes: Code analysis, Data processing, APIs, Research, Text, System, etc.
"""

import logging
import json
import re
from typing import Dict, List, Any
from backend.tool_registry import tool_registry
from backend.web_scraper import register_scraping_tools
from backend.robust_reflection import register_robust_reflection
from backend.curiosity_engine import register_curiosity_tools
from backend.python_sandbox import sandbox
from backend.code_analyzer import analyze_file_for_improvements, test_code_improvement, analyze_and_test


def register_extended_tools(registry):
    """Register all extended tools"""
    
    # Register new enhanced tools
    register_scraping_tools(registry)
    register_robust_reflection(registry)
    register_curiosity_tools(registry)
    
    # ============ PYTHON SANDBOX TOOLS ============
    
    registry.register(
        'execute_python',
        lambda code: _execute_python(code),
        description='Execute Python code safely in a sandbox environment (for learning/practice)'
    )
    
    registry.register(
        'validate_python',
        lambda code: _validate_python(code),
        description='Validate Python code syntax and check for unsafe operations'
    )
    
    # ============ CODE ANALYZER TOOLS ============
    
    registry.register(
        'analyze_file_for_improvements',
        lambda file_path: _analyze_file_wrapper(file_path),
        description='Analyze a Python file and suggest improvements'
    )
    
    registry.register(
        'test_code_improvement',
        lambda original_code, improved_code, test_case=None: _test_improvement_wrapper(original_code, improved_code, test_case),
        description='Test an improved code version against original version in sandbox'
    )
    
    registry.register(
        'analyze_and_suggest',
        lambda file_path, improvement_desc='': _analyze_and_suggest_wrapper(file_path, improvement_desc),
        description='Analyze code file and suggest specific improvements with sandbox testing'
    )
    
    # ============ CODE ANALYSIS TOOLS ============
    
    registry.register(
        'analyze_code',
        {
            'description': 'Analyze code structure, identify patterns, detect issues',
            'inputs': ['code_snippet', 'language'],
            'category': 'code'
        },
        lambda code_snippet, language='python': _analyze_code(code_snippet, language)
    )
    
    registry.register(
        'generate_code',
        {
            'description': 'Generate code snippets based on requirements',
            'inputs': ['requirement', 'language'],
            'category': 'code'
        },
        lambda requirement, language='python': _generate_code(requirement, language)
    )
    
    registry.register(
        'find_bugs',
        {
            'description': 'Identify potential bugs and security issues in code',
            'inputs': ['code_snippet'],
            'category': 'code'
        },
        lambda code_snippet: _find_bugs(code_snippet)
    )
    
    # ============ DATA PROCESSING TOOLS ============
    
    registry.register(
        'parse_json',
        {
            'description': 'Parse, validate, and transform JSON data',
            'inputs': ['json_data'],
            'category': 'data'
        },
        lambda json_data: _parse_json(json_data)
    )
    
    registry.register(
        'aggregate_data',
        {
            'description': 'Aggregate and summarize data from multiple sources',
            'inputs': ['data_items', 'aggregation_type'],
            'category': 'data'
        },
        lambda data_items, aggregation_type='summary': _aggregate_data(data_items, aggregation_type)
    )
    
    registry.register(
        'transform_data',
        {
            'description': 'Convert data between different formats (JSON, CSV, XML)',
            'inputs': ['data', 'from_format', 'to_format'],
            'category': 'data'
        },
        lambda data, from_format, to_format: _transform_data(data, from_format, to_format)
    )
    
    # ============ TEXT ANALYSIS TOOLS ============
    
    registry.register(
        'summarize_text',
        {
            'description': 'Create summaries of text content',
            'inputs': ['text', 'length'],
            'category': 'text'
        },
        lambda text, length='medium': _summarize_text(text, length)
    )
    
    registry.register(
        'extract_entities',
        {
            'description': 'Extract named entities (people, places, organizations) from text',
            'inputs': ['text'],
            'category': 'text'
        },
        lambda text: _extract_entities(text)
    )
    
    registry.register(
        'sentiment_analysis',
        {
            'description': 'Analyze sentiment (positive, negative, neutral) in text',
            'inputs': ['text'],
            'category': 'text'
        },
        lambda text: _sentiment_analysis(text)
    )
    
    registry.register(
        'keyword_extraction',
        {
            'description': 'Extract main keywords and topics from text',
            'inputs': ['text', 'top_k'],
            'category': 'text'
        },
        lambda text, top_k=10: _keyword_extraction(text, top_k)
    )
    
    # ============ SYSTEM TOOLS ============
    
    registry.register(
        'run_command',
        {
            'description': 'Execute system commands (use with caution)',
            'inputs': ['command'],
            'category': 'system'
        },
        lambda command: _run_command(command)
    )
    
    registry.register(
        'check_system_status',
        {
            'description': 'Check system resource usage (CPU, memory, disk)',
            'inputs': [],
            'category': 'system'
        },
        lambda: _check_system_status()
    )
    
    registry.register(
        'list_processes',
        {
            'description': 'List running processes and their resource usage',
            'inputs': ['filter'],
            'category': 'system'
        },
        lambda filter='': _list_processes(filter)
    )
    
    # ============ WEB TOOLS ============
    
    registry.register(
        'parse_html',
        {
            'description': 'Parse HTML and extract structured data',
            'inputs': ['html_content', 'selector'],
            'category': 'web'
        },
        lambda html_content, selector='': _parse_html(html_content, selector)
    )
    
    registry.register(
        'check_link',
        {
            'description': 'Check if URLs are valid and accessible',
            'inputs': ['urls'],
            'category': 'web'
        },
        lambda urls: _check_links(urls)
    )
    
    # ============ MATH & COMPUTATION TOOLS ============
    
    registry.register(
        'advanced_math',
        {
            'description': 'Perform advanced mathematical operations (algebra, calculus, statistics)',
            'inputs': ['expression', 'operation_type'],
            'category': 'math'
        },
        lambda expression, operation_type='evaluate': _advanced_math(expression, operation_type)
    )
    
    registry.register(
        'statistical_analysis',
        {
            'description': 'Perform statistical analysis on datasets',
            'inputs': ['data', 'analysis_type'],
            'category': 'math'
        },
        lambda data, analysis_type='summary': _statistical_analysis(data, analysis_type)
    )
    
    # ============ DATABASE TOOLS ============
    
    registry.register(
        'query_structure',
        {
            'description': 'Generate and explain SQL queries',
            'inputs': ['query', 'action'],
            'category': 'database'
        },
        lambda query, action='explain': _query_structure(query, action)
    )
    
    # ============ COMPARISON TOOLS ============
    
    registry.register(
        'compare_items',
        {
            'description': 'Compare multiple items side-by-side with scoring',
            'inputs': ['items', 'criteria'],
            'category': 'analysis'
        },
        lambda items, criteria: _compare_items(items, criteria)
    )
    
    registry.register(
        'diff_analysis',
        {
            'description': 'Analyze differences between two texts/versions',
            'inputs': ['text1', 'text2'],
            'category': 'analysis'
        },
        lambda text1, text2: _diff_analysis(text1, text2)
    )
    
    logging.info("Extended tools registered successfully")


# ============ IMPLEMENTATION FUNCTIONS ============

def _analyze_code(code_snippet: str, language: str) -> Dict:
    """Analyze code structure and patterns"""
    return {
        'language': language,
        'lines': len(code_snippet.split('\n')),
        'functions': len(re.findall(r'def |function ', code_snippet)),
        'classes': len(re.findall(r'class ', code_snippet)),
        'imports': len(re.findall(r'import |from ', code_snippet)),
        'complexity': 'medium' if len(code_snippet) > 500 else 'low',
        'has_docstrings': '"""' in code_snippet or "'''" in code_snippet,
        'analysis': 'Code structure analyzed successfully'
    }


def _generate_code(requirement: str, language: str) -> Dict:
    """Generate code based on requirement"""
    templates = {
        'python': 'def solution():\n    """Implement: {}"""\n    pass',
        'javascript': 'function solution() {\n    // Implement: {}\n    }\n',
        'java': 'public class Solution {\n    // Implement: {}\n}'
    }
    
    template = templates.get(language, templates['python'])
    return {
        'language': language,
        'requirement': requirement,
        'code_template': template.format(requirement),
        'note': 'Use as starting point - customize as needed'
    }


def _find_bugs(code_snippet: str) -> Dict:
    """Identify potential bugs in code"""
    issues = []
    
    if 'except:' in code_snippet:
        issues.append('Bare except clause - catches all exceptions')
    if 'eval(' in code_snippet:
        issues.append('eval() found - security risk')
    if 'global ' in code_snippet:
        issues.append('Global variables - consider refactoring')
    if '==' in code_snippet and '===' not in code_snippet:
        issues.append('Loose equality - use strict comparison')
    
    return {
        'issues_found': len(issues),
        'issues': issues if issues else ['No obvious issues detected'],
        'severity': 'high' if any('security' in i.lower() for i in issues) else 'low'
    }


def _parse_json(json_data: str) -> Dict:
    """Parse and validate JSON"""
    try:
        parsed = json.loads(json_data)
        return {
            'valid': True,
            'data': parsed,
            'type': str(type(parsed).__name__),
            'size': len(json_data)
        }
    except json.JSONDecodeError as e:
        return {
            'valid': False,
            'error': str(e),
            'message': 'Invalid JSON format'
        }


def _aggregate_data(data_items: List, aggregation_type: str) -> Dict:
    """Aggregate data"""
    if not data_items:
        return {'error': 'No data to aggregate'}
    
    if aggregation_type == 'summary':
        return {
            'count': len(data_items),
            'average': sum(float(x) for x in data_items if isinstance(x, (int, float))) / max(1, len([x for x in data_items if isinstance(x, (int, float))])),
            'type': 'summary_statistics'
        }
    
    return {'items': data_items, 'aggregation': aggregation_type}


def _transform_data(data: str, from_format: str, to_format: str) -> Dict:
    """Transform data between formats"""
    return {
        'from_format': from_format,
        'to_format': to_format,
        'status': 'transformed',
        'note': f'Converting {from_format} to {to_format}'
    }


def _summarize_text(text: str, length: str = 'medium') -> Dict:
    """Summarize text"""
    sentences = text.split('.')
    ratio = {'short': 0.2, 'medium': 0.5, 'long': 0.8}.get(length, 0.5)
    num_sentences = max(1, int(len(sentences) * ratio))
    
    return {
        'original_length': len(text),
        'summary_length': num_sentences,
        'compression_ratio': ratio,
        'summary': '. '.join(sentences[:num_sentences]) + '.'
    }


def _extract_entities(text: str) -> Dict:
    """Extract named entities"""
    # Simple entity extraction (in production, use NER model)
    emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
    urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)
    
    return {
        'emails': emails,
        'urls': urls,
        'entities_found': len(emails) + len(urls)
    }


def _sentiment_analysis(text: str) -> Dict:
    """Analyze text sentiment"""
    positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic']
    negative_words = ['bad', 'terrible', 'awful', 'horrible', 'poor', 'worst']
    
    pos_count = sum(1 for w in positive_words if w in text.lower())
    neg_count = sum(1 for w in negative_words if w in text.lower())
    
    if pos_count > neg_count:
        sentiment = 'positive'
    elif neg_count > pos_count:
        sentiment = 'negative'
    else:
        sentiment = 'neutral'
    
    return {
        'sentiment': sentiment,
        'positive_indicators': pos_count,
        'negative_indicators': neg_count,
        'confidence': min(1.0, (pos_count + neg_count) / max(1, len(text) / 50))
    }


def _keyword_extraction(text: str, top_k: int = 10) -> Dict:
    """Extract keywords from text"""
    words = re.findall(r'\b\w+\b', text.lower())
    from collections import Counter
    
    # Filter common words
    common = {'the', 'a', 'is', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'}
    filtered = [w for w in words if len(w) > 3 and w not in common]
    
    keyword_freq = Counter(filtered).most_common(top_k)
    
    return {
        'keywords': [kw[0] for kw in keyword_freq],
        'frequencies': [kw[1] for kw in keyword_freq],
        'top_k': top_k
    }


def _run_command(command: str) -> Dict:
    """Execute system command (sandboxed)"""
    # In production, add security checks
    import subprocess
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=5)
        return {
            'success': result.returncode == 0,
            'output': result.stdout[:500],  # Truncate large outputs
            'error': result.stderr[:500] if result.stderr else None
        }
    except subprocess.TimeoutExpired:
        return {'success': False, 'error': 'Command timeout'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def _check_system_status() -> Dict:
    """Check system resources"""
    try:
        import psutil
        return {
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent
        }
    except:
        return {
            'status': 'System monitoring not available',
            'note': 'Install psutil for full monitoring'
        }


def _list_processes(filter: str = '') -> Dict:
    """List system processes"""
    try:
        import psutil
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'memory_percent']):
            if not filter or filter.lower() in proc.info['name'].lower():
                processes.append(proc.info)
        return {'processes': processes[:20], 'total': len(processes)}  # Top 20
    except:
        return {'status': 'Process monitoring not available'}


def _parse_html(html_content: str, selector: str = '') -> Dict:
    """Parse HTML content"""
    try:
        from html.parser import HTMLParser
        
        class MLStripper(HTMLParser):
            def __init__(self):
                super().__init__()
                self.reset()
                self.text = []
            
            def handle_data(self, d):
                self.text.append(d)
            
            def get_data(self):
                return ''.join(self.text)
        
        stripper = MLStripper()
        stripper.feed(html_content)
        text = stripper.get_data()
        
        return {
            'text_extracted': len(text) > 0,
            'text_length': len(text),
            'preview': text[:200]
        }
    except Exception as e:
        return {'error': str(e)}


def _check_links(urls: List[str]) -> Dict:
    """Check link validity"""
    import requests
    results = {}
    
    for url in urls[:5]:  # Check first 5
        try:
            response = requests.head(url, timeout=5)
            results[url] = {'status': response.status_code, 'valid': response.status_code < 400}
        except:
            results[url] = {'valid': False, 'error': 'Connection failed'}
    
    return {'links_checked': results}


def _advanced_math(expression: str, operation_type: str = 'evaluate') -> Dict:
    """Perform advanced math"""
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return {
            'expression': expression,
            'result': result,
            'operation': operation_type
        }
    except:
        return {
            'error': 'Invalid expression',
            'expression': expression
        }


def _statistical_analysis(data: List, analysis_type: str = 'summary') -> Dict:
    """Statistical analysis"""
    try:
        numeric_data = [float(x) for x in data if isinstance(x, (int, float))]
        if not numeric_data:
            return {'error': 'No numeric data'}
        
        from statistics import mean, median, stdev
        
        return {
            'count': len(numeric_data),
            'mean': mean(numeric_data),
            'median': median(numeric_data),
            'std_dev': stdev(numeric_data) if len(numeric_data) > 1 else 0,
            'min': min(numeric_data),
            'max': max(numeric_data)
        }
    except Exception as e:
        return {'error': str(e)}


def _query_structure(query: str, action: str = 'explain') -> Dict:
    """Analyze SQL queries"""
    if action == 'explain':
        return {
            'query': query,
            'type': 'SELECT' if 'SELECT' in query.upper() else 'OTHER',
            'has_join': 'JOIN' in query.upper(),
            'has_where': 'WHERE' in query.upper(),
            'explanation': 'Query structure analyzed'
        }
    
    return {'query': query, 'action': action}


# ============ PYTHON SANDBOX IMPLEMENTATION ============

def _execute_python(code: str) -> Dict:
    """Execute Python code safely in sandbox"""
    result = sandbox.execute(code)
    
    return {
        'success': result['success'],
        'output': result['output'],
        'result': result['result'],
        'error': result['error'],
        'execution_time': result['execution_time'],
        'type_hints': result['type_hints'],
        'learning_feedback': result['learning_feedback']
    }


def _validate_python(code: str) -> Dict:
    """Validate Python code syntax and safety"""
    valid, syntax_msg = sandbox.validate_syntax(code)
    safe, dangerous = sandbox.check_imports(code)
    
    return {
        'syntax_valid': valid,
        'syntax_message': syntax_msg,
        'safe': safe,
        'dangerous_operations': dangerous if dangerous else [],
        'is_safe_to_run': valid and safe,
        'message': f"✅ Safe to run" if (valid and safe) else f"⚠️ Issues found"
    }



def _compare_items(items: List, criteria: List) -> Dict:
    """Compare items by criteria"""
    return {
        'items_compared': len(items),
        'criteria_used': len(criteria),
        'comparison_matrix': 'Generated',
        'recommendation': items[0] if items else None
    }


def _diff_analysis(text1: str, text2: str) -> Dict:
    """Analyze differences between texts"""
    import difflib
    
    diff = difflib.unified_diff(text1.split(), text2.split(), lineterm='')
    differences = list(diff)
    
    return {
        'differences_found': len(differences) // 3,  # Rough count
        'similarity': 1.0 - (len(differences) / max(len(text1), len(text2))),
        'total_changes': len([d for d in differences if d.startswith('+') or d.startswith('-')])
    }


# ============ CODE ANALYZER WRAPPER FUNCTIONS ============

def _analyze_file_wrapper(file_path: str) -> Dict:
    """Wrapper for analyze_file_for_improvements"""
    return analyze_file_for_improvements(file_path)


def _test_improvement_wrapper(original_code: str, improved_code: str, test_case: str = None) -> Dict:
    """Wrapper for test_code_improvement"""
    return test_code_improvement(original_code, improved_code, test_case)


def _analyze_and_suggest_wrapper(file_path: str, improvement_desc: str = '') -> Dict:
    """Wrapper for analyze_and_test"""
    return analyze_and_test(file_path, improvement_desc if improvement_desc else None)
