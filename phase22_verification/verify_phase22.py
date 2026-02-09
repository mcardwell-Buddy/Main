"""
Phase 22 Verification Script

Runs dry-run and live executions, validates outputs, computes metrics,
checks anomalies, and generates verification reports.

Exit Codes:
    0 - Success
    1 - Verification failure
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from buddy_phase22_harness import Phase22Harness


REQUIRED_METRICS = {
    "success_rate": 0.90,
    "throughput": 35.0,
    "agent_utilization": 0.70,
    "confidence_trajectory": 0.95,
    "schedule_adherence": 0.95,
    "optimization_efficiency": 0.90,
}

ANOMALY_TYPES = {
    "high_failure",
    "schedule_drift",
    "confidence_drop",
    "excessive_retries",
    "optimization_failure",
}


def run_harness(base_dir: Path, dry_run: bool, waves: List[int]) -> Dict:
    phase20_dir = base_dir / "phase20"
    phase21_dir = base_dir / "phase21"
    phase16_dir = base_dir / "phase16"
    phase18_dir = base_dir / "phase18"
    phase22_dir = base_dir / ("phase22" if not dry_run else "phase22_dry_run")

    harness = Phase22Harness(
        phase20_dir=phase20_dir,
        phase21_dir=phase21_dir,
        phase16_dir=phase16_dir,
        phase18_dir=phase18_dir,
        phase22_output_dir=phase22_dir,
        num_agents=4,
        dry_run=dry_run,
    )
    result = harness.run_phase22(waves=waves, tasks_per_wave=10)
    return {"result": result, "phase22_dir": phase22_dir}


def read_jsonl(path: Path) -> List[Dict]:
    if not path.exists():
        return []
    items: List[Dict] = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))
    return items


def validate_jsonl(
    path: Path, required_fields: List[str], allow_empty: bool = False
) -> Tuple[bool, List[str]]:
    errors: List[str] = []
    records = read_jsonl(path)
    if not records and allow_empty:
        return True, errors
    if not records:
        errors.append(f"{path.name} contains no records")
        return False, errors

    for idx, record in enumerate(records, start=1):
        for field in required_fields:
            if field not in record:
                errors.append(f"{path.name} record {idx} missing field: {field}")
    return len(errors) == 0, errors


def validate_system_health(path: Path) -> Tuple[bool, List[str]]:
    errors: List[str] = []
    if not path.exists():
        return False, [f"{path.name} not found"]
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not data:
        return False, ["system_health.json is empty or invalid"]
    for idx, entry in enumerate(data, start=1):
        for field in ["wave", "overall_health_score", "health_status", "metrics", "anomaly_count", "timestamp"]:
            if field not in entry:
                errors.append(f"system_health.json entry {idx} missing field: {field}")
    return len(errors) == 0, errors


def verify_metrics(metrics_records: List[Dict]) -> Tuple[bool, Dict]:
    summary = {}
    success = True
    metric_map: Dict[str, float] = {}
    for record in metrics_records:
        metric_map[record["metric_name"]] = record["value"]

    for metric, target in REQUIRED_METRICS.items():
        value = metric_map.get(metric)
        if value is None:
            success = False
            summary[metric] = {"status": "missing", "target": target}
        else:
            meets = value >= target
            success = success and meets
            summary[metric] = {"value": value, "target": target, "status": "pass" if meets else "fail"}

    return success, summary


def verify_anomalies(anomalies: List[Dict]) -> Tuple[bool, Dict]:
    summary = {"total": len(anomalies), "types": {}}
    success = True
    for anomaly in anomalies:
        anomaly_type = anomaly.get("anomaly_type")
        if anomaly_type not in ANOMALY_TYPES:
            success = False
        summary["types"].setdefault(anomaly_type, 0)
        summary["types"][anomaly_type] += 1
    return success, summary


def validate_feedback(phase22_dir: Path, base_dir: Path, dry_run: bool) -> Tuple[bool, List[str]]:
    errors: List[str] = []
    learning_signals = phase22_dir / "learning_signals.jsonl"
    ok, field_errors = validate_jsonl(learning_signals, ["signal_id", "signal_type", "target_phase", "confidence", "content", "timestamp"])
    if not ok:
        errors.extend(field_errors)

    if not dry_run:
        for phase in [16, 18, 20]:
            path = base_dir / f"phase{phase}" / "phase22_feedback.jsonl"
            if not path.exists():
                errors.append(f"Missing feedback file for phase {phase}: {path}")
    return len(errors) == 0, errors


def write_verification_outputs(verification_dir: Path, metrics: Dict, anomalies: Dict, system_health: Dict) -> None:
    verification_dir.mkdir(parents=True, exist_ok=True)
    (verification_dir / "verification_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (verification_dir / "verification_anomalies.json").write_text(json.dumps(anomalies, indent=2), encoding="utf-8")
    (verification_dir / "verification_system_health.json").write_text(json.dumps(system_health, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--waves", nargs="+", type=int, default=[1, 2, 3])
    args = parser.parse_args()

    base_dir = BASE_DIR
    verification_dir = base_dir / "phase22_verification"

    dry_run_result = run_harness(base_dir, dry_run=True, waves=args.waves)
    live_result = run_harness(base_dir, dry_run=False, waves=args.waves)

    phase22_dir = live_result["phase22_dir"]

    metrics_path = phase22_dir / "metrics.jsonl"
    anomalies_path = phase22_dir / "anomalies.jsonl"
    system_health_path = phase22_dir / "system_health.json"

    metrics_records = read_jsonl(metrics_path)
    anomalies_records = read_jsonl(anomalies_path)

    metrics_ok, metrics_errors = validate_jsonl(metrics_path, ["metric_name", "wave", "value", "unit", "target_value", "status", "timestamp"])
    anomalies_ok, anomalies_errors = validate_jsonl(
        anomalies_path,
        ["anomaly_id", "anomaly_type", "severity", "description", "recommendation", "wave", "timestamp"],
        allow_empty=True,
    )
    system_ok, system_errors = validate_system_health(system_health_path)

    metric_targets_ok, metric_summary = verify_metrics(metrics_records)
    anomaly_types_ok, anomaly_summary = verify_anomalies(anomalies_records)

    feedback_ok, feedback_errors = validate_feedback(phase22_dir, base_dir, dry_run=False)

    summary = {
        "dry_run_execution": {
            "status": dry_run_result["result"].status,
            "success_rate": dry_run_result["result"].success_rate,
        },
        "live_execution": {
            "status": live_result["result"].status,
            "success_rate": live_result["result"].success_rate,
        },
        "jsonl_validation": {
            "metrics": {"ok": metrics_ok, "errors": metrics_errors},
            "anomalies": {"ok": anomalies_ok, "errors": anomalies_errors},
            "system_health": {"ok": system_ok, "errors": system_errors},
        },
        "metric_targets": metric_summary,
        "anomaly_summary": anomaly_summary,
        "feedback": {"ok": feedback_ok, "errors": feedback_errors},
    }

    verification_ok = all(
        [
            metrics_ok,
            anomalies_ok,
            system_ok,
            metric_targets_ok,
            anomaly_types_ok,
            feedback_ok,
        ]
    )

    write_verification_outputs(verification_dir, metric_summary, anomaly_summary, summary)

    report_path = verification_dir / "PHASE_22_VERIFICATION_INDEX.md"
    report_path.write_text(
        "# Phase 22 Verification Index\n\n"
        f"Status: {'PASS' if verification_ok else 'FAIL'}\n\n"
        "## Summary\n"
        f"- Dry-run status: {dry_run_result['result'].status}\n"
        f"- Live status: {live_result['result'].status}\n"
        f"- Metric targets met: {metric_targets_ok}\n"
        f"- Feedback outputs valid: {feedback_ok}\n",
        encoding="utf-8",
    )

    return 0 if verification_ok else 1


if __name__ == "__main__":
    sys.exit(main())
