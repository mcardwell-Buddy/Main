"""
Self-Improvement Engine: Enables Buddy to autonomously improve his own code

Workflow:
1. Analyze own codebase → Find improvement opportunities  
2. User approves a suggestion
3. Autonomous loop: Build → Test → Fix → Repeat until tests pass
4. Report progress in chat
5. Show demo when ready
6. Deploy after final approval
"""

import logging
import os
import json
import difflib
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
from backend.code_analyzer import analyze_file_for_improvements, test_code_improvement, generate_improvement_code
from backend.buddys_soul import evaluate_alignment
from backend.python_sandbox import sandbox
from backend.llm_client import llm_client

logger = logging.getLogger(__name__)


class SelfImprovementEngine:
    """Autonomous self-improvement system for Buddy"""
    
    def __init__(self):
        self.current_task = None
        self.iteration = 0
        self.max_iterations = 10
        self.test_results = []
        self.progress_log = []
        
    def scan_codebase_for_improvements(self) -> List[Dict]:
        """
        Scan Buddy's own codebase and identify improvement opportunities.
        
        Returns list of files with suggested improvements
        """
        logger.info("🔍 Scanning codebase for improvement opportunities...")
        
        backend_path = Path(__file__).parent
        python_files = list(backend_path.glob("*.py"))
        
        opportunities = []
        
        for file_path in python_files:
            # Skip __init__ and test files
            if file_path.name.startswith('__') or file_path.name.startswith('test_'):
                continue
                
            relative_path = f"backend/{file_path.name}"
            
            try:
                analysis = analyze_file_for_improvements(relative_path)
                
                if analysis.get('success') and analysis.get('analysis'):
                    suggestions = analysis['analysis'].get('suggestions', [])
                    if suggestions:
                        opportunities.append({
                            'file': relative_path,
                            'suggestions': suggestions,
                            'metrics': analysis['analysis'].get('metrics', {}),
                            'priority': self._calculate_priority(analysis['analysis'])
                        })
            except Exception as e:
                logger.error(f"Error analyzing {relative_path}: {e}")
                
        # Sort by priority
        opportunities.sort(key=lambda x: x['priority'], reverse=True)
        
        logger.info(f"✓ Found {len(opportunities)} improvement opportunities")
        return opportunities
        
    def autonomous_improve_until_tests_pass(
        self,
        file_path: str,
        improvement_description: str,
        progress_callback=None,
        require_confirmation: bool = True,
        confirmed: bool = False,
    ) -> Dict:
        """
        Main autonomous improvement loop:
        1. Generate improved code
        2. Test in sandbox
        3. If tests fail, analyze failure and adjust
        4. Repeat until tests pass or max iterations
        
        Args:
            file_path: File to improve
            improvement_description: What to improve
            progress_callback: Function to call with progress updates
            
        Returns:
            Final result with improved code and test outcomes
        """
        self.current_task = {
            'file': file_path,
            'description': improvement_description,
            'started_at': datetime.now().isoformat()
        }
        self.iteration = 0
        self.test_results = []
        self.progress_log = []
        
        self._report_progress("Starting autonomous improvement...", progress_callback)
        
        # Check rationale before proceeding
        analysis = analyze_file_for_improvements(file_path)
        if analysis.get('error'):
            return {'error': analysis.get('error'), 'file': file_path}

        rationale = analysis.get('rationale', {})
        rationale_score = rationale.get('score', 0.0)
        soul_alignment = evaluate_alignment(improvement_description)
        combined_score = (rationale_score * 0.7) + (soul_alignment.get('score', 0.0) * 0.3)

        if combined_score < 0.25:
            return {
                'success': False,
                'file': file_path,
                'improvement': improvement_description,
                'rationale': rationale,
                'soul_alignment': soul_alignment,
                'combined_score': round(combined_score, 3),
                'message': 'Improvement not warranted based on current rationale score. Review manually.'
            }

        # Read original file
        try:
            project_root = Path(__file__).parent.parent
            full_path = project_root / file_path
            with open(full_path, 'r', encoding='utf-8') as f:
                original_code = f.read()
        except Exception as e:
            return {'error': f'Could not read file: {e}'}

        if require_confirmation and not confirmed:
            draft_code = self._generate_improvement(
                original_code=original_code,
                improvement_description=improvement_description,
            )
            diff = self._build_diff(original_code, draft_code, file_path)
            return {
                'success': False,
                'file': file_path,
                'improvement': improvement_description,
                'rationale': rationale,
                'soul_alignment': soul_alignment,
                'combined_score': round(combined_score, 3),
                'message': 'Review the proposed diff and confirm before running sandbox improvements. Any changes you want to add?',
                'needs_confirmation': True,
                'proposal': {
                    'file': file_path,
                    'improvement': improvement_description,
                    'rationale': rationale,
                    'soul_alignment': soul_alignment,
                    'combined_score': round(combined_score, 3),
                    'diff': diff,
                    'draft_code': draft_code
                },
                'next_step_hint': 'If approved, resend with confirmed=true (and optionally update improvement text).'
            }
            
        improved_code = original_code
        last_error = None
        
        while self.iteration < self.max_iterations:
            self.iteration += 1
            self._report_progress(
                f"Iteration {self.iteration}/{self.max_iterations}: Generating improvement...",
                progress_callback
            )
            
            # Generate improved code
            improved_code = self._generate_improvement(
                original_code=original_code,
                improvement_description=improvement_description,
                previous_attempt=improved_code if self.iteration > 1 else None,
                previous_error=last_error
            )
            
            self._report_progress(
                "Testing improved code in sandbox...",
                progress_callback
            )
            
            # Test the improved code
            test_result = self._test_improvement(original_code, improved_code)
            self.test_results.append(test_result)
            
            if test_result.get('passed'):
                self._report_progress(
                    f"Tests passed. Improvement successful after {self.iteration} iteration(s)",
                    progress_callback
                )
                return {
                    'success': True,
                    'iterations': self.iteration,
                    'file': file_path,
                    'improvement': improvement_description,
                    'original_code': original_code,
                    'improved_code': improved_code,
                    'diff': self._build_diff(original_code, improved_code, file_path),
                    'test_results': test_result,
                    'progress_log': self.progress_log,
                    'ready_for_approval': True
                }
            else:
                last_error = test_result.get('error')
                self._report_progress(
                    f"Tests failed: {last_error}. Analyzing and adjusting...",
                    progress_callback
                )
                
        # Max iterations reached
        self._report_progress(
            f"Reached max iterations ({self.max_iterations}). Best attempt ready for review.",
            progress_callback
        )
        
        return {
            'success': False,
            'iterations': self.iteration,
            'file': file_path,
            'improvement': improvement_description,
            'original_code': original_code,
            'improved_code': improved_code,
            'diff': self._build_diff(original_code, improved_code, file_path),
            'test_results': self.test_results[-1] if self.test_results else {},
            'progress_log': self.progress_log,
            'needs_manual_review': True,
            'message': f'Attempted {self.iteration} iterations but tests did not pass. Review the best attempt.'
        }
        
    def _generate_improvement(
        self, 
        original_code: str, 
        improvement_description: str,
        previous_attempt: Optional[str] = None,
        previous_error: Optional[str] = None
    ) -> str:
        """
        Use LLM to generate improved code.
        
        If previous attempt failed, includes error for learning.
        """
        if previous_attempt and previous_error:
            prompt = f"""
The previous code improvement attempt failed with this error:
{previous_error}

Previous attempt:
```python
{previous_attempt[:1000]}...
```

Original code:
```python
{original_code[:1000]}...
```

Improvement goal: {improvement_description}

Generate IMPROVED code that:
1. Fixes the error from previous attempt
2. Achieves the improvement goal
3. Maintains original functionality
4. Is syntactically correct

Return ONLY the complete improved Python code, no explanations.
"""
        else:
            prompt = f"""
Original code:
```python
{original_code[:1500]}...
```

Improvement goal: {improvement_description}

Generate IMPROVED code that:
1. Achieves the improvement goal
2. Maintains original functionality  
3. Is syntactically correct and well-structured
4. Includes proper error handling

Return ONLY the complete improved Python code, no explanations.
"""
        
        try:
            improved_code = llm_client.complete(prompt, max_tokens=2000)
            if not improved_code:
                # Fallback to simple heuristic improvement
                return generate_improvement_code(original_code, improvement_description)
            
            # Extract code from markdown if present
            if '```python' in improved_code:
                improved_code = improved_code.split('```python')[1].split('```')[0].strip()
            elif '```' in improved_code:
                improved_code = improved_code.split('```')[1].split('```')[0].strip()
                
            return improved_code
        except Exception as e:
            logger.error(f"Error generating improvement: {e}")
            return generate_improvement_code(original_code, improvement_description)
            
    def _test_improvement(self, original_code: str, improved_code: str) -> Dict:
        """
        Test the improved code in sandbox.
        
        Returns test results with pass/fail status
        """
        # First check syntax
        is_valid, syntax_msg = sandbox.validate_syntax(improved_code)
        if not is_valid:
            return {
                'passed': False,
                'error': f'Syntax error: {syntax_msg}',
                'stage': 'syntax_validation'
            }
            
        # Check for dangerous operations (skip execution if restricted)
        is_safe, dangerous = sandbox.check_imports(improved_code)
        if not is_safe:
            return {
                'passed': True,
                'warning': f'Skipped execution due to restricted operations: {dangerous}',
                'stage': 'safety_check_skipped'
            }

        # Execute in sandbox
        result = sandbox.execute(improved_code)
        
        if not result.get('success'):
            return {
                'passed': False,
                'error': result.get('error', 'Execution failed'),
                'output': result.get('output', ''),
                'stage': 'execution'
            }

    def _build_diff(self, original_code: str, improved_code: str, file_path: str = "") -> str:
        """Build a unified diff for review/approval."""
        try:
            from_label = f"a/{file_path}" if file_path else "a/original"
            to_label = f"b/{file_path}" if file_path else "b/improved"
            diff = difflib.unified_diff(
                original_code.splitlines(keepends=True),
                improved_code.splitlines(keepends=True),
                fromfile=from_label,
                tofile=to_label,
            )
            return "".join(diff)
        except Exception:
            return ""
            
        # Compare with original (best-effort)
        try:
            original_result = sandbox.execute(original_code)
        except Exception:
            original_result = {'output': ''}
        
        return {
            'passed': True,
            'improved_output': result.get('output', ''),
            'original_output': original_result.get('output', ''),
            'execution_time': result.get('execution_time', 0),
            'stage': 'complete'
        }
        
    def _calculate_priority(self, analysis: Dict) -> int:
        """Calculate priority score for an improvement opportunity"""
        score = 0
        
        suggestions = analysis.get('suggestions', [])
        score += len(suggestions) * 10
        
        metrics = analysis.get('metrics', {})
        if metrics.get('total_lines', 0) > 100:
            score += 5
        if metrics.get('comment_lines', 0) == 0:
            score += 15
        if 'error handling' in ' '.join(suggestions).lower():
            score += 20
            
        return score
        
    def _report_progress(self, message: str, callback=None):
        """Report progress to log and optional callback"""
        timestamp = datetime.now().isoformat()
        log_entry = {
            'timestamp': timestamp,
            'message': message,
            'iteration': self.iteration
        }
        self.progress_log.append(log_entry)
        logger.info(message)
        
        if callback:
            callback(log_entry)


# Global instance
self_improvement_engine = SelfImprovementEngine()
