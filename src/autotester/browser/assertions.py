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
    """Whether the expectation holds right now (one probe, no waiting).

    AT-551: a page that cannot be read is not a page whose text can be
    confirmed present OR absent -- `body_text` returning None (not "") on a
    read failure makes visible_text/absent_text fail SAFE (unmet) here
    instead of falling through to the blanket `return True` below."""
    with contextlib.suppress(Exception):
        if expected.url and expected.url not in session.page.url:
            return False
        if expected.visible_text or expected.absent_text:
            body = body_text(session)
            if body is None:
                return False
            if expected.visible_text and any(text not in body for text in expected.visible_text):
                return False
            if expected.absent_text and any(text in body for text in expected.absent_text):
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
            EvidenceKind.DOM, f"assert url: {_url_label(session, expected.url)} "
            f"(expected to contain {expected.url!r})", step_order=step_order))
    if expected.visible_text or expected.absent_text:
        body = body_text(session)
    if expected.visible_text:
        for text in expected.visible_text:
            evidence.append(session._record(
                EvidenceKind.DOM, f"assert visible_text: "
                f"{_text_label(body, text, want_present=True)} "
                f"(expected to contain {text!r})", step_order=step_order))
    if expected.absent_text:
        for text in expected.absent_text:
            evidence.append(session._record(
                EvidenceKind.DOM, f"assert absent_text: "
                f"{_text_label(body, text, want_present=False)} "
                f"(expected absent: {text!r})", step_order=step_order))
    for selector in expected.dom_asserts:
        found = selector_exists(session, selector)
        evidence.append(session._record(
            EvidenceKind.DOM, f"assert dom_asserts: {'met' if found else 'unmet'} "
            f"(selector {selector!r} {'exists' if found else 'not found'})",
            step_order=step_order))
    return evidence


def _url_label(session, url: str) -> str:
    """AT-552: `assert_expected`'s docstring promises 'raises nothing' -- the
    url read is its own probe (not `met()`'s, which already suppresses),
    wrapped so an unreadable `page.url` records unmet instead of surfacing
    as an uncaught ERRORED."""
    try:
        current = session.page.url or ""
    except Exception:
        return "unmet (url unreadable)"
    return "met" if url in current else "unmet"


def _text_label(body: str | None, text: str, *, want_present: bool) -> str:
    """AT-551: `body` is None when the page could not be read at all -- that
    is neither met nor unmet by chance, it is unmet (we cannot confirm
    presence OR absence on a page we can't see)."""
    if body is None:
        return "unmet (page unreadable)"
    return "met" if (text in body) == want_present else "unmet"


def body_text(session) -> str | None:
    """The page's visible text, or None if it could not be read at all --
    distinct from a genuinely empty body (AT-551: collapsing both to ""
    made an absent_text expectation read as met on a page the executor
    couldn't even see)."""
    try:
        return session.page.locator("body").inner_text() or ""
    except Exception:
        return None


def selector_exists(session, selector: str) -> bool:
    with contextlib.suppress(Exception):
        return session.page.locator(selector).count() > 0
    return False