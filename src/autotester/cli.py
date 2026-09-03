"""Command line. Every action the UI offers is available here first."""

from __future__ import annotations

from datetime import date

import typer

from autotester import doctor as doctor_module
from autotester import providers
from autotester.core.paths import RepoDocs
from autotester.ledger import render, store
from autotester.ledger.relitigation import gate_message, relitigate
from autotester.schema.enums import FeatureEventKind, UserValue

app = typer.Typer(help="AutoTester — AI automated end-to-end tester", no_args_is_help=True)
ledger_app = typer.Typer(help="The feature ledger (docs/FEATURES.jsonl) — the only write path.")
app.add_typer(ledger_app, name="ledger")


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


@app.command("map")
def map_cmd() -> None:
    """Regenerate docs/MAP.md — directory map + schema summary, derived from code."""
    docs = RepoDocs()
    docs.map.write_text(render.apply_map(docs), encoding="utf-8")
    typer.secho("map: docs/MAP.md regenerated", fg=typer.colors.GREEN)


@app.command()
def snapshot(print_only: bool = typer.Option(False, "--print", help="print, do not write")) -> None:
    """Regenerate docs/SNAPSHOT.md — the digest injected at session start."""
    docs = RepoDocs()
    text = render.render_snapshot(docs)
    if print_only:
        typer.echo(text)
        return
    docs.snapshot.write_text(text, encoding="utf-8")
    typer.secho(f"snapshot: {text.count(chr(10))} lines written", fg=typer.colors.GREEN)


@ledger_app.command("add")
def ledger_add(
    feature: str,
    title: str,
    event: FeatureEventKind,
    description: str = typer.Option(..., "--description", "-d"),
    reason: str | None = typer.Option(None, "--reason", "-r"),
    user_value: UserValue = typer.Option(UserValue.NORMAL, "--value"),
    unit: str | None = typer.Option(None, "--unit"),
    verdict_ref: str | None = typer.Option(None, "--verdict"),
    supersedes: str | None = typer.Option(None, "--supersedes"),
    on: str | None = typer.Option(None, "--date", help="YYYY-MM-DD, default today"),
) -> None:
    """Append one feature event. Retirements require a real --reason."""
    docs = RepoDocs()
    events = store.load_events(docs.features)
    row = store.new_event(
        events, feature=feature, title=title, event=event, description=description,
        user_value=user_value, reason=reason, unit=unit, verdict_ref=verdict_ref,
        supersedes=supersedes, on=date.fromisoformat(on) if on else None,
    )
    store.append_event(docs.features, row)
    docs.snapshot.write_text(render.render_snapshot(docs), encoding="utf-8")
    typer.secho(f"{row.id} {row.event.value} {row.feature}", fg=typer.colors.GREEN)
    if row.ask_required:
        typer.secho("ASK: high-value feature with auto reason — confirm or edit the reason "
                    "(`ledger add ... updated --reason ...`)", fg=typer.colors.YELLOW)


@ledger_app.command("weight")
def ledger_weight(feature: str, value: UserValue) -> None:
    """Re-weight a feature after shipping. Raising to high asks for the reason once."""
    docs = RepoDocs()
    row = store.raise_weight(docs.features, feature, value)
    docs.snapshot.write_text(render.render_snapshot(docs), encoding="utf-8")
    typer.secho(f"{row.id} weight -> {value.value}", fg=typer.colors.GREEN)
    if row.ask_required:
        typer.secho("ASK: now high-value — provide the reasoning for this feature",
                    fg=typer.colors.YELLOW)


@ledger_app.command("check")
def ledger_check() -> None:
    """L3: every closed high-value goal task has a live/updated row."""
    docs = RepoDocs()
    events = store.load_events(docs.features)
    missing = store.check_rows_on_pass(events, store.load_goal_tasks(docs.goal))
    if missing:
        typer.secho("missing ledger rows for: " + ", ".join(missing), fg=typer.colors.RED)
        raise typer.Exit(1)
    typer.secho("ledger: every closed high-value task has a row", fg=typer.colors.GREEN)


@ledger_app.command("relitigation")
def ledger_relitigation(
    unit_text: str, provider: str = typer.Option("mock", "--provider")
) -> None:
    """Gate check before a unit is built: is this a retired feature coming back?"""
    docs = RepoDocs()
    retired = store.retired(store.load_events(docs.features))
    verdict = relitigate(unit_text, retired, providers.get(provider), docs)
    if verdict.gate:
        typer.secho(gate_message(verdict, retired), fg=typer.colors.YELLOW)
        raise typer.Exit(2)
    typer.secho(f"no gate — {verdict.justification} ({verdict.decided_by})", fg=typer.colors.GREEN)


def main() -> None:
    app()
