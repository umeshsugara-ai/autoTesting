"""How a claim BLOCK is read: which lines carry it, and where it ends.

Split from `test_ledger_checks.py` under AT-513, along the seam those tests already
had. That file asks what the check CONCLUDES about a ledger row — lost, stale, or
fine. This one asks what the check READS before it concludes anything: whether a line
carries a claim at all (AT-504), and where the block that carries it stops (AT-509,
AT-511).

Four consecutive units grew the original to 295 of C2's 300 lines, all four in this
half — the same evidence for both halves of the split.

`_qa` and `ROW` are imported rather than copied: one concept, one place.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from test_ledger_checks import ROW, _qa

from autotester.ledger import checks


@pytest.mark.parametrize("line", [
    "ISSUES-WRITTEN: AT-900",
    "**ISSUES-WRITTEN:** AT-900",
    "## ISSUES-WRITTEN: AT-900",
    "  - ISSUES-WRITTEN: AT-900",
])
def test_a_decorated_marker_line_is_still_a_marker_line(line: str, tmp_path: Path) -> None:
    """The AT-504 fix must not read the marker so strictly that real claims vanish.
    Both decorated forms are live: `at097-session-start-hook-regression.md` writes
    `**ISSUES-WRITTEN:**` and `at206-guards-that-guard.md` writes `## ISSUES-WRITTEN:`.
    Measured before the fix: a bare `startswith` would have dropped 12 real claims."""
    _qa(tmp_path, ledger="", verdicts={"u.md": line})

    assert [v.rule for v in checks.check_qa_issue_rows(tmp_path)] == ["ledger-row-lost"]


@pytest.mark.parametrize("line", [
    "on manifest `**Issues addressed:**` lines: AT-900 (at900-thing.md)",
    "none of them sits on a `**Issues addressed:**` line, so AT-900 is invisible",
])
def test_prose_that_quotes_the_marker_is_not_a_claim(line: str, tmp_path: Path) -> None:
    """AT-504: `marker in line` read a document DISCUSSING the marker as one USING it,
    so at500's own manifest counted itself and then its verdict counted too — the
    probe's violation count compounded 2 -> 3 -> 4 as each artifact appeared, without
    bound. A backtick is what separates the two cases; markdown decoration is not."""
    _qa(tmp_path, ledger="", manifests={"u.md": line})

    assert checks.check_qa_issue_rows(tmp_path) == []


def test_a_line_opening_with_the_marker_in_backticks_is_not_a_claim(tmp_path: Path) -> None:
    """The real shape from at500's own verdict, and the reason a backtick is not
    stripped as decoration: here the marker IS at the start of the line's content, so
    only the backtick separates prose from a claim."""
    _qa(tmp_path, ledger="",
        verdicts={"u.md": "`ISSUES-WRITTEN` marker. The only id it newly reads is AT-900."})

    assert checks.check_qa_issue_rows(tmp_path) == []


def test_an_id_on_a_continuation_line_is_still_named(tmp_path: Path) -> None:
    """AT-509: the block wraps. Both checks read only the first physical line, so an id
    on the continuation was examined by neither — invisible rather than mis-judged.
    Measured over the live manifests: 14 of them wrap, hiding 30 ids. AT-496 disclosed
    this as a limit and four units inherited the framing without testing it."""
    _qa(tmp_path, ledger="", manifests={"u.md":
        "**Issues addressed:** AT-900 (medium, open -> fixed) ·\nAT-901 (low, cycle-1 FAIL)\n"})

    lost = {d.split()[0] for v in checks.check_qa_issue_rows(tmp_path)
            for d in [v.detail] if v.rule == "ledger-row-lost"}

    assert lost == {"AT-900", "AT-901"}, "the wrapped half counts too"


def test_a_fix_claim_on_a_continuation_line_is_read(tmp_path: Path) -> None:
    """`at358-visual-order-detector.md` puts four ids and their parenthetical entirely
    on the wrapped line. A claim there must reach the stale check like any other."""
    _qa(tmp_path, ledger=ROW % "open",
        manifests={"u.md": "**Issues addressed:** the two halves are listed below ·\n"
                           "AT-900 (low, open -> fixed)\n"},
        verdicts={"u.md": "VERDICT: PASS"})

    assert [v.rule for v in checks.check_qa_issue_rows(tmp_path)] == ["ledger-row-stale"]


def test_a_verdict_block_ends_at_the_next_FIELD_not_at_a_blank_line(tmp_path: Path) -> None:
    """AT-509's own first fix got this wrong and the live tree caught it. A verdict is
    a run of labelled fields with no blank line between them, so walking to the blank
    line swallowed `EXPLANATION:` and reported two ids the explanation merely discussed
    — the AT-504 false-accusation shape, reintroduced by the fix for AT-509."""
    _qa(tmp_path, ledger="",
        verdicts={"u.md": "ISSUES-WRITTEN: AT-900 (low)\n"
                          "EXPLANATION: the widening newly reads AT-901, which has no row\n"})

    named = {d.split()[0] for v in checks.check_qa_issue_rows(tmp_path) for d in [v.detail]}

    assert named == {"AT-900"}, "AT-901 is discussed in the next field, not written by this one"


@pytest.mark.parametrize("tail", ["\n\nAT-901 lives in a later paragraph",
                                  "\n## Why AT-901 stays open"])
def test_the_block_ends_at_a_blank_line_or_a_heading(tail: str, tmp_path: Path) -> None:
    """The stop condition is what keeps this from swallowing the whole document. A
    markdown paragraph ends at a blank line or a new block; every one of the 14 live
    wrapped manifests terminates that way, so nothing past it is part of the claim."""
    _qa(tmp_path, ledger="",
        manifests={"u.md": f"**Issues addressed:** AT-900 (low, open){tail}\n"})

    named = {d.split()[0] for v in checks.check_qa_issue_rows(tmp_path) for d in [v.detail]}

    assert named == {"AT-900"}, "AT-901 is outside the block and must stay unread"


def test_a_field_label_carrying_a_parenthetical_still_ends_the_block(tmp_path: Path) -> None:
    """AT-511: the stop condition could not see a label with a parenthetical before its
    colon, so `**ISSUES KEPT OPEN (claimed fixed, not fixed):**` was swallowed as a
    continuation. Live in at097's and at176's verdicts — 6 ids misattributed to
    ISSUES-WRITTEN. `FAILURES (if any):` is the same shape in every verdict here."""
    _qa(tmp_path, ledger="",
        verdicts={"u.md": "ISSUES-WRITTEN: AT-900 (low)\n"
                          "ISSUES KEPT OPEN (claimed fixed, not fixed): AT-901\n"})

    named = {d.split()[0] for v in checks.check_qa_issue_rows(tmp_path) for d in [v.detail]}

    assert named == {"AT-900"}, "AT-901 belongs to the next field, not to this one"


def test_an_issue_id_with_a_parenthetical_is_not_a_field_label(tmp_path: Path) -> None:
    """The counter-direction, and the reason the rule keys on DIGITS. `AT-036 (filed in
    the previous unit): …` is a list item, not a new field. Measured: a rule that
    accepted any parenthetical before a colon would have matched 167 live lines, ending
    blocks early and re-creating the very misses AT-509 fixed."""
    _qa(tmp_path, ledger="",
        manifests={"u.md": "**Issues addressed:** AT-900 (low) ·\n"
                           "AT-901 (filed in the previous unit): why it stayed open\n"})

    named = {d.split()[0] for v in checks.check_qa_issue_rows(tmp_path) for d in [v.detail]}

    assert named == {"AT-900", "AT-901"}, "an id with a parenthetical is still a list item"


def test_a_code_fence_ends_the_block(tmp_path: Path) -> None:
    """Same root cause: a fence closes the block it belongs to, so nothing after it is
    part of the claim."""
    _qa(tmp_path, ledger="",
        verdicts={"u.md": "ISSUES-WRITTEN: AT-900 (low)\n```\nAT-901 is quoted below\n"})

    named = {d.split()[0] for v in checks.check_qa_issue_rows(tmp_path) for d in [v.detail]}

    assert named == {"AT-900"}
