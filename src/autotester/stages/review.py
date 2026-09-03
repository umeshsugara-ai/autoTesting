"""FlowSpec review gate: nothing generates cases from an unreviewed understanding
of the product. Contract: qa/contracts/review-gate.md R1-R3.

A `FlowSpec` starts `DRAFT` (ingest.py never sets any other status). A human
approves it — via this module's `approve`, called by the CLI or a future UI —
before `stages/expand.py` (T-070) may consume it; `require_reviewed` is the
one guard every such stage calls first.
"""

from __future__ import annotations

from datetime import UTC, datetime

from autotester.schema.enums import ReviewStatus
from autotester.schema.flowspec import FlowSpec, Review


class FlowSpecNotReviewed(RuntimeError):
    """Raised when a stage tries to consume a `FlowSpec` that isn't approved."""


def _now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def approve(spec: FlowSpec, by: str, note: str | None = None) -> FlowSpec:
    """A human approved this understanding of the product as-is."""
    if not by:
        raise ValueError("approve() needs who approved it")
    review = Review(status=ReviewStatus.APPROVED, by=by, at=_now_iso(), note=note)
    return spec.model_copy(update={"review": review})


def request_edit(spec: FlowSpec, by: str, note: str) -> FlowSpec:
    """A human found something wrong — back to draft with the reason recorded,
    so the next ingest/edit pass has a concrete note to work from."""
    if not by or not note:
        raise ValueError("request_edit() needs who found the problem and what it is")
    review = Review(status=ReviewStatus.NEEDS_EDIT, by=by, at=_now_iso(), note=note)
    return spec.model_copy(update={"review": review})


def require_reviewed(spec: FlowSpec) -> None:
    """Raise `FlowSpecNotReviewed` unless `spec.review.status` is `APPROVED`.
    `stages/expand.py` (T-070) calls this first, before generating any case."""
    if spec.review.status is not ReviewStatus.APPROVED:
        raise FlowSpecNotReviewed(
            f"FlowSpec for '{spec.project}' is {spec.review.status.value}, not approved — "
            "run `autotester flowspec approve <project> --by <name>` before expanding cases"
        )
