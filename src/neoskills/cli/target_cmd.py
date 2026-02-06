"""neoskills target - manage deployment targets."""

import click
from rich.console import Console
from rich.table import Table

from neoskills.core.workspace import Workspace
from neoskills.mappings.target import TargetManager

console = Console()


@click.group()
def target() -> None:
    """Manage deployment targets."""


@target.command("list")
def target_list() -> None:
    """List all configured targets."""
    ws = Workspace()
    mgr = TargetManager(ws)

    # Ensure builtins exist
    created = mgr.ensure_builtins()
    if created:
        console.print(f"[dim]Created {len(created)} built-in target(s)[/dim]")

    targets = mgr.list_targets()
    if not targets:
        console.print("[yellow]No targets configured. Run 'neoskills init' first.[/yellow]")
        return

    table = Table(title="Configured Targets")
    table.add_column("ID", style="cyan")
    table.add_column("Agent Type", style="green")
    table.add_column("Display Name")
    table.add_column("Writable", justify="center")
    table.add_column("Discovery Paths", style="dim")

    for t in targets:
        table.add_row(
            t.target_id,
            t.agent_type,
            t.display_name,
            "yes" if t.writable else "no",
            ", ".join(t.discovery_paths),
        )

    console.print(table)


@target.command("add")
@click.argument("target_id")
@click.option("--agent-type", required=True, help="Agent type (claude-code, opencode, openclaw)")
@click.option("--display-name", default="", help="Human-readable name")
@click.option("--discovery", multiple=True, help="Discovery path (can repeat)")
@click.option("--install", "install_paths", multiple=True, help="Install path (can repeat)")
@click.option("--readonly", is_flag=True, help="Mark as read-only")
def target_add(
    target_id: str,
    agent_type: str,
    display_name: str,
    discovery: tuple[str, ...],
    install_paths: tuple[str, ...],
    readonly: bool,
) -> None:
    """Add a new target."""
    from neoskills.core.models import Target, TransportType

    ws = Workspace()
    mgr = TargetManager(ws)

    t = Target(
        target_id=target_id,
        agent_type=agent_type,
        display_name=display_name or target_id,
        discovery_paths=list(discovery),
        install_paths=list(install_paths),
        writable=not readonly,
        transport=TransportType.LOCAL_FS,
    )
    path = mgr.add(t)
    console.print(f"[green]Target '{target_id}' added at {path}[/green]")
