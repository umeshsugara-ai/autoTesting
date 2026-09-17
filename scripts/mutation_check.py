"""Prove a unit's new tests are not vacuous, by killing them on purpose.

Contract: `qa/contracts/core-invariants.md` C7 — a unit that adds or rewrites a
test owes a mutation run showing each new test dies when the behaviour it names
is reverted. A test that passes against the code it was written to defend is
worse than no test: it reports safety that does not exist.

This exists because four vacuous tests shipped in one session (see
`qa/feedback-inbox.md` 2026-09-11), every one found by a checker's mutation run
and none by re-reading. The fifth was caught by running this instead of reading.

A mutation spec is JSON:

    {"mutations": [
      {"name": "port fallback removed",
       "file": "scripts/migrate_url_patterns.py",
       "old":  "    if a not in hosts and a.split(':')[0] not in hosts:",
       "new":  "    if a not in hosts:",
       "kills": ["test_a_pattern_carrying_a_port_matches_a_host_declared_without_one"]}
    ], "tests": "tests/test_migrate_url_patterns.py"}

    uv run python scripts/mutation_check.py qa/evidence/<unit>/mutations.json

**What this refuses, and why each refusal exists** (AT-307, AT-311 — both found
in this harness's own predecessor, which reported four confident kills while
naming a test that did not exist):

- A named test that is not collected. The predecessor's `defends:` label was
  decorative prose; it named a renamed test for four runs and nobody noticed.
- A red baseline. `KILLED` used to mean `exit != 0`, so an already-red suite
  certified every test non-vacuous — precisely when it matters, since a flake
  makes the suite red without anyone editing a test (AT-196).
- A collection error counted as a kill. A mutation that breaks the module's
  syntax exits non-zero having run NOTHING, which the predecessor reported as
  `KILLED  1 error` with an empty failure list.
- An unrelated failure counted as a kill. The suite going red is not evidence
  that THIS test noticed; only the named test in pytest's own failure reports is.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
from pathlib import Path

TIMED_OUT = -1  # pytest outlived its bound and was killed with its children (AT-487)
PYTEST_TIMEOUT_S = 1800.0  # per pytest run; a spec may lower it with "timeout_s"
KILL_GRACE_S = 30.0  # how long a killed process tree may take to actually go away
INTERRUPTED = 2  # pytest ran tests and was then interrupted — its failure reports are real
REPORT_PLUGIN = "_mutation_report"
PLUGIN_SOURCE = '''"""Written by mutation_check into its sandbox root; never part of a project."""
import json
import os

# Read once, when pytest loads the plugin: a test that reassigns or removes the variable
# must not redirect or break the report (AT-481).
_REPORT = os.environ["MUTATION_REPORT"]
_failed = set()


def pytest_runtest_logreport(report):
    if report.when == "call" and report.failed:
        _failed.add(report.nodeid)


def pytest_sessionfinish(session):
    with open(_REPORT, "w", encoding="utf-8") as handle:
        json.dump(sorted(_failed), handle)
'''


class MutationError(RuntimeError):
    """The run itself is invalid — not a verdict about any test."""


def is_kill(exit_code: int, expected: set[str], failures: set[str]) -> bool:
    """Whether a mutation was genuinely killed by the tests that claim to.

    Both clauses are load-bearing and neither implies the other:

    - `exit_code == 1` is "pytest ran tests and some failed". Any OTHER non-zero
      code means it produced no test result at all — a collection error exits 4,
      an internal error 3 — and the predecessor counted those as kills (AT-311).
    - `expected <= failures` is "the tests that CLAIM to notice actually did".
      A red suite is not evidence that THIS test noticed.

    Both clauses ARE reachable by mutation, and the pair is separated by an
    INTERRUPTED run: pytest exits 2 while printing the `FAILED` lines of tests
    that already failed, so `exit_code == 2` with `expected <= failures` says
    killed under a weakened `!= 0` and not-killed under the correct `== 1`.

    An earlier version of this docstring claimed no mutation could reach the
    first clause. That was false (AT-321): it assumed every non-1 non-zero exit
    is a *collection* error. The claim was falsified by one attempt, and it was
    the second unreachability claim from this maker to be. "I could not think of
    a mutation" is not "no mutation exists" — `test_an_interrupted_run_...`
    below is the mutation-reachable proof, and the table test remains as the
    cheaper direct assertion beside it.
    """
    if not expected:
        raise MutationError("a kill claimed by no test is not a kill (empty 'kills')")
    return exit_code == 1 and expected <= failures


def _targets(tests: str | list[str]) -> list[str]:
    """`tests` may name one file or several — a suite split at the 300-line cap
    (C2) is still ONE suite for mutation purposes, and running only half of it
    would let a mutation look survived because its test lives in the other half."""
    return [tests] if isinstance(tests, str) else list(tests)


def _run_pytest(cwd: Path, tests: str | list[str], *extra: str,
                timeout: float = PYTEST_TIMEOUT_S) -> tuple[int, str]:
    """Run pytest in the sandbox with the report plugin, which sits in the sandbox's
    parent (`_sandbox` writes it) so it is never inside the tree under test.

    Bounded (AT-487): a mutation can make pytest loop forever. Output goes to a file,
    not a pipe, because a test's child process inherits the handle and a pipe reader
    then waits for that child as well; on timeout the whole process tree is killed."""
    # PYTHONUTF8: the log is a file, whose encoding is the locale's unless forced, so a
    # refusal would otherwise quote replacement characters for what pytest printed.
    env = dict(os.environ, MUTATION_REPORT=str(_report_path(cwd)), PYTHONUTF8="1",
               PYTHONPATH=os.pathsep.join(filter(None, [str(cwd.parent),
                                                        os.environ.get("PYTHONPATH")])))
    _report_path(cwd).unlink(missing_ok=True)
    log = cwd.parent / "mutation-pytest.log"
    with open(log, "w", encoding="utf-8") as sink:
        proc = subprocess.Popen(
            [sys.executable, "-m", "pytest", *_targets(tests), "-o", "addopts=", "-q",
             "--no-header", "-p", "no:cacheprovider", "-p", REPORT_PLUGIN, *extra],
            cwd=cwd, stdout=sink, stderr=subprocess.STDOUT, env=env,
            start_new_session=os.name != "nt")
        try:
            code = proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            _kill_tree(proc)
            code = TIMED_OUT
    out = log.read_text(encoding="utf-8", errors="replace")
    if code == TIMED_OUT:
        out += f"{chr(10)}pytest did not finish within {timeout:g}s; killed with its children"
    return code, out


def _kill_tree(proc: subprocess.Popen, posix: bool = os.name != "nt") -> None:
    """Kill pytest and everything it started, and wait a BOUNDED time for it (AT-490).

    taskkill's exit code is not the signal: it is non-zero whenever some child had
    already exited. Whether pytest itself is gone is, so a survivor is refused. On
    POSIX the session can exit between the timeout and the kill (AT-491)."""
    if posix:
        with contextlib.suppress(ProcessLookupError):
            os.killpg(proc.pid, signal.SIGKILL)
    else:
        with contextlib.suppress(subprocess.TimeoutExpired):  # the wait below decides
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                           capture_output=True, check=False, timeout=KILL_GRACE_S)
    try:
        proc.wait(timeout=KILL_GRACE_S)
    except subprocess.TimeoutExpired as exc:
        raise MutationError(f"pytest (pid {proc.pid}) survived a kill of its process tree "
                            f"for {KILL_GRACE_S:g}s") from exc


def _report_path(cwd: Path) -> Path:
    return cwd.parent / "mutation-report.json"


def collected_tests(cwd: Path, tests: str | list[str],
                    timeout: float = PYTEST_TIMEOUT_S) -> dict[str, set[str]]:
    """Every collected test, as `bare name -> {full nodeid, ...}`.

    AT-320: a bare name is NOT an identifier. Both sides used to
    `split("::")[-1]`, so a same-named test in another file or class satisfied
    attribution and a mutation could be reported killed by a module it never
    touched — verbatim AT-311's second failure mode, inside the fix for AT-311.
    """
    code, out = _run_pytest(cwd, tests, "--collect-only", timeout=timeout)
    if code != 0:
        raise MutationError(
            f"cannot collect {tests}: pytest exit {code}" + chr(10) + out[-2000:])
    collected: dict[str, set[str]] = {}
    for line in out.splitlines():
        nodeid = line.strip()
        if "::" in nodeid and not nodeid.startswith(("FAILED", "ERROR")):
            # Keyed BOTH ways (AT-324). The ambiguity guard tells the author to
            # "name the full nodeid", and keying only on the bare name meant that
            # remedy was then refused as "not collected" — a guard whose own
            # instruction does not work. Live in this repo: two test files share
            # `test_act_without_a_schema_raises`.
            collected.setdefault(nodeid.split("::")[-1], set()).add(nodeid)
            collected.setdefault(nodeid, {nodeid})
    return collected


def failed_tests(cwd: Path) -> set[str]:
    """Full nodeids of the tests that FAILED in the last run in `cwd` (AT-320), as
    pytest itself reported them: `report.nodeid` of every failed call phase.

    AT-478/AT-479: this used to scan `^FAILED` over the whole text output. Captured
    stdout could print a summary line for a sibling that passed, a spaced parametrize
    id had to be recovered by guessing where the nodeid ended (AT-469/AT-473), and a
    renamed id's line could fit a baseline nodeid that never ran. Each was a false
    KILLED or a false SURVIVED. The structured report has none of those failure modes:
    it names exactly the tests that ran and failed. No report (pytest never reached
    session end) means no failures, which can only read SURVIVED."""
    try:
        return set(json.loads(_report_path(cwd).read_text(encoding="utf-8")))
    except (OSError, ValueError):
        return set()


def _sandbox(repo: Path) -> tuple[Path, Path]:
    """A copy OUTSIDE the repo, so a mutation can never touch the live tree.

    Returns `(work, owned_root)`. `owned_root` is the temp directory THIS call
    created, and is the only thing cleanup is ever allowed to delete — see
    `_discard`.
    """
    owned_root = Path(tempfile.mkdtemp(prefix="mutation-check-"))
    work = owned_root / "repo"
    for directory in ("scripts", "tests", "src"):
        if (repo / directory).is_dir():
            shutil.copytree(repo / directory, work / directory,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for name in ("pyproject.toml", "conftest.py"):
        if (repo / name).is_file():
            shutil.copy2(repo / name, work / name)
    (owned_root / f"{REPORT_PLUGIN}.py").write_text(PLUGIN_SOURCE, encoding="utf-8")
    return work, owned_root


def _discard(owned_root: Path) -> None:
    """Delete a sandbox this module created, and refuse anything else.

    AT-325 was a leak: `_sandbox` copied scripts/ tests/ src/ per run and never
    removed them — 1824 `mutation-check-*` trees had accumulated, and C7 makes
    these runs mandatory, so it grows with every unit.

    The containment check is not ceremony. The first fix deleted
    `work.parent`, which is correct only while `work` really is a sandbox — and
    this module's own mutation spec contains `work = repo`, which would have
    turned cleanup into "delete the real tree's parent". A destructive operation
    keyed on an unverified path is AT-314 wearing different clothes.

    What this actually enforces is ownership **by convention** — under the system
    temp dir AND carrying this module's prefix — not ownership by creation
    (AT-329). It cannot tell its own sandbox from a concurrent run's, which is
    exactly why `check()` never sweeps by glob: it deletes only the root handed
    to it by its own `_sandbox` call.
    """
    root = owned_root.resolve()
    temp = Path(tempfile.gettempdir()).resolve()
    if not root.is_relative_to(temp) or not root.name.startswith("mutation-check-"):
        raise MutationError(
            f"refusing to delete {root} — cleanup may only remove a sandbox this "
            f"module created under {temp}")
    shutil.rmtree(root, ignore_errors=True)


def _inside(work: Path, relative: str, name: str) -> Path:
    """Resolve `relative` inside the sandbox, or refuse.

    AT-314: `work / mutation["file"]` looks contained and is not — pathlib
    DISCARDS the left operand for an absolute right one, and `../` climbs out,
    so a spec could mutate the live tree while the docstring promised it could
    not. A promise the code does not enforce is the same defect class as a test
    that does not test.
    """
    resolved = (work / relative).resolve()
    root = work.resolve()
    if not resolved.is_relative_to(root):
        raise MutationError(
            f"mutation {name!r}: file {relative!r} resolves outside the sandbox "
            f"({resolved}). Mutations may only touch the copy.")
    if not resolved.is_file():
        raise MutationError(f"mutation {name!r}: {relative!r} is not a file in the sandbox")
    return resolved


def check(spec: dict, repo: Path) -> list[dict]:
    """Run every mutation. Returns one result per mutation."""
    tests = spec["tests"]
    mutations = spec["mutations"]
    if not mutations:
        raise MutationError("spec declares no mutations")

    work, owned_root = _sandbox(repo)
    try:
        return _check_in(work, spec, tests, mutations)
    finally:
        _discard(owned_root)


def _timeout(spec: dict) -> float:
    value = spec.get("timeout_s", PYTEST_TIMEOUT_S)
    if isinstance(value, bool) or not isinstance(value, int | float) or value <= 0:
        raise MutationError(f"'timeout_s' must be a positive number of seconds, got {value!r}")
    return float(value)


def _check_in(work: Path, spec: dict, tests: str | list[str], mutations: list) -> list[dict]:
    timeout = _timeout(spec)
    collected = collected_tests(work, tests, timeout)

    # Every named test must EXIST before anything is mutated. A label naming a
    # renamed test is the exact defect AT-311 was filed for.
    for mutation in mutations:
        if not mutation.get("kills"):
            raise MutationError(
                f"mutation {mutation['name']!r} names no test in 'kills'. An unattributed "
                f"kill is exactly the defect this instrument exists to refuse (AT-313).")
        missing = [t for t in mutation["kills"] if t not in collected]
        if missing:
            raise MutationError(
                f"mutation {mutation['name']!r} names test(s) that are not collected: "
                f"{missing}. A 'kills' label is a claim, not a comment.")
        # AT-320: an ambiguous name cannot attribute a kill to anything.
        ambiguous = {t: sorted(collected[t]) for t in mutation["kills"] if len(collected[t]) > 1}
        if ambiguous:
            raise MutationError(
                f"mutation {mutation['name']!r} names test(s) that collect more than once: "
                f"{ambiguous}. A bare name is not an identifier — name the full nodeid.")
        mutation["_nodeids"] = {next(iter(collected[t])) for t in mutation["kills"]}

    code, out = _run_pytest(work, tests, timeout=timeout)
    if code != 0:
        raise MutationError(
            f"baseline is NOT green (pytest exit {code}) — every kill below would be "
            f"meaningless:\n{out[-2000:]}")

    results = []
    for mutation in mutations:
        target = _inside(work, mutation["file"], mutation["name"])
        original = target.read_text(encoding="utf-8")
        occurrences = original.count(mutation["old"])
        if occurrences != 1:
            raise MutationError(
                f"mutation {mutation['name']!r}: anchor matched {occurrences} times in "
                f"{mutation['file']} (need exactly 1)")
        target.write_text(original.replace(mutation["old"], mutation["new"], 1),
                          encoding="utf-8", newline="\n")
        if target.read_text(encoding="utf-8") == original:
            raise MutationError(f"mutation {mutation['name']!r} changed nothing")

        code, out = _run_pytest(work, tests, timeout=timeout)
        failures = failed_tests(work)
        expected = mutation["_nodeids"]  # full nodeids, resolved at validation (AT-320)
        # A kill is the NAMED test failing. Not a non-zero exit (that includes a
        # collection error, which runs nothing), and not some other test failing.
        survivors = sorted(expected - failures)
        killed = is_kill(code, expected, failures)

        target.write_text(original, encoding="utf-8", newline="\n")
        if target.read_text(encoding="utf-8") != original:
            raise MutationError(f"could not restore {mutation['file']}")

        results.append({
            "name": mutation["name"], "killed": killed, "exit": code,
            "expected": sorted(expected), "failed": sorted(failures), "survivors": survivors,
            # AT-322: exit 2 is INTERRUPTED, not "collected nothing" — a run
            # can be interrupted after real tests have already failed. Claiming
            # pytest ran nothing about a run that produced results is the same
            # false-report class this instrument exists to refuse.
            "no_test_results": code not in (0, 1) and not failures,
            "timed_out": code == TIMED_OUT,
        })
    return results


def report(results: list[dict]) -> int:
    worst = 0
    for r in results:
        status = "KILLED" if r["killed"] else ">>> SURVIVED"
        print(f"{status}  {r['name']}  (pytest exit {r['exit']})")
        print(f"    claims to kill : {', '.join(r['expected'])}")
        print(f"    actually failed: {', '.join(r['failed']) or '(nothing)'}")
        if r["survivors"]:
            # AT-323: a survivor is INCONCLUSIVE, not proven vacuous. C7's
            # zero-failure clause forbids the stronger word on this evidence —
            # the mutation may simply not have changed observable behaviour.
            print(f"    SURVIVING      : {', '.join(r['survivors'])}"
                  f"  <- INCONCLUSIVE: this mutation did not make them fail")
        if r.get("timed_out"):
            print("    NOTE: pytest timed out and was killed — a hang is not a kill")
        if r["no_test_results"]:
            print("    NOTE: pytest produced no test results — not a kill")
        if not r["killed"]:
            worst = 1
    print()
    print(f"{sum(r['killed'] for r in results)}/{len(results)} mutations killed")
    return worst


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prove a unit's new tests are not vacuous.")
    parser.add_argument("spec", type=Path, help="path to the mutation spec JSON")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)

    try:
        results = check(json.loads(args.spec.read_text(encoding="utf-8")), args.repo)
    except MutationError as exc:
        print(f"MUTATION RUN INVALID: {exc}")
        return 2
    return report(results)


if __name__ == "__main__":
    sys.exit(main())
