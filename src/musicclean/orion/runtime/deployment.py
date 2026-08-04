"""Deployment-oriented runtime path resolution."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class DeploymentPaths:
    state_dir: Path
    log_dir: Path
    telemetry_dir: Path

    @classmethod
    def from_environment(cls) -> DeploymentPaths:
        state = Path(os.environ.get("MUSICCLEAN_ORION_STATE_DIR", "var/orion"))
        logs = Path(os.environ.get("MUSICCLEAN_ORION_LOG_DIR", str(state / "log")))
        telemetry = Path(
            os.environ.get(
                "MUSICCLEAN_ORION_TELEMETRY_DIR",
                str(state / "telemetry"),
            )
        )
        return cls(state, logs, telemetry)

    def ensure(self) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.telemetry_dir.mkdir(parents=True, exist_ok=True)
