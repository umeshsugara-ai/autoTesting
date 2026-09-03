"""Base model every artifact inherits. Defines the shared envelope.

Three fields ride on every artifact so a human (or an auditor) can always answer
"what shape is this, when was it made, and where did it come from".
"""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field

SCHEMA_VERSION = 1


def utc_now() -> datetime:
    return datetime.now(UTC)


class Provenance(BaseModel):
    """Who or what produced this artifact, and from what."""

    model_config = ConfigDict(extra="forbid")

    produced_by: str = Field(description="stage name, 'human', or provider id")
    inputs: list[str] = Field(default_factory=list, description="ids of inputs consumed")
    note: str | None = None


class Artifact(BaseModel):
    """Common envelope: versioned, timestamped, attributable.

    `extra="forbid"` is deliberate — a typo'd key fails loudly at load time
    instead of silently vanishing, which is how schemas rot.
    """

    model_config = ConfigDict(extra="forbid", use_enum_values=False)

    schema_version: int = SCHEMA_VERSION
    created_at: datetime = Field(default_factory=utc_now)
    provenance: Provenance | None = None
