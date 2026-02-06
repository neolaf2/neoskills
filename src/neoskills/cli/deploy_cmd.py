"""neoskills deploy - deploy skills or bundles to targets."""

import click
from rich.console import Console

from neoskills.adapters.factory import get_adapter
from neoskills.bank.store import SkillStore
from neoskills.bundles.manager import BundleManager
from neoskills.core.models import Bundle
from neoskills.core.workspace import Workspace
from neoskills.mappings.target import TargetManager

console = Console()


@click.group()
def deploy() -> None:
    """Deploy skills or bundles to targets."""


@deploy.command("skill")
@click.argument("skill_id")
@click.option("--to", "target_id", required=True, help="Target to deploy to")
def deploy_skill(skill_id: str, target_id: str) -> None:
    """Deploy a single skill to a target."""
    ws = Workspace()
    store = SkillStore(ws)
    mgr = TargetManager(ws)
    mgr.ensure_builtins()

    skill = store.get(skill_id)
    if not skill:
        console.print(f"[red]Skill '{skill_id}' not found in bank.[/red]")
        raise SystemExit(1)

    target = mgr.get(target_id)
    if not target:
        console.print(f"[red]Target '{target_id}' not found.[/red]")
        raise SystemExit(1)

    if not target.writable:
        console.print(f"[red]Target '{target_id}' is read-only.[/red]")
        raise SystemExit(1)

    adapter = get_adapter(target.agent_type)

    # Try variant first, fall back to canonical
    variant_content = store.get_variant_content(skill_id, target.agent_type)
    content = variant_content or adapter.translate(skill, target)

    path = adapter.install(target, skill_id, content)
    console.print(f"[green]Deployed '{skill_id}' to {target_id} at {path}[/green]")


@deploy.command("bundle")
@click.argument("bundle_id")
@click.option("--to", "target_id", required=True, help="Target to deploy to")
def deploy_bundle(bundle_id: str, target_id: str) -> None:
    """Deploy a bundle (set of skills) to a target."""
    ws = Workspace()
    store = SkillStore(ws)
    mgr = TargetManager(ws)
    mgr.ensure_builtins()
    bmgr = BundleManager(ws)

    bundle = bmgr.get(bundle_id)
    if not bundle:
        console.print(f"[red]Bundle '{bundle_id}' not found.[/red]")
        raise SystemExit(1)

    target = mgr.get(target_id)
    if not target:
        console.print(f"[red]Target '{target_id}' not found.[/red]")
        raise SystemExit(1)

    if not target.writable:
        console.print(f"[red]Target '{target_id}' is read-only.[/red]")
        raise SystemExit(1)

    adapter = get_adapter(target.agent_type)
    deployed = 0

    for skill_id in bundle.skill_ids:
        skill = store.get(skill_id)
        if not skill:
            console.print(f"  [yellow]~[/yellow] {skill_id} (not in bank, skipped)")
            continue

        variant_content = store.get_variant_content(skill_id, target.agent_type)
        content = variant_content or adapter.translate(skill, target)
        adapter.install(target, skill_id, content)
        console.print(f"  [green]+[/green] {skill_id}")
        deployed += 1

    console.print(
        f"\n[bold green]Deployed {deployed}/{len(bundle.skill_ids)} "
        f"skills from bundle '{bundle_id}' to '{target_id}'[/bold green]"
    )


@deploy.command("create-bundle")
@click.argument("bundle_id")
@click.option("--name", default="", help="Bundle display name")
@click.option("--description", default="", help="Bundle description")
@click.option("--skill", "skill_ids", multiple=True, required=True, help="Skill IDs to include")
@click.option("--tag", "tags", multiple=True, help="Tags")
def create_bundle(
    bundle_id: str,
    name: str,
    description: str,
    skill_ids: tuple[str, ...],
    tags: tuple[str, ...],
) -> None:
    """Create a new bundle."""
    ws = Workspace()
    bmgr = BundleManager(ws)

    bundle = Bundle(
        bundle_id=bundle_id,
        name=name or bundle_id,
        description=description,
        skill_ids=list(skill_ids),
        tags=list(tags),
    )
    path = bmgr.create(bundle)
    console.print(f"[green]Bundle '{bundle_id}' created at {path}[/green]")
    console.print(f"[dim]Skills: {', '.join(skill_ids)}[/dim]")
