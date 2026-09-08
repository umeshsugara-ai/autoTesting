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

ALWAYS_TRUE = ("true", ":", "exit 0")
"""Commands that cannot fail at all. AT-100's original was literally
`{"cmd": "true"}` on the live production ERP crawl."""


def tasks() -> list[dict]:
    return json.loads(GOAL.read_text(encoding="utf-8"))["tasks"]


def _is_task_specific(segment: str) -> bool:
    """Does this ONE command depend on a particular task's deliverables?

    AT-154/AT-155 -- this used to be a denylist (`_is_repo_wide`), and a
    denylist on shell commands fails OPEN by construction: every shape I had
    not thought of was accepted. The checker measured seven false negatives,
    including one INSIDE my own stated logic -- `pytest tests/` is the whole
    suite, and the directory `tests/` satisfied the same `startswith("tests")`
    the docstring said made a check specific.

    So this is an allowlist. A command is task-specific only if it is a shape
    known to depend on a deliverable. Anything unrecognised is rejected, and
    the way past that is a written `waiver`, not a cleverer command.
    """
    if segment.strip() in ALWAYS_TRUE:
        return False
    parts = shlex.split(segment)
    if not parts:
        return False

    if any(p.endswith("check_deliverable.py") for p in parts):
        # Its own no-assertion guard exits 2, so a bare invocation always fails.
        return True

    if "pytest" in parts:
        if "--collect-only" in parts:
            return False  # collects without running: exit 0 on anything importable
        # A path is specific only when it names a FILE or a node id. `tests/`
        # is the whole suite wearing a path.
        return any(p.endswith(".py") or "::" in p for p in parts)

    if "python" in parts or any(p.endswith("python") for p in parts):
        scripts = [p for p in parts if p.endswith(".py") and "scripts" in p]
        return bool(scripts) and not any(p == "-c" for p in parts)

    return False


def is_capable_of_failing(command: str) -> bool:
    """Can this `done_check` distinguish done from not-started?

    Every segment is examined, and `||` disqualifies the whole command: a
    trailing `|| true` neuters anything in front of it, so there is no
    interesting question left to ask about the rest."""
    if "||" in command:
        return False
    segments = [s.strip() for s in command.replace("&&", ";").split(";") if s.strip()]
    return bool(segments) and any(_is_task_specific(seg) for seg in segments)


def waiver_of(task: dict) -> str:
    return str(task.get("done_check", {}).get("waiver") or "").strip()


def test_no_pending_task_has_a_done_check_that_cannot_fail() -> None:
    """The AT-100 shape. `{"cmd": "true"}` was the first instance; `uv run
    autotester doctor` on a governance task is the same defect wearing a
    plausible command; `pytest tests/` is it wearing a path.

    A task whose check genuinely cannot be made specific may carry
    `done_check.waiver: "<why>"`. That is the point of an allowlist: the
    escape hatch is a sentence someone wrote and can be grepped for, not a
    command shape nobody noticed."""
    offenders = [
        (t["id"], t["done_check"]["cmd"])
        for t in tasks()
        if t["status"] != "done" and t.get("done_check", {}).get("cmd")
        and not is_capable_of_failing(t["done_check"]["cmd"])
        and not waiver_of(t)
    ]

    assert offenders == [], (
        "these done_checks pass on a clean repo whether or not their task was "
        f"started, and carry no waiver: {offenders}")


def _waiver_offenders(rows: list[dict]) -> list[str]:
    return [r["id"] for r in rows
            if r.get("done_check", {}).get("waiver") is not None
            and len(waiver_of(r)) < 20]


def test_no_task_on_disk_carries_an_empty_waiver() -> None:
    """A waiver is a written decision, so an empty or placeholder one is worse
    than none — it silences the guard while recording nothing."""
    assert _waiver_offenders(tasks()) == []


def test_the_waiver_rule_actually_rejects_a_hollow_waiver() -> None:
    """Sabotaging the waiver length check was INCONCLUSIVE — zero failures,
    because no task on disk carries a waiver at all, so the rule had no data
    to bite on (C7's new clause caught exactly that). A guard that is only
    ever asked about an empty set has not been shown to work, so it is asked
    here about rows that would break it."""
    hollow = [
        {"id": "T-x", "status": "pending", "done_check": {"cmd": "true", "waiver": ""}},
        {"id": "T-y", "status": "pending", "done_check": {"cmd": "true", "waiver": "wip"}},
    ]
    real = [{"id": "T-z", "status": "pending", "done_check": {
        "cmd": "true",
        "waiver": "no deliverable exists until the ERP credentials are entered"}}]

    assert _waiver_offenders(hollow) == ["T-x", "T-y"]
    assert _waiver_offenders(real) == []


def test_a_waived_task_is_exempt_from_the_unfailable_check() -> None:
    """The other half: a waiver must actually buy the exemption, or nobody
    would write one."""
    waived = {"id": "T-w", "status": "pending", "done_check": {
        "cmd": "uv run autotester doctor",
        "waiver": "governance-only task with no artifact to assert on"}}

    assert not is_capable_of_failing(waived["done_check"]["cmd"])
    assert waiver_of(waived)


def test_every_pending_task_actually_has_a_done_check() -> None:
    """A missing check is the same defect as an unfailable one, minus the
    pretence."""
    missing = [t["id"] for t in tasks()
               if t["status"] != "done" and not t.get("done_check", {}).get("cmd")]

    assert missing == [], f"pending tasks with no done_check: {missing}"


def test_the_guard_recognises_the_shapes_it_exists_to_catch() -> None:
    """A guard whose own predicate is wrong protects nothing. Every command
    below was measured by the checker against the real repo (AT-154/AT-155);
    each REJECTED one exits 0 today regardless of any task's state."""
    rejected = [
        "true",                                        # AT-100's original
        "uv run autotester doctor",                    # T-126, T-150
        "uv run pytest -q && uv run autotester doctor",  # T-135
        "uv run pytest tests/ -q",                     # AT-154: the whole suite as a path
        "uv run pytest tests",
        "uv run pytest -q tests/",
        "uv run pytest --collect-only tests/test_x.py",  # collects, never runs
        "echo done",
        'uv run python -c "pass"',
        "test -f README.md",
        "ls src/autotester/stages/merge_flowspec.py || true",   # `||` neuters anything
        "uv run pytest tests/test_explore.py -q || exit 0",
        "true # tests/test_x.py",
    ]
    for command in rejected:
        assert not is_capable_of_failing(command), f"accepted an unfailable check: {command!r}"

    accepted = [
        "uv run pytest tests/test_explore.py -q",
        "uv run pytest tests/test_explore.py::test_one",
        "uv run python scripts/check_crawl_approval.py erp",
        "uv run python scripts/check_deliverable.py --exists qa/contracts/ai-target.md "
        "&& uv run autotester doctor",
    ]
    for command in accepted:
        assert is_capable_of_failing(command), f"rejected a legitimate check: {command!r}"


def test_the_three_known_offenders_are_actually_fixed() -> None:
    """AT-115 recorded two; measuring found three. Named individually so a
    regression on any one of them fails loudly rather than being absorbed into
    the aggregate above."""
    by_id = {t["id"]: t for t in tasks()}

    for task_id in ("T-126", "T-135", "T-150"):
        cmd = by_id[task_id]["done_check"]["cmd"]
        assert is_capable_of_failing(cmd), f"{task_id} regressed to {cmd!r}"


def test_check_deliverable_reports_an_unreadable_path_instead_of_crashing() -> None:
    """AT-157. Sabotaging this was INCONCLUSIVE — nothing exercised it. The old
    code raised an unhandled traceback on a directory: still non-zero, so never
    unsafe, but a `done_check` that dies with a stack trace tells its reader
    nothing about what is missing, which is its whole job."""
    from check_deliverable import main

    assert main(["--contains", "src", "needle"]) == 1
    assert main(["--exists", "src/autotester/cli.py"]) == 0
    assert main([]) == 2, "a check with no assertion must not be able to pass"
