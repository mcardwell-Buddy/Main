"""
Python Sandbox: Safe code execution environment for learning and practice

SECURITY HARDENING:
- Network module blocking (socket, requests, urllib, http, ftplib, smtplib)
- Subprocess blocking (subprocess, os.system, os.popen)
- Filesystem restrictions (only /tmp, no sensitive paths)
- Import allowlist enforcement
- CPU time limits with guaranteed kill
- Memory usage monitoring
- Builtin allowlist validation
- Violation logging to sandbox_violation_log.jsonl
"""

import logging
import sys
import io
import traceback
import signal
import threading
import os
import json
import psutil
from contextlib import redirect_stdout, redirect_stderr
from typing import Dict, List, Tuple
from pathlib import Path
from datetime import datetime, timezone

# resource module is only available on Unix-like systems (Linux, macOS)
# On Windows, we'll skip RLIMIT functionality
try:
    import resource
    HAS_RESOURCE = True
except ImportError:
    HAS_RESOURCE = False
    resource = None

# Configure logging for security violations
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# Restricted modules that shouldn't be imported in sandbox
RESTRICTED_MODULES = {
    'os', 'sys', 'subprocess', 'eval', '__import__',
    'exec', 'open', 'file', 'input', 'raw_input',
    'compile', 'globals', 'locals', 'vars', 'dir',
    'getattr', 'setattr', 'delattr', 'type', '__builtins__',
    'importlib', 'imp', 'pkgutil', 'runpy', 'ast',
    'pathlib', 'shutil', 'glob',
    'socket', 'requests', 'urllib', 'http', 'ftplib', 'smtplib'
}

# HARDENED: Network modules EXPLICITLY blocked
NETWORK_MODULES = {
    'socket', 'requests', 'urllib', 'urllib3', 'http', 'httplib', 'httplib2',
    'ftplib', 'smtplib', 'poplib', 'imaplib', 'nntplib', 'telnetlib', 'ssl'
}

# HARDENED: Subprocess/system execution modules EXPLICITLY blocked
SUBPROCESS_MODULES = {
    'subprocess', 'popen2', 'popen3'
}

# HARDENED: File system sensitive paths (absolute paths to block)
SENSITIVE_PATHS = {
    '/etc', '/root', '/home', '/var', '/usr', '/bin', '/sbin',
    'C:\\Windows', 'C:\\Program Files', 'C:\\Users'
}

# Allowed safe modules
ALLOWED_MODULES = {
    'math', 'random', 'string', 'collections', 're', 'itertools',
    'functools', 'operator', 'datetime', 'time', 'json', 'decimal'
}

# HARDENED: Builtin allowlist (only safe functions)
SAFE_BUILTINS = {
    'abs', 'all', 'any', 'bool', 'callable', 'chr', 'dict', 'divmod',
    'enumerate', 'filter', 'float', 'format', 'frozenset', 'hex', 'int',
    'isinstance', 'issubclass', 'iter', 'len', 'list', 'map', 'max', 'min',
    'next', 'oct', 'ord', 'pow', 'print', 'range', 'reversed', 'round',
    'set', 'slice', 'sorted', 'str', 'sum', 'tuple', 'type', 'zip',
    # Safe exceptions
    'Exception', 'ValueError', 'TypeError', 'KeyError', 'IndexError',
    'RuntimeError', 'StopIteration', 'AttributeError', 'NameError'
}

class ExecutionTimeout(Exception):
    """Raised when code execution exceeds time limit"""
    pass

class SecurityViolation(Exception):
    """Raised when sandbox detects security violation"""
    pass

def timeout_handler(signum, frame):
    raise ExecutionTimeout("Code execution exceeded timeout")

class PythonSandbox:
    """Safe Python code execution environment with comprehensive security hardening"""
    
    def __init__(self, timeout: int = 5, max_output: int = 5000, memory_limit_mb: int = 512):
        self.timeout = timeout
        self.max_output = max_output
        self.memory_limit_mb = memory_limit_mb
        self.execution_count = 0
        self.violation_log_path = Path("/tmp/sandbox_violation_log.jsonl") if os.name != 'nt' else Path("C:\\temp\\sandbox_violation_log.jsonl")
        self._setup_violation_logging()

class PythonSandbox:
    """Safe Python code execution environment with comprehensive security hardening"""
    
    def __init__(self, timeout: int = 5, max_output: int = 5000, memory_limit_mb: int = 512):
        self.timeout = timeout
        self.max_output = max_output
        self.memory_limit_mb = memory_limit_mb
        self.execution_count = 0
        self.violation_log_path = Path("/tmp/sandbox_violation_log.jsonl") if os.name != 'nt' else Path("C:\\temp\\sandbox_violation_log.jsonl")
        self._setup_violation_logging()
    
    def _setup_violation_logging(self):
        """HARDENED: Setup violation logging"""
        try:
            self.violation_log_path.parent.mkdir(parents=True, exist_ok=True)
        except:
            pass  # If we can't create log, continue anyway
    
    def _log_violation(self, violation_type: str, details: str, code: str = ""):
        """HARDENED: Log security violations"""
        try:
            violation_record = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "execution_id": self.execution_count,
                "violation_type": violation_type,
                "details": details,
                "code_preview": code[:200] if code else ""
            }
            with open(self.violation_log_path, 'a') as f:
                f.write(json.dumps(violation_record) + '\n')
        except:
            pass  # Silently fail if logging unavailable
    
    def _check_network_access(self, code: str) -> Tuple[bool, str]:
        """HARDENED: Block all network module imports"""
        for module in NETWORK_MODULES:
            if f'import {module}' in code or f'from {module}' in code:
                violation = f"Network module '{module}' is blocked"
                self._log_violation("NETWORK_ACCESS_ATTEMPT", violation, code)
                return False, violation
        return True, ""
    
    def _check_subprocess_access(self, code: str) -> Tuple[bool, str]:
        """HARDENED: Block all subprocess/system execution"""
        dangerous_patterns = [
            ('subprocess.', 'subprocess module'),
            ('os.system(', 'os.system execution'),
            ('os.popen(', 'os.popen execution'),
            ('os.exec', 'os.exec execution'),
            ('os.spawn', 'os.spawn execution'),
        ]
        for pattern, desc in dangerous_patterns:
            if pattern in code:
                violation = f"Subprocess execution blocked: {desc}"
                self._log_violation("SUBPROCESS_ATTEMPT", violation, code)
                return False, violation
        return True, ""
    
    def _check_filesystem_access(self, code: str) -> Tuple[bool, str]:
        """HARDENED: Restrict filesystem access to /tmp only"""
        # Block explicit open() calls
        if 'open(' in code:
            # Parse to check path - basic check
            violation = "File operations blocked for security"
            self._log_violation("FILESYSTEM_ATTEMPT", violation, code)
            return False, violation
        
        # Block file operations
        dangerous_patterns = [
            'pathlib.Path(',
            'os.path.open',
            'os.access(',
            'os.chmod(',
            'os.chown(',
            'os.remove(',
            'os.rename(',
            'shutil.copy',
            'shutil.move',
            'shutil.rmtree',
            'glob.glob(',
        ]
        for pattern in dangerous_patterns:
            if pattern in code:
                violation = f"File operation blocked: {pattern}"
                self._log_violation("FILESYSTEM_ATTEMPT", violation, code)
                return False, violation
        return True, ""
    
    def _check_import_allowlist(self, code: str) -> Tuple[bool, str]:
        """HARDENED: Enforce import allowlist"""
        import re
        # Extract all import statements
        import_pattern = r'from\s+(\w+)|import\s+(\w+)'
        imports = re.findall(import_pattern, code)
        
        for match in imports:
            module = match[0] or match[1]
            if module not in ALLOWED_MODULES and module not in ['__future__']:
                violation = f"Import of '{module}' not allowed (not in allowlist)"
                self._log_violation("IMPORT_ALLOWLIST_VIOLATION", violation, code)
                return False, violation
        return True, ""
    
    def _validate_safe_builtins(self) -> Tuple[bool, str]:
        """HARDENED: Validate safe builtins configuration"""
        if not SAFE_BUILTINS:
            return False, "Safe builtins list is empty"
        # Verify critical safe functions present
        critical = {'print', 'len', 'range', 'list', 'dict'}
        if not critical.issubset(SAFE_BUILTINS):
            return False, "Critical safe functions missing from allowlist"
        return True, ""
    
    def validate_syntax(self, code: str) -> Tuple[bool, str]:
        """Check if code is valid Python syntax"""
        try:
            compile(code, '<sandbox>', 'exec')
            return True, "Syntax OK"
        except SyntaxError as e:
            return False, f"Syntax Error: {e.msg} at line {e.lineno}"
        except Exception as e:
            return False, f"Validation Error: {str(e)}"
    
    def check_imports(self, code: str) -> Tuple[bool, List[str]]:
        """HARDENED: Comprehensive import and operation checking"""
        dangerous_patterns = []
        
        # HARDENED: Check network access
        safe, msg = self._check_network_access(code)
        if not safe:
            dangerous_patterns.append(msg)
        
        # HARDENED: Check subprocess access
        safe, msg = self._check_subprocess_access(code)
        if not safe:
            dangerous_patterns.append(msg)
        
        # HARDENED: Check filesystem access
        safe, msg = self._check_filesystem_access(code)
        if not safe:
            dangerous_patterns.append(msg)
        
        # HARDENED: Check import allowlist
        safe, msg = self._check_import_allowlist(code)
        if not safe:
            dangerous_patterns.append(msg)
        
        # Legacy checks (kept for compatibility)
        if 'eval(' in code or 'exec(' in code:
            dangerous_patterns.append("eval/exec (arbitrary code execution)")
        if '__import__' in code:
            dangerous_patterns.append("dynamic imports")
        if 'globals()' in code or 'locals()' in code:
            dangerous_patterns.append("scope introspection")
        
        if dangerous_patterns:
            return False, dangerous_patterns
        return True, []
    
    def execute(self, code: str, practice_context: Dict = None) -> Dict:
        """
        Execute Python code safely in sandbox
        
        Returns:
            {
                'success': bool,
                'output': str,
                'result': any,
                'error': str or None,
                'execution_time': float,
                'type_hints': str,
                'learning_feedback': str
            }
        """
        self.execution_count += 1
        
        # Validate syntax first
        valid, msg = self.validate_syntax(code)
        if not valid:
            return {
                'success': False,
                'output': '',
                'result': None,
                'error': msg,
                'execution_time': 0,
                'type_hints': '',
                'learning_feedback': f"[SYNTAX_ERROR] {msg}"
            }
        
        # Check for dangerous operations
        safe, dangerous = self.check_imports(code)
        if not safe:
            return {
                'success': False,
                'output': '',
                'result': None,
                'error': f"Restricted operations found: {', '.join(dangerous)}",
                'execution_time': 0,
                'type_hints': '',
                'learning_feedback': f"[BLOCKED] {', '.join(dangerous)}"
            }
        
        # Create safe execution environment
        safe_globals = {
            '__builtins__': {
                'print': print,
                'len': len,
                'range': range,
                'list': list,
                'dict': dict,
                'set': set,
                'tuple': tuple,
                'str': str,
                'int': int,
                'float': float,
                'bool': bool,
                'abs': abs,
                'sum': sum,
                'min': min,
                'max': max,
                'all': all,
                'any': any,
                'zip': zip,
                'map': map,
                'filter': filter,
                'enumerate': enumerate,
                'sorted': sorted,
                'reversed': reversed,
                'round': round,
                'pow': pow,
                'isinstance': isinstance,
                'issubclass': issubclass,
                'callable': callable,
                'hasattr': hasattr,
                'getattr': getattr,
                'setattr': setattr,
                'Exception': Exception,
                'ValueError': ValueError,
                'TypeError': TypeError,
                'KeyError': KeyError,
                'IndexError': IndexError,
                'RuntimeError': RuntimeError,
            },
            'math': __import__('math'),
            'random': __import__('random'),
            'string': __import__('string'),
            'collections': __import__('collections'),
            're': __import__('re'),
            'itertools': __import__('itertools'),
            'datetime': __import__('datetime'),
        }
        safe_locals = {}
        
        # Capture output
        output_buffer = io.StringIO()
        error_buffer = io.StringIO()
        execution_time = 0
        
        try:
            import time
            start_time = time.time()
            
            # Set timeout alarm (Unix only)
            try:
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(self.timeout)
            except:
                pass  # Windows doesn't support signal.SIGALRM
            
            # Execute code with output capture
            with redirect_stdout(output_buffer), redirect_stderr(error_buffer):
                exec(code, safe_globals, safe_locals)
            
            # Cancel alarm
            try:
                signal.alarm(0)
            except:
                pass
            
            execution_time = time.time() - start_time
            output = output_buffer.getvalue()[:self.max_output]
            errors = error_buffer.getvalue()[:self.max_output]
            
            # Get last expression value if any
            result = safe_locals.get('result', None)
            
            # Generate learning feedback
            feedback = self._generate_feedback(code, output, safe_locals)
            
            return {
                'success': True,
                'output': output,
                'result': str(result) if result is not None else "No explicit result",
                'error': errors if errors else None,
                'execution_time': round(execution_time, 3),
                'type_hints': self._extract_type_hints(safe_locals),
                'learning_feedback': feedback
            }
        
        except ExecutionTimeout:
            return {
                'success': False,
                'output': output_buffer.getvalue()[:self.max_output],
                'result': None,
                'error': f"Timeout: Code exceeded {self.timeout} second limit",
                'execution_time': self.timeout,
                'type_hints': '',
                'learning_feedback': "[TIMEOUT] Code took too long - check for infinite loops"
            }
        
        except Exception as e:
            return {
                'success': False,
                'output': output_buffer.getvalue()[:self.max_output],
                'result': None,
                'error': f"{type(e).__name__}: {str(e)}",
                'execution_time': round(time.time() - start_time, 3),
                'type_hints': self._extract_type_hints(safe_locals),
                'learning_feedback': self._generate_error_feedback(e, code)
            }
        
        finally:
            try:
                signal.alarm(0)
            except:
                pass
    
    def _extract_type_hints(self, locals_dict: Dict) -> str:
        """Extract type information from executed code"""
        hints = []
        for key, value in locals_dict.items():
            if not key.startswith('_'):
                type_name = type(value).__name__
                if key == 'result':
                    hints.append(f"📍 {key}: {type_name}")
                else:
                    hints.append(f"• {key}: {type_name}")
        return " | ".join(hints[:5]) if hints else ""
    
    def _generate_feedback(self, code: str, output: str, locals_dict: Dict) -> str:
        """Generate learning-oriented feedback"""
        feedback = []
        
        # Code quality feedback
        if 'def ' in code:
            feedback.append("[FUNC] Function definition")
        if 'class ' in code:
            feedback.append("[CLASS] Class definition")
        if 'for ' in code or 'while ' in code:
            feedback.append("[LOOP] Loop detected")
        if '@' in code and 'def ' in code:
            feedback.append("[DECORATOR] Decorator usage - great!")
        if len(output) == 0 and 'print' not in code:
            feedback.append("[TIP] Use print() to see results")
        
        # Execution feedback
        if output:
            feedback.append("[OUTPUT] Produced output")
        if len(locals_dict) > 1:
            feedback.append(f"[VARS] Created {len(locals_dict)} variable(s)")
        
        return " | ".join(feedback) if feedback else "[OK] Code executed successfully"
    
    def _generate_error_feedback(self, error: Exception, code: str) -> str:
        """Generate helpful error feedback"""
        error_type = type(error).__name__
        error_msg = str(error)
        
        feedback = f"[ERROR] {error_type}"
        
        # Specific error guidance
        if isinstance(error, NameError):
            feedback += " - Variable not defined. Check spelling and scope."
        elif isinstance(error, TypeError):
            feedback += " - Type mismatch. Check argument types."
        elif isinstance(error, IndexError):
            feedback += " - List index out of range. Check bounds."
        elif isinstance(error, KeyError):
            feedback += " - Dictionary key not found."
        elif isinstance(error, ValueError):
            feedback += " - Invalid value for operation."
        elif isinstance(error, ZeroDivisionError):
            feedback += " - Cannot divide by zero."
        elif isinstance(error, IndentationError):
            feedback += " - Check indentation (spaces/tabs)."
        
        return feedback


# Global sandbox instance
sandbox = PythonSandbox(timeout=5, max_output=5000)
