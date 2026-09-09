"""Scoring AutoTester against a human tester's sheet — T-136.

The sharpest tests here read the REAL workbooks on disk. Every column-shape fact
was measured on `ERP_Issues_Trainers.xlsx` and `ERP_Issues_ALL.xlsx`
(`.work/track-a-corpus-facts.md`, 2026-09-08) and four of them contradicted the
plan. A hand-copied header is a claim about a file; these read the file.

Contract: qa/contracts/video-learning.md (T-136 acceptance).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from autotester.schema.enums import IssueCategory, Severity
from autotester.schema.issue import Issue
from autotester.stages.score import (
    RECORDING_COLUMNS,
    TruthRow,
    TruthSheetError,
    at_seconds,
    load_truth,
    recording_key,
    score,
)

CORPUS = Path("C:/Users/Lenovo/Videos/Screen Recordings")
TRAINERS, ALL_ISSUES = CORPUS / "ERP_Issues_Trainers.xlsx", CORPUS / "ERP_Issues_ALL.xlsx"
CLIP = "erp1.mp4 (Divya Kamboj, trainer pipeline)"


def a_row(**kw) -> TruthRow:
    return TruthRow(
        id=kw.pop("id", "E-01"),
        title=kw.pop("title", "Trainer cannot be moved past Shortlisted"),
        what_is_wrong=kw.pop("what_is_wrong", "Move reports Saving then silently reverts"),
        recording=kw.pop("recording", "erp1.mp4"),
        at_s=kw.pop("at_s", 29.0),
        row_number=kw.pop("row_number", 2),
    )


def an_issue(**kw) -> Issue:
    return Issue(
        project="erp",
        source_id=kw.pop("source_id", "src_1"),
        recording_label=kw.pop("recording_label", CLIP),
        at_s=kw.pop("at_s", 30.0),
        screen=kw.pop("screen", "Trainers"),
        title=kw.pop("title", "Trainer cannot be moved past Shortlisted"),
        what_is_wrong=kw.pop("what_is_wrong", "the Move button reverts with no message"),
        severity=kw.pop("severity", Severity.S1),
        category=kw.pop("category", IssueCategory.FEATURE_GAP),
        **kw)


# -- the two sheets do not share a schema ------------------------------------

@pytest.mark.skipif(not TRAINERS.exists(), reason="the real corpus is not on this host")
def test_the_trainers_sheet_loads_with_its_own_column_names() -> None:
    """`ERP_Issues_Trainers.xlsx` has 12 columns and calls the recording `Clip`.
    T-133's docstring claimed "the scorer accommodates both" while no scorer
    existed (AT-201) — this is that claim finally being true and checked."""
    rows = load_truth(TRAINERS, "Trainer module")

    assert len(rows) == 7, "the Trainer module sheet holds 7 measured rows"
    assert all(r.recording.startswith("erp") for r in rows)
    assert {r.at_s for r in rows} != {0.0}, "every At parsed to zero — MM:SS was not read"


@pytest.mark.skipif(not ALL_ISSUES.exists(), reason="the real corpus is not on this host")
def test_the_all_sheet_loads_though_it_names_the_column_differently() -> None:
    """13 columns, `Recording` not `Clip`, and **32** data rows — not the plan's
    33. A scorer that knew only one of the two names would silently match
    nothing here and report a recall of zero that looked like a measurement."""
    rows = load_truth(ALL_ISSUES, "All issues")

    assert len(rows) == 32
    assert all(r.title for r in rows)


def test_both_recording_column_names_are_known() -> None:
    """The offline half, so the shape stays pinned on a host without the corpus."""
    assert set(RECORDING_COLUMNS) == {"Clip", "Recording"}


# -- the four facts that each silently produce a recall of zero ---------------

@pytest.mark.parametrize("cell,expected", [
    ("00:29", 29.0), ("01:33", 93.0), ("10:00", 600.0), ("0:02", 2.0), (93.4, 93.4),
])
def test_times_are_read_the_way_the_human_sheet_writes_them(cell, expected) -> None:
    """Measured: the `At` column holds STRINGS. A scorer comparing a float to
    that cell matches nothing, silently."""
    assert at_seconds(cell) == expected


def test_an_unreadable_time_is_refused_not_scored_as_zero() -> None:
    """Second zero matches whatever opens the recording, so a bad cell would
    invent a match rather than report a problem."""
    with pytest.raises(TruthSheetError, match="MM:SS"):
        at_seconds("sometime around the start")


def test_the_clip_cell_is_a_filename_plus_prose_and_only_the_filename_matches() -> None:
    """The cell reads `erp1.mp4 (Divya Kamboj, trainer pipeline)`. Comparing the
    whole cell to a source label matches nothing."""
    assert recording_key(CLIP) == "erp1.mp4"
    assert recording_key("erp2.mp4") == "erp2.mp4"
    assert recording_key(CLIP) == recording_key("ERP1.MP4 (someone else)")


def test_a_sheet_with_no_recording_column_is_refused_by_name(tmp_path: Path) -> None:
    """Refused with the column names it looked for, so the reader can fix the
    sheet. My first version of this test passed a .py file and asserted my own
    error -- openpyxl raised its own first, so the test proved nothing about
    this code."""
    from openpyxl import Workbook

    book = Workbook()
    book.active.title = "Issues"
    book.active.append(["ID", "Title", "What is wrong", "At"])
    book.active.append(["E-01", "t", "w", "00:29"])
    path = tmp_path / "no-clip.xlsx"
    book.save(path)

    with pytest.raises(TruthSheetError, match="no recording column"):
        load_truth(path, "Issues")


def test_a_missing_sheet_names_the_sheets_that_do_exist(tmp_path: Path) -> None:
    from openpyxl import Workbook

    book = Workbook()
    book.active.title = "Issues"
    path = tmp_path / "one-sheet.xlsx"
    book.save(path)

    with pytest.raises(TruthSheetError, match="Issues"):
        load_truth(path, "Trainer module")


# -- matching: all three of recording, time and text ---------------------------

def test_the_same_fault_at_the_same_second_is_found() -> None:
    card = score([a_row()], [an_issue()])

    assert card.found == 1
    assert card.recall == 1.0
    assert card.false_positives == []


def test_the_same_text_in_a_different_recording_is_not_a_match() -> None:
    """Text alone would let one loud finding claim rows across every clip."""
    card = score([a_row(recording="erp2.mp4")], [an_issue()])

    assert card.found == 0
    assert len(card.false_positives) == 1


def test_the_same_text_far_away_in_time_is_not_a_match() -> None:
    card = score([a_row(at_s=29.0)], [an_issue(at_s=300.0)], window_s=20.0)

    assert card.found == 0


def test_unrelated_text_at_the_right_second_is_not_a_match() -> None:
    """Time alone would match whatever the model happened to say at that second."""
    card = score([a_row()], [an_issue(title="Logo is the wrong shade of blue",
                                      what_is_wrong="cosmetic tint difference in the header")])

    assert card.found == 0


def test_one_issue_cannot_claim_two_truth_rows() -> None:
    """Each truth row is claimed at most once, so a single report cannot inflate
    recall by matching everything near it."""
    rows = [a_row(id="E-01", at_s=29.0), a_row(id="E-02", at_s=31.0)]

    card = score(rows, [an_issue(at_s=30.0)])

    assert card.found == 1
    assert card.truth_rows == 2
    assert card.recall == 0.5


def test_an_unmatched_report_is_a_false_positive_not_silence() -> None:
    card = score([a_row()], [an_issue(), an_issue(at_s=200.0, title="Something else entirely",
                                                  what_is_wrong="unrelated")])

    assert card.found == 1
    assert len(card.false_positives) == 1


def test_scoring_nothing_against_seven_rows_is_recall_zero_and_says_so() -> None:
    """The honest shape of today's reality: no model has run, so there are no
    issues. The number is zero and the report says `reported: 0` — the CLI is
    what refuses to exit 0 on it."""
    card = score([a_row(), a_row(id="E-02")], [])

    assert (card.found, card.reported, card.recall) == (0, 0, 0.0)


def test_the_report_names_every_truth_row_found_or_not() -> None:
    """A recall figure with no per-row detail cannot be checked by the tester
    whose sheet it is."""
    report = score([a_row(id="E-01"), a_row(id="E-02", at_s=400.0)], [an_issue()]).as_dict()

    assert [r["id"] for r in report["per_row"]] == ["E-01", "E-02"]
    assert [r["found"] for r in report["per_row"]] == [True, False]
    assert report["recall"] == 0.5
