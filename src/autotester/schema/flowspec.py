"""The FlowSpec — the system's understanding of the product under test.

Produced by INGEST from videos/docs/text, reviewed and editable by a human, and
consumed by EXPAND. Every step carries provenance back to its source timestamp
so a human can watch the exact second the system learned a step from.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from autotester.core.ids import content_id
from autotester.schema.base import Artifact
from autotester.schema.enums import Action, ReviewStatus


class SourceRef(BaseModel):
    """Where a piece of understanding came from — a video second, a doc line."""

    model_config = ConfigDict(extra="forbid")

    source_id: str
    t_start: float | None = Field(default=None, description="seconds into a video")
    t_end: float | None = None
    locator: str | None = Field(default=None, description="page/section for a doc")


class FieldConstraints(BaseModel):
    """What the UI says a field accepts. Drives boundary/edge case generation."""

    model_config = ConfigDict(extra="forbid")

    min: float | None = None
    max: float | None = None
    min_length: int | None = None
    max_length: int | None = None
    pattern: str | None = None
    enum: list[str] | None = None


class InputField(BaseModel):
    """One input on a screen."""

    model_config = ConfigDict(extra="forbid")

    name: str
    label: str | None = None
    type: str = Field(default="text", description="text, email, password, select, file…")
    required: bool = False
    secret_key: str | None = Field(default=None, description="SecretRef key if sensitive")
    constraints: FieldConstraints = Field(default_factory=FieldConstraints)


class ExpectedState(BaseModel):
    """What must be true for a step to have succeeded.

    `visual_signal` exists because the DOM does not always say it — the brain's
    canonical example is "the thumbs-up turns yellow when a post is liked".
    """

    model_config = ConfigDict(extra="forbid")

    url: str | None = Field(default=None, description="exact URL or glob pattern")
    visible_text: list[str] = Field(default_factory=list)
    absent_text: list[str] = Field(default_factory=list)
    dom_asserts: list[str] = Field(default_factory=list, description="selectors that must exist")
    visual_signal: str | None = None
    network: list[str] = Field(default_factory=list, description="expected request patterns")


class Step(BaseModel):
    """One browser action plus what it should produce."""

    model_config = ConfigDict(extra="forbid")

    order: int
    action: Action
    target: str = Field(description="semantic locator: role/name/label, not a brittle CSS path")
    value: str | None = Field(default=None, description="literal, or {{SECRET:KEY}} placeholder")
    expected: ExpectedState = Field(default_factory=ExpectedState)
    source_ref: SourceRef | None = None
    note: str | None = None


class Screen(BaseModel):
    """A distinguishable page/state of the product."""

    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    url_pattern: str | None = None
    signals: list[str] = Field(default_factory=list, description="cues that identify this screen")
    fields: list[InputField] = Field(default_factory=list)
    screenshot_ref: str | None = None


class Flow(BaseModel):
    """An end-to-end journey through screens."""

    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    entry_screen: str
    exit_screen: str | None = None
    preconditions: list[str] = Field(default_factory=list)
    steps: list[Step] = Field(default_factory=list)
    requires_auth: bool = False


class Review(BaseModel):
    """The human gate. A flowspec drives nothing until a person approves it."""

    model_config = ConfigDict(extra="forbid")

    status: ReviewStatus = ReviewStatus.DRAFT
    by: str | None = None
    at: str | None = None
    note: str | None = None


class Conflict(BaseModel):
    """Sources disagreed. Flagged for a human — never silently merged."""

    model_config = ConfigDict(extra="forbid")

    subject: str
    claims: list[str]
    source_refs: list[SourceRef] = Field(default_factory=list)


class FlowSpec(Artifact):
    """The reviewed understanding of one project's UI."""

    project: str
    version: int = 1
    screens: list[Screen] = Field(default_factory=list)
    flows: list[Flow] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)
    conflicts: list[Conflict] = Field(default_factory=list)
    review: Review = Field(default_factory=Review)

    @property
    def fingerprint(self) -> str:
        """Content id of the semantic payload — changes only when meaning changes."""
        payload = {
            "screens": [s.model_dump(mode="json") for s in self.screens],
            "flows": [f.model_dump(mode="json") for f in self.flows],
        }
        return content_id("fs", payload)

    def flow(self, flow_id: str) -> Flow | None:
        return next((f for f in self.flows if f.id == flow_id), None)

    def screen(self, screen_id: str) -> Screen | None:
        return next((s for s in self.screens if s.id == screen_id), None)


class ObservedStep(BaseModel):
    """One action a vision model saw in a video. Raw material for a `Step` —
    `stages/ingest.py` turns `t_start`/`t_end` into a `SourceRef`."""

    model_config = ConfigDict(extra="forbid")

    order: int
    action: Action
    target: str = Field(description="what was clicked/filled, in plain terms — a role/name/"
                        "label a human would use, never a CSS selector")
    value: str | None = None
    t_start: float = Field(description="seconds into the video when this action starts")
    t_end: float | None = None


class ObservedFlow(BaseModel):
    """One journey a vision model saw across screens."""

    model_config = ConfigDict(extra="forbid")

    name: str
    entry_screen: str = Field(description="the name of the screen this flow starts on")
    steps: list[ObservedStep] = Field(default_factory=list)


class ObservedScreen(BaseModel):
    """One distinguishable screen a vision model saw."""

    model_config = ConfigDict(extra="forbid")

    name: str
    t_start: float = Field(description="seconds into the video when this screen first appears")
    signals: list[str] = Field(default_factory=list, description="visible cues that identify it")


class VideoObservation(BaseModel):
    """A vision provider's raw reading of one video — `stages/ingest.py`'s input,
    turned into a `FlowSpec` (ids minted, provenance attached)."""

    model_config = ConfigDict(extra="forbid")

    screens: list[ObservedScreen] = Field(default_factory=list)
    flows: list[ObservedFlow] = Field(default_factory=list)
