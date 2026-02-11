"""
Artifact Views Module (Phase 4C)

Pure utility functions for read-only artifact interpretation, summarization, and comparison.

STRICT RULES:
- NO mission creation
- NO tool execution
- NO session context mutation
- NO inference beyond artifact data
- Deterministic patterns only
"""

from typing import Optional, List, Dict, Any
from datetime import datetime


def get_recent_artifacts(session_context, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Get recent execution artifacts from session context.
    
    READ-ONLY. Never mutates context.
    
    Args:
        session_context: SessionContext object
        limit: Max artifacts to return (None = all)
    
    Returns:
        List of execution artifacts in chronological order (oldest first)
    """
    artifacts = []
    
    if not session_context:
        return artifacts
    
    # Collect all artifacts from session (currently only last_execution_artifact)
    # In future versions, this could collect from artifact_history if tracked
    last_artifact = session_context.get_last_execution_artifact()
    if last_artifact:
        artifacts.append(dict(last_artifact))
    
    if limit and len(artifacts) > limit:
        return artifacts[-limit:]
    
    return artifacts


def summarize_artifact(artifact: Dict[str, Any]) -> Dict[str, Any]:
    """
    Summarize a single execution artifact.
    
    READ-ONLY. Returns structured summary without inference.
    
    Args:
        artifact: Execution artifact dict
    
    Returns:
        Summary dict with safe, deterministic fields
    """
    if not artifact:
        return {}
    
    summary = {
        "artifact_type": artifact.get("artifact_type"),
        "intent": artifact.get("objective_type") or "unknown",
        "source_url": artifact.get("source_url"),
        "final_url": artifact.get("final_url"),
        "timestamp": artifact.get("timestamp") or artifact.get("created_at"),
    }
    
    # Safely extract count
    extracted = artifact.get("extracted_data", {})
    if isinstance(extracted, dict):
        if "items" in extracted and isinstance(extracted["items"], list):
            summary["item_count"] = len(extracted["items"])
        elif "count" in extracted:
            summary["item_count"] = extracted["count"]
    
    # Include result summary if available
    summary["result_summary"] = artifact.get("result_summary")
    
    # Extract first N items (safe preview)
    if isinstance(extracted, dict) and "items" in extracted:
        items = extracted["items"]
        if isinstance(items, list) and items:
            summary["items_preview"] = items[:3]
    
    return {k: v for k, v in summary.items() if v is not None}


def summarize_artifact_set(artifacts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Summarize a set of execution artifacts.
    
    READ-ONLY. Combines summaries without inference.
    
    Args:
        artifacts: List of execution artifacts
    
    Returns:
        Combined summary dict
    """
    if not artifacts:
        return {"total_artifacts": 0}
    
    summaries = [summarize_artifact(art) for art in artifacts]
    
    combined = {
        "total_artifacts": len(artifacts),
        "artifacts": summaries,
    }
    
    # Count by intent
    intents = {}
    for summary in summaries:
        intent = summary.get("intent", "unknown")
        intents[intent] = intents.get(intent, 0) + 1
    combined["by_intent"] = intents if intents else None
    
    # Count by source
    sources = {}
    for summary in summaries:
        source = summary.get("source_url", "unknown")
        sources[source] = sources.get(source, 0) + 1
    combined["by_source"] = sources if sources else None
    
    # Total items
    total_items = sum(s.get("item_count", 0) for s in summaries)
    combined["total_items"] = total_items if total_items > 0 else None
    
    return {k: v for k, v in combined.items() if v is not None}


def compare_artifacts(a1: Dict[str, Any], a2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compare two execution artifacts.
    
    READ-ONLY. Returns factual differences without interpretation.
    
    Args:
        a1: First artifact
        a2: Second artifact
    
    Returns:
        Comparison dict with detected differences
    """
    if not a1 or not a2:
        return {"error": "Cannot compare: missing artifact"}
    
    s1 = summarize_artifact(a1)
    s2 = summarize_artifact(a2)
    
    comparison = {
        "artifact_1": s1,
        "artifact_2": s2,
        "differences": {},
    }
    
    # Compare intent
    if s1.get("intent") != s2.get("intent"):
        comparison["differences"]["intent_changed"] = {
            "from": s1.get("intent"),
            "to": s2.get("intent"),
        }
    
    # Compare source
    if s1.get("source_url") != s2.get("source_url"):
        comparison["differences"]["source_changed"] = {
            "from": s1.get("source_url"),
            "to": s2.get("source_url"),
        }
    
    # Compare item counts
    count1 = s1.get("item_count", 0)
    count2 = s2.get("item_count", 0)
    if count1 != count2:
        comparison["differences"]["item_count_delta"] = count2 - count1
    
    if not comparison["differences"]:
        comparison["differences"] = None
    
    return {k: v for k, v in comparison.items() if v is not None}


def format_artifact_summary(summary: Dict[str, Any]) -> str:
    """
    Format artifact summary for user display.
    
    READ-ONLY. Pure presentation, no logic.
    
    Args:
        summary: Artifact summary dict
    
    Returns:
        Formatted string for display
    """
    if not summary:
        return "No artifact data available."
    
    lines = []
    
    if "artifact_type" in summary:
        lines.append(f"**Type**: {summary['artifact_type']}")
    
    if "intent" in summary:
        lines.append(f"**Action**: {summary['intent']}")
    
    if "source_url" in summary:
        lines.append(f"**Source**: {summary['source_url']}")
    
    if "item_count" in summary:
        lines.append(f"**Items Found**: {summary['item_count']}")
    
    if "result_summary" in summary:
        lines.append(f"**Result**: {summary['result_summary']}")
    
    if "items_preview" in summary:
        items = summary["items_preview"]
        if items:
            items_text = ", ".join(str(i)[:30] for i in items[:3])
            lines.append(f"**Sample Items**: {items_text}")
    
    return "\n".join(lines) if lines else "No summary available."


def format_artifact_set_summary(combined: Dict[str, Any]) -> str:
    """
    Format artifact set summary for user display.
    
    READ-ONLY. Pure presentation.
    
    Args:
        combined: Combined artifact summary
    
    Returns:
        Formatted string for display
    """
    if not combined:
        return "No artifacts to summarize."
    
    lines = []
    total = combined.get("total_artifacts", 0)
    lines.append(f"**Total Artifacts**: {total}")
    
    if "total_items" in combined and combined["total_items"] is not None:
        lines.append(f"**Total Items**: {combined['total_items']}")
    
    if "by_intent" in combined and combined["by_intent"]:
        intent_list = ", ".join(
            f"{intent} ({count})"
            for intent, count in combined["by_intent"].items()
        )
        lines.append(f"**By Intent**: {intent_list}")
    
    if "by_source" in combined and combined["by_source"]:
        source_list = ", ".join(
            f"{source} ({count})"
            for source, count in combined["by_source"].items()
        )
        lines.append(f"**By Source**: {source_list}")
    
    return "\n".join(lines)


def format_comparison(comparison: Dict[str, Any]) -> str:
    """
    Format artifact comparison for user display.
    
    READ-ONLY. Pure presentation.
    
    Args:
        comparison: Comparison dict
    
    Returns:
        Formatted string for display
    """
    if "error" in comparison:
        return comparison["error"]
    
    lines = []
    
    diffs = comparison.get("differences")
    if not diffs:
        lines.append("**No differences detected** — artifacts are similar.")
        return "\n".join(lines)
    
    lines.append("**Changes detected**:")
    
    if "intent_changed" in diffs:
        change = diffs["intent_changed"]
        lines.append(f"• **Intent**: {change['from']} → {change['to']}")
    
    if "source_changed" in diffs:
        change = diffs["source_changed"]
        lines.append(f"• **Source**: {change['from']} → {change['to']}")
    
    if "item_count_delta" in diffs:
        delta = diffs["item_count_delta"]
        sign = "+" if delta > 0 else ""
        lines.append(f"• **Items**: {sign}{delta}")
    
    return "\n".join(lines)

