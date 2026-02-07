"""CLI commands: tap, untap — manage tap repositories."""

import re

import click

from neoskills.core.cellar import Cellar
from neoskills.core.tap import TapManager


def _name_from_url(url: str) -> str:
    """Derive a tap name from a git URL."""
    # github.com/user/mySkills.git → mySkills
    match = re.search(r"/([^/]+?)(?:\.git)?$", url.rstrip("/"))
    return match.group(1) if match else "unknown"


@click.command()
@click.argument("url")
@click.option("--name", default=None, help="Tap name (derived from URL if omitted).")
@click.option("--branch", default="main", help="Git branch.")
@click.option("--root", default=None, type=click.Path(), help="Workspace root.")
def tap(url: str, name: str | None, branch: str, root: str | None) -> None:
    """Register a tap (clone a skill repository)."""
    from pathlib import Path

    cellar = Cellar(Path(root) if root else None)
    if not cellar.is_initialized:
        cellar.initialize()

    tap_name = name or _name_from_url(url)
    mgr = TapManager(cellar)

    try:
        tap_dir = mgr.add(tap_name, url, branch)
        skills = mgr.list_skills(tap_name)
        click.echo(f"Tapped {tap_name} ({url}) → {tap_dir}")
        click.echo(f"  {len(skills)} skills available")
    except FileExistsError:
        click.echo(f"Tap '{tap_name}' already exists. Use 'neoskills untap {tap_name}' first.")
        raise SystemExit(1)
    except Exception as exc:
        click.echo(f"Failed to tap {url}: {exc}")
        raise SystemExit(1)


@click.command()
@click.argument("name")
@click.option("--root", default=None, type=click.Path(), help="Workspace root.")
def untap(name: str, root: str | None) -> None:
    """Remove a tap repository."""
    from pathlib import Path

    cellar = Cellar(Path(root) if root else None)
    mgr = TapManager(cellar)

    if mgr.remove(name):
        click.echo(f"Untapped {name}")
    else:
        click.echo(f"Tap '{name}' not found.")
        raise SystemExit(1)
