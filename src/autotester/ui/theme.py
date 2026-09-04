"""Shared visual system for every UI route. Contract: qa/contracts/docker.md D5.

One place for styling (anti-drift C3) — every route in `ui/app.py` calls
`page()`/`card()`/`stat()`/`empty_state()` to build its HTML; no route writes
its own `<style>` block or reinvents a layout primitive.

Design identity: a "technical instrument," not a generic SaaS dashboard —
Fraunces (a characterful serif with real optical weight) for headings and the
wordmark, IBM Plex Sans for body copy, IBM Plex Mono for anything that reads
like data (ids, run numbers, badges) — this is a tool that drives a real
browser and reports real evidence, and the type should feel like an
instrument panel, not a marketing page. One committed accent (signal amber,
`--accent`) carries every primary action and the brand mark; PASS/FAIL/etc.
keep their own semantic colors so a result badge is never confused with a
button.
"""

from __future__ import annotations

from autotester.ui.theme_style import PAGE_STYLE

NAV = """
<header class="topbar">
  <a class="brand" href="/">
    <span class="brand-mark">AT</span>
    <span class="brand-name">AutoTester</span>
  </a>
  <nav>
    <a href="/">Projects</a>
    <a href="/onboard">+ New project</a>
    <a href="/live" class="nav-live">● Live view</a>
    <a href="/settings/providers">⚙ Settings</a>
  </nav>
</header>
"""

_BADGE_CLASS = {
    "PASS": ("badge-pass", "✓"), "FAIL": ("badge-fail", "✕"),
    "BLOCKED": ("badge-blocked", "⏸"), "INCONCLUSIVE": ("badge-inconclusive", "?"),
}


def badge(value: str, count: int | None = None) -> str:
    """A colored `<span>` for a test RESULT value (PASS/FAIL/BLOCKED/INCONCLUSIVE)
    already HTML-escaped by the caller. Never reuse this for a non-test-result
    status (credential presence, review state) — that's what `pill()` is for;
    the two vocabularies read as the same thing to a user otherwise. Pass
    `count` to render a compact "N RESULT" summary badge (e.g. a run-history
    row) instead of a single case's own result — same color/icon lookup."""
    cls, icon = _BADGE_CLASS.get(value, ("badge-inconclusive", ""))
    label = f"{count} {value}" if count is not None else value
    return f"<span class='badge {cls}'>{icon} {label}</span>"


_PILL_CLASS = {
    "positive": "badge-pass", "warning": "badge-blocked", "neutral": "badge-inconclusive",
    "danger": "badge-fail",
}


def pill(text: str, tone: str = "neutral") -> str:
    """A colored status label for anything that ISN'T a test result — credential
    presence, review state, connection state. `text` must already be escaped."""
    cls = _PILL_CLASS.get(tone, "badge-inconclusive")
    return f"<span class='badge {cls}'>{text}</span>"


def stat(value: str, label: str) -> str:
    """One metric tile — a big number/value with a small label under it."""
    return (
        f"<div class='stat'><div class='value'>{value}</div>"
        f"<div class='label'>{label}</div></div>"
    )


def card(body: str, title: str | None = None) -> str:
    heading = f"<h2>{title}</h2>" if title else ""
    return f"<div class='card'>{heading}{body}</div>"


def empty_state(icon: str, message: str, action_html: str = "") -> str:
    return (
        f"<div class='empty-state'><div class='icon'>{icon}</div>"
        f"<p>{message}</p>{action_html}</div>"
    )


def page(title: str, body: str) -> str:
    """Wrap one route's HTML fragment in the shared stylesheet + nav + main
    container. `title` and `body` must already be caller-escaped where they
    carry user/project data — this function adds no escaping of its own,
    matching every route's existing `html.escape` discipline (ui.md U5)."""
    return f"<!doctype html><title>{title} — AutoTester</title>{PAGE_STYLE}{NAV}<main>{body}</main>"
