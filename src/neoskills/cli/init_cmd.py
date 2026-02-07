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
@click.option(
    "--from-repo",
    "repo_url",
    default=None,
    help="Clone existing skill bank from a GitHub URL",
)
@click.option("--branch", default="main", help="Branch to clone (default: main)")
@click.option("--force", is_flag=True, help="Overwrite existing workspace")
def init(root: str | None, repo_url: str | None, branch: str, force: bool) -> None:
    """Initialize the neoskills workspace (~/.neoskills/)."""
    workspace = Workspace(Path(root) if root else None)

    if repo_url:
        _init_from_repo(workspace, repo_url, branch, force)
        return

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
    console.print(
        f"\n[dim]Total: {len(dirs_created)} dirs, "
        f"{len(memory_created)} memory files, "
        f"{len(configs_created)} config files[/dim]"
    )

    # Init-time validation
    validation = workspace.validate_init()
    if validation["errors"]:
        for err in validation["errors"]:
            console.print(f"  [red]ERROR:[/red] {err}")
    if validation["warnings"]:
        for warn in validation["warnings"]:
            console.print(f"  [yellow]WARN:[/yellow] {warn}")


def _init_from_repo(workspace: Workspace, repo_url: str, branch: str, force: bool) -> None:
    """Clone an existing skill bank repo as the workspace."""
    import git

    if workspace.root.exists() and any(workspace.root.iterdir()):
        if not force:
            console.print(f"[red]Workspace already exists at {workspace.root}[/red]")
            console.print("[dim]Use --force to overwrite.[/dim]")
            raise SystemExit(1)
        import shutil

        console.print(f"[yellow]Removing existing workspace at {workspace.root}...[/yellow]")
        shutil.rmtree(workspace.root)

    console.print(f"[dim]Cloning {repo_url} (branch: {branch})...[/dim]")
    git.Repo.clone_from(repo_url, str(workspace.root), branch=branch)

    # Ensure any missing directories are created
    workspace.initialize()

    # Verify the clone has expected structure
    has_config = workspace.config_file.exists()
    has_registry = workspace.registry_file.exists()
    has_bank = workspace.bank_skills.exists()

    console.print()
    console.print(f"[bold green]Workspace cloned from {repo_url}[/bold green]")
    console.print(f"  Root: {workspace.root}")
    if has_bank:
        skills = [d.name for d in workspace.bank_skills.iterdir() if d.is_dir()]
        console.print(f"  Skills: {len(skills)}")
    console.print(
        f"  Config: {'found' if has_config else '[yellow]missing (created default)[/yellow]'}"
    )
    console.print(
        f"  Registry: {'found' if has_registry else '[yellow]missing (created default)[/yellow]'}"
    )
