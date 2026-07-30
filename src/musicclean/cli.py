from __future__ import annotations

import shutil
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from musicclean import __version__
from musicclean.config import AppConfig, ConfigError, load_config
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


@app.callback()
def main(
    version: Annotated[
        bool | None,
        typer.Option("--version", help="Show the MusicClean version and exit."),
    ] = None,
) -> None:
    if version:
        console.print(f"MusicClean {__version__}")
        raise typer.Exit()


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
) -> None:
    """Scan configured audio roots into SQLite."""
    config = _load(config_path, verbose)

    selected = config.paths
    if root is not None:
        if root not in config.paths:
            console.print(f"[red]Unknown root group:[/red] {root}")
            raise typer.Exit(code=2)
        selected = {root: config.paths[root]}

    total_seen = 0
    total_changed = 0
    total_errors = 0

    with Database(config.database.path) as database:
        for root_name, paths in selected.items():
            for path in paths:
                if not path.is_dir():
                    console.print(f"[yellow]Skipping missing directory:[/yellow] {path}")
                    total_errors += 1
                    continue

                console.print(f"Scanning [bold]{root_name}[/bold]: {path}")
                result = scan_root(database, root_name, path, config.scanner)
                total_seen += result.files_seen
                total_changed += result.files_changed
                total_errors += result.errors

    console.print(
        f"[green]Scan complete.[/green] "
        f"Seen: {total_seen:,}  Changed/new: {total_changed:,}  Errors: {total_errors:,}"
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
    """Display indexed-library statistics."""
    config = _load(config_path, verbose)

    with Database(config.database.path) as database:
        data = database.stats()

    table = Table(title="MusicClean Inventory")
    table.add_column("Metric")
    table.add_column("Value", justify="right")
    table.add_row("Audio files", f"{data['files']:,}")
    table.add_row("Directories", f"{data['directories']:,}")
    table.add_row("Indexed bytes", f"{data['bytes']:,}")
    table.add_row("Indexed GiB", f"{data['bytes'] / (1024 ** 3):,.2f}")
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
