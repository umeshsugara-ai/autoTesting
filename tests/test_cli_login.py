"""CLI wiring for `autotester login`. Contract: qa/contracts/manual-login.md ML4."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from autotester import cli
from autotester.schema.project import Project
from autotester.store import ProjectStore

runner = CliRunner()


@pytest.fixture
def scratch_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("AUTOTESTER_ROOT", str(tmp_path))
    return tmp_path


def test_login_refuses_an_unknown_project(scratch_root: Path) -> None:
    result = runner.invoke(cli.app, ["login", "nope"])
    assert result.exit_code == 1
    assert "no project" in result.output


def test_login_calls_manual_login_for_a_real_project(
    scratch_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ProjectStore("demo", scratch_root).save_project(
        Project(slug="demo", name="Demo", base_url="https://demo.test",
                allowed_domains=["demo.test"])
    )
    called = {}
    monkeypatch.setattr(
        cli.manual_login_stage, "manual_login",
        lambda project, *a, **kw: called.setdefault("project", project.slug),
    )

    result = runner.invoke(cli.app, ["login", "demo"])

    assert result.exit_code == 0
    assert called["project"] == "demo"
    assert "session saved" in result.output
