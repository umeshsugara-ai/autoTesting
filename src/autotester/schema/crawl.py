"""Crawl-safety primitives. B1's minimal slice — `stages/explore_safety.py`
(Track B4) and `stages/explore.py` (B3) extend this file with `CrawlBounds`,
`SafetyPolicy`, `CrawlIssue`, `Crawl` once those stages exist.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class DialogEvent(BaseModel):
    """One JS dialog (`alert`/`confirm`/`prompt`/`beforeunload`) the observer saw."""

    model_config = ConfigDict(extra="forbid")

    dialog_type: str
    message: str = ""
    accepted: bool = False
