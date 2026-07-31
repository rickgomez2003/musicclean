# MusicClean

## Sprint 4.1 — Metadata Error Analyzer

Sprint 4.1 adds a real `musicclean errors` command while keeping MusicClean
completely read-only against the music collection.

### Install

Copy the Sprint 4.1 files over the repository and reinstall:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

### Verify

```powershell
.\.venv\Scripts\musicclean.exe --version
.\.venv\Scripts\musicclean.exe errors --help
```

Expected version:

```text
MusicClean 0.4.1
```

### Analyze existing errors

No rescan is required because Sprint 3 already stored the metadata errors in SQLite:

```powershell
.\.venv\Scripts\musicclean.exe errors
```

Show all current records:

```powershell
.\.venv\Scripts\musicclean.exe errors --limit 1000
```

Filter one category:

```powershell
.\.venv\Scripts\musicclean.exe errors --category truncated_file
```

### Export

```powershell
.\.venv\Scripts\musicclean.exe errors `
  --format csv `
  --output .musicclean\reports\metadata-errors.csv
```

```powershell
.\.venv\Scripts\musicclean.exe errors `
  --format json `
  --output .musicclean\reports\metadata-errors.json
```

### Categories

- `unsupported_format`
- `damaged_or_invalid`
- `truncated_file`
- `tag_parse_failure`
- `access_failure`
- `empty_or_unreadable`
- `unknown`

Suggested actions are advisory. MusicClean does not repair, move, or delete files.

### Validate

```powershell
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\pytest.exe
.\.venv\Scripts\mypy.exe src
```
