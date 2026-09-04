"""AT-037: a project's own public base_url must not be flagged as a leak
just because the same string also happens to sit in .env as a convenience
value. Contract: scripts/check_no_secrets.py is the tool this project's own
maker-checker cycle runs before every commit -- a false positive here either
gets silently ignored (defeating the tool) or wastes a real investigation.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import check_no_secrets as cns

from autotester.schema.project import Project
from autotester.store import ProjectStore


def test_a_projects_own_base_url_is_excluded_even_if_also_in_env(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text(
        "SOME_LOGIN_URL=https://app.example.com/signin\n"
        "REAL_SECRET=hunter2-trombone-staple\n",
        encoding="utf-8",
    )
    ProjectStore("demo", tmp_path).save_project(
        Project(slug="demo", name="Demo", base_url="https://app.example.com/signin",
                allowed_domains=["app.example.com"])
    )

    values = cns.real_values(tmp_path)

    assert "https://app.example.com/signin" not in values
    assert "hunter2-trombone-staple" in values


def test_a_real_secret_that_happens_to_differ_from_base_url_still_flags(tmp_path: Path) -> None:
    target = tmp_path / "leaky.md"
    target.write_text("REAL_SECRET=hunter2-trombone-staple", encoding="utf-8")
    (tmp_path / ".env").write_text("REAL_SECRET=hunter2-trombone-staple\n", encoding="utf-8")

    outcome = cns.scan([target], cns.real_values(tmp_path))

    assert outcome[target] is False  # not clean -- a real leak


def test_a_project_base_url_no_longer_flags_project_json_itself(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text(
        "SOME_LOGIN_URL=https://app.example.com/signin\n", encoding="utf-8"
    )
    store = ProjectStore("demo", tmp_path)
    store.save_project(
        Project(slug="demo", name="Demo", base_url="https://app.example.com/signin",
                allowed_domains=["app.example.com"])
    )

    outcome = cns.scan([store.paths.config], cns.real_values(tmp_path))

    assert outcome[store.paths.config] is True  # clean -- AT-037's regression case


def test_a_coincidental_non_url_secret_still_flags_even_if_it_matches_a_base_url(
    tmp_path: Path,
) -> None:
    """AT-038: excluding by bare VALUE alone (AT-037's first fix) meant a
    genuinely different secret that happened to coincide with a base_url
    string would go uncaught. Scoping the exclusion to URL-named keys closes
    that -- a coincidental match under a non-URL key must still be caught."""
    (tmp_path / ".env").write_text(
        "SOME_LOGIN_URL=https://app.example.com/signin\n"
        "OAUTH_CALLBACK_SECRET=https://app.example.com/signin\n",
        encoding="utf-8",
    )
    ProjectStore("demo", tmp_path).save_project(
        Project(slug="demo", name="Demo", base_url="https://app.example.com/signin",
                allowed_domains=["app.example.com"])
    )
    leaked = tmp_path / "some_artifact.json"
    leaked.write_text("callback: https://app.example.com/signin", encoding="utf-8")

    outcome = cns.scan([leaked], cns.real_values(tmp_path))

    assert outcome[leaked] is False  # OAUTH_CALLBACK_SECRET's coincidental leak is still caught
