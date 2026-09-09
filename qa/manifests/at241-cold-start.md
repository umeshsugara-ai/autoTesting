# Manifest — at241-cold-start

**Unit:** AT-241 + AT-239 + AT-240 — close the cold start: the FlowSpec review gate, EXPAND's
button, and the video-request queue, all reachable from the UI
**Commit:** `abce166`
**Fix cycle:** 1
**Dual check:** no
**Contract:** `qa/contracts/ui.md` (U1–U6, U8/U9), `qa/contracts/expand.md` (X1),
`qa/contracts/coverage.md` (V1–V3), review-gate R1–R3
**Goal task:** T-100 (reopened `pending` by the sweep). This unit is the first half of what
reopened it; it does **not** close T-100 — see "What this does not claim".
**Issues addressed:** AT-241, AT-239, AT-240, AT-244 (partial)

## Why this unit exists — the product's own promise was false

The business-truth campaign drove AutoTester's UI in a real browser and onboarded a product it had
never seen. A freshly onboarded product's **only** route to being runnable was hand-writing cases
one at a time. T-100's acceptance note — *"full onboarding → report without touching the CLI"* —
was false on the day it was written.

The sweep then measured the consequence: across four real projects there are **52 cases, 50 of them
`happy`, and ZERO produced by the expander.** `expand_flow` had no callers in `src/` or `scripts/`
at all.

## What changed

- `src/autotester/ui/routes_learn.py` (new, 232) — the three surfaces:
  `GET /projects/{slug}/flowspec` · `POST …/flowspec/approve` · `POST …/flowspec/request-edit` ·
  `POST …/cases/generate` · `GET …/requests`
- `src/autotester/ui/app.py` — registers the router; the zero-case empty state now offers
  **"Teach it from a recording"** beside "+ Add the first case". That single missing link was
  AT-241's dead end.
- `src/autotester/ui/project_view.py` (new) — `_actions_card` moved out when `app.py` crossed 300
- `src/autotester/ui/routes_runs.py` — `_ask_for_what_it_did_not_recognise` after `save_run`
- `src/autotester/ui/routes_crawls.py` — the same, after `run_crawl`
- `src/autotester/stages/coverage.py` — `queue_requests`, the one place a gap becomes an ask
- `src/autotester/cli.py` — `autotester expand` (AT-239's CLI half)

## The three findings, each stated as what was actually wrong

**AT-239 — the differentiator had no door.** `stages/expand.py` was written, tested and PASSed, and
nothing called it. A feature with no entry point is not a slow feature; it is an absent one.

**AT-240 — the self-extension loop's last link was missing.** `diff_coverage`, `request_for` and
`ProjectStore.add_request` were each correct and each called only from tests. **Not one
`VideoRequest` had ever been created**, so the north star's *"when it meets a screen it does not
know, it asks the human for a video instead of guessing"* had never happened once.

**Worth reading the shape of that gap:** of the six wiring tests, the three *"asks for nothing"*
cases **passed for free** while the feature did nothing at all. A negative test over an inert
feature is indistinguishable from a negative test over a correct one — the vacuous-guard class
(AT-218) arriving as a coverage illusion rather than a weak assertion.

**AT-241 — the gate swings both ways.** A review page with only an Approve button is a rubber stamp.
`request-edit` is here for that reason, and an approval nobody signed is refused (R2).

## Mistakes I made in this unit, both caught by running

1. **`theme.breadcrumb` and `theme.empty_state` take CALLER-escaped labels** — their own docstrings
   say so. I passed `project.name` raw into three call sites, and U5's hostile probe
   (`<script>alert(1)</script>`) caught all three. The `<title>` was the sharpest: `theme.page`
   does not escape it either.
2. `SecretStore(slug)` is not the constructor. Every other route uses
   `SecretStore.load(project, ProjectPaths(slug).env_file, strict=False)`; I invented a second
   construction and it failed at once.

## How to verify

```
uv run pytest                                    → 909 passed, 2 skipped
uv run ruff check src tests scripts              → All checks passed!
uv run autotester map && uv run autotester doctor → doctor: clean
uv run pytest tests/test_ui_learn.py tests/test_ui_requests.py tests/test_coverage_wiring.py \
              tests/test_expand_cli.py           → 30 passed
```

## Live browser evidence

`qa/evidence/browser-at241-cold-start-2026-09-09/report.json` — real headless Chromium against a
live `uvicorn` on a **cold-start project** (zero cases, zero flowspec), the exact state AT-241 is
about.

- **3 pages, 0 console errors.**
- **4/4 interactions passed**, and they interact rather than look:
  - the zero-case project page offers a route to `/projects/demo/flowspec` — **1 link found**
  - **clicking it** lands on the flowspec page (`url` ends `/flowspec`), not a 404
  - that page says *"no flowspec"* and carries **2 onward links** — not a dead end
  - the empty request queue gives an honest empty state, not a blank page

**This is a smoke check and is never the validation** (the ship rule). The checker runs Mode D with
its own script.

## What this unit does NOT claim

- **It does not close T-100.** The sweep reopened it on stronger grounds than this unit repairs:
  **24 UI-touching PASS verdicts, 0 of 24 carrying a `LIVE-BROWSER` line** (AT-243). This unit adds
  the missing surfaces; it does not re-validate the other 23.
- **No case has yet been generated by the expander on a real product.** The button exists and is
  tested with a mock provider; the 50-of-52-`happy` measurement is unchanged until someone drives it
  against a real FlowSpec — and **there are still zero FlowSpecs anywhere on disk.**
- `AT-244` is only partly addressed: refusals from *these* routes are pages; other routes still
  raise raw `HTTPException`.

## Contract criteria requested (checker to author)

- A project with no FlowSpec renders a page that states so and offers at least one way onward.
- The review gate refuses an unsigned approval and changes nothing on refusal.
- The gate moves in both directions from the UI.
- Free-text review fields go through the same credential guard as the case form (U8/U9).
- Generate refuses — as a themed page, not raw JSON — when there is no FlowSpec, when it is
  unapproved (X1), or when no provider is available; and writes no cases in any of those cases.
- Every coverage gap a run or a crawl produces becomes exactly one `VideoRequest`, and a known
  route produces none (V1–V3).
- Both new GET routes escape project data (U5).

## Status: ready-for-check
