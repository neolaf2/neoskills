"""CLI command: create — scaffold a new skill in the default tap."""

import click

from neoskills.core.cellar import Cellar
from neoskills.core.frontmatter import write_frontmatter


@click.command()
@click.argument("skill_id")
@click.option("--description", "-d", default="", help="Skill description.")
@click.option("--author", "-a", default="", help="Author name.")
@click.option("--tags", "-t", default="first-party", help="Comma-separated tags.")
@click.option("--root", default=None, type=click.Path(), help="Workspace root.")
def create(skill_id: str, description: str, author: str, tags: str, root: str | None) -> None:
    """Scaffold a new skill in the default tap."""
    from pathlib import Path

    cellar = Cellar(Path(root) if root else None)
    skill_dir = cellar.default_tap_skills_dir / skill_id

    if skill_dir.exists():
        click.echo(f"Skill '{skill_id}' already exists at {skill_dir}")
        raise SystemExit(1)

    skill_dir.mkdir(parents=True)

    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    fm = {
        "name": skill_id,
        "description": description or f"TODO: describe {skill_id}",
        "author": author,
        "tags": tag_list,
        "targets": ["claude-code"],
    }

    body = f"# {skill_id.replace('-', ' ').title()}\n\nTODO: Add skill content here.\n"
    (skill_dir / "SKILL.md").write_text(write_frontmatter(fm, body))

    click.echo(f"Created {skill_id} at {skill_dir}")
    click.echo(f"  Edit: {skill_dir / 'SKILL.md'}")
