"""What `autotester explore` and `autotester approve` ACTUALLY do — AT-140.

The sweep measured the gap: every explore test called `run_crawl` directly —
the entry point AT-111's own checker called "the one no operator uses" — and
the shipped commands had zero coverage. `approve`, the command that GRANTS
consent, was untested while the refusal path was well defended. T-145
(CRITICAL) points that untested path at a live production ERP.

These tests need no browser: `_preflight_consent` runs before `paths.ensure()`
and before `BrowserSession`, which is the whole point of AT-111's fix. The
success path stops at the consent seam deliberately — a real crawl belongs to
`scripts/explore_proof.py`, not here.

Contract: qa/contracts/consent.md CN1-CN9, explore.md.
"""

from __future__ import annotations

import re
import shlex
from datetime import date, timedelta
from pathlib import Path

import pytest
from typer.testing import CliRunner

from autotester.cli import app
from autotester.schema.project import Project
from autotester.store.project_store import ProjectStore

runner = CliRunner()

TOMORROW = (date.today() + timedelta(days=1)).isoformat()
BASE_URL = "https://demo.test/"

# The typer defaults on `explore_cmd`. These exact numbers are what
# `require_consent` judges a production run against, so they are pinned here:
# a default that drifts out of step with an approval is not a test failure
# anywhere else in the suite.
CLI_DEFAULT_ACTIONS = 200
CLI_DEFAULT_WALL_CLOCK = "600.0"

# What the refusal leaves for a human to supply. Substituting them is the test's
# job precisely because the tool must NOT invent them: who authorised a
# production crawl, and until when, is not a value software gets to default.
PLACEHOLDERS = {
    "<what this run may touch>": "read-only crawl",
    "<name>": "umesh",
    "<YYYY-MM-DD>": TOMORROW,
}


@pytest.fixture
def root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("AUTOTESTER_ROOT", str(tmp_path))
    store = ProjectStore("demo", tmp_path)
    store.save_project(Project(slug="demo", name="Demo", base_url=BASE_URL,
                               allowed_domains=["demo.test"]))
    return tmp_path


def grant(*extra: str) -> object:
    return runner.invoke(app, [
        "approve", "demo", "--kind", "crawl", "--target", BASE_URL,
        "--scope", "read-only crawl", "--granted-by", "umesh",
        "--expires", TOMORROW, *extra,
    ])


# -- the refusal, through the shipped command ------------------------------

def test_explore_without_an_approval_exits_two(root: Path) -> None:
    """CN1 through the CLI. This was proven only by `scripts/explore_proof.py`
    and by calling `run_crawl` directly; the command an operator actually types
    had no test at all."""
    result = runner.invoke(app, ["explore", "demo"])

    assert result.exit_code == 2, result.output
    assert "approv" in result.output.lower()


def test_a_refused_crawl_leaves_nothing_on_disk(root: Path) -> None:
    """CN1 means what it says. AT-111 found a refused run still left
    `crawl/<id>/shots/` and a populated Chromium profile behind, because
    `BrowserSession.start()` runs inside the `with` that wraps `run_crawl`.

    AT-143 -- the first version of this test globbed `projects/<slug>` for
    names containing "crawl" or "profile" and saw **3 of the 211 entries** a
    refused run creates. The entire Chromium profile tree (`Default/Network/
    Cookies`, `Login Data`, `History`) lives at `root/profiles/<slug>`, a
    SIBLING of `projects/` -- unreachable by that glob whatever it searched
    for, and it is the very artefact this docstring names. A test that names
    the right property and then looks in the wrong place is worse than none:
    it reports the guarantee as held.

    So: snapshot the WHOLE root, and diff. Nothing new anywhere, not "nothing
    new where I thought to look."
    """
    before = set(root.rglob("*"))

    result = runner.invoke(app, ["explore", "demo"])

    assert result.exit_code == 2, result.output
    created = sorted(p for p in set(root.rglob("*")) - before)
    assert created == [], (
        f"a refused run created {len(created)} entries, e.g. {created[:5]}")


def test_the_refusal_names_every_bound_of_the_run_it_refused(root: Path) -> None:
    """CN6. The refusal prints a grant command, and it must carry the bounds of
    the run being refused. The first version omitted them, and `--max-actions`
    defaults to 0 — so pasting the command produced a SECOND refusal.

    It deliberately leaves placeholders for what only a human can supply (who
    granted it, until when, what it may touch); "works verbatim" is not the
    property, and a test asserting it would be asserting a design mistake."""
    refusal = runner.invoke(app, ["explore", "demo"]).output

    assert "--max-actions 200" in refusal, "the action budget is missing"
    assert "--wall-clock 600" in refusal, "the wall-clock budget is missing"
    assert "--granted-by" in refusal and "--expires" in refusal


def test_the_refusals_command_grants_the_run_once_a_human_fills_it_in(
    root: Path,
) -> None:
    """The half that IS testable: substitute the placeholders and the command
    must grant exactly the run that was refused — not a narrower one that
    refuses again."""
    from autotester.schema.crawl import CrawlBounds
    from autotester.stages.explore import require_consent

    refusal = runner.invoke(app, ["explore", "demo"]).output
    match = re.search(r"autotester approve.*", refusal)
    assert match, f"the refusal named no grant command: {refusal!r}"

    argv = shlex.split(match.group(0))[1:]  # drop the leading "autotester"
    argv = [PLACEHOLDERS.get(a, a) for a in argv]
    granted = runner.invoke(app, argv)
    assert granted.exit_code == 0, f"the filled-in command failed: {granted.output!r}"

    store = ProjectStore("demo", root)
    require_consent(store.load_project(), store, CrawlBounds())  # must not raise


# -- `approve`, the command that grants consent ----------------------------

def test_approve_writes_a_row_that_covers_the_cli_defaults(root: Path) -> None:
    """An approval for exactly the default action budget must let the default
    run through.

    AT-146 -- I originally called this "the one row I would keep", claiming it
    pins `explore_cmd`'s TYPER defaults to `require_consent`. It does not: it
    never invokes `explore`, it constructs `CrawlBounds()` directly, so it pins
    the SCHEMA defaults. The checker proved it by drifting the typer default
    200 -> 137, under which this test still passed. What actually protects that
    seam is the two refusal tests above, which read the bounds out of the real
    command's output. Kept, correctly described."""
    from autotester.schema.crawl import CrawlBounds
    from autotester.stages.explore import require_consent

    assert grant("--max-actions", str(CLI_DEFAULT_ACTIONS),
                 "--wall-clock", CLI_DEFAULT_WALL_CLOCK).exit_code == 0

    store = ProjectStore("demo", root)
    proj = store.load_project()
    require_consent(proj, store, CrawlBounds())  # must not raise


def test_an_approval_narrower_than_the_run_still_refuses(root: Path) -> None:
    """One action short. A gate that only fails when the approval is ABSENT is
    a gate that never checks its own bounds."""
    from autotester.core.consent import ApprovalRequired
    from autotester.schema.crawl import CrawlBounds
    from autotester.stages.explore import require_consent

    assert grant("--max-actions", str(CLI_DEFAULT_ACTIONS - 1),
                 "--wall-clock", CLI_DEFAULT_WALL_CLOCK).exit_code == 0

    store = ProjectStore("demo", root)
    with pytest.raises(ApprovalRequired):
        require_consent(store.load_project(), store, CrawlBounds())


def test_approve_rejects_an_unknown_kind_and_names_the_valid_ones(root: Path) -> None:
    result = runner.invoke(app, [
        "approve", "demo", "--kind", "definitely-not-a-kind", "--target", BASE_URL,
        "--scope", "s", "--granted-by", "umesh", "--expires", TOMORROW,
    ])

    assert result.exit_code == 1
    assert "crawl" in result.output and "adversarial" in result.output


def test_approve_on_an_unknown_project_exits_one(root: Path) -> None:
    result = runner.invoke(app, [
        "approve", "nope", "--kind", "crawl", "--target", BASE_URL,
        "--scope", "s", "--granted-by", "umesh", "--expires", TOMORROW,
    ])

    assert result.exit_code == 1
    assert "no project" in result.output


# -- the two exit-1 paths in _resolve_crawl_target -------------------------

def test_exploring_an_unknown_project_exits_one_without_a_traceback(root: Path) -> None:
    result = runner.invoke(app, ["explore", "nope"])

    assert result.exit_code == 1
    assert "no project 'nope'" in result.output
    assert "Traceback" not in result.output


def test_a_missing_login_case_is_named_not_ignored(root: Path) -> None:
    """Silently crawling logged-OUT because the named case did not exist would
    produce a graph of the login wall and call it the product."""
    result = runner.invoke(app, ["explore", "demo", "--login-case", "case_nope"])

    assert result.exit_code == 1
    assert "case_nope" in result.output


# -- AT-144: the bound flags must actually reach CrawlBounds ---------------

def test_every_bound_flag_reaches_the_crawl_bounds(
    root: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AT-144: hardcoding `max_screens=999` in `explore_cmd` left the whole
    633-test suite green. `--max-screens` and `--max-depth` never reach an
    approval (consent bounds actions/probes/wall-clock only), so nothing else
    in the system can notice if they stop being wired — and they are the two
    bounds that decide how much of a live production ERP gets touched."""
    from autotester import cli_crawl

    seen: dict[str, object] = {}
    real = cli_crawl._preflight_consent

    def capture(proj: object, store_: object, bounds: object) -> None:
        seen["bounds"] = bounds
        real(proj, store_, bounds)  # still refuses, so nothing runs

    monkeypatch.setattr(cli_crawl, "_preflight_consent", capture)

    runner.invoke(app, ["explore", "demo", "--max-screens", "7", "--max-actions", "11",
                        "--wall-clock", "13.0", "--max-depth", "3"])

    bounds = seen.get("bounds")
    assert bounds is not None, "the CLI never reached the consent pre-flight"
    assert (bounds.max_screens, bounds.max_actions) == (7, 11)
    assert (bounds.wall_clock_s, bounds.max_depth) == (13.0, 3)


# -- AT-145: a grant that cannot cover anything must say so ---------------

def test_approve_refuses_an_already_expired_date(root: Path) -> None:
    """AT-145: `approve --expires 2020-01-01` exited 0 with a green "granted"
    line. The safety property held — `require_consent` refuses an expired row
    — but the human granting T-145's PRODUCTION consent was told it worked.
    A gate that reports success for a grant it will never honour trains the
    operator to ignore it."""
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    result = runner.invoke(app, [
        "approve", "demo", "--kind", "crawl", "--target", BASE_URL,
        "--scope", "s", "--granted-by", "umesh", "--expires", yesterday,
    ])

    assert result.exit_code == 1
    assert "already" in result.output.lower() or "past" in result.output.lower()


def test_approve_refuses_an_unparseable_expiry(root: Path) -> None:
    """`--expires never` was accepted verbatim and stored, where it can only
    ever compare as "not today's date"."""
    result = runner.invoke(app, [
        "approve", "demo", "--kind", "crawl", "--target", BASE_URL,
        "--scope", "s", "--granted-by", "umesh", "--expires", "never",
    ])

    assert result.exit_code == 1
    assert "YYYY-MM-DD" in result.output


def test_approve_warns_when_the_target_is_not_the_projects_base_url(root: Path) -> None:
    """Not refused — an endpoint under test legitimately differs from base_url,
    and CN5 matches exactly at consent time anyway. But granting consent for a
    target this project will never ask about is almost certainly a typo, and
    the operator should hear it AT GRANT TIME rather than at the refusal."""
    result = runner.invoke(app, [
        "approve", "demo", "--kind", "crawl", "--target", "https://unrelated.test/",
        "--scope", "s", "--granted-by", "umesh", "--expires", TOMORROW,
    ])

    assert result.exit_code == 0
    assert "base_url" in result.output or "does not match" in result.output
