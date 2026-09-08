"""A `done_check` must be able to fail — C9 for the second of its three fields.

C9 says a declared control value is honoured or rejected, never silently
ignored. Its Verify clause tested only `base_criticality`; nothing anywhere
pinned `done_check` (AT-141). Meanwhile T-126, T-150 and T-135 all carried
`uv run autotester doctor` — which passes on a clean repo whether or not the
task it guards has been started, so it would have reported "done" for work
nobody had done (AT-100, AT-115).

That is the AT-100 shape three times, not the twice AT-115 recorded, and it
lives in the machinery that decides whether anything is finished.

The guard is deliberately STATIC. Running every pending task's `done_check` for
real would take minutes and would itself pass once the work landed — the
property worth pinning is not "it fails today" but "it is *capable* of failing",
i.e. it names something specific to this task rather than asserting the repo is
healthy.
"""

from __future__ import annotations

import json
import shlex
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
GOAL = REPO_ROOT / ".goal" / "goal.json"

REPO_WIDE = (
    "autotester doctor",   # green on a clean repo, whatever the task is
    "autotester map",
    "autotester snapshot",
    "ruff check",
)
"""Commands whose result is a property of the REPO, not of any one task. A
`done_check` built only from these cannot distinguish done from not-started."""

ALWAYS_TRUE = ("true", ":", "exit 0")
"""Commands that cannot fail at all. AT-100's original was literally
`{"cmd": "true"}` on the live production ERP crawl — and my first cut of
`_is_repo_wide` did not catch it, because I wrote the predicate against the
three offenders in front of me instead of against the shape's own history.
The guard's self-test caught that, which is exactly what it is for."""


def tasks() -> list[dict]:
    return json.loads(GOAL.read_text(encoding="utf-8"))["tasks"]


def _is_repo_wide(command: str) -> bool:
    """True when this single command says nothing about a specific task."""
    if command.strip() in ALWAYS_TRUE:
        return True
    if any(marker in command for marker in REPO_WIDE):
        return True
    parts = shlex.split(command)
    if "pytest" in parts:
        # A bare `pytest` runs the whole suite: green once the repo is green,
        # regardless of the task. `pytest tests/test_thing.py` is specific.
        return not any(p.endswith(".py") or p.startswith("tests") for p in parts)
    return False


def is_capable_of_failing(command: str) -> bool:
    """Does any part of this check depend on the task's own deliverables?"""
    segments = [s.strip() for s in command.replace("&&", ";").split(";") if s.strip()]
    return any(not _is_repo_wide(seg) for seg in segments)


def test_no_pending_task_has_a_done_check_that_cannot_fail() -> None:
    """The AT-100 shape. `{"cmd": "true"}` was the first instance and is gone;
    `uv run autotester doctor` on a task about governance is the same defect
    wearing a plausible command."""
    offenders = [
        (t["id"], t["done_check"]["cmd"])
        for t in tasks()
        if t["status"] != "done" and t.get("done_check", {}).get("cmd")
        and not is_capable_of_failing(t["done_check"]["cmd"])
    ]

    assert offenders == [], (
        "these done_checks pass on a clean repo whether or not their task was "
        f"started: {offenders}")


def test_every_pending_task_actually_has_a_done_check() -> None:
    """A missing check is the same defect as an unfailable one, minus the
    pretence."""
    missing = [t["id"] for t in tasks()
               if t["status"] != "done" and not t.get("done_check", {}).get("cmd")]

    assert missing == [], f"pending tasks with no done_check: {missing}"


def test_the_guard_recognises_the_shapes_it_exists_to_catch() -> None:
    """A guard whose own predicate is wrong protects nothing — so the predicate
    is pinned against the real commands from this repo's history."""
    assert not is_capable_of_failing("uv run autotester doctor")           # T-126, T-150
    assert not is_capable_of_failing("uv run pytest -q && uv run autotester doctor")  # T-135
    assert not is_capable_of_failing("true")                              # AT-100's original

    assert is_capable_of_failing("uv run pytest tests/test_explore.py -q")
    assert is_capable_of_failing("uv run python scripts/check_crawl_approval.py erp")
    assert is_capable_of_failing(
        "uv run python scripts/check_deliverable.py --exists qa/contracts/ai-target.md "
        "&& uv run autotester doctor")


def test_the_three_known_offenders_are_actually_fixed() -> None:
    """AT-115 recorded two; measuring found three. Named individually so a
    regression on any one of them fails loudly rather than being absorbed into
    the aggregate above."""
    by_id = {t["id"]: t for t in tasks()}

    for task_id in ("T-126", "T-135", "T-150"):
        cmd = by_id[task_id]["done_check"]["cmd"]
        assert is_capable_of_failing(cmd), f"{task_id} regressed to {cmd!r}"
