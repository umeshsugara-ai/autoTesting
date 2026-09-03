"""The feature ledger row and the relitigation verdict. Contract: qa/contracts/living-ledger.md."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field, model_validator

from autotester.schema.base import Artifact
from autotester.schema.enums import FeatureEventKind, UserValue

AUTO_REASON = "update"


class FeatureEvent(Artifact):
    """One dated event in the life of a feature: planned, live, updated, or retired.

    Every change gets a row (S2). The *reasoning* is human-typed only when the
    feature's `user_value` is high; otherwise it is the auto-stamp `update`.
    A retirement always carries a real reason — that is the whole point of
    the ledger (relitigation reads it back).
    """

    id: str = Field(pattern=r"^F-\d{3,}$")
    feature: str = Field(pattern=r"^[a-z0-9][a-z0-9-]*$", description="stable feature slug")
    title: str = Field(min_length=3)
    event: FeatureEventKind
    date: date
    unit: str | None = Field(default=None, description="goal task id, e.g. T-011")
    verdict_ref: str | None = Field(default=None, description="qa/verdicts/<slug>.md")
    reason: str = Field(min_length=1)
    user_value: UserValue = UserValue.NORMAL
    description: str = Field(min_length=1, description="what the feature does for the user")
    supersedes: str | None = Field(default=None, pattern=r"^F-\d{3,}$")

    @model_validator(mode="after")
    def _retirement_needs_a_real_reason(self) -> FeatureEvent:
        if self.event is FeatureEventKind.RETIRED and self.reason.strip().lower() == AUTO_REASON:
            raise ValueError("a retired feature needs a real reason, not the auto-stamp 'update'")
        return self

    @property
    def ask_required(self) -> bool:
        """True when a human should confirm or write the reason (high value, auto reason)."""
        return self.user_value is UserValue.HIGH and self.reason.strip().lower() == AUTO_REASON


class RelitigationVerdict(BaseModel):
    """The judge's answer to "is this new unit a retired feature coming back?"."""

    model_config = ConfigDict(extra="forbid")

    same_behaviour: bool
    matched_feature_id: str | None = Field(default=None, pattern=r"^F-\d{3,}$")
    justification: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    decided_by: str = Field(default="llm", description="'rule' when certain, else 'llm'")

    @property
    def gate(self) -> bool:
        return self.same_behaviour
