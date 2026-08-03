from musicclean.orion.application import StartupRecoverySweep


def test_startup_recovery_sweep_command_is_constructible() -> None:
    assert StartupRecoverySweep() == StartupRecoverySweep()
