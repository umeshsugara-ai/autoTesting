"""Screen identity: turn one `PageObservation` into a `ScreenNode`.

Contract: qa/contracts/explore.md X3 (once that contract exists, T-143).
Deliberately structural — never URL-only (the prior attempt made every SPA
state invisible) and never an LLM's free-text description (its stop
condition then never fired, because the text kept changing). Pure; no
browser, no provider.
"""

from __future__ import annotations

import re

from autotester.core.ids import content_hash
from autotester.core.urls import url_template
from autotester.schema.screen_graph import ElementRef, PageObservation, ScreenNode

_WHITESPACE = re.compile(r"\s+")
_DIGITS = re.compile(r"\d+")
_PUNCTUATION = re.compile(r"[^\w\s]")


def _normalise_name(name: str) -> str:
    """Casefold, collapse whitespace, strip punctuation, map digit runs to
    `#` — so "Edit row 42" and "Edit row 17" contribute the same signature
    token (row data doesn't change a screen's identity)."""
    text = name.strip().casefold()
    text = _PUNCTUATION.sub("", text)
    text = _DIGITS.sub("#", text)
    text = _WHITESPACE.sub(" ", text).strip()
    return text[:40]


def structural_signature(elements: list[ElementRef]) -> str:
    """Content hash of the sorted, deduplicated `(role, normalised-name)` set
    of VISIBLE, non-row elements. Row/list-item elements are excluded so two
    list pages differing only in row data collapse to one signature."""
    keys = {
        f"{el.role}|{_normalise_name(el.name)}"
        for el in elements
        if el.visible and not el.in_row
    }
    return content_hash(sorted(keys))


def node_from(
    observation: PageObservation, crawl_id: str, project: str, depth: int,
    *, discovered_by: str | None = None,
) -> ScreenNode:
    """Build a `ScreenNode` whose id is a pure function of
    `(url_template, structural_signature)` — the same inputs always produce
    the same node, regardless of when or how it was visited."""
    template = url_template(observation.url, keep_host=False)
    signature = structural_signature(observation.elements)
    return ScreenNode(
        crawl_id=crawl_id, project=project, url_template=template,
        url_example=observation.url, signature=signature, title=observation.title,
        name=observation.title or template, depth=depth,
        elements=observation.elements, discovered_by=discovered_by,
    )
