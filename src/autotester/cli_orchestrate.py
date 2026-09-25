"""`autotester orchestrate` — the live caller of `stages/orchestrate.py::run_or_resume`.

AT-575: T-163's resumable orchestrator (D-036) had no entry point outside its
own tests (`tests/test_orchestrate*.py`), so resume-after-interruption was
reachable only from pytest. This command drives that SAME `run_or_resume`,
wiring the two entry stages (INGEST/DISCOVER) plus MODEL — the orchestrator
stops at the review gate by design (contract `orchestrator.md`, D-036); a
human runs `flowspec approve` then `expand` to continue, exactly as they do
today after a manual `ingest run` or `explore --merge`.

Split out of `cli.py` for the same reason `cli_crawl.py` is: that file is at
its line budget, and a stage's commands belong beside the stage they drive.
No new logic is added here beyond wiring — the stage adapters
(`stages/orchestrate_runners.py`) and the existing crawl/consent/secret
primitives `cli_crawl.py`'s `explore` command already uses are reused as-is.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

import typer

from autotester import providers
from autotester.core.ids import run_id as mint_run_id
from autotester.core.paths import ProjectPaths, RepoDocs
from autotester.schema.run_state import RunState, StageName
from autotester.stages.orchestrate import TEACHING_KINDS, StageContext, choose_mode, run_or_resume
from autotester.stages.orchestrate_runners import (
    make_discover_runner,
    make_ingest_runner,
    make_model_runner,
)
from autotester.store.project_store import ProjectStore

if TYPE_CHECKING:
    from autotester.browser.secrets import SecretStore
    from autotester.schema.crawl import Crawl
    from autotester.schema.project import Project, Source
    from autotester.schema.screen_graph import ScreenNode


def _entry_source(sources: list[Source]) -> Source:
    """The Source INGEST watches. `choose_mode` already established at least
    one teaching Source exists whenever it returns `"learn"`; the earliest one
    (list order = registration order) keeps a re-run deterministic."""
    return next(s for s in sources if s.kind in TEACHING_KINDS)


def _require_crawl_consent(proj: Project, store_: ProjectStore, bounds: object) -> None:
    """D-018 gate 2, checked before anything is created and before a browser
    would start — the same check `explore` runs as its own preflight
    (`cli_crawl.py::_preflight_consent`), so DISCOVER never bypasses consent
    just because it is reached through the orchestrator instead."""
    from autotester.core.consent import ApprovalRequired
    from autotester.schema.crawl import SafetyPolicy
    from autotester.stages import explore_consent

    try:
        explore_consent.require_consent(
            proj, store_, bounds, policy=SafetyPolicy(write_policy=proj.write_policy))
    except ApprovalRequired as exc:
        typer.secho(str(exc), fg=typer.colors.YELLOW)
        raise typer.Exit(2) from None


def _make_crawl_fn(
    proj: Project, store_: ProjectStore, paths: ProjectPaths, secrets: SecretStore,
    bounds: object, login_case_id: str | None,
) -> Callable[[], tuple[Crawl, list[ScreenNode]]]:
    """The DISCOVER stage's injected `crawl_fn` (`orchestrate_runners.py`'s own
    seam): opens the browser and runs the existing bounded-BFS crawl only when
    the DISCOVER stage actually executes, exactly like `explore_cmd` does."""

    def _run() -> tuple[Crawl, list[ScreenNode]]:
        from autotester.browser.observe import PageObserver
        from autotester.browser.session import BrowserSession
        from autotester.stages import explore as explore_stage

        paths.ensure()
        case = store_.get_case(login_case_id) if login_case_id else None
        observer = PageObserver()
        crawl_id = mint_run_id("crawl")
        with BrowserSession(proj, secrets, paths.crawl_shots_dir(crawl_id), paths,
                            observer=observer) as session:
            crawl = explore_stage.run_crawl(proj, session, store_, observer=observer,
                                            bounds=bounds, login_case=case, crawl_id=crawl_id)
        return crawl, store_.list_nodes(crawl.id)

    return _run


def _build_runners(
    mode: str, sources: list[Source], project: str, proj: Project, store_: ProjectStore,
    paths: ProjectPaths, secrets: SecretStore, provider_id: str, bounds: object,
    login_case_id: str | None,
) -> dict[StageName, Callable]:
    """The autonomous run wires exactly {INGEST|DISCOVER, MODEL} (STOP point
    at the review gate, `orchestrate.py`'s own contract) — never EXPAND
    onward, so this never grows into a second approval mechanism (OR-no-fire)."""
    if mode == "learn":
        source = _entry_source(sources)
        model = providers.get(provider_id)
        return {
            StageName.INGEST: make_ingest_runner(source, project, model, RepoDocs()),
            StageName.MODEL: make_model_runner(source_id=source.id),
        }
    _require_crawl_consent(proj, store_, bounds)
    crawl_fn = _make_crawl_fn(proj, store_, paths, secrets, bounds, login_case_id)
    return {
        StageName.DISCOVER: make_discover_runner(proj, crawl_fn),
        StageName.MODEL: make_model_runner(),
    }


def _echo_state(project: str, state: RunState) -> bool:
    """Print every checkpoint and say what to do next. Returns whether the run
    is clean (no failed stage) — the command's exit code hangs off this."""
    typer.secho(f"{project}: run {state.run_id} — {state.mode} ({state.mode_reason})",
                fg=typer.colors.GREEN)
    ok = True
    for checkpoint in state.stages:
        colour = {"done": typer.colors.GREEN, "failed": typer.colors.RED,
                 "skipped": typer.colors.GREEN}.get(checkpoint.status, typer.colors.YELLOW)
        line = f"  {checkpoint.stage.value:8} {checkpoint.status}"
        if checkpoint.error:
            line += f" — {checkpoint.error}"
            ok = False
        typer.secho(line, fg=colour)
    pending = state.next_pending()
    if pending is None:
        typer.secho("run complete through the wired stages (INGEST|DISCOVER -> MODEL)",
                    fg=typer.colors.GREEN)
    elif pending.status == "failed":
        typer.secho(f"resume with: --run-id {state.run_id}", fg=typer.colors.YELLOW)
    else:
        typer.secho(
            f"stopped at the review gate — `flowspec approve {project} --by <name>` then "
            f"`expand {project}` to continue (resume with --run-id {state.run_id})",
            fg=typer.colors.YELLOW)
    return ok


def orchestrate_cmd(
    project: str = typer.Argument(..., help="project slug"),
    run_id: str = typer.Option(
        None, "--run-id",
        help="resume this run (pass the id a previous invocation printed); "
             "default mints a fresh one"),
    provider: str = typer.Option("gemini", "--provider", help="ingest provider (learn path only)"),
    max_screens: int = typer.Option(30, "--max-screens", help="explore path only"),
    max_actions: int = typer.Option(200, "--max-actions", help="explore path only"),
    wall_clock: float = typer.Option(600.0, "--wall-clock", help="seconds; explore path only"),
    max_depth: int = typer.Option(6, "--max-depth", help="explore path only"),
    login_case: str | None = typer.Option(None, "--login-case", help="explore path only"),
) -> None:
    """Run (or resume) the pipeline for `project`: the same entry-path choice
    (teach->INGEST / creds->DISCOVER) and per-stage `RunState` checkpoints
    `stages/orchestrate.py::run_or_resume` and its tests exercise, now reachable
    from the command line. Stops at the review gate (contract `orchestrator.md`).
    """
    from autotester.browser.secrets import SecretStore
    from autotester.schema.crawl import CrawlBounds

    store_ = ProjectStore(project)
    proj = store_.load_project()
    if proj is None:
        typer.secho(f"no project '{project}' yet", fg=typer.colors.RED)
        raise typer.Exit(1)

    sources = store_.list_sources()
    mode = choose_mode(sources)[0]
    paths = ProjectPaths(project)
    secrets = SecretStore.load(proj, paths.env_file, strict=False)
    bounds = CrawlBounds(max_screens=max_screens, max_actions=max_actions,
                         wall_clock_s=wall_clock, max_depth=max_depth)

    runners = _build_runners(mode, sources, project, proj, store_, paths, secrets, provider,
                             bounds, login_case)
    ctx = StageContext(store=store_, run_id=run_id or mint_run_id("run"), runners=runners,
                       secrets=secrets)
    state = run_or_resume(proj, ctx)
    ok = _echo_state(project, state)
    if not ok:
        raise typer.Exit(1)
