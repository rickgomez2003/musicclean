# MusicClean

MusicClean is a command-line tool for scanning and cleaning large music collections on
TrueNAS, FreeBSD, Linux, Windows, and macOS.

## Sprint 1 features

- YAML configuration
- Rotating log files
- SQLite inventory database
- Incremental filesystem scanning
- Audio-file filtering
- CLI commands for initialization, scanning, statistics, and database optimization
- GitHub Actions test workflow

## Default paths

Download staging:

```text
/mnt/Data/Media/Downloads/sabnzdb/complete/music/
```

Permanent library:

```text
/mnt/Data/Media/Music/
```

## Install on Windows for development

```bash
git clone https://github.com/rickgomez2003/musicclean.git
cd musicclean
py -3.11 -m venv .venv
source .venv/Scripts/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
musicclean --help
```

## Install on FreeBSD / TrueNAS

```sh
pkg install -y python311 py311-pip
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
pip install -e .
musicclean --help
```

## Initialize

```sh
musicclean init
```

This creates local runtime directories and copies `config.example.yaml` to `config.yaml`
when no local configuration exists.

## Scan

```sh
musicclean scan
```

Scan a specific configured root:

```sh
musicclean scan --root downloads
musicclean scan --root library
```

## Statistics

```sh
musicclean stats
```

## Optimize SQLite

```sh
musicclean optimize
```

## Development

```bash
pytest
ruff check .
mypy src
```

## Status

This repository is under active development. Destructive cleanup is intentionally not
enabled in Sprint 1; the first release establishes a reliable inventory and database
foundation.
