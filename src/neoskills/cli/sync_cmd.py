"""neoskills sync - git operations on the .neoskills/ workspace."""

import click
from rich.console import Console

from neoskills.core.workspace import Workspace

console = Console()


@click.group()
def sync() -> None:
    """Sync the skill bank with git."""


@sync.command("status")
def sync_status() -> None:
    """Show git status of the workspace."""
    import git

    ws = Workspace()
    if not ws.is_initialized:
        console.print("[red]Workspace not initialized.[/red]")
        raise SystemExit(1)

    try:
        repo = git.Repo(ws.root)
    except git.InvalidGitRepositoryError:
        console.print(f"[yellow]{ws.root} is not a git repository.[/yellow]")
        console.print("Run 'neoskills sync init' or 'git init' in ~/.neoskills/ first.")
        return

    if repo.is_dirty(untracked_files=True):
        console.print("[yellow]Workspace has uncommitted changes:[/yellow]")
        for item in repo.untracked_files:
            console.print(f"  [green]+ {item}[/green]")
        for item in repo.index.diff(None):
            console.print(f"  [yellow]~ {item.a_path}[/yellow]")
        for item in repo.index.diff("HEAD"):
            console.print(f"  [cyan]S {item.a_path}[/cyan]")
    else:
        console.print("[green]Workspace is clean.[/green]")

    if repo.remotes:
        console.print(f"[dim]Remote: {repo.remotes[0].url}[/dim]")
    else:
        console.print("[dim]No remote configured.[/dim]")


@sync.command("commit")
@click.option("-m", "--message", default="Update skill bank", help="Commit message")
def sync_commit(message: str) -> None:
    """Commit all changes in the workspace."""
    import git

    ws = Workspace()
    try:
        repo = git.Repo(ws.root)
    except git.InvalidGitRepositoryError:
        console.print(f"[yellow]Initializing git in {ws.root}...[/yellow]")
        repo = git.Repo.init(ws.root)

    repo.git.add(A=True)

    try:
        has_staged = bool(repo.index.diff("HEAD"))
    except git.BadName:
        # No HEAD yet (first commit)
        has_staged = bool(repo.index.entries)
    if not has_staged:
        console.print("[green]Nothing to commit.[/green]")
        return

    repo.index.commit(message)
    console.print(f"[green]Committed: {message}[/green]")


@sync.command("push")
@click.option("--remote", default="origin", help="Remote name")
@click.option("--branch", default=None, help="Branch name (default: current)")
def sync_push(remote: str, branch: str | None) -> None:
    """Push workspace to remote."""
    import git

    ws = Workspace()
    repo = git.Repo(ws.root)

    if remote not in [r.name for r in repo.remotes]:
        console.print(f"[red]Remote '{remote}' not found.[/red]")
        console.print("Add one with: git -C ~/.neoskills remote add origin <url>")
        raise SystemExit(1)

    branch = branch or repo.active_branch.name
    repo.remotes[remote].push(branch)
    console.print(f"[green]Pushed to {remote}/{branch}[/green]")


@sync.command("pull")
@click.option("--remote", default="origin", help="Remote name")
@click.option("--branch", default=None, help="Branch name (default: current)")
def sync_pull(remote: str, branch: str | None) -> None:
    """Pull latest from remote."""
    import git

    ws = Workspace()
    repo = git.Repo(ws.root)

    if remote not in [r.name for r in repo.remotes]:
        console.print(f"[red]Remote '{remote}' not found.[/red]")
        raise SystemExit(1)

    branch = branch or repo.active_branch.name
    repo.remotes[remote].pull(branch)
    console.print(f"[green]Pulled from {remote}/{branch}[/green]")
