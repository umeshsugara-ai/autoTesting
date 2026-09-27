"""What moved in the product since the last crawl: new / changed / missing / broken.

Contract: qa/contracts/crawl-traversal.md CR4, with CR5's honesty interaction.
A new module rather than more lines in `stages/portal_persona.py`, which the
contract names as already near its C2 cap.

`portal_persona.py::_merge` is PP2 **add-only**: new screens are appended and
nothing existing is ever dropped, blanked or rewritten. CR4 does not change
that — this module never mutates the persona. It computes a CLASSIFICATION
alongside the merge, which is recorded on the dated `PersonaRevision` (PP3).
The persona stays add-only; the revision history carries the diff.

**Scope (CR4's own wording).** This classifies the CRAWL-SOURCED screens only:
a stored screen with a `signature` came from a crawl, so a crawl can be
evidence about it. A stored screen with no signature came from a reviewed
FlowSpec or a taught flow; a crawl not reaching it is not evidence it is gone,
so it is left out of the diff entirely rather than reported as `missing`.

**The honesty rule (CR5).** `missing` is a claim that a screen the product used
to have is no longer reachable. A crawl that stopped on a bound never reached
the whole frontier, so it cannot make that claim about anything — those stored
keys go to `missing_unjudged`, which is a disclosed unknown, not a finding.
Reporting them as `missing` would turn "we ran out of budget" into "the product
lost a screen", which is the precise dishonesty this contract exists to stop.
"""

from __future__ import annotations

from autotester.schema.enums import NodeStatus
from autotester.schema.portal_persona import PortalPersona
from autotester.schema.screen_graph import ScreenNode
from autotester.stages.explore_incremental import node_key

BROKEN_STATUSES = frozenset({NodeStatus.ABORTED_ERROR, NodeStatus.ABORTED_DIALOG})
"""A visit that ended in an error or a dialog storm. `SKIPPED_UNCHANGED` is
deliberately absent: a skipped screen was not looked at, so it is evidence of
nothing (CR5)."""

CATEGORIES = ("new_screens", "changed_screens", "missing_screens",
              "broken_screens", "missing_unjudged")


def _previously_broken(existing: PortalPersona | None) -> frozenset[str]:
    """CR4: `broken` means an error status "that the prior stored screen did not
    carry". A `PersonaScreen` carries no status — PP2 forbids rewriting one — so
    the prior state is read from the append-only revision history instead: the
    most recent revision that classified anything. A screen still broken since
    last time is already recorded and is not re-reported as newly broken."""
    if existing is None:
        return frozenset()
    for revision in reversed(existing.history):
        if any(getattr(revision, name) for name in CATEGORIES):
            return frozenset(revision.broken_screens)
    return frozenset()


def classify(
    existing: PortalPersona | None,
    nodes: list[ScreenNode],
    *,
    frontier_exhausted: bool,
) -> dict[str, list[str]]:
    """The four CR4 categories plus CR5's disclosed unknown, keyed exactly as
    `PersonaRevision`'s own fields — so the schema defines the shape once (C3)
    and this returns values for it, never a parallel model of it.

    Every returned list is sorted, so two runs over the same evidence produce
    byte-identical output (CR6 determinism).
    """
    stored = {s.key(): s for s in existing.screens} if existing is not None else {}
    crawl_sourced = {key for key, s in stored.items() if s.signature is not None}
    reached = _reached(nodes)
    was_broken = _previously_broken(existing)

    new = sorted(key for key in reached if key not in stored)
    changed = sorted(
        key for key, node in reached.items()
        if key in crawl_sourced and stored[key].signature != node.signature
    )
    broken = sorted(
        key for key, node in reached.items()
        if key in stored and node.status in BROKEN_STATUSES and key not in was_broken
    )
    absent = sorted(crawl_sourced - set(reached))
    return {
        "new_screens": new, "changed_screens": changed,
        "missing_screens": absent if frontier_exhausted else [],
        "broken_screens": broken,
        "missing_unjudged": [] if frontier_exhausted else absent,
    }


def _reached(nodes: list[ScreenNode]) -> dict[str, ScreenNode]:
    """Key -> the node this crawl reached at it. A `QUEUED` node was enqueued and
    never visited, so it is not evidence about anything and is excluded; the
    first node wins so the mapping is stable."""
    reached: dict[str, ScreenNode] = {}
    for node in nodes:
        if node.status is NodeStatus.QUEUED:
            continue
        reached.setdefault(node_key(node), node)
    return reached


def describe(diff: dict[str, list[str]]) -> str | None:
    """A one-line prose fragment for the revision `summary`, or None when nothing
    moved. The COUNTS on the revision remain the machine-checkable record (CR4);
    this is only what a human reads first."""
    labels = (("new_screens", "new"), ("changed_screens", "changed"),
              ("missing_screens", "missing"), ("broken_screens", "broken"),
              ("missing_unjudged", "not judged (a bound truncated the frontier)"))
    parts = [f"{len(diff[field])} {label}" for field, label in labels if diff[field]]
    if not parts:
        return None
    return "screens " + ", ".join(parts)
