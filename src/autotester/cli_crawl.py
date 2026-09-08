"""Crawl commands — `autotester explore` and `autotester report crawl`.

Split out of `cli.py` at its 300-line cap (C2); the commands are mounted onto
the same typer apps there, so the CLI surface a user sees is unchanged.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import typer

from autotester.store.project_store import ProjectStore


def _preflight_consent(proj: Any, store_: ProjectStore, bounds: Any) -> None:
    """D-018, checked before ANY directory is created and before the browser
    starts — `run_crawl` checks again at the seam, so this is additional.

    AT-111: with the check only at the seam, a refused run still left
    `crawl/<id>/shots/` and a populated Chromium profile behind, because
    `BrowserSession.start()` runs inside the `with` that wraps `run_crawl`.
    Even `paths.ensure()` alone leaves an empty profile dir — harmless, but
    "a refused run leaves no trace" has to mean what it says.
    """
    from autotester.core.consent import ApprovalRequired
    from autotester.stages import explore as explore_stage

    try:
        explore_stage.require_consent(proj, store_, bounds)
    except ApprovalRequired as exc:
        typer.secho(str(exc), fg=typer.colors.YELLOW)
        raise typer.Exit(2) from None


def _resolve_crawl_target(project: str, login_case: str | None) -> tuple[ProjectStore, Any, Any]:
    """The project and (optional) login case, or a clean CLI exit naming which
    one is missing — never a traceback at a user."""
    store_ = ProjectStore(project)
    proj = store_.load_project()
    if proj is None:
        typer.secho(f"no project '{project}' yet", fg=typer.colors.RED)
        raise typer.Exit(1)
    case = store_.get_case(login_case) if login_case else None
    if login_case and case is None:
        typer.secho(f"no case '{login_case}' in {project}", fg=typer.colors.RED)
        raise typer.Exit(1)
    return store_, proj, case


def explore_cmd(
    project: str,
    max_screens: int = typer.Option(30, "--max-screens"),
    max_actions: int = typer.Option(200, "--max-actions"),
    wall_clock: float = typer.Option(600.0, "--wall-clock", help="seconds"),
    max_depth: int = typer.Option(6, "--max-depth"),
    login_case: str | None = typer.Option(None, "--login-case", help="case id to log in with"),
    merge: bool = typer.Option(
        False, "--merge", help="fold the crawled screens into the FlowSpec (resets it to DRAFT)"
    ),
) -> None:
    """Bounded BFS crawl of a project, refusing anything its write_policy
    denies. Contract: qa/contracts/explore.md. Nothing is typed except the
    optional login case; nothing destructive is clicked."""
    from autotester.browser.observe import PageObserver
    from autotester.browser.secrets import SecretStore
    from autotester.browser.session import BrowserSession
    from autotester.core.consent import ApprovalRequired
    from autotester.core.ids import run_id
    from autotester.core.paths import ProjectPaths
    from autotester.schema.crawl import CrawlBounds
    from autotester.stages import explore as explore_stage

    store_, proj, case = _resolve_crawl_target(project, login_case)
    bounds = CrawlBounds(max_screens=max_screens, max_actions=max_actions,
                         wall_clock_s=wall_clock, max_depth=max_depth)
    _preflight_consent(proj, store_, bounds)
    paths = ProjectPaths(project)
    paths.ensure()
    secrets = SecretStore.load(proj, paths.env_file, strict=False)
    observer = PageObserver()
    crawl_id = run_id("crawl")
    try:
        with BrowserSession(proj, secrets, paths.crawl_shots_dir(crawl_id),
                            paths, observer=observer) as session:
            crawl = explore_stage.run_crawl(proj, session, store_, observer=observer,
                                            bounds=bounds, login_case=case, crawl_id=crawl_id)
    except ApprovalRequired as exc:
        typer.secho(str(exc), fg=typer.colors.YELLOW)
        raise typer.Exit(2) from None
    echo_crawl_summary(crawl)
    if merge:
        _merge_into_flowspec(store_, project, crawl.id)
    typer.echo(str(paths.crawl_dir(crawl.id)))


def echo_crawl_summary(crawl: Any) -> None:
    """The whole report a headless or CI run gets (AT-122).

    `tool_failures` belongs here for the same reason it belongs in the
    workbook: this line is the only place such a run learns the crawl could
    not record part of what it saw. Dropping it under-reports as dishonestly
    as folding it into `issues` over-reported."""
    typer.secho(
        f"{crawl.id}: {crawl.status.value} ({crawl.stop_reason}) — "
        f"{crawl.screens} screens, {crawl.edges} edges, {crawl.actions} actions, "
        f"{crawl.denied} denied, {crawl.issues} issues, "
        f"{crawl.tool_failures} tool failures",
        fg=typer.colors.GREEN,
    )


def _merge_into_flowspec(store_: ProjectStore, project: str, crawl_id: str) -> None:
    """Fold the crawl's screens into the FlowSpec and say what that cost the
    review status — a merge always sends an approved spec back to DRAFT, and a
    user who is not told that will think the spec is still approved."""
    from autotester.stages.explore_merge import merge_screens

    before = store_.load_flowspec()
    spec = merge_screens(before, store_.list_nodes(crawl_id), project, crawl_id=crawl_id)
    store_.save_flowspec(spec)
    added = len(spec.screens) - (len(before.screens) if before else 0)
    typer.secho(
        f"merged {added} new screen(s) into flowspec v{spec.version} "
        f"(review: {spec.review.status.value})",
        fg=typer.colors.GREEN,
    )


def _validate_grant(expires: str, target: str, proj: Any) -> None:
    """Refuse a grant that can never cover anything, and flag a likely typo (AT-145).

    The safety property was never in doubt -- `require_consent` refuses an
    expired or unparseable row at run time. What was wrong is what the HUMAN is
    told: `approve --expires 2020-01-01` printed a green "granted" line for a
    consent that will refuse every run it is asked about. A gate that reports
    success for a grant it will never honour trains the operator to stop
    reading it, and the operator here is granting production consent for a
    crawl of a live ERP.
    """
    try:
        expiry = date.fromisoformat(expires)
    except ValueError:
        typer.secho(f"--expires must be YYYY-MM-DD, not {expires!r}", fg=typer.colors.RED)
        raise typer.Exit(1) from None
    if expiry < date.today():
        typer.secho(
            f"--expires {expires} is already in the past — this grant would refuse "
            f"every run it was asked about",
            fg=typer.colors.RED)
        raise typer.Exit(1)
    if proj is not None and proj.base_url and not target.startswith(proj.base_url.rstrip("/")):
        # Not refused: an endpoint under test may legitimately differ from
        # base_url, and CN5 matches exactly at consent time regardless. But say
        # it now rather than leaving the operator to discover it at the refusal.
        typer.secho(
            f"note: {target} does not match this project's base_url "
            f"({proj.base_url}) — a crawl of it will not match this approval",
            fg=typer.colors.YELLOW)


def approve_cmd(
    project: str,
    kind: str = typer.Option(..., "--kind", help="read | crawl | adversarial | live_case"),
    target: str = typer.Option(..., "--target", help="the exact base_url or endpoint"),
    scope: str = typer.Option(..., "--scope", help="what this run may touch, in your words"),
    granted_by: str = typer.Option(..., "--granted-by"),
    expires: str = typer.Option(..., "--expires", help="YYYY-MM-DD; consent is never open-ended"),
    max_actions: int = typer.Option(0, "--max-actions"),
    max_probes: int = typer.Option(0, "--max-probes"),
    wall_clock: float = typer.Option(0.0, "--wall-clock", help="seconds"),
    production: bool = typer.Option(
        False, "--production", help="required for an adversarial run against production"
    ),
) -> None:
    """Grant a human's approval for one kind of run against one target (D-018).

    Nothing outward-facing starts without one. The approval is content-addressed,
    so an accidental edit to the row invalidates it rather than silently taking
    effect — but the hash is unkeyed, so this is tamper EVIDENCE, not tamper
    proofing: anyone who can write approvals.jsonl can recompute a valid id
    (AT-110).
    """
    from autotester.schema.approval import RunApproval
    from autotester.schema.enums import ApprovalKind

    store_ = ProjectStore(project)
    if store_.load_project() is None:
        typer.secho(f"no project '{project}' yet", fg=typer.colors.RED)
        raise typer.Exit(1)
    try:
        run_kind = ApprovalKind(kind)
    except ValueError:
        allowed = ", ".join(k.value for k in ApprovalKind)
        typer.secho(f"--kind must be one of: {allowed}", fg=typer.colors.RED)
        raise typer.Exit(1) from None
    _validate_grant(expires, target, store_.load_project())
    approval = store_.add_approval(RunApproval(
        project=project, run_kind=run_kind, target=target, scope=scope,
        max_actions=max_actions, max_probes=max_probes, wall_clock_s=wall_clock,
        production=production, granted_by=granted_by,
        granted_at=date.today().isoformat(), expires_at=expires,
    ))
    typer.secho(
        f"{approval.id}: {run_kind.value} on {target} until {expires} "
        f"(actions<={max_actions}, probes<={max_probes})",
        fg=typer.colors.GREEN,
    )


def report_crawl(
    project: str,
    crawl_id: str = typer.Argument(..., help="crawl id, e.g. crawl_01J…"),
    out: str = typer.Option(..., "--out", help="output .xlsx path"),
) -> None:
    """Summary, screens, edges, refusals, issues and third-party noise."""
    from autotester.stages.crawl_report import export_crawl_excel

    try:
        path = export_crawl_excel(project, crawl_id, Path(out))
    except ValueError as exc:
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(1) from exc
    typer.secho(f"wrote {path}", fg=typer.colors.GREEN)
