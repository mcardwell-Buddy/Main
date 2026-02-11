"""
Mission Whiteboard: Read-only reconstruction of mission history.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from Back_End.learning.negative_knowledge_registry import get_negative_knowledge_for_whiteboard
from Back_End.revenue_readiness_gate import RevenueReadinessGate


# Support environment variable overrides for testing
MISSIONS_FILE = Path(os.environ.get("MISSIONS_FILE", "outputs/phase25/missions.jsonl"))
SIGNALS_FILE = Path(os.environ.get("LEARNING_SIGNALS_FILE", "outputs/phase25/learning_signals.jsonl"))
GOALS_FILE = Path(os.environ.get("GOALS_FILE", "outputs/phase25/goals.jsonl"))
PROGRAMS_FILE = Path(os.environ.get("PROGRAMS_FILE", "outputs/phase25/programs.jsonl"))
REGRET_REGISTRY_FILE = Path(os.environ.get("REGRET_REGISTRY_FILE", "outputs/phase25/regret_registry.jsonl"))
ARTIFACTS_FILE = Path(os.environ.get("ARTIFACTS_FILE", "outputs/phase25/artifacts.jsonl"))
BUILDS_FILE = Path(os.environ.get("BUILDS_FILE", "outputs/phase11/builds.jsonl"))
DELIVERABLES_FILE = Path(os.environ.get("DELIVERABLES_FILE", "outputs/phase25/build_deliverables.jsonl"))
BUILD_REVIEWS_FILE = Path(os.environ.get("BUILD_REVIEWS_FILE", "outputs/phase25/build_reviews.jsonl"))


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    records: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def _reconstruct_builds(build_records: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Reconstruct latest build state from append-only build records."""
    builds: Dict[str, Dict[str, Any]] = {}
    for record in build_records:
        event_type = record.get("event_type")

        if event_type == "build_created":
            build = record.get("build", {})
            build_id = build.get("build_id")
            if not build_id:
                continue
            builds[build_id] = {
                "build_id": build_id,
                "name": build.get("name"),
                "objective": build.get("objective"),
                "build_type": build.get("build_type"),
                "current_stage": build.get("current_stage"),
                "status": build.get("status"),
                "mission_ids": list(build.get("mission_ids", [])),
                "artifact_ids": list(build.get("artifact_ids", [])),
                "investment_score": build.get("investment_score"),
                "created_at": build.get("created_at"),
                "updated_at": build.get("updated_at"),
            }
            continue

        build_id = record.get("build_id")
        if not build_id or build_id not in builds:
            continue

        current = builds[build_id]

        if event_type == "build_stage_update":
            current["current_stage"] = record.get("new_stage", current.get("current_stage"))
            current["updated_at"] = record.get("timestamp", current.get("updated_at"))
        elif event_type == "build_status_update":
            current["status"] = record.get("status", current.get("status"))
            current["updated_at"] = record.get("timestamp", current.get("updated_at"))
        elif event_type == "build_artifact_attached":
            artifact_id = record.get("artifact_id")
            if artifact_id and artifact_id not in current["artifact_ids"]:
                current["artifact_ids"].append(artifact_id)
            current["updated_at"] = record.get("timestamp", current.get("updated_at"))
        elif event_type == "build_investment_update":
            current["investment_score"] = record.get("investment_score", current.get("investment_score"))
            current["updated_at"] = record.get("timestamp", current.get("updated_at"))

    return builds


def _latest_build_reviews(review_records: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Return latest review per build_id."""
    latest: Dict[str, Dict[str, Any]] = {}
    for record in review_records:
        build_id = record.get("build_id")
        if not build_id:
            continue
        latest[build_id] = {
            "verdict": record.get("verdict"),
            "confidence": record.get("confidence"),
            "reviewer": record.get("reviewer"),
            "timestamp": record.get("timestamp"),
            "rationale": record.get("rationale"),
        }
    return latest


def _deliverables_for_mission(deliverables: List[Dict[str, Any]], mission_id: str) -> List[Dict[str, Any]]:
    """Filter deliverables by mission_id."""
    results: List[Dict[str, Any]] = []
    for d in deliverables:
        if d.get("mission_id") == mission_id:
            results.append(d)
    return results


def _artifacts_summary(mission_id: str) -> Dict[str, Any]:
    """Summarize artifacts for a mission (ignores artifacts without mission_id)."""
    artifacts = _read_jsonl(ARTIFACTS_FILE)
    mission_artifacts = [a for a in artifacts if a.get("created_by") == mission_id]

    return {
        "artifact_count": len(mission_artifacts),
        "artifact_types": sorted({a.get("artifact_type") for a in mission_artifacts if a.get("artifact_type")}),
        "items": [
            {
                "title": a.get("title"),
                "presentation_hint": a.get("presentation_hint"),
                "artifact_type": a.get("artifact_type"),
            }
            for a in mission_artifacts
        ]
    }


def _find_mission_created(mission_id: str, mission_records: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    for record in mission_records:
        if record.get("event_type") == "mission_created":
            mission = record.get("mission", {})
            if mission.get("mission_id") == mission_id:
                return record
    return None


def _find_latest_status(mission_id: str, mission_records: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    latest = None
    for record in mission_records:
        if record.get("event_type") == "mission_status_update" and record.get("mission_id") == mission_id:
            latest = record
    return latest


def _latest_progress(mission_id: str, signals: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    latest = None
    for signal in signals:
        if signal.get("signal_type") == "mission_progress_update" and signal.get("mission_id") == mission_id:
            latest = signal
    return latest


def _navigation_summary(mission_id: str, signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    summary: List[Dict[str, Any]] = []
    for signal in signals:
        if signal.get("signal_type") == "intent_action_taken" and signal.get("mission_id") == mission_id:
            action = signal.get("action", {})
            summary.append({
                "timestamp": signal.get("timestamp"),
                "action": "intent_action_taken",
                "text": action.get("text"),
                "href": action.get("href"),
                "confidence": signal.get("confidence")
            })
    return summary


def _selector_summary(mission_id: str, signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Compute selector performance summary for mission."""
    selector_stats: Dict[str, Any] = {}
    
    for signal in signals:
        if signal.get("signal_type") == "selector_outcome" and signal.get("mission_id") == mission_id:
            selector = signal.get("selector", "unknown")
            outcome = signal.get("outcome", "unknown")
            duration_ms = signal.get("duration_ms", 0)
            
            if selector not in selector_stats:
                selector_stats[selector] = {
                    "selector": selector,
                    "selector_type": signal.get("selector_type", "unknown"),
                    "attempts": 0,
                    "successes": 0,
                    "failures": 0,
                    "total_duration_ms": 0,
                    "avg_duration_ms": 0.0,
                    "success_rate": 0.0
                }
            
            selector_stats[selector]["attempts"] += 1
            selector_stats[selector]["total_duration_ms"] += duration_ms
            
            if outcome == "success":
                selector_stats[selector]["successes"] += 1
            else:
                selector_stats[selector]["failures"] += 1
    
    # Compute derived metrics
    summary: List[Dict[str, Any]] = []
    for selector_data in selector_stats.values():
        if selector_data["attempts"] > 0:
            selector_data["avg_duration_ms"] = selector_data["total_duration_ms"] / selector_data["attempts"]
            selector_data["success_rate"] = selector_data["successes"] / selector_data["attempts"]
        summary.append(selector_data)
    
    return summary


def _goal_evaluation(mission_id: str, signals: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Extract latest goal evaluation for mission."""
    for signal in reversed(signals):
        if signal.get("signal_type") == "goal_evaluation" and signal.get("mission_id") == mission_id:
            return {
                "goal_satisfied": signal.get("goal_satisfied"),
                "confidence": signal.get("confidence", 0.0),
                "evidence": signal.get("evidence", []),
                "gap_reason": signal.get("gap_reason"),
                "timestamp": signal.get("timestamp")
            }
    return None


def _opportunities_summary(mission_id: str, signals: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Extract opportunity normalization summary for mission."""
    summary = {
        "opportunities_created": 0,
        "opportunity_types": {},
        "avg_confidence": 0.0
    }
    
    for signal in reversed(signals):
        if signal.get("signal_type") == "opportunity_normalized" and signal.get("mission_id") == mission_id:
            summary["opportunities_created"] = signal.get("opportunities_created", 0)
            summary["opportunity_types"] = signal.get("opportunity_types", {})
            summary["avg_confidence"] = signal.get("avg_confidence", 0.0)
            break
    
    return summary


def _ambiguity_evaluation(mission_id: str, signals: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Extract ambiguity evaluation for mission."""
    for signal in reversed(signals):
        if signal.get("signal_type") == "mission_ambiguous" and signal.get("mission_id") == mission_id:
            return {
                "ambiguous": signal.get("ambiguous"),
                "reason": signal.get("reason"),
                "recommended_next_mission": signal.get("recommended_next_mission"),
                "confidence_gap": signal.get("confidence_gap", 0.0),
                "opportunity_weakness": signal.get("opportunity_weakness", 0.0),
                "evidence_sufficiency": signal.get("evidence_sufficiency", 0.0),
                "timestamp": signal.get("timestamp")
            }
    return None


def _cost_summary(mission_id: str, signals: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Extract cost summary for mission."""
    for signal in reversed(signals):
        if signal.get("signal_type") == "mission_cost_report" and signal.get("mission_id") == mission_id:
            cost_units = signal.get("cost_units", {})
            return {
                "total_duration_sec": signal.get("total_duration_sec", 0.0),
                "pages_visited": signal.get("pages_visited", 0),
                "selectors_attempted": signal.get("selectors_attempted", 0),
                "selectors_failed": signal.get("selectors_failed", 0),
                "retries_total": signal.get("retries_total", 0),
                "time_cost": cost_units.get("time_cost", 0.0),
                "page_cost": cost_units.get("page_cost", 0),
                "failure_cost": cost_units.get("failure_cost", 0),
                "timestamp": signal.get("timestamp")
            }
    return None


def _decision_trace(mission_id: str, signals: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Extract most recent decision rationale for mission."""
    for signal in reversed(signals):
        if signal.get("signal_type") == "decision_rationale" and signal.get("mission_id") == mission_id:
            rationale = signal.get("rationale", {})
            return {
                "decision": rationale.get("decision"),
                "because": rationale.get("because", []),
                "action_type": signal.get("action_type"),
                "timestamp": signal.get("timestamp")
            }
    return None


def _negative_knowledge_summary(outputs_dir: str = "outputs/phase25") -> Dict[str, Any]:
    """
    Get negative knowledge summary for whiteboard.
    
    Returns:
        Dictionary with "what_buddy_avoids" insights
    """
    try:
        return get_negative_knowledge_for_whiteboard(outputs_dir=outputs_dir)
    except Exception as e:
        # Graceful degradation if registry not available
        return {
            "summary": {},
            "high_confidence_patterns": {},
            "total_patterns": 0,
            "error": str(e)
        }


def _expectation_delta(mission_id: str, signals: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Extract expectation delta evaluation for a mission.
    
    Returns:
        Dict with alignment, confidence, reason or None if not evaluated
    """
    # Find the expectation_delta signal for this mission
    expectation_signals = [
        s for s in signals
        if s.get("signal_type") == "expectation_delta" and s.get("mission_id") == mission_id
    ]
    
    if not expectation_signals:
        return None
    
    # Take the most recent evaluation (last one)
    latest = expectation_signals[-1]
    
    return {
        "alignment": latest.get("alignment"),
        "confidence": latest.get("confidence"),
        "reason": latest.get("reason"),
        "timestamp": latest.get("timestamp")
    }


def _drift_alerts(signals: List[Dict[str, Any]], limit: int = 5) -> List[Dict[str, Any]]:
    """
    Extract recent drift warnings for whiteboard.
    """
    alerts = [
        {
            "metric": s.get("metric"),
            "baseline": s.get("baseline"),
            "current": s.get("current"),
            "delta": s.get("delta"),
            "mission_id": s.get("mission_id"),
            "mission_thread_id": s.get("mission_thread_id"),
            "timestamp": s.get("timestamp")
        }
        for s in signals
        if s.get("signal_type") == "drift_warning"
    ]
    return alerts[-limit:]


def _mission_drift_warning(mission_id: str, signals: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Extract drift warning for a specific mission.
    """
    for s in reversed(signals):
        if s.get("signal_type") == "drift_warning" and s.get("mission_id") == mission_id:
            return {
                "metric": s.get("metric"),
                "baseline": s.get("baseline"),
                "current": s.get("current"),
                "delta": s.get("delta"),
                "timestamp": s.get("timestamp")
            }
    return None


def get_mission_whiteboard(mission_id: str) -> Dict[str, Any]:
    mission_records = _read_jsonl(MISSIONS_FILE)
    signals = _read_jsonl(SIGNALS_FILE)

    created_record = _find_mission_created(mission_id, mission_records)
    latest_status = _find_latest_status(mission_id, mission_records)
    progress = _latest_progress(mission_id, signals)

    mission = (created_record or {}).get("mission", {})
    objective = mission.get("objective", {})
    scope = mission.get("scope", {})

    status = (latest_status or {}).get("status") or mission.get("status") or "active"
    start_time = mission.get("created_at")
    end_time = (latest_status or {}).get("completed_at")

    constraints = {
        "max_pages": scope.get("max_pages", 0) or 0,
        "max_duration_sec": scope.get("max_duration_seconds", 0) or 0,
        "target_items": objective.get("target")
    }

    progress_block = {
        "pages_visited": 0,
        "items_collected": (progress or {}).get("items_collected", 0) or 0,
        "actions_taken": len(_navigation_summary(mission_id, signals))
    }

    termination = {
        "reason": (latest_status or {}).get("reason"),
        "confidence": None
    }
    
    goal_eval = _goal_evaluation(mission_id, signals)
    opportunities_summary = _opportunities_summary(mission_id, signals)
    ambiguity_eval = _ambiguity_evaluation(mission_id, signals)
    cost_summary = _cost_summary(mission_id, signals)
    decision_trace = _decision_trace(mission_id, signals)
    negative_knowledge = _negative_knowledge_summary()
    expectation_delta = _expectation_delta(mission_id, signals)
    expectation_alignment = expectation_delta.get("alignment") if expectation_delta else None
    expectation_misaligned = expectation_alignment == "misaligned"
    drift_alerts = _drift_alerts(signals)
    mission_drift_warning = _mission_drift_warning(mission_id, signals)

    build_records = _read_jsonl(BUILDS_FILE)
    deliverable_records = _read_jsonl(DELIVERABLES_FILE)
    review_records = _read_jsonl(BUILD_REVIEWS_FILE)

    builds = _reconstruct_builds(build_records)
    latest_reviews = _latest_build_reviews(review_records)

    mission_builds = []
    for build in builds.values():
        if mission_id in (build.get("mission_ids") or []):
            review = latest_reviews.get(build.get("build_id"))
            deliverables_for_build = [
                d for d in deliverable_records
                if d.get("build_id") == build.get("build_id")
            ]
            readiness = RevenueReadinessGate.evaluate_from_records(
                build_record=build,
                deliverable_records=deliverables_for_build,
                latest_review_record=review,
            )
            mission_builds.append({
                "build_id": build.get("build_id"),
                "name": build.get("name"),
                "build_type": build.get("build_type"),
                "current_stage": build.get("current_stage"),
                "status": build.get("status"),
                "investment_score": build.get("investment_score"),
                "latest_review": review,
                "revenue_readiness": readiness.to_dict(),
            })

    mission_deliverables = _deliverables_for_mission(deliverable_records, mission_id)

    return {
        "mission_id": mission_id,
        "status": status,
        "objective": objective.get("description") or "",
        "artifacts_summary": _artifacts_summary(mission_id),
        "drift_alerts": drift_alerts,
        "mission_drift_warning": mission_drift_warning,
        "start_time": start_time,
        "end_time": end_time,
        "constraints": constraints,
        "progress": progress_block,
        "navigation_summary": _navigation_summary(mission_id, signals),
        "selector_summary": _selector_summary(mission_id, signals),
        "goal_evaluation": goal_eval,
        "expectation_delta": expectation_delta,
        "expectation_alignment": expectation_alignment,
        "expectation_misaligned": expectation_misaligned,
        "opportunities": opportunities_summary,
        "ambiguity": ambiguity_eval,
        "cost_summary": cost_summary,
        "decision_trace": decision_trace,
        "what_buddy_avoids": negative_knowledge,
        "termination": termination,
        "goal_id": mission.get("goal_id"),
        "program_id": mission.get("program_id"),
        "mission_thread_id": mission.get("mission_thread_id"),
        "builds": mission_builds,
        "deliverables": mission_deliverables
    }


def get_goal_whiteboard(goal_id: str) -> Dict[str, Any]:
    """
    Get goal view with aggregated program and mission data.
    
    Returns:
        Goal view with programs count, missions count, and completion ratio
    """
    goals = _read_jsonl(GOALS_FILE)
    programs = _read_jsonl(PROGRAMS_FILE)
    mission_records = _read_jsonl(MISSIONS_FILE)
    signals = _read_jsonl(SIGNALS_FILE)
    
    # Find goal
    goal_data = None
    for g in goals:
        if g.get("goal_id") == goal_id:
            goal_data = g
            break
    
    if not goal_data:
        return {
            "goal_id": goal_id,
            "error": "goal_not_found"
        }
    
    # Find programs under this goal
    goal_programs = [p for p in programs if p.get("goal_id") == goal_id]
    
    # Find missions under these programs
    program_ids = [p.get("program_id") for p in goal_programs]
    goal_missions = []
    for record in mission_records:
        if record.get("event_type") == "mission_created":
            mission = record.get("mission", {})
            if mission.get("program_id") in program_ids:
                goal_missions.append(mission)
    
    # Calculate completion stats
    total_missions = len(goal_missions)
    completed_missions = 0
    failed_missions = 0
    
    for mission in goal_missions:
        mission_id = mission.get("mission_id")
        latest_status = _find_latest_status(mission_id, mission_records)
        if latest_status:
            status = latest_status.get("status")
            if status == "completed":
                completed_missions += 1
            elif status == "failed":
                failed_missions += 1
    
    completion_ratio = completed_missions / total_missions if total_missions > 0 else 0.0
    
    # Aggregate opportunities
    total_opportunities = 0
    for mission in goal_missions:
        mission_id = mission.get("mission_id")
        opp_summary = _opportunities_summary(mission_id, signals)
        total_opportunities += opp_summary.get("opportunities_created", 0)
    
    return {
        "goal_id": goal_id,
        "description": goal_data.get("description"),
        "status": goal_data.get("status"),
        "created_at": goal_data.get("created_at"),
        "programs_count": len(goal_programs),
        "missions_count": total_missions,
        "missions_completed": completed_missions,
        "missions_failed": failed_missions,
        "completion_ratio": completion_ratio,
        "total_opportunities": total_opportunities,
        "program_ids": [p.get("program_id") for p in goal_programs]
    }


def get_program_whiteboard(program_id: str) -> Dict[str, Any]:
    """
    Get program view with missions under program.
    
    Returns:
        Program view with missions summary and aggregated opportunities
    """
    programs = _read_jsonl(PROGRAMS_FILE)
    mission_records = _read_jsonl(MISSIONS_FILE)
    signals = _read_jsonl(SIGNALS_FILE)
    
    # Find program
    program_data = None
    for p in programs:
        if p.get("program_id") == program_id:
            program_data = p
            break
    
    if not program_data:
        return {
            "program_id": program_id,
            "error": "program_not_found"
        }
    
    # Find missions under this program
    program_missions = []
    for record in mission_records:
        if record.get("event_type") == "mission_created":
            mission = record.get("mission", {})
            if mission.get("program_id") == program_id:
                program_missions.append(mission)
    
    # Calculate mission stats
    mission_summaries = []
    total_opportunities = 0
    success_count = 0
    failure_count = 0
    
    for mission in program_missions:
        mission_id = mission.get("mission_id")
        latest_status = _find_latest_status(mission_id, mission_records)
        progress = _latest_progress(mission_id, signals)
        opp_summary = _opportunities_summary(mission_id, signals)
        goal_eval = _goal_evaluation(mission_id, signals)
        
        status = latest_status.get("status") if latest_status else mission.get("status", "active")
        
        if status == "completed":
            success_count += 1
        elif status == "failed":
            failure_count += 1
        
        total_opportunities += opp_summary.get("opportunities_created", 0)
        
        mission_summaries.append({
            "mission_id": mission_id,
            "objective": mission.get("objective", {}).get("description"),
            "status": status,
            "items_collected": (progress or {}).get("items_collected", 0),
            "opportunities_created": opp_summary.get("opportunities_created", 0),
            "goal_satisfied": (goal_eval or {}).get("goal_satisfied") if goal_eval else None,
            "created_at": mission.get("created_at"),
            "completed_at": latest_status.get("completed_at") if latest_status else None
        })
    
    return {
        "program_id": program_id,
        "goal_id": program_data.get("goal_id"),
        "description": program_data.get("description"),
        "status": program_data.get("status"),
        "created_at": program_data.get("created_at"),
        "missions_count": len(program_missions),
        "missions_succeeded": success_count,
        "missions_failed": failure_count,
        "total_opportunities": total_opportunities,
        "missions": mission_summaries
    }


def list_goals() -> List[Dict[str, Any]]:
    """List all goals with summary stats."""
    goals = _read_jsonl(GOALS_FILE)
    
    goal_summaries = []
    for goal in goals:
        goal_id = goal.get("goal_id")
        whiteboard = get_goal_whiteboard(goal_id)
        goal_summaries.append(whiteboard)
    
    return goal_summaries


def list_programs(goal_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all programs, optionally filtered by goal."""
    programs = _read_jsonl(PROGRAMS_FILE)
    
    if goal_id:
        programs = [p for p in programs if p.get("goal_id") == goal_id]
    
    program_summaries = []
    for program in programs:
        program_id = program.get("program_id")
        whiteboard = get_program_whiteboard(program_id)
        program_summaries.append(whiteboard)
    
    return program_summaries


def get_proposed_missions() -> List[Dict[str, Any]]:
    """
    Get all proposed missions awaiting approval.
    
    Returns:
        List of proposed missions with details
    """
    mission_records = _read_jsonl(MISSIONS_FILE)
    
    proposed = []
    for record in mission_records:
        if record.get('status') == 'proposed':
            objective = record.get('objective', {})
            scope = record.get('scope', {})
            metadata = record.get('metadata', {})
            
            proposed.append({
                'mission_id': record.get('mission_id'),
                'source': record.get('source', 'unknown'),
                'status': 'proposed',
                'objective_type': objective.get('type', 'unknown'),
                'objective_description': objective.get('description', ''),
                'target_count': objective.get('target_count'),
                'allowed_domains': scope.get('allowed_domains', []),
                'max_pages': scope.get('max_pages', 0),
                'max_duration_seconds': scope.get('max_duration_seconds', 0),
                'created_at': metadata.get('created_at'),
                'raw_chat_message': metadata.get('raw_chat_message'),
                'intent_keywords': metadata.get('intent_keywords', []),
                'awaiting_approval': metadata.get('awaiting_approval', True)
            })
    
    return proposed


def get_missions_by_thread(mission_thread_id: str) -> List[Dict[str, Any]]:
    """
    Get all missions in a thread, ordered chronologically.
    
    Args:
        mission_thread_id: The thread ID to filter by
        
    Returns:
        List of mission summaries in chronological order
    """
    mission_records = _read_jsonl(MISSIONS_FILE)
    
    # Find all missions with this thread_id
    thread_missions = []
    for record in mission_records:
        if record.get("event_type") == "mission_created":
            mission = record.get("mission", {})
            if mission.get("mission_thread_id") == mission_thread_id:
                thread_missions.append(mission)
    
    # Sort by created_at
    thread_missions.sort(key=lambda m: m.get("created_at", ""))
    
    # Get whiteboard for each mission
    mission_summaries = []
    for mission in thread_missions:
        mission_id = mission.get("mission_id")
        whiteboard = get_mission_whiteboard(mission_id)
        mission_summaries.append({
            "mission_id": mission_id,
            "objective": whiteboard.get("objective"),
            "status": whiteboard.get("status"),
            "start_time": whiteboard.get("start_time"),
            "end_time": whiteboard.get("end_time"),
            "items_collected": whiteboard.get("progress", {}).get("items_collected", 0),
            "goal_id": whiteboard.get("goal_id"),
            "program_id": whiteboard.get("program_id")
        })
    
    return mission_summaries


def get_signals_by_time_context(
    hour_of_day: Optional[int] = None,
    day_of_week: Optional[int] = None,
    min_elapsed_sec: Optional[int] = None,
    max_elapsed_sec: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Filter economic outcome signals by time context.
    
    Phase 4 Step 5: Economic Time Awareness
    
    Args:
        hour_of_day: Hour to filter (0-23), or None for all hours
        day_of_week: Day to filter (0=Monday, 6=Sunday), or None for all days
        min_elapsed_sec: Minimum elapsed seconds from mission start, or None
        max_elapsed_sec: Maximum elapsed seconds from mission start, or None
    
    Returns:
        List of economic signals (mission_completed, opportunity_normalized) with matching time context
    """
    signals = _read_jsonl(SIGNALS_FILE)
    
    # Filter for signals with time_context (mission_completed and opportunity_normalized)
    economic_signals = [
        s for s in signals
        if s.get("signal_type") in ["mission_completed", "opportunity_normalized"]
        and "time_context" in s
    ]
    
    # Apply time context filters
    filtered = []
    for signal in economic_signals:
        time_context = signal.get("time_context", {})
        
        # Hour filter
        if hour_of_day is not None:
            if time_context.get("hour_of_day") != hour_of_day:
                continue
        
        # Day filter
        if day_of_week is not None:
            if time_context.get("day_of_week") != day_of_week:
                continue
        
        # Elapsed time range filter
        elapsed_sec = time_context.get("elapsed_time_sec")
        if elapsed_sec is not None:
            if min_elapsed_sec is not None and elapsed_sec < min_elapsed_sec:
                continue
            if max_elapsed_sec is not None and elapsed_sec > max_elapsed_sec:
                continue
        
        filtered.append(signal)
    
    return filtered


def get_mission_time_context(mission_id: str) -> Dict[str, Any]:
    """
    Get all time context metadata for a mission's economic outcomes.
    
    Args:
        mission_id: Mission ID to analyze
    
    Returns:
        Dictionary with:
        - mission_completed: Time context for mission completion (if available)
        - opportunity_normalized: List of time contexts for opportunity normalizations
        - summary: Statistics about mission timing
    """
    signals = _read_jsonl(SIGNALS_FILE)
    
    mission_completed_time = None
    opportunity_times = []
    
    for signal in signals:
        if signal.get("mission_id") != mission_id:
            continue
        
        if signal.get("signal_type") == "mission_completed":
            mission_completed_time = signal.get("time_context")
        elif signal.get("signal_type") == "opportunity_normalized":
            if "time_context" in signal:
                opportunity_times.append({
                    "timestamp": signal.get("timestamp"),
                    "time_context": signal.get("time_context"),
                    "opportunities_created": signal.get("opportunities_created", 0)
                })
    
    # Calculate summary stats
    summary = {
        "total_time_context_signals": (1 if mission_completed_time else 0) + len(opportunity_times),
        "business_hours_completion": False,
        "avg_elapsed_sec": None
    }
    
    if mission_completed_time:
        hour = mission_completed_time.get("hour_of_day")
        day = mission_completed_time.get("day_of_week")
        if hour is not None and day is not None:
            summary["business_hours_completion"] = 0 <= day <= 4 and 9 <= hour <= 17
    
    if opportunity_times:
        elapsed_times = [
            t["time_context"].get("elapsed_time_sec")
            for t in opportunity_times
            if t["time_context"].get("elapsed_time_sec") is not None
        ]
        if elapsed_times:
            summary["avg_elapsed_sec"] = sum(elapsed_times) / len(elapsed_times)
    
    return {
        "mission_id": mission_id,
        "mission_completed": mission_completed_time,
        "opportunity_normalized": opportunity_times,
        "summary": summary
    }


def get_chat_observations(session_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get chat observation signals (all user interactions).
    
    Phase 5: Observability - Track all chat interactions and outcomes.
    
    Args:
        session_id: Optional - filter to specific session, otherwise return all
        
    Returns:
        List of chat observation signals with intent, message, outcome
    """
    signals = _read_jsonl(SIGNALS_FILE)
    
    chat_observations = [
        s for s in signals
        if s.get("signal_type") == "chat_observation"
    ]
    
    if session_id:
        chat_observations = [
            s for s in chat_observations
            if s.get("session_id") == session_id
        ]
    
    return chat_observations


def get_session_summary(session_id: str) -> Dict[str, Any]:
    """
    Get summary of all interactions in a session.
    
    Phase 5: Observability - Session-level chat summary.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Dictionary with interaction counts, types, outcomes
    """
    observations = get_chat_observations(session_id)
    
    if not observations:
        return {
            "session_id": session_id,
            "total_interactions": 0,
            "intents": {},
            "outcomes": {},
            "latest_observation": None
        }
    
    # Count intents
    intents = {}
    for obs in observations:
        intent_type = obs.get("intent_type", "unknown")
        intents[intent_type] = intents.get(intent_type, 0) + 1
    
    # Count outcomes
    outcomes = {}
    for obs in observations:
        outcome = obs.get("outcome", "unknown")
        outcomes[outcome] = outcomes.get(outcome, 0) + 1
    
    # Get latest
    latest = observations[-1] if observations else None
    
    return {
        "session_id": session_id,
        "total_interactions": len(observations),
        "intents": intents,
        "outcomes": outcomes,
        "latest_observation": latest
    }


def get_regrets(
    severity: Optional[str] = None,
    irreversible_only: bool = False
) -> List[Dict[str, Any]]:
    """
    Get all regrets from registry.
    
    Phase 4 Step 6: Regret Registry - Display irreversible failures
    
    Args:
        severity: Filter by severity (critical, high, medium, low)
        irreversible_only: Only return irreversible failures
    
    Returns:
        List of regret entries, sorted by severity (critical first)
    """
    if not REGRET_REGISTRY_FILE.exists():
        return []
    
    severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    regrets = []
    
    with open(REGRET_REGISTRY_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                regret = json.loads(line)
                
                # Apply filters
                if severity and regret.get("severity") != severity:
                    continue
                
                if irreversible_only and not regret.get("irreversible"):
                    continue
                
                regrets.append(regret)
            except json.JSONDecodeError:
                continue
    
    # Sort by severity (critical first)
    regrets.sort(key=lambda r: severity_order.get(r.get("severity"), 0), reverse=True)
    
    return regrets


def get_regrets_by_mission(mission_id: str) -> List[Dict[str, Any]]:
    """
    Get all regrets for a specific mission.
    
    Args:
        mission_id: Mission ID to filter by
    
    Returns:
        List of regrets for this mission, sorted by severity
    """
    if not REGRET_REGISTRY_FILE.exists():
        return []
    
    severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    regrets = []
    
    with open(REGRET_REGISTRY_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                regret = json.loads(line)
                if regret.get("mission_id") == mission_id:
                    regrets.append(regret)
            except json.JSONDecodeError:
                continue
    
    # Sort by severity
    regrets.sort(key=lambda r: severity_order.get(r.get("severity"), 0), reverse=True)
    
    return regrets


def get_regret_summary() -> Dict[str, Any]:
    """
    Get summary statistics of all regrets.
    
    Returns:
        Dictionary with summary stats, costs, and failure reason breakdown
    """
    regrets = get_regrets()
    
    if not regrets:
        return {
            "total_regrets": 0,
            "irreversible_count": 0,
            "critical_count": 0,
            "total_cost": {"time_lost": 0, "trust_impact": 0, "opportunities_lost": 0},
            "failure_reasons": {},
            "common_actions": {}
        }
    
    # Count by severity
    irreversible_count = sum(1 for r in regrets if r.get("irreversible"))
    critical_count = sum(1 for r in regrets if r.get("severity") == "critical")
    
    # Aggregate costs
    total_cost = {
        "time_lost": sum(r.get("estimated_cost", {}).get("time_lost", 0) for r in regrets),
        "trust_impact": sum(r.get("estimated_cost", {}).get("trust_impact", 0) for r in regrets),
        "opportunities_lost": sum(r.get("estimated_cost", {}).get("opportunities_lost", 0) for r in regrets)
    }
    
    # Count failure reasons
    failure_reasons = {}
    for r in regrets:
        reason = r.get("failure_reason", "unknown")
        failure_reasons[reason] = failure_reasons.get(reason, 0) + 1
    
    # Count action types
    common_actions = {}
    for r in regrets:
        action = r.get("action", "unknown")
        common_actions[action] = common_actions.get(action, 0) + 1
    
    return {
        "total_regrets": len(regrets),
        "irreversible_count": irreversible_count,
        "critical_count": critical_count,
        "total_cost": total_cost,
        "failure_reasons": failure_reasons,
        "common_actions": common_actions
    }



