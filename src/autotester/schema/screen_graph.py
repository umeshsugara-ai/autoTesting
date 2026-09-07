"""What one page-visit observed: its interactive elements and identity inputs.

`ElementRef`/`PageObservation` are B1's minimal slice — `stages/explore.py`
(Track B3) and `stages/screen_identity.py` (B2) extend this file with
`ScreenNode`/`ScreenEdge`/`CrawlFrontier` once the crawl stage itself exists.
`browser/observe.py` is the only producer.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ElementRef(BaseModel):
    """One interactive element found by `browser/enumerate.js`."""

    model_config = ConfigDict(extra="forbid")

    role: str
    name: str = ""
    selector: str
    enabled: bool = True
    visible: bool = True
    href: str | None = None
    is_form_submit: bool = False
    in_row: bool = Field(
        default=False,
        description="inside a table row / list item with siblings — excluded from a "
        "screen's structural signature so two list pages with different rows are one screen",
    )
    target_blank: bool = False
    tag: str = ""


class PageObservation(BaseModel):
    """One page-visit's raw material: its url/title and interactive elements."""

    model_config = ConfigDict(extra="forbid")

    url: str
    title: str = ""
    elements: list[ElementRef] = Field(default_factory=list)
