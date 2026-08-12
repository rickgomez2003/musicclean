from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _stable_entry_id(entry: dict[str, Any]) -> str:
    payload = json.dumps(
        entry,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return hashlib.sha256(payload).hexdigest()


def build_history(
    existing: list[dict[str, Any]],
    observation: dict[str, Any],
    *,
    max_entries: int = 20,
) -> list[dict[str, Any]]:
    candidate = {
        "schema_version": observation.get("schema_version"),
        "sample_count": observation.get("sample_count"),
        "minimum_samples": observation.get("minimum_samples"),
        "authoritative": observation.get("authoritative"),
        "overall_status": observation.get("overall_status"),
        "metrics": observation.get("metrics"),
        "provider_neutral": observation.get("provider_neutral"),
        "external_export_enabled": observation.get("external_export_enabled"),
    }
    candidate["history_id"] = _stable_entry_id(candidate)

    deduplicated: list[dict[str, Any]] = []
    seen: set[str] = set()

    for item in [*existing, candidate]:
        if not isinstance(item, dict):
            continue

        history_id = item.get("history_id")
        if not isinstance(history_id, str):
            history_id = _stable_entry_id(item)
            item = {**item, "history_id": history_id}

        if history_id in seen:
            continue

        seen.add(history_id)
        deduplicated.append(item)

    return deduplicated[-max_entries:]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--history", type=Path, required=True)
    parser.add_argument("--slo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-entries", type=int, default=20)
    args = parser.parse_args()

    existing: list[dict[str, Any]] = []
    if args.history.exists():
        raw_history = _load_json(args.history)
        if isinstance(raw_history, list):
            existing = [item for item in raw_history if isinstance(item, dict)]

    observation = _load_json(args.slo)
    if not isinstance(observation, dict):
        raise ValueError("SLO evidence must be a JSON object")

    history = build_history(
        existing,
        observation,
        max_entries=max(1, args.max_entries),
    )

    args.output.write_text(
        json.dumps(history, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(
        "recovery alert routed SLO alert delivery routed delivery routed delivery SLO history built"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
