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
  that THIS test noticed; only the named test appearing in FAILED is.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

FAILED = re.compile(r"^FAILED\s+(?P<nodeid>\S+)", re.MULTILINE)
NO_TESTS_RAN = 5  # pytest's exit code when the selection collects nothing


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

    Exposed as a function because a mutation cannot prove the first clause: a
    collection error yields no `FAILED` lines, so the second clause fails too and
    a weakened `exit_code != 0` survives every mutation (AT-315 — a vacuous test
    inside the instrument built to catch vacuous tests). It is asserted directly.
    """
    if not expected:
        raise MutationError("a kill claimed by no test is not a kill (empty 'kills')")
    return exit_code == 1 and expected <= failures


def _run_pytest(cwd: Path, tests: str, *extra: str) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", tests, "-o", "addopts=", "-q", "--no-header",
         "-p", "no:cacheprovider", *extra],
        cwd=cwd, capture_output=True, text=True)
    return proc.returncode, proc.stdout + proc.stderr


def collected_tests(cwd: Path, tests: str) -> set[str]:
    """Test function names pytest can actually collect."""
    code, out = _run_pytest(cwd, tests, "--collect-only")
    if code != 0:
        raise MutationError(f"cannot collect {tests}: pytest exit {code}\n{out[-2000:]}")
    return {line.split("::")[-1].strip() for line in out.splitlines() if "::" in line}


def failed_tests(output: str) -> set[str]:
    return {m.group("nodeid").split("::")[-1] for m in FAILED.finditer(output)}


def _sandbox(repo: Path) -> Path:
    """A copy OUTSIDE the repo, so a mutation can never touch the live tree."""
    work = Path(tempfile.mkdtemp(prefix="mutation-check-")) / "repo"
    for directory in ("scripts", "tests", "src"):
        if (repo / directory).is_dir():
            shutil.copytree(repo / directory, work / directory,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for name in ("pyproject.toml", "conftest.py"):
        if (repo / name).is_file():
            shutil.copy2(repo / name, work / name)
    return work


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

    work = _sandbox(repo)
    available = collected_tests(work, tests)

    # Every named test must EXIST before anything is mutated. A label naming a
    # renamed test is the exact defect AT-311 was filed for.
    for mutation in mutations:
        if not mutation.get("kills"):
            raise MutationError(
                f"mutation {mutation['name']!r} names no test in 'kills'. An unattributed "
                f"kill is exactly the defect this instrument exists to refuse (AT-313).")
        missing = [t for t in mutation["kills"] if t not in available]
        if missing:
            raise MutationError(
                f"mutation {mutation['name']!r} names test(s) that are not collected: "
                f"{missing}. A 'kills' label is a claim, not a comment.")

    code, out = _run_pytest(work, tests)
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

        code, out = _run_pytest(work, tests)
        failures = failed_tests(out)
        expected = set(mutation["kills"])
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
            "collected_nothing": code in (NO_TESTS_RAN, 2, 3, 4),
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
            print(f"    SURVIVING      : {', '.join(r['survivors'])}  <- vacuous for its property")
        if r["collected_nothing"]:
            print("    NOTE: that exit code means pytest ran nothing — not a kill")
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
