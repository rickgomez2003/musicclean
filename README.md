# MusicClean

MusicClean is a cross-platform command-line tool for inventorying, analyzing, and
eventually cleaning large music collections.

## Sprint 3 capabilities

- Exact duplicate detection using stored BLAKE3 hashes
- Duplicate groups sorted by reclaimable disk space
- Total duplicate-file and reclaimable-space summaries
- Optional root-group filtering
- Minimum file-size filtering
- Table, JSON, and UTF-8 CSV reports
- Automatic SQLite schema migration and indexes
- Recursive audio-file discovery
- Incremental rescans based on file size and nanosecond modification time
- Audio metadata and technical properties through Mutagen
- Live Rich progress reporting
- Automated Ruff, MyPy, Pytest, and coverage checks on Python 3.11–3.13

MusicClean remains read-only with respect to the music collection. It does not move,
rename, modify, quarantine, or delete audio files.

## Upgrade

```powershell
git switch develop
git pull --ff-only origin develop
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

## Scan

A duplicate report requires hashes, so do not use `--no-hash` for the indexing scan.

```powershell
.\.venv\Scripts\musicclean.exe scan
```

A second scan skips analysis for files whose size and nanosecond modification time have
not changed.

## Exact duplicate report

Display the 50 groups with the most reclaimable space:

```powershell
.\.venv\Scripts\musicclean.exe duplicates
```

Show more groups:

```powershell
.\.venv\Scripts\musicclean.exe duplicates --limit 200
```

Limit the query to one configured root:

```powershell
.\.venv\Scripts\musicclean.exe duplicates --root library
```

Ignore files smaller than 10 MiB:

```powershell
.\.venv\Scripts\musicclean.exe duplicates --minimum-size 10485760
```

Write JSON:

```powershell
.\.venv\Scripts\musicclean.exe duplicates `
  --format json `
  --output .musicclean\reports\duplicates.json
```

Write a spreadsheet-compatible CSV:

```powershell
.\.venv\Scripts\musicclean.exe duplicates `
  --format csv `
  --output .musicclean\reports\duplicates.csv
```

The reclaimable-space calculation assumes that one file in every exact duplicate group
must be retained.

## Statistics

```powershell
.\.venv\Scripts\musicclean.exe stats
```

The statistics now include exact duplicate groups, files in those groups, and potentially
reclaimable disk space.

## Validation

```powershell
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\pytest.exe
.\.venv\Scripts\mypy.exe src
```

Run the same coverage threshold used by CI:

```powershell
.\.venv\Scripts\pytest.exe `
  --cov=musicclean `
  --cov-report=term-missing `
  --cov-report=xml
```
