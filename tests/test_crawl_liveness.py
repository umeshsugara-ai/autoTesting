"""AT-483: a crawl orphaned by a killed serving process is distinguishable from one
still running.

`stages/explore.py`'s `_bfs` used to persist `crawl.json` exactly twice (once before
the loop, once in `_finish`) — so a crawl killed mid-BFS froze at `status=running,
screens=0, actions=0` forever, although `nodes.jsonl`/`edges.jsonl` held real partial
progress (X11). `explore_node.py` now re-persists the envelope, with a `heartbeat_at`
timestamp, after the crawl's 1st action and every `heartbeat_every_actions`'th one
after that; `stages/explore_status.displayed_status` shows a RUNNING crawl whose
heartbeat has gone stale as ABORTED — the same display-only reuse it already makes
for BLOCKED_NO_ACTIONS (X18(d)), not a new `CrawlStatus` member (`schema/enums.py`
sits at its own 300-line cap). `crawl.json` itself is never rewritten by this check.

Contract: qa/contracts/explore.md X11 (incremental persistence), X16 (every surface
carries the one judged status), X18(c)/(d) (display honesty, legacy rule).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from crawl_fake import crawl_it

from autotester.schema.crawl import Crawl, CrawlBounds
from autotester.schema.enums import CrawlStatus
from autotester.stages.explore_status import displayed_status
from autotester.store.project_store import ProjectStore


def _running(**fields: object) -> Crawl:
    fields.setdefault("id", "crawl_live")
    return Crawl(project="demo", status=CrawlStatus.RUNNING, **fields)


# -- displayed_status: stale vs fresh vs legacy vs a finished crawl ----------

def test_a_stale_heartbeat_displays_as_interrupted() -> None:
    now = datetime(2026, 9, 17, 12, 0, 0, tzinfo=UTC)
    crawl = _running(
        heartbeat_at=(now - timedelta(seconds=200)).isoformat(),
        bounds=CrawlBounds(heartbeat_stale_after_s=90.0),
    )
    assert displayed_status(crawl, now=now) is CrawlStatus.ABORTED


def test_a_fresh_heartbeat_still_displays_as_running() -> None:
    now = datetime(2026, 9, 17, 12, 0, 0, tzinfo=UTC)
    crawl = _running(
        heartbeat_at=(now - timedelta(seconds=10)).isoformat(),
        bounds=CrawlBounds(heartbeat_stale_after_s=90.0),
    )
    assert displayed_status(crawl, now=now) is CrawlStatus.RUNNING


def test_a_legacy_crawl_json_with_no_heartbeat_field_loads_and_displays_unchanged(
    tmp_path: Path,
) -> None:
    """X18(d): `write_json` excludes None fields, so a crawl's own unset default for
    `heartbeat_at` already reproduces the exact byte-shape of a crawl.json written
    before this unit — no manual surgery needed to prove the shape. `extra='forbid'`
    only rejects UNKNOWN keys, so it loads fine, and with nothing to compare it is
    never flagged, however old the file."""
    store = ProjectStore("demo", tmp_path)
    store.save_crawl(_running(id="crawl_legacy"))
    manifest = store.paths.crawl_manifest("crawl_legacy")
    assert "heartbeat_at" not in json.loads(manifest.read_text(encoding="utf-8"))

    loaded = store.load_crawl("crawl_legacy")

    assert loaded is not None
    assert loaded.heartbeat_at is None
    far_future = datetime.now(UTC) + timedelta(days=30)
    assert displayed_status(loaded, now=far_future) is CrawlStatus.RUNNING


def test_a_completed_crawl_with_a_stale_heartbeat_is_unaffected() -> None:
    """The control: once a crawl is genuinely finished, its `status` is no longer
    RUNNING, so a heartbeat frozen hours ago — the normal end state, `_finish` never
    heartbeats again — must never flip its display."""
    now = datetime(2026, 9, 17, 12, 0, 0, tzinfo=UTC)
    crawl = Crawl(
        project="demo", status=CrawlStatus.COMPLETED, stop_reason="frontier empty",
        heartbeat_at=(now - timedelta(hours=5)).isoformat(),
        bounds=CrawlBounds(heartbeat_stale_after_s=90.0),
    )
    assert displayed_status(crawl, now=now) is CrawlStatus.COMPLETED


# -- the BFS itself persists progress mid-run --------------------------------

def test_the_bfs_persists_progress_and_a_heartbeat_before_the_crawl_finishes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A monkeypatched `heartbeat_every_actions=1` forces a write after the very
    first action on the fake site's several screens — proving the save happens
    DURING the BFS, not only at `_finish`, and that it carries real, non-zero
    counts: the AT-483 reproduction's frozen `screens=0, actions=0` never happens
    for a crawl whose process stays alive."""
    saved: list[Crawl] = []
    original = ProjectStore.save_crawl

    def spy(self: ProjectStore, crawl: Crawl) -> None:
        saved.append(crawl)
        original(self, crawl)

    monkeypatch.setattr(ProjectStore, "save_crawl", spy)

    crawl, _store, _page = crawl_it(tmp_path, bounds=CrawlBounds(heartbeat_every_actions=1))

    assert crawl.status is CrawlStatus.COMPLETED
    mid_run = saved[1:-1]  # [0] = the pre-BFS write (screens=0), [-1] = _finish's
    assert mid_run, "expected at least one heartbeat write between start and finish"
    assert any(
        c.status is CrawlStatus.RUNNING and c.heartbeat_at is not None
        and (c.actions > 0 or c.screens > 0)
        for c in mid_run
    )
