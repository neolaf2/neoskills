"""CLI entry point - Click group wiring all subcommands."""

import click

from neoskills import __version__


@click.group()
@click.version_option(version=__version__, prog_name="neoskills")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """neoskills - Cross-Agent Skill Bank & Transfer System."""
    ctx.ensure_object(dict)


# Import and register subcommands
from neoskills.cli.init_cmd import init  # noqa: E402

cli.add_command(init)


def _register_later_commands() -> None:
    """Register commands from later phases (silently skip if not yet implemented)."""
    command_modules = [
        # --- v0.3 Brew-style commands ---
        ("neoskills.cli.tap_cmd", "tap"),
        ("neoskills.cli.tap_cmd", "untap"),
        ("neoskills.cli.brew_install_cmd", "brew_install"),  # registers as "install"
        ("neoskills.cli.brew_install_cmd", "uninstall"),
        ("neoskills.cli.link_cmd", "link"),
        ("neoskills.cli.link_cmd", "unlink"),
        ("neoskills.cli.update_cmd", "update"),
        ("neoskills.cli.update_cmd", "upgrade"),
        ("neoskills.cli.list_cmd", "list_skills"),  # registers as "list"
        ("neoskills.cli.list_cmd", "search"),
        ("neoskills.cli.list_cmd", "info"),
        ("neoskills.cli.doctor_cmd", "doctor"),
        ("neoskills.cli.create_cmd", "create"),
        ("neoskills.cli.push_cmd", "push"),
        ("neoskills.cli.migrate_cmd", "migrate"),
        # --- Kept commands ---
        ("neoskills.cli.config_cmd", "config"),
        ("neoskills.cli.enhance_cmd", "enhance"),
        ("neoskills.cli.agent_cmd", "agent"),
        ("neoskills.cli.plugin_cmd", "plugin"),
    ]
    import importlib

    for module_path, cmd_name in command_modules:
        try:
            mod = importlib.import_module(module_path)
            cmd = getattr(mod, cmd_name, None)
            if cmd and cmd.name not in cli.commands:
                cli.add_command(cmd)
        except (ImportError, AttributeError):
            pass


_register_later_commands()
