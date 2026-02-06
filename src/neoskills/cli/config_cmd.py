"""neoskills config - configuration management."""

import click
from rich.console import Console

from neoskills.core.config import Config
from neoskills.core.workspace import Workspace

console = Console()


@click.group("config")
def config() -> None:
    """Manage neoskills configuration."""


@config.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key: str, value: str) -> None:
    """Set a configuration value."""
    ws = Workspace()
    cfg = Config(ws.config_file)
    cfg.set(key, value)
    cfg.save()
    console.print(f"[green]Set {key} = {value}[/green]")


@config.command("get")
@click.argument("key")
def config_get(key: str) -> None:
    """Get a configuration value."""
    ws = Workspace()
    cfg = Config(ws.config_file)
    value = cfg.get(key)
    if value is None:
        console.print(f"[yellow]{key} is not set[/yellow]")
    else:
        console.print(f"{key} = {value}")


@config.command("show")
def config_show() -> None:
    """Show all configuration."""
    import yaml

    ws = Workspace()
    cfg = Config(ws.config_file)
    console.print(yaml.dump(cfg.data, default_flow_style=False))
