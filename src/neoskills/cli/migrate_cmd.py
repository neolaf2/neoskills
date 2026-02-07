"""CLI command: migrate — one-time migration from v0.2 bank structure to v0.3 taps."""

import shutil
from pathlib import Path

import click
import yaml

from neoskills.core.cellar import Cellar
from neoskills.core.frontmatter import parse_frontmatter, write_frontmatter


def _migrate_skill(
    skill_id: str,
    old_skill_dir: Path,
    new_skills_dir: Path,
    dry_run: bool,
) -> dict:
    """Migrate one skill from LTM/bank/skills/{id}/canonical/ to taps/{tap}/skills/{id}/."""
    canonical = old_skill_dir / "canonical"
    if not canonical.exists():
        return {"skill_id": skill_id, "action": "skipped", "reason": "no canonical/"}

    new_dir = new_skills_dir / skill_id

    # Read existing SKILL.md
    skill_md = canonical / "SKILL.md"
    if not skill_md.exists():
        return {"skill_id": skill_id, "action": "skipped", "reason": "no SKILL.md"}

    fm, body = parse_frontmatter(skill_md.read_text())

    # Merge metadata.yaml fields into frontmatter
    meta_file = old_skill_dir / "metadata.yaml"
    if meta_file.exists():
        try:
            meta = yaml.safe_load(meta_file.read_text()) or {}
            fm.setdefault("version", meta.get("version", ""))
            fm.setdefault("author", meta.get("author", ""))
            if meta.get("tags") and not fm.get("tags"):
                fm["tags"] = meta["tags"]
            if meta.get("format") and meta["format"] != "canonical":
                existing_tags = fm.get("tags", [])
                if isinstance(existing_tags, list):
                    fm["tags"] = existing_tags
        except Exception:
            pass

    # Merge provenance.yaml source info
    prov_file = old_skill_dir / "provenance.yaml"
    if prov_file.exists():
        try:
            prov = yaml.safe_load(prov_file.read_text()) or {}
            if prov.get("source_type") and not fm.get("source"):
                fm["source"] = prov.get("source_type", "")
        except Exception:
            pass

    if dry_run:
        return {"skill_id": skill_id, "action": "would_migrate", "fields_added": list(fm.keys())}

    # Copy canonical/ contents to new flat directory
    if new_dir.exists():
        shutil.rmtree(new_dir)
    shutil.copytree(canonical, new_dir)

    # Write enriched SKILL.md
    (new_dir / "SKILL.md").write_text(write_frontmatter(fm, body))

    return {"skill_id": skill_id, "action": "migrated"}


@click.command()
@click.option("--root", default=None, type=click.Path(), help="Workspace root.")
@click.option("--tap-name", default="mySkills", help="Name for the default tap.")
@click.option("--dry-run", is_flag=True, help="Preview without making changes.")
def migrate(root: str | None, tap_name: str, dry_run: bool) -> None:
    """Migrate from v0.2 bank structure to v0.3 taps structure."""
    old_root = Path(root).expanduser() if root else Path.home() / ".neoskills"
    old_bank = old_root / "LTM" / "bank" / "skills"

    if not old_bank.exists():
        click.echo(f"No v0.2 bank found at {old_bank}")
        click.echo("Nothing to migrate.")
        return

    cellar = Cellar(old_root)

    # Count old skills
    old_skills = [
        d for d in old_bank.iterdir()
        if d.is_dir() and (d / "canonical" / "SKILL.md").exists()
    ]
    click.echo(f"Found {len(old_skills)} skills in v0.2 bank")

    if dry_run:
        click.echo(f"\n--- DRY RUN (no changes will be made) ---\n")

    # Step 1: Create new directory structure
    taps_dir = old_root / "taps"
    tap_dir = taps_dir / tap_name
    new_skills_dir = tap_dir / "skills"

    if not dry_run:
        taps_dir.mkdir(parents=True, exist_ok=True)
        tap_dir.mkdir(parents=True, exist_ok=True)
        new_skills_dir.mkdir(parents=True, exist_ok=True)
        (old_root / "cache").mkdir(parents=True, exist_ok=True)

        # Create tap.yaml
        tap_yaml = {
            "name": tap_name,
            "description": "Personal skill library (migrated from v0.2)",
            "version": "1.0.0",
        }
        (tap_dir / "tap.yaml").write_text(yaml.dump(tap_yaml, default_flow_style=False))
    click.echo(f"{'Would create' if dry_run else 'Created'} tap: {tap_dir}")

    # Step 2: Migrate each skill
    migrated = 0
    skipped = 0
    for old_skill_dir in sorted(old_skills):
        result = _migrate_skill(old_skill_dir.name, old_skill_dir, new_skills_dir, dry_run)
        if result["action"] in ("migrated", "would_migrate"):
            migrated += 1
        else:
            skipped += 1
            click.echo(f"  Skipped {result['skill_id']}: {result.get('reason', '')}")

    click.echo(f"\n{'Would migrate' if dry_run else 'Migrated'} {migrated} skills ({skipped} skipped)")

    # Step 3: Update config.yaml
    if not dry_run:
        config = cellar.load_config()
        config["version"] = "0.3.0"
        config["default_tap"] = tap_name
        config["default_target"] = config.pop("default_target", "claude-code-user").replace("-user", "")
        config.setdefault("targets", {
            "claude-code": {"skill_path": "~/.claude/skills"},
            "opencode": {"skill_path": "~/.config/opencode/skills"},
        })
        config.setdefault("taps", {})
        config["taps"][tap_name] = {"default": True}
        cellar.save_config(config)
        click.echo("Updated config.yaml")

    # Step 4: Re-create symlinks
    if not dry_run:
        from neoskills.core.linker import Linker
        linker = Linker(cellar)
        actions = linker.link_all(new_skills_dir)
        linked = sum(1 for a in actions if a.action == "linked")
        click.echo(f"Linked {linked} skills to {cellar.target_path()}")

    if dry_run:
        click.echo(f"\nRun without --dry-run to execute migration.")
    else:
        click.echo(f"\nMigration complete. Old structure at {old_bank} can be archived.")
        click.echo("Run 'neoskills doctor' to verify health.")
