"""
Whiteboard Metrics Aggregator

Aggregates structured data from core logs and stores for the whiteboard UI.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from Back_End.budget_tracker import get_budget_tracker
from Back_End.conversation.session_store import get_conversation_store
from Back_End.mission_store import get_mission_store


API_USAGE_LOG = Path("outputs/phase25/api_usage.jsonl")
EXTERNAL_API_LOG = Path("outputs/phase25/external_api_usage.jsonl")
ARTIFACTS_LOG = Path("outputs/phase25/artifacts.jsonl")
REVENUE_SIGNALS_LOG = Path("outputs/phase25/revenue_signals.jsonl")
BUDGETS_LOG = Path("data/budgets.jsonl")


@dataclass
class TimeRange:
    start: datetime
    end: datetime


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _parse_timestamp(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(float(value), tz=timezone.utc)
        except Exception:
            return None
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return datetime.fromisoformat(text.replace("Z", "+00:00"))
        except Exception:
            return None
    return None


def _load_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    records: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def _filter_by_range(records: List[Dict[str, Any]], key: str, time_range: TimeRange) -> List[Dict[str, Any]]:
    filtered: List[Dict[str, Any]] = []
    for record in records:
        ts = _parse_timestamp(record.get(key))
        if not ts:
            continue
        if time_range.start <= ts <= time_range.end:
            filtered.append(record)
    return filtered


def _percentile(values: List[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = max(0, min(len(ordered) - 1, int(round((percentile / 100) * (len(ordered) - 1)))))
    return ordered[rank]


def _build_time_range(days: int) -> TimeRange:
    end = _now_utc()
    start = end - timedelta(days=max(days, 1))
    return TimeRange(start=start, end=end)


def log_api_usage(record: Dict[str, Any]) -> None:
    API_USAGE_LOG.parent.mkdir(parents=True, exist_ok=True)
    with API_USAGE_LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")


def log_external_api_usage(company: str, request_type: str, duration_ms: float = 0.0, cost_usd: float = 0.0) -> None:
    """
    Log usage of external APIs (OpenAI, SerpAPI, GoHighLevel, MSGraph, etc.)
    
    Args:
        company: Company name (e.g., "OpenAI", "SerpAPI", "GoHighLevel")
        request_type: Type of request (e.g., "chat_completion", "search", "contact_create")
        duration_ms: Request duration in milliseconds
        cost_usd: Cost in USD for the request
    """
    EXTERNAL_API_LOG.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": _now_utc().isoformat(),
        "company": company,
        "request_type": request_type,
        "duration_ms": duration_ms,
        "cost_usd": cost_usd,
    }
    with EXTERNAL_API_LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")


def _ensure_log_exists():
    """Ensure log directories exist"""
    API_USAGE_LOG.parent.mkdir(parents=True, exist_ok=True)
    EXTERNAL_API_LOG.parent.mkdir(parents=True, exist_ok=True)


# Initialize log directories on module load
_ensure_log_exists()


def collect_api_usage(days: int) -> Dict[str, Any]:
    time_range = _build_time_range(days)
    records = _filter_by_range(_load_jsonl(API_USAGE_LOG), "timestamp", time_range)

    total_requests = len(records)
    by_endpoint: Dict[str, Dict[str, Any]] = {}
    all_durations = []
    
    for record in records:
        path = record.get("path") or "unknown"
        method = record.get("method") or "GET"
        duration = float(record.get("duration_ms") or 0.0)
        entry = by_endpoint.setdefault(path, {
            "path": path,
            "count": 0,
            "methods": {},
            "durations": [],
        })
        entry["count"] += 1
        entry["methods"][method] = entry["methods"].get(method, 0) + 1
        entry["durations"].append(duration)
        all_durations.append(duration)

    # Calculate overall average latency
    overall_avg_latency = round(sum(all_durations) / len(all_durations), 2) if all_durations else 0.0

    # Build endpoints array
    endpoints = []
    summary = {}
    
    for entry in by_endpoint.values():
        durations = entry["durations"]
        avg_latency = round(sum(durations) / len(durations), 2) if durations else 0.0
        endpoint_info = {
            "path": entry["path"],
            "count": entry["count"],
            "methods": entry["methods"],
            "avg_latency_ms": avg_latency,
        }
        endpoints.append(endpoint_info)
        summary[entry["path"]] = {
            "count": entry["count"],
            "avg_latency_ms": avg_latency,
            "methods": entry["methods"],
        }

    # Sort by request count (descending) to show most-slammed endpoints first
    endpoints.sort(key=lambda e: e["count"], reverse=True)
    
    return {
        "total_requests": total_requests,
        "avg_latency_ms": overall_avg_latency,
        "summary": summary,
        "by_endpoint": endpoints,
    }


def collect_external_api_usage(days: int) -> Dict[str, Any]:
    """
    Collect usage metrics for external APIs (OpenAI, SerpAPI, GoHighLevel, MSGraph, etc.)
    Groups by company name with request type breakdown
    """
    time_range = _build_time_range(days)
    records = _filter_by_range(_load_jsonl(EXTERNAL_API_LOG), "timestamp", time_range)
    
    total_calls = len(records)
    by_company: Dict[str, Dict[str, Any]] = {}
    all_durations = []
    
    for record in records:
        company = record.get("company") or "Unknown"
        request_type = record.get("request_type") or "unknown"
        duration = float(record.get("duration_ms") or 0.0)
        cost = float(record.get("cost_usd") or 0.0)
        
        if company not in by_company:
            by_company[company] = {
                "company": company,
                "total_calls": 0,
                "total_cost": 0.0,
                "durations": [],
                "request_types": {},
            }
        
        company_data = by_company[company]
        company_data["total_calls"] += 1
        company_data["total_cost"] += cost
        company_data["durations"].append(duration)
        all_durations.append(duration)
        
        if request_type not in company_data["request_types"]:
            company_data["request_types"][request_type] = {
                "type": request_type,
                "count": 0,
                "cost": 0.0,
                "durations": [],
            }
        
        type_data = company_data["request_types"][request_type]
        type_data["count"] += 1
        type_data["cost"] += cost
        type_data["durations"].append(duration)
    
    # Calculate statistics for each company
    companies = []
    for company_data in by_company.values():
        durations = company_data["durations"]
        avg_latency = round(sum(durations) / len(durations), 2) if durations else 0.0
        
        # Calculate stats for each request type
        request_types = []
        for type_data in company_data["request_types"].values():
            type_durations = type_data["durations"]
            type_avg_latency = round(sum(type_durations) / len(type_durations), 2) if type_durations else 0.0
            request_types.append({
                "type": type_data["type"],
                "count": type_data["count"],
                "cost": round(type_data["cost"], 4),
                "avg_latency_ms": type_avg_latency,
            })
        
        companies.append({
            "company": company_data["company"],
            "total_calls": company_data["total_calls"],
            "total_cost": round(company_data["total_cost"], 4),
            "avg_latency_ms": avg_latency,
            "request_types": sorted(request_types, key=lambda x: x["count"], reverse=True),
        })
    
    # Sort by total calls (most used first)
    companies.sort(key=lambda x: x["total_calls"], reverse=True)
    
    overall_avg_latency = round(sum(all_durations) / len(all_durations), 2) if all_durations else 0.0
    
    return {
        "total_calls": total_calls,
        "avg_latency_ms": overall_avg_latency,
        "by_company": companies,
    }


def collect_response_times(days: int) -> Dict[str, Any]:
    time_range = _build_time_range(days)
    records = _filter_by_range(_load_jsonl(API_USAGE_LOG), "timestamp", time_range)
    durations = [float(r.get("duration_ms") or 0.0) for r in records if r.get("duration_ms") is not None]
    avg_ms = round(sum(durations) / len(durations), 2) if durations else 0.0
    return {
        "avg_ms": avg_ms,
        "p50_ms": round(_percentile(durations, 50), 2),
        "p95_ms": round(_percentile(durations, 95), 2),
        "count": len(durations),
    }


def collect_costing(days: int) -> Dict[str, Any]:
    time_range = _build_time_range(days)
    records = _filter_by_range(_load_jsonl(BUDGETS_LOG), "timestamp", time_range)

    serpapi_searches = 0
    openai_cost = 0.0
    firestore_cost = 0.0

    for record in records:
        event_type = record.get("event_type")
        if event_type == "serpapi_usage":
            serpapi_searches += int(record.get("searches_used", 0) or 0)
        elif event_type == "openai_usage":
            openai_cost += float(record.get("cost_usd", 0.0) or 0.0)
        elif event_type == "firestore_usage":
            firestore_cost += float(record.get("cost_usd", 0.0) or 0.0)

    budget_tracker = get_budget_tracker()
    serpapi_budget = budget_tracker.get_serpapi_budget()
    openai_budget = budget_tracker.get_openai_budget()
    firestore_budget = budget_tracker.get_firestore_budget()

    return {
        "accounts": {
            "serpapi_tier": serpapi_budget.tier,
            "billing_period_end": serpapi_budget.billing_period_end,
        },
        "api": {
            "serpapi_searches": serpapi_searches,
            "openai_cost_usd": round(openai_cost, 4),
        },
        "storage": {
            "firestore_cost_usd": round(firestore_cost, 4),
        },
        "cloud": {
            "estimated_cost_usd": 0.0,
            "source": "unavailable",
        },
        "budgets": {
            "serpapi": serpapi_budget.to_dict(),
            "openai": openai_budget.to_dict(),
            "firestore": firestore_budget.to_dict(),
        },
    }


def collect_income(days: int) -> Dict[str, Any]:
    time_range = _build_time_range(days)
    records = _filter_by_range(_load_jsonl(REVENUE_SIGNALS_LOG), "timestamp", time_range)

    gigs_recommended = 0
    gigs_hired = 0
    invoices_received = 0

    for record in records:
        signal = (record.get("signal_type") or record.get("event_type") or "").lower()
        if "gig_recommended" in signal or "opportunity_recommended" in signal:
            gigs_recommended += 1
        elif "gig_hired" in signal or "opportunity_hired" in signal:
            gigs_hired += 1
        elif "invoice_received" in signal or "invoice_paid" in signal:
            invoices_received += 1

    return {
        "gigs_recommended": gigs_recommended,
        "gigs_hired": gigs_hired,
        "invoices_received": invoices_received,
        "source": "revenue_signals" if records else "no_records",
    }


def collect_tool_confidence(days: int) -> Dict[str, Any]:
    time_range = _build_time_range(days)
    store = get_mission_store()
    events = store.get_all_events()

    tool_events: Dict[str, List[float]] = {}
    timestamped: Dict[str, List[Tuple[datetime, float]]] = {}
    total_events = 0

    for event in events:
        if event.event_type != "mission_executed":
            continue
        ts = _parse_timestamp(event.timestamp)
        if not ts or not (time_range.start <= ts <= time_range.end):
            continue
        tool_name = event.tool_used or "unknown"
        confidence = float(event.tool_confidence or 0.0)
        tool_events.setdefault(tool_name, []).append(confidence)
        timestamped.setdefault(tool_name, []).append((ts, confidence))
        total_events += 1

    rows = []
    for tool_name, confidences in tool_events.items():
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        variation = max(confidences) - min(confidences) if len(confidences) > 1 else 0.0
        selection_pct = (len(confidences) / total_events * 100.0) if total_events else 0.0
        rows.append({
            "tool_name": tool_name,
            "confidence_pct": round(avg_confidence * 100, 2),
            "selection_pct": round(selection_pct, 2),
            "confidence_variation": round(variation * 100, 2),
        })

    rows.sort(key=lambda r: r["selection_pct"], reverse=True)
    return {
        "rows": rows,
        "total_executions": total_events,
    }


def collect_session_stats() -> Dict[str, Any]:
    store = get_conversation_store()
    sessions = store.list_sessions()
    session_rows = []
    for session in sessions:
        sent = sum(1 for m in session.messages if m.role == "user")
        received = sum(1 for m in session.messages if m.role == "assistant")
        session_rows.append({
            "session_id": session.session_id,
            "source": session.source,
            "messages_sent": sent,
            "messages_received": received,
            "total_messages": len(session.messages),
            "last_message_at": session.messages[-1].timestamp if session.messages else None,
            "title": session.title,
            "archived": session.archived,
        })
    return {
        "sessions": session_rows,
        "total_sessions": len(session_rows),
    }


def collect_artifacts(days: int) -> Dict[str, Any]:
    time_range = _build_time_range(days)
    records = _filter_by_range(_load_jsonl(ARTIFACTS_LOG), "timestamp", time_range)

    counts: Dict[str, int] = {}
    for record in records:
        artifact_type = record.get("artifact_type") or "unknown"
        counts[artifact_type] = counts.get(artifact_type, 0) + 1

    return {
        "total": len(records),
        "by_type": counts,
    }


def collect_whiteboard_summary(days: int) -> Dict[str, Any]:
    time_range = _build_time_range(days)
    return {
        "range": {
            "days": days,
            "start": time_range.start.isoformat(),
            "end": time_range.end.isoformat(),
        },
        "api_usage": collect_api_usage(days),
        "external_api_usage": collect_external_api_usage(days),
        "costing": collect_costing(days),
        "income": collect_income(days),
        "tool_confidence": collect_tool_confidence(days),
        "response_times": collect_response_times(days),
        "session_stats": collect_session_stats(),
        "artifacts": collect_artifacts(days),
        "data_sources": {
            "api_usage_log": str(API_USAGE_LOG),
            "external_api_log": str(EXTERNAL_API_LOG),
            "artifacts_log": str(ARTIFACTS_LOG),
            "budgets_log": str(BUDGETS_LOG),
            "revenue_signals_log": str(REVENUE_SIGNALS_LOG),
            "mission_store": "firebase",
            "conversation_store": "firebase",
        },
    }


def _collect_agents_data() -> Dict[str, Any]:
    """Collect agent status data from Firebase agents collection."""
    try:
        import firebase_admin
        from firebase_admin import firestore
        from Back_End.config import Config
        
        if not Config.FIREBASE_ENABLED:
            return {"agents": []}
        
        db = firestore.client()
        agents_ref = db.collection('agents')
        docs = agents_ref.stream()
        
        agents_list = []
        for doc in docs:
            agent_data = doc.to_dict()
            agent_id = doc.id
            
            # Get heartbeat data
            heartbeat_ref = agents_ref.document(agent_id).collection('heartbeat').document('current')
            heartbeat_doc = heartbeat_ref.get()
            
            if heartbeat_doc.exists:
                heartbeat = heartbeat_doc.to_dict()
                agents_list.append({
                    "agent_id": agent_id,
                    "tasks_completed_today": heartbeat.get('tasks_processed', 0),
                    "avg_response_time": heartbeat.get('avg_response_time', 0.0),
                    "success_rate": heartbeat.get('success_rate', 0.0),
                    "status": heartbeat.get('status', 'OFFLINE')
                })
        
        return {"agents": agents_list}
    except Exception as e:
        import logging
        logging.error(f"Error collecting agents data: {e}")
        return {"agents": []}


def _collect_capacity_forecast() -> Dict[str, Any]:
    """Collect capacity forecast data."""
    try:
        import firebase_admin
        from firebase_admin import firestore
        from Back_End.config import Config
        
        if not Config.FIREBASE_ENABLED:
            return {"forecasts": []}
        
        db = firestore.client()
        agents_ref = db.collection('agents')
        docs = agents_ref.stream()
        
        forecasts = []
        for doc in docs:
            agent_id = doc.id
            heartbeat_ref = agents_ref.document(agent_id).collection('heartbeat').document('current')
            heartbeat_doc = heartbeat_ref.get()
            
            if heartbeat_doc.exists:
                heartbeat = heartbeat_doc.to_dict()
                tasks_processed = heartbeat.get('tasks_processed', 0)
                success_rate = heartbeat.get('success_rate', 0.0)
                
                # Simple capacity calculation: 100% - (current load estimate)
                # Assume average agent can handle 100 tasks/day
                current_load = min(100, (tasks_processed / 100.0) * 100)
                available_capacity = max(0, 100 - current_load)
                
                forecasts.append({
                    "agent_id": agent_id,
                    "estimated_available_capacity": int(available_capacity),
                    "bottleneck_tools": []  # Can be enhanced with actual bottleneck detection
                })
        
        return {"forecasts": forecasts}
    except Exception as e:
        import logging
        logging.error(f"Error collecting capacity forecast: {e}")
        return {"forecasts": []}


def _collect_task_pipeline() -> Dict[str, Any]:
    """Collect task pipeline data from missions (last 24 hours)."""
    try:
        store = get_mission_store()
        time_range = _build_time_range(1)  # Last 24 hours
        
        all_events = store.get_all_events()
        
        total_tasks = 0
        successful_tasks = 0
        failed_tasks = 0
        
        for event in all_events:
            if event.event_type != "mission_executed":
                continue
            
            ts = _parse_timestamp(event.timestamp)
            if not ts or not (time_range.start <= ts <= time_range.end):
                continue
            
            total_tasks += 1
            if event.status == "completed":
                successful_tasks += 1
            elif event.status == "failed":
                failed_tasks += 1
        
        success_rate = (successful_tasks / total_tasks) if total_tasks > 0 else 0.0
        
        return {
            "last_24_hours": {
                "total_tasks": total_tasks,
                "success_rate": success_rate,
                "successful_tasks": successful_tasks,
                "failed_tasks": failed_tasks
            }
        }
    except Exception as e:
        import logging
        logging.error(f"Error collecting task pipeline: {e}")
        return {
            "last_24_hours": {
                "total_tasks": 0,
                "success_rate": 0.0,
                "successful_tasks": 0,
                "failed_tasks": 0
            }
        }


def _collect_costs_and_usage() -> Dict[str, Any]:
    """Collect costs and API usage data."""
    try:
        costing = collect_costing(1)  # Last 24 hours
        api_usage_internal = collect_api_usage(1)
        external_usage = collect_external_api_usage(1)
        
        # Calculate total tasks and tokens from internal API usage
        total_tasks_24h = api_usage_internal.get('total_requests', 0)
        total_tokens_24h = 0
        api_calls_24h = external_usage.get('total_calls', 0)
        
        # Estimate tokens from external API usage (if available)
        for company_data in external_usage.get('by_company', []):
            # Rough estimate: 1 API call = ~500 tokens average
            total_tokens_24h += company_data.get('total_calls', 0) * 500
        
        return {
            "costing": {
                "execution_costs_24h": costing.get('total_cost', 0.0),
                "storage_costs_daily": 0.000001,  # Placeholder - can be calculated from Firebase usage
                "total_daily_cost": costing.get('total_cost', 0.0) + 0.000001
            },
            "api_usage": {
                "total_tasks_24h": total_tasks_24h,
                "total_tokens_24h": total_tokens_24h,
                "api_calls_24h": api_calls_24h
            }
        }
    except Exception as e:
        import logging
        logging.error(f"Error collecting costs and usage: {e}")
        return {
            "costing": {
                "execution_costs_24h": 0.0,
                "storage_costs_daily": 0.0,
                "total_daily_cost": 0.0
            },
            "api_usage": {
                "total_tasks_24h": 0,
                "total_tokens_24h": 0,
                "api_calls_24h": 0
            }
        }


def _collect_learning_data() -> Dict[str, Any]:
    """Collect learning data (tool confidence)."""
    try:
        tool_conf = collect_tool_confidence(7)  # Last 7 days for better data
        
        rows = tool_conf.get('rows', [])
        
        # Categorize by confidence level
        high_confidence = 0
        medium_confidence = 0
        low_confidence = 0
        
        tool_profiles = []
        
        for row in rows:
            conf_pct = row.get('confidence_pct', 0)
            tool_name = row.get('tool_name', 'unknown')
            
            # Calculate confidence level
            if conf_pct >= 70:
                level = "High"
                high_confidence += 1
            elif conf_pct >= 40:
                level = "Medium"
                medium_confidence += 1
            else:
                level = "Low"
                low_confidence += 1
            
            # Estimate executions and success rate from selection percentage
            total_execs = tool_conf.get('total_executions', 0)
            selection_pct = row.get('selection_pct', 0)
            tool_executions = int((selection_pct / 100) * total_execs) if total_execs > 0 else 0
            
            tool_profiles.append({
                "tool_name": tool_name,
                "total_executions": tool_executions,
                "success_rate": conf_pct / 100.0,  # Use confidence as proxy for success rate
                "confidence_level": level
            })
        
        return {
            "confidence_distribution": {
                "high_confidence": high_confidence,
                "medium_confidence": medium_confidence,
                "low_confidence": low_confidence
            },
            "tool_profiles": tool_profiles
        }
    except Exception as e:
        import logging
        logging.error(f"Error collecting learning data: {e}")
        return {
            "confidence_distribution": {
                "high_confidence": 0,
                "medium_confidence": 0,
                "low_confidence": 0
            },
            "tool_profiles": []
        }


def collect_analytics_dashboard() -> Dict[str, Any]:
    """Collect all analytics data for Phase 8 dashboard."""
    return {
        "agents": _collect_agents_data(),
        "capacity": _collect_capacity_forecast(),
        "pipeline": _collect_task_pipeline(),
        "costs": _collect_costs_and_usage(),
        "learning": _collect_learning_data()
    }
