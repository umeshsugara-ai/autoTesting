"""ISSUES: turn an adjudicated analysis into rows a human tester can read.

Contract: qa/contracts/video-learning.md VL5/VL6. Pure over artifacts on
disk — no provider, no network.

The Excel columns are not this system's choice. They are the columns Vidysea's
own testers already use in `ERP_Issues_ALL.xlsx`, in their order, so a person
can put AutoTester's sheet beside their own and read across. That is the whole
point of T-136: the comparison is only fair if the shapes match.

**Measured, not assumed** (`.work/track-a-corpus-facts.md`, 2026-09-08): the two
human sheets do NOT share a schema. `ERP_Issues_ALL.xlsx` has these 13 columns
exactly. `ERP_Issues_Trainers.xlsx` — the sheet T-136's acceptance actually
scores against — has 12, with no `Date` and `Clip` where ALL says `Recording`.
The scorer accommodates both; this exporter writes the 13-column form, because
that is the one a reader gets when they ask for "the issues".
"""

from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook

from autotester.core.excel import autosize_columns
from autotester.schema.analysis import AnalysedIssue, VideoAnalysis
from autotester.schema.enums import IssueOrigin
from autotester.schema.issue import Issue
from autotester.schema.project import Source

ISSUE_COLUMNS = [
    "ID", "Date", "Severity", "Type", "Title", "What is wrong", "How we know",
    "Confirm first", "Said verbatim", "Recording", "At", "Screenshot shows", "Evidence",
]
"""The human sheet's columns, in the human sheet's order. Changing one breaks
the side-by-side comparison T-136 exists to make."""

SEVERITY_WORDS = {"S1": "High", "S2": "Medium", "S3": "Low"}
"""Their vocabulary, not ours. A tester reading `S2` has to translate; a tester
reading `Medium` does not, and this sheet is for them."""


def at_mmss(seconds: float) -> str:
    """`93.4` -> `01:33`. The human sheet writes times this way, and its `At`
    column holds strings — so a scorer comparing a float to that cell silently
    matches nothing (measured on the real workbook)."""
    total = round(seconds)
    return f"{total // 60:02d}:{total % 60:02d}"


def _origin(issue: AnalysedIssue) -> IssueOrigin:
    """How we know — spoken, on-screen, or both.

    Derived from what the observation actually carried rather than taken from
    the model's own claim: a model asked "how do you know" answers plausibly
    every time, and the fields either hold a quote and on-screen text or they
    do not."""
    spoken = bool(issue.narration)
    on_screen = bool(issue.on_screen_text)
    if spoken and on_screen:
        return IssueOrigin.SPOKEN_AND_SCREEN
    if spoken:
        return IssueOrigin.SPOKEN
    if on_screen:
        return IssueOrigin.SCREEN
    return IssueOrigin.MODEL_DETECTED


def derive_issues(analysis: VideoAnalysis, source: Source, project: str) -> list[Issue]:
    """One `Issue` per adjudicated finding, provenance attached.

    `Issue.id` is content-addressed by the schema, so re-deriving the same
    analysis produces the same ids — which is what lets `add_issue` stay
    idempotent and a re-run not double the ledger."""
    return [
        Issue(
            project=project,
            source_id=source.id,
            recording_label=source.label or Path(source.path or "").name or source.id,
            recorded_on=source.recorded_on,
            at_s=issue.t_start,
            t_end_s=issue.t_end,
            screen=issue.screen,
            title=issue.title,
            what_is_wrong=issue.what_is_wrong,
            how_we_know=_origin(issue),
            models_agreeing=issue.models_agreeing,
            model_labels=list(issue.model_labels),
            said_verbatim=issue.narration,
            screenshot_shows=issue.on_screen_text,
            severity=issue.severity,
            category=issue.category,
            confidence=issue.confidence,
        )
        for issue in analysis.issues
    ]


def issue_row(issue: Issue) -> list[str]:
    """One sheet row, in `ISSUE_COLUMNS` order."""
    return [
        issue.human_id or issue.id,
        issue.recorded_on or "",
        SEVERITY_WORDS.get(issue.severity.value, issue.severity.value),
        issue.category.value,
        issue.title,
        issue.what_is_wrong,
        issue.how_we_know.value,
        issue.confirm_first or "",
        issue.said_verbatim or "",
        issue.recording_label,
        at_mmss(issue.at_s),
        issue.screenshot_shows or "",
        ", ".join(issue.evidence_refs),
    ]


def export_issues_excel(issues: list[Issue], out_path: Path) -> Path:
    """The issues as a workbook a tester can open beside their own."""
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "All issues"
    sheet.append(ISSUE_COLUMNS)
    for issue in sorted(issues, key=lambda i: (i.recording_label, i.at_s)):
        sheet.append(issue_row(issue))
    autosize_columns(sheet)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(out_path)
    return out_path
