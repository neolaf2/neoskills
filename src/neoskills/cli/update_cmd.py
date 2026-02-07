"""CLI commands: update, upgrade — sync taps and refresh skills."""

import click

from neoskills.core.cellar import Cellar
from neoskills.core.linker import Linker
from neoskills.core.tap import TapManager


@click.command()
@click.argument("tap_name", required=False)
@click.option("--root", default=None, type=click.Path(), help="Workspace root.")
def update(tap_name: str | None, root: str | None) -> None:
    """Pull latest from tap repositories (git pull)."""
    from pathlib import Path

    cellar = Cellar(Path(root) if root else None)
    mgr = TapManager(cellar)

    updated = mgr.update(tap_name)
    if updated:
        click.echo(f"Updated {len(updated)} tap(s): {', '.join(updated)}")
    else:
        click.echo("No taps to update.")


@click.command()
@click.argument("skill_id", required=False)
@click.option("--target", default=None, help="Target agent.")
@click.option("--root", default=None, type=click.Path(), help="Workspace root.")
def upgrade(skill_id: str | None, target: str | None, root: str | None) -> None:
    """Update taps then verify/refresh symlinks."""
    from pathlib import Path

    cellar = Cellar(Path(root) if root else None)
    mgr = TapManager(cellar)
    linker = Linker(cellar)

    # First update taps
    mgr.update()

    # Then check health
    health = linker.check_health(target)
    broken = health["broken"]

    if broken:
        click.echo(f"Found {len(broken)} broken links — attempting repair:")
        for b in broken:
            click.echo(f"  Broken: {b['skill_id']}")
            linker.unlink(b["skill_id"], target)
    else:
        click.echo(f"All {health['healthy']} linked skills up to date")
