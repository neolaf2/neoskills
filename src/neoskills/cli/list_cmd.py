"""CLI commands: list, search, info — query installed and available skills."""

import click

from neoskills.core.cellar import Cellar
from neoskills.core.linker import Linker
from neoskills.core.models import SkillSpec
from neoskills.core.tap import TapManager


@click.command("list")
@click.option("--linked", is_flag=True, help="Show only linked skills.")
@click.option("--available", is_flag=True, help="Show all skills in default tap.")
@click.option("--target", default=None, help="Target agent.")
@click.option("--tap", "tap_name", default=None, help="Tap to list from.")
@click.option("--root", default=None, type=click.Path(), help="Workspace root.")
def list_skills(
    linked: bool, available: bool, target: str | None, tap_name: str | None, root: str | None
) -> None:
    """List installed and/or linked skills."""
    from pathlib import Path

    cellar = Cellar(Path(root) if root else None)
    mgr = TapManager(cellar)
    linker = Linker(cellar)

    if linked:
        links = linker.list_links(target)
        managed = [l for l in links if l["managed"]]
        click.echo(f"Linked skills ({len(managed)} managed):")
        for l in links:
            status = "→" if l["linked"] else " "
            flag = " [broken]" if l["broken"] else ""
            flag += " [unmanaged]" if l["linked"] and not l["managed"] else ""
            click.echo(f"  {status} {l['skill_id']}{flag}")
        return

    if available or tap_name:
        skills = mgr.list_skills(tap_name)
        click.echo(f"Available skills in {tap_name or cellar.default_tap} ({len(skills)}):")
        for s in skills:
            tags = ", ".join(s["tags"][:3]) if s["tags"] else ""
            click.echo(f"  {s['skill_id']:40s} {tags}")
        return

    # Default: show tap skills with link status
    tap = tap_name or cellar.default_tap
    skills = mgr.list_skills(tap)
    links = linker.list_links(target)
    linked_ids = {l["skill_id"] for l in links if l["linked"]}

    click.echo(f"Skills in {tap} ({len(skills)} total, {len(linked_ids)} linked):")
    for s in skills:
        marker = "●" if s["skill_id"] in linked_ids else "○"
        click.echo(f"  {marker} {s['skill_id']}")


@click.command()
@click.argument("query")
@click.option("--root", default=None, type=click.Path(), help="Workspace root.")
def search(query: str, root: str | None) -> None:
    """Search for skills across all taps."""
    from pathlib import Path

    cellar = Cellar(Path(root) if root else None)
    mgr = TapManager(cellar)

    results = mgr.search(query)
    if not results:
        click.echo(f"No skills matching '{query}'")
        return

    click.echo(f"Found {len(results)} skill(s) matching '{query}':")
    for s in results:
        tags = ", ".join(s["tags"][:3]) if s["tags"] else ""
        click.echo(f"  {s['skill_id']:40s} [{s['tap']}] {tags}")


@click.command()
@click.argument("skill_id")
@click.option("--root", default=None, type=click.Path(), help="Workspace root.")
def info(skill_id: str, root: str | None) -> None:
    """Show detailed info for a skill."""
    from pathlib import Path

    cellar = Cellar(Path(root) if root else None)
    mgr = TapManager(cellar)
    linker = Linker(cellar)

    skill_path = mgr.get_skill_path(skill_id)
    if skill_path is None:
        click.echo(f"Skill '{skill_id}' not found.")
        raise SystemExit(1)

    spec = SkillSpec.from_skill_dir(skill_path)

    # Check link status
    links = linker.list_links()
    link_info = next((l for l in links if l["skill_id"] == skill_id), None)

    click.echo(f"Name:        {spec.name}")
    click.echo(f"Description: {spec.description}")
    if spec.version:
        click.echo(f"Version:     {spec.version}")
    if spec.author:
        click.echo(f"Author:      {spec.author}")
    if spec.tags:
        click.echo(f"Tags:        {', '.join(spec.tags)}")
    if spec.targets:
        click.echo(f"Targets:     {', '.join(spec.targets)}")
    if spec.source:
        click.echo(f"Source:      {spec.source}")
    click.echo(f"Path:        {skill_path}")
    if link_info:
        click.echo(f"Linked:      yes → {link_info['source']}")
    else:
        click.echo("Linked:      no")
