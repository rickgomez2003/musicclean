from musicclean import __version__
from musicclean.orion.runtime.bootstrap import ORION_RUNTIME_VERSION


def test_runtime_and_package_share_one_version_source() -> None:
    assert __version__ == ORION_RUNTIME_VERSION
