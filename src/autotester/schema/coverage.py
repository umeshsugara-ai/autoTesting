"""Coverage gaps and the video requests that close them.

The self-extending half of the product: when a run meets a screen or route the
FlowSpec does not describe, the system asks the human for material instead of
guessing at it.
"""

from __future__ import annotations

from pydantic import Field

from autotester.core.ids import content_id
from autotester.schema.base import Artifact
from autotester.schema.enums import RequestStatus


class CoverageGap(Artifact):
    """A screen or route observed in a run but absent from the FlowSpec."""

    id: str = ""
    project: str
    kind: str = Field(default="route", description="route | screen | field | class")
    subject: str = Field(description="the URL, screen id, or taxonomy class not covered")
    seen_in_run: str | None = None
    reason: str = ""

    def model_post_init(self, _context: object) -> None:
        if not self.id:
            object.__setattr__(
                self,
                "id",
                content_id("gap", {"p": self.project, "k": self.kind, "s": self.subject}),
            )


class VideoRequest(Artifact):
    """What the system asks a human to record, and why."""

    id: str = ""
    project: str
    gap_id: str
    prompt: str = Field(description="human-readable ask, e.g. 'record creating a new report'")
    status: RequestStatus = RequestStatus.OPEN
    fulfilled_by_source: str | None = None

    def model_post_init(self, _context: object) -> None:
        if not self.id:
            object.__setattr__(self, "id", content_id("req", {"p": self.project, "g": self.gap_id}))
