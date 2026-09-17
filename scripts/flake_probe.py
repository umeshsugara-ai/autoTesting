"""Measure a flaky test's real failure rate — and say how little N green runs prove.

AT-335: the modal crawl lost the dismissed-dashboard screen once, and the maker who
filed it tried 13 times to reproduce it, got 13 greens, and honestly recorded the
fix as unproven rather than claiming it could not happen.

That was the right call for the wrong arithmetic. **Thirteen green runs do not
exclude a 1-in-14 defect — they barely constrain it at all.** With zero failures in
13 runs the 95% upper bound on the true rate is ~20.6%, and the suspected rate is
7.1%, which sits comfortably underneath. To have a 95% chance of *seeing* a
1-in-14 flake you need 41 runs. "I could not reproduce it" was a statement about
the sample size, not about the bug.

So this harness does not fix anything and does not hunt the cause. It turns
"I tried and it didn't happen" into a number with a bound on it, which is the
prerequisite for anyone ever claiming AT-335 is fixed: a fix verified against 13
green runs would be exactly the unfalsifiable claim C7 forbids.

    python scripts/flake_probe.py <pytest-nodeid> --runs 41

Exit 0 whether or not failures were seen — a probe reports, it does not judge.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mutation_check import kill_tree  # one bounded-kill implementation, not two (AT-494)

CONFIDENCE = 0.95
TIMED_OUT = -1
"""A run that never answered. Its own returncode, so `failed` needs no special case
and a hang can never be counted as a green run (AT-401)."""
RUN_TIMEOUT_S = 1800.0
"""Per run. The subject is a browser crawl, which hangs as readily as it fails."""
SUSPECTED_RATE = 1 / 14
"""AT-335's own estimate — one lost screen in fourteen runs."""


def ceiling_given_no_failures(runs: int, confidence: float = CONFIDENCE) -> float:
    """The highest true failure rate still consistent with `runs` clean runs.

    `1 - (1-confidence)**(1/n)` — the exact inverse of `runs_for_confidence`, NOT
    the familiar rule-of-three shortcut `3/n`. The shortcut is an approximation
    that overstates the bound, and here that is not a rounding detail: it made
    this module's two functions contradict each other. `runs_for_confidence` said
    41 runs suffice for a 7.1% flake, while `3/n` put the bound after 41 runs at
    7.3% — still above 7.1%, i.e. "run 41 times" followed by "41 was not enough".
    A tool whose two halves disagree about the same question is worse than no
    tool; my own consistency test is what surfaced it.

    This is the number missing from AT-335: without it "13 green" reads as
    evidence of absence when it is barely evidence of anything."""
    if runs <= 0:
        raise ValueError("a bound needs at least one run")
    return 1.0 - (1.0 - confidence) ** (1.0 / runs)


def runs_for_confidence(rate: float, confidence: float = CONFIDENCE) -> int:
    """Runs needed for a `confidence` chance of seeing a rate-`rate` flake at least once."""
    if not 0.0 < rate < 1.0:
        raise ValueError("a rate must be strictly between 0 and 1")
    return math.ceil(math.log(1.0 - confidence) / math.log(1.0 - rate))


@dataclass(frozen=True)
class Run:
    """One invocation. `failed` is the only thing the statistics read."""

    index: int
    returncode: int
    seconds: float
    tail: str = ""
    """Last few lines, kept only for a failure — the whole point is to have the
    evidence in hand when the rare run finally lands."""

    @property
    def failed(self) -> bool:
        return self.returncode != 0

    @property
    def timed_out(self) -> bool:
        """Distinct from a failure with a verdict: nothing was measured, and saying so
        is the point — an unattended probe that silently lost a trial reports a rate
        computed from fewer trials than it claims (AT-401)."""
        return self.returncode == TIMED_OUT


@dataclass(frozen=True)
class Summary:
    nodeid: str
    runs: list[Run] = field(default_factory=list)
    confidence: float = CONFIDENCE

    @property
    def failures(self) -> list[Run]:
        return [run for run in self.runs if run.failed]

    @property
    def observed_rate(self) -> float | None:
        """None when nothing ran — an empty probe has no rate, not a rate of zero."""
        return len(self.failures) / len(self.runs) if self.runs else None

    @property
    def ceiling(self) -> float | None:
        """Only meaningful with zero failures; otherwise the observed rate is the answer."""
        if not self.runs or self.failures:
            return None
        return ceiling_given_no_failures(len(self.runs), self.confidence)


def describe(summary: Summary, suspected: float = SUSPECTED_RATE) -> list[str]:
    """Human-readable lines. The bound is stated whether or not it flatters us."""
    if not summary.runs:
        return [f"{summary.nodeid}: no runs"]

    count = len(summary.runs)
    lines = [f"{summary.nodeid}: {len(summary.failures)} failure(s) in {count} run(s)"]
    for failure in summary.failures:
        verdict = "TIMED OUT" if failure.timed_out else f"FAILED (rc={failure.returncode})"
        lines.append(f"  run {failure.index} {verdict} ({failure.seconds:.1f}s)")
    needed = runs_for_confidence(suspected, summary.confidence)
    if summary.failures:
        lines.append(f"  observed rate {summary.observed_rate:.1%} — reproduced, "
                     f"evidence captured")
        return lines

    ceiling = summary.ceiling
    assert ceiling is not None
    lines.append(
        f"  zero failures bounds the true rate at {ceiling:.1%} "
        f"({summary.confidence:.0%} confidence) — NOT at zero")
    verdict = "does NOT exclude" if suspected <= ceiling else "excludes"
    lines.append(
        f"  the suspected {suspected:.1%} rate is {'inside' if suspected <= ceiling else 'outside'}"
        f" that bound, so this probe {verdict} it; "
        f"{needed} runs are needed for a {summary.confidence:.0%} chance of seeing it")
    return lines


def run_once(nodeid: str, index: int, timeout: float = RUN_TIMEOUT_S) -> Run:
    """One pytest invocation, isolated from the cache so runs do not inform each other.

    Bounded (AT-401): the probe exists to repeat a run unattended, so one hang used to
    stop the whole probe with nothing recorded.

    Output goes to a FILE, and the timeout kills the whole process tree (AT-494). A pipe
    would not be bounded at all here: `subprocess.run`'s timeout kills pytest and then
    drains the pipe, which waits for every holder of the write end — and this probe's own
    subject is a browser crawl, whose browser is exactly such a holder. `kill_tree` is
    `mutation_check`'s, not a second copy: AT-487/AT-490 are the same defect in the
    sibling script, and one bounded-kill implementation is the point."""
    started = time.monotonic()
    log = Path(tempfile.gettempdir()) / f"flake-probe-{os.getpid()}-{index}.log"
    notes = ""
    try:
        with open(log, "w", encoding="utf-8") as sink:
            proc = subprocess.Popen(
                [sys.executable, "-m", "pytest", nodeid, "-q", "-p", "no:cacheprovider",
                 "-o", "addopts="],
                stdout=sink, stderr=subprocess.STDOUT, env=dict(os.environ, PYTHONUTF8="1"),
                start_new_session=os.name != "nt")
            try:
                code = proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                code = TIMED_OUT
                try:
                    kill_tree(proc)
                except RuntimeError as unkilled:  # MutationError: the tree outlived the kill
                    notes = f"{chr(10)}{unkilled}"
        output = log.read_text(encoding="utf-8", errors="replace")
    finally:
        log.unlink(missing_ok=True)
    elapsed = time.monotonic() - started
    if code == TIMED_OUT:
        return Run(index=index, returncode=code, seconds=elapsed,
                   tail=f"the run did not finish within {timeout:g}s and was killed with its "
                        f"children{notes}{chr(10)}{_tail(output)}".rstrip())
    return Run(index=index, returncode=code, seconds=elapsed,
               tail="" if code == 0 else _tail(output))


def _tail(output: str, lines: int = 25) -> str:
    return "\n".join(output.splitlines()[-lines:])


def probe(nodeid: str, runs: int, timeout: float = RUN_TIMEOUT_S) -> Summary:
    """Run it `runs` times, stopping for nothing — a probe that stops at the first
    failure cannot measure a rate, only confirm an existence. A timed-out run is one
    of the trials, not the end of the probe."""
    return Summary(nodeid=nodeid,
                   runs=[run_once(nodeid, index, timeout) for index in range(1, runs + 1)])


def write_report(summary: Summary, out: Path) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "nodeid": summary.nodeid,
        "runs": len(summary.runs),
        "failures": len(summary.failures),
        "observed_rate": summary.observed_rate,
        "ceiling_at_confidence": summary.ceiling,
        "confidence": summary.confidence,
        "detail": [{"index": r.index, "returncode": r.returncode,
                    "seconds": round(r.seconds, 2), "timed_out": r.timed_out,
                    "tail": r.tail} for r in summary.runs],
    }, indent=2), encoding="utf-8")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("nodeid", help="pytest node id, e.g. tests/test_x.py::test_y")
    parser.add_argument("--runs", type=int, default=runs_for_confidence(SUSPECTED_RATE))
    parser.add_argument("--out", type=Path,
                        default=Path(".work") / "flake-probe.json")
    parser.add_argument("--timeout", type=float, default=RUN_TIMEOUT_S,
                        help="seconds one run may take before it is killed and recorded "
                             "as TIMED OUT")
    args = parser.parse_args(argv)
    if args.timeout <= 0:
        print("--timeout must be a positive number of seconds")
        return 2

    summary = probe(args.nodeid, args.runs, args.timeout)
    for line in describe(summary):
        print(line)
    print(f"report: {write_report(summary, args.out)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
