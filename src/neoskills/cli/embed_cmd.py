"""neoskills embed/unembed - symlink-based skill projection."""

from pathlib import Path

import click
from rich.console import Console

from neoskills.bank.store import SkillStore
from neoskills.core.workspace import Workspace
from neoskills.mappings.resolver import SymlinkResolver
from neoskills.mappings.target import TargetManager

console = Console()


@click.command()
@click.option("--target", "target_id", default="claude-code-user", help="Target to embed into")
@click.option(
    "--skill", "skill_ids", multiple=True, help="Specific skill(s) to embed (default: all)"
)
def embed(target_id: str, skill_ids: tuple[str, ...]) -> None:
    """Embed bank skills into a target via symlinks."""
    ws = Workspace()
    store = SkillStore(ws)
    mgr = TargetManager(ws)
    mgr.ensure_builtins()
    resolver = SymlinkResolver(ws)

    target = mgr.get(target_id)
    if not target:
        console.print(f"[red]Target '{target_id}' not found.[/red]")
        raise SystemExit(1)

    if not target.install_paths:
        console.print(f"[red]Target '{target_id}' has no install paths.[/red]")
        raise SystemExit(1)

    # Determine skills to embed
    ids = list(skill_ids) if skill_ids else store.list_skills()
    if not ids:
        console.print("[yellow]No skills in bank to embed.[/yellow]")
        return

    install_base = Path(target.install_paths[0]).expanduser()
    actions = []

    for skill_id in ids:
        # Determine bank path: prefer variant, fall back to canonical
        variant_dir = store.variant_dir(skill_id, target.agent_type)
        canonical = store.canonical_dir(skill_id)

        if variant_dir.exists() and (variant_dir / "SKILL.md").exists():
            bank_path = variant_dir
        elif canonical.exists():
            bank_path = canonical
        else:
            console.print(f"  [yellow]~[/yellow] {skill_id} (not found in bank, skipped)")
            continue

        agent_path = install_base / skill_id
        action = resolver.create_symlink(skill_id, bank_path, agent_path)
        actions.append(action)

        backup_note = " (backed up original)" if action.backup else ""
        console.print(f"  [green]+[/green] {skill_id} -> {bank_path}{backup_note}")

    resolver.save_state(actions)
    console.print(f"\n[bold green]Embedded {len(actions)} skill(s) into '{target_id}'[/bold green]")


@click.command()
@click.option("--target", "target_id", default="claude-code-user", help="Target to unembed from")
@click.option(
    "--skill", "skill_ids", multiple=True, help="Specific skill(s) (default: all embedded)"
)
def unembed(target_id: str, skill_ids: tuple[str, ...]) -> None:
    """Remove embedded symlinks and restore originals."""
    ws = Workspace()
    resolver = SymlinkResolver(ws)

    embedded = resolver.load_state()
    if not embedded:
        console.print("[yellow]No embedded skills found.[/yellow]")
        return

    ids = list(skill_ids) if skill_ids else list(embedded.keys())
    removed = []

    for skill_id in ids:
        if skill_id not in embedded:
            console.print(f"  [yellow]~[/yellow] {skill_id} (not embedded, skipped)")
            continue

        info = embedded[skill_id]
        agent_path = Path(info["target"])

        if resolver.remove_symlink(skill_id, agent_path):
            removed.append(skill_id)
            console.print(f"  [red]-[/red] {skill_id}")
        else:
            console.print(f"  [yellow]~[/yellow] {skill_id} (not a symlink, skipped)")

    resolver.clear_state(removed)
    console.print(
        f"\n[bold green]Unembedded {len(removed)} skill(s) from '{target_id}'[/bold green]"
    )
