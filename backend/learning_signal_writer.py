"""
Learning Signal Writer for Capability Classification
Emits learning signals when tasks are classified
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from backend.capability_boundary_model import ClassificationResult, Capability


class LearningSignalWriter:
    """Writes learning signals from capability classification"""
    
    def __init__(self, log_path: str = "learning_signals.jsonl"):
        """Initialize signal writer"""
        self.log_path = Path(log_path)
        # Ensure parent directory exists
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
    
    def emit_classification_signal(
        self,
        result: ClassificationResult,
    ) -> None:
        """
        Emit a learning signal when a task is classified.
        Signal is appended to learning_signals.jsonl
        """
        signal = {
            "signal_type": "capability_classified",
            "signal_layer": "cognition",
            "signal_source": "capability_model",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "task_description": result.task_description,
                "capability": result.capability.value,
                "confidence": round(result.confidence, 3),
                "evidence_keywords": result.evidence_keywords,
                "reasoning": result.reasoning,
                "classified_at": result.classified_at.isoformat(),
            },
        }
        
        # Append to JSONL file (one JSON object per line)
        with open(self.log_path, "a") as f:
            f.write(json.dumps(signal) + "\n")
    
    def read_signals(self) -> list:
        """Read all logged signals"""
        if not self.log_path.exists():
            return []
        
        signals = []
        with open(self.log_path, "r") as f:
            for line in f:
                if line.strip():
                    signals.append(json.loads(line))
        
        return signals
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics from logged signals"""
        signals = self.read_signals()
        
        if not signals:
            return {
                "total_signals": 0,
                "digital_count": 0,
                "physical_count": 0,
                "hybrid_count": 0,
                "avg_confidence": 0.0,
            }
        
        digital_count = sum(
            1 for s in signals if s["data"]["capability"] == "digital"
        )
        physical_count = sum(
            1 for s in signals if s["data"]["capability"] == "physical"
        )
        hybrid_count = sum(
            1 for s in signals if s["data"]["capability"] == "hybrid"
        )
        
        confidences = [s["data"]["confidence"] for s in signals]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        return {
            "total_signals": len(signals),
            "digital_count": digital_count,
            "physical_count": physical_count,
            "hybrid_count": hybrid_count,
            "avg_confidence": round(avg_confidence, 3),
            "digital_percentage": round((digital_count / len(signals) * 100), 1),
            "physical_percentage": round((physical_count / len(signals) * 100), 1),
            "hybrid_percentage": round((hybrid_count / len(signals) * 100), 1),
        }


# Global writer instance
_writer: Optional[LearningSignalWriter] = None


def get_signal_writer(
    log_path: str = "learning_signals.jsonl",
) -> LearningSignalWriter:
    """Get or create global signal writer"""
    global _writer
    if _writer is None:
        _writer = LearningSignalWriter(log_path)
    return _writer
