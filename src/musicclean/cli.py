from __future__ import annotations

import shutil
from pathlib import Path
from typing import Annotated

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
from musicclean.config import AppConfig, ConfigError, ScannerConfig, load_config
from musicclean.database import Database
from musicclean.logging_setup import configure_logging
from musicclean.scanner import scan_root

app = typer.Typer(
    name="musicclean",
    help="Music library inventory, duplicate detection, and cleanup.",
    no_args_is_help=True,
)
console = Console()

DEFAULT_CONFIG = Path("config.yaml")
EXAMPLE_CONFIG = Path("config.example.yaml")


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


@app.callback()
def version_callback(value: bool) -> None:
    """Print the version before Typer checks for a subcommand."""
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


@app.command()
def stats(
    config_path: Annotated[
        Path,
        typer.Option("--config", help="Path to the YAML configuration file."),
    ] = DEFAULT_CONFIG,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Enable debug logging."),
    ] = False,
) -> None:
    """Display indexed-library and analysis statistics."""
    config = _load(config_path, verbose)

    with Database(config.database.path) as database:
        data = database.stats()

    duration_seconds = float(data["duration"])
    duration_hours = duration_seconds / 3600

    table = Table(title="MusicClean Inventory")
    table.add_column("Metric")
    table.add_column("Value", justify="right")
    table.add_row("Audio files", f"{int(data['files']):,}")
    table.add_row("Directories", f"{int(data['directories']):,}")
    table.add_row("Indexed GiB", f"{int(data['bytes']) / (1024 ** 3):,.2f}")
    table.add_row("Analyzed files", f"{int(data['analyzed']):,}")
    table.add_row("Hashed files", f"{int(data['hashed']):,}")
    table.add_row("Metadata errors", f"{int(data['metadata_errors']):,}")
    table.add_row("Total play time", f"{duration_hours:,.2f} hours")
    console.print(table)


@app.command()
def optimize(
    config_path: Annotated[
        Path,
        typer.Option("--config", help="Path to the YAML configuration file."),
    ] = DEFAULT_CONFIG,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Enable debug logging."),
    ] = False,
) -> None:
    """Optimize and compact the SQLite database."""
    config = _load(config_path, verbose)
    with Database(config.database.path) as database:
        database.optimize()
    console.print("[green]Database optimization complete.[/green]")


if __name__ == "__main__":
    app()
