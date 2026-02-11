"""
Execution Learning Signal Emitter

Firebase-only writer for execution learning signals.
OBSERVE-ONLY: Emits signals after execution completes.
Does NOT affect execution behavior.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional


class ExecutionLearningEmitter:
    """
    Emits learning signals for completed executions.
    
    Rules:
    - Emit exactly one signal per execution
    - Firebase-only persistence (no local files)
    - Non-blocking (failures are logged but don't halt execution)
    - Observe-only (signals are for future analysis, not current decisions)
    """
    
    def __init__(self):
        from Back_End.memory_manager import memory
        self.memory = memory
    
    def emit_execution_outcome(
        self,
        mission_id: str,
        intent: str,
        tool_used: str,
        tool_confidence: float,
        success: bool,
        execution_result: Dict[str, Any],
        objective: Optional[str] = None,
        error: Optional[str] = None
    ) -> None:
        """
        Emit a learning signal for an execution outcome.
        
        This is called AFTER execution completes.
        Does NOT affect execution behavior.
        
        Args:
            mission_id: Mission identifier
            intent: Classified intent (e.g., "calculation", "extraction")
            tool_used: Tool that was used
            tool_confidence: Confidence score from tool selector
            success: Whether execution succeeded
            execution_result: Result from tool execution
            objective: Original mission objective (optional)
            error: Error message if failed (optional)
        """
        try:
            signal = {
                "signal_type": "execution_outcome",
                "signal_layer": "execution",
                "signal_source": "execution_service",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": {
                    "mission_id": mission_id,
                    "objective": objective,
                    "intent": intent,
                    "tool_used": tool_used,
                    "tool_confidence": round(tool_confidence, 3),
                    "success": success,
                    "error": error,
                    "result_preview": self._extract_result_preview(execution_result)
                }
            }
            
            # Save to Firebase memory only
            signal_key = f"execution_outcome:{mission_id}"
            self.memory.safe_call("set", signal_key, signal)
            
            # Also update index for querying
            index_key = "execution_learning_signal_index"
            existing_index = self.memory.safe_call("get", index_key) or []
            existing_index.append(signal_key)
            # Keep index bounded
            if len(existing_index) > 1000:
                existing_index = existing_index[-1000:]
            self.memory.safe_call("set", index_key, existing_index)
        
        except Exception as e:
            # Log the error but DO NOT let it affect execution
            # This is observe-only mode - learning failures are non-critical
            print(f"[LEARNING] Warning: Failed to emit learning signal: {e}")
            # Swallow the exception - execution must continue
    
    def _extract_result_preview(self, execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract a preview of the result for learning (limit size)"""
        if not execution_result:
            return {}
        
        preview = {}
        
        # Include success flag
        if 'success' in execution_result:
            preview['success'] = execution_result['success']
        
        # Include error if present
        if 'error' in execution_result:
            preview['error'] = str(execution_result['error'])[:200]  # Limit error length
        
        # Include result value if present (limit to first 200 chars)
        if 'result' in execution_result:
            result_str = str(execution_result['result'])
            preview['result'] = result_str[:200] + ('...' if len(result_str) > 200 else '')
        
        # Include expression if present (for calculations)
        if 'expression' in execution_result:
            preview['expression'] = execution_result['expression']
        
        return preview


# Global emitter instance
_emitter: Optional[ExecutionLearningEmitter] = None


def get_learning_emitter() -> ExecutionLearningEmitter:
    """Get or create global learning emitter"""
    global _emitter
    if _emitter is None:
        _emitter = ExecutionLearningEmitter()
    return _emitter

