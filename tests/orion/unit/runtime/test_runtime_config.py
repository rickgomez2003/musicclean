from pathlib import Path

import pytest

from musicclean.orion.runtime import RuntimeConfig


def test_runtime_config_has_local_safe_defaults() -> None:
    config = RuntimeConfig(database_path=Path("orion.db"))

    assert config.host == "127.0.0.1"
    assert config.port == 8765
    assert config.startup_reconcile is True


def test_runtime_config_rejects_invalid_port() -> None:
    with pytest.raises(ValueError, match="port"):
        RuntimeConfig(database_path=Path("orion.db"), port=70000)
