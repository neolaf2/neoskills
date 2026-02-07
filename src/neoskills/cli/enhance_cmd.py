"""neoskills enhance - meta-skill operations."""

import click
from rich.console import Console
from rich.panel import Panel

from neoskills.core.cellar import Cellar
from neoskills.core.tap import TapManager
from neoskills.meta.enhancer import ENHANCE_OPERATIONS, Enhancer

console = Console()


@click.command()
@click.argument("operation", type=click.Choice(list(ENHANCE_OPERATIONS.keys())))
@click.option("--skill", "skill_id", required=True, help="Skill ID to enhance")
@click.option("--apply", "apply_result", is_flag=True, help="Apply the result to the skill")
@click.option("--target-agent", default="opencode", help="Target agent for generate-variant")
@click.option("--root", default=None, type=click.Path(), help="Workspace root.")
def enhance(operation: str, skill_id: str, apply_result: bool, target_agent: str, root: str | None) -> None:
    """Enhance a skill using Claude."""
    from pathlib import Path

    cellar = Cellar(Path(root) if root else None)
    mgr = TapManager(cellar)

    skill_path = mgr.get_skill_path(skill_id)
    if not skill_path:
        console.print(f"[red]Skill '{skill_id}' not found in any tap.[/red]")
        raise SystemExit(1)

    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        console.print(f"[red]No SKILL.md found for '{skill_id}'.[/red]")
        raise SystemExit(1)

    enhancer = Enhancer()
    if not enhancer.available:
        console.print("[red]No LLM backend available.[/red]")
        console.print("[dim]Set ANTHROPIC_API_KEY in .env or install claude-agent-sdk.[/dim]")
        raise SystemExit(1)

    console.print(f"[dim]Enhancing '{skill_id}' with operation: {operation}...[/dim]")

    extra_context = {}
    if operation == "generate-variant":
        extra_context["target_agent"] = target_agent

    content = skill_md.read_text()

    try:
        result = enhancer.enhance(content, operation, extra_context)
    except Exception as e:
        console.print(f"[red]Enhancement failed: {e}[/red]")
        raise SystemExit(1)

    if apply_result:
        skill_md.write_text(result)
        console.print(f"[green]Enhanced skill saved to {skill_path}.[/green]")
    else:
        console.print(Panel(result, title=f"Enhancement: {operation}", border_style="cyan"))
        console.print("[dim]Use --apply to write changes to the skill.[/dim]")
