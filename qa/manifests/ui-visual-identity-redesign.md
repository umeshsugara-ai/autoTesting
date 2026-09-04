# Manifest — ui-visual-identity-redesign

**Contract:** qa/contracts/ui.md (U1–U5, unchanged behavior) + qa/contracts/docker.md D5
**Goal task:** none
**Date:** 2026-09-04
**Fix cycle:** 1 of max 3
**Issues addressed:** none

## Why this unit

Umesh, after the earlier component-based redesign: "humko iss product ka UI bhi professionally
build karna hai — abhi ye aisa hai ki mann hi nahi kar raha isko chalane ka aur use karne ka" —
we need to build this product's UI professionally too; right now it's such that I don't even feel
like running or using it. The earlier pass (cards, stat tiles, badges) was structurally sound but
visually generic — this unit is a real design pass, not another layout tweak.

## Design direction

A "technical instrument," not a generic SaaS dashboard: this tool drives a real browser and
reports real evidence, so the type should read like an instrument panel. Fraunces (a
characterful serif with real optical weight) carries headings and the wordmark; IBM Plex Sans is
body copy; IBM Plex Mono is anything that reads like data — ids, breadcrumbs, badges, table
headers. One committed accent (a burnt-amber, `--accent`) carries every primary action and the
brand mark, distinct from the semantic PASS/FAIL/BLOCKED colors so a result badge is never
mistaken for a button. A subtle dot-grid background texture and a colored left-edge accent on
project cards add depth without new components.

## What changed

`src/autotester/ui/theme.py` — rewritten `PAGE_STYLE` and `NAV`; the public function API
(`page`, `card`, `stat`, `badge`, `pill`, `empty_state`) is **byte-identical in signature** —
this is a pure visual restyle, zero changes to `ui/app.py` or any route's logic/escaping.
Google Fonts loaded via 4 short `<link>` tags (Fraunces regular/bold/italic split to keep each
URL under the line-length limit, IBM Plex Sans, IBM Plex Mono).

## Real verification performed (not simulated)

```
$ uv run pytest tests/test_ui.py -v      # 16 passed, 1 skipped -- every pre-existing assertion
                                           # holds unchanged (proof this is presentation-only)
$ uv run pytest -q                        # all green
$ uv run ruff check src tests scripts     # All checks passed!
$ uv run autotester doctor                # doctor: clean
```

Restarted the live Docker container and took real headless-Playwright screenshots (visually
inspected, not just curled for 200): `/` (project cards with the amber left-edge accent, serif
heading, dot-grid background), `/projects/pathlynks` (mono breadcrumb, serif numeral stat tiles),
`/onboard` (labeled fields with the new type hierarchy). All three read as a cohesive, deliberate
identity — not the generic blue-badge dashboard look from the previous pass.

```
$ uv run python scripts/check_no_secrets.py src/autotester/ui/theme.py
scanned 1 file(s); 0 leak(s)
```

## How to verify

- `uv run pytest tests/test_ui.py -v` → 16 passed, 1 skipped, unchanged
- `uv run pytest -q` / `ruff check` / `autotester doctor` → all clean
- `docker compose restart` then open `/`, `/onboard`, `/projects/<slug>` in a real browser →
  serif headings, mono data/breadcrumbs, amber accent, no generic blue/purple SaaS look

## Scope notes for the checker

- Zero logic changes anywhere — confirm via `git diff --stat` that only `theme.py` changed.
- Every one of `tests/test_ui.py`'s substring assertions (case titles, "no runs yet", "set"/"not
  set", etc.) still passing unchanged is the actual proof this is presentation-only, not a claim
  to take on faith — please re-run the suite yourself.
- This is a visual-quality judgment call as much as a functional one — take your own screenshots
  and form an independent opinion on whether this reads as a deliberate, professional identity or
  still a generic template; say so explicitly in the verdict either way.

## Status: checked-PASS — see qa/verdicts/ui-visual-identity-redesign.md, cycle 1 PASS
