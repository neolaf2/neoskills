"""CLI commands: install, uninstall — add/remove skills from tap + link."""

import shutil

import click

from neoskills.core.cellar import Cellar
from neoskills.core.linker import Linker
from neoskills.core.tap import TapManager


@click.command("install")
@click.argument("skill_id")
@click.option("--from", "from_tap", default=None, help="Source tap (if not in default tap).")
@click.option("--target", default=None, help="Target agent (default: from config).")
@click.option("--root", default=None, type=click.Path(), help="Workspace root.")
def brew_install(skill_id: str, from_tap: str | None, target: str | None, root: str | None) -> None:
    """Install a skill (copy to default tap if needed, then link)."""
    from pathlib import Path

    cellar = Cellar(Path(root) if root else None)
    mgr = TapManager(cellar)
    linker = Linker(cellar)
    default_tap = cellar.default_tap

    # Check if skill is already in default tap
    skill_path = mgr.get_skill_path(skill_id, default_tap)

    if skill_path is None and from_tap:
        # Copy from source tap to default tap
        source_path = mgr.get_skill_path(skill_id, from_tap)
        if source_path is None:
            click.echo(f"Skill '{skill_id}' not found in tap '{from_tap}'.")
            raise SystemExit(1)

        dest = cellar.tap_skills_dir(default_tap) / skill_id
        dest.mkdir(parents=True, exist_ok=True)
        for item in source_path.iterdir():
            if item.is_dir():
                shutil.copytree(item, dest / item.name, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dest / item.name)

        # Update source field in frontmatter
        from neoskills.core.frontmatter import parse_frontmatter, write_frontmatter

        skill_md = dest / "SKILL.md"
        if skill_md.exists():
            fm, body = parse_frontmatter(skill_md.read_text())
            fm["source"] = from_tap
            skill_md.write_text(write_frontmatter(fm, body))

        skill_path = dest
        click.echo(f"Copied {skill_id} from {from_tap} → {default_tap}")
    elif skill_path is None:
        # Search all taps
        skill_path = mgr.get_skill_path(skill_id)
        if skill_path is None:
            click.echo(f"Skill '{skill_id}' not found in any tap.")
            raise SystemExit(1)

    # Link to target
    action = linker.link(skill_id, skill_path, target)
    if action.action == "linked":
        click.echo(f"Installed {skill_id} → {action.target}")
    elif action.action == "skipped":
        click.echo(f"{skill_id} already linked")
    else:
        click.echo(f"{skill_id}: {action.action}")


@click.command()
@click.argument("skill_id")
@click.option("--target", default=None, help="Target agent.")
@click.option("--keep", is_flag=True, help="Keep in tap, only unlink.")
@click.option("--root", default=None, type=click.Path(), help="Workspace root.")
def uninstall(skill_id: str, target: str | None, keep: bool, root: str | None) -> None:
    """Uninstall a skill (unlink, optionally remove from tap)."""
    from pathlib import Path

    cellar = Cellar(Path(root) if root else None)
    linker = Linker(cellar)

    # Unlink from target
    action = linker.unlink(skill_id, target)
    if action.action == "unlinked":
        click.echo(f"Unlinked {skill_id}")
    else:
        click.echo(f"{skill_id} was not linked")

    if not keep:
        # Remove from default tap
        skill_dir = cellar.default_tap_skills_dir / skill_id
        if skill_dir.exists():
            shutil.rmtree(skill_dir)
            click.echo(f"Removed {skill_id} from {cellar.default_tap}")
