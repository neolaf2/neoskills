"""neoskills config - configuration management."""

import click
from rich.console import Console

from neoskills.core.cellar import Cellar

console = Console()


@click.group("config")
def config() -> None:
    """Manage neoskills configuration."""


@config.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key: str, value: str) -> None:
    """Set a configuration value."""
    cellar = Cellar()
    cfg = cellar.load_config()

    # Support dotted keys (e.g. "default_target")
    cfg[key] = value
    cellar.save_config(cfg)
    console.print(f"[green]Set {key} = {value}[/green]")


@config.command("get")
@click.argument("key")
def config_get(key: str) -> None:
    """Get a configuration value."""
    cellar = Cellar()
    cfg = cellar.load_config()
    value = cfg.get(key)
    if value is None:
        console.print(f"[yellow]{key} is not set[/yellow]")
    else:
        console.print(f"{key} = {value}")


@config.command("show")
def config_show() -> None:
    """Show all configuration."""
    import yaml

    cellar = Cellar()
    cfg = cellar.load_config()
    console.print(yaml.dump(cfg, default_flow_style=False))
