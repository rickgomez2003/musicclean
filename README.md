# MusicClean

MusicClean is a cross-platform command-line tool for inventorying, analyzing, and
eventually cleaning large music collections.

## Sprint 2 capabilities

- Recursive audio-file discovery
- SQLite inventory with automatic schema migration
- Incremental rescans based on file size and nanosecond modification time
- BLAKE3 whole-file hashes
- Audio metadata and technical properties through Mutagen
- Codec, bitrate, sample rate, bit depth, channel count, duration, and common tags
- Embedded-artwork detection
- MusicBrainz identifier capture when present
- Live Rich progress display
- Windows, FreeBSD, TrueNAS, Linux, and macOS-compatible paths
- Ruff, mypy, pytest, and GitHub Actions validation

No files are moved, renamed, modified, or deleted in Sprint 2.

## Upgrade an existing development checkout

```powershell
git switch develop
git pull --ff-only origin develop
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

Your existing SQLite database is upgraded automatically when MusicClean opens it.

## Initialize

```powershell
.\.venv\Scripts\musicclean.exe init
```

Use `--force` only when you intentionally want to replace the local `config.yaml`:

```powershell
.\.venv\Scripts\musicclean.exe init --force
```

## Scan

Scan every configured root:

```powershell
.\.venv\Scripts\musicclean.exe scan
```

Scan only one configured group:

```powershell
.\.venv\Scripts\musicclean.exe scan --root downloads
.\.venv\Scripts\musicclean.exe scan --root library
```

Temporarily skip expensive operations:

```powershell
.\.venv\Scripts\musicclean.exe scan --no-hash
.\.venv\Scripts\musicclean.exe scan --no-metadata
```

The first complete scan reads and hashes every audio file. A later scan skips analysis
when the file size and nanosecond modification time are unchanged.

## Statistics

```powershell
.\.venv\Scripts\musicclean.exe stats
```

## Validation

```powershell
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\pytest.exe
.\.venv\Scripts\mypy.exe src
```

## Current safety behavior

Sprint 2 is read-only with respect to the music collection. It only writes to the local
MusicClean SQLite database and log directory.
