# MusicClean Sprint 4.2 — Scanner Reliability

This overlay upgrades MusicClean to 0.4.2.

## Included

- Safe tag-value extraction that does not index arbitrary Mutagen value objects
- Improved APEv2/WavPack tag handling
- APEv2 embedded artwork detection
- Safe numeric conversion for technical metadata
- New `musicclean inspect <file>` diagnostic command
- Regression tests for sequence-like tag values and APEv2 wrappers

## Install

Extract this ZIP over the root of the MusicClean repository and allow files to be replaced. Then run:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\musicclean.exe --version
.\.venv\Scripts\musicclean.exe inspect "\\server\share\path\example.wv"
```

To refresh the existing database records after verifying one file:

```powershell
.\.venv\Scripts\musicclean.exe scan --root downloads
.\.venv\Scripts\musicclean.exe errors --limit 1000
```

## Quality gates

```powershell
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\pytest.exe
.\.venv\Scripts\mypy.exe src
```
