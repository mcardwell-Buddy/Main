"""
Autonomy manager: defines autonomy levels and escalation workflow.
Design-only: no automatic escalation.
"""

import logging
from datetime import datetime
from typing import Dict, Tuple, List, Optional
from Back_End.memory import memory


class AutonomyManager:
    """Manage agent autonomy levels (design-only)."""

    LEVELS = {
        1: "suggest_only",
        2: "draft_and_queue",
        3: "execute_safe_tools",
        4: "schedule_tasks",
        5: "cross_goal_optimization",
    }

    LEVEL_REQUIREMENTS = {
        1: {},
        2: {"min_successful_sessions": 10, "max_error_rate": 0.10, "min_confidence": 0.70},
        3: {"min_successful_sessions": 50, "max_error_rate": 0.05, "min_confidence": 0.75, "unsafe_tool_requests": 0},
        4: {"min_successful_sessions": 100, "max_error_rate": 0.05, "demonstrated_goal_chaining": True},
        5: {"min_successful_sessions": 200, "max_error_rate": 0.03, "demonstrated_cross_goal": True},
    }

    SAFE_TOOLS = {
        1: ["web_search", "calculate", "read_file", "list_directory", "get_time", "repo_index", "file_summary", "dependency_map", "reflect", "learning_query", "understanding_metrics"],
        2: ["web_search", "calculate", "read_file", "list_directory", "get_time", "repo_index", "file_summary", "dependency_map", "reflect", "learning_query", "understanding_metrics"],
        3: ["web_search", "calculate", "read_file", "list_directory", "get_time", "repo_index", "file_summary", "dependency_map", "reflect", "learning_query", "understanding_metrics"],
        4: ["web_search", "calculate", "read_file", "list_directory", "get_time", "repo_index", "file_summary", "dependency_map", "reflect", "learning_query", "understanding_metrics"],
        5: ["web_search", "calculate", "read_file", "list_directory", "get_time", "repo_index", "file_summary", "dependency_map", "reflect", "learning_query", "understanding_metrics"],
    }

    def __init__(self):
        self.current_level = 1
        self.session_stats = self._load_session_stats()
        self.requests_key = "autonomy_escalation_requests"
        self.decisions_key = "autonomy_decisions"

    def get_current_level(self) -> int:
        return self.current_level

    def can_tool_execute_at_level(self, tool_name: str, level: int) -> bool:
        return tool_name in self.SAFE_TOOLS.get(level, [])

    def evaluate_escalation(self, target_level: int) -> Tuple[bool, str, Dict]:
        if target_level <= self.current_level:
            return False, "Target level must be higher than current", {}
        if target_level > 5:
            return False, "Maximum autonomy level is 5", {}

        requirements = self.LEVEL_REQUIREMENTS.get(target_level, {})
        metrics = self.session_stats

        for req_key, req_value in requirements.items():
            if req_key == "min_successful_sessions":
                if metrics.get("successful_sessions", 0) < req_value:
                    return False, f"Need {req_value} successful sessions, have {metrics.get('successful_sessions', 0)}", metrics
            elif req_key == "max_error_rate":
                error_rate = 1.0 - metrics.get("success_rate", 0.0)
                if error_rate > req_value:
                    return False, f"Error rate {error_rate:.1%} exceeds limit {req_value:.1%}", metrics
            elif req_key == "min_confidence":
                if metrics.get("avg_confidence", 0.0) < req_value:
                    return False, f"Avg confidence {metrics.get('avg_confidence', 0.0):.2f} below {req_value:.2f}", metrics
            elif req_key == "unsafe_tool_requests":
                if metrics.get("unsafe_requests", 0) > req_value:
                    return False, f"Unsafe tool requests: {metrics.get('unsafe_requests', 0)}", metrics

        return True, "Meets all requirements", metrics

    def request_escalation(self, target_level: int, reason: str = "") -> Dict:
        can_escalate, reason_msg, metrics = self.evaluate_escalation(target_level)
        request_id = f"req_{datetime.utcnow().timestamp()}"
        request = {
            "id": request_id,
            "type": "autonomy_escalation_request",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "current_level": self.current_level,
            "requested_level": target_level,
            "meets_requirements": can_escalate,
            "justification": reason,
            "reason_if_not_met": reason_msg,
            "metrics": metrics,
            "status": "pending_human_review",
            "requires_human_approval": True,
        }

        existing = memory.safe_call("get", self.requests_key) or []
        existing.append(request)
        memory.safe_call("set", self.requests_key, existing)

        logging.warning(f"Agent requested escalation to level {target_level}: {reason}")
        return request

    def approve_escalation(self, request_id: str, approved: bool, human_comment: str = "") -> Dict:
        requests = memory.safe_call("get", self.requests_key) or []
        request = next((r for r in requests if r.get("id") == request_id), None)
        if not request:
            return {"error": "Request not found"}

        if approved:
            old_level = self.current_level
            self.current_level = request["requested_level"]
            action = {
                "type": "autonomy_escalation_approved",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "old_level": old_level,
                "new_level": self.current_level,
                "human_comment": human_comment,
                "approved_by": "human_reviewer",
            }
            request["status"] = "approved"
            logging.warning(f"AUTONOMY ESCALATION APPROVED: Level {old_level} → {self.current_level}")
        else:
            action = {
                "type": "autonomy_escalation_denied",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "requested_level": request["requested_level"],
                "human_comment": human_comment,
                "denied_by": "human_reviewer",
            }
            request["status"] = "denied"
            logging.info(f"AUTONOMY ESCALATION DENIED: Level {request['requested_level']}")

        memory.safe_call("set", self.requests_key, requests)
        decisions = memory.safe_call("get", self.decisions_key) or []
        decisions.append(action)
        memory.safe_call("set", self.decisions_key, decisions)

        return action

    def list_requests(self, status: Optional[str] = None) -> List[Dict]:
        requests = memory.safe_call("get", self.requests_key) or []
        if not status:
            return requests
        return [r for r in requests if r.get("status") == status]

    def _load_session_stats(self) -> Dict:
        return {
            "total_sessions": 0,
            "successful_sessions": 0,
            "success_rate": 1.0,
            "avg_confidence": 0.8,
            "unsafe_requests": 0,
            "total_tools_used": 0,
        }


autonomy_manager = AutonomyManager()

