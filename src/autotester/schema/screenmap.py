"""The product map — every screen the system has learned across all a
project's recordings, folded together by `stages/product_map.py`.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from autotester.schema.analysis import JourneyStop
from autotester.schema.base import Artifact


class ScreenVisit(BaseModel):
    """One recording that showed this screen."""

    model_config = ConfigDict(extra="forbid")

    source_id: str
    t_start: float
    t_end: float | None = None


class MappedScreen(BaseModel):
    """One screen folded across every recording that showed it."""

    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    purpose: str | None = None
    url_pattern: str | None = None
    fields: list[str] = Field(default_factory=list)
    ui_elements: list[str] = Field(default_factory=list)
    frame_ref: str | None = Field(
        default=None, description="project-relative PNG path, when extracted"
    )
    visits: list[ScreenVisit] = Field(default_factory=list)
    models_agreeing: int = 1


class Journey(BaseModel):
    """One recording's ordered path through screens."""

    model_config = ConfigDict(extra="forbid")

    source_id: str
    label: str
    stops: list[JourneyStop] = Field(default_factory=list)


class ScreenMap(Artifact):
    """The product map: every learned screen plus the journeys that visited them."""

    project: str
    screens: list[MappedScreen] = Field(default_factory=list)
    journeys: list[Journey] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)
