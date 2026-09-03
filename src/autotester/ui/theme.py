"""Shared visual chrome for every UI route. Contract: qa/contracts/docker.md D5.

One place for styling (anti-drift C3) — every route in `ui/app.py` calls `page()`
to wrap its own HTML fragment; no route builds its own `<style>` block.
"""

from __future__ import annotations

NAV = (
    "<nav><a href='/'>Home</a> · <a href='/onboard'>+ Onboard</a> · "
    "<a href='/live'>Live view</a></nav>"
)

PAGE_STYLE = """
<style>
  :root { color-scheme: light dark; }
  body { font-family: -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
         max-width: 860px; margin: 2rem auto; padding: 0 1rem; line-height: 1.5; }
  nav { margin-bottom: 1.5rem; padding-bottom: .75rem; border-bottom: 1px solid #8883; }
  nav a { text-decoration: none; }
  nav a:hover { text-decoration: underline; }
  h1 { font-size: 1.5rem; margin-bottom: .25rem; }
  table { border-collapse: collapse; width: 100%; margin: 1rem 0; }
  th, td { text-align: left; padding: .4rem .6rem; border-bottom: 1px solid #8883; }
  form { margin: .5rem 0; }
  input[type=text], input[type=password], input:not([type]) {
    padding: .35rem .5rem; border: 1px solid #8886; border-radius: 4px; margin: .15rem 0;
  }
  button { padding: .4rem .9rem; border: 1px solid #8886; border-radius: 4px;
           background: #2563eb; color: #fff; cursor: pointer; }
  button:hover { opacity: .9; }
  ul { padding-left: 1.2rem; }
  .badge { display: inline-block; padding: .1rem .5rem; border-radius: 3px; font-size: .85em; }
  .badge-pass { background: #16a34a33; color: #16a34a; }
  .badge-fail { background: #dc262633; color: #dc2626; }
  .badge-blocked { background: #ca8a0433; color: #ca8a04; }
  .badge-inconclusive { background: #8883; }
  iframe.live-view { width: 100%; height: 70vh; border: 1px solid #8886; border-radius: 6px; }
</style>
"""

_BADGE_CLASS = {
    "PASS": "badge-pass", "FAIL": "badge-fail",
    "BLOCKED": "badge-blocked", "INCONCLUSIVE": "badge-inconclusive",
}


def badge(value: str) -> str:
    """A colored `<span>` for a result/outcome value already HTML-escaped by the caller."""
    cls = _BADGE_CLASS.get(value, "")
    return f"<span class='badge {cls}'>{value}</span>"


def page(title: str, body: str) -> str:
    """Wrap one route's HTML fragment in the shared stylesheet + nav. `title` and
    `body` must already be caller-escaped where they carry user/project data —
    this function adds no escaping of its own, matching every route's existing
    `html.escape` discipline (qa/contracts/ui.md U5)."""
    return f"<!doctype html><title>{title} — AutoTester</title>{PAGE_STYLE}{NAV}{body}"
