"""Design rules over the project's RECORDS, as opposed to its source files.

`doctor` enforces two different kinds of rule and they were living in one module.
The rules in `doctor.py` read `src/` and `tests/` and ask whether the code stayed
readable. The rules here read `docs/FEATURES.jsonl` and `qa/` and ask whether the
project's account of itself stayed true — whether a closed task has a ledger row,
whether an issue a handshake artifact names still exists, whether a PASSed unit's
issue is still open.

Split out under AT-506: three consecutive units (AT-496, AT-500, AT-504) grew
`doctor.py` from 264 to 287 lines against C2's 300-line cap, all three of them in
this half of the file, and `doctor` itself would have stayed silent until 301.
Nothing here changed behaviour — the split is the whole change.
"""

from __future__ import annotations

import re
from pathlib import Path

from autotester.core.paths import RepoDocs
from autotester.doctor import Violation

ISSUE_ID = r"AT-\d+[a-z]?"
r"""One issue id, in one place, for every regex below.

The letter suffix is not decoration: when two checkers file the same defect, the
second row takes one (AT-293's convention — AT-297b, AT-298b and AT-299b are live
rows). `\bAT-\d+\b` matches NOTHING inside `AT-297b`, so reading an id without this
made every suffixed row invisible to the whole check (AT-500)."""

_MARKER_LEAD = re.compile(r"^[\s>#*_-]*")
"""Markdown decoration before a marker, which is still the marker."""


def _is_marker_line(line: str, marker: str) -> bool:
    """Does this line MAKE the claim, or merely talk about lines that do (AT-504)?

    `marker in line` could not tell the difference, so a manifest documenting the
    guard counted itself, its verdict counted too, and the count compounded without
    bound as more documents discussed it. Measured over the live tree: decoration is
    common and load-bearing — `**ISSUES-WRITTEN:**` and `## ISSUES-WRITTEN:` are both
    real, and requiring a bare prefix would have silently dropped 12 true claims. A
    backtick is the thing that marks prose, so it is deliberately not stripped.
    """
    return _MARKER_LEAD.sub("", line).startswith(marker.strip("*"))


_FIXED = re.compile(r"\bfixed\b", re.IGNORECASE)
_NOT_FIXED = re.compile(r"\bnot\b[\w\s-]{0,15}?\bfixed\b", re.IGNORECASE)


def _claims_a_fix(note: str) -> bool:
    """Does this parenthetical claim the unit FIXED the issue (AT-508)?

    It was `"fixed" in note and "not fixed" not in note`, which read `unfixed`,
    `not-fixed`, `not yet fixed` and `prefixed` as fix claims. The direction is what
    made it serious: it accused a manifest that had correctly declared an issue
    unfixed of leaving a stale row — the one case this filter exists to protect —
    and a false accusation costs more than a miss. Live since AT-496; found by a
    fresh engineering review rather than by the four units built on top of it.

    Word boundaries settle `unfixed`/`prefixed` on their own. The negation stays a
    regex so it also catches a hyphen or a word in between, and its character class
    cannot cross punctuation, so a `not` belonging to another clause
    (`not a duplicate, open -> fixed`) does not swallow the claim. Measured over all
    54 distinct notes in the live manifests: not one changes verdict.
    """
    return bool(_FIXED.search(note)) and not _NOT_FIXED.search(note)


def check_ledger(root: Path) -> list[Violation]:
    """L2/L3: every FEATURES.jsonl row validates; closed high-value tasks have a row."""
    from autotester.ledger.store import check_rows_on_pass, load_events, load_goal_tasks

    docs = RepoDocs(root)
    try:
        events = load_events(docs.features)
    except Exception as exc:  # a doctor reports, it never tracebacks (AT-021)
        return [Violation("ledger-invalid", "docs/FEATURES.jsonl", f"{type(exc).__name__}: {exc}")]
    missing = check_rows_on_pass(events, load_goal_tasks(docs.goal))
    return [Violation("ledger-row-missing", task, "closed high-value task has no live/updated row")
            for task in missing]


def check_qa_issue_rows(root: Path) -> list[Violation]:
    """C10: the ledger never silently loses what the handshake recorded (AT-496).

    Two maker loops share this working tree. A commit built from a stale copy of
    `qa/issues.jsonl` drops rows the other loop appended and reverts statuses it
    flipped, and nothing noticed: AT-494's row vanished after its own PASS, and
    AT-401 went back to `open` a commit after being closed. The manifests and
    verdicts survive in git, so they are what makes the loss visible — an issue a
    handshake artifact names must have a row, and a PASSed unit's issue must not
    still be `open`.
    """
    ledger = root / "qa" / "issues.jsonl"
    if not ledger.exists():
        return []
    text = ledger.read_text(encoding="utf-8", errors="replace")
    status_of = dict(re.findall(rf'"id":\s*"({ISSUE_ID})".*?"status":\s*"(\w+)"', text))
    out: list[Violation] = []
    for kind, marker in (("manifests", "**Issues addressed:**"), ("verdicts", "ISSUES-WRITTEN")):
        for path in sorted((root / "qa" / kind).glob("*.md")):
            body = path.read_text(encoding="utf-8", errors="replace")
            named = {i for line in body.splitlines() if _is_marker_line(line, marker)
                     for i in re.findall(rf"\b{ISSUE_ID}\b", line)}
            subject = f"qa/{kind}/{path.name}"
            out += [Violation("ledger-row-lost", subject,
                              f"{issue} is named here but has no row in qa/issues.jsonl")
                    for issue in sorted(named - set(status_of))]
            if kind == "manifests" and _passed(root, path.name):
                # Only an issue this manifest CLAIMS to have fixed — "AT-x (low, open -> fixed)".
                # A line may also name issues it deliberately did NOT fix, and those stay open.
                claimed = {i for line in body.splitlines() if _is_marker_line(line, marker)
                           for i, note in re.findall(rf"\b({ISSUE_ID})\s*\(([^)]*)\)", line)
                           if _claims_a_fix(note)}
                out += [Violation("ledger-row-stale", subject,
                                  f"{issue} is still `open` although this unit PASSed")
                        for issue in sorted(claimed) if status_of.get(issue) == "open"]
    return out


def _passed(root: Path, name: str) -> bool:
    verdict = root / "qa" / "verdicts" / name
    return verdict.exists() and "VERDICT: PASS" in verdict.read_text(encoding="utf-8",
                                                                     errors="replace")
