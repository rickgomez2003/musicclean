from __future__ import annotations

import shutil
from pathlib import Path
from typing import Annotated, Literal, SupportsIndex, SupportsInt

import typer
from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table

from musicclean import __version__
from musicclean.album_intelligence import build_album_editions
from musicclean.config import AppConfig, ConfigError, ScannerConfig, load_config
from musicclean.database import Database
from musicclean.error_reporting import (
    write_metadata_errors_csv,
    write_metadata_errors_json,
)
from musicclean.logging_setup import configure_logging
from musicclean.metadata import inspect_audio_file
from musicclean.models import DuplicateGroup, MetadataErrorRecord
from musicclean.reporting import write_csv_report, write_json_report
from musicclean.scanner import scan_root

app = typer.Typer(
    name="musicclean",
    help="Music library inventory, duplicate detection, and cleanup.",
    no_args_is_help=True,
)
console = Console()

DEFAULT_CONFIG = Path("config.yaml")
EXAMPLE_CONFIG = Path("config.example.yaml")
ReportFormat = Literal["table", "json", "csv"]


def _load(config_path: Path, verbose: bool) -> AppConfig:
    try:
        config = load_config(config_path)
    except ConfigError as exc:
        console.print(f"[bold red]Configuration error:[/bold red] {exc}")
        raise typer.Exit(code=2) from exc

    configure_logging(config.logging, verbose=verbose)
    return config


def _scanner_overrides(
    config: ScannerConfig,
    *,
    no_hash: bool,
    no_metadata: bool,
) -> ScannerConfig:
    return ScannerConfig(
        follow_symlinks=config.follow_symlinks,
        include_hidden=config.include_hidden,
        batch_size=config.batch_size,
        hash_files=config.hash_files and not no_hash,
        read_metadata=config.read_metadata and not no_metadata,
        hash_chunk_size=config.hash_chunk_size,
        extensions=config.extensions,
    )


def _format_bytes(value: int) -> str:
    units = ("B", "KiB", "MiB", "GiB", "TiB")
    amount = float(value)

    for unit in units:
        if abs(amount) < 1024 or unit == units[-1]:
            return f"{amount:,.2f} {unit}"
        amount /= 1024

    return f"{amount:,.2f} TiB"


def _safe_display_int(value: object) -> int:
    if value is None:
        return 0

    if not isinstance(
        value,
        (str, bytes, bytearray, SupportsInt, SupportsIndex),
    ):
        return 0

    try:
        return int(value)
    except (TypeError, ValueError, OverflowError):
        return 0


def version_callback(value: bool) -> None:
    if value:
        console.print(f"MusicClean {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool | None,
        typer.Option(
            "--version",
            help="Show the MusicClean version and exit.",
            callback=version_callback,
            is_eager=True,
        ),
    ] = None,
) -> None:
    """MusicClean command-line interface."""


@app.command()
def init(
    force: Annotated[
        bool,
        typer.Option("--force", help="Overwrite an existing config.yaml."),
    ] = False,
) -> None:
    """Create local runtime directories and a working configuration file."""
    if not EXAMPLE_CONFIG.is_file():
        console.print(f"[red]Missing {EXAMPLE_CONFIG}[/red]")
        raise typer.Exit(code=1)

    if DEFAULT_CONFIG.exists() and not force:
        console.print(f"{DEFAULT_CONFIG} already exists; use --force to replace it.")
    else:
        shutil.copyfile(EXAMPLE_CONFIG, DEFAULT_CONFIG)
        console.print(f"Created {DEFAULT_CONFIG}")

    Path(".musicclean/logs").mkdir(parents=True, exist_ok=True)
    console.print("Initialized .musicclean runtime directory.")


@app.command()
def scan(
    root: Annotated[
        str | None,
        typer.Option("--root", help="Scan one configured root group, such as downloads."),
    ] = None,
    config_path: Annotated[
        Path,
        typer.Option("--config", help="Path to the YAML configuration file."),
    ] = DEFAULT_CONFIG,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Enable debug logging."),
    ] = False,
    no_hash: Annotated[
        bool,
        typer.Option("--no-hash", help="Skip BLAKE3 hashing for this scan."),
    ] = False,
    no_metadata: Annotated[
        bool,
        typer.Option("--no-metadata", help="Skip audio metadata extraction for this scan."),
    ] = False,
) -> None:
    """Scan configured audio roots, metadata, and hashes into SQLite."""
    config = _load(config_path, verbose)
    scanner_config = _scanner_overrides(
        config.scanner,
        no_hash=no_hash,
        no_metadata=no_metadata,
    )

    selected = config.paths
    if root is not None:
        if root not in config.paths:
            console.print(f"[red]Unknown root group:[/red] {root}")
            raise typer.Exit(code=2)
        selected = {root: config.paths[root]}

    total_seen = 0
    total_analyzed = 0
    total_unchanged = 0
    total_errors = 0

    progress_columns = [
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TaskProgressColumn(),
        TextColumn("Analyzed: {task.fields[analyzed]}"),
        TextColumn("Unchanged: {task.fields[unchanged]}"),
        TimeElapsedColumn(),
    ]

    with Database(config.database.path) as database:
        for root_name, paths in selected.items():
            for path in paths:
                if not path.is_dir():
                    console.print(f"[yellow]Skipping missing directory:[/yellow] {path}")
                    total_errors += 1
                    continue

                console.print(f"Scanning [bold]{root_name}[/bold]: {path}")

                with Progress(*progress_columns, console=console) as progress:
                    task_id = progress.add_task(
                        "Discovering audio files",
                        total=None,
                        analyzed=0,
                        unchanged=0,
                    )

                    def update(
                        seen: int,
                        analyzed: int,
                        unchanged: int,
                        current_path: Path,
                        *,
                        bound_task_id: TaskID = task_id,
                    ) -> None:
                        progress.update(
                            bound_task_id,
                            completed=seen,
                            description=current_path.name[:50],
                            analyzed=analyzed,
                            unchanged=unchanged,
                        )

                    result = scan_root(
                        database,
                        root_name,
                        path,
                        scanner_config,
                        progress=update,
                    )

                total_seen += result.files_seen
                total_analyzed += result.files_analyzed
                total_unchanged += result.files_unchanged
                total_errors += result.errors

    console.print(
        f"[green]Scan complete.[/green] "
        f"Seen: {total_seen:,}  "
        f"Analyzed: {total_analyzed:,}  "
        f"Unchanged: {total_unchanged:,}  "
        f"Errors: {total_errors:,}"
    )


def _render_duplicate_groups(groups: list[DuplicateGroup]) -> None:
    if not groups:
        console.print("[green]No exact duplicate groups found.[/green]")
        return

    for index, group in enumerate(groups, start=1):
        table = Table(
            title=(
                f"Group {index} · {group.file_count} files · "
                f"{_format_bytes(group.reclaimable_bytes)} reclaimable"
            )
        )
        table.add_column("Root")
        table.add_column("Path")
        table.add_column("Codec")
        table.add_column("Audio")
        table.add_column("Size", justify="right")

        for file in group.files:
            audio_parts = []
            if file.sample_rate is not None:
                audio_parts.append(f"{file.sample_rate / 1000:g} kHz")
            if file.bits_per_sample is not None:
                audio_parts.append(f"{file.bits_per_sample}-bit")
            if file.bitrate is not None:
                audio_parts.append(f"{file.bitrate / 1000:,.0f} kbps")

            table.add_row(
                file.root_name,
                str(file.path),
                file.codec or "Unknown",
                " / ".join(audio_parts) or "Unknown",
                _format_bytes(file.size),
            )

        console.print(table)


@app.command()
def duplicates(
    root: Annotated[
        str | None,
        typer.Option("--root", help="Limit results to one configured root name."),
    ] = None,
    minimum_size: Annotated[
        int,
        typer.Option("--minimum-size", min=0),
    ] = 1,
    limit: Annotated[
        int | None,
        typer.Option("--limit", min=1),
    ] = 50,
    report_format: Annotated[
        ReportFormat,
        typer.Option("--format", case_sensitive=False),
    ] = "table",
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o"),
    ] = None,
    config_path: Annotated[
        Path,
        typer.Option("--config"),
    ] = DEFAULT_CONFIG,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v"),
    ] = False,
) -> None:
    """Find exact duplicate files using stored BLAKE3 hashes."""
    config = _load(config_path, verbose)

    with Database(config.database.path) as database:
        summary = database.duplicate_summary(
            root_name=root,
            minimum_size=minimum_size,
        )
        groups = list(
            database.iter_duplicate_groups(
                root_name=root,
                minimum_size=minimum_size,
                limit=limit,
            )
        )

    console.print(
        f"[bold]Exact duplicate summary:[/bold] "
        f"{summary['groups']:,} groups, "
        f"{summary['duplicate_files']:,} files, "
        f"{_format_bytes(summary['reclaimable_bytes'])} reclaimable."
    )

    if report_format == "table":
        _render_duplicate_groups(groups)
        return

    if output is None:
        output = Path(".musicclean/reports") / f"exact-duplicates.{report_format}"

    if report_format == "json":
        write_json_report(groups, output)
    else:
        write_csv_report(groups, output)

    console.print(f"[green]Report written:[/green] {output.resolve()}")


def _render_metadata_errors(records: list[MetadataErrorRecord]) -> None:
    if not records:
        console.print("[green]No metadata errors matched the requested filters.[/green]")
        return

    table = Table(title=f"Metadata Errors · {len(records):,} shown")
    table.add_column("Category")
    table.add_column("Codec")
    table.add_column("Size", justify="right")
    table.add_column("Path")
    table.add_column("Error")
    table.add_column("Suggested action")

    for record in records:
        table.add_row(
            record.category,
            record.codec or record.extension or "Unknown",
            _format_bytes(record.size),
            str(record.path),
            record.error[:100],
            record.suggested_action,
        )

    console.print(table)


@app.command(name="errors")
def errors_command(
    root: Annotated[
        str | None,
        typer.Option("--root", help="Limit results to one configured root."),
    ] = None,
    category: Annotated[
        str | None,
        typer.Option(
            "--category",
            help="Filter by an error category shown in the summary.",
        ),
    ] = None,
    limit: Annotated[
        int | None,
        typer.Option("--limit", min=1),
    ] = 200,
    report_format: Annotated[
        ReportFormat,
        typer.Option("--format", case_sensitive=False),
    ] = "table",
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o"),
    ] = None,
    config_path: Annotated[
        Path,
        typer.Option("--config"),
    ] = DEFAULT_CONFIG,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v"),
    ] = False,
) -> None:
    """Analyze files whose audio metadata could not be read cleanly."""
    config = _load(config_path, verbose)

    with Database(config.database.path) as database:
        summary = database.metadata_error_summary(root_name=root)
        records = database.metadata_errors(
            root_name=root,
            category=category,
            limit=limit,
        )

    summary_table = Table(title="Metadata Error Summary")
    summary_table.add_column("Category")
    summary_table.add_column("Files", justify="right")
    for key, count in sorted(summary.items(), key=lambda item: (-item[1], item[0])):
        summary_table.add_row(key, f"{count:,}")
    console.print(summary_table)

    if report_format == "table":
        _render_metadata_errors(records)
        return

    if output is None:
        output = Path(".musicclean/reports") / f"metadata-errors.{report_format}"

    if report_format == "json":
        write_metadata_errors_json(records, output)
    else:
        write_metadata_errors_csv(records, output)

    console.print(f"[green]Report written:[/green] {output.resolve()}")


@app.command()
def stats(
    config_path: Annotated[
        Path,
        typer.Option("--config"),
    ] = DEFAULT_CONFIG,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v"),
    ] = False,
) -> None:
    """Display indexed-library, analysis, and duplicate statistics."""
    config = _load(config_path, verbose)

    with Database(config.database.path) as database:
        data = database.stats()
        duplicate_data = database.duplicate_summary()

    duration_hours = float(data["duration"]) / 3600

    table = Table(title="MusicClean Inventory")
    table.add_column("Metric")
    table.add_column("Value", justify="right")
    table.add_row("Audio files", f"{int(data['files']):,}")
    table.add_row("Directories", f"{int(data['directories']):,}")
    table.add_row("Indexed size", _format_bytes(int(data["bytes"])))
    table.add_row("Analyzed files", f"{int(data['analyzed']):,}")
    table.add_row("Hashed files", f"{int(data['hashed']):,}")
    table.add_row("Metadata errors", f"{int(data['metadata_errors']):,}")
    table.add_row("Total play time", f"{duration_hours:,.2f} hours")
    table.add_row("Exact duplicate groups", f"{duplicate_data['groups']:,}")
    table.add_row("Files in duplicate groups", f"{duplicate_data['duplicate_files']:,}")
    table.add_row(
        "Potentially reclaimable",
        _format_bytes(duplicate_data["reclaimable_bytes"]),
    )
    console.print(table)


@app.command(name="inspect")
def inspect_command(
    path: Annotated[Path, typer.Argument(help="Audio file to inspect.")],
) -> None:
    """Inspect one audio file and display parser and metadata diagnostics."""
    diagnostic = inspect_audio_file(path)
    if diagnostic.get("error"):
        console.print(f"[bold red]Inspection failed:[/bold red] {diagnostic['error']}")
        raise typer.Exit(code=1)

    metadata = diagnostic.get("metadata")
    metadata_map = metadata if isinstance(metadata, dict) else {}

    table = Table(title=f"Audio Inspection · {path.name}")
    table.add_column("Field")
    table.add_column("Value")
    table.add_row("Path", str(path.resolve()))
    table.add_row("Size", _format_bytes(_safe_display_int(diagnostic.get("size"))))
    table.add_row("Parser", str(diagnostic.get("parser") or "Unknown"))
    table.add_row("Tag type", str(diagnostic.get("tag_type") or "None"))
    table.add_row("Tag count", str(diagnostic.get("tag_count") or 0))

    fields = (
        ("Codec", "codec"),
        ("Sample rate", "sample_rate"),
        ("Bit depth", "bits_per_sample"),
        ("Channels", "channels"),
        ("Bitrate", "bitrate"),
        ("Duration", "duration"),
        ("Title", "title"),
        ("Artist", "artist"),
        ("Album", "album"),
        ("Album artist", "album_artist"),
        ("Track", "track_number"),
        ("Disc", "disc_number"),
        ("Date", "date"),
        ("Artwork", "has_artwork"),
        ("MusicBrainz track ID", "musicbrainz_track_id"),
        ("MusicBrainz album ID", "musicbrainz_album_id"),
        ("MusicBrainz artist ID", "musicbrainz_artist_id"),
        ("Metadata error", "error"),
    )
    for label, key in fields:
        value = metadata_map.get(key)
        table.add_row(label, "" if value is None else str(value))

    console.print(table)

    warning = diagnostic.get("warning")
    if warning:
        console.print(f"[yellow]Parser warning:[/yellow] {warning}")

    tag_keys = diagnostic.get("tag_keys")
    if isinstance(tag_keys, list) and tag_keys:
        console.print("[bold]Tag keys:[/bold] " + ", ".join(str(key) for key in tag_keys))


@app.command(name="albums")
def albums_command(
    config_path: Annotated[Path, typer.Option("--config")] = DEFAULT_CONFIG,
    root: Annotated[str | None, typer.Option("--root")] = None,
    artist: Annotated[str | None, typer.Option("--artist")] = None,
    album: Annotated[str | None, typer.Option("--album")] = None,
    limit: Annotated[int, typer.Option("--limit", min=1)] = 50,
    show_reasons: Annotated[bool, typer.Option("--reasons")] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False,
) -> None:
    """Score album editions and recommend which copies to keep or review."""
    config = _load(config_path, verbose)
    with Database(config.database.path) as database:
        rows = database.album_rows(root_name=root, artist=artist, album=album)
    editions = build_album_editions(rows)[:limit]
    if not editions:
        console.print("[yellow]No indexed albums matched the filters.[/yellow]")
        return

    table = Table(title="Album Intelligence")
    table.add_column("Rating")
    table.add_column("Score", justify="right")
    table.add_column("Recommendation")
    table.add_column("Artist")
    table.add_column("Album")
    table.add_column("Tracks", justify="right")
    table.add_column("Edition directory")
    for edition in editions:
        table.add_row(
            edition.stars,
            str(edition.score),
            edition.recommendation,
            edition.artist,
            edition.album,
            str(edition.track_count),
            str(edition.directory),
        )
    console.print(table)
    if show_reasons:
        for edition in editions:
            console.print(
                f"[bold]{edition.artist} — {edition.album}[/bold] "
                f"({edition.score}/100): " + "; ".join(edition.reasons)
            )


@app.command()
def optimize(
    config_path: Annotated[
        Path,
        typer.Option("--config"),
    ] = DEFAULT_CONFIG,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v"),
    ] = False,
) -> None:
    """Optimize and compact the SQLite database."""
    config = _load(config_path, verbose)
    with Database(config.database.path) as database:
        database.optimize()
    console.print("[green]Database optimization complete.[/green]")


if __name__ == "__main__":
    app()
