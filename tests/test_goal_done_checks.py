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
import re
import shlex
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
GOAL = REPO_ROOT / ".goal" / "goal.json"

ALWAYS_TRUE = ("true", ":", "exit 0")
"""Commands that cannot fail at all. AT-100's original was literally
`{"cmd": "true"}` on the live production ERP crawl."""


def tasks() -> list[dict]:
    return json.loads(GOAL.read_text(encoding="utf-8"))["tasks"]


SHELL_NEUTERING = ("|", "#", "`", "$(", ">", "<", "&")
"""Characters that can make a command's exit code mean something other than
what the command in front of them did. `pytest x.py | true`, `true # pytest
x.py`, `cmd > /dev/null || exit 0` — AT-158 measured four such families, all
admitted because the predicate looked at TOKENS rather than at what actually
runs. Rejected outright: a `done_check` needs none of them, and a waiver is
the way to ask for one."""

RUNNERS = ("uv", "run", "poetry", "pdm", "hatch", "env")
"""Wrapper words that precede the real program. `uv run pytest x.py` runs
pytest; the program is the first token that is not one of these."""


def _program(parts: list[str]) -> str:
    """The command that actually executes, not any token that resembles one.

    AT-158's root cause: this used to ask `"pytest" in parts`, so `echo pytest
    tests/x.py` and `true # pytest tests/x.py` both read as pytest invocations.
    A program name is only a program name in the program position."""
    for token in parts:
        if token in RUNNERS or "=" in token:
            continue
        return Path(token).name
    return ""


def _is_task_specific(segment: str) -> bool:
    """Does this ONE command depend on a particular task's deliverables?

    An ALLOWLIST (AT-155): a command qualifies only as a shape known to depend
    on a deliverable. Anything unrecognised is rejected and the way past that
    is a written `waiver`, not a cleverer command — a denylist on shell
    commands fails open by construction, which is what AT-154/AT-155 were.
    """
    if segment.strip() in ALWAYS_TRUE:
        return False
    if any(ch in segment for ch in SHELL_NEUTERING):
        return False
    try:
        parts = shlex.split(segment)
    except ValueError:
        return False  # unbalanced quotes: not a command anyone can reason about
    if not parts:
        return False
    program = _program(parts)
    if program == "check_deliverable.py" or any(
            p.endswith("check_deliverable.py") for p in parts[:3]):
        # Its own no-assertion guard exits 2, so a bare invocation always fails.
        return True
    if program == "pytest" or (program.startswith("python") and "-m" in parts
                               and "pytest" in parts):
        if any(p in ("--collect-only", "--co") for p in parts):
            return False  # collects without running: exit 0 on anything importable
        # A path is specific only when it names a FILE or a node id. `tests/`
        # is the whole suite wearing a path (AT-154).
        return any(p.endswith(".py") or "::" in p for p in parts)
    if program.startswith("python"):
        # AT-159: `python3` and a script outside scripts/ are the SAME shape
        # this branch was written for — an interpreter running a repo script.
        if "-c" in parts or "-m" in parts:
            return False
        return any(p.endswith(".py") for p in parts[1:])
    return False


def _is_bare_exit(segment: str) -> bool:
    """`exit`/`exit N` terminates the shell immediately -- nothing after it,
    across ANY separator, ever runs (AT-359 cycle 2)."""
    try:
        parts = shlex.split(segment)
    except ValueError:
        return False
    return len(parts) in (1, 2) and parts[0] == "exit"


def _truncate_after_first_exit(command: str) -> str:
    """Scan segments left to right across `;`/`&&` and cut after the first
    bare `exit`: `exit 0 && X` / `exit 0; X` both exit 0 without X ever
    running -- AT-100's shape wearing `exit` (checker FAIL, cycle 1). A
    trailing `exit` (e.g. `pytest x.py && exit 0`) is untouched."""
    parts = re.split(r"(;|&&)", command)
    for i in range(0, len(parts), 2):
        if _is_bare_exit(parts[i].strip()):
            return "".join(parts[:i + 1])
    return command


def is_capable_of_failing(command: str) -> bool:
    """Can this `done_check` distinguish done from not-started?

    `||` disqualifies the command anywhere; a leading/mid-chain bare `exit`
    hides everything after it (`_truncate_after_first_exit`). Otherwise `;`
    and `&&` score differently (AT-359): a `;`-sequence's exit status is its
    LAST group's alone; a `&&`-chain propagates the FIRST failure, so any
    task-specific segment in the group is enough regardless of what
    follows. AT-161's flatten-and-any() missed a `;`-terminated `echo`/`ls`
    and over-rejected `&& true` chains."""
    if "||" in command:
        return False
    command = _truncate_after_first_exit(command)
    groups = [g.strip() for g in command.split(";") if g.strip()]
    if not groups:
        return False
    last_group_segments = [s.strip() for s in groups[-1].split("&&") if s.strip()]
    if not last_group_segments:
        return False
    return any(_is_task_specific(seg) for seg in last_group_segments)


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
    offenders = offenders_in(tasks())
    assert offenders == [], (
        "these done_checks pass on a clean repo whether or not their task was "
        f"started, and carry no waiver: {offenders}")


def _referenced_py_files(command: str) -> list[str]:
    """Every `.py` path this command names, node id stripped (reuses
    `_is_task_specific`'s own notion of a file reference)."""
    try:
        parts = shlex.split(command)
    except ValueError:
        return []
    return [p.split("::", 1)[0] for p in parts if p.endswith(".py") or "::" in p]


def test_no_done_task_has_a_done_check_naming_a_file_that_does_not_exist() -> None:
    """Mirror image of the test above (AT-647): T-185 named
    `tests/test_scroll_reach.py`, which never existed, so a task whose real
    work was long finished elsewhere could never close on its own check — it
    LOOKS task-specific, so nothing else here catches it, and no amount of
    building makes it pass.

    Scoped to `status == "done"` only: a PENDING task's file legitimately
    doesn't exist yet (~19 pending tasks name unbuilt test files today, which
    is normal). Once a task is marked done its check is supposed to have
    already passed, so the file it names must be real -- `Path.is_file`,
    no build-status signal needed."""
    missing = {t["id"]: bad for t in tasks() if t["status"] == "done"
               for bad in [[f for f in _referenced_py_files(t.get("done_check", {}).get("cmd", ""))
                            if not (REPO_ROOT / f).is_file()]]
               if bad}
    assert missing == {}, (
        "these DONE tasks' done_checks name a file that does not exist on disk: "
        f"{missing}")


def _waiver_offenders(rows: list[dict]) -> list[str]:
    return [r["id"] for r in rows
            if r.get("done_check", {}).get("waiver") is not None
            and len(waiver_of(r)) < 20]


def test_no_task_on_disk_carries_an_empty_waiver() -> None:
    """A waiver is a written decision, so an empty or placeholder one is worse
    than none — it silences the guard while recording nothing."""
    assert _waiver_offenders(tasks()) == []


def test_the_waiver_rule_actually_rejects_a_hollow_waiver() -> None:
    """Sabotaging the waiver length check was INCONCLUSIVE when this was
    written — zero failures, because no task on disk carried a waiver at all
    yet (T-190 is now the first, AT-638), so the rule had no data to bite on
    (C7's new clause caught exactly that). A guard that is only ever asked
    about an empty set has not been shown to work, so it is asked here about
    rows built to break it, independent of whatever is on disk today."""
    hollow = [
        {"id": "T-x", "status": "pending", "done_check": {"cmd": "true", "waiver": ""}},
        {"id": "T-y", "status": "pending", "done_check": {"cmd": "true", "waiver": "wip"}},
    ]
    real = [{"id": "T-z", "status": "pending", "done_check": {
        "cmd": "true",
        "waiver": "no deliverable exists until the ERP credentials are entered"}}]
    assert _waiver_offenders(hollow) == ["T-x", "T-y"]
    assert _waiver_offenders(real) == []


def offenders_in(rows: list[dict]) -> list[str]:
    """The exact rule `test_no_pending_task_...` applies, extracted so it can
    be asserted on rows that do not exist on disk (AT-160)."""
    return [r["id"] for r in rows
            if r["status"] != "done" and r.get("done_check", {}).get("cmd")
            and not is_capable_of_failing(r["done_check"]["cmd"])
            and not waiver_of(r)]


def test_a_waived_task_is_exempt_and_an_unwaived_one_is_not() -> None:
    """AT-160: the previous version asserted the two helpers SEPARATELY and
    never their composition, so deleting `and not waiver_of(t)` from the
    offenders rule left the suite green — an unguarded exemption clause, which
    is C7's own INCONCLUSIVE class inside a test written to close it.
    This asserts the rule itself, on rows chosen so a broken composition cannot
    pass: one waived and one not, both otherwise identical."""
    waived = {"id": "T-w", "status": "pending", "done_check": {
        "cmd": "uv run autotester doctor",
        "waiver": "governance-only task with no artifact to assert on"}}
    unwaived = {"id": "T-u", "status": "pending",
                "done_check": {"cmd": "uv run autotester doctor"}}
    assert offenders_in([waived, unwaived]) == ["T-u"], (
        "the waiver must exempt exactly its own task and nothing else")
    assert offenders_in([waived]) == []
    assert offenders_in([unwaived]) == ["T-u"]


def test_every_pending_task_actually_has_a_done_check() -> None:
    """A missing check is the same defect as an unfailable one, minus the
    pretence."""
    missing = [t["id"] for t in tasks()
               if t["status"] != "done" and not t.get("done_check", {}).get("cmd")]
    assert missing == [], f"pending tasks with no done_check: {missing}"


def test_check_deliverable_reports_an_unreadable_path_instead_of_crashing() -> None:
    """AT-157. Sabotaging this was INCONCLUSIVE — nothing exercised it. The old
    code raised an unhandled traceback on a directory: still non-zero, so never
    unsafe, but a `done_check` that dies with a stack trace tells its reader
    nothing about what is missing, which is its whole job."""
    from check_deliverable import main
    assert main(["--contains", "src", "needle"]) == 1
    assert main(["--exists", "src/autotester/cli.py"]) == 0
    assert main([]) == 2, "a check with no assertion must not be able to pass"


# test_revised_goal_contract_is_registered moved to test_goal_contract_registration.py
# (AT-638: doctor's 300-line cap, and it is a different responsibility -- a one-off
# snapshot of the T-160..T-184 registration, not a goal.json-wide guard like the tests
# in this file).
