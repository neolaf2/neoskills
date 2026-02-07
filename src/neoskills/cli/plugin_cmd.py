"""neoskills plugin - create and validate plugin packages."""

from pathlib import Path

import click
import yaml
from rich.console import Console

from neoskills.plugin.schema import validate_plugin_yaml

console = Console()

# Default plugin.yaml content for marketplace template
_MARKETPLACE_PLUGIN_YAML = {
    "name": "neoskills",
    "version": "0.2.1",
    "namespace": "plugin/neoskills",
    "capabilities": ["discover", "lifecycle", "evolution", "registry", "governance"],
    "registry": {"type": "local", "path": "registry/registry.yaml", "writable": True},
    "host_constraints": {"sandboxed": True},
}


@click.group("plugin")
def plugin() -> None:
    """Create and validate neoskills plugins."""


@plugin.command("create")
@click.option(
    "--template",
    type=click.Choice(["marketplace", "minimal"]),
    default="marketplace",
    help="Template to use (default: marketplace)",
)
@click.option("--path", "output_path", default=".", help="Output directory")
def plugin_create(template: str, output_path: str) -> None:
    """Scaffold a plugin package from a template."""
    base = Path(output_path)

    if template == "marketplace":
        _create_marketplace(base)
    else:
        _create_minimal(base)


@plugin.command("validate")
@click.argument("path", type=click.Path(exists=True))
def plugin_validate(path: str) -> None:
    """Validate a plugin.yaml and skill structure."""
    plugin_path = Path(path)
    yaml_path = plugin_path / "plugin.yaml"

    result = validate_plugin_yaml(yaml_path)
    if result["valid"]:
        console.print("[bold green]plugin.yaml is valid.[/bold green]")
    else:
        console.print("[bold red]plugin.yaml validation failed:[/bold red]")
        for err in result["errors"]:
            console.print(f"  [red]x[/red] {err}")
        raise SystemExit(1)

    # Check skill structure
    skills_dir = plugin_path / "skills"
    if skills_dir.exists():
        skill_count = sum(1 for d in skills_dir.rglob("SKILL.md"))
        console.print(f"  Skills found: {skill_count}")
    else:
        console.print("  [dim]No skills/ directory[/dim]")

    agents_dir = plugin_path / "agents"
    if agents_dir.exists():
        agent_count = sum(1 for f in agents_dir.glob("*.md"))
        console.print(f"  Agents found: {agent_count}")


def _create_marketplace(base: Path) -> None:
    """Create the full MarketPlace/plugin/neoskills hierarchy."""
    plugin_root = base / "MarketPlace" / "plugin" / "neoskills"

    # Create directories
    dirs = [
        plugin_root / "skills" / "skill_management" / "discover" / "find_skills",
        plugin_root / "skills" / "skill_management" / "lifecycle" / "install_skill",
        plugin_root / "skills" / "skill_management" / "evolution" / "skill_creator",
        plugin_root / "agents",
        plugin_root / "registry",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

    # plugin.yaml
    (plugin_root / "plugin.yaml").write_text(
        yaml.dump(_MARKETPLACE_PLUGIN_YAML, default_flow_style=False)
    )

    # Sample skills
    _write_skill(
        plugin_root / "skills" / "skill_management" / "discover" / "find_skills",
        "find_skills",
        "Discover skills across targets and the bank",
        "Use the capabilities.discover module to scan targets.\n",
    )
    _write_skill(
        plugin_root / "skills" / "skill_management" / "lifecycle" / "install_skill",
        "install_skill",
        "Install skills from the bank to agent targets",
        "Use the capabilities.lifecycle module to install/uninstall.\n",
    )
    _write_skill(
        plugin_root / "skills" / "skill_management" / "evolution" / "skill_creator",
        "skill_creator",
        "Create and evolve skills in the bank",
        "Use the capabilities.evolution module to create/refactor/specialize.\n",
    )

    # Agent
    (plugin_root / "agents" / "skill-manager.md").write_text(
        "---\n"
        "name: skill-manager\n"
        "description: |\n"
        "  Autonomous skill management agent. Use when the user asks to\n"
        "  find, install, create, or manage skills across targets.\n"
        "model: inherit\n"
        "color: cyan\n"
        "---\n\n"
        "You are a skill management agent for neoskills.\n\n"
        "Use the capabilities layer (discover, lifecycle, evolution, governance)\n"
        "to manage skills across the bank and deployment targets.\n"
    )

    # Registry
    (plugin_root / "registry" / "registry.yaml").write_text(
        yaml.dump({"version": "0.2.1", "skills": {}, "updated_at": ""}, default_flow_style=False)
    )

    # CI workflow
    gh_dir = base / "MarketPlace" / ".github" / "workflows"
    gh_dir.mkdir(parents=True, exist_ok=True)
    (gh_dir / "validate.yml").write_text(
        "name: Validate Plugin\n"
        "on: [push, pull_request]\n"
        "jobs:\n"
        "  validate:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        "      - uses: actions/checkout@v4\n"
        "      - uses: astral-sh/setup-uv@v5\n"
        "      - run: uv pip install neoskills\n"
        "      - run: neoskills plugin validate plugin/neoskills\n"
    )

    console.print(f"[bold green]MarketPlace template created at {base / 'MarketPlace'}[/bold green]")
    console.print(f"  plugin.yaml: {plugin_root / 'plugin.yaml'}")
    console.print("  Skills: 3 (find_skills, install_skill, skill_creator)")
    console.print("  Agents: 1 (skill-manager)")


def _create_minimal(base: Path) -> None:
    """Create a minimal plugin with just plugin.yaml and one skill."""
    plugin_root = base / "plugin" / "neoskills"
    (plugin_root / "skills").mkdir(parents=True, exist_ok=True)

    minimal_yaml = {
        "name": "neoskills",
        "version": "0.2.1",
        "namespace": "plugin/neoskills",
        "capabilities": ["discover"],
    }
    (plugin_root / "plugin.yaml").write_text(
        yaml.dump(minimal_yaml, default_flow_style=False)
    )

    console.print(f"[bold green]Minimal plugin created at {plugin_root}[/bold green]")


def _write_skill(skill_dir: Path, name: str, description: str, body: str) -> None:
    """Write a SKILL.md file."""
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: {description}\n---\n\n# {name}\n\n{body}"
    )
