"""neoskills install - one-step skill install (bank verify + embed)."""

from pathlib import Path

import click
import yaml
from rich.console import Console

from neoskills.bank.store import SkillStore
from neoskills.core.workspace import Workspace
from neoskills.mappings.resolver import SymlinkResolver
from neoskills.mappings.target import TargetManager

console = Console()


def _default_target(workspace: Workspace) -> str:
    """Read default_target from config.yaml, fallback to claude-code-user."""
    if workspace.config_file.exists():
        cfg = yaml.safe_load(workspace.config_file.read_text()) or {}
        return cfg.get("default_target", "claude-code-user")
    return "claude-code-user"


@click.command()
@click.argument("skill_ids", nargs=-1, required=True)
@click.option("--target", "target_id", default=None, help="Target to install into (default: from config)")
@click.option("--no-embed", is_flag=True, help="Verify in bank only, skip symlink embedding")
@click.option("--root", type=click.Path(), default=None, help="Workspace root override")
def install(skill_ids: tuple[str, ...], target_id: str | None, no_embed: bool, root: str | None) -> None:
    """Install skill(s) — verify in bank and embed into target."""
    ws = Workspace(Path(root)) if root else Workspace()
    if not ws.is_initialized:
        console.print("[red]Workspace not initialized. Run 'neoskills init' first.[/red]")
        raise SystemExit(1)

    store = SkillStore(ws)

    # Verify all skills exist in bank
    missing = [sid for sid in skill_ids if not store.get(sid)]
    if missing:
        for sid in missing:
            console.print(f"  [red]x[/red] {sid} (not found in bank)")
        console.print("\n[yellow]Import missing skills first: neoskills import ...[/yellow]")
        raise SystemExit(1)

    if no_embed:
        console.print(f"[green]All {len(skill_ids)} skill(s) verified in bank.[/green]")
        return

    # Resolve target
    tid = target_id or _default_target(ws)
    mgr = TargetManager(ws)
    mgr.ensure_builtins()
    target = mgr.get(tid)
    if not target:
        console.print(f"[red]Target '{tid}' not found.[/red]")
        raise SystemExit(1)

    if not target.install_paths:
        console.print(f"[red]Target '{tid}' has no install paths.[/red]")
        raise SystemExit(1)

    install_base = Path(target.install_paths[0]).expanduser()
    if not install_base.exists():
        install_base.mkdir(parents=True, exist_ok=True)
        console.print(f"  [dim]Created target directory: {install_base}[/dim]")

    resolver = SymlinkResolver(ws)
    actions = []

    for sid in skill_ids:
        # Prefer variant for this target's agent type, fall back to canonical
        variant_dir = store.variant_dir(sid, target.agent_type)
        canonical = store.canonical_dir(sid)

        bank_path = variant_dir if (variant_dir / "SKILL.md").exists() else canonical
        agent_path = install_base / sid

        # Report what's happening: new, update, or replace
        if agent_path.is_symlink():
            existing_target = agent_path.resolve()
            if existing_target == bank_path.resolve():
                console.print(f"  [dim]=[/dim] {sid} (already linked)")
                continue
            console.print(f"  [yellow]~[/yellow] {sid} (updating symlink)")
        elif agent_path.exists():
            console.print(f"  [yellow]~[/yellow] {sid} (replacing existing dir, backup in STM)")
        else:
            console.print(f"  [green]+[/green] {sid} -> {agent_path}")

        action = resolver.create_symlink(sid, bank_path, agent_path)
        actions.append(action)

    if actions:
        resolver.save_state(actions)
        console.print(
            f"\n[bold green]Installed {len(actions)} skill(s) into '{tid}'[/bold green]"
        )
    else:
        console.print(f"\n[dim]All skill(s) already up-to-date in '{tid}'[/dim]")
