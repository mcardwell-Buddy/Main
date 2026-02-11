#!/usr/bin/env python3
"""
Synthetic Usage Harness for Buddy (Observation Only)

Constraints enforced:
- Standalone file (no modifications to production code)
- Uses public API /reasoning/execute (same as UI)
- No config changes, no autonomy escalation
- No writes to long-term memory (tags synthetic_test, persist: false)
- Halts immediately on invariant violation
"""

import argparse
import csv
import json
import random
import sys
import time
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple


DEFAULT_BASE_URL = "http://127.0.0.1:8000"
DEFAULT_RUNS = 500
MIN_RUNS = 500
MAX_RUNS = 1000


@dataclass
class Scenario:
    category: str
    goal: str


def build_scenarios() -> Dict[str, List[str]]:
    return {
        "atomic": [
            "Inspect the current page and list all buttons.",
            "Find the login element on the page.",
            "Summarize the forms detected on the current page.",
            "Identify the primary call-to-action on this page.",
            "List all input fields and their types.",
        ],
        "ambiguous": [
            "Help me get this done.",
            "Make this work for me.",
            "I need help but I'm not sure what to do.",
            "Get me set up with the right steps.",
            "Fix whatever is wrong here.",
        ],
        "failure-injected": [
            "Use a nonexistent tool to solve this.",
            "Click a button that does not exist on the page.",
            "Find an element that cannot be found.",
            "Complete a task with missing information.",
            "Attempt an impossible action without context.",
        ],
        "cross-domain": [
            "Analyze this Python code for bugs and propose fixes.",
            "Summarize this JSON dataset and compute averages.",
            "Draft a short marketing email for a new product.",
            "Design a database schema for a hiring platform.",
            "Create a project plan with milestones and risks.",
        ],
    }


def choose_scenarios(total_runs: int, seed: int) -> List[Scenario]:
    random.seed(seed)
    scenarios_by_category = build_scenarios()
    categories = list(scenarios_by_category.keys())

    selected: List[Scenario] = []
    for _ in range(total_runs):
        category = random.choice(categories)
        goal = random.choice(scenarios_by_category[category])
        selected.append(Scenario(category=category, goal=goal))
    return selected


def post_json(url: str, payload: Dict[str, Any], timeout: int = 120) -> Dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        body = response.read().decode("utf-8")
        return json.loads(body)


def invariant_violation(message: str, run_index: int, outdir: str, records: List[Dict[str, Any]]) -> None:
    timestamp = int(time.time())
    partial_path = f"{outdir}/synthetic_partial_{timestamp}.json"
    try:
        with open(partial_path, "w", encoding="utf-8") as f:
            json.dump({"error": message, "run_index": run_index, "records": records}, f, indent=2)
    finally:
        print(f"INVARIANT VIOLATION: {message}")
        print(f"Partial results saved to: {partial_path}")
        sys.exit(2)


def validate_response(resp: Dict[str, Any], run_index: int, outdir: str, records: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not isinstance(resp, dict) or "success" not in resp:
        invariant_violation("Missing or invalid 'success' field in response", run_index, outdir, records)
    # success can be True or False - both are valid responses
    success = resp.get("success")
    if not isinstance(success, bool):
        invariant_violation("'success' field is not a boolean", run_index, outdir, records)
    
    result = resp.get("result")
    if not isinstance(result, dict):
        invariant_violation("Missing or invalid 'result' field", run_index, outdir, records)

    tool_results = result.get("tool_results")
    tools_used = result.get("tools_used")
    confidence = result.get("confidence")

    if not isinstance(tool_results, list):
        invariant_violation("Missing or invalid 'tool_results' list", run_index, outdir, records)
    if not isinstance(tools_used, list):
        invariant_violation("Missing or invalid 'tools_used' list", run_index, outdir, records)
    if not isinstance(confidence, (int, float)) or confidence < 0.0 or confidence > 1.0:
        invariant_violation("'confidence' is missing or out of bounds", run_index, outdir, records)
    if len(tool_results) != len(tools_used):
        invariant_violation("Mismatch between tool_results and tools_used lengths", run_index, outdir, records)

    for tr in tool_results:
        if not isinstance(tr, dict) or "tool_name" not in tr or "success" not in tr:
            invariant_violation("Invalid tool_result entry structure", run_index, outdir, records)

    return result


def summarize_records(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(records)
    success_runs = sum(1 for r in records if r["run_success"])
    avg_latency = sum(r["latency_ms"] for r in records) / total if total else 0
    avg_conf_delta = sum(r["confidence_delta"] for r in records) / total if total else 0

    by_category: Dict[str, Dict[str, Any]] = {}
    for r in records:
        cat = r["category"]
        by_category.setdefault(cat, {"count": 0, "success": 0, "avg_latency_ms": 0.0, "avg_conf_delta": 0.0})
        by_category[cat]["count"] += 1
        by_category[cat]["success"] += 1 if r["run_success"] else 0
        by_category[cat]["avg_latency_ms"] += r["latency_ms"]
        by_category[cat]["avg_conf_delta"] += r["confidence_delta"]

    for cat, stats in by_category.items():
        count = stats["count"]
        stats["avg_latency_ms"] = stats["avg_latency_ms"] / count if count else 0
        stats["avg_conf_delta"] = stats["avg_conf_delta"] / count if count else 0
        stats["success_rate"] = stats["success"] / count if count else 0

    return {
        "tag": "Synthetic Observation",
        "total_runs": total,
        "success_runs": success_runs,
        "success_rate": success_runs / total if total else 0,
        "avg_latency_ms": avg_latency,
        "avg_confidence_delta": avg_conf_delta,
        "by_category": by_category,
    }


def build_failure_heatmap(records: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
    heatmap: Dict[str, Dict[str, int]] = {}
    for r in records:
        cat = r["category"]
        heatmap.setdefault(cat, {})
        for tr in r["tool_results"]:
            tool_name = tr.get("tool_name", "unknown")
            if not tr.get("success", False):
                heatmap[cat][tool_name] = heatmap[cat].get(tool_name, 0) + 1
    return heatmap


def build_confidence_drift(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    deltas = [r["confidence_delta"] for r in records]
    by_category: Dict[str, List[float]] = {}
    for r in records:
        by_category.setdefault(r["category"], []).append(r["confidence_delta"])

    return {
        "tag": "Synthetic Observation",
        "overall": {
            "mean": sum(deltas) / len(deltas) if deltas else 0.0,
            "min": min(deltas) if deltas else 0.0,
            "max": max(deltas) if deltas else 0.0,
        },
        "by_category": {
            cat: {
                "mean": sum(vals) / len(vals) if vals else 0.0,
                "min": min(vals) if vals else 0.0,
                "max": max(vals) if vals else 0.0,
            }
            for cat, vals in by_category.items()
        },
        "series": [
            {"run_index": r["run_index"], "category": r["category"], "confidence_delta": r["confidence_delta"]}
            for r in records
        ],
    }


def write_outputs(outdir: str, records: List[Dict[str, Any]]) -> Tuple[str, str, str, str]:
    summary = summarize_records(records)
    heatmap = build_failure_heatmap(records)
    drift = build_confidence_drift(records)

    summary_json_path = f"{outdir}/synthetic_summary.json"
    summary_csv_path = f"{outdir}/synthetic_summary.csv"
    heatmap_path = f"{outdir}/synthetic_failure_heatmap.json"
    drift_path = f"{outdir}/synthetic_confidence_drift.json"

    with open(summary_json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    with open(summary_csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "tag",
            "total_runs",
            "success_runs",
            "success_rate",
            "avg_latency_ms",
            "avg_confidence_delta",
        ])
        writer.writerow([
            summary["tag"],
            summary["total_runs"],
            summary["success_runs"],
            summary["success_rate"],
            summary["avg_latency_ms"],
            summary["avg_confidence_delta"],
        ])

    with open(heatmap_path, "w", encoding="utf-8") as f:
        json.dump({"tag": "Synthetic Observation", "heatmap": heatmap}, f, indent=2)

    with open(drift_path, "w", encoding="utf-8") as f:
        json.dump(drift, f, indent=2)

    return summary_json_path, summary_csv_path, heatmap_path, drift_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Synthetic Usage Harness (Observation Only)")
    parser.add_argument("--runs", type=int, default=DEFAULT_RUNS, help="Number of scenarios to execute (500-1000)")
    parser.add_argument("--base-url", type=str, default=DEFAULT_BASE_URL, help="Base URL for Buddy server")
    parser.add_argument("--outdir", type=str, default="synthetic_reports", help="Output directory for reports")
    parser.add_argument("--seed", type=int, default=1337, help="Random seed for scenario selection")
    args = parser.parse_args()

    if args.runs < MIN_RUNS or args.runs > MAX_RUNS:
        print(f"Runs must be between {MIN_RUNS} and {MAX_RUNS}.")
        return 1

    scenarios = choose_scenarios(args.runs, args.seed)

    # Prepare output directory
    try:
        import os
        os.makedirs(args.outdir, exist_ok=True)
    except Exception as exc:
        print(f"Failed to create output directory: {exc}")
        return 1

    records: List[Dict[str, Any]] = []

    for idx, scenario in enumerate(scenarios, start=1):
        payload = {
            "goal": scenario.goal,
            "context": {
                "synthetic_test": True,
                "persist": False,
                "tag": "Synthetic Observation",
            },
        }

        start = time.perf_counter()
        try:
            resp = post_json(f"{args.base_url}/reasoning/execute", payload)
        except Exception as exc:
            invariant_violation(f"HTTP error during request: {exc}", idx, args.outdir, records)
            return 2
        latency_ms = (time.perf_counter() - start) * 1000.0

        result = validate_response(resp, idx, args.outdir, records)

        tool_results = result.get("tool_results", [])
        tools_used = result.get("tools_used", [])
        confidence = result.get("confidence", 0.0)
        confidence_delta = confidence - 0.0  # baseline from reset

        run_success = True
        if tool_results:
            run_success = all(tr.get("success", False) for tr in tool_results)

        memory_save_decision = bool(result.get("key_findings") or result.get("recommendations"))

        record = {
            "tag": "Synthetic Observation",
            "synthetic_test": True,
            "persist": False,
            "run_index": idx,
            "category": scenario.category,
            "goal": scenario.goal,
            "tool_selected": tools_used[-1] if tools_used else "none",
            "tools_used": tools_used,
            "tool_results": tool_results,
            "run_success": run_success,
            "latency_ms": latency_ms,
            "confidence": confidence,
            "confidence_delta": confidence_delta,
            "memory_save_decision": memory_save_decision,
        }
        records.append(record)

        if idx % 50 == 0:
            print(f"Completed {idx}/{args.runs} synthetic runs...")

    summary_json_path, summary_csv_path, heatmap_path, drift_path = write_outputs(args.outdir, records)

    print("Synthetic Observation complete.")
    print(f"Summary JSON: {summary_json_path}")
    print(f"Summary CSV: {summary_csv_path}")
    print(f"Failure heatmap: {heatmap_path}")
    print(f"Confidence drift: {drift_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

