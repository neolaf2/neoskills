"""neoskills validate - audit skills for completeness."""

from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from neoskills.bank.validator import Severity, SkillValidator, ValidationReport
from neoskills.core.workspace import Workspace

console = Console()


@click.command()
@click.option("--skill", default=None, help="Validate a single skill by ID")
@click.option("--fix", is_flag=True, help="Auto-create stubs for missing referenced files")
@click.option(
    "--root",
    type=click.Path(),
    default=None,
    help="Workspace root override (default: ~/.neoskills)",
)
def validate(skill: str | None, fix: bool, root: str | None) -> None:
    """Validate skills in the bank for completeness and consistency."""
    workspace = Workspace(Path(root) if root else None)

    if not workspace.bank_skills.exists():
        console.print("[red]No bank found. Run 'neoskills init' first.[/red]")
        raise SystemExit(1)

    validator = SkillValidator(workspace)

    # Fix stubs if requested
    if fix:
        if not skill:
            console.print("[red]--fix requires --skill <id>[/red]")
            raise SystemExit(1)
        created = validator.fix_stubs(skill)
        if created:
            console.print(f"[green]Created {len(created)} stub files:[/green]")
            for p in created:
                console.print(f"  {p}")
        else:
            console.print("[dim]No stubs needed.[/dim]")
        # Show validation report after fixing
        report = validator.validate_one(skill)
        _display_report(report)
        if not report.passed:
            raise SystemExit(1)
        return

    # Validate
    if skill:
        report = validator.validate_one(skill)
    else:
        report = validator.validate_all()

    _display_report(report)

    if not report.passed:
        raise SystemExit(1)


def _display_report(report: ValidationReport) -> None:
    """Print validation results as a Rich table."""
    if not report.issues:
        console.print(
            f"[bold green]All {report.total_skills} skills passed validation.[/bold green]"
        )
        return

    table = Table(title=f"Validation Results ({report.total_skills} skills)")
    table.add_column("Severity", style="bold", width=8)
    table.add_column("Skill", style="cyan")
    table.add_column("Category", style="dim")
    table.add_column("Message")

    for issue in report.issues:
        sev_style = "red" if issue.severity == Severity.ERROR else "yellow"
        table.add_row(
            f"[{sev_style}]{issue.severity.value}[/{sev_style}]",
            issue.skill_id,
            issue.category.value,
            issue.message,
        )

    console.print(table)
    console.print(f"\n[bold]{len(report.errors)} errors, {len(report.warnings)} warnings[/bold]")
