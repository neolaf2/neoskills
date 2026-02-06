"""neoskills import - import skills into the bank."""

import shutil
import tempfile
from datetime import datetime
from pathlib import Path

import click
from rich.console import Console

from neoskills.adapters.factory import get_adapter
from neoskills.bank.provenance import ProvenanceTracker
from neoskills.bank.registry import Registry
from neoskills.bank.store import SkillStore
from neoskills.core.checksum import checksum_string
from neoskills.core.models import Provenance, SkillFormat
from neoskills.core.workspace import Workspace
from neoskills.mappings.resolver import SymlinkResolver
from neoskills.mappings.target import TargetManager

console = Console()


def _auto_embed(ws: Workspace, skill_ids: list[str]) -> None:
    """Symlink imported skills to default target (best-effort)."""
    import yaml as _yaml

    cfg = _yaml.safe_load(ws.config_file.read_text()) if ws.config_file.exists() else {}
    target_id = cfg.get("default_target", "claude-code-user")

    mgr = TargetManager(ws)
    mgr.ensure_builtins()
    target = mgr.get(target_id)
    if not target or not target.install_paths:
        return

    install_base = Path(target.install_paths[0]).expanduser()
    store = SkillStore(ws)
    resolver = SymlinkResolver(ws)
    actions = []

    for sid in skill_ids:
        variant_dir = store.variant_dir(sid, target.agent_type)
        canonical = store.canonical_dir(sid)
        bank_path = variant_dir if (variant_dir / "SKILL.md").exists() else canonical
        if not bank_path.exists():
            continue
        agent_path = install_base / sid
        action = resolver.create_symlink(sid, bank_path, agent_path)
        actions.append(action)

    if actions:
        resolver.save_state(actions)
        console.print(f"  [dim]Auto-embedded {len(actions)} skill(s) into '{target_id}'[/dim]")


@click.group("import")
def import_skills() -> None:
    """Import skills into the bank."""


@import_skills.command("from-target")
@click.argument("target_id")
@click.option("--skill", "skill_ids", multiple=True, help="Specific skill ID(s) to import")
@click.option("--all", "import_all", is_flag=True, help="Import all discovered skills")
@click.option("--no-embed", is_flag=True, help="Import to bank only, skip auto-embed")
def from_target(target_id: str, skill_ids: tuple[str, ...], import_all: bool, no_embed: bool) -> None:
    """Import skills from a configured target."""
    ws = Workspace()
    if not ws.is_initialized:
        console.print("[red]Workspace not initialized. Run 'neoskills init' first.[/red]")
        raise SystemExit(1)

    mgr = TargetManager(ws)
    mgr.ensure_builtins()
    target = mgr.get(target_id)
    if not target:
        console.print(f"[red]Target '{target_id}' not found.[/red]")
        raise SystemExit(1)

    adapter = get_adapter(target.agent_type)
    store = SkillStore(ws)
    registry = Registry(ws)
    prov_tracker = ProvenanceTracker(ws.bank_skills)

    # Determine which skills to import
    if import_all:
        discovered = adapter.discover(target)
        ids_to_import = [s.skill_id for s in discovered]
    elif skill_ids:
        ids_to_import = list(skill_ids)
    else:
        console.print("[yellow]Specify --skill <id> or --all[/yellow]")
        return

    # Export and import
    exported = adapter.export(target, ids_to_import)
    if not exported:
        console.print("[yellow]No skills found to import.[/yellow]")
        return

    format_map = {
        "claude-code": SkillFormat.CLAUDE_CODE,
        "opencode": SkillFormat.OPENCODE,
        "openclaw": SkillFormat.OPENCLAW,
    }
    source_format = format_map.get(target.agent_type, SkillFormat.CANONICAL)

    imported = 0
    for skill_id, content in exported:
        skill = store.add(skill_id, content, source_format=source_format)
        registry.register(skill)

        # Record provenance
        prov = Provenance(
            skill_id=skill_id,
            source_type="target",
            source_location=str(target.discovery_paths),
            source_target=target_id,
            imported_at=datetime.now(),
            original_checksum=checksum_string(content),
        )
        prov_tracker.record(prov)
        imported += 1
        console.print(f"  [green]+[/green] {skill_id}")

    console.print(f"\n[bold green]Imported {imported} skill(s) from '{target_id}'[/bold green]")

    if not no_embed and imported:
        _auto_embed(ws, [sid for sid, _ in exported])


@import_skills.command("from-git")
@click.argument("url")
@click.option("--skill", "skill_ids", multiple=True, help="Specific skill ID(s) to import")
@click.option("--branch", default="main", help="Git branch")
@click.option("--no-embed", is_flag=True, help="Import to bank only, skip auto-embed")
def from_git(url: str, skill_ids: tuple[str, ...], branch: str, no_embed: bool) -> None:
    """Import skills from a git repository."""
    import git

    ws = Workspace()
    if not ws.is_initialized:
        console.print("[red]Workspace not initialized. Run 'neoskills init' first.[/red]")
        raise SystemExit(1)

    store = SkillStore(ws)
    registry = Registry(ws)
    prov_tracker = ProvenanceTracker(ws.bank_skills)

    with tempfile.TemporaryDirectory() as tmpdir:
        console.print(f"[dim]Cloning {url} (branch: {branch})...[/dim]")
        git.Repo.clone_from(url, tmpdir, branch=branch, depth=1)

        # Find skills (directories with SKILL.md)
        tmppath = Path(tmpdir)
        skill_dirs = []
        for skill_md in tmppath.rglob("SKILL.md"):
            skill_dir = skill_md.parent
            sid = skill_dir.name
            if skill_ids and sid not in skill_ids:
                continue
            skill_dirs.append((sid, skill_md))

        if not skill_dirs:
            console.print("[yellow]No SKILL.md files found in repository.[/yellow]")
            return

        imported = 0
        for skill_id, skill_file in skill_dirs:
            content = skill_file.read_text()
            skill = store.add(skill_id, content)
            registry.register(skill)

            prov = Provenance(
                skill_id=skill_id,
                source_type="git",
                source_location=url,
                imported_at=datetime.now(),
                original_checksum=checksum_string(content),
                notes=f"branch: {branch}",
            )
            prov_tracker.record(prov)
            imported += 1
            console.print(f"  [green]+[/green] {skill_id}")

    console.print(f"\n[bold green]Imported {imported} skill(s) from git[/bold green]")

    if not no_embed and imported:
        _auto_embed(ws, [sid for sid, _ in skill_dirs])


@import_skills.command("from-web")
@click.argument("url")
@click.option("--skill-id", default=None, help="Override skill ID")
@click.option("--no-embed", is_flag=True, help="Import to bank only, skip auto-embed")
def from_web(url: str, skill_id: str | None, no_embed: bool) -> None:
    """Import a skill from a web URL (raw file or zip)."""
    import urllib.request

    ws = Workspace()
    if not ws.is_initialized:
        console.print("[red]Workspace not initialized. Run 'neoskills init' first.[/red]")
        raise SystemExit(1)

    store = SkillStore(ws)
    registry = Registry(ws)
    prov_tracker = ProvenanceTracker(ws.bank_skills)

    console.print(f"[dim]Fetching {url}...[/dim]")

    if url.endswith(".zip"):
        # Download and extract zip
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "download.zip"
            urllib.request.urlretrieve(url, zip_path)
            shutil.unpack_archive(zip_path, tmpdir)

            # Find SKILL.md files
            imported_ids = []
            for skill_md in Path(tmpdir).rglob("SKILL.md"):
                sid = skill_id or skill_md.parent.name
                content = skill_md.read_text()
                skill = store.add(sid, content)
                registry.register(skill)
                prov = Provenance(
                    skill_id=sid,
                    source_type="web",
                    source_location=url,
                    imported_at=datetime.now(),
                    original_checksum=checksum_string(content),
                )
                prov_tracker.record(prov)
                imported_ids.append(sid)
                console.print(f"  [green]+[/green] {sid}")

            console.print(f"\n[bold green]Imported {len(imported_ids)} skill(s) from zip[/bold green]")

            if not no_embed and imported_ids:
                _auto_embed(ws, imported_ids)
    else:
        # Single file URL
        with urllib.request.urlopen(url) as resp:
            content = resp.read().decode("utf-8")

        sid = skill_id or Path(url).stem
        skill = store.add(sid, content)
        registry.register(skill)
        prov = Provenance(
            skill_id=sid,
            source_type="web",
            source_location=url,
            imported_at=datetime.now(),
            original_checksum=checksum_string(content),
        )
        prov_tracker.record(prov)
        console.print(f"  [green]+[/green] {sid}")
        console.print(f"\n[bold green]Imported '{sid}' from URL[/bold green]")

        if not no_embed:
            _auto_embed(ws, [sid])
