"""neoskills sync - git operations on the .neoskills/ workspace."""

import click
from rich.console import Console

from neoskills.core.workspace import Workspace

console = Console()

# Paths that should be staged when committing (relative to workspace root).
# Everything else (e.g. .env, scratch files) is excluded.
_SAFE_PATHS = ["LTM/", "registry.yaml", "config.yaml", "state.yaml", ".gitignore"]


def _get_branch(repo) -> str:
    """Get current branch name, handling detached HEAD gracefully."""
    if repo.head.is_detached:
        return ""
    return repo.active_branch.name


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
        console.print("Run 'neoskills sync commit' to initialize, or 'git init' in ~/.neoskills/.")
        return

    if repo.is_dirty(untracked_files=True):
        console.print("[yellow]Workspace has uncommitted changes:[/yellow]")
        for item in repo.untracked_files:
            console.print(f"  [green]+ {item}[/green]")
        for item in repo.index.diff(None):
            console.print(f"  [yellow]~ {item.a_path}[/yellow]")
        try:
            for item in repo.index.diff("HEAD"):
                console.print(f"  [cyan]S {item.a_path}[/cyan]")
        except git.BadName:
            pass  # No HEAD yet
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
    if not ws.is_initialized:
        console.print("[red]Workspace not initialized.[/red]")
        raise SystemExit(1)

    try:
        repo = git.Repo(ws.root)
    except git.InvalidGitRepositoryError:
        console.print(f"[yellow]Initializing git in {ws.root}...[/yellow]")
        repo = git.Repo.init(ws.root)

    # Stage only safe paths (never .env or secrets)
    for path_spec in _SAFE_PATHS:
        full = ws.root / path_spec
        if full.exists():
            repo.git.add(path_spec)

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
    if not ws.is_initialized:
        console.print("[red]Workspace not initialized.[/red]")
        raise SystemExit(1)

    try:
        repo = git.Repo(ws.root)
    except git.InvalidGitRepositoryError:
        console.print(f"[red]{ws.root} is not a git repository.[/red]")
        raise SystemExit(1)

    if remote not in [r.name for r in repo.remotes]:
        console.print(f"[red]Remote '{remote}' not found.[/red]")
        console.print("Add one with: git -C ~/.neoskills remote add origin <url>")
        raise SystemExit(1)

    if not branch:
        branch = _get_branch(repo)
        if not branch:
            console.print("[red]Cannot push: HEAD is detached. Specify --branch explicitly.[/red]")
            raise SystemExit(1)

    try:
        repo.remotes[remote].push(branch)
        console.print(f"[green]Pushed to {remote}/{branch}[/green]")
    except git.GitCommandError as e:
        console.print(f"[red]Push failed:[/red] {e.stderr.strip() if e.stderr else e}")
        raise SystemExit(1)


@sync.command("pull")
@click.option("--remote", default="origin", help="Remote name")
@click.option("--branch", default=None, help="Branch name (default: current)")
def sync_pull(remote: str, branch: str | None) -> None:
    """Pull latest from remote."""
    import git

    ws = Workspace()
    if not ws.is_initialized:
        console.print("[red]Workspace not initialized.[/red]")
        raise SystemExit(1)

    try:
        repo = git.Repo(ws.root)
    except git.InvalidGitRepositoryError:
        console.print(f"[red]{ws.root} is not a git repository.[/red]")
        raise SystemExit(1)

    if remote not in [r.name for r in repo.remotes]:
        console.print(f"[red]Remote '{remote}' not found.[/red]")
        raise SystemExit(1)

    if not branch:
        branch = _get_branch(repo)
        if not branch:
            console.print("[red]Cannot pull: HEAD is detached. Specify --branch explicitly.[/red]")
            raise SystemExit(1)

    try:
        repo.remotes[remote].pull(branch)
        console.print(f"[green]Pulled from {remote}/{branch}[/green]")
    except git.GitCommandError as e:
        stderr = e.stderr.strip() if e.stderr else str(e)
        if "CONFLICT" in stderr or "conflict" in stderr.lower():
            console.print("[red]Pull failed: merge conflict.[/red]")
            console.print("[dim]Resolve conflicts in ~/.neoskills/ then run 'neoskills sync commit'.[/dim]")
        else:
            console.print(f"[red]Pull failed:[/red] {stderr}")
        raise SystemExit(1)
