"""Deterministic assertion evaluation (D-032/AT-540) — split from
`browser/session.py` for the 300-line cap (the module was at 298/300 when the
assertion layer arrived).

One job: evaluate a declared `ExpectedState` against the live page and record
each field's result as DOM evidence. Deterministic fields only — `url`
(substring), `visible_text` (present), `absent_text` (truly absent),
`dom_asserts` (selectors exist). `network` is observer-derived and
`visual_signal` is the judge's (execute.md E1's no-fire line, unchanged).

C7 holds by construction: these functions RECORD facts, they never assign
PASS/FAIL — the grader still owns the verdict.
"""

from __future__ import annotations

import contextlib

from autotester.schema.enums import EvidenceKind
from autotester.schema.flowspec import ExpectedState

POLL_MS = 250
def met(session, expected: ExpectedState) -> bool:
    """Whether the expectation holds right now (one probe, no waiting)."""
    with contextlib.suppress(Exception):
        if expected.url and expected.url not in session.page.url:
            return False
        if expected.visible_text:
            body = body_text(session)
            if any(text not in body for text in expected.visible_text):
                return False
        if expected.absent_text:
            body = body_text(session)
            if any(text in body for text in expected.absent_text):
                return False
        for selector in expected.dom_asserts:
            if not selector_exists(session, selector):
                return False
    return True


def assert_expected(session, expected: ExpectedState, *,
                    timeout_ms: int = 8000, step_order: int | None = None) -> list:
    """Poll until the expectation holds (or the ceiling expires), then record
    one DOM evidence item per evaluated field with an explicit
    `assert <field>: met|unmet (<detail>)` label. Raises nothing: the caller
    (execute.py) reads the recorded results and decides the observation-level
    consequence."""
    elapsed = 0
    while elapsed < timeout_ms and not met(session, expected):
        with contextlib.suppress(Exception):
            session.page.wait_for_timeout(POLL_MS)
        elapsed += POLL_MS

    evidence: list = []
    if expected.url:
        evidence.append(session._record(
            EvidenceKind.DOM, f"assert url: "
            f"{'met' if expected.url in (session.page.url or '') else 'unmet'} "
            f"(expected to contain {expected.url!r})", step_order=step_order))
    if expected.visible_text:
        body = body_text(session)
        for text in expected.visible_text:
            evidence.append(session._record(
                EvidenceKind.DOM, f"assert visible_text: "
                f"{'met' if text in body else 'unmet'} (expected to contain {text!r})",
                step_order=step_order))
    if expected.absent_text:
        body = body_text(session)
        for text in expected.absent_text:
            evidence.append(session._record(
                EvidenceKind.DOM, f"assert absent_text: "
                f"{'met' if text not in body else 'unmet'} "
                f"(expected absent: {text!r})", step_order=step_order))
    for selector in expected.dom_asserts:
        found = selector_exists(session, selector)
        evidence.append(session._record(
            EvidenceKind.DOM, f"assert dom_asserts: {'met' if found else 'unmet'} "
            f"(selector {selector!r} {'exists' if found else 'not found'})",
            step_order=step_order))
    return evidence


def body_text(session) -> str:
    with contextlib.suppress(Exception):
        return session.page.locator("body").inner_text() or ""
    return ""


def selector_exists(session, selector: str) -> bool:
    with contextlib.suppress(Exception):
        return session.page.locator(selector).count() > 0
    return False