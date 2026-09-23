"""T-163 driver: the resumable learn-or-explore orchestrator (orchestrator.md).

Covers OR1 (mode chosen once, with a recorded reason), OR2 (resume never re-runs
a done stage), OR4 (a raising stage leaves a failed checkpoint that resume
re-enters), OR5 (one run_id keys one lineage). OR3/OR6 live in
test_orchestrate_runners.py, which exercises the concrete stage adapters.

Fully offline: the stages are mock runners, driven against a temp project dir —
no browser, network, or model. Each OR row in the manifest carries a single-hunk
falsifying edit reproduced red->green.
"""

from __future__ import annotations

from pathlib import Path

from autotester.schema.enums import SourceKind
from autotester.schema.project import Project, Source
from autotester.schema.run_state import RunState, StageName
from autotester.stages.orchestrate import (
    StageContext,
    choose_mode,
    run_or_resume,
)
from autotester.store.filestore import read_json
from autotester.store.project_store import ProjectStore


def _store(tmp_path: Path, *sources: Source) -> ProjectStore:
    store = ProjectStore("demo", tmp_path)
    store.save_project(Project(slug="demo", name="Demo", base_url="https://demo.test",
                               allowed_domains=["demo.test"]))
    for source in sources:
        store.add_source(source)
    return store


def _video(name: str = "a") -> Source:
    return Source(project="demo", kind=SourceKind.VIDEO, path=f"/tmp/{name}.mp4",
                  sha256=f"sha-{name}")


def _url() -> Source:
    return Source(project="demo", kind=SourceKind.URL, url="https://demo.test")


class _Recorder:
    """A mock StageRunner that counts calls and parks a tiny artifact whose bytes
    are the call number — so a re-run that should NOT fire is caught by an
    unchanged count and unchanged bytes."""

    def __init__(self, tmp_path: Path, name: str, *, fail_times: int = 0) -> None:
        self.calls = 0
        self.fail_times = fail_times
        self.path = tmp_path / f"{name}.txt"

    def __call__(self, ctx: StageContext, prev_ref: str | None) -> str:
        self.calls += 1
        if self.calls <= self.fail_times:
            raise RuntimeError("boom")
        self.path.write_text(str(self.calls), encoding="utf-8")
        return str(self.path)


# -- OR1 -------------------------------------------------------------------

def test_choose_mode_learn_records_why() -> None:
    mode, reason = choose_mode([_video()])
    assert mode == "learn"
    assert "teaching sources present" in reason and "video" in reason


def test_choose_mode_explore_records_why() -> None:
    mode, reason = choose_mode([_url()])
    assert mode == "explore"
    assert "credentials bootstrap" in reason


def test_teaching_material_drives_a_learn_run(tmp_path: Path) -> None:
    """OR1: a project with a teaching Source takes the INGEST path, and the
    choice + reason are written to RunState (never silently defaulted)."""
    ctx = StageContext(store=_store(tmp_path, _video()), run_id="run_learn")
    state = run_or_resume(Project(slug="demo", name="D", base_url="https://demo.test"), ctx)
    assert state.mode == "learn"
    assert state.stages[0].stage is StageName.INGEST
    assert state.mode_reason  # non-empty reason recorded
    assert read_json(ctx.store.paths.run_dir("run_learn") / "state.json", RunState).mode == "learn"


def test_credentials_only_drives_an_explore_run(tmp_path: Path) -> None:
    """OR1: no teaching Source -> the DISCOVER path, reason recorded."""
    ctx = StageContext(store=_store(tmp_path, _url()), run_id="run_expl")
    state = run_or_resume(Project(slug="demo", name="D", base_url="https://demo.test"), ctx)
    assert state.mode == "explore"
    assert state.stages[0].stage is StageName.DISCOVER
    assert "DISCOVER" in state.mode_reason


# -- OR2 -------------------------------------------------------------------

def test_resume_never_reruns_a_done_stage(tmp_path: Path) -> None:
    """OR2: once INGEST is done, a second run_or_resume does not call its runner
    again and does not rewrite its artifact."""
    store = _store(tmp_path, _video())
    ingest = _Recorder(tmp_path, "ingest")
    ctx = StageContext(store=store, run_id="run1", runners={StageName.INGEST: ingest})
    project = Project(slug="demo", name="D", base_url="https://demo.test")

    first = run_or_resume(project, ctx)
    assert ingest.calls == 1
    assert first.checkpoint(StageName.INGEST).status == "done"
    assert ingest.path.read_text(encoding="utf-8") == "1"

    run_or_resume(project, ctx)
    assert ingest.calls == 1, "a done stage was re-run"
    assert ingest.path.read_text(encoding="utf-8") == "1", "a done stage's artifact was rewritten"


# -- OR4 -------------------------------------------------------------------

def test_a_raising_stage_leaves_a_failed_checkpoint_then_resume_re_enters(
    tmp_path: Path,
) -> None:
    """OR4: a stage that raises is recorded failed with a non-empty error and no
    artifact_ref (never done); the next run re-enters exactly that stage."""
    store = _store(tmp_path, _video())
    ingest = _Recorder(tmp_path, "ingest", fail_times=1)
    ctx = StageContext(store=store, run_id="run1", runners={StageName.INGEST: ingest})
    project = Project(slug="demo", name="D", base_url="https://demo.test")

    first = run_or_resume(project, ctx)
    failed = first.checkpoint(StageName.INGEST)
    assert failed.status == "failed"
    assert failed.error and "boom" in failed.error
    assert failed.artifact_ref is None
    assert first.next_pending().stage is StageName.INGEST  # resume pointer sits on it

    second = run_or_resume(project, ctx)
    assert ingest.calls == 2, "resume did not re-enter the failed stage"
    assert second.checkpoint(StageName.INGEST).status == "done"
    assert second.checkpoint(StageName.INGEST).artifact_ref is not None


# -- OR5 -------------------------------------------------------------------

def test_two_run_ids_keep_separate_lineages(tmp_path: Path) -> None:
    """OR5: two runs (distinct run_ids, one project) each read and write only
    their own state.json — neither sees the other's checkpoints."""
    store = _store(tmp_path, _video())
    project = Project(slug="demo", name="D", base_url="https://demo.test")
    rec_a = _Recorder(tmp_path, "a")
    rec_b = _Recorder(tmp_path, "b")
    ctx_a = StageContext(store=store, run_id="run_a", runners={StageName.INGEST: rec_a})
    ctx_b = StageContext(store=store, run_id="run_b", runners={StageName.INGEST: rec_b})

    run_or_resume(project, ctx_a)
    run_or_resume(project, ctx_b)

    path_a = store.paths.run_dir("run_a") / "state.json"
    path_b = store.paths.run_dir("run_b") / "state.json"
    assert path_a != path_b
    state_a = read_json(path_a, RunState)
    state_b = read_json(path_b, RunState)
    assert state_a.run_id == "run_a" and state_b.run_id == "run_b"
    assert state_a.checkpoint(StageName.INGEST).artifact_ref == str(rec_a.path)
    assert state_b.checkpoint(StageName.INGEST).artifact_ref == str(rec_b.path)
    assert state_a.checkpoint(StageName.INGEST).artifact_ref != \
        state_b.checkpoint(StageName.INGEST).artifact_ref
