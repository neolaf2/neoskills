"""neoskills agent - discover and run agents from the agents/ directory."""

from importlib import resources as pkg_resources
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from neoskills.core.frontmatter import parse_frontmatter

console = Console()


def _find_agents_dir() -> Path | None:
    """Locate the agents/ directory: package first, then project root."""
    # Try package-bundled agents
    try:
        ref = pkg_resources.files("neoskills") / "agents"
        pkg_path = Path(str(ref))
        if pkg_path.is_dir() and any(pkg_path.glob("*.md")):
            return pkg_path
    except (TypeError, FileNotFoundError):
        pass

    # Fall back to project root agents/
    project_root = Path(__file__).resolve().parents[3]
    fallback = project_root / "agents"
    if fallback.is_dir() and any(fallback.glob("*.md")):
        return fallback

    return None


def _list_agent_files(agents_dir: Path) -> list[tuple[Path, dict, str]]:
    """Parse all .md files in agents_dir. Returns (path, frontmatter, body) tuples."""
    agents = []
    for md_file in sorted(agents_dir.glob("*.md")):
        content = md_file.read_text()
        fm, body = parse_frontmatter(content)
        if fm.get("name"):
            agents.append((md_file, fm, body))
    return agents


@click.group("agent")
def agent() -> None:
    """Discover and run agents."""


@agent.command("list")
def agent_list() -> None:
    """List available agents."""
    agents_dir = _find_agents_dir()
    if not agents_dir:
        console.print("[yellow]No agents/ directory found.[/yellow]")
        return

    agents = _list_agent_files(agents_dir)
    if not agents:
        console.print("[yellow]No agents found.[/yellow]")
        return

    table = Table(title=f"Agents ({agents_dir})")
    table.add_column("Name", style="cyan")
    table.add_column("Model", style="dim")
    table.add_column("Description")

    for _, fm, _ in agents:
        desc = fm.get("description", "")
        if len(desc) > 80:
            desc = desc[:77] + "..."
        table.add_row(
            fm["name"],
            fm.get("model", "inherit"),
            desc,
        )

    console.print(table)


@agent.command("run")
@click.argument("name")
@click.option("--task", default=None, help="Task description for the agent")
def agent_run(name: str, task: str | None) -> None:
    """Run an agent by name."""
    agents_dir = _find_agents_dir()
    if not agents_dir:
        console.print("[red]No agents/ directory found.[/red]")
        raise SystemExit(1)

    # Find the agent
    agents = _list_agent_files(agents_dir)
    match = None
    for path, fm, body in agents:
        if fm["name"] == name:
            match = (path, fm, body)
            break

    if not match:
        names = [fm["name"] for _, fm, _ in agents]
        console.print(f"[red]Agent '{name}' not found.[/red]")
        if names:
            console.print(f"[dim]Available: {', '.join(names)}[/dim]")
        raise SystemExit(1)

    _, fm, system_prompt = match

    if not task:
        console.print("[yellow]No --task provided. Provide a task for the agent.[/yellow]")
        console.print(f"[dim]Usage: neoskills agent run {name} --task 'your task'[/dim]")
        raise SystemExit(1)

    # Combine system prompt + task and send to LLM
    from neoskills.meta.enhancer import Enhancer

    enhancer = Enhancer()
    if not enhancer.available:
        console.print("[red]No LLM backend available.[/red]")
        console.print("[dim]Set ANTHROPIC_API_KEY in .env or install claude-agent-sdk.[/dim]")
        raise SystemExit(1)

    full_prompt = (
        f"## System\n{system_prompt}\n\n"
        f"## Task\n{task}"
    )

    console.print(f"[dim]Running agent '{name}'...[/dim]")
    try:
        result = enhancer._call_llm(full_prompt)
    except Exception as e:
        console.print(f"[red]Agent run failed: {e}[/red]")
        raise SystemExit(1)
    console.print(result)
