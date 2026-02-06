"""neoskills enhance - meta-skill operations."""

import click
from rich.console import Console
from rich.panel import Panel

from neoskills.bank.store import SkillStore
from neoskills.core.workspace import Workspace
from neoskills.meta.enhancer import ENHANCE_OPERATIONS, Enhancer

console = Console()


@click.command()
@click.argument("operation", type=click.Choice(list(ENHANCE_OPERATIONS.keys())))
@click.option("--skill", "skill_id", required=True, help="Skill ID to enhance")
@click.option("--apply", "apply_result", is_flag=True, help="Apply the result to the skill")
@click.option("--target-agent", default="opencode", help="Target agent for generate-variant")
def enhance(operation: str, skill_id: str, apply_result: bool, target_agent: str) -> None:
    """Enhance a skill using Claude."""
    ws = Workspace()
    store = SkillStore(ws)

    skill = store.get(skill_id)
    if not skill:
        console.print(f"[red]Skill '{skill_id}' not found in bank.[/red]")
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

    try:
        result = enhancer.enhance(skill.content, operation, extra_context)
    except Exception as e:
        console.print(f"[red]Enhancement failed: {e}[/red]")
        raise SystemExit(1)

    if apply_result:
        if operation == "generate-variant":
            store.add_variant(skill_id, target_agent, result)
            console.print(
                f"[green]Variant for '{target_agent}' saved to bank.[/green]"
            )
        else:
            store.add(skill_id, result)
            console.print("[green]Enhanced skill saved to bank.[/green]")
    else:
        console.print(Panel(result, title=f"Enhancement: {operation}", border_style="cyan"))
        console.print("[dim]Use --apply to write changes to the bank.[/dim]")
