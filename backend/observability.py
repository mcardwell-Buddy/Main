"""
System Observability Layer

Provides end-to-end tracing without changing behavior.

Components:
1. TraceContext - Carries trace_id through entire request
2. DecisionTraceLogger - Logs decision points with reasoning
3. DuplicateDetector - Guards against duplicate messages
4. Whiteboard visibility ping - Signals mission creation

All logging is append-only JSONL format.
No behavior changes - observability only.
"""

import logging
import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import uuid4
from collections import defaultdict

logger = logging.getLogger(__name__)

# Files
DEBUG_DIR = Path('outputs/debug')
DECISION_TRACES_FILE = DEBUG_DIR / 'decision_traces.jsonl'
DUPLICATES_FILE = DEBUG_DIR / 'duplicates.jsonl'


class TraceContext:
    """Carries trace_id and related context through request."""
    
    def __init__(self, trace_id: Optional[str] = None):
        self.trace_id = trace_id or str(uuid4())
        self.created_at = datetime.utcnow().isoformat()
        self.decision_points = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'trace_id': self.trace_id,
            'created_at': self.created_at
        }


class DecisionTraceLogger:
    """
    Logs decision points for end-to-end tracing.
    
    Records:
    - Keyword analysis (what keywords were found)
    - Confidence scores (how confident was each classification)
    - Chosen path (which intent was selected)
    - Explicit reasoning (why this path was chosen)
    """
    
    @staticmethod
    def _ensure_dir():
        DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def log_classification(
        trace_id: str,
        message: str,
        intent_type: str,
        confidence: float,
        keyword_matches: Optional[Dict[str, int]] = None,
        reasoning: Optional[str] = None
    ):
        """Log intent classification decision."""
        DecisionTraceLogger._ensure_dir()
        
        record = {
            'decision_point': 'intent_classification',
            'trace_id': trace_id,
            'timestamp': datetime.utcnow().isoformat(),
            'input_message': message,
            'chosen_intent': intent_type,
            'confidence': confidence,
            'keyword_analysis': keyword_matches or {},
            'reasoning': reasoning or f"Selected {intent_type} with confidence {confidence:.2f}"
        }
        
        try:
            with open(DECISION_TRACES_FILE, 'a', encoding='utf-8') as f:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
            logger.debug(f"[TRACE] Classification: {intent_type} ({confidence:.2f})")
        except Exception as e:
            logger.warning(f"Failed to log classification trace: {e}")
    
    @staticmethod
    def log_routing(
        trace_id: str,
        intent_type: str,
        handler_name: str,
        reasoning: Optional[str] = None
    ):
        """Log routing decision."""
        DecisionTraceLogger._ensure_dir()
        
        record = {
            'decision_point': 'routing',
            'trace_id': trace_id,
            'timestamp': datetime.utcnow().isoformat(),
            'intent_type': intent_type,
            'chosen_handler': handler_name,
            'reasoning': reasoning or f"Routed {intent_type} to {handler_name}"
        }
        
        try:
            with open(DECISION_TRACES_FILE, 'a', encoding='utf-8') as f:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
            logger.debug(f"[TRACE] Routing: {handler_name}")
        except Exception as e:
            logger.warning(f"Failed to log routing trace: {e}")
    
    @staticmethod
    def log_deterministic_shortcut(
        trace_id: str,
        message: str,
        shortcut_type: str,
        result: str
    ):
        """Log when deterministic path is taken (math, etc)."""
        DecisionTraceLogger._ensure_dir()
        
        record = {
            'decision_point': 'deterministic_shortcut',
            'trace_id': trace_id,
            'timestamp': datetime.utcnow().isoformat(),
            'message': message,
            'shortcut_type': shortcut_type,
            'result_summary': result[:100],  # First 100 chars
            'reasoning': f"Took {shortcut_type} shortcut (no mission created)"
        }
        
        try:
            with open(DECISION_TRACES_FILE, 'a', encoding='utf-8') as f:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
            logger.debug(f"[TRACE] Deterministic shortcut: {shortcut_type}")
        except Exception as e:
            logger.warning(f"Failed to log shortcut trace: {e}")
    
    @staticmethod
    def log_mission_creation(
        trace_id: str,
        mission_id: str,
        objective_type: str,
        objective_description: str
    ):
        """Log when mission is created."""
        DecisionTraceLogger._ensure_dir()
        
        record = {
            'decision_point': 'mission_creation',
            'trace_id': trace_id,
            'timestamp': datetime.utcnow().isoformat(),
            'mission_id': mission_id,
            'objective_type': objective_type,
            'objective_description': objective_description[:100],
            'reasoning': f"Mission created: {objective_type}"
        }
        
        try:
            with open(DECISION_TRACES_FILE, 'a', encoding='utf-8') as f:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
            logger.debug(f"[TRACE] Mission creation: {mission_id}")
        except Exception as e:
            logger.warning(f"Failed to log mission creation trace: {e}")


class DuplicateDetector:
    """
    Guards against duplicate messages within 500ms.
    
    Tracks (session_id + message_hash) to detect duplicates.
    Logs duplicates to outputs/debug/duplicates.jsonl.
    """
    
    # In-memory cache: (session_id, message_hash) -> timestamp
    _cache = {}
    _duplicate_threshold_ms = 500
    
    @staticmethod
    def _hash_message(message: str) -> str:
        """Generate hash of message content."""
        return hashlib.sha256(message.encode()).hexdigest()[:16]
    
    @staticmethod
    def _cleanup_cache():
        """Remove old entries (> 1 second old)."""
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=1)
        
        keys_to_remove = [
            k for k, (ts, _) in DuplicateDetector._cache.items()
            if datetime.fromisoformat(ts) < cutoff
        ]
        
        for k in keys_to_remove:
            del DuplicateDetector._cache[k]
    
    @staticmethod
    def check_duplicate(
        session_id: str,
        message: str,
        trace_id: str
    ) -> bool:
        """
        Check if message is duplicate of recent message.
        
        Returns:
            True if duplicate detected, False otherwise
        """
        DuplicateDetector._cleanup_cache()
        
        msg_hash = DuplicateDetector._hash_message(message)
        cache_key = (session_id, msg_hash)
        
        now = datetime.utcnow()
        now_iso = now.isoformat()
        
        if cache_key in DuplicateDetector._cache:
            prev_timestamp_iso, prev_trace_id = DuplicateDetector._cache[cache_key]
            prev_timestamp = datetime.fromisoformat(prev_timestamp_iso)
            
            elapsed_ms = (now - prev_timestamp).total_seconds() * 1000
            
            if elapsed_ms < DuplicateDetector._duplicate_threshold_ms:
                # Duplicate detected
                DuplicateDetector._log_duplicate(
                    session_id, message, trace_id, prev_trace_id, elapsed_ms
                )
                return True
        
        # Not a duplicate - update cache
        DuplicateDetector._cache[cache_key] = (now_iso, trace_id)
        return False
    
    @staticmethod
    def _log_duplicate(
        session_id: str,
        message: str,
        current_trace_id: str,
        previous_trace_id: str,
        elapsed_ms: float
    ):
        """Log duplicate detection."""
        DEBUG_DIR.mkdir(parents=True, exist_ok=True)
        
        record = {
            'event': 'duplicate_detected',
            'timestamp': datetime.utcnow().isoformat(),
            'session_id': session_id,
            'message_hash': DuplicateDetector._hash_message(message),
            'message': message[:100],  # First 100 chars
            'current_trace_id': current_trace_id,
            'previous_trace_id': previous_trace_id,
            'elapsed_ms': elapsed_ms,
            'action': 'dropped'
        }
        
        try:
            with open(DUPLICATES_FILE, 'a', encoding='utf-8') as f:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
            logger.info(f"[DUPLICATE] Dropped duplicate message after {elapsed_ms:.0f}ms")
        except Exception as e:
            logger.warning(f"Failed to log duplicate: {e}")


def ensure_observability_dirs():
    """Create debug directories."""
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
