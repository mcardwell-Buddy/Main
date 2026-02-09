"""
Code Analyzer Tool: Analyzes code files and suggests improvements with sandbox testing

Allows the agent to:
1. Read and analyze code files
2. Generate improvement suggestions
3. Test improvements in the Python sandbox
4. Provide actionable feedback
"""

import os
import logging
from pathlib import Path
from backend.python_sandbox import sandbox
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


def analyze_file_for_improvements(file_path: str) -> Dict[str, Any]:
    """
    Analyze a file and suggest improvements with sandbox testing.
    
    Args:
        file_path: Path to the Python file to analyze (relative to project root)
    
    Returns:
        Dictionary with analysis results, suggestions, and test outcomes
    """
    try:
        # Construct full path
        project_root = Path(__file__).parent.parent
        full_path = project_root / file_path
        
        if not full_path.exists():
            return {'error': f'File not found: {full_path}'}
        
        if not str(full_path).endswith('.py'):
            return {'error': 'Only Python files are supported'}
        
        # Read the file
        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()
        
        # Validate syntax
        is_valid, syntax_msg = sandbox.validate_syntax(code)
        if not is_valid:
            return {
                'error': 'File has syntax errors',
                'syntax_error': syntax_msg,
                'file': file_path
            }
        
        # Check for dangerous imports (warn only for analysis)
        is_safe, dangerous_ops = sandbox.check_imports(code)
        restricted_warning = dangerous_ops if not is_safe else []
        
        # Generate analysis
        analysis = _perform_code_analysis(code, file_path)
        
        rationale = build_improvement_rationale(analysis)
        return {
            'success': True,
            'file': file_path,
            'lines_of_code': len(code.split('\n')),
            'analysis': analysis,
            'rationale': rationale,
            'restricted_warning': restricted_warning,
            'file_content_summary': f"{len(code)} characters, {len(code.split(chr(10)))} lines"
        }
    
    except Exception as e:
        logger.error(f"Error analyzing file: {e}")
        return {'error': str(e)}


def test_code_improvement(original_code: str, improved_code: str, test_case: str = None) -> Dict[str, Any]:
    """
    Test an improvement by running both versions in the sandbox and comparing.
    
    Args:
        original_code: The original Python code
        improved_code: The improved Python code
        test_case: Optional test code to run on both versions
    
    Returns:
        Dictionary with test results comparing original vs improved
    """
    try:
        results = {
            'original': None,
            'improved': None,
            'comparison': None,
            'recommendation': None
        }
        
        # Test original code
        original_result = sandbox.execute(original_code)
        results['original'] = {
            'success': original_result.get('success', False),
            'output': original_result.get('output', ''),
            'error': original_result.get('error'),
            'execution_time': original_result.get('execution_time', 0),
            'feedback': original_result.get('learning_feedback', '')
        }
        
        # Test improved code
        improved_result = sandbox.execute(improved_code)
        results['improved'] = {
            'success': improved_result.get('success', False),
            'output': improved_result.get('output', ''),
            'error': improved_result.get('error'),
            'execution_time': improved_result.get('execution_time', 0),
            'feedback': improved_result.get('learning_feedback', '')
        }
        
        # Compare results
        if results['original']['success'] and results['improved']['success']:
            time_improvement = (
                results['original']['execution_time'] - 
                results['improved']['execution_time']
            )
            results['comparison'] = {
                'both_successful': True,
                'time_improvement_ms': time_improvement,
                'time_improvement_percent': (
                    (time_improvement / results['original']['execution_time'] * 100)
                    if results['original']['execution_time'] > 0 else 0
                ),
                'output_matches': results['original']['output'] == results['improved']['output']
            }
            
            if time_improvement > 0:
                results['recommendation'] = f"Improvement shows {abs(time_improvement):.4f}ms faster execution"
            elif time_improvement < 0:
                results['recommendation'] = f"Original is {abs(time_improvement):.4f}ms faster"
            else:
                results['recommendation'] = "Performance is similar"
        else:
            results['comparison'] = {
                'both_successful': False,
                'original_success': results['original']['success'],
                'improved_success': results['improved']['success']
            }
            results['recommendation'] = "Version with errors needs fixing"
        
        results['success'] = True
        return results
    
    except Exception as e:
        logger.error(f"Error testing code improvement: {e}")
        return {'error': str(e)}


def _perform_code_analysis(code: str, file_path: str) -> Dict[str, Any]:
    """
    Analyze code structure and patterns.
    
    Returns suggestions based on:
    - Code length
    - Function definitions
    - Error handling
    - Documentation
    - Import patterns
    """
    lines = code.split('\n')
    analysis = {
        'patterns_detected': [],
        'suggestions': [],
        'metrics': {
            'total_lines': len(lines),
            'blank_lines': len([l for l in lines if not l.strip()]),
            'comment_lines': len([l for l in lines if l.strip().startswith('#')]),
            'function_definitions': len([l for l in lines if l.strip().startswith('def ')]),
            'class_definitions': len([l for l in lines if l.strip().startswith('class ')]),
        }
    }
    
    # Detect patterns
    if 'def ' in code:
        analysis['patterns_detected'].append('Function definitions found')
    if 'class ' in code:
        analysis['patterns_detected'].append('Class definitions found')
    if 'try:' in code:
        analysis['patterns_detected'].append('Error handling (try/except) found')
    if '"""' in code or "'''" in code:
        analysis['patterns_detected'].append('Docstrings found')
    
    # Generate suggestions based on metrics
    if analysis['metrics']['comment_lines'] == 0:
        analysis['suggestions'].append('Consider adding comments for clarity')
    if analysis['metrics']['total_lines'] > 100 and analysis['metrics']['function_definitions'] < 3:
        analysis['suggestions'].append('Large file with few functions - consider breaking into modules')
    if 'try:' not in code and analysis['metrics']['function_definitions'] > 0:
        analysis['suggestions'].append('Consider adding error handling to functions')
    
    return analysis


def build_improvement_rationale(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build a rationale score explaining whether improvements are warranted.
    Returns a score (0.0-1.0) and a list of reasons.
    """
    reasons = []
    score = 0.1

    metrics = analysis.get('metrics', {})
    suggestions = analysis.get('suggestions', [])

    if suggestions:
        score += min(0.6, 0.15 * len(suggestions))
        reasons.extend([f"Suggestion: {s}" for s in suggestions])

    if metrics.get('total_lines', 0) > 300:
        score += 0.15
        reasons.append("Large file size indicates refactor potential")
    elif metrics.get('total_lines', 0) > 150:
        score += 0.08
        reasons.append("Moderate file size suggests review")

    if metrics.get('comment_lines', 0) == 0:
        score += 0.1
        reasons.append("No comments present; documentation may improve clarity")

    if metrics.get('function_definitions', 0) == 0 and metrics.get('class_definitions', 0) == 0:
        score -= 0.05
        reasons.append("No functions or classes detected; improvements may be limited")

    score = max(0.0, min(1.0, score))
    return {
        'score': round(score, 3),
        'reasons': reasons
    }


def suggest_and_build_improvement(file_path: str, improvement_description: str) -> Dict[str, Any]:
    """
    High-level tool: Analyze file, generate specific improvement, test it.
    
    Args:
        file_path: Path to the Python file
        improvement_description: Description of improvement to make (e.g., "add error handling", "optimize loop")
    
    Returns:
        Results including before/after comparison
    """
    try:
        # First, analyze the file
        analysis = analyze_file_for_improvements(file_path)
        if 'error' in analysis:
            return analysis
        
        # Read the original file
        project_root = Path(__file__).parent.parent
        full_path = project_root / file_path
        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
            original_code = f.read()
        
        # Generate improvement suggestion (would be done by LLM in real scenario)
        improvement_result = {
            'original_file': file_path,
            'improvement_requested': improvement_description,
            'analysis': analysis['analysis'],
            'original_code': original_code[:500] + '...' if len(original_code) > 500 else original_code,
            'next_steps': [
                'Use generate_code tool with the file content and improvement description',
                'The generated improved code should then be tested in sandbox',
                f'Compare results using test_code_improvement tool'
            ],
            'note': 'This is a foundation - the LLM agent should generate the specific improved code based on analysis'
        }
        
        return improvement_result
    
    except Exception as e:
        logger.error(f"Error in suggest_and_build_improvement: {e}")
        return {'error': str(e)}


# Convenience function for the tool registry
def analyze_and_test(file_path: str, improvement_description: str = None) -> Dict[str, Any]:
    """
    Main entry point for the agent to analyze code and suggest improvements.
    
    Args:
        file_path: Path to analyze
        improvement_description: Optional specific improvement to focus on
    
    Returns:
        Comprehensive analysis with actionable suggestions
    """
    if improvement_description:
        return suggest_and_build_improvement(file_path, improvement_description)
    else:
        return analyze_file_for_improvements(file_path)


def build_suggestion(file_path: str, improvement_description: str = "add error handling") -> Dict[str, Any]:
    """
    Build a simple improvement suggestion, test it in the sandbox, and return results.
    """
    try:
        analysis = analyze_file_for_improvements(file_path)
        if 'error' in analysis:
            return analysis

        project_root = Path(__file__).parent.parent
        full_path = project_root / file_path
        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
            original_code = f.read()

        improved_code = generate_improvement_code(original_code, improvement_description)
        test_results = test_code_improvement(original_code, improved_code)

        return {
            'success': True,
            'suggestion_id': _generate_suggestion_id(file_path),
            'file': file_path,
            'improvement_description': improvement_description,
            'analysis': analysis.get('analysis', {}),
            'original_code': original_code,
            'improved_code': improved_code,
            'test_results': test_results
        }
    except Exception as e:
        logger.error(f"Error in build_suggestion: {e}")
        return {'error': str(e)}


def _generate_suggestion_id(file_path: str) -> str:
    import uuid
    return f"suggestion-{uuid.uuid4()}"


def generate_improvement_code(code: str, improvement_description: str) -> str:
    description = (improvement_description or "").lower()
    if "error" in description or "try" in description or "exception" in description:
        return _add_basic_error_handling(code)
    return _add_basic_error_handling(code)


def _add_basic_error_handling(code: str) -> str:
    lines = code.split('\n')
    
    # Look for if __name__ == "__main__":
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped in ('if __name__ == "__main__":', "if __name__ == '__main__':"):
            body_index = i + 1
            if body_index < len(lines) and lines[body_index].strip():
                body_line = lines[body_index]
                body_indent = body_line[:len(body_line) - len(body_line.lstrip())]
                # Replace the body line with try/except wrapper
                lines[body_index] = f"{body_indent}try:"
                lines.insert(body_index + 1, f"{body_indent}    {body_line.strip()}")
                lines.insert(body_index + 2, f"{body_indent}except Exception as err:")
                lines.insert(body_index + 3, f"{body_indent}    print(f'Error: {{err}}')")
                return '\n'.join(lines)

    # If no main block, add one
    if "def main(" in code:
        return code + "\n\nif __name__ == '__main__':\n    try:\n        main()\n    except Exception as err:\n        print(f'Error: {err}')\n"

    # Fallback: just add a comment
    return code + "\n\n# Suggested: add try/except around main entry point\n"
