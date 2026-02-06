"""neoskills scan - discover skills from a target."""

import click
from rich.console import Console
from rich.table import Table

from neoskills.adapters.factory import get_adapter
from neoskills.core.workspace import Workspace
from neoskills.mappings.target import TargetManager

console = Console()


@click.command()
@click.argument("target_id")
def scan(target_id: str) -> None:
    """Scan a target for installed skills."""
    ws = Workspace()
    if not ws.is_initialized:
        console.print("[red]Workspace not initialized. Run 'neoskills init' first.[/red]")
        raise SystemExit(1)

    mgr = TargetManager(ws)
    mgr.ensure_builtins()
    target = mgr.get(target_id)
    if not target:
        console.print(f"[red]Target '{target_id}' not found.[/red]")
        console.print("Run 'neoskills target list' to see available targets.")
        raise SystemExit(1)

    adapter = get_adapter(target.agent_type)
    discovered = adapter.discover(target)

    if not discovered:
        console.print(f"[yellow]No skills found in target '{target_id}'.[/yellow]")
        return

    table = Table(title=f"Skills in '{target_id}' ({target.display_name})")
    table.add_column("#", style="dim", justify="right")
    table.add_column("Skill ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Type", justify="center")
    table.add_column("Frontmatter", justify="center")
    table.add_column("Description", max_width=50)

    for i, s in enumerate(discovered, 1):
        table.add_row(
            str(i),
            s.skill_id,
            s.name,
            "dir" if s.is_directory else "file",
            "yes" if s.has_frontmatter else "no",
            (s.description[:47] + "...") if len(s.description) > 50 else s.description,
        )

    console.print(table)
    console.print(f"\n[dim]Total: {len(discovered)} skill(s)[/dim]")
