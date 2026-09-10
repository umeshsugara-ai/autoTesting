"""`autotester ingest run --merge` — the production caller of `merge_flowspec`.

AT-220 and AT-240 are the same scar twice: `analyze` and `expand` both shipped
checker-PASSed with zero production callers, so a stage that worked perfectly
under direct call was an absent feature in the product. `merge_flowspec` gets
its door in the same unit as itself, and these tests assert the FILE and the
request ledger — the oracle a green unit test would have missed.

Split from `test_merge_flowspec.py` at the 300-line cap (C2), the same way
`test_expand_cli.py` is split from `test_expand.py`.
"""

from __future__ import annotations

from pathlib import Path

from autotester.schema.enums import EvidenceKind, Outcome, ReviewStatus
from autotester.schema.flowspec import FlowSpec, Review, Screen
from autotester.schema.run import Evidence, RawResult
from autotester.stages.coverage import diff_coverage, queue_requests
from autotester.stages.merge_flowspec import open_requests
from autotester.store.project_store import ProjectStore


def screen(sid: str, name: str, url_pattern: str | None = None) -> Screen:
    return Screen(id=sid, name=name, url_pattern=url_pattern)


def make_result(case_id: str, *urls: str) -> RawResult:
    evidence = [Evidence(kind=EvidenceKind.URL, path=u) for u in urls]
    return RawResult(case_id=case_id, outcome=Outcome.COMPLETED, evidence=evidence)

# -- the door (coverage.md V6 / expand.md X6: a stage with no caller is absent) --
#
# AT-220 and AT-240 are the same scar twice: `analyze` and `expand` both shipped
# checker-PASSed with zero production callers. `merge_flowspec` gets its caller in
# the same unit, and these tests assert the FILE and the request ledger — the
# oracle a green unit test would have missed.

def _cli_bits():
    from typer.testing import CliRunner

    from autotester.cli import app
    return CliRunner(), app


def _seed_project_with_an_open_request(root: Path, monkeypatch) -> ProjectStore:
    from autotester.providers.mock import MockProvider
    from autotester.schema.observation import ObservedScreen, VideoObservation
    from autotester.schema.project import Project
    from autotester.stages.ingest import register_source

    monkeypatch.setenv("AUTOTESTER_ROOT", str(root))
    store = ProjectStore("demo", root)
    store.save_project(Project(slug="demo", name="Demo", base_url="https://demo.test",
                              allowed_domains=["demo.test"]))
    reviewed = screen("scr_1", "Sign in (reviewed by hand)", "https://demo.test/signin")
    store.save_flowspec(FlowSpec(
        project="demo", screens=[reviewed], version=3,
        review=Review(status=ReviewStatus.APPROVED, by="umesh", at="2026-09-10T00:00:00Z")))
    queue_requests(store, diff_coverage(
        store.load_flowspec(), [make_result("case_1", "https://demo.test/reports/new")]))

    video = root / "answer.mp4"
    video.write_bytes(b"fake-mp4")
    register_source(store, video, label="the answer")
    observation = VideoObservation(
        screens=[ObservedScreen(name="New report", t_start=1.0, t_end=4.0,
                                url="https://demo.test/reports/new")],
        flows=[], summary="Making a report.")
    provider = MockProvider(responses={"vision": [observation]})
    monkeypatch.setattr("autotester.cli_video.providers.get", lambda _id, **_kw: provider)
    return store


def test_the_cli_merges_into_an_approved_spec_instead_of_refusing(
    tmp_path: Path, monkeypatch
) -> None:
    """Without `--merge`, answering a VideoRequest against an APPROVED spec is
    impossible: `persist_ingest` refuses, and `--replace` would discard the very
    review the request was raised under."""
    store = _seed_project_with_an_open_request(tmp_path, monkeypatch)
    runner, app = _cli_bits()
    source_id = store.list_sources()[0].id

    result = runner.invoke(app, ["ingest", "run", "demo", source_id, "--merge"])

    assert result.exit_code == 0, result.output
    saved = ProjectStore("demo", tmp_path).load_flowspec()
    assert saved is not None
    # reviewed truth survived, and the recording's screen landed
    assert "Sign in (reviewed by hand)" in [s.name for s in saved.screens]
    assert "New report" in [s.name for s in saved.screens]
    assert saved.review.status is ReviewStatus.DRAFT


def test_the_cli_merge_closes_the_request_that_asked_for_the_recording(
    tmp_path: Path, monkeypatch
) -> None:
    store = _seed_project_with_an_open_request(tmp_path, monkeypatch)
    runner, app = _cli_bits()
    source_id = store.list_sources()[0].id
    assert len(open_requests(store)) == 1

    runner.invoke(app, ["ingest", "run", "demo", source_id, "--merge"])

    after = ProjectStore("demo", tmp_path)
    assert open_requests(after) == []
    assert after.list_requests()[0].fulfilled_by_source == source_id


def test_merge_and_replace_together_are_refused(tmp_path: Path, monkeypatch) -> None:
    """They are opposites — one keeps the review, the other discards it.
    Silently letting one win would decide a human's judgement by flag order."""
    store = _seed_project_with_an_open_request(tmp_path, monkeypatch)
    runner, app = _cli_bits()
    source_id = store.list_sources()[0].id

    result = runner.invoke(app, ["ingest", "run", "demo", source_id, "--merge", "--replace"])

    assert result.exit_code == 2
    assert ProjectStore("demo", tmp_path).load_flowspec().review.status is ReviewStatus.APPROVED
