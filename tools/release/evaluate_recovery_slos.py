"""Evaluate recovery drill evidence against configured recovery SLOs."""

from __future__ import annotations

import argparse
import json
import tomllib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _load_policy(path: Path) -> dict[str, Any]:
    with path.open("rb") as stream:
        document = tomllib.load(stream)
    recovery = document.get("recovery")
    if not isinstance(recovery, dict):
        raise ValueError("recovery SLO policy table is missing")
    return recovery


def _metric_status(
    value: float,
    *,
    warning: float,
    objective: float,
    lower_is_better: bool,
) -> str:
    if lower_is_better:
        if value <= warning:
            return "PASS"
        if value <= objective:
            return "WARN"
        return "FAIL"

    if value >= warning:
        return "PASS"
    if value >= objective:
        return "WARN"
    return "FAIL"


def _overall_status(statuses: list[str]) -> str:
    if "FAIL" in statuses:
        return "FAIL"
    if "WARN" in statuses:
        return "WARN"
    return "PASS"


def evaluate(
    *,
    policy: dict[str, Any],
    latest_drill: dict[str, Any],
    history: list[dict[str, Any]],
    now: datetime,
) -> dict[str, Any]:
    if latest_drill.get("status") != "PASS":
        return {
            "schema_version": 1,
            "evaluated_at": now.isoformat(),
            "status": "FAIL",
            "reason": "latest recovery drill did not pass",
            "metrics": {},
        }

    elapsed = latest_drill.get("elapsed_seconds")
    completed_at = latest_drill.get("completed_at")
    if not isinstance(elapsed, (int, float)):
        raise ValueError("latest recovery drill elapsed_seconds is invalid")
    if not isinstance(completed_at, str):
        raise ValueError("latest recovery drill completed_at is invalid")

    completed = datetime.fromisoformat(completed_at)
    if completed.tzinfo is None:
        raise ValueError("latest recovery drill completed_at must be timezone-aware")

    age_days = max(0.0, (now - completed.astimezone(UTC)).total_seconds() / 86400.0)

    duration_policy = policy["duration_seconds"]
    age_policy = policy["successful_drill_age_days"]
    ratio_policy = policy["success_ratio"]

    if not all(isinstance(item, dict) for item in (duration_policy, age_policy, ratio_policy)):
        raise ValueError("recovery SLO metric policy is invalid")

    duration_status = _metric_status(
        float(elapsed),
        warning=float(duration_policy["warning"]),
        objective=float(duration_policy["objective"]),
        lower_is_better=True,
    )
    age_status = _metric_status(
        age_days,
        warning=float(age_policy["warning"]),
        objective=float(age_policy["objective"]),
        lower_is_better=True,
    )

    minimum_samples = int(ratio_policy["minimum_samples"])
    evaluated_history = history[-minimum_samples:] if minimum_samples > 0 else []
    if len(evaluated_history) < minimum_samples:
        ratio_status = "WARN"
        success_ratio = (
            sum(1 for item in evaluated_history if item.get("status") == "PASS")
            / len(evaluated_history)
            if evaluated_history
            else 0.0
        )
        ratio_reason = "insufficient drill history"
    else:
        successes = sum(1 for item in evaluated_history if item.get("status") == "PASS")
        success_ratio = successes / len(evaluated_history)
        ratio_status = _metric_status(
            success_ratio,
            warning=float(ratio_policy["warning"]),
            objective=float(ratio_policy["objective"]),
            lower_is_better=False,
        )
        ratio_reason = None

    statuses = [duration_status, age_status, ratio_status]

    return {
        "schema_version": 1,
        "evaluated_at": now.isoformat(),
        "status": _overall_status(statuses),
        "reason": ratio_reason,
        "latest_drill": {
            "drill_id": latest_drill.get("drill_id"),
            "tag": latest_drill.get("tag"),
            "completed_at": completed_at,
        },
        "metrics": {
            "recovery_duration_seconds": {
                "value": float(elapsed),
                "warning": float(duration_policy["warning"]),
                "objective": float(duration_policy["objective"]),
                "status": duration_status,
            },
            "successful_drill_age_days": {
                "value": age_days,
                "warning": float(age_policy["warning"]),
                "objective": float(age_policy["objective"]),
                "status": age_status,
            },
            "success_ratio": {
                "value": success_ratio,
                "warning": float(ratio_policy["warning"]),
                "objective": float(ratio_policy["objective"]),
                "minimum_samples": minimum_samples,
                "samples_evaluated": len(evaluated_history),
                "status": ratio_status,
            },
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--latest-drill", type=Path, required=True)
    parser.add_argument("--history", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    policy = _load_policy(args.policy)
    latest = _load_json(args.latest_drill)
    history_data = json.loads(args.history.read_text(encoding="utf-8"))
    if not isinstance(history_data, list) or not all(
        isinstance(item, dict) for item in history_data
    ):
        raise ValueError("recovery drill history must be a JSON array of objects")

    report = evaluate(
        policy=policy,
        latest_drill=latest,
        history=history_data,
        now=datetime.now(UTC),
    )
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
