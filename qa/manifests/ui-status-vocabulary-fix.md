# Manifest — ui-status-vocabulary-fix

**Contract:** qa/contracts/ui.md (U1–U5, unchanged behavior) + qa/contracts/docker.md D5
**Goal task:** none
**Date:** 2026-09-04
**Fix cycle:** 1 of max 3
**Issues addressed:** none (pre-emptive polish, found while demoing the server to Umesh)

## Why this unit

Umesh asked to see the system running live as a server, framing it explicitly around a future
production launch and "user experience better and easy to use hona chaiyee." Reviewing my own
screenshots before showing him, I found two real clarity bugs in the previous redesign:

1. The credentials page reused the test-result `badge()` component (colored PASS/INCONCLUSIVE
   pills) to mean "a value is set" — a user seeing a green "✓ PASS" pill next to a credential
   key could reasonably think a test had run and passed, when it only means a `.env` value
   exists. Same visual vocabulary, different meaning — exactly the kind of confusion "easy to
   use" is asking to avoid.
2. The project detail page rendered flowspec review status (`"no flowspec yet"`, `"draft"`,
   `"approved"`) as a `stat` tile — the same big-bold-number component used for a case count.
   A long sentence in that slot reads oddly (a "metric" that's actually a sentence).

## What changed

- `src/autotester/ui/theme.py` — new `pill(text, tone)` helper (`_PILL_CLASS`: positive/warning/
  neutral), documented as the non-test-result counterpart to `badge()` (docstring on `badge()`
  updated to say explicitly not to reuse it for non-test-result status).
- `src/autotester/ui/app.py`:
  - `env_editor_view()` — credential status is now `pill("● Set", "positive")` /
    `pill("○ Not set", "neutral")` instead of misusing `badge('PASS')`/`badge('INCONCLUSIVE')`.
  - `project_detail()` — review status moved out of the stat row into a small pill next to the
    base URL (`review: <pill>`), tone-mapped (`positive` for `approved`, `warning` for any other
    real status, `neutral` for "no flowspec yet"); the stat row now only holds actual counts
    (cases, allowed domains).

## Real verification performed (not simulated)

```
$ uv run pytest tests/test_ui.py -v      # 16 passed, 1 skipped, all pre-existing assertions hold
$ uv run pytest -q                        # all green
$ uv run ruff check src tests scripts     # All checks passed!
$ uv run autotester doctor                # doctor: clean
```

Restarted the live container (`docker compose restart`) — confirmed Xvfb/x11vnc/websockify all
survived (the entrypoint restart-safety fix from the prior unit holds) — and took fresh
screenshots via a real headless Playwright client:
- `/projects/pathlynks/env` — every row now shows a green "● Set" pill, visually distinct from
  a test-result badge (different label, same color family intentionally kept for "good/present").
- `/projects/pathlynks` — review status is a small gray "no flowspec yet" pill next to the URL,
  no longer a giant sentence sitting where a number belongs.

Opened both pages in a real Windows browser window (`Start-Process`) for Umesh, live against the
running Docker container.

## How to verify

- `uv run pytest -q` / `ruff check` / `autotester doctor` → all clean
- `docker compose restart` then reload `/projects/<slug>/env` and `/projects/<slug>` in a browser
  → credential rows show "Set"/"Not set" pills (not PASS/INCONCLUSIVE test badges); review status
  is a small pill next to the subtitle, not a stat tile

## Scope notes for the checker

- Purely presentational — no route's underlying `ProjectStore`/`SecretStore` calls or escaping
  changed; `tests/test_ui.py`'s pre-existing assertions (which check for the word "set" and for
  "no flowspec yet" as substrings) still pass unchanged against the new markup.
- `badge()` itself is unchanged in behavior — only its docstring was tightened, and a sibling
  `pill()` was added, so no existing caller (`run_view`, `report`) is affected.

## Status: checked-PASS — see qa/verdicts/ui-status-vocabulary-fix.md, cycle 1 PASS
