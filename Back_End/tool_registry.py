import threading
import time
import logging
from typing import Callable, Dict, Any
from Back_End.config import Config

class ToolRegistry:
    def __init__(self):
        self.tools = {}

    def register(self, name: str, func: Callable, mock_func: Callable = None, description: str = ""):
        self.tools[name] = {
            'func': func,
            'mock_func': mock_func,
            'description': description
        }

    def call(self, name: str, *args, domain: str = "_global", **kwargs) -> Any:
        tool = self.tools.get(name)
        if not tool:
            return {'error': f'Tool {name} not found.'}
        func = tool['mock_func'] if Config.MOCK_MODE and tool['mock_func'] else tool['func']
        result = {'error': 'Tool execution failed (timeout).'}
        start_time = time.time()
        def target():
            nonlocal result
            try:
                result = func(*args, **kwargs)
            except Exception as e:
                logging.exception(f"Tool {name} failed: {e}")
                result = {'error': str(e)}
        thread = threading.Thread(target=target)
        thread.start()
        thread.join(timeout=Config.TIMEOUT)
        latency_ms = (time.time() - start_time) * 1000
        
        if thread.is_alive():
            result = {'error': 'Tool execution timed out.'}
            success = False
            failure_mode = 'timeout'
        else:
            success = 'error' not in result
            failure_mode = result.get('failure_type') if not success else None
        
        # Track performance (now with domain)
        try:
            from Back_End.tool_performance import tracker
            tracker.record_usage(
                name, 
                success, 
                latency_ms, 
                domain=domain,
                failure_mode=failure_mode,
                context={'args_count': len(args), 'kwargs_count': len(kwargs)}
            )
        except Exception as e:
            logging.debug(f"Performance tracking skipped: {e}")
        
        return result

tool_registry = ToolRegistry()

