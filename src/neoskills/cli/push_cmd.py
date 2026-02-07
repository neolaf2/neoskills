"""CLI command: push — commit and push tap changes to remote."""

import click

from neoskills.core.cellar import Cellar


@click.command()
@click.option("--tap", "tap_name", default=None, help="Tap to push (default: default tap).")
@click.option("-m", "--message", default=None, help="Commit message.")
@click.option("--root", default=None, type=click.Path(), help="Workspace root.")
def push(tap_name: str | None, message: str | None, root: str | None) -> None:
    """Commit and push tap changes to GitHub."""
    import git
    from pathlib import Path

    cellar = Cellar(Path(root) if root else None)
    tap_name = tap_name or cellar.default_tap
    tap_dir = cellar.tap_dir(tap_name)

    if not tap_dir.exists():
        click.echo(f"Tap '{tap_name}' not found.")
        raise SystemExit(1)

    try:
        repo = git.Repo(tap_dir)
    except git.InvalidGitRepositoryError:
        click.echo(f"Tap '{tap_name}' is not a git repository.")
        raise SystemExit(1)

    # Check for changes
    if not repo.is_dirty(untracked_files=True):
        click.echo(f"No changes in {tap_name}.")
        return

    # Stage all changes in skills/ and plugins/
    repo.git.add("skills/", "plugins/", "tap.yaml", "README.md", catch_exceptions=False)

    # Commit
    msg = message or f"Update skills in {tap_name}"
    repo.index.commit(msg)
    click.echo(f"Committed: {msg}")

    # Push
    try:
        origin = repo.remotes.origin
        origin.push()
        click.echo(f"Pushed {tap_name} to {origin.url}")
    except Exception as exc:
        click.echo(f"Push failed: {exc}")
        click.echo("Changes are committed locally.")
