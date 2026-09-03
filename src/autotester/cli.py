"""Command line. Every action the UI offers is available here first."""

from __future__ import annotations

import typer

from autotester import doctor as doctor_module
from autotester import providers

app = typer.Typer(help="AutoTester — AI automated end-to-end tester", no_args_is_help=True)


@app.command()
def doctor() -> None:
    """Check the repo against the design rules that keep it readable."""
    violations = doctor_module.run()
    if not violations:
        typer.secho("doctor: clean", fg=typer.colors.GREEN)
        raise typer.Exit(0)
    for violation in violations:
        typer.secho(str(violation), fg=typer.colors.RED)
    typer.secho(f"\n{len(violations)} violation(s)", fg=typer.colors.RED, bold=True)
    raise typer.Exit(1)


@app.command("providers")
def providers_check() -> None:
    """Show which model providers have credentials present on this machine."""
    ready = providers.available_ids()
    typer.echo("available providers: " + (", ".join(ready) if ready else "none"))


def main() -> None:
    app()
