"""What `autotester approve` ACTUALLY does — the command that GRANTS consent.

Split from `test_crawl_real_cli.py` at the 300-line cap, by responsibility:
that file is about refusing a crawl, this one is about issuing the approval
that permits one. `approve` had no test at all until AT-140, while the refusal
path around it was well defended — the gate's *deny* half was guarded and its
*grant* half was not.

Contract: qa/contracts/consent.md CN5-CN7.
"""

from __future__ import annotations

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
CLI_DEFAULT_ACTIONS = 200
CLI_DEFAULT_WALL_CLOCK = "600.0"


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


# -- AT-147 / AT-148: the boundary day, and the lookalike host -------------

def test_approve_refuses_an_expiry_of_today(root: Path) -> None:
    """AT-147, high, and the date an operator granting SAME-DAY production
    consent for T-145 would actually type.

    `_validate_grant` compared `< date.today()` while `RunApproval.is_expired`
    reads a bare date through `fromisoformat` — i.e. MIDNIGHT — so an approval
    "expiring today" was already dead at 00:00:01. `approve` printed a green
    granted line; the very next `explore` refused it as `expired`."""
    result = runner.invoke(app, [
        "approve", "demo", "--kind", "crawl", "--target", BASE_URL,
        "--scope", "s", "--granted-by", "umesh", "--expires", date.today().isoformat(),
    ])

    assert result.exit_code == 1
    assert "today" in result.output
    assert TOMORROW in result.output, "the refusal must name the date to use instead"


def test_the_grant_and_the_runtime_agree_on_every_expiry_they_accept(
    root: Path,
) -> None:
    """The real property behind AT-145 and AT-147, stated once: any expiry
    `approve` ACCEPTS must be one `require_consent` will HONOUR. The two used
    different comparisons, so there was a whole day where they disagreed."""
    from autotester.schema.crawl import CrawlBounds
    from autotester.stages.explore import require_consent

    for offset in (1, 2, 30):
        when = (date.today() + timedelta(days=offset)).isoformat()
        assert grant("--max-actions", str(CLI_DEFAULT_ACTIONS),
                     "--wall-clock", CLI_DEFAULT_WALL_CLOCK,
                     "--expires", when).exit_code == 0, f"{when} was refused at grant"

        store = ProjectStore("demo", root)
        require_consent(store.load_project(), store, CrawlBounds())  # must not raise


def test_a_lookalike_host_is_flagged_not_silently_accepted(root: Path) -> None:
    """AT-148: `target.startswith(base_url)` reads `https://demo.test.evil.com/`
    as matching `https://demo.test/`. Bounded — CN5 matches exactly at run time,
    so no approval widens — but the typo advisory was silent on precisely the
    shape a typo-squat takes."""
    result = runner.invoke(app, [
        "approve", "demo", "--kind", "crawl", "--target", "https://demo.test.evil.com/",
        "--scope", "s", "--granted-by", "umesh", "--expires", TOMORROW,
    ])

    assert result.exit_code == 0
    assert "does not match" in result.output


def test_a_genuine_sub_path_of_the_base_url_is_not_flagged(root: Path) -> None:
    """The other side: crawling a path under base_url is the normal case and
    must not cry wolf, or the warning gets ignored when it matters."""
    result = runner.invoke(app, [
        "approve", "demo", "--kind", "crawl", "--target", BASE_URL + "admin",
        "--scope", "s", "--granted-by", "umesh", "--expires", TOMORROW,
    ])

    assert result.exit_code == 0
    assert "does not match" not in result.output


# -- AT-149 / AT-150: the same bug one line below its own fix --------------

def _project_with_base(root: Path, base_url: str) -> None:
    ProjectStore("demo", root).save_project(Project(
        slug="demo", name="Demo", base_url=base_url, allowed_domains=["demo.test"]))


def approve_target(target: str) -> object:
    return runner.invoke(app, [
        "approve", "demo", "--kind", "crawl", "--target", target,
        "--scope", "s", "--granted-by", "umesh", "--expires", TOMORROW,
    ])


@pytest.mark.parametrize("target", [
    "https://demo.test/apple-secrets",   # /app is a prefix but not a parent
    "https://demo.test/appliance/admin",
])
def test_a_path_that_merely_starts_with_the_base_path_is_flagged(
    root: Path, target: str,
) -> None:
    """AT-149: AT-148 fixed the naive prefix match in the HOST half, and the
    identical bug survived ONE LINE BELOW it in the PATH half. Against a
    base_url of `https://demo.test/app`, `/apple-secrets` was silently accepted
    as being under `/app`. A prefix is only a containment if it ends at a
    separator."""
    _project_with_base(root, "https://demo.test/app")

    result = approve_target(target)

    assert result.exit_code == 0
    assert "does not match" in result.output


@pytest.mark.parametrize("target", [
    "https://demo.test/app",             # the base itself
    "https://demo.test/app/",            # the base, trailing slash
    "https://demo.test/app/admin",       # a genuine child
])
def test_the_base_path_and_its_real_children_are_not_flagged(
    root: Path, target: str,
) -> None:
    """The other side: a warning that fires on the normal case gets ignored on
    the case it exists for."""
    _project_with_base(root, "https://demo.test/app")

    result = approve_target(target)

    assert result.exit_code == 0
    assert "does not match" not in result.output


def test_the_expiry_refusal_prints_a_usable_date(root: Path) -> None:
    """AT-150: the refusal said the operator needs "tomorrow's date" and never
    printed one. My own test asserted only that the word "tomorrow" appeared,
    so a refusal naming no usable date would have passed it — a test written
    against the message I meant rather than the message a reader gets."""
    result = runner.invoke(app, [
        "approve", "demo", "--kind", "crawl", "--target", BASE_URL,
        "--scope", "s", "--granted-by", "umesh", "--expires", date.today().isoformat(),
    ])

    assert result.exit_code == 1
    assert TOMORROW in result.output, "the refusal must name a date, not a word"
