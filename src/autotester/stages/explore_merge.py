"""Fold a crawl's screen graph into the reviewed FlowSpec (Track B5).

The crawl discovers screens the FlowSpec has never heard of. This stage is the
one place those become `Screen` rows a human can review — and it is deliberately
conservative: an existing screen is never rewritten, a disagreement becomes a
`Conflict` with both claims kept, and any real change sends the spec back to
DRAFT so the human gate is re-armed rather than bypassed.

Contract: qa/contracts/explore.md X12 amendment + qa/contracts/coverage.md V1.
"""

from __future__ import annotations

from autotester.core.urls import url_template
from autotester.schema.enums import ReviewStatus
from autotester.schema.flowspec import Conflict, FlowSpec, InputField, Review, Screen, SourceRef
from autotester.schema.screen_graph import ScreenNode

_FIELD_ROLES = {
    "textbox": "text", "searchbox": "text", "combobox": "select",
    "checkbox": "checkbox", "radio": "radio", "spinbutton": "number",
}
_MAX_SIGNALS = 8


def _signals(node: ScreenNode) -> list[str]:
    """The screen's identifying cues: its title plus the names of its stable
    (non-row) controls. Row content is excluded for the same reason it is
    excluded from the structural signature — it is data, not identity."""
    names = [el.name for el in node.elements if el.visible and el.name and not el.in_row]
    seen: list[str] = []
    for name in names:
        if name not in seen:
            seen.append(name)
    return ([node.title] if node.title else []) + seen[:_MAX_SIGNALS]


def _fields(node: ScreenNode) -> list[InputField]:
    """Inputs the crawl saw. `secret_key` is deliberately never inferred — a
    field is only a secret because a human declared a `SecretRef` for it."""
    fields: list[InputField] = []
    for el in node.elements:
        kind = _FIELD_ROLES.get(el.role)
        if kind is None or not el.visible:
            continue
        fields.append(InputField(name=el.name or el.selector, label=el.name or None, type=kind))
    return fields


def screen_from(node: ScreenNode) -> Screen:
    """One crawled node as a FlowSpec `Screen`, keeping the node's own id so a
    re-merge of the same crawl is a no-op rather than a duplicate.

    `url_pattern` is derived host-lessly from `url_example` rather than reused
    from `node.url_template`: the node template carries a host (it is a browsing
    identity), while a `Screen.url_pattern` is a path pattern — that is what
    `stages/coverage.py` and `stages/ingest.py` both compare against.
    """
    return Screen(
        id=node.id,
        name=node.name or node.title or node.url_template,
        url_pattern=url_template(node.url_example, keep_host=False),
        signals=_signals(node),
        fields=_fields(node),
        screenshot_ref=node.screenshot_ref,
        source_ref=SourceRef(source_id=node.crawl_id, locator=node.url_example),
    )


def _conflict_for(existing: Screen, incoming: Screen, crawl_id: str) -> Conflict:
    return Conflict(
        subject=incoming.url_pattern or incoming.id,
        claims=[
            f"existing screen '{existing.name}' ({existing.id})",
            f"crawled screen '{incoming.name}' ({incoming.id})",
        ],
        source_refs=[
            existing.source_ref or SourceRef(source_id="unknown"),
            SourceRef(source_id=crawl_id, locator=incoming.url_pattern),
        ],
    )


def merge_screens(
    spec: FlowSpec | None, nodes: list[ScreenNode], project: str, *, crawl_id: str
) -> FlowSpec:
    """Add every crawled screen the spec does not already have.

    Never rewrites an existing screen. When a crawled screen claims a
    `url_pattern` an existing screen already claims under a different name, both
    are kept and a `Conflict` records the disagreement for the human — silently
    picking a winner is how a product map stops matching the product.

    Idempotent: merging the same crawl twice changes nothing, so the version is
    not bumped and the review is not reset a second time.
    """
    spec = spec or FlowSpec(project=project)
    known_ids = {s.id for s in spec.screens}
    by_pattern = {s.url_pattern: s for s in spec.screens if s.url_pattern}

    added: list[Screen] = []
    conflicts: list[Conflict] = []
    for node in nodes:
        incoming = screen_from(node)
        if incoming.id in known_ids:
            continue
        clash = by_pattern.get(incoming.url_pattern)
        if clash is not None and clash.name != incoming.name:
            conflicts.append(_conflict_for(clash, incoming, crawl_id))
        added.append(incoming)
        known_ids.add(incoming.id)

    if not added:
        return spec

    known_conflicts = {(c.subject, tuple(c.claims)) for c in spec.conflicts}
    new_conflicts = [c for c in conflicts if (c.subject, tuple(c.claims)) not in known_conflicts]
    return spec.model_copy(update={
        "screens": [*spec.screens, *added],
        "conflicts": [*spec.conflicts, *new_conflicts],
        "source_ids": sorted({*spec.source_ids, crawl_id}),
        "version": spec.version + 1,
        "review": Review(
            status=ReviewStatus.DRAFT,
            note=f"{len(added)} screen(s) added by crawl {crawl_id} — needs review",
        ),
    })
