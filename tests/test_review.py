"""FlowSpec review gate. Contract: qa/contracts/review-gate.md R1-R3."""

from __future__ import annotations

import pytest

from autotester.schema.enums import ReviewStatus
from autotester.schema.flowspec import FlowSpec
from autotester.stages.review import FlowSpecNotReviewed, approve, request_edit, require_reviewed


def make_spec() -> FlowSpec:
    return FlowSpec(project="pathlynks")


# -- R1 starts DRAFT, require_reviewed blocks it -----------------------------

def test_fresh_flowspec_is_draft_and_blocked() -> None:
    spec = make_spec()
    assert spec.review.status is ReviewStatus.DRAFT
    with pytest.raises(FlowSpecNotReviewed, match="draft"):
        require_reviewed(spec)


# -- R2 approve unblocks it, records who and when -----------------------------

def test_approve_unblocks_and_records_who() -> None:
    spec = make_spec()
    approved = approve(spec, by="umesh", note="looks right")

    assert approved.review.status is ReviewStatus.APPROVED
    assert approved.review.by == "umesh"
    assert approved.review.at is not None
    assert approved.review.note == "looks right"
    require_reviewed(approved)  # does not raise


def test_approve_requires_a_who() -> None:
    with pytest.raises(ValueError, match="who"):
        approve(make_spec(), by="")


def test_approve_does_not_mutate_the_original() -> None:
    spec = make_spec()
    approve(spec, by="umesh")
    assert spec.review.status is ReviewStatus.DRAFT  # unchanged


# -- R3 request_edit sends it back with a reason ------------------------------

def test_request_edit_sends_back_to_needs_edit_with_a_note() -> None:
    spec = approve(make_spec(), by="umesh")
    edited = request_edit(spec, by="umesh", note="flow 3 is missing a step")

    assert edited.review.status is ReviewStatus.NEEDS_EDIT
    assert edited.review.note == "flow 3 is missing a step"
    with pytest.raises(FlowSpecNotReviewed, match="needs_edit"):
        require_reviewed(edited)


def test_request_edit_requires_a_note() -> None:
    with pytest.raises(ValueError, match="what"):
        request_edit(make_spec(), by="umesh", note="")
