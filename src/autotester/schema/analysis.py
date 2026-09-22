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
    requested_providers: list[str] = Field(default_factory=list)
    """AT-550: the provider labels the CALLER asked for, before credential
    availability was checked — always known, even for a provider that never
    produced a single observation. `providers.get(n) for n in vision_ensemble()`
    used to be filtered down to `available()` providers before `analyze` ever
    ran, so a 2-provider config with one missing credential silently became an
    ensemble of one, and nothing on disk recorded that it had shrunk. Empty
    means the caller did not say (older analyses, or a caller that ran exactly
    what it was given); non-empty and equal to `provider_labels` means the full
    requested ensemble answered. See `degraded_providers` below."""
    vision_config_defaulted: bool = False
    """AT-550: True when the project's `vision` config was empty and the
    caller substituted `ProviderConfig.DEFAULT_VISION_PROVIDER`
    (`schema/project.py`) instead of what an operator explicitly chose —
    set from `ProviderConfig.vision_ensemble_defaulted()`. False both for an
    explicit single-provider config and for a caller that predates this
    field; the point is that a defaulted run must never look identical to an
    explicit one on the persisted artifact."""
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

    @property
    def degraded_providers(self) -> list[str]:
        """AT-550: providers that were REQUESTED but produced zero observations
        — a credential gap or a total per-provider failure, distinct from
        `is_complete`'s per-chunk partial completion. Empty when the caller did
        not record `requested_providers`, OR when every requested provider
        answered — the two honest cases are not distinguishable from this
        property alone, which is why `requested_providers` itself is also on
        the artifact rather than only this derived list."""
        return sorted(set(self.requested_providers) - set(self.provider_labels))
