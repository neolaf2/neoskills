"""CLI command: doctor — health check for the skill system."""

import click

from neoskills.core.cellar import Cellar
from neoskills.core.linker import Linker
from neoskills.core.tap import TapManager


@click.command()
@click.option("--target", default=None, help="Target agent to check.")
@click.option("--root", default=None, type=click.Path(), help="Workspace root.")
def doctor(target: str | None, root: str | None) -> None:
    """Check skill system health (broken links, missing frontmatter, orphans)."""
    from pathlib import Path

    cellar = Cellar(Path(root) if root else None)
    mgr = TapManager(cellar)
    linker = Linker(cellar)
    issues = 0

    # 1. Check workspace
    if not cellar.is_initialized:
        click.echo("Warning: Workspace not initialized. Run 'neoskills init'.")
        issues += 1

    # 2. Check taps
    taps = mgr.list_taps()
    if not taps:
        click.echo("Warning: No taps registered. Run 'neoskills tap <url>'.")
        issues += 1
    else:
        click.echo(f"Taps: {len(taps)} registered ({', '.join(taps)})")

    # 3. Check skills in default tap
    default_tap = cellar.default_tap
    if default_tap in taps:
        skills = mgr.list_skills(default_tap)
        missing_desc = [s for s in skills if not s["description"]]
        click.echo(f"Skills in {default_tap}: {len(skills)}")
        if missing_desc:
            click.echo(f"  Warning: {len(missing_desc)} skill(s) missing description:")
            for s in missing_desc[:5]:
                click.echo(f"    - {s['skill_id']}")
            if len(missing_desc) > 5:
                click.echo(f"    ... and {len(missing_desc) - 5} more")
            issues += len(missing_desc)

    # 4. Check symlink health
    health = linker.check_health(target)
    click.echo(f"Links: {health['total']} total, {health['healthy']} healthy")

    if health["broken"]:
        click.echo(f"  Broken links ({len(health['broken'])}):")
        for b in health["broken"]:
            click.echo(f"    - {b['skill_id']} → {b['source']}")
        issues += len(health["broken"])

    if health["unmanaged"]:
        click.echo(f"  Unmanaged symlinks ({len(health['unmanaged'])}):")
        for u in health["unmanaged"]:
            click.echo(f"    - {u['skill_id']} → {u['source']}")

    if health["local"]:
        click.echo(f"  Local (non-symlink) skills: {len(health['local'])}")

    # 5. Check for unlinked tap skills
    if default_tap in taps:
        skills = mgr.list_skills(default_tap)
        links = linker.list_links(target)
        linked_ids = {l["skill_id"] for l in links}
        unlinked = [s for s in skills if s["skill_id"] not in linked_ids]
        if unlinked:
            click.echo(f"  Unlinked skills in {default_tap}: {len(unlinked)}")

    # Summary
    if issues == 0:
        click.echo("System is healthy.")
    else:
        click.echo(f"\n{issues} issue(s) found.")
