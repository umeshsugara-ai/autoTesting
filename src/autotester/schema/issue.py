"""A video-derived issue — its own artifact, deliberately NOT a `CaseClass`.

D-005 rejected opening `CaseClass` ("the completeness guarantee is the
product"); D-014 confirms that decision stands. `Issue` fields mirror the
human `ERP_Issues_*.xlsx` 13-column format so `stages/issues.py::export_issues_excel`
is a straight field-to-column mapping (VL6).
"""

from __future__ import annotations

from pydantic import Field

from autotester.core.ids import content_id
from autotester.schema.base import Artifact
from autotester.schema.enums import Confidence, IssueCategory, IssueOrigin, IssueStatus, Severity


class Issue(Artifact):
    """One row of "what's wrong", derived from a video and (optionally) matched
    to a human-logged issue for scoring (T-136)."""

    id: str = ""
    project: str
    source_id: str
    recording_label: str
    recorded_on: str | None = None
    at_s: float
    t_end_s: float | None = None
    screen: str
    title: str
    what_is_wrong: str
    how_we_know: IssueOrigin = IssueOrigin.MODEL_DETECTED
    models_agreeing: int = 1
    model_labels: list[str] = Field(default_factory=list)
    confirm_first: str | None = None
    said_verbatim: str | None = None
    screenshot_shows: str | None = None
    evidence_refs: list[str] = Field(default_factory=list)
    severity: Severity = Severity.S2
    category: IssueCategory = IssueCategory.OTHER
    confidence: Confidence = Confidence.MEDIUM
    status: IssueStatus = IssueStatus.OPEN
    human_id: str | None = Field(
        default=None, description="matching row id in a human sheet, if scored"
    )

    def model_post_init(self, _context: object) -> None:
        if not self.id:
            bucket = round(self.at_s / 5)
            normalised_title = " ".join(self.title.strip().lower().split())
            payload = {
                "project": self.project,
                "source_id": self.source_id,
                "screen": self.screen.strip().casefold(),
                "category": str(self.category),
                "bucket": bucket,
                "title": normalised_title,
            }
            object.__setattr__(self, "id", content_id("iss", payload))
