from __future__ import annotations

import importlib.util
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


sbom = _load(
    "musicclean_release_sbom",
    "tools/release/verify_sbom.py",
)


def test_repository_sbom_configuration() -> None:
    assert sbom.verify_configuration(ROOT) == ()


def test_valid_spdx_document() -> None:
    document = {
        "spdxVersion": "SPDX-2.3",
        "documentNamespace": "https://example.invalid/musicclean/sbom",
        "packages": [{"name": "musicclean", "SPDXID": "SPDXRef-Package"}],
    }
    assert sbom.verify_document(document) == ()


def test_invalid_spdx_document_is_rejected() -> None:
    errors = sbom.verify_document({})
    assert "SBOM is not an SPDX document" in errors
    assert "SBOM documentNamespace is missing" in errors
    assert "SBOM does not contain any packages" in errors
