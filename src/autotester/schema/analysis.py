"""The adjudicated result of running an ensemble over one video's chunks.

`stages/adjudicate.py` is the only producer — a pure, deterministic function
over cached `ModelObservation`s (VL4). Nothing here calls a provider.
"""

from __future__ import annotations

from pydantic import ConfigDict, Field

from autotester.schema.base import Artifact
from autotester.schema.observation import ObservedFlow, ObservedIssue, ObservedScreen


class AnalysedScreen(ObservedScreen):
    """An `ObservedScreen` two or more models agreed on (or the one model that
    saw it, when only one did)."""

    model_config = ConfigDict(extra="forbid")

    models_agreeing: int = 1
    model_labels: list[str] = Field(default_factory=list)


class AnalysedIssue(ObservedIssue):
    """An `ObservedIssue` after cross-model merge — `id` is stamped by
    `stages/issues.py::derive_issues`, not here (this model stays pure)."""

    model_config = ConfigDict(extra="forbid")

    models_agreeing: int = 1
    model_labels: list[str] = Field(default_factory=list)


class JourneyStop(ObservedScreen):
    """One stop in a recording's end-to-end journey — reuses `ObservedScreen`'s
    shape (name/t_start/purpose/...) rather than duplicating it (C3)."""

    model_config = ConfigDict(extra="forbid")

    what_user_does: str = ""


class VideoAnalysis(Artifact):
    """One source's adjudicated understanding — screens, flows, the ordered
    journey, and issues — after `stages/adjudicate.py` has merged every
    model's chunked observations."""

    source_id: str
    observations_used: int = 0
    """How many model answers this reading was actually built from."""
    observations_expected: int = 0
    """How many there would have been if every planned call had succeeded.

    Two numbers rather than a flag, because "we watched it and found nothing"
    and "23 of 24 calls failed" produce the same screens and the same issues —
    and a reader who cannot tell them apart will trust the second one."""
    provider_labels: list[str] = Field(default_factory=list)
    prompt_names: list[str] = Field(default_factory=list)
    screens: list[AnalysedScreen] = Field(default_factory=list)
    flows: list[ObservedFlow] = Field(default_factory=list)
    journey: list[JourneyStop] = Field(default_factory=list)
    issues: list[AnalysedIssue] = Field(default_factory=list)
    summary: str = ""
    open_questions: list[str] = Field(default_factory=list)

    @property
    def is_complete(self) -> bool:
        """Every planned model call landed. A partial reading is still worth
        having; it is worth knowing that it is partial."""
        return (self.observations_expected > 0
                and self.observations_used >= self.observations_expected)
