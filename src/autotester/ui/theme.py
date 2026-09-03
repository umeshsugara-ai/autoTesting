"""Shared visual system for every UI route. Contract: qa/contracts/docker.md D5.

One place for styling (anti-drift C3) — every route in `ui/app.py` calls
`page()`/`card()`/`stat()`/`empty_state()` to build its HTML; no route writes
its own `<style>` block or reinvents a layout primitive.
"""

from __future__ import annotations

NAV = """
<header class="topbar">
  <a class="brand" href="/">
    <span class="brand-mark">AT</span><span class="brand-name">AutoTester</span>
  </a>
  <nav>
    <a href="/">Projects</a>
    <a href="/onboard">+ New project</a>
    <a href="/live" class="nav-live">● Live view</a>
  </nav>
</header>
"""

PAGE_STYLE = """
<style>
  :root {
    color-scheme: light dark;
    --bg: #f7f8fa; --surface: #ffffff; --border: #e2e5ea;
    --text: #16181d; --text-dim: #667085; --muted: #9aa1ac;
    --primary: #2563eb; --primary-text: #ffffff; --primary-dim: #eef2ff;
    --success: #16a34a; --success-bg: #ecfdf3; --danger: #dc2626; --danger-bg: #fef2f2;
    --warning: #b45309; --warning-bg: #fffbeb; --neutral-bg: #f1f2f4;
    --radius: 10px; --shadow: 0 1px 2px rgba(16,24,40,.06), 0 1px 3px rgba(16,24,40,.08);
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --bg: #0f1115; --surface: #171a21; --border: #2a2e37;
      --text: #eef0f3; --text-dim: #9aa1ac; --muted: #6b7280;
      --primary: #5b8def; --primary-text: #0b1220; --primary-dim: #16223d;
      --success: #34d399; --success-bg: #0d2a1e; --danger: #f87171; --danger-bg: #2c1414;
      --warning: #fbbf24; --warning-bg: #2c2210; --neutral-bg: #20242c;
      --shadow: 0 1px 2px rgba(0,0,0,.4);
    }
  }
  * { box-sizing: border-box; }
  body {
    background: var(--bg); color: var(--text); margin: 0;
    font-family: -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    line-height: 1.5; -webkit-font-smoothing: antialiased;
  }
  main { max-width: 980px; margin: 0 auto; padding: 2rem 1.5rem 4rem; }

  .topbar {
    display: flex; align-items: center; justify-content: space-between;
    padding: .9rem 1.5rem; background: var(--surface); border-bottom: 1px solid var(--border);
    position: sticky; top: 0; z-index: 10;
  }
  .brand { display: flex; align-items: center; gap: .5rem; text-decoration: none;
           color: var(--text); }
  .brand-mark {
    display: inline-grid; place-items: center; width: 28px; height: 28px; border-radius: 8px;
    background: var(--primary); color: var(--primary-text); font-weight: 700; font-size: .8rem;
  }
  .brand-name { font-weight: 600; }
  .topbar nav { display: flex; gap: 1.4rem; align-items: center; }
  .topbar nav a { color: var(--text-dim); text-decoration: none; font-size: .92rem; }
  .topbar nav a:hover { color: var(--text); }
  .nav-live { color: var(--success) !important; font-weight: 600; }

  h1 { font-size: 1.5rem; margin: 0 0 .3rem; letter-spacing: -.01em; }
  .page-header { display: flex; align-items: baseline; justify-content: space-between;
                 gap: 1rem; margin-bottom: 1.5rem; flex-wrap: wrap; }
  .subtitle { color: var(--text-dim); margin: 0; font-size: .95rem; }
  .breadcrumb { font-size: .85rem; color: var(--muted); margin-bottom: .5rem; }
  .breadcrumb a { color: var(--muted); }

  .card {
    background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius);
    padding: 1.25rem 1.4rem; box-shadow: var(--shadow); margin-bottom: 1.25rem;
  }
  .card h2 { font-size: 1.05rem; margin: 0 0 .9rem; }
  .card-actions { display: flex; gap: .6rem; flex-wrap: wrap; margin-top: 1rem; }

  .project-grid {
    display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 1rem;
  }
  .project-card {
    background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius);
    padding: 1.1rem 1.2rem; text-decoration: none; color: var(--text); box-shadow: var(--shadow);
    transition: border-color .12s, transform .12s;
  }
  .project-card:hover { border-color: var(--primary); transform: translateY(-1px); }
  .project-card .name { font-weight: 600; margin-bottom: .5rem; display: block; }
  .project-card .meta { color: var(--text-dim); font-size: .85rem; }

  .stat-row { display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 1.5rem; }
  .stat {
    flex: 1 1 140px; background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 1rem 1.2rem; box-shadow: var(--shadow);
  }
  .stat .value { font-size: 1.6rem; font-weight: 700; line-height: 1.1; }
  .stat .label { color: var(--text-dim); font-size: .82rem; margin-top: .2rem; }

  table { border-collapse: collapse; width: 100%; }
  th { text-align: left; font-size: .78rem; text-transform: uppercase; letter-spacing: .03em;
       color: var(--text-dim); padding: .5rem .7rem; border-bottom: 1px solid var(--border); }
  td { padding: .65rem .7rem; border-bottom: 1px solid var(--border); font-size: .92rem; }
  tr:last-child td { border-bottom: none; }
  tr:hover td { background: var(--neutral-bg); }

  form { margin: 0; }
  .field { margin-bottom: 1.1rem; }
  .field label { display: block; font-size: .85rem; font-weight: 600; margin-bottom: .35rem; }
  .field .hint { display: block; color: var(--muted); font-size: .8rem; margin-top: .3rem; }
  input[type=text], input[type=password], input[type=url], input:not([type]) {
    width: 100%; padding: .55rem .7rem; border: 1px solid var(--border); border-radius: 7px;
    background: var(--surface); color: var(--text); font-size: .95rem;
  }
  input:focus { outline: 2px solid var(--primary); outline-offset: 1px; }

  .btn {
    display: inline-flex; align-items: center; gap: .4rem; padding: .55rem 1.1rem;
    border-radius: 7px; border: 1px solid var(--border); background: var(--surface);
    color: var(--text); font-size: .9rem; font-weight: 600; cursor: pointer;
    text-decoration: none; line-height: 1;
  }
  .btn:hover { border-color: var(--primary); }
  .btn-primary { background: var(--primary); color: var(--primary-text);
                 border-color: var(--primary); }
  .btn-primary:hover { opacity: .92; }
  .btn-sm { padding: .35rem .7rem; font-size: .82rem; }

  .badge {
    display: inline-flex; align-items: center; gap: .3rem; padding: .18rem .6rem;
    border-radius: 999px; font-size: .78rem; font-weight: 600;
  }
  .badge-pass { background: var(--success-bg); color: var(--success); }
  .badge-fail { background: var(--danger-bg); color: var(--danger); }
  .badge-blocked { background: var(--warning-bg); color: var(--warning); }
  .badge-inconclusive { background: var(--neutral-bg); color: var(--text-dim); }

  .empty-state {
    text-align: center; padding: 3rem 1.5rem; color: var(--text-dim);
    border: 1px dashed var(--border); border-radius: var(--radius); background: var(--surface);
  }
  .empty-state .icon { font-size: 2rem; margin-bottom: .6rem; }
  .empty-state p { margin: .3rem 0 1.2rem; }

  .live-shell { border: 1px solid var(--border); border-radius: var(--radius);
                overflow: hidden; box-shadow: var(--shadow); }
  .live-shell iframe { width: 100%; height: 68vh; border: none; display: block; }
  .live-tip { background: var(--surface); border: 1px solid var(--border);
              border-radius: var(--radius); padding: 1rem 1.2rem; margin-bottom: 1.25rem; }
  .live-tip code { background: var(--neutral-bg); padding: .1rem .4rem; border-radius: 4px; }
</style>
"""

_BADGE_CLASS = {
    "PASS": ("badge-pass", "✓"), "FAIL": ("badge-fail", "✕"),
    "BLOCKED": ("badge-blocked", "⏸"), "INCONCLUSIVE": ("badge-inconclusive", "?"),
}


def badge(value: str) -> str:
    """A colored `<span>` for a test RESULT value (PASS/FAIL/BLOCKED/INCONCLUSIVE)
    already HTML-escaped by the caller. Never reuse this for a non-test-result
    status (credential presence, review state) — that's what `pill()` is for;
    the two vocabularies read as the same thing to a user otherwise."""
    cls, icon = _BADGE_CLASS.get(value, ("badge-inconclusive", ""))
    return f"<span class='badge {cls}'>{icon} {value}</span>"


_PILL_CLASS = {
    "positive": "badge-pass", "warning": "badge-blocked", "neutral": "badge-inconclusive",
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
