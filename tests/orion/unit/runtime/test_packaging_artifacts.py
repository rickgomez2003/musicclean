from pathlib import Path

ROOT = Path(__file__).parents[4]


def test_dockerfile_launches_existing_runtime_composition_root() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert 'CMD ["python", "-m", "musicclean.orion.runtime"]' in dockerfile
    assert "HEALTHCHECK" in dockerfile
    assert "USER musicclean" in dockerfile


def test_systemd_unit_launches_existing_runtime_composition_root() -> None:
    unit = (ROOT / "deploy" / "systemd" / "musicclean-orion.service").read_text(encoding="utf-8")

    assert "-m musicclean.orion.runtime" in unit
    assert "EnvironmentFile=/etc/musicclean/orion.env" in unit
    assert "Restart=on-failure" in unit


def test_environment_example_does_not_contain_a_real_secret() -> None:
    example = (ROOT / "deploy" / "orion.env.example").read_text(encoding="utf-8")

    assert "MUSICCLEAN_ORION_API_KEY=change-me" in example
