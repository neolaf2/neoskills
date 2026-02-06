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
from neoskills.core.checksum import checksum_directory, checksum_string
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
@click.option("--force", is_flag=True, help="Overwrite existing bank skills")
def from_target(target_id: str, skill_ids: tuple[str, ...], import_all: bool, no_embed: bool, force: bool) -> None:
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

    # Discover skills to get full paths (not just content)
    discovered = adapter.discover(target)
    discovered_map = {s.skill_id: s for s in discovered}

    # Determine which skills to import
    if import_all:
        ids_to_import = [s.skill_id for s in discovered]
    elif skill_ids:
        ids_to_import = list(skill_ids)
    else:
        console.print("[yellow]Specify --skill <id> or --all[/yellow]")
        return

    if not ids_to_import:
        console.print("[yellow]No skills found to import.[/yellow]")
        return

    format_map = {
        "claude-code": SkillFormat.CLAUDE_CODE,
        "opencode": SkillFormat.OPENCODE,
        "openclaw": SkillFormat.OPENCLAW,
    }
    source_format = format_map.get(target.agent_type, SkillFormat.CANONICAL)

    imported_ids = []
    skipped = 0
    for skill_id in ids_to_import:
        disc = discovered_map.get(skill_id)
        if not disc:
            console.print(f"  [red]x[/red] {skill_id} (not found in target)")
            continue

        # Duplicate check: compare full directory checksums
        if store.exists(skill_id) and not force:
            if disc.is_directory:
                source_cksum = checksum_directory(disc.path)
            else:
                source_cksum = checksum_string(disc.path.read_text())
            bank_cksum = store.dir_checksum(skill_id)
            if source_cksum == bank_cksum:
                console.print(f"  [dim]=[/dim] {skill_id} (identical in bank, skipped)")
                skipped += 1
                continue
            console.print(f"  [yellow]![/yellow] {skill_id} (differs from bank, use --force to overwrite)")
            skipped += 1
            continue

        # Import: copy full directory or just content
        if disc.is_directory:
            skill = store.add_from_dir(skill_id, disc.path, source_format=source_format)
        else:
            content = disc.path.read_text()
            skill = store.add(skill_id, content, source_format=source_format)
        registry.register(skill)

        prov = Provenance(
            skill_id=skill_id,
            source_type="target",
            source_location=str(target.discovery_paths),
            source_target=target_id,
            imported_at=datetime.now(),
            original_checksum=skill.checksum,
        )
        prov_tracker.record(prov)
        imported_ids.append(skill_id)
        console.print(f"  [green]+[/green] {skill_id}")

    msg = f"Imported {len(imported_ids)} skill(s) from '{target_id}'"
    if skipped:
        msg += f" ({skipped} skipped)"
    console.print(f"\n[bold green]{msg}[/bold green]")

    if not no_embed and imported_ids:
        _auto_embed(ws, imported_ids)


@import_skills.command("from-git")
@click.argument("url")
@click.option("--skill", "skill_ids", multiple=True, help="Specific skill ID(s) to import")
@click.option("--branch", default="main", help="Git branch")
@click.option("--no-embed", is_flag=True, help="Import to bank only, skip auto-embed")
@click.option("--force", is_flag=True, help="Overwrite existing bank skills")
def from_git(url: str, skill_ids: tuple[str, ...], branch: str, no_embed: bool, force: bool) -> None:
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
            skill_dirs.append((sid, skill_dir))

        if not skill_dirs:
            console.print("[yellow]No SKILL.md files found in repository.[/yellow]")
            return

        imported_ids = []
        skipped = 0
        for skill_id, source_dir in skill_dirs:
            # Duplicate check
            if store.exists(skill_id) and not force:
                source_cksum = checksum_directory(source_dir)
                bank_cksum = store.dir_checksum(skill_id)
                if source_cksum == bank_cksum:
                    console.print(f"  [dim]=[/dim] {skill_id} (identical in bank, skipped)")
                    skipped += 1
                    continue
                console.print(f"  [yellow]![/yellow] {skill_id} (differs from bank, use --force to overwrite)")
                skipped += 1
                continue

            # Copy full skill directory (SKILL.md + scripts/ + references/ + assets/)
            skill = store.add_from_dir(skill_id, source_dir)
            registry.register(skill)

            prov = Provenance(
                skill_id=skill_id,
                source_type="git",
                source_location=url,
                imported_at=datetime.now(),
                original_checksum=skill.checksum,
                notes=f"branch: {branch}",
            )
            prov_tracker.record(prov)
            imported_ids.append(skill_id)
            console.print(f"  [green]+[/green] {skill_id}")

    msg = f"Imported {len(imported_ids)} skill(s) from git"
    if skipped:
        msg += f" ({skipped} skipped)"
    console.print(f"\n[bold green]{msg}[/bold green]")

    if not no_embed and imported_ids:
        _auto_embed(ws, imported_ids)


@import_skills.command("from-web")
@click.argument("url")
@click.option("--skill-id", default=None, help="Override skill ID")
@click.option("--no-embed", is_flag=True, help="Import to bank only, skip auto-embed")
@click.option("--force", is_flag=True, help="Overwrite existing bank skills")
def from_web(url: str, skill_id: str | None, no_embed: bool, force: bool) -> None:
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

            # Find SKILL.md files and copy full directories
            imported_ids = []
            skipped = 0
            for skill_md in Path(tmpdir).rglob("SKILL.md"):
                source_dir = skill_md.parent
                sid = skill_id or source_dir.name

                # Duplicate check
                if store.exists(sid) and not force:
                    source_cksum = checksum_directory(source_dir)
                    bank_cksum = store.dir_checksum(sid)
                    if source_cksum == bank_cksum:
                        console.print(f"  [dim]=[/dim] {sid} (identical in bank, skipped)")
                        skipped += 1
                        continue
                    console.print(f"  [yellow]![/yellow] {sid} (differs from bank, use --force)")
                    skipped += 1
                    continue

                skill = store.add_from_dir(sid, source_dir)
                registry.register(skill)
                prov = Provenance(
                    skill_id=sid,
                    source_type="web",
                    source_location=url,
                    imported_at=datetime.now(),
                    original_checksum=skill.checksum,
                )
                prov_tracker.record(prov)
                imported_ids.append(sid)
                console.print(f"  [green]+[/green] {sid}")

            msg = f"Imported {len(imported_ids)} skill(s) from zip"
            if skipped:
                msg += f" ({skipped} skipped)"
            console.print(f"\n[bold green]{msg}[/bold green]")

            if not no_embed and imported_ids:
                _auto_embed(ws, imported_ids)
    else:
        # Single file URL
        with urllib.request.urlopen(url) as resp:
            content = resp.read().decode("utf-8")

        sid = skill_id or Path(url).stem

        # Duplicate check for single file
        if store.exists(sid) and not force:
            bank_cksum = store.dir_checksum(sid)
            source_cksum = checksum_string(content)
            if source_cksum == bank_cksum:
                console.print(f"  [dim]=[/dim] {sid} (identical in bank, skipped)")
                return
            console.print(f"  [yellow]![/yellow] {sid} (differs from bank, use --force)")
            return

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
