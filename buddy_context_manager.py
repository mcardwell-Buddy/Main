"""
BUDDY CONTEXT MANAGER - Multi-Step Session State Management
===========================================================

Maintains session-level state across multiple sequential requests to Buddy.
Provides read-only access to Phase 1/2 systems while tracking contextual
information across request sequences.

Thread-safe, with automatic state clearing and metrics aggregation.
"""

import json
import time
import threading
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from pathlib import Path
from enum import Enum

# Feature flag for multi-step testing
MULTI_STEP_TESTING_ENABLED = True


class ConfidenceBucket(Enum):
    """Confidence categories"""
    LOW = "low"        # < 0.55
    MEDIUM = "medium"  # 0.55-0.85
    HIGH = "high"      # > 0.85


@dataclass
class PreValidationRecord:
    """Record of pre-validation results"""
    status: str  # "passed", "failed", "not_triggered"
    catches: int = 0
    details: str = ""


@dataclass
class ApprovalRecord:
    """Record of approval decision"""
    path: str  # "approved", "clarification", "error"
    confidence: float = 0.0
    reasoning: str = ""


@dataclass
class RequestSnapshot:
    """Snapshot of a single request in a sequence"""
    request_id: str
    timestamp: str
    input: Dict[str, Any]
    
    # Outcomes
    success: bool = True
    execution_time_ms: float = 0.0
    error: Optional[str] = None
    
    # Metrics
    confidence: float = 0.0
    confidence_bucket: str = "medium"
    pre_validation: PreValidationRecord = field(default_factory=lambda: PreValidationRecord("not_triggered"))
    approval: ApprovalRecord = field(default_factory=lambda: ApprovalRecord("unknown"))
    clarification_triggered: bool = False
    soul_used: str = "mock"  # "mock" or "real"
    
    # Context from prior requests
    prior_context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self):
        """Convert to JSON-serializable dict"""
        return {
            "request_id": self.request_id,
            "timestamp": self.timestamp,
            "input": self.input,
            "success": self.success,
            "execution_time_ms": self.execution_time_ms,
            "error": self.error,
            "confidence": self.confidence,
            "confidence_bucket": self.confidence_bucket,
            "pre_validation": {
                "status": self.pre_validation.status,
                "catches": self.pre_validation.catches,
                "details": self.pre_validation.details
            },
            "approval": {
                "path": self.approval.path,
                "confidence": self.approval.confidence,
                "reasoning": self.approval.reasoning
            },
            "clarification_triggered": self.clarification_triggered,
            "soul_used": self.soul_used,
            "prior_context": self.prior_context
        }


@dataclass
class SessionMetrics:
    """Aggregated metrics for a session"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    success_rate: float = 0.0
    
    # Performance
    avg_execution_time_ms: float = 0.0
    min_execution_time_ms: float = float('inf')
    max_execution_time_ms: float = 0.0
    
    # Confidence
    confidence_mean: float = 0.0
    confidence_std_dev: float = 0.0
    confidence_min: float = 1.0
    confidence_max: float = 0.0
    
    # Confidence distribution
    low_confidence_count: int = 0
    medium_confidence_count: int = 0
    high_confidence_count: int = 0
    
    # Approval routing
    approved_count: int = 0
    clarification_count: int = 0
    error_count: int = 0
    
    # Pre-validation
    pre_validation_passes: int = 0
    pre_validation_failures: int = 0
    pre_validation_not_triggered: int = 0
    
    # Clarifications
    clarification_triggered_count: int = 0
    clarification_rate: float = 0.0
    
    # Soul usage
    soul_real_count: int = 0
    soul_mock_count: int = 0
    
    # Errors
    error_count: int = 0
    error_details: List[str] = field(default_factory=list)
    
    def to_dict(self):
        """Convert to JSON-serializable dict"""
        return asdict(self)


class SessionContext:
    """
    Thread-safe context manager for multi-step Buddy sequences.
    
    Maintains state across sequential requests while providing read-only
    access to Phase 1/2 systems.
    """
    
    def __init__(self, session_id: Optional[str] = None):
        """Initialize a new session context"""
        self.session_id = session_id or self._generate_session_id()
        self.created_at = datetime.now().isoformat()
        
        # State management
        self._lock = threading.RLock()
        self._request_history: List[RequestSnapshot] = []
        self._metrics = SessionMetrics()
        
        # Session state
        self._current_goal: Optional[str] = None
        self._current_confidence: float = 0.0
        self._current_approval_path: str = "unknown"
        self._clarification_count: int = 0
        self._prior_clarifications: List[str] = []
        
        # Feature flags
        self.feature_flags = {
            "multi_step_enabled": MULTI_STEP_TESTING_ENABLED,
            "track_confidence_distribution": True,
            "track_pre_validation": True,
            "track_approval_paths": True,
        }
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        timestamp = str(time.time())
        hash_obj = hashlib.md5(timestamp.encode())
        return f"session_{hash_obj.hexdigest()[:8]}"
    
    def add_request(
        self,
        input_data: Dict[str, Any],
        success: bool,
        confidence: float,
        approval_path: str,
        execution_time_ms: float,
        pre_validation_status: str = "not_triggered",
        pre_validation_catches: int = 0,
        clarification_triggered: bool = False,
        soul_used: str = "mock",
        error: Optional[str] = None
    ) -> RequestSnapshot:
        """
        Add a request result to the session context.
        
        Returns a RequestSnapshot with prior context included.
        """
        with self._lock:
            # Generate request ID
            request_id = f"{self.session_id}_req_{len(self._request_history) + 1}"
            
            # Create prior context from history
            prior_context = self._build_prior_context()
            
            # Create snapshot
            snapshot = RequestSnapshot(
                request_id=request_id,
                timestamp=datetime.now().isoformat(),
                input=input_data,
                success=success,
                execution_time_ms=execution_time_ms,
                error=error,
                confidence=confidence,
                confidence_bucket=self._get_confidence_bucket(confidence),
                pre_validation=PreValidationRecord(
                    status=pre_validation_status,
                    catches=pre_validation_catches
                ),
                approval=ApprovalRecord(
                    path=approval_path,
                    confidence=confidence
                ),
                clarification_triggered=clarification_triggered,
                soul_used=soul_used,
                prior_context=prior_context
            )
            
            # Add to history
            self._request_history.append(snapshot)
            
            # Update session state
            self._current_goal = input_data.get("goal", "")
            self._current_confidence = confidence
            self._current_approval_path = approval_path
            if clarification_triggered:
                self._clarification_count += 1
                self._prior_clarifications.append(request_id)
            
            # Update metrics
            self._update_metrics(snapshot)
            
            return snapshot
    
    def _build_prior_context(self) -> Dict[str, Any]:
        """Build context from previous requests in this session"""
        if not self._request_history:
            return {}
        
        last_request = self._request_history[-1]
        prior_requests = len(self._request_history)
        
        return {
            "prior_requests_in_session": prior_requests,
            "last_goal": last_request.input.get("goal", ""),
            "last_confidence": last_request.confidence,
            "last_approval_path": last_request.approval.path,
            "last_clarification_triggered": last_request.clarification_triggered,
            "cumulative_clarifications": self._clarification_count,
            "session_success_rate": self._metrics.success_rate,
            "average_confidence_so_far": self._metrics.confidence_mean,
        }
    
    def _get_confidence_bucket(self, confidence: float) -> str:
        """Categorize confidence into buckets"""
        if confidence < 0.55:
            return ConfidenceBucket.LOW.value
        elif confidence < 0.85:
            return ConfidenceBucket.MEDIUM.value
        else:
            return ConfidenceBucket.HIGH.value
    
    def _update_metrics(self, snapshot: RequestSnapshot):
        """Update session metrics with new request"""
        # Request counts
        self._metrics.total_requests += 1
        if snapshot.success:
            self._metrics.successful_requests += 1
        else:
            self._metrics.failed_requests += 1
        
        # Success rate
        self._metrics.success_rate = (
            self._metrics.successful_requests / self._metrics.total_requests
            if self._metrics.total_requests > 0 else 0.0
        )
        
        # Execution time
        self._metrics.min_execution_time_ms = min(
            self._metrics.min_execution_time_ms,
            snapshot.execution_time_ms
        )
        self._metrics.max_execution_time_ms = max(
            self._metrics.max_execution_time_ms,
            snapshot.execution_time_ms
        )
        total_time = sum(r.execution_time_ms for r in self._request_history)
        self._metrics.avg_execution_time_ms = (
            total_time / len(self._request_history)
            if self._request_history else 0.0
        )
        
        # Confidence distribution
        confidences = [r.confidence for r in self._request_history]
        if confidences:
            self._metrics.confidence_mean = sum(confidences) / len(confidences)
            self._metrics.confidence_min = min(confidences)
            self._metrics.confidence_max = max(confidences)
            
            # Calculate std dev
            if len(confidences) > 1:
                variance = sum((x - self._metrics.confidence_mean) ** 2 for x in confidences) / len(confidences)
                self._metrics.confidence_std_dev = variance ** 0.5
        
        # Confidence buckets
        bucket = snapshot.confidence_bucket
        if bucket == ConfidenceBucket.LOW.value:
            self._metrics.low_confidence_count += 1
        elif bucket == ConfidenceBucket.MEDIUM.value:
            self._metrics.medium_confidence_count += 1
        elif bucket == ConfidenceBucket.HIGH.value:
            self._metrics.high_confidence_count += 1
        
        # Approval routing
        if snapshot.approval.path == "approved":
            self._metrics.approved_count += 1
        elif snapshot.approval.path == "clarification":
            self._metrics.clarification_count += 1
        else:
            self._metrics.error_count += 1
        
        # Pre-validation
        if snapshot.pre_validation.status == "passed":
            self._metrics.pre_validation_passes += 1
        elif snapshot.pre_validation.status == "failed":
            self._metrics.pre_validation_failures += 1
        else:
            self._metrics.pre_validation_not_triggered += 1
        
        # Clarifications
        if snapshot.clarification_triggered:
            self._metrics.clarification_triggered_count += 1
        self._metrics.clarification_rate = (
            self._metrics.clarification_triggered_count / self._metrics.total_requests
            if self._metrics.total_requests > 0 else 0.0
        )
        
        # Soul usage
        if snapshot.soul_used == "real":
            self._metrics.soul_real_count += 1
        else:
            self._metrics.soul_mock_count += 1
        
        # Errors
        if snapshot.error:
            self._metrics.error_count += 1
            self._metrics.error_details.append(snapshot.error)
    
    def get_history(self) -> List[RequestSnapshot]:
        """Get the complete request history for this session"""
        with self._lock:
            return list(self._request_history)
    
    def get_metrics(self) -> SessionMetrics:
        """Get aggregated metrics for this session"""
        with self._lock:
            return SessionMetrics(**asdict(self._metrics))
    
    def get_current_state(self) -> Dict[str, Any]:
        """Get current session state"""
        with self._lock:
            return {
                "session_id": self.session_id,
                "created_at": self.created_at,
                "current_goal": self._current_goal,
                "current_confidence": self._current_confidence,
                "current_approval_path": self._current_approval_path,
                "total_requests": len(self._request_history),
                "clarification_count": self._clarification_count,
                "prior_clarifications": list(self._prior_clarifications),
                "success_rate": self._metrics.success_rate,
                "average_confidence": self._metrics.confidence_mean,
            }
    
    def get_request_snapshot(self, index: int) -> Optional[RequestSnapshot]:
        """Get a specific request snapshot by index"""
        with self._lock:
            if 0 <= index < len(self._request_history):
                return self._request_history[index]
            return None
    
    def clear_session(self):
        """Clear all session state and start fresh"""
        with self._lock:
            self._request_history.clear()
            self._metrics = SessionMetrics()
            self._current_goal = None
            self._current_confidence = 0.0
            self._current_approval_path = "unknown"
            self._clarification_count = 0
            self._prior_clarifications.clear()
    
    def export_to_json(self, filepath: str):
        """Export session data to JSON file"""
        with self._lock:
            export_data = {
                "session_id": self.session_id,
                "created_at": self.created_at,
                "exported_at": datetime.now().isoformat(),
                "metrics": self._metrics.to_dict(),
                "request_history": [r.to_dict() for r in self._request_history],
            }
            
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2)
    
    def import_from_json(self, filepath: str):
        """Import session data from JSON file"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Note: This is for inspection only; actual state management
        # happens through add_request() to ensure proper metric calculation
        with self._lock:
            self.session_id = data.get("session_id", self.session_id)
            self.created_at = data.get("created_at", self.created_at)


class SessionManager:
    """
    Manages multiple concurrent sessions.
    Thread-safe singleton for global session management.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._sessions: Dict[str, SessionContext] = {}
        self._lock = threading.RLock()
        self._initialized = True
    
    def create_session(self, session_id: Optional[str] = None) -> SessionContext:
        """Create a new session"""
        session = SessionContext(session_id)
        
        with self._lock:
            self._sessions[session.session_id] = session
        
        return session
    
    def get_session(self, session_id: str) -> Optional[SessionContext]:
        """Get an existing session"""
        with self._lock:
            return self._sessions.get(session_id)
    
    def list_sessions(self) -> List[str]:
        """List all active session IDs"""
        with self._lock:
            return list(self._sessions.keys())
    
    def delete_session(self, session_id: str):
        """Delete a session"""
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
    
    def export_all_sessions(self, directory: str):
        """Export all sessions to directory"""
        Path(directory).mkdir(exist_ok=True)
        
        with self._lock:
            for session_id, session in self._sessions.items():
                filepath = Path(directory) / f"{session_id}.json"
                session.export_to_json(str(filepath))


# Global session manager instance
_session_manager = SessionManager()


def get_session_manager() -> SessionManager:
    """Get the global session manager"""
    return _session_manager

