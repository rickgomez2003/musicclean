from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[4]


def _load(name: str, relative: str) -> ModuleType:
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load release tool: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


verify = _load(
    "musicclean_recovery_drill_verify",
    "tools/release/verify_recovery_drill.py",
)
record_tool = _load(
    "musicclean_recovery_drill_record",
    "tools/release/recovery_drill_record.py",
)


def test_repository_recovery_drill_configuration() -> None:
    assert verify.verify_configuration(ROOT) == ()


def test_passing_drill_record_is_valid(tmp_path: Path) -> None:
    path = tmp_path / "drill.json"
    record = {
        "schema_version": 1,
        "drill_id": "owner/repo:123",
        "repository": "owner/repo",
        "run_id": 123,
        "tag": "v0.6.43",
        "retention_class": "long-term",
        "started_at": "2026-08-05T00:00:00+00:00",
        "completed_at": "2026-08-05T00:00:10+00:00",
        "elapsed_seconds": 10.0,
        "status": "PASS",
        "restore_receipt": {
            "remote_verified": True,
            "download_verified": True,
            "safe_extract": True,
        },
        "failure_reason": None,
    }
    path.write_text(json.dumps(record), encoding="utf-8")
    assert verify.verify_record(path) == ()


def test_failed_drill_requires_reason(tmp_path: Path) -> None:
    path = tmp_path / "drill.json"
    record = {
        "schema_version": 1,
        "drill_id": "owner/repo:123",
        "repository": "owner/repo",
        "run_id": 123,
        "tag": "v0.6.43",
        "retention_class": "long-term",
        "started_at": "2026-08-05T00:00:00+00:00",
        "completed_at": "2026-08-05T00:00:10+00:00",
        "elapsed_seconds": 10.0,
        "status": "FAIL",
        "restore_receipt": None,
        "failure_reason": None,
    }
    path.write_text(json.dumps(record), encoding="utf-8")
    errors = verify.verify_record(path)
    assert "failed recovery drill must contain failure reason" in errors


def test_drill_record_start_and_complete(tmp_path: Path) -> None:
    record_path = tmp_path / "drill.json"
    receipt_path = tmp_path / "restore.json"

    record_tool.start(
        record_path,
        tag="v0.6.43",
        retention_class="long-term",
        run_id=123,
        repository="owner/repo",
    )

    receipt = {
        "remote_verified": True,
        "download_verified": True,
        "safe_extract": True,
    }
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

    completed = record_tool.complete(record_path, receipt_path)

    assert completed["status"] == "PASS"
    assert completed["failure_reason"] is None
    assert completed["elapsed_seconds"] >= 0
    assert completed["restore_receipt"] == receipt
    assert verify.verify_record(record_path) == ()


def test_drill_record_start_and_fail(tmp_path: Path) -> None:
    record_path = tmp_path / "drill.json"

    record_tool.start(
        record_path,
        tag="v0.6.43",
        retention_class="long-term",
        run_id=123,
        repository="owner/repo",
    )

    failed = record_tool.fail(
        record_path,
        "AWS archive restore failed",
    )

    assert failed["status"] == "FAIL"
    assert failed["failure_reason"] == "AWS archive restore failed"
    assert failed["elapsed_seconds"] >= 0
    assert verify.verify_record(record_path) == ()
