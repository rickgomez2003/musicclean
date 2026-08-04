"""Launch MusicClean Orion as a local/network HTTP service."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

import uvicorn

from musicclean.orion.runtime.bootstrap import bootstrap_runtime
from musicclean.orion.runtime.config import RuntimeConfig


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m musicclean.orion.runtime",
        description="Run the MusicClean Orion HTTP service.",
    )
    parser.add_argument("--database", type=Path, default=Path("orion.db"))
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument(
        "--log-level",
        default="info",
        choices=("critical", "error", "warning", "info", "debug", "trace"),
    )
    parser.add_argument(
        "--no-startup-reconcile",
        action="store_true",
        help="Skip the detection-only startup reconciliation sweep.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = RuntimeConfig(
        database_path=args.database,
        host=args.host,
        port=args.port,
        log_level=args.log_level,
        startup_reconcile=not args.no_startup_reconcile,
    )
    runtime = bootstrap_runtime(config)

    uvicorn.run(
        runtime.app,
        host=config.host,
        port=config.port,
        log_level=config.log_level,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
