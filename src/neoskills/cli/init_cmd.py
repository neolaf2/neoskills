"""neoskills init - create the ~/.neoskills/ workspace."""

from pathlib import Path

import click
from rich.console import Console
from rich.tree import Tree

from neoskills.core.cellar import Cellar

console = Console()


@click.command()
@click.option(
    "--root",
    type=click.Path(),
    default=None,
    help="Custom workspace root (default: ~/.neoskills)",
)
def init(root: str | None) -> None:
    """Initialize the neoskills workspace (~/.neoskills/)."""
    cellar = Cellar(Path(root) if root else None)

    if cellar.is_initialized:
        console.print(f"[yellow]Workspace already exists at {cellar.root}[/yellow]")
        console.print("Checking for missing directories and files...")

    result = cellar.initialize()

    dirs_created = result["directories"]
    files_created = result["files"]
    total = len(dirs_created) + len(files_created)

    if total == 0:
        console.print("[green]Workspace is up to date. Nothing to create.[/green]")
        return

    tree = Tree(f"[bold cyan]{cellar.root}[/bold cyan]")

    if dirs_created:
        dirs_branch = tree.add("[bold]Directories created")
        for d in dirs_created:
            dirs_branch.add(f"[dim]{d.relative_to(cellar.root)}[/dim]")

    if files_created:
        files_branch = tree.add("[bold]Files created")
        for f in files_created:
            files_branch.add(f"[green]{f.name}[/green]")

    console.print()
    console.print("[bold green]neoskills workspace initialized![/bold green]")
    console.print(tree)
    console.print(
        f"\n[dim]Total: {len(dirs_created)} dirs, {len(files_created)} files[/dim]"
    )
    console.print("\n[dim]Next: run 'neoskills tap <url>' to add a skill tap.[/dim]")
