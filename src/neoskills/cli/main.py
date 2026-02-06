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
        ("neoskills.cli.config_cmd", "config"),
        ("neoskills.cli.target_cmd", "target"),
        ("neoskills.cli.scan_cmd", "scan"),
        ("neoskills.cli.import_cmd", "import_skills"),
        ("neoskills.cli.deploy_cmd", "deploy"),
        ("neoskills.cli.embed_cmd", "embed"),
        ("neoskills.cli.embed_cmd", "unembed"),
        ("neoskills.cli.sync_cmd", "sync"),
        ("neoskills.cli.enhance_cmd", "enhance"),
        ("neoskills.cli.validate_cmd", "validate"),
        ("neoskills.cli.install_cmd", "install"),
        ("neoskills.cli.agent_cmd", "agent"),
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
