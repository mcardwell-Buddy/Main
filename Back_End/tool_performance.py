import json
import logging
from datetime import datetime
from Back_End.memory import memory

class ToolPerformanceTracker:
    def __init__(self):
        self.collection_key = "tool_performance"
    
    def record_usage(self, tool_name: str, success: bool, latency_ms: float, 
                    domain: str = "_global", failure_mode: str = None, context: dict = None):
        """
        Track tool performance scoped to domain.
        
        Args:
            tool_name: Name of tool
            success: Whether tool succeeded
            latency_ms: Execution time
            domain: Domain context (e.g., 'marketing', 'crypto', 'engineering')
            failure_mode: Type of failure if applicable
            context: Additional context
        """
        try:
            # Record domain-specific performance
            domain_key = f"{self.collection_key}:{tool_name}:{domain}"
            domain_data = memory.safe_call('get', domain_key) or self._init_record(tool_name, domain)
            
            # Update domain-specific metrics
            domain_data['total_calls'] += 1
            if success:
                domain_data['successful_calls'] += 1
            else:
                domain_data['failed_calls'] += 1
                if failure_mode:
                    domain_data['failure_modes'].append(failure_mode)
                    # Keep only last 10 failure modes
                    if len(domain_data['failure_modes']) > 10:
                        domain_data['failure_modes'] = domain_data['failure_modes'][-10:]
            
            # Update domain-specific latency (running average)
            prev_avg = domain_data['avg_latency_ms']
            n = domain_data['total_calls']
            domain_data['avg_latency_ms'] = ((prev_avg * (n - 1)) + latency_ms) / n
            
            # Update timestamp
            domain_data['last_used'] = datetime.utcnow().isoformat()
            
            # Append to history (keep last 10)
            domain_data['history'].append({
                'timestamp': domain_data['last_used'],
                'success': success,
                'latency_ms': latency_ms,
                'failure_mode': failure_mode,
                'context': context or {}
            })
            if len(domain_data['history']) > 10:
                domain_data['history'] = domain_data['history'][-10:]
            
            # Save domain-specific record
            memory.safe_call('set', domain_key, domain_data)
            
            # ALSO update global aggregate (for fallback when no domain history)
            global_key = f"{self.collection_key}:{tool_name}:_global"
            global_data = memory.safe_call('get', global_key) or self._init_record(tool_name, "_global")
            
            # Update global metrics
            global_data['total_calls'] += 1
            if success:
                global_data['successful_calls'] += 1
            else:
                global_data['failed_calls'] += 1
            
            prev_avg_global = global_data['avg_latency_ms']
            n_global = global_data['total_calls']
            global_data['avg_latency_ms'] = ((prev_avg_global * (n_global - 1)) + latency_ms) / n_global
            global_data['last_used'] = datetime.utcnow().isoformat()
            
            memory.safe_call('set', global_key, global_data)
            return domain_data
        except Exception as e:
            logging.error(f"Tool performance tracking failed: {e}")
            return None
    
    def _init_record(self, tool_name: str, domain: str) -> dict:
        """Initialize a new performance record"""
        return {
            'tool_name': tool_name,
            'domain': domain,
            'total_calls': 0,
            'successful_calls': 0,
            'failed_calls': 0,
            'avg_latency_ms': 0.0,
            'last_used': None,
            'failure_modes': [],
            'history': [],
            'created_at': datetime.utcnow().isoformat()
        }
    
    def get_stats(self, tool_name: str, domain: str = "_global"):
        """
        Get stats for tool in specific domain.
        If no domain history exists, falls back to global.
        """
        domain_key = f"{self.collection_key}:{tool_name}:{domain}"
        stats = memory.safe_call('get', domain_key)
        
        # If no domain-specific history and not requesting global, fall back to global
        if not stats and domain != "_global":
            logging.debug(f"No history for {tool_name} in domain '{domain}', using global fallback")
            global_key = f"{self.collection_key}:{tool_name}:_global"
            stats = memory.safe_call('get', global_key)
        
        return stats
    
    def get_all_stats(self):
        """Note: This is a simplified version. In production, you'd query all keys matching the pattern."""
        from Back_End.tool_registry import tool_registry
        all_stats = {}
        for tool_name in tool_registry.tools.keys():
            # Get global stats for each tool
            stats = self.get_stats(tool_name, domain="_global")
            if stats:
                all_stats[tool_name] = stats
        return all_stats
    
    def get_usefulness_score(self, tool_name: str, domain: str = "_global") -> float:
        """
        Calculate a usefulness score (0.0 to 1.0) for tool in domain.
        Falls back to global if no domain history.
        """
        stats = self.get_stats(tool_name, domain)
        if not stats or stats['total_calls'] == 0:
            return 0.5  # neutral default
        
        success_rate = stats['successful_calls'] / stats['total_calls']
        # Weight by total calls (more calls = more confidence in the metric)
        confidence = min(1.0, stats['total_calls'] / 10.0)
        return (success_rate * 0.7 + 0.5 * 0.3) * confidence

tracker = ToolPerformanceTracker()

