"""neoskills init - create the full .neoskills/ workspace."""

from pathlib import Path

import click
from rich.console import Console
from rich.tree import Tree

from neoskills.core.workspace import Workspace

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
    workspace = Workspace(Path(root) if root else None)

    if workspace.is_initialized:
        console.print(f"[yellow]Workspace already exists at {workspace.root}[/yellow]")
        console.print("Checking for missing directories and files...")

    result = workspace.initialize()

    # Display results
    dirs_created = result["directories"]
    memory_created = result["memory_files"]
    configs_created = result["config_files"]

    total = len(dirs_created) + len(memory_created) + len(configs_created)

    if total == 0:
        console.print("[green]Workspace is up to date. Nothing to create.[/green]")
        return

    tree = Tree(f"[bold cyan]{workspace.root}[/bold cyan]")

    if dirs_created:
        dirs_branch = tree.add("[bold]Directories created")
        for d in dirs_created:
            dirs_branch.add(f"[dim]{d.relative_to(workspace.root)}[/dim]")

    if memory_created:
        mem_branch = tree.add("[bold]myMemory templates")
        for f in memory_created:
            mem_branch.add(f"[green]{f.name}[/green]")

    if configs_created:
        cfg_branch = tree.add("[bold]Config files")
        for f in configs_created:
            cfg_branch.add(f"[blue]{f.name}[/blue]")

    console.print()
    console.print("[bold green]neoskills workspace initialized![/bold green]")
    console.print(tree)
    console.print(f"\n[dim]Total: {len(dirs_created)} dirs, "
                  f"{len(memory_created)} memory files, "
                  f"{len(configs_created)} config files[/dim]")
