"""The record rules: does the ledger still hold what the handshake recorded?

Split from `test_doctor.py` alongside the module it tests (AT-506). That file is
the rules over SOURCE -- line caps, function length, duplicated concepts, root
clutter. These are the rules over the project's own ACCOUNT of itself, and the
three units that wrote them (AT-496, AT-500, AT-504) are what pushed both files
toward their caps.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from autotester.ledger import checks

# -- AT-496: a handshake artifact naming an issue that has no ledger row -------


def _qa(root: Path, ledger: str, manifests: dict | None = None,
        verdicts: dict | None = None) -> None:
    (root / "qa").mkdir(parents=True, exist_ok=True)
    (root / "qa" / "issues.jsonl").write_text(ledger, encoding="utf-8")
    for kind, files in (("manifests", manifests or {}), ("verdicts", verdicts or {})):
        (root / "qa" / kind).mkdir(exist_ok=True)
        for name, body in files.items():
            (root / "qa" / kind / name).write_text(body, encoding="utf-8")


ROW = '{"id": "AT-900", "severity": "low", "title": "t", "status": "%s"}'


def test_an_issue_a_manifest_names_must_still_have_a_ledger_row(tmp_path: Path) -> None:
    """AT-496: two loops share this tree, and a commit built from a stale copy of
    qa/issues.jsonl drops rows another loop appended. AT-494's row vanished that way
    while its verdict stayed in git — so the verdict is what makes the loss visible."""
    _qa(tmp_path, ledger="", manifests={"u.md": "**Issues addressed:** AT-900 (low, open)"})

    codes = [(v.rule, v.location) for v in checks.check_qa_issue_rows(tmp_path)]

    assert ("ledger-row-lost", "qa/manifests/u.md") in codes


def test_an_issue_a_verdict_wrote_must_still_have_a_ledger_row(tmp_path: Path) -> None:
    _qa(tmp_path, ledger=ROW % "open",
        verdicts={"u.md": "ISSUES-WRITTEN: AT-900 (low), AT-901 (medium)"})

    lost = [(v.rule, v.detail) for v in checks.check_qa_issue_rows(tmp_path)]

    assert [r for r, d in lost if "AT-901" in d] == ["ledger-row-lost"], lost
    assert not any("AT-900" in d for _, d in lost), "AT-900 has a row; only AT-901 is missing"


def test_a_passed_unit_whose_issue_is_still_open_is_a_stale_row(tmp_path: Path) -> None:
    """AT-401's row was flipped to `fixed` by its PASS and then reverted to `open` by a
    later stale write. Nothing noticed, because the verdict file was still right."""
    _qa(tmp_path, ledger=ROW % "open",
        manifests={"u.md": "**Issues addressed:** AT-900 (low, open -> fixed)"},
        verdicts={"u.md": "VERDICT: PASS"})

    codes = [v.rule for v in checks.check_qa_issue_rows(tmp_path)]

    assert "ledger-row-stale" in codes


def test_a_passed_unit_whose_issue_is_fixed_is_not_flagged(tmp_path: Path) -> None:
    _qa(tmp_path, ledger=ROW % "fixed",
        manifests={"u.md": "**Issues addressed:** AT-900 (low, open -> fixed)"},
        verdicts={"u.md": "VERDICT: PASS"})

    assert checks.check_qa_issue_rows(tmp_path) == []


def test_a_failed_or_unchecked_unit_leaves_its_issue_open(tmp_path: Path) -> None:
    """Only a PASS is evidence the issue was closed; an open row is correct otherwise."""
    _qa(tmp_path, ledger=ROW % "open",
        manifests={"u.md": "**Issues addressed:** AT-900 (low, open -> fixed)"},
        verdicts={"u.md": "VERDICT: FAIL"})

    assert checks.check_qa_issue_rows(tmp_path) == []


def test_a_project_with_no_qa_directory_is_not_a_violation(tmp_path: Path) -> None:
    assert checks.check_qa_issue_rows(tmp_path) == []


@pytest.mark.parametrize("issue", ["AT-900", "AT-900b"])
def test_a_letter_suffixed_id_is_an_id_too(issue: str, tmp_path: Path) -> None:
    r"""AT-500: when two checkers file the same defect, the second row takes a letter
    suffix — AT-297b, AT-298b and AT-299b are live rows filed under that convention.
    Both regexes ended at a word boundary straight after the digits, and `\bAT-\d+\b`
    matches nothing at all inside `AT-297b`, so a manifest naming one was invisible."""
    _qa(tmp_path, ledger="", manifests={"u.md": f"**Issues addressed:** {issue} (low, open)"})

    lost = [(v.rule, v.detail) for v in checks.check_qa_issue_rows(tmp_path)]

    assert [r for r, d in lost if issue in d] == ["ledger-row-lost"], lost


@pytest.mark.parametrize("issue", ["AT-900", "AT-900b"])
def test_a_letter_suffixed_id_is_read_on_both_sides_of_the_comparison(
    issue: str, tmp_path: Path
) -> None:
    """Widening only the handshake side would turn every suffixed row into a phantom
    loss: the id is read a second time out of the LEDGER, and the two must agree or
    the check reports a row it is looking at as missing."""
    _qa(tmp_path, ledger=ROW.replace("AT-900", issue) % "open",
        manifests={"u.md": f"**Issues addressed:** {issue} (low, open -> fixed)"},
        verdicts={"u.md": "VERDICT: PASS"})

    codes = [v.rule for v in checks.check_qa_issue_rows(tmp_path)]

    assert codes == ["ledger-row-stale"], "the row EXISTS (never lost), it is only stale"


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


def test_an_issue_a_manifest_says_it_did_NOT_fix_stays_open(tmp_path: Path) -> None:
    """A manifest may name issues it filed and deliberately left open —
    `at227-first-paint-modal` names AT-335 that way. Reading "NOT fixed" as a fix
    claim made that unit's PASS look like a stale row."""
    _qa(tmp_path, ledger=ROW % "open",
        manifests={"u.md": "**Issues addressed:** AT-900 (filed, NOT fixed - reasons below)"},
        verdicts={"u.md": "VERDICT: PASS"})

    assert checks.check_qa_issue_rows(tmp_path) == []
