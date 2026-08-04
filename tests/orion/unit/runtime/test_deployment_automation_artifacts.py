from pathlib import Path

ROOT = Path(__file__).parents[4]


def test_linux_installer_is_idempotency_oriented() -> None:
    script = (ROOT / "deploy" / "linux" / "install-orion.sh").read_text(encoding="utf-8")

    assert "install_config_if_missing" in script
    assert "systemctl restart" in script
    assert "verify_health" in script


def test_windows_installer_preserves_existing_environment() -> None:
    script = (ROOT / "deploy" / "windows" / "Install-Orion.ps1").read_text(encoding="utf-8")

    assert "Ensure-Directory" in script
    assert "Test-OrionHealth" in script
    assert "Test-Path $pythonExe" in script


def test_deployment_workflow_builds_container() -> None:
    workflow = (ROOT / ".github" / "workflows" / "orion-deployment.yml").read_text(encoding="utf-8")

    assert "docker build -t musicclean-orion:ci ." in workflow
    assert "bash -n deploy/linux/install-orion.sh" in workflow
