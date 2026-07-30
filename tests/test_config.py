from pathlib import Path

from musicclean.config import load_config


def test_load_config(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
paths:
  downloads:
    - /tmp/music
database:
  path: data/musicclean.db
logging:
  directory: logs
scanner:
  extensions:
    - flac
    - .mp3
""",
        encoding="utf-8",
    )

    config = load_config(config_file)

    assert config.database.path == (tmp_path / "data/musicclean.db").resolve()
    assert config.logging.directory == (tmp_path / "logs").resolve()
    assert config.scanner.extensions == frozenset({".flac", ".mp3"})
