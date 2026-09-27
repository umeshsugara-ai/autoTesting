"""T-191/AT-587 V5: at most the 20 most recently created kept videos survive,
project-wide, chosen by `(run_id, case order within that run)` -- never
filesystem `mtime` (two videos written the same second are indistinguishable
by it; `run_id` is a ULID and already sorts lexicographically by creation
time). Contract: qa/contracts/run-video.md V5. Fixture-only, no real browser:
this unit is a pure filesystem/store operation over pre-seeded evidence.
"""

from __future__ import annotations

from pathlib import Path

from autotester.schema.enums import EvidenceKind, Outcome
from autotester.schema.project import Project
from autotester.schema.run import Evidence, RawResult, Run
from autotester.stages.video_retention import prune_old_videos
from autotester.store.project_store import ProjectStore

RUNS = {  # run_id -> case ids, in `Run.case_ids` order -- lexicographic run_id order
    "run-a-0001": [f"case-a{i}" for i in range(10)],   # oldest
    "run-b-0002": [f"case-b{i}" for i in range(8)],
    "run-c-0003": [f"case-c{i}" for i in range(7)],    # newest -- 25 videos total
}


def _seed_25_kept_videos(tmp_path: Path) -> ProjectStore:
    store = ProjectStore("demo", tmp_path)
    store.save_project(Project(slug="demo", name="Demo", base_url="https://demo.test",
                               allowed_domains=["demo.test"]))
    for run_id, case_ids in RUNS.items():
        store.save_run(Run(id=run_id, project="demo", case_ids=case_ids))
        run_dir = store.paths.run_dir(run_id)
        for case_id in case_ids:
            rel = f"{case_id}.webm"
            (run_dir / rel).write_bytes(f"video bytes for {case_id}".encode())
            store.save_result(run_id, RawResult(
                case_id=case_id, outcome=Outcome.COMPLETED,
                evidence=[Evidence(kind=EvidenceKind.VIDEO, path=rel, masked=True)],
            ))
    return store


def test_pruning_25_kept_videos_to_20_drops_exactly_the_5_oldest_by_run_and_case_order(
    tmp_path: Path,
) -> None:
    store = _seed_25_kept_videos(tmp_path)

    deleted = prune_old_videos(store, keep=20)

    assert sorted(deleted) == sorted(f"case-a{i}.webm" for i in range(5))
    for i in range(5):
        assert not (store.paths.run_dir("run-a-0001") / f"case-a{i}.webm").exists()
    for i in range(5, 10):
        assert (store.paths.run_dir("run-a-0001") / f"case-a{i}.webm").exists()
    for run_id in ("run-b-0002", "run-c-0003"):
        for case_id in RUNS[run_id]:
            assert (store.paths.run_dir(run_id) / f"{case_id}.webm").exists()


def test_pruned_videos_evidence_row_is_removed_from_its_raw_result(tmp_path: Path) -> None:
    """A report must never link a file the prune already deleted (V8's report
    link would 404 on a dangling path otherwise)."""
    store = _seed_25_kept_videos(tmp_path)

    prune_old_videos(store, keep=20)

    pruned_results = {r.case_id: r for r in store.load_results("run-a-0001")}
    for i in range(5):
        result = pruned_results[f"case-a{i}"]
        assert not any(e.kind is EvidenceKind.VIDEO for e in result.evidence)
    for i in range(5, 10):
        result = pruned_results[f"case-a{i}"]
        assert any(e.kind is EvidenceKind.VIDEO for e in result.evidence)


def test_a_second_prune_on_the_same_state_is_a_no_op(tmp_path: Path) -> None:
    store = _seed_25_kept_videos(tmp_path)
    first = prune_old_videos(store, keep=20)
    assert len(first) == 5

    second = prune_old_videos(store, keep=20)

    assert second == []


def test_pruning_when_at_or_under_the_limit_deletes_nothing(tmp_path: Path) -> None:
    store = ProjectStore("demo", tmp_path)
    store.save_project(Project(slug="demo", name="Demo", base_url="https://demo.test",
                               allowed_domains=["demo.test"]))
    store.save_run(Run(id="run-only", project="demo", case_ids=["case-0", "case-1"]))
    for case_id in ("case-0", "case-1"):
        rel = f"{case_id}.webm"
        (store.paths.run_dir("run-only") / rel).write_bytes(b"x")
        store.save_result("run-only", RawResult(
            case_id=case_id, outcome=Outcome.COMPLETED,
            evidence=[Evidence(kind=EvidenceKind.VIDEO, path=rel, masked=True)],
        ))

    assert prune_old_videos(store, keep=20) == []
    assert (store.paths.run_dir("run-only") / "case-0.webm").exists()
    assert (store.paths.run_dir("run-only") / "case-1.webm").exists()
