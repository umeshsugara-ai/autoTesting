"""Does an approval's TARGET match the project it was granted for?

Split from `test_approve_cli.py` at doctor's 300-line cap, by responsibility:
that file is about WHEN an approval is valid (expiry, kind, project), this one
about WHAT it covers. The two collected their own bugs — AT-147 was a boundary
date; AT-148, AT-149 and AT-152 were three separate ways a string can look like
a prefix of a URL without being underneath it.

The warning here never refuses. An endpoint under test may legitimately differ
from `base_url`, and CN5 matches exactly at run time regardless — it exists so
a typo is caught at GRANT time rather than discovered at a refusal.

Contract: qa/contracts/consent.md CN5.
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


@pytest.fixture
def root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("AUTOTESTER_ROOT", str(tmp_path))
    _save_project(tmp_path, BASE_URL)
    return tmp_path


def _save_project(root: Path, base_url: str) -> None:
    ProjectStore("demo", root).save_project(Project(
        slug="demo", name="Demo", base_url=base_url, allowed_domains=["demo.test"]))


def approve_target(target: str) -> object:
    return runner.invoke(app, [
        "approve", "demo", "--kind", "crawl", "--target", target,
        "--scope", "s", "--granted-by", "umesh", "--expires", TOMORROW,
    ])


# -- AT-145: a target this project will never ask about --------------------

def test_a_wholly_unrelated_target_is_flagged(root: Path) -> None:
    """Not refused — CN5 matches exactly at run time anyway. But granting
    consent for a target this project will never ask about is almost certainly
    a typo, and the operator should hear it at grant time."""
    result = approve_target("https://unrelated.test/")

    assert result.exit_code == 0
    assert "does not match" in result.output


# -- AT-148: the host half -------------------------------------------------

def test_a_lookalike_host_is_flagged_not_silently_accepted(root: Path) -> None:
    """`target.startswith(base_url)` read `https://demo.test.evil.com/` as
    matching `https://demo.test/`. Bounded — CN5 matches exactly at run time,
    so no approval widens — but the advisory was silent on precisely the shape
    a typo-squat takes."""
    result = approve_target("https://demo.test.evil.com/")

    assert result.exit_code == 0
    assert "does not match" in result.output


def test_the_exact_base_url_is_not_flagged(root: Path) -> None:
    result = approve_target(BASE_URL)

    assert result.exit_code == 0
    assert "does not match" not in result.output


def test_a_genuine_sub_path_of_the_base_url_is_not_flagged(root: Path) -> None:
    """A warning that cries wolf on the normal case gets ignored on the case it
    exists for."""
    result = approve_target(BASE_URL + "admin")

    assert result.exit_code == 0
    assert "does not match" not in result.output


# -- AT-149: the path half, one line below the host fix --------------------

@pytest.mark.parametrize("target", [
    "https://demo.test/apple-secrets",   # /app is a prefix but not a parent
    "https://demo.test/appliance/admin",
])
def test_a_path_that_merely_starts_with_the_base_path_is_flagged(
    root: Path, target: str,
) -> None:
    """AT-148 fixed the naive prefix match in the HOST half, and the identical
    bug survived ONE LINE BELOW it in the PATH half. Against a base_url of
    `https://demo.test/app`, `/apple-secrets` was silently accepted as being
    under `/app`. A prefix is only a containment if it ends at a separator."""
    _save_project(root, "https://demo.test/app")

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
    _save_project(root, "https://demo.test/app")

    result = approve_target(target)

    assert result.exit_code == 0
    assert "does not match" not in result.output


# -- AT-152: a path that climbs back out -----------------------------------

def test_a_path_that_climbs_out_of_the_base_is_flagged(root: Path) -> None:
    """`urlparse` normalises no dot-segments, so `/app/../evil` reads as
    contained while RESOLVING to `/evil`. A string that can climb out is not
    under anything — the check refuses to vouch for it rather than guessing
    where it lands."""
    _save_project(root, "https://demo.test/app")

    result = approve_target("https://demo.test/app/../evil")

    assert result.exit_code == 0
    assert "does not match" in result.output
